from domain.ports.cancellation_checker import CancellationChecker
from infrastructure.persistence.models import Job


class DjangoCancellationChecker(CancellationChecker):
    def is_cancelled(self, job_id: str) -> bool:
        job = Job.objects.filter(id=job_id).only("status").first()
        return job.status == "CANCELLED" if job else False