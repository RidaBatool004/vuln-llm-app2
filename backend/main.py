import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .database import init_db, get_db, reset_demo_db
from .models import ChatRequest, ChatResponse

app = FastAPI(title="NEXA AI Support API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TicketCreate(BaseModel):
    customer_id: int
    subject: str
    description: str = ""
    priority: str = "medium"


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "NEXA AI Support API"}


@app.get("/api/customers")
def get_customers():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/api/customers/{customer_id}")
def get_customer(customer_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Customer not found")
    return dict(row)


@app.get("/api/orders")
def get_orders():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/api/orders/{order_id}")
def get_order(order_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    return dict(row)


@app.get("/api/tickets")
def get_tickets():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return dict(row)


@app.post("/api/tickets")
def create_ticket(ticket: TicketCreate):
    """Create a new support ticket."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify customer exists
    cursor.execute("SELECT id FROM customers WHERE id = ?", (ticket.customer_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Customer not found")
    
    cursor.execute(
        "INSERT INTO tickets (customer_id, subject, description, status, priority) VALUES (?, ?, ?, 'open', ?)",
        (ticket.customer_id, ticket.subject, ticket.description, ticket.priority)
    )
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"success": True, "ticket_id": ticket_id, "message": "Ticket created successfully"}


@app.post("/api/demo/reset")
def demo_reset():
    """Reset the demo database to its original state."""
    reset_demo_db()
    return {"status": "ok", "message": "Demo data reset successfully"}


@app.post("/api/chat")
def chat(request: ChatRequest):
    from .ai_agent import generate_response

    print(f"[AGENT] User message received")

    messages = []

    if request.history:
        for msg in request.history:
            messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": request.message})

    response_text, tools_used = generate_response(messages)

    print(f"[AGENT] Final response generated")

    return ChatResponse(response=response_text, tools_used=tools_used)


# Serve frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/assistant.html")
def serve_assistant():
    return FileResponse(os.path.join(frontend_dir, "assistant.html"))


@app.get("/customers.html")
def serve_customers():
    return FileResponse(os.path.join(frontend_dir, "customers.html"))


@app.get("/settings.html")
def serve_settings():
    return FileResponse(os.path.join(frontend_dir, "settings.html"))
