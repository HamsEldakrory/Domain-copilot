# Composition root.
# This is the one place where concrete Infrastructure implementations
# get wired to the abstract Ports defined in domain/ports. Application
# and Domain code never see this file — they only ever see the Ports.
import os
from application.container import container
from domain.ports.llm_provider import LLMProvider
from infrastructure.llm.openai_provider import OpenAIProvider
from infrastructure.llm.ollama_provider import OllamaProvider

PROVIDERS = {
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}
def _build_llm_provider():
    primary_name = os.getenv("LLM_PROVIDER", "openai")
    fallback_name = os.getenv("LLM_FALLBACK_PROVIDER", "ollama")
    primary_cls = PROVIDERS.get(primary_name, OpenAIProvider)
    fallback_cls = PROVIDERS.get(fallback_name, OllamaProvider)
    try:
        return primary_cls()
    except Exception:
        return fallback_cls()
    
def build_embedding_provider():
    name = os.getenv("EMBEDDING_PROVIDER", "openai")
    if name not in PROVIDERS:
        raise ValueError(
            f"EMBEDDING_PROVIDER='{name}' is not a recognized provider. "
            f"Valid options: {list(PROVIDERS.keys())}"
        )
    return PROVIDERS[name]()

def bootstrap():
    container.register(LLMProvider, _build_llm_provider)