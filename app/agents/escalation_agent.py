"""
Escalation Agent — handles cases routed as needing human attention:
frustrated/angry customers, legal threats, repeated unresolved issues,
or explicit requests for a human. Produces an empathetic holding response
and flags the ticket for human handoff.
"""

from app.agents.state import AgentState
from app.core.logging import get_logger
from app.services.llm_client import get_llm_client

logger = get_logger(__name__)

ESCALATION_SYSTEM_PROMPT = """You are a senior customer support agent handling an
escalated case. The customer may be frustrated or have an unresolved issue.

Your job:
1. Acknowledge their frustration genuinely and briefly (1-2 sentences max).
2. Confirm their issue is being escalated to a human specialist.
3. Set a clear expectation (e.g., "within 24 hours" — do not invent specific times/SLAs beyond this).
4. Do NOT try to solve the technical/billing issue yourself — that's for the human agent.

Keep the tone calm, respectful, and reassuring. Keep it short — under 100 words.
"""


def escalation_node(state: AgentState) -> AgentState:
    llm = get_llm_client()
    query = state["user_message"]

    response_text, latency = llm.generate(
        system_prompt=ESCALATION_SYSTEM_PROMPT,
        user_prompt=query,
        temperature=0.4,
        max_tokens=200,
    )

    trace = state.get("trace", [])
    trace.append(
        {
            "agent": "escalation",
            "action": "handoff_to_human",
            "detail": "ticket flagged",
        }
    )

    logger.info("escalation_triggered", ticket_id=state.get("ticket_id"))

    return {
        **state,
        "final_response": response_text,
        "agent_used": "escalation_agent",
        "confidence_score": 1.0,  # certainty that this needs human attention
        "escalated": True,
        "escalation_reason": state.get("category", "unspecified"),
        "trace": trace,
        "latency_ms": state.get("latency_ms", 0) + latency,
    }
