"""
Chat routes — the main customer-facing endpoint. Takes a user message tied
to a ticket, runs it through the multi-agent LangGraph pipeline, persists
the conversation, and returns the agent's response.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.orchestrator import run_agent_pipeline
from app.api.deps import get_current_user
from app.core.logging import get_logger
from app.db.models import Message, SenderType, Ticket, TicketStatus, User
from app.db.session import get_db
from app.schemas.schemas import ChatRequest, ChatResponse
from app.services.mlflow_logger import log_agent_run

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
logger = get_logger(__name__)


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Process a user message for a given ticket through the agentic pipeline
    and return the generated response.
    """
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == payload.ticket_id, Ticket.user_id == current_user.id)
        .first()
    )
    if not ticket or not ticket.conversation:
        raise HTTPException(status_code=404, detail="Ticket not found")

    conversation = ticket.conversation

    # Persist the incoming user message
    user_msg = Message(
        conversation_id=conversation.id,
        sender_type=SenderType.USER,
        content=payload.message,
    )
    db.add(user_msg)
    db.commit()

    # Build conversation history for the agent (last 10 messages)
    history = [
        {
            "role": "user" if m.sender_type == SenderType.USER else "assistant",
            "content": m.content,
        }
        for m in conversation.messages[-10:]
    ]

    # Run the multi-agent pipeline
    result = run_agent_pipeline(
        ticket_id=ticket.id,
        user_message=payload.message,
        conversation_history=history,
    )

    # Persist the agent's response
    agent_msg = Message(
        conversation_id=conversation.id,
        sender_type=SenderType.AGENT,
        agent_name=result.get("agent_used", "unknown_agent"),
        content=result.get("final_response", ""),
    )
    db.add(agent_msg)

    # Update ticket status if escalated
    if result.get("escalated"):
        ticket.status = TicketStatus.ESCALATED
    elif ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.IN_PROGRESS

    db.commit()

    # Fire-and-forget MLflow logging — doesn't block the response
    background_tasks.add_task(
        log_agent_run,
        ticket_id=ticket.id,
        agent_used=result.get("agent_used", "unknown"),
        user_message=payload.message,
        response=result.get("final_response", ""),
        confidence_score=result.get("confidence_score", 0.0),
        escalated=result.get("escalated", False),
        latency_ms=result.get("latency_ms", 0),
        sources=result.get("sources", []),
        retrieved_context=result.get("retrieved_context", ""),
    )

    return ChatResponse(
        ticket_id=ticket.id,
        response=result.get("final_response", ""),
        agent_used=result.get("agent_used", "unknown"),
        confidence_score=result.get("confidence_score", 0.0),
        escalated=result.get("escalated", False),
        sources=result.get("sources", []),
        latency_ms=result.get("latency_ms", 0),
    )
