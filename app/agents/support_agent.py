"""
Support Agent — handles technical/account troubleshooting.
Uses RAG context PLUS a small set of "tools" (simulated account lookup,
diagnostic checks) to provide actionable troubleshooting steps.
"""

from app.agents.state import AgentState
from app.agents.tools import TOOL_REGISTRY, get_tool_descriptions
from app.core.logging import get_logger
from app.rag.retriever import get_retriever
from app.services.llm_client import get_llm_client

logger = get_logger(__name__)

SUPPORT_SYSTEM_PROMPT = """You are a technical support agent for a SaaS product.
You help users troubleshoot account and technical issues step by step.

You have access to the following tools (described below). If a tool would help
diagnose the issue, mention which tool you'd use and why, then continue with
general troubleshooting guidance using the knowledge base context provided.

Available tools:
{tools}

Knowledge Base Context:
{context}

Be empathetic, clear, and give concrete next steps. If the issue seems unresolved
after standard steps, recommend escalation to a human agent.
"""


def support_node(state: AgentState) -> AgentState:
    """Handle a technical support query, optionally invoking diagnostic tools."""
    retriever = get_retriever()
    llm = get_llm_client()

    query = state["user_message"]
    chunks = retriever.retrieve(query, top_k=4, category_filter="technical")
    context = retriever.format_context(chunks)
    tools_desc = get_tool_descriptions()

    # Simple heuristic tool invocation: check account status if relevant keywords appear
    tool_output = ""
    if any(
        kw in query.lower()
        for kw in ["account", "login", "locked", "access", "subscription"]
    ):
        result = TOOL_REGISTRY["check_account_status"](
            ticket_id=state.get("ticket_id", "unknown")
        )
        tool_output = f"\n\n[Tool Result — check_account_status]: {result}"

    system_prompt = SUPPORT_SYSTEM_PROMPT.format(tools=tools_desc, context=context)
    user_prompt = query + tool_output

    response_text, latency = llm.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.4,
        max_tokens=600,
    )

    avg_score = sum(c.score for c in chunks) / len(chunks) if chunks else 0.0
    sources = list({c.source for c in chunks})

    trace = state.get("trace", [])
    trace.append(
        {
            "agent": "support",
            "action": "troubleshoot",
            "detail": f"tool_used={bool(tool_output)}",
        }
    )

    return {
        **state,
        "retrieved_context": context,
        "sources": sources,
        "final_response": response_text,
        "agent_used": "support_agent",
        "confidence_score": round(avg_score, 3),
        "escalated": False,
        "trace": trace,
        "latency_ms": state.get("latency_ms", 0) + latency,
    }
