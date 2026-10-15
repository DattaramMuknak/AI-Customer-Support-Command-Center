"""
Evaluation metrics — scores agent responses along multiple dimensions
for offline evaluation and continuous quality monitoring.

Uses a mix of cheap heuristics (fast, free, always-on) and LLM-as-judge
(slower, used for deeper/offline evaluation runs).
"""

import json
import re

from app.core.logging import get_logger
from app.services.llm_client import get_llm_client

logger = get_logger(__name__)


# ---------- Heuristic metrics (no LLM call, fast, run on every request) ----------


def response_length_score(
    response: str, min_words: int = 10, max_words: int = 300
) -> float:
    """Penalize responses that are too short (unhelpful) or too long (verbose)."""
    word_count = len(response.split())
    if word_count < min_words:
        return word_count / min_words
    if word_count > max_words:
        return max(0.5, 1 - (word_count - max_words) / max_words)
    return 1.0


def groundedness_score(response: str, context: str) -> float:
    """
    Cheap proxy for hallucination risk: what fraction of meaningful response
    words also appear in the retrieved context. Not perfect, but a fast signal.
    """
    if (
        not context
        or context.strip() == "No relevant knowledge base articles were found."
    ):
        return 0.5  # neutral — no context to ground against

    stopwords = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "to",
        "of",
        "and",
        "in",
        "for",
        "on",
        "with",
        "you",
        "your",
    }
    response_words = {
        w.lower().strip(".,!?")
        for w in response.split()
        if w.lower() not in stopwords and len(w) > 3
    }
    context_words = {w.lower().strip(".,!?") for w in context.split()}

    if not response_words:
        return 0.0

    overlap = response_words & context_words
    return round(len(overlap) / len(response_words), 3)


def has_unsafe_patterns(response: str) -> bool:
    """Flag obviously problematic patterns (placeholder for more advanced safety checks)."""
    red_flags = [
        r"i (don't|do not) know",
        r"as an ai",
        r"i cannot help",
    ]
    text = response.lower()
    return any(re.search(pattern, text) for pattern in red_flags)


# ---------- LLM-as-judge metrics (slower, used in offline eval batches) ----------

JUDGE_SYSTEM_PROMPT = """You are an expert evaluator for a customer support AI system.
Score the AGENT RESPONSE on a scale of 1-5 for each dimension below, given the
USER QUESTION and the KNOWLEDGE BASE CONTEXT that was available to the agent.

Dimensions:
- relevance: Does the response actually address the user's question?
- correctness: Is the response factually consistent with the provided context?
- helpfulness: Would a real customer find this response actionable and clear?
- tone: Is the tone professional, empathetic, and appropriate?

Respond ONLY with valid JSON, no other text:
{"relevance": <1-5>, "correctness": <1-5>, "helpfulness": <1-5>, "tone": <1-5>, "overall_comment": "<one sentence>"}
"""


def llm_judge_score(user_question: str, context: str, agent_response: str) -> dict:
    """
    Use the LLM itself as a judge to score response quality.
    Used in offline/batch evaluation — too slow/costly to run on every live request.
    """
    llm = get_llm_client()
    prompt = (
        f"USER QUESTION:\n{user_question}\n\n"
        f"KNOWLEDGE BASE CONTEXT:\n{context}\n\n"
        f"AGENT RESPONSE:\n{agent_response}"
    )

    raw, _ = llm.generate(
        system_prompt=JUDGE_SYSTEM_PROMPT,
        user_prompt=prompt,
        temperature=0.0,
        max_tokens=200,
    )

    try:
        cleaned = raw.strip().strip("`").removeprefix("json").strip()
        scores = json.loads(cleaned)
    except (json.JSONDecodeError, AttributeError):
        logger.warning("llm_judge_parse_failed", raw=raw)
        scores = {
            "relevance": 0,
            "correctness": 0,
            "helpfulness": 0,
            "tone": 0,
            "overall_comment": "parse_failed",
        }

    return scores


def compute_all_heuristics(response: str, context: str) -> dict:
    """Run all fast heuristic metrics and return as a dict (used on every live request)."""
    return {
        "length_score": round(response_length_score(response), 3),
        "groundedness_score": groundedness_score(response, context),
        "has_unsafe_pattern": has_unsafe_patterns(response),
    }
