from domain.ports.agent_run_recorder import AgentRunRecorder
from infrastructure.persistence.models import Job, AgentRun
class DjangoAgentRunRecorder(AgentRunRecorder):
    def __init__(self, existing_job_id: str | None = None):
        self._existing_job_id = existing_job_id

    def start_job(self, claim_id: str) -> str:
        if self._existing_job_id:
            return self._existing_job_id
        job = Job.objects.create(claim_id=claim_id, status="RUNNING")
        return str(job.id)

    def record_agent_run(self, job_id, agent_name, input_data, output_data):
        AgentRun.objects.create(job_id=job_id, agent_name=agent_name, input_data=input_data, output_data=output_data)

    def complete_job(self, job_id: str) -> None:
        Job.objects.filter(id=job_id).update(status="COMPLETED")
    def update_job_status(self, job_id: str, status: str) -> None:
        Job.objects.filter(id=job_id).update(status=status)