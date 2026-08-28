from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterator

@dataclass
class Message:
    role: str     
    content: str

@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict  


@dataclass
class ToolCall:
    name: str
    arguments: dict


@dataclass
class CompletionResult:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0


class LLMProvider(ABC):
    # Port (interface) for any LLM provider. Application/domain code depends
    # only on this abstraction - never on a specific SDK like openai directly. 
    # Concrete implementations in  infrastructure/llm/ and satisfy this contract.

    @abstractmethod
    def completion(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> CompletionResult:
        #Send messages and get back a single,complete response.
        raise NotImplementedError

    @abstractmethod
    def stream_completion(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> Iterator[str]:
        #Same as completion, but yields the response incrementally (token by token or chunk by chunk) instead of all at once.
        raise NotImplementedError
    @abstractmethod
    def embeddings(self, texts: list[str]) -> list[list[float]]:
        #Return an embedding vector for each input text, same order.
        raise NotImplementedError