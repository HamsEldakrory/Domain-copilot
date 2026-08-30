from domain.ports.agent import Agent, AgentInput, AgentOutput
from domain.ports.llm_provider import LLMProvider, Message
from domain.ports.tool import Tool


class ExclusionAnalystAgent(Agent):
    name = "exclusion_analyst"
    def __init__(self, llm_provider: LLMProvider, search_policy: Tool):
        self._llm = llm_provider
        self._search_policy = search_policy
    def run(self, input: AgentInput) -> AgentOutput:
        policy_version_id = input.context.get("policy_version_id")
        search_result = self._search_policy.run(query="exclusions", policy_version_id=policy_version_id)
        citations = search_result.output.get("citations", [])
        context_text = "\n".join(f"- {c['excerpt']}" for c in citations)
        prompt = (
            "You are an Exclusion Analyst for an insurance claims adjudication system. "
            "Based only on the policy excerpts below, summarize any exclusions that might apply. "
            "If nothing in the excerpts suggests an exclusion, say so plainly.\n\n"
            f"Policy excerpts:\n{context_text}\n\nRespond in 2-3 sentences."
        )
        completion = self._llm.completion([Message(role="user", content=prompt)])

        return AgentOutput(
            agent_name=self.name,
            result={"exclusion_summary": completion.content},
            tool_calls=["search_policy"],
            citations=citations,
        )