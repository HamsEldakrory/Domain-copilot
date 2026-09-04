from abc import ABC, abstractmethod


class CancellationChecker(ABC):
    @abstractmethod
    def is_cancelled(self, job_id: str) -> bool:
        raise NotImplementedError