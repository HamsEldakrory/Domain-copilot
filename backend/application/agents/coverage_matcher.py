from backend.application.agents.tool_gateway import ToolGateway
from domain.ports.agent import Agent, AgentInput, AgentOutput
from domain.ports.llm_provider import LLMProvider, Message
from domain.ports.tool import Tool

class CoverageMatcherAgent(Agent):
    name = "coverage_matcher"
    ALLOWED_TOOLS = ["get_policy_version", "search_policy"]
    def __init__(self, llm_provider: LLMProvider, get_policy_version, search_policy):
        self._llm = llm_provider
        self._gateway = ToolGateway(
            self.name, {"get_policy_version": get_policy_version, "search_policy": search_policy}
        )

    def run(self, input: AgentInput) -> AgentOutput:
        version_result = self._gateway.call("get_policy_version", claim_id=input.claim_id)
        if version_result.error:
            return AgentOutput(agent_name=self.name, result={"error": version_result.error}, tool_calls=["get_policy_version"])

        policy_version_id = version_result.output["policy_version_id"]
        search_result = self._gateway.call("search_policy", query="coverage insuring agreement", policy_version_id=policy_version_id)
        citations = search_result.output.get("citations", [])
        context_text = "\n".join(f"- {c['excerpt']}" for c in citations)

        prompt = (
            "You are a Coverage Matcher for an insurance claims adjudication system. "
            "Based only on the policy excerpts below, summarize what coverage applies. "
            "If the excerpts don't clearly establish coverage, say so plainly - do not guess.\n\n"
            f"Policy excerpts:\n{context_text}\n\nRespond in 2-3 sentences."
        )
        completion = self._llm.completion([Message(role="user", content=prompt)])

        return AgentOutput(
            agent_name=self.name,
            result={
                "policy_version_id": policy_version_id,
                "version_mismatch_detected": version_result.output.get("version_mismatch_detected", False),
                "coverage_summary": completion.content,
            },
            tool_calls=["get_policy_version", "search_policy"],
            citations=citations,
        )