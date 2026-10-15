"""
Ticket routes — create, list, and fetch support tickets for the current user.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Conversation, Message, SenderType, Ticket, User
from app.db.session import get_db
from app.schemas.schemas import MessageOut, TicketCreate, TicketOut

router = APIRouter(prefix="/api/v1/tickets", tags=["tickets"])


@router.post("", response_model=TicketOut, status_code=201)
def create_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new support ticket along with its conversation thread and first message."""
    ticket = Ticket(user_id=current_user.id, subject=payload.subject)
    db.add(ticket)
    db.flush()  # get ticket.id without full commit

    conversation = Conversation(ticket_id=ticket.id)
    db.add(conversation)
    db.flush()

    first_message = Message(
        conversation_id=conversation.id,
        sender_type=SenderType.USER,
        content=payload.initial_message,
    )
    db.add(first_message)
    db.commit()
    db.refresh(ticket)

    return ticket


@router.get("", response_model=list[TicketOut])
def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Ticket)
        .filter(Ticket.user_id == current_user.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id, Ticket.user_id == current_user.id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.get("/{ticket_id}/messages", response_model=list[MessageOut])
def get_ticket_messages(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id, Ticket.user_id == current_user.id)
        .first()
    )
    if not ticket or not ticket.conversation:
        raise HTTPException(status_code=404, detail="Ticket or conversation not found")
    return ticket.conversation.messages
