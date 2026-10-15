"""
Billing Agent — specialized agent for payment, refund, invoice, and
subscription-related queries. Uses billing tools + RAG context.
"""

import re

from app.agents.state import AgentState
from app.agents.tools import TOOL_REGISTRY, get_tool_descriptions
from app.core.logging import get_logger
from app.rag.retriever import get_retriever
from app.services.llm_client import get_llm_client

logger = get_logger(__name__)

BILLING_SYSTEM_PROMPT = """You are a billing support agent. You help with payments,
refunds, invoices, and subscription questions. Be precise about policy (refund
windows, billing cycles) using the knowledge base context. Never promise a refund
amount yourself — only confirm that a request has been filed via tools.

Available tools:
{tools}

Knowledge Base Context:
{context}
"""


def billing_node(state: AgentState) -> AgentState:
    retriever = get_retriever()
    llm = get_llm_client()

    query = state["user_message"]
    chunks = retriever.retrieve(query, top_k=4, category_filter="billing")
    context = retriever.format_context(chunks)
    tools_desc = get_tool_descriptions()

    tool_output = ""
    if any(kw in query.lower() for kw in ["refund", "money back", "charged"]):
        amount_match = re.search(r"\$?(\d+(?:\.\d{1,2})?)", query)
        amount = float(amount_match.group(1)) if amount_match else 0.0
        result = TOOL_REGISTRY["create_refund_request"](
            ticket_id=state.get("ticket_id", "unknown"), amount=amount
        )
        tool_output = f"\n\n[Tool Result — create_refund_request]: {result}"
    elif any(
        kw in query.lower() for kw in ["plan", "subscription", "upgrade", "downgrade"]
    ):
        result = TOOL_REGISTRY["check_subscription_plan"](
            ticket_id=state.get("ticket_id", "unknown")
        )
        tool_output = f"\n\n[Tool Result — check_subscription_plan]: {result}"

    system_prompt = BILLING_SYSTEM_PROMPT.format(tools=tools_desc, context=context)
    response_text, latency = llm.generate(
        system_prompt=system_prompt,
        user_prompt=query + tool_output,
        temperature=0.2,
        max_tokens=500,
    )

    avg_score = sum(c.score for c in chunks) / len(chunks) if chunks else 0.0
    sources = list({c.source for c in chunks})

    trace = state.get("trace", [])
    trace.append(
        {
            "agent": "billing",
            "action": "handle_billing",
            "detail": f"tool_used={bool(tool_output)}",
        }
    )

    return {
        **state,
        "retrieved_context": context,
        "sources": sources,
        "final_response": response_text,
        "agent_used": "billing_agent",
        "confidence_score": round(avg_score, 3),
        "escalated": False,
        "trace": trace,
        "latency_ms": state.get("latency_ms", 0) + latency,
    }
