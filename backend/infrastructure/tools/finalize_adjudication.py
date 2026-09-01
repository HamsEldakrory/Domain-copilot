from domain.ports.tool import Tool, ToolResult
from infrastructure.persistence.models import Claim, Decision


class FinalizeAdjudicationTool(Tool):
    name = "finalize_adjudication"
    description = "Persist the final adjudication decision. Requires prior human approval."

    def run(self, claim_id: str, job_id: str, approved_by: str | None, outcome: str, rationale: str) -> ToolResult:
        if not approved_by:
            return ToolResult(tool_name=self.name, error="finalize_adjudication cannot run without approved_by")
        try:
            claim = Claim.objects.get(id=claim_id)
        except Claim.DoesNotExist:
            return ToolResult(tool_name=self.name, error=f"Claim {claim_id} not found")

        decision = Decision.objects.create(claim=claim, job_id=job_id, approved_by_id=approved_by, outcome=outcome, rationale=rationale)
        claim.status = "decided"
        claim.save(update_fields=["status"])
        return ToolResult(tool_name=self.name, output={"decision_id": str(decision.id), "outcome": outcome})