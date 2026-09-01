import os
from openai import OpenAI

from domain.ports.llm_provider import (
    LLMProvider,
    Message,
    ToolDefinition,
    ToolCall,
    CompletionResult,
)


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self._model = model or os.getenv("OPENAI_MODEL")

    def _to_openai_messages(self, messages: list[Message]) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in messages]

    def _to_openai_tools(self, tools: list[ToolDefinition] | None) -> list[dict] | None:
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
        response = self._client.chat.completions.create(
            model=self._model,
            messages=self._to_openai_messages(messages),
            tools=self._to_openai_tools(tools),
        )
        choice = response.choices[0]
        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                import json
                tool_calls.append(
                    ToolCall(name=tc.function.name, arguments=json.loads(tc.function.arguments))
                )
        return CompletionResult(
            content=choice.message.content or "",
            tool_calls=tool_calls,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )

    def stream_completion(self, messages, tools=None):
        stream = self._client.chat.completions.create(
            model=self._model,
            messages=self._to_openai_messages(messages),
            tools=self._to_openai_tools(tools),
            stream=True,
        )
        try:
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
        finally:
            close = getattr(stream, "close", None)
            if close:
                close()

    def embeddings(self, texts: list[str]) -> list[list[float]]:
        embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL")
        response = self._client.embeddings.create(
            model=embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]