from domain.ports.agent import Agent, AgentInput, AgentOutput
from domain.ports.llm_provider import LLMProvider, Message
from domain.ports.job_event_publisher import JobEventPublisher
from domain.ports.cancellation_checker import CancellationChecker
from domain.errors import JobCancelledError
from application.agents.tool_gateway import ToolGateway
class AdjudicationDrafterAgent(Agent):
    name = "adjudication_drafter"
    ALLOWED_TOOLS = ["calculate_payout", "detect_anomaly"]
    def __init__(
        self, llm_provider: LLMProvider, calculate_payout, detect_anomaly,
        event_publisher: JobEventPublisher | None = None,
        cancellation_checker: CancellationChecker | None = None,
    ):
        self._llm = llm_provider
        self._gateway = ToolGateway(self.name, {"calculate_payout": calculate_payout, "detect_anomaly": detect_anomaly})
        self._event_publisher = event_publisher
        self._cancellation_checker = cancellation_checker

    def _publish(self, job_id, event_type, data):
        if self._event_publisher and job_id:
            self._event_publisher.publish(job_id, event_type, data)

    def run(self, input: AgentInput) -> AgentOutput:
        job_id = input.job_id
        self._publish(job_id, "agent_started", {"agent": self.name})
        claimed_amount = input.context.get("claimed_amount", 0)
        policy_limit = input.context.get("policy_limit", 0)
        deductible = input.context.get("deductible", 0)
        payout_result = self._gateway.call("calculate_payout", claimed_amount=claimed_amount, policy_limit=policy_limit, deductible=deductible)
        anomaly_result = self._gateway.call("detect_anomaly", claim_id=input.claim_id, claimed_amount=claimed_amount)

        payout_dict = {
            k: float(v) if hasattr(v, "quantize") else v 
            for k, v in payout_result.output.items()
        }
        self._publish(job_id, "payout", {
            **payout_dict,
            "anomaly_flags": anomaly_result.output.get("flags", []),
        })
        self._publish(job_id, "agent_progress", {"agent": self.name, "stage": "payout_and_anomaly_computed"})

        prompt = (
            "You are an Adjudication Drafter. Draft a short recommendation narrative for a "
            "human adjuster to review. The payout has been calculated for you.\n\n"
            f"Coverage analysis: {input.context.get('coverage_summary', '')}\n"
            f"Exclusion analysis: {input.context.get('exclusion_summary', '')}\n"
            f"Anomaly flags: {anomaly_result.output.get('flags', [])}\n"
            f"Calculated Payout: ${payout_dict.get('payout', 0):.2f}\n\n"
            "Write 2-3 sentences recommending approve, reject, or escalate, with reasoning. "
            "Make sure to explicitly mention the final calculated payout amount in your recommendation."
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
        self._publish(job_id, "agent_complete", {"agent": self.name ,"input_tokens": stream.input_tokens, "output_tokens": stream.output_tokens})
        
        return AgentOutput(
            agent_name=self.name,
            result={"payout": payout_dict, "anomaly": anomaly_result.output, "recommendation_narrative": full_text},
            tool_calls=["calculate_payout", "detect_anomaly"],
            input_tokens=stream.input_tokens,
            output_tokens=stream.output_tokens,
        )