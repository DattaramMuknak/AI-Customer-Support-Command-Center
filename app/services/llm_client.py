"""
Groq LLM client — wraps the Groq API with retry/fallback logic for
fast, low-latency inference used across all agents.
"""

import time

from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GroqLLMClient:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)
        self.primary_model = settings.groq_model
        self.fallback_model = settings.groq_fallback_model

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8)
    )
    def _call(
        self, model: str, messages: list[dict], temperature: float, max_tokens: int
    ) -> str:
        completion = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return completion.choices[0].message.content

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> tuple[str, int]:
        """
        Generate a response. Returns (response_text, latency_ms).
        Falls back to the smaller/faster model if the primary model fails.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        start = time.time()
        try:
            text = self._call(self.primary_model, messages, temperature, max_tokens)
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "primary_model_failed_falling_back",
                error=str(e),
                fallback=self.fallback_model,
            )
            text = self._call(self.fallback_model, messages, temperature, max_tokens)

        latency_ms = int((time.time() - start) * 1000)
        return text, latency_ms


_llm_instance: GroqLLMClient | None = None


def get_llm_client() -> GroqLLMClient:
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = GroqLLMClient()
    return _llm_instance
