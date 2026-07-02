import json
from abc import ABC, abstractmethod
from typing import Any

import httpx

from .config import Settings


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, system: str, payload: dict[str, Any]) -> str: ...


class DeterministicDemoLLM(LLMProvider):
    async def complete(self, system: str, payload: dict[str, Any]) -> str:
        """Stable JSON rendering used by tests and credential-free deployments."""
        if system == "committee-chair-synthesis":
            return (
                f"Evidence-weighted council score {payload['score']}/100 is "
                f"{payload['consensus'].lower()}; the valuation range and declared "
                "data gaps matter more than a point estimate."
            )
        return json.dumps(
            {"provider": "demo", "system": system, "payload": payload},
            sort_keys=True,
            ensure_ascii=False,
        )


class OpenAIProvider(LLMProvider):
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model

    async def complete(self, system: str, payload: dict[str, Any]) -> str:
        instructions = (
            "You are an investment committee chair. Synthesize only the supplied "
            "structured evidence in at most two sentences. Separate uncertainty from "
            "fact and never give personalized investment advice."
            if system == "committee-chair-synthesis"
            else system
        )
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "instructions": instructions,
                    "input": json.dumps(payload, ensure_ascii=False),
                },
            )
            response.raise_for_status()
        body = response.json()
        if "output_text" in body:
            return str(body["output_text"])
        for item in body.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return str(content.get("text", ""))
        raise RuntimeError("OpenAI response did not contain output text")


def build_llm(settings: Settings) -> LLMProvider:
    if settings.llm_provider.lower() == "openai" and settings.openai_api_key:
        return OpenAIProvider(settings)
    return DeterministicDemoLLM()
