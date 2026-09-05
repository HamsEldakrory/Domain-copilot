import logging

from domain.ports.llm_provider import CompletionResult, LLMProvider, Message, ToolDefinition

logger = logging.getLogger(__name__)


def _is_quota_error(exc: Exception) -> bool:
    """Return True when the OpenAI error means credits / quota are exhausted.

    openai>=1.x raises openai.RateLimitError (HTTP 429) when quota is exhausted
    and openai.AuthenticationError (HTTP 401) when billing is inactive.
    In some library versions the base openai.OpenAIError is raised instead;
    we fall through to the HTTP status-code check to catch that case too.
    """
    try:
        import openai as _openai
        # Use early-return True so the status_code fallback still runs when
        # the exception is the base OpenAIError (not a RateLimitError subclass).
        if isinstance(exc, (_openai.RateLimitError, _openai.AuthenticationError)):
            return True
    except AttributeError:
        pass
    # Fallback: check HTTP status code present on the exception object.
    status_code = getattr(exc, "http_status", None) or getattr(exc, "status_code", None)
    return status_code in (401, 402, 429)


class _FallbackStream:
    """
    Wraps a primary token stream and switches to a fallback provider's stream
    when a quota/billing error is raised *during iteration*.

    This is necessary because OpenAI's streaming client raises RateLimitError on
    the first next() call (inside the agent's for-loop), not during
    stream_completion() itself. So the fallback must live inside the iterator.
    """

    def __init__(self, primary_stream, fallback_fn):
        """
        primary_stream : the stream object returned by the primary provider
        fallback_fn    : callable() -> new stream from the fallback provider
        """
        self._stream = primary_stream
        self._fallback_fn = fallback_fn
        self._switched = False
        self.input_tokens = 0
        self.output_tokens = 0

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            try:
                token = next(self._stream)
                # Mirror token counts from whichever stream is active
                self.input_tokens = getattr(self._stream, "input_tokens", 0) or 0
                self.output_tokens = getattr(self._stream, "output_tokens", 0) or 0
                return token
            except StopIteration:
                raise
            except Exception as exc:
                if not self._switched and _is_quota_error(exc):
                    logger.warning(
                        "Primary LLM stream failed with quota/billing error (%s). "
                        "Switching to fallback provider stream.",
                        exc,
                    )
                    try:
                        self._stream.close()
                    except Exception:
                        pass
                    self._stream = self._fallback_fn()
                    self._switched = True
                    # Loop back and pull from the fallback stream
                    continue
                raise

    def close(self):
        try:
            self._stream.close()
        except Exception:
            pass


class FallbackCompletionProvider(LLMProvider):
    """
    Wraps a primary LLM provider and transparently switches to a fallback
    provider when the primary raises a quota / billing error — both at
    completion() call time and during stream iteration.
    """

    def __init__(self, primary: LLMProvider, fallback: LLMProvider):
        self._primary = primary
        self._fallback = fallback

    def completion(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> CompletionResult:
        """Non-streaming completion — error fires immediately on the call."""
        try:
            return self._primary.completion(messages, tools)
        except Exception as exc:
            if _is_quota_error(exc):
                logger.warning(
                    "Primary LLM completion failed with quota/billing error (%s). "
                    "Retrying with fallback provider.",
                    exc,
                )
                return self._fallback.completion(messages, tools)
            raise

    def stream_completion(self, messages, tools=None):
        """
        Streaming completion with two-layer fallback:

        1. Call-time errors (e.g. openai raises 429 synchronously inside
           .create() before returning a stream iterator): caught here and
           redirected straight to the fallback provider.
        2. Iteration-time errors (e.g. RateLimitError on the first next()
           inside the caller's for-loop): caught transparently by
           _FallbackStream during iteration.
        """
        try:
            primary_stream = self._primary.stream_completion(messages, tools)
        except Exception as exc:
            if _is_quota_error(exc):
                logger.warning(
                    "Primary LLM stream_completion raised quota/billing error at "
                    "call time (%s). Switching to fallback provider.",
                    exc,
                )
                return self._fallback.stream_completion(messages, tools)
            raise
        return _FallbackStream(
            primary_stream=primary_stream,
            fallback_fn=lambda: self._fallback.stream_completion(messages, tools),
        )

    def embeddings(self, texts: list[str]) -> list[list[float]]:
        try:
            return self._primary.embeddings(texts)
        except Exception as exc:
            if _is_quota_error(exc):
                logger.warning(
                    "Primary LLM embeddings failed with quota/billing error (%s). "
                    "Retrying with fallback provider.",
                    exc,
                )
                return self._fallback.embeddings(texts)
            raise
