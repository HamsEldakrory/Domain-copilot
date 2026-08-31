from application.use_cases.get_run_trace import TraceEntry
from infrastructure.persistence.models import AgentRun, AuditLog, Job

class DjangoTraceRepository:
    def get_trace(self, job_id: str) -> list[TraceEntry]:
        entries = []
        for run in AgentRun.objects.filter(job_id=job_id).order_by("created_at"):
            entries.append(TraceEntry(
                timestamp=str(run.created_at), kind="agent_run",
                detail={"agent_name": run.agent_name, "input": run.input_data, "output": run.output_data},
            ))

        for log in AuditLog.objects.filter(job_id=job_id).order_by("created_at"):
            entries.append(TraceEntry(
                timestamp=str(log.created_at), kind="audit",
                detail={"actor_id": str(log.actor_id) if log.actor_id else None, "action": log.action, "metadata": log.metadata},
            ))

        entries.sort(key=lambda e: e.timestamp)
        return entries