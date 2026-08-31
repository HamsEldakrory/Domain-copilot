import concurrent.futures
from dataclasses import dataclass
from typing import Callable
from domain.ports.audit_logger import AuditLogger
from domain.ports.agent import AgentInput
from domain.ports.agent_run_recorder import AgentRunRecorder
from domain.errors import MaxIterationsExceededError, StepTimeoutError
from application.support.retry import retry_with_backoff


MAX_ITERATIONS = 5
STEP_TIMEOUT_SECONDS = 30
@dataclass
class PipelineResult:
    job_id: str
    steps: list[dict]
    final_recommendation: dict
    degraded: bool = False
class AdjudicationPipelineOrchestrator:
    RECOVERABLE_ERRORS = (MaxIterationsExceededError, StepTimeoutError, ConnectionError, TimeoutError)
    def __init__(
        self,
        coverage_matcher,
        exclusion_analyst,
        adjudication_drafter,
        run_recorder: AgentRunRecorder,
        policy_limit_lookup: Callable[[str], tuple[float, float]],
        search_policy_tool=None,
        audit_logger: AuditLogger | None = None,
        get_policy_version_tool=None,
        max_iterations: int = MAX_ITERATIONS,

    ):
        self._coverage_matcher = coverage_matcher
        self._exclusion_analyst = exclusion_analyst
        self._adjudication_drafter = adjudication_drafter
        self._run_recorder = run_recorder
        self._policy_limit_lookup = policy_limit_lookup
        self._search_policy_tool = search_policy_tool
        self._iteration_count = 0
        self._audit_logger = audit_logger
        self._get_policy_version_tool = get_policy_version_tool
        self._max_iterations = max_iterations

    def _run_step_with_controls(self, agent, agent_input, step_name):
        self._iteration_count += 1
        if self._iteration_count > self._max_iterations:
            raise MaxIterationsExceededError(self._max_iterations)

        @retry_with_backoff(max_attempts=3, base_delay=1.0)
        def _call():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(agent.run, agent_input)
                try:
                    return future.result(timeout=STEP_TIMEOUT_SECONDS)
                except concurrent.futures.TimeoutError:
                    raise StepTimeoutError(step_name, STEP_TIMEOUT_SECONDS)

        return _call()

    def _degrade_to_plain_rag(self, claim_id: str, job_id: str) -> PipelineResult:
        if not self._search_policy_tool:
            return PipelineResult(job_id=job_id, steps=[], final_recommendation={"error": "Pipeline failed and no degradation path available"}, degraded=True)
        policy_version_id = None
        if self._get_policy_version_tool:
            version_result = self._get_policy_version_tool.run(claim_id=claim_id)
            if not version_result.error:
                policy_version_id = version_result.output.get("policy_version_id")

        result = self._search_policy_tool.run(query="policy overview coverage", policy_version_id=policy_version_id)
        self._run_recorder.record_agent_run(job_id, "plain_rag_fallback", input_data={"claim_id": claim_id, "policy_version_id": policy_version_id}, output_data=result.output)
        self._run_recorder.update_job_status(job_id, "WAITING_APPROVAL")
        return PipelineResult(
            job_id=job_id, steps=[{"agent": "plain_rag_fallback", "result": result.output}],
            final_recommendation={"note": "Full agent pipeline unavailable - degraded to direct policy search, still filtered to the correct policy version where resolvable. Escalate for manual review.", "search_result": result.output},
            degraded=True,
        )
    def run(self, claim_id: str, claimed_amount: float) -> PipelineResult:
        job_id = self._run_recorder.start_job(claim_id)
        context = {"claimed_amount": claimed_amount}
        steps = []


        def record(agent_output):
            self._run_recorder.record_agent_run(
                job_id, agent_output.agent_name,
                input_data={"claim_id": claim_id, "context_keys": list(context.keys())},
                output_data={**agent_output.result, "citations": agent_output.citations},
            )
            steps.append({"agent": agent_output.agent_name, "result": agent_output.result})
            if self._audit_logger:
                self._audit_logger.log(job_id, None, f"agent_run:{agent_output.agent_name}", {"tool_calls": agent_output.tool_calls})
        try:
            coverage_output = self._run_step_with_controls(
                self._coverage_matcher, AgentInput(claim_id=claim_id, context=context), "coverage_matcher"
            )
            record(coverage_output)
            context["coverage_summary"] = coverage_output.result.get("coverage_summary", "")
            context["policy_version_id"] = coverage_output.result.get("policy_version_id")

            if context.get("policy_version_id"):
                limit, deductible = self._policy_limit_lookup(context["policy_version_id"])
                context["policy_limit"] = limit
                context["deductible"] = deductible

            exclusion_output = self._run_step_with_controls(
                self._exclusion_analyst, AgentInput(claim_id=claim_id, context=context), "exclusion_analyst"
            )
            record(exclusion_output)
            context["exclusion_summary"] = exclusion_output.result.get("exclusion_summary", "")

            drafter_output = self._run_step_with_controls(
                self._adjudication_drafter, AgentInput(claim_id=claim_id, context=context), "adjudication_drafter"
            )
            record(drafter_output)

            self._run_recorder.update_job_status(job_id, "WAITING_APPROVAL")
            if self._audit_logger:
                self._audit_logger.log(job_id, None, "pipeline_completed_awaiting_approval", {})
            return PipelineResult(job_id=job_id, steps=steps, final_recommendation=drafter_output.result)

        except self.RECOVERABLE_ERRORS:
            return self._degrade_to_plain_rag(claim_id, job_id)