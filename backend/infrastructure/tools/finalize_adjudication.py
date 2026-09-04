from domain.ports.tool import Tool, ToolResult
from infrastructure.persistence.models import Claim, Decision


class FinalizeAdjudicationTool(Tool):
    name = "finalize_adjudication"
    description = "Persist the final adjudication decision. Requires prior human approval."

    def run(self, claim_id: str, job_id: str, approved_by: str | None, outcome: str, rationale: str, final_payout: float | None = None) -> ToolResult:
        if not approved_by:
            return ToolResult(tool_name=self.name, error="finalize_adjudication cannot run without approved_by")
        if final_payout is not None:
            final_payout = float(final_payout)
        try:
            claim = Claim.objects.get(id=claim_id)
        except Claim.DoesNotExist:
            return ToolResult(tool_name=self.name, error=f"Claim {claim_id} not found")

        decision = Decision.objects.create(claim=claim, job_id=job_id, approved_by_id=approved_by, outcome=outcome, rationale=rationale, final_payout=final_payout)
        claim.status = "decided"
        if final_payout is not None:
            claim.final_payout = final_payout
        claim.save(update_fields=["status", "final_payout"] if final_payout is not None else ["status"])
        return ToolResult(tool_name=self.name, output={"decision_id": str(decision.id), "outcome": outcome})