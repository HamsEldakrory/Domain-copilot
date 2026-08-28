import os
import ollama

from domain.ports.llm_provider import (
    LLMProvider,
    Message,
    ToolDefinition,
    ToolCall,
    CompletionResult,
)

class OllamaProvider(LLMProvider):
    def __init__(self, model: str | None = None, host: str | None = None):
        self._model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self._client = ollama.Client(host=host or os.getenv("OLLAMA_HOST", "http://localhost:11434"))

    def _to_ollama_messages(self, messages: list[Message]) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in messages]

    def _to_ollama_tools(self, tools: list[ToolDefinition] | None) -> list[dict] | None:
        if not tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    def completion(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> CompletionResult:
        response = self._client.chat(
            model=self._model,
            messages=self._to_ollama_messages(messages),
            tools=self._to_ollama_tools(tools),
        )
        tool_calls = []
        if response.message.tool_calls:
            for tc in response.message.tool_calls:
                tool_calls.append(ToolCall(name=tc.function.name, arguments=tc.function.arguments))
        return CompletionResult(
            content=response.message.content or "",
            tool_calls=tool_calls,
            input_tokens=response.get("prompt_eval_count", 0),
            output_tokens=response.get("eval_count", 0),
        )
    def stream_completion(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ):
        stream = self._client.chat(
            model=self._model,
            messages=self._to_ollama_messages(messages),
            stream=True,
        )
        for chunk in stream:
            content = chunk.message.content
            if content:
                yield content

    def embeddings(self, texts: list[str]) -> list[list[float]]:
        return [
            self._client.embeddings(model=self._model, prompt=text)["embedding"]
            for text in texts
        ]