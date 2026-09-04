import os

import ollama

from domain.ports.llm_provider import (
    CompletionResult,
    LLMProvider,
    Message,
    ToolCall,
    ToolDefinition,
)


class OllamaTokenStream:
    def __init__(self, raw_stream):
        self._raw_stream = raw_stream
        self.input_tokens = 0
        self.output_tokens = 0

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            chunk = next(self._raw_stream)
            done = getattr(chunk, "done", False)
            if done:
                self.input_tokens = getattr(chunk, "prompt_eval_count", 0) or 0
                self.output_tokens = getattr(chunk, "eval_count", 0) or 0
            message = getattr(chunk, "message", None)
            content = getattr(message, "content", None) if message else None
            if content:
                return content

    def close(self):
        close = getattr(self._raw_stream, "close", None)
        if close:
            close()

class OllamaProvider(LLMProvider):
    def __init__(self, model: str | None = None, embedding_model: str | None = None, host: str | None = None):
        self._model = model or os.getenv("OLLAMA_MODEL")
        self._embedding_model = embedding_model or os.getenv("OLLAMA_EMBEDDING_MODEL")
        self._client = ollama.Client(host=host or os.getenv("OLLAMA_HOST"))

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
    def stream_completion(self, messages, tools=None):
        raw_stream = self._client.chat(
            model=self._model,
            messages=self._to_ollama_messages(messages),
            stream=True,
        )
        return OllamaTokenStream(raw_stream)
    def embeddings(self, texts: list[str]) -> list[list[float]]:
        return [
            self._client.embeddings(model=self._embedding_model, prompt=text)["embedding"]
            for text in texts
        ]