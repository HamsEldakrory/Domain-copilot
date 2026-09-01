from abc import ABC, abstractmethod


class JobEventPublisher(ABC):

    @abstractmethod
    def publish(self, job_id: str, event_type: str, data: dict) -> None:
        raise NotImplementedError