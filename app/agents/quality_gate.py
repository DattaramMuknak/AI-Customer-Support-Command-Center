"""
Quality Gate — runs AFTER knowledge/support/billing agents.
If confidence is too low, automatically reroutes to escalation instead of
returning an unreliable answer to the customer.
"""

from app.agents.state import AgentState
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

LOW_CONFIDENCE_THRESHOLD = (
    settings.similarity_threshold - 0.15
)  # a bit more lenient than retrieval cutoff


def quality_gate_node(state: AgentState) -> AgentState:
    """Pass-through node that just decides whether to escalate next."""
    confidence = state.get("confidence_score", 0.0)
    needs_escalation = confidence < LOW_CONFIDENCE_THRESHOLD and not state.get(
        "escalated", False
    )

    trace = state.get("trace", [])
    trace.append(
        {
            "agent": "quality_gate",
            "action": "evaluate_confidence",
            "detail": f"confidence={confidence}, needs_escalation={needs_escalation}",
        }
    )

    return {**state, "trace": trace, "_needs_escalation": needs_escalation}


def quality_selector(state: AgentState) -> str:
    """Conditional edge: route to escalation if confidence too low, else end."""
    if state.get("_needs_escalation"):
        return "escalation"
    return "end"
