from .database import get_db


def search_customers(query: str = "") -> list[dict]:
    """Search customers by name or email. Returns all if query is empty. Excludes internal_notes."""
    conn = get_db()
    cursor = conn.cursor()
    if query:
        cursor.execute(
            "SELECT id, name, email, phone, address, status, support_priority, created_at "
            "FROM customers WHERE name LIKE ? OR email LIKE ?",
            (f"%{query}%", f"%{query}%")
        )
    else:
        cursor.execute(
            "SELECT id, name, email, phone, address, status, support_priority, created_at "
            "FROM customers ORDER BY id"
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_customer(customer_id: int) -> dict | None:
    """Retrieve a single customer by ID. VULNERABILITY: Includes internal_notes."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, email, phone, address, status, internal_notes, support_priority, created_at "
        "FROM customers WHERE id = ?",
        (customer_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        customer = dict(row)
        if customer.get("internal_notes"):
            print(f"[LLM02 DEMO] Sensitive data exposed to LLM context")
            print(f"[LLM02 DEMO] Tool: get_customer")
            print(f"[LLM02 DEMO] Customer ID: {customer['id']}")
            print(f"[LLM02 DEMO] internal_notes: {customer['internal_notes']}")
        return customer
    return None


def get_order(order_id: int) -> dict | None:
    """Retrieve a single order by ID. Excludes internal_notes."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, customer_id, amount, status, delivery_date, product, created_at "
        "FROM orders WHERE id = ?",
        (order_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def search_tickets(query: str = "", status: str = "") -> list[dict]:
    """Search tickets by subject, description, or status. Returns all if both empty. Excludes internal_notes."""
    conn = get_db()
    cursor = conn.cursor()
    if query:
        cursor.execute(
            "SELECT id, customer_id, subject, description, status, priority, created_at "
            "FROM tickets WHERE subject LIKE ? OR description LIKE ?",
            (f"%{query}%", f"%{query}%")
        )
    elif status:
        cursor.execute(
            "SELECT id, customer_id, subject, description, status, priority, created_at "
            "FROM tickets WHERE status = ?",
            (status,)
        )
    else:
        cursor.execute(
            "SELECT id, customer_id, subject, description, status, priority, created_at "
            "FROM tickets ORDER BY id"
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_ticket(ticket_id: int) -> dict | None:
    """Retrieve a single ticket by ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, customer_id, subject, description, status, priority, created_at "
        "FROM tickets WHERE id = ?",
        (ticket_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


VALID_STATUSES = ("open", "in_progress", "resolved")


def update_ticket_status(ticket_id: int, status: str) -> dict:
    """Update a ticket's status. VULNERABILITY: LLM06 Excessive Agency - no authorization check."""
    if status not in VALID_STATUSES:
        return {"success": False, "error": f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"}

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, status FROM tickets WHERE id = ?", (ticket_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {"success": False, "error": f"Ticket #{ticket_id} not found"}

    previous_status = dict(row)["status"]
    cursor.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
    conn.commit()
    conn.close()

    print(f"[LLM06 DEMO] AI agent invoked consequential action")
    print(f"[LLM06 DEMO] Tool: update_ticket_status")
    print(f"[LLM06 DEMO] Ticket: {ticket_id}")
    print(f"[LLM06 DEMO] Previous status: {previous_status}")
    print(f"[LLM06 DEMO] New status: {status}")

    return {"success": True, "ticket_id": ticket_id, "previous_status": previous_status, "new_status": status}


def add_internal_note(ticket_id: int, note: str) -> dict:
    """Add an internal note to a ticket. VULNERABILITY: LLM06 Excessive Agency - no authorization check."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, internal_notes FROM tickets WHERE id = ?", (ticket_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {"success": False, "error": f"Ticket #{ticket_id} not found"}

    previous_notes = dict(row)["internal_notes"] or ""
    new_notes = f"{previous_notes}\n{note}".strip() if previous_notes else note
    cursor.execute("UPDATE tickets SET internal_notes = ? WHERE id = ?", (new_notes, ticket_id))
    conn.commit()
    conn.close()

    print(f"[LLM06 DEMO] AI agent invoked consequential action")
    print(f"[LLM06 DEMO] Tool: add_internal_note")
    print(f"[LLM06 DEMO] Ticket: {ticket_id}")
    print(f"[LLM06 DEMO] Note added: {note[:50]}...")

    return {"success": True, "ticket_id": ticket_id, "note_added": note}


VALID_AGENTS = ("agent_smith", "agent_jones", "agent_williams", "agent_brown", "unassigned")


def assign_ticket(ticket_id: int, agent: str) -> dict:
    """Assign a ticket to a support agent. VULNERABILITY: LLM06 Excessive Agency - no authorization check."""
    if agent not in VALID_AGENTS:
        return {"success": False, "error": f"Invalid agent. Must be one of: {', '.join(VALID_AGENTS)}"}

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, internal_notes FROM tickets WHERE id = ?", (ticket_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {"success": False, "error": f"Ticket #{ticket_id} not found"}

    previous_notes = dict(row)["internal_notes"] or ""
    assignment_note = f"Assigned to {agent}"
    new_notes = f"{previous_notes}\n{assignment_note}".strip() if previous_notes else assignment_note
    cursor.execute("UPDATE tickets SET internal_notes = ? WHERE id = ?", (new_notes, ticket_id))
    conn.commit()
    conn.close()

    print(f"[LLM06 DEMO] AI agent invoked consequential action")
    print(f"[LLM06 DEMO] Tool: assign_ticket")
    print(f"[LLM06 DEMO] Ticket: {ticket_id}")
    print(f"[LLM06 DEMO] Assigned to: {agent}")

    return {"success": True, "ticket_id": ticket_id, "assigned_to": agent}
