"""
Shared agent state — passed between nodes in the LangGraph state graph.
Every agent reads from and writes to this single state object.
"""

from typing import TypedDict


class AgentState(TypedDict, total=False):
    # --- Input ---
    ticket_id: str
    user_message: str
    conversation_history: list[dict]  # [{role, content}, ...]

    # --- Routing ---
    route: str  # "knowledge" | "support" | "escalation" | "billing"
    intent: str
    category: str

    # --- RAG ---
    retrieved_context: str
    sources: list[str]

    # --- Output ---
    final_response: str
    agent_used: str
    confidence_score: float
    escalated: bool
    escalation_reason: str | None

    # --- Observability ---
    latency_ms: int
    trace: list[dict]  # list of {agent, action, detail} for debugging/MLflow
