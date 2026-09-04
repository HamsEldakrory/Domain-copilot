from unittest.mock import MagicMock

from django.test import TestCase

from infrastructure.llm.ollama_provider import OllamaTokenStream
from infrastructure.llm.openai_provider import OpenAITokenStream


def make_openai_chunk(content=None, usage=None):
    chunk = MagicMock()
    chunk.choices = [MagicMock(delta=MagicMock(content=content))] if content is not None else []
    chunk.usage = usage
    return chunk


class OpenAITokenStreamTests(TestCase):
    def test_real_usage_captured_from_final_chunk(self):
        usage = MagicMock(prompt_tokens=42, completion_tokens=17)
        raw = iter([
            make_openai_chunk(content="Hel"),
            make_openai_chunk(content="lo"),
            make_openai_chunk(content=None, usage=usage),  # final usage-only chunk
        ])
        stream = OpenAITokenStream(raw)
        tokens = list(stream)
        self.assertEqual("".join(tokens), "Hello")
        self.assertEqual(stream.input_tokens, 42)
        self.assertEqual(stream.output_tokens, 17)


class OllamaTokenStreamTests(TestCase):
    def test_real_usage_captured_from_done_chunk(self):
        def make_chunk(content=None, done=False, prompt_eval_count=0, eval_count=0):
            chunk = MagicMock()
            chunk.done = done
            chunk.prompt_eval_count = prompt_eval_count
            chunk.eval_count = eval_count
            chunk.message = MagicMock(content=content) if content else None
            return chunk

        raw = iter([
            make_chunk(content="Hi"),
            make_chunk(done=True, prompt_eval_count=30, eval_count=8),
        ])
        stream = OllamaTokenStream(raw)
        tokens = list(stream)
        self.assertEqual("".join(tokens), "Hi")
        self.assertEqual(stream.input_tokens, 30)
        self.assertEqual(stream.output_tokens, 8)