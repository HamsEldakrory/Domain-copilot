from abc import ABC, abstractmethod
from dataclasses import dataclass, field

@dataclass
class ToolResult:
    tool_name: str
    output: dict = field(default_factory=dict)
    error: str | None = None


class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, **kwargs) -> ToolResult:
        raise NotImplementedError