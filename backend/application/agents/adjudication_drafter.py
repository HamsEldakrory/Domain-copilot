from application.agents.tool_gateway import ToolGateway
from domain.ports.agent import Agent, AgentInput, AgentOutput
from domain.ports.llm_provider import LLMProvider, Message
from domain.ports.tool import Tool
class AdjudicationDrafterAgent(Agent):
    name = "adjudication_drafter"
    ALLOWED_TOOLS = ["calculate_payout", "detect_anomaly"]
    def __init__(self, llm_provider: LLMProvider, calculate_payout: Tool, detect_anomaly: Tool):
        self._llm = llm_provider
        self._gateway = ToolGateway(
            self.name, {"calculate_payout": calculate_payout, "detect_anomaly": detect_anomaly}
        )
    def run(self, input: AgentInput) -> AgentOutput:
        claimed_amount = input.context.get("claimed_amount", 0)
        policy_limit = input.context.get("policy_limit", 0)
        deductible = input.context.get("deductible", 0)
        payout_result = self._gateway.call("calculate_payout", claimed_amount=claimed_amount, policy_limit=policy_limit, deductible=deductible)
        anomaly_result = self._gateway.call("detect_anomaly", claim_id=input.claim_id, claimed_amount=claimed_amount)
        prompt = (
            "You are an Adjudication Drafter. Draft a short recommendation narrative for a "
            "human adjuster to review. Do NOT state any dollar figure yourself - the payout "
            "amount is computed separately and deterministically.\n\n"
            f"Coverage analysis: {input.context.get('coverage_summary', '')}\n"
            f"Exclusion analysis: {input.context.get('exclusion_summary', '')}\n"
            f"Anomaly flags: {anomaly_result.output.get('flags', [])}\n\n"
            "Write 2-3 sentences recommending approve, reject, or escalate, with reasoning."
        )
        completion = self._llm.completion([Message(role="user", content=prompt)])
        return AgentOutput(
            agent_name=self.name,
            result={
                "payout": payout_result.output,
                "anomaly": anomaly_result.output,
                "recommendation_narrative": completion.content,
            },
            tool_calls=["calculate_payout", "detect_anomaly"],
        )