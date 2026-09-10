from pydantic import BaseModel
from typing import Optional


class Customer(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    status: str
    internal_notes: Optional[str] = None
    support_priority: str
    created_at: str


class Order(BaseModel):
    id: int
    customer_id: int
    amount: float
    status: str
    delivery_date: Optional[str] = None
    product: str
    internal_notes: Optional[str] = None
    created_at: str


class Ticket(BaseModel):
    id: int
    customer_id: int
    subject: str
    description: Optional[str] = None
    status: str
    priority: str
    internal_notes: Optional[str] = None
    created_at: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[list[ChatMessage]] = None


class ChatResponse(BaseModel):
    response: str
    tools_used: list[str] = []
