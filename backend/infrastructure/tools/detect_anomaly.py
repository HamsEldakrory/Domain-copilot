from django.db.models import Q

from domain.ports.tool import Tool, ToolResult
from infrastructure.persistence.models import Claim, PolicyVersion


class DetectAnomalyTool(Tool):
    name = "detect_anomaly"
    description = "Flag rule-based anomalies: claim date outside policy period, duplicate claim."

    def run(self, claim_id: str, claimed_amount: float | None = None) -> ToolResult:
        try:
            claim = Claim.objects.select_related("policy_version__policy").get(id=claim_id)
        except Claim.DoesNotExist:
            return ToolResult(tool_name=self.name, error=f"Claim {claim_id} not found")

        flags = []
        pv = claim.policy_version

        # Find the correct version covering the claim date (same logic as GetPolicyVersionTool)
        if pv:
            correct_version = (
                PolicyVersion.objects.filter(
                    policy=pv.policy,
                    effective_from__lte=claim.claim_date,
                )
                .filter(Q(effective_to__gte=claim.claim_date) | Q(effective_to__isnull=True))
                .order_by("-effective_from")
                .first()
            )
            if not correct_version:
                flags.append("claim_date_outside_policy_period")

        duplicate_count = Claim.objects.filter(
            client_id=claim.client_id,
            policy_version_id=claim.policy_version_id,
            claim_date=claim.claim_date,
        ).exclude(id=claim.id).count()
        if duplicate_count > 0:
            flags.append("possible_duplicate_claim")
        return ToolResult(tool_name=self.name, output={"flags": flags, "anomaly_detected": len(flags) > 0})