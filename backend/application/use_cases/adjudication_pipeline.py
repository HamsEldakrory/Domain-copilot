from dataclasses import dataclass
from typing import Callable
from domain.ports.agent import AgentInput
from domain.ports.agent_run_recorder import AgentRunRecorder

@dataclass
class PipelineResult:
    job_id: str
    steps: list[dict]
    final_recommendation: dict

class AdjudicationPipelineOrchestrator:
    def __init__(
        self,
        coverage_matcher,
        exclusion_analyst,
        adjudication_drafter,
        run_recorder: AgentRunRecorder,
        policy_limit_lookup: Callable[[str], tuple[float, float]],
    ):
        self._coverage_matcher = coverage_matcher
        self._exclusion_analyst = exclusion_analyst
        self._adjudication_drafter = adjudication_drafter
        self._run_recorder = run_recorder
        self._policy_limit_lookup = policy_limit_lookup

    def run(self, claim_id: str, claimed_amount: float) -> PipelineResult:
        job_id = self._run_recorder.start_job(claim_id)
        context = {"claimed_amount": claimed_amount}
        steps = []

        def record(agent_output):
            self._run_recorder.record_agent_run(
                job_id, agent_output.agent_name,
                input_data={"claim_id": claim_id, "context_keys": list(context.keys())},
                output_data=agent_output.result,
            )
            steps.append({"agent": agent_output.agent_name, "result": agent_output.result})

        coverage_output = self._coverage_matcher.run(AgentInput(claim_id=claim_id, context=context))
        record(coverage_output)
        context["coverage_summary"] = coverage_output.result.get("coverage_summary", "")
        context["policy_version_id"] = coverage_output.result.get("policy_version_id")

        if context.get("policy_version_id"):
            limit, deductible = self._policy_limit_lookup(context["policy_version_id"])
            context["policy_limit"] = limit
            context["deductible"] = deductible
        exclusion_output = self._exclusion_analyst.run(AgentInput(claim_id=claim_id, context=context))
        record(exclusion_output)
        context["exclusion_summary"] = exclusion_output.result.get("exclusion_summary", "")
        drafter_output = self._adjudication_drafter.run(AgentInput(claim_id=claim_id, context=context))
        record(drafter_output)
        self._run_recorder.complete_job(job_id)
        return PipelineResult(job_id=job_id, steps=steps, final_recommendation=drafter_output.result)