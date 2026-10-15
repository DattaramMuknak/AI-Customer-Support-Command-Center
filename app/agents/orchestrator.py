"""
Agent Orchestrator — builds and compiles the LangGraph StateGraph wiring
together: Router -> {Knowledge, Support, Billing, Escalation} -> Quality Gate -> Escalation/End

This is the single entry point the API layer calls to run the full
multi-agent pipeline for a user message.
"""

import time

from langgraph.graph import END, StateGraph

from app.agents.billing_agent import billing_node
from app.agents.escalation_agent import escalation_node
from app.agents.knowledge_agent import knowledge_node
from app.agents.quality_gate import quality_gate_node, quality_selector
from app.agents.router_agent import route_selector, router_node
from app.agents.state import AgentState
from app.agents.support_agent import support_node
from app.core.logging import get_logger

logger = get_logger(__name__)


def build_agent_graph():
    """Construct and compile the LangGraph state machine for the support pipeline."""
    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("router", router_node)
    graph.add_node("knowledge", knowledge_node)
    graph.add_node("support", support_node)
    graph.add_node("billing", billing_node)
    graph.add_node("escalation", escalation_node)
    graph.add_node("quality_gate", quality_gate_node)

    # Entry point
    graph.set_entry_point("router")

    # Router decides which specialized agent handles the query
    graph.add_conditional_edges(
        "router",
        route_selector,
        {
            "knowledge": "knowledge",
            "support": "support",
            "billing": "billing",
            "escalation": "escalation",
        },
    )

    # Specialized agents (except escalation) go through the quality gate
    graph.add_edge("knowledge", "quality_gate")
    graph.add_edge("support", "quality_gate")
    graph.add_edge("billing", "quality_gate")

    # Quality gate either ends or reroutes to escalation
    graph.add_conditional_edges(
        "quality_gate",
        quality_selector,
        {
            "escalation": "escalation",
            "end": END,
        },
    )

    # Escalation is always a terminal node
    graph.add_edge("escalation", END)

    return graph.compile()


_compiled_graph = None


def get_agent_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_agent_graph()
    return _compiled_graph


def run_agent_pipeline(
    ticket_id: str, user_message: str, conversation_history: list[dict] | None = None
) -> AgentState:
    """
    Main entry point: runs the full multi-agent graph for a single user message
    and returns the final state including the response, agent used, confidence, etc.
    """
    graph = get_agent_graph()
    start = time.time()

    initial_state: AgentState = {
        "ticket_id": ticket_id,
        "user_message": user_message,
        "conversation_history": conversation_history or [],
        "trace": [],
        "latency_ms": 0,
    }

    final_state = graph.invoke(initial_state)
    total_latency = int((time.time() - start) * 1000)
    final_state["latency_ms"] = total_latency

    logger.info(
        "agent_pipeline_complete",
        ticket_id=ticket_id,
        agent_used=final_state.get("agent_used"),
        escalated=final_state.get("escalated"),
        latency_ms=total_latency,
    )

    return final_state
