from dataclasses import dataclass


@dataclass
class TraceEntry:
    timestamp: str
    kind: str  # "agent_run" | "audit" | "approval" | "decision"
    detail: dict

class GetRunTraceUseCase:
    def __init__(self, trace_repository):
        self._repo = trace_repository

    def execute(self, job_id: str) -> list[TraceEntry]:
        return self._repo.get_trace(job_id)