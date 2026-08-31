from abc import ABC, abstractmethod
from dataclasses import dataclass, field

@dataclass
class AgentInput:
    claim_id: str
    context: dict = field(default_factory=dict)


@dataclass
class AgentOutput:
    agent_name: str
    result: dict
    tool_calls: list[str] = field(default_factory=list)
    citations: list[dict] = field(default_factory=list)

class Agent(ABC):
    name: str
    @abstractmethod
    def run(self, input: AgentInput) -> AgentOutput:
        raise NotImplementedError