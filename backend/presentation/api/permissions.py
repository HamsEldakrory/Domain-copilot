from rest_framework.permissions import BasePermission

from domain.policies.claim_access_policy import can_access_claim
from infrastructure.persistence.models import Claim, Job
class CanAccessClaim(BasePermission):

    message = "You do not have access to this claim."

    def _resolve_claim(self, request, view):
        claim_id = view.kwargs.get("claim_id")
        if not claim_id and request.method == "POST":
            claim_id = request.data.get("claim_id")

        if claim_id:
            return Claim.objects.filter(id=claim_id).first()

        job_id = view.kwargs.get("job_id")
        if job_id:
            job = Job.objects.filter(id=job_id).select_related("claim").first()
            return job.claim if job else None

        return None

    def has_permission(self, request, view):
        claim = self._resolve_claim(request, view)
        if not claim:
            return True  # let the view's own 404 handling take over
        return can_access_claim(
            user_role=getattr(request.user, "role", ""),
            user_id=str(request.user.id),
            claim_adjuster_id=str(claim.adjuster_id),
        )


class IsManager(BasePermission):

    message = "Only managers can perform this action."

    def has_permission(self, request, view):
        return getattr(request.user, "role", None) == "MANAGER"


class IsAdjuster(BasePermission):
    message = "Only adjusters can perform this action."
    def has_permission(self, request, view):
        return getattr(request.user, "role", None) == "ADJUSTER"
