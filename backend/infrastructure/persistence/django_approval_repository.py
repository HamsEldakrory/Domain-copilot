from domain.ports.approval_repository import ApprovalRepository
from infrastructure.persistence.models import Approval, Job

class DjangoApprovalRepository(ApprovalRepository):
    def record_approval(self, claim_id, job_id, approver_id, status, comment):
        Approval.objects.create(
            claim_id=claim_id, job_id=job_id, approver_id=approver_id, status=status, comment=comment,
        )

    def get_job_status(self, job_id):
        job = Job.objects.filter(id=job_id).first()
        return job.status if job else None

    def update_job_status(self, job_id, status):
        Job.objects.filter(id=job_id).update(status=status)