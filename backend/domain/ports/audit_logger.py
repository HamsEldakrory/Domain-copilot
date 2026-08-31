from abc import ABC, abstractmethod

class AuditLogger(ABC):
    @abstractmethod
    def log(self, job_id: str, actor_id: str | None, action: str, metadata: dict) -> None:
        raise NotImplementedError