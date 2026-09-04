from django.db.models import Q

from domain.ports.tool import Tool, ToolResult
from infrastructure.persistence.models import Claim, PolicyVersion


class GetPolicyVersionTool(Tool):
    name = "get_policy_version"
    description = "Resolve the policy version applicable to a claim's loss date."

    def run(self, claim_id: str) -> ToolResult:
        try:
            claim = Claim.objects.select_related("policy_version__policy").get(id=claim_id)
        except Claim.DoesNotExist:
            return ToolResult(tool_name=self.name, error=f"Claim {claim_id} not found")

        if not claim.policy_version:
            return ToolResult(tool_name=self.name, error="Claim has no associated policy")
        policy = claim.policy_version.policy
        correct_version = (
            PolicyVersion.objects.filter(policy=policy, effective_from__lte=claim.claim_date)
            .filter(Q(effective_to__gte=claim.claim_date) | Q(effective_to__isnull=True))
            .order_by("-effective_from")
            .first()
        )

        if not correct_version:
            return ToolResult(
                tool_name=self.name,
                error=f"No policy version found covering claim date {claim.claim_date}",
            )

        return ToolResult(
            tool_name=self.name,
            output={
                "policy_version_id": str(correct_version.id),
                "version_label": correct_version.version,
                "effective_from": str(correct_version.effective_from),
                "effective_to": str(correct_version.effective_to) if correct_version.effective_to else None,
                "version_mismatch_detected": str(correct_version.id) != str(claim.policy_version_id),
            },
        )