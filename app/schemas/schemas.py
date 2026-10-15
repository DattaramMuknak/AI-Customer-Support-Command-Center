"""
Pydantic request/response schemas for the API layer.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.db.models import SenderType, TicketPriority, TicketStatus


# ---------- Auth ----------

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)
    is_admin: bool = False


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    is_admin: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Tickets ----------
class TicketCreate(BaseModel):
    subject: str
    initial_message: str


class TicketOut(BaseModel):
    id: str
    subject: str
    status: TicketStatus
    priority: TicketPriority
    category: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Chat / Messages ----------
class ChatRequest(BaseModel):
    ticket_id: str
    message: str = Field(min_length=1, max_length=4000)


class MessageOut(BaseModel):
    id: str
    sender_type: SenderType
    agent_name: str | None
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    ticket_id: str
    response: str
    agent_used: str
    confidence_score: float
    escalated: bool
    sources: list[str] = []
    latency_ms: int


# ---------- Knowledge Base ----------
class KBDocumentIn(BaseModel):
    title: str
    content: str
    category: str | None = None
    metadata: dict = {}


class KBIngestResponse(BaseModel):
    chunks_ingested: int
    document_ids: list[str]


class RetrievedChunk(BaseModel):
    text: str
    score: float
    source: str
    metadata: dict = {}
