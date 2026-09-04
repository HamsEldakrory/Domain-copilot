from django.db import IntegrityError, transaction
from django.utils import timezone

from domain.ports.agent_run_recorder import AgentRunRecorder
from domain.ports.job_event_publisher import JobEventPublisher
from infrastructure.persistence.models import AgentRun, Job, JobStep


class DjangoAgentRunRecorder(AgentRunRecorder):
    def __init__(self, existing_job_id: str | None = None, event_publisher: JobEventPublisher | None = None):
        self._existing_job_id = existing_job_id
        self._event_publisher = event_publisher

    def start_job(self, claim_id: str) -> str:
        if self._existing_job_id:
            return self._existing_job_id
        job = Job.objects.create(claim_id=claim_id, status="RUNNING")
        return str(job.id)

    def record_agent_run(self, job_id, agent_name, input_data, output_data, input_tokens=0, output_tokens=0, correlation_id=None):
        AgentRun.objects.create(
            job_id=job_id, agent_name=agent_name, input_data=input_data, output_data=output_data,
            input_tokens=input_tokens, output_tokens=output_tokens, correlation_id=correlation_id or "",
        )
    def update_job_status(self, job_id: str, status: str) -> None:
        Job.objects.filter(id=job_id).update(status=status)
        if self._event_publisher:
            self._event_publisher.publish(job_id, "status", {"status": status})

    def complete_job(self, job_id: str) -> None:
        Job.objects.filter(id=job_id).update(status="COMPLETED")
        if self._event_publisher:
            self._event_publisher.publish(job_id, "status", {"status": "COMPLETED"})

    def start_or_resume_step(self, job_id: str, step_name: str) -> tuple[str, dict | None]:
        try:
            with transaction.atomic():
                JobStep.objects.create(job_id=job_id, name=step_name, status="RUNNING", started_at=timezone.now())
            return "CLAIMED", None
        except IntegrityError:
            pass

        with transaction.atomic():
            step = JobStep.objects.select_for_update().get(job_id=job_id, name=step_name)

            if step.status == "COMPLETED":
                existing_run = (
                    AgentRun.objects.filter(job_id=job_id, agent_name=step_name)
                    .order_by("-created_at").first()
                )
                return "COMPLETED", (existing_run.output_data if existing_run else {})

            if step.status == "RUNNING":
                return "ALREADY_RUNNING", None

            step.status = "RUNNING"
            step.started_at = timezone.now()
            step.save(update_fields=["status", "started_at"])
            return "CLAIMED", None

    def complete_step(self, job_id: str, step_name: str, output: dict) -> None:
        JobStep.objects.filter(job_id=job_id, name=step_name).update(status="COMPLETED", finished_at=timezone.now())

    def is_cancelled(self, job_id: str) -> bool:
        job = Job.objects.filter(id=job_id).only("status").first()
        return job.status == "CANCELLED" if job else False