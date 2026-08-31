from abc import ABC, abstractmethod

class ApprovalRepository(ABC):
    @abstractmethod
    def record_approval(self, claim_id: str, approver_id: str, status: str, comment: str) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def update_job_status(self, job_id: str, status: str) -> None:
        raise NotImplementedError
    @abstractmethod
    def get_job_status(self, job_id: str) -> str | None:
        raise NotImplementedError