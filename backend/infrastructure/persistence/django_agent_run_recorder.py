from django.utils import timezone
from domain.ports.agent_run_recorder import AgentRunRecorder
from domain.ports.job_event_publisher import JobEventPublisher
from infrastructure.persistence.models import Job, AgentRun,JobStep
class DjangoAgentRunRecorder(AgentRunRecorder):
    def __init__(self, existing_job_id: str | None = None,event_publisher: JobEventPublisher | None = None):
        self._existing_job_id = existing_job_id
        self._event_publisher = event_publisher

    def start_job(self, claim_id: str) -> str:
        if self._existing_job_id:
            return self._existing_job_id
        job = Job.objects.create(claim_id=claim_id, status="RUNNING")
        return str(job.id)


    def record_agent_run(self, job_id, agent_name, input_data, output_data):
        AgentRun.objects.create(job_id=job_id, agent_name=agent_name, input_data=input_data, output_data=output_data)

    def complete_step(self, job_id: str, step_name: str, output: dict) -> None:
        JobStep.objects.filter(job_id=job_id, name=step_name).update(status="COMPLETED", finished_at=timezone.now())
    def complete_job(self, job_id: str) -> None:
        Job.objects.filter(id=job_id).update(
            status="COMPLETED",
        )

        if self._event_publisher:
            self._event_publisher.publish(
                job_id,
                "status",
                {"status": "COMPLETED"},
            )

    
    def update_job_status(self, job_id: str, status: str) -> None:
        Job.objects.filter(id=job_id).update(status=status)
        if self._event_publisher:
            self._event_publisher.publish(job_id, "status", {"status": status})

    def start_or_resume_step(self, job_id: str, step_name: str) -> tuple[str, dict | None]:
        step, created = JobStep.objects.get_or_create(
            job_id=job_id, name=step_name, defaults={"status": "RUNNING", "started_at": timezone.now()},
        )
        if not created and step.status == "COMPLETED":
            existing_run = AgentRun.objects.filter(job_id=job_id, agent_name=step_name).order_by("-created_at").first()
            return "COMPLETED", (existing_run.output_data if existing_run else {})
        if not created:
            JobStep.objects.filter(id=step.id).update(status="RUNNING", started_at=timezone.now())
        return "RUNNING", None
    
    def is_cancelled(self, job_id: str) -> bool:
        job = Job.objects.filter(id=job_id).only("status").first()
        return job.status == "CANCELLED" if job else False
