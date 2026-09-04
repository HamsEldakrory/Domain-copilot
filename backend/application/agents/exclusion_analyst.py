from application.agents.tool_gateway import ToolGateway
from domain.errors import JobCancelledError
from domain.ports.agent import Agent, AgentInput, AgentOutput
from domain.ports.cancellation_checker import CancellationChecker
from domain.ports.job_event_publisher import JobEventPublisher
from domain.ports.llm_provider import LLMProvider, Message


class ExclusionAnalystAgent(Agent):
    name = "exclusion_analyst"
    ALLOWED_TOOLS = ["search_policy"]

    def __init__(
        self, llm_provider: LLMProvider, search_policy,
        event_publisher: JobEventPublisher | None = None,
        cancellation_checker: CancellationChecker | None = None,
    ):
        self._llm = llm_provider
        self._gateway = ToolGateway(self.name, {"search_policy": search_policy})
        self._event_publisher = event_publisher
        self._cancellation_checker = cancellation_checker

    def _publish(self, job_id, event_type, data):
        if self._event_publisher and job_id:
            self._event_publisher.publish(job_id, event_type, data)

    def run(self, input: AgentInput) -> AgentOutput:
        job_id = input.job_id
        self._publish(job_id, "agent_started", {"agent": self.name})

        policy_version_id = input.context.get("policy_version_id")
        search_result = self._gateway.call("search_policy", query="exclusions", policy_version_id=policy_version_id)
        citations = search_result.output.get("citations", [])
        context_text = "\n".join(f"- {c['excerpt']}" for c in citations)
        self._publish(job_id, "agent_progress", {"agent": self.name, "stage": "evidence_gathered", "citation_count": len(citations)})

        prompt = (
            "You are an Exclusion Analyst for an insurance claims adjudication system. "
            "Based only on the policy excerpts below, summarize any exclusions that might apply. "
            "If nothing in the excerpts suggests an exclusion, say so plainly.\n\n"
            f"Policy excerpts:\n{context_text}\n\nRespond in 2-3 sentences."
        )

        stream = self._llm.stream_completion([Message(role="user", content=prompt)])
        full_text = ""
        for token in stream:
            if self._cancellation_checker and job_id and self._cancellation_checker.is_cancelled(job_id):
                stream.close()
                raise JobCancelledError(job_id)
            full_text += token
            self._publish(job_id, "token", {"agent": self.name, "token": token})

        self._publish(job_id, "agent_complete", {"agent": self.name, "input_tokens": stream.input_tokens, "output_tokens": stream.output_tokens})

        return AgentOutput(
            agent_name=self.name,
            result={"exclusion_summary": full_text},
            tool_calls=["search_policy"],
            citations=citations,
            input_tokens=stream.input_tokens,
            output_tokens=stream.output_tokens,
        )