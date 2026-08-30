from domain.ports.tool import Tool, ToolResult
from infrastructure.persistence.models import Claim
class DetectAnomalyTool(Tool):
    name = "detect_anomaly"
    description = "Flag rule-based anomalies: claim date outside policy period, duplicate claim."

    def run(self, claim_id: str, claimed_amount: float | None = None) -> ToolResult:
        try:
            claim = Claim.objects.select_related("policy_version").get(id=claim_id)
        except Claim.DoesNotExist:
            return ToolResult(tool_name=self.name, error=f"Claim {claim_id} not found")

        flags = []
        pv = claim.policy_version
        if pv and (claim.claim_date < pv.effective_from or (pv.effective_to and claim.claim_date > pv.effective_to)):
            flags.append("claim_date_outside_policy_period")

        duplicate_count = Claim.objects.filter(
            client_id=claim.client_id,
            policy_version_id=claim.policy_version_id,
            claim_date=claim.claim_date,
        ).exclude(id=claim.id).count()
        if duplicate_count > 0:
            flags.append("possible_duplicate_claim")
        return ToolResult(tool_name=self.name, output={"flags": flags, "anomaly_detected": len(flags) > 0})