import json

import pytest

from app.config import Settings
from app.llm import DeterministicDemoLLM, OpenAIProvider, build_llm


@pytest.mark.asyncio
async def test_demo_llm_is_stable_and_keyless() -> None:
    llm = build_llm(Settings(llm_provider="demo", openai_api_key=None))
    assert isinstance(llm, DeterministicDemoLLM)
    first = await llm.complete("research", {"b": 2, "a": 1})
    second = await llm.complete("research", {"a": 1, "b": 2})
    assert first == second
    assert json.loads(first)["provider"] == "demo"


def test_openai_provider_requires_key() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        OpenAIProvider(Settings(llm_provider="openai", openai_api_key=None))


def test_openai_configuration_without_key_falls_back_to_demo() -> None:
    llm = build_llm(Settings(llm_provider="openai", openai_api_key=None))
    assert isinstance(llm, DeterministicDemoLLM)
