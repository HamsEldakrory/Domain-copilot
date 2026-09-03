from domain.ports.agent import Agent, AgentInput, AgentOutput
from domain.ports.llm_provider import LLMProvider, Message
from domain.ports.job_event_publisher import JobEventPublisher
from domain.ports.cancellation_checker import CancellationChecker
from domain.errors import JobCancelledError
from application.agents.tool_gateway import ToolGateway
class CoverageMatcherAgent(Agent):
    name = "coverage_matcher"
    ALLOWED_TOOLS = ["get_policy_version", "search_policy"]

    def __init__(
        self, llm_provider: LLMProvider, get_policy_version, search_policy,
        event_publisher: JobEventPublisher | None = None,
        cancellation_checker: CancellationChecker | None = None,
    ):
        self._llm = llm_provider
        self._gateway = ToolGateway(self.name, {"get_policy_version": get_policy_version, "search_policy": search_policy})
        self._event_publisher = event_publisher
        self._cancellation_checker = cancellation_checker

    def _publish(self, job_id, event_type, data):
        if self._event_publisher and job_id:
            self._event_publisher.publish(job_id, event_type, data)

    def run(self, input: AgentInput) -> AgentOutput:
        job_id = input.job_id
        self._publish(job_id, "agent_started", {"agent": self.name})
        version_result = self._gateway.call("get_policy_version", claim_id=input.claim_id)
        if version_result.error:
            self._publish(job_id, "agent_complete", {"agent": self.name, "error": version_result.error})
            return AgentOutput(agent_name=self.name, result={"error": version_result.error}, tool_calls=["get_policy_version"])

        policy_version_id = version_result.output["policy_version_id"]
        search_result = self._gateway.call("search_policy", query="coverage insuring agreement", policy_version_id=policy_version_id)
        citations = search_result.output.get("citations", [])
        context_text = "\n".join(f"- {c['excerpt']}" for c in citations)

        self._publish(job_id, "agent_progress", {"agent": self.name, "stage": "evidence_gathered", "citation_count": len(citations)})
        prompt = (
            "You are a Coverage Matcher for an insurance claims adjudication system. "
            "Based only on the policy excerpts below, summarize what coverage applies. "
            "If the excerpts don't clearly establish coverage, say so plainly - do not guess.\n\n"
            f"Policy excerpts:\n{context_text}\n\nRespond in 2-3 sentences."
        )
        stream = self._llm.stream_completion([Message(role="user", content=prompt)])
        full_text = ""
        try:
            for token in stream:
                if self._cancellation_checker and job_id and self._cancellation_checker.is_cancelled(job_id):
                    stream.close()
                    raise JobCancelledError(job_id)
                full_text += token
                self._publish(job_id, "token", {"agent": self.name, "token": token})
        except JobCancelledError:
            raise

        self._publish(job_id, "agent_complete", {
            "agent": self.name,
            "input_tokens": stream.input_tokens,
            "output_tokens": stream.output_tokens,
        })
        return AgentOutput(
            agent_name=self.name,
            result={
                "policy_version_id": policy_version_id,
                "version_mismatch_detected": version_result.output.get("version_mismatch_detected", False),
                "coverage_summary": full_text,
            },
            tool_calls=["get_policy_version", "search_policy"],
            citations=citations,
            input_tokens=stream.input_tokens,
            output_tokens=stream.output_tokens,
        )