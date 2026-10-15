"""
Knowledge Agent — answers factual/how-to questions using RAG retrieval
over the support knowledge base (Pinecone).
"""

from app.agents.state import AgentState
from app.core.logging import get_logger
from app.rag.retriever import get_retriever
from app.services.llm_client import get_llm_client

logger = get_logger(__name__)

KNOWLEDGE_SYSTEM_PROMPT = """You are a helpful customer support assistant.
Answer the user's question using ONLY the provided knowledge base context below.
If the context doesn't contain a clear answer, say you're not certain and suggest
the user contact human support — do NOT make up information.

Be concise, friendly, and professional. Use a numbered list for multi-step instructions.

Knowledge Base Context:
{context}
"""


def knowledge_node(state: AgentState) -> AgentState:
    """Retrieve relevant context and generate a grounded answer."""
    retriever = get_retriever()
    llm = get_llm_client()

    query = state["user_message"]
    chunks = retriever.retrieve(query, top_k=5, category_filter=None)
    context = retriever.format_context(chunks)

    system_prompt = KNOWLEDGE_SYSTEM_PROMPT.format(context=context)
    response_text, latency = llm.generate(
        system_prompt=system_prompt,
        user_prompt=query,
        temperature=0.3,
        max_tokens=500,
    )

    avg_score = sum(c.score for c in chunks) / len(chunks) if chunks else 0.0
    sources = list({c.source for c in chunks})

    trace = state.get("trace", [])
    trace.append(
        {"agent": "knowledge", "action": "rag_answer", "detail": f"sources={sources}"}
    )

    logger.info(
        "knowledge_agent_response",
        sources=sources,
        confidence=avg_score,
        latency_ms=latency,
    )

    return {
        **state,
        "retrieved_context": context,
        "sources": sources,
        "final_response": response_text,
        "agent_used": "knowledge_agent",
        "confidence_score": round(avg_score, 3),
        "escalated": False,
        "trace": trace,
        "latency_ms": state.get("latency_ms", 0) + latency,
    }
