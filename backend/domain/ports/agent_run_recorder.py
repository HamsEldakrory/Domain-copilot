from abc import ABC, abstractmethod


class AgentRunRecorder(ABC):
    @abstractmethod
    def start_job(self, claim_id: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def record_agent_run(self, job_id, agent_name, input_data, output_data, input_tokens=0, output_tokens=0, correlation_id=None) -> None:
        raise NotImplementedError
    @abstractmethod
    def complete_job(self, job_id: str) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def update_job_status(self, job_id, status: str) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def start_or_resume_step(self, job_id: str, step_name: str) -> tuple[str, dict | None]:
        raise NotImplementedError
    
    @abstractmethod
    def complete_step(self, job_id: str, step_name: str, output: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_cancelled(self, job_id: str) -> bool:
        raise NotImplementedError