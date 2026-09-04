from dataclasses import dataclass

from domain.job_states import JOB_TERMINAL_STATUSES as TERMINAL_STATUSES


@dataclass
class CancelJobResult:
    success: bool
    error: str | None = None

class CancelJobUseCase:
    def __init__(self, run_recorder, job_status_reader):
        self._run_recorder = run_recorder
        self._job_status_reader = job_status_reader
    def execute(self, job_id: str) -> CancelJobResult:
        current = self._job_status_reader.get_job_status(job_id)
        if current is None:
            return CancelJobResult(success=False, error="Job not found")
        if current in TERMINAL_STATUSES:
            return CancelJobResult(success=False, error=f"Cannot cancel a job in status {current}")
        self._run_recorder.update_job_status(job_id, "CANCELLED")
        return CancelJobResult(success=True)