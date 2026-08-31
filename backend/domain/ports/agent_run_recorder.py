from abc import ABC, abstractmethod
class AgentRunRecorder(ABC):
    @abstractmethod
    def start_job(self, claim_id: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def record_agent_run(self, job_id: str, agent_name: str, input_data: dict, output_data: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    def complete_job(self, job_id: str) -> None:
        raise NotImplementedError
    @abstractmethod
    def update_job_status(self, job_id, status: str) -> None:
        raise NotImplementedError