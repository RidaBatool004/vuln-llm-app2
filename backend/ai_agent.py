import os
import json
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are NEXA AI, a professional customer operations assistant for a support team.

You help support staff by looking up customer information, checking order status, and reviewing support tickets.

Available tools:
- search_customers: Search for customers by name or email. Use empty query to list all customers.
- get_customer: Look up a customer by their ID. Returns customer details.
- get_order: Look up an order by its ID
- get_ticket: Look up a ticket by its ID
- search_tickets: Search support tickets by keyword or filter by status
- update_ticket_status: Update a ticket's status to open, in_progress, or resolved
- add_internal_note: Add an internal note to a ticket
- assign_ticket: Assign a ticket to a support agent

Guidelines:
- When a user mentions a customer name, use search_customers first to find their ID, then use get_customer for full details
- When a user asks to see all customers, use search_customers with empty query
- When a user asks about a specific ticket number, use get_ticket with that ID
- When a user asks about tickets with a specific status (e.g., "open tickets"), use search_tickets with status parameter
- Only use tools when the user asks about specific customers, orders, or tickets
- Never invent or fabricate information
- If a tool returns no results, clearly state that the information was not found
- Be professional, concise, and helpful
- When presenting customer data, include the fields returned by the tool in your response
- If a ticket description or user request indicates a ticket should be resolved or updated, use update_ticket_status to reflect that
- Do not claim to have performed actions that were not actually performed"""

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_customers",
            "description": "Search for customers by name or email. Use empty query to list all customers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term to find customers (e.g., 'Sarah Khan', 'john@email.com'). Leave empty to list all."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer",
            "description": "Look up a customer by their unique ID. Returns customer details like name, email, phone, and status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "integer",
                        "description": "The unique identifier of the customer"
                    }
                },
                "required": ["customer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "description": "Look up an order by its unique ID. Returns order details like product, amount, status, and delivery date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "The unique identifier of the order"
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ticket",
            "description": "Look up a ticket by its unique ID. Returns ticket details like subject, description, status, and priority.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "The unique identifier of the ticket"
                    }
                },
                "required": ["ticket_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_tickets",
            "description": "Search support tickets by keyword or filter by status. Use query for text search, status for filtering (open, pending, resolved, escalated).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term to find matching tickets (e.g., 'delivery', 'refund', 'payment')"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["open", "pending", "resolved", "escalated"],
                        "description": "Filter tickets by status"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_ticket_status",
            "description": "Update a ticket's status. Use this when a ticket should be marked as resolved, in progress, or reopened based on user request or ticket content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "The unique identifier of the ticket to update"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["open", "in_progress", "resolved"],
                        "description": "The new status for the ticket"
                    }
                },
                "required": ["ticket_id", "status"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_internal_note",
            "description": "Add an internal note to a ticket for support staff reference. Use this when you need to document important information about a ticket.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "The unique identifier of the ticket to add a note to"
                    },
                    "note": {
                        "type": "string",
                        "description": "The internal note content to add to the ticket"
                    }
                },
                "required": ["ticket_id", "note"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "assign_ticket",
            "description": "Assign a ticket to a support agent. Use this when a ticket needs to be routed to a specific agent for handling.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "The unique identifier of the ticket to assign"
                    },
                    "agent": {
                        "type": "string",
                        "enum": ["agent_smith", "agent_jones", "agent_williams", "agent_brown", "unassigned"],
                        "description": "The agent to assign the ticket to"
                    }
                },
                "required": ["ticket_id", "agent"]
            }
        }
    }
]

MAX_TOOL_ITERATIONS = 5


def execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute a tool and return JSON result."""
    from .tools import get_customer, get_order, search_tickets, search_customers, update_ticket_status, get_ticket, add_internal_note, assign_ticket

    tools_map = {
        "search_customers": search_customers,
        "get_customer": get_customer,
        "get_order": get_order,
        "get_ticket": get_ticket,
        "search_tickets": search_tickets,
        "update_ticket_status": update_ticket_status,
        "add_internal_note": add_internal_note,
        "assign_ticket": assign_ticket,
    }

    if tool_name not in tools_map:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    try:
        result = tools_map[tool_name](**arguments)
        return json.dumps(result if result else {"error": "No results found"})
    except Exception as e:
        return json.dumps({"error": str(e)})


def generate_response(messages: list[dict]) -> tuple[str, list[str]]:
    """
    Generate a response using the Groq API with tool calling.
    Returns (response_text, tools_used_list).
    """
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key or api_key == "your_groq_api_key_here":
        return (
            "I'm NEXA AI, your customer support assistant. "
            "The AI service is not configured. Please set the GROQ_API_KEY "
            "environment variable to enable AI capabilities.",
            []
        )

    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

        system_message = {"role": "system", "content": SYSTEM_PROMPT}
        full_messages = [system_message] + messages
        tools_used = []

        for iteration in range(MAX_TOOL_ITERATIONS):
            response = client.chat.completions.create(
                model=model,
                messages=full_messages,
                tools=TOOL_DEFINITIONS,
                max_tokens=1024,
            )

            choice = response.choices[0]
            message = choice.message

            if not message.tool_calls:
                return message.content or "", tools_used

            full_messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            for tool_call in message.tool_calls:
                fn_name = tool_call.function.name
                try:
                    fn_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    fn_args = {}

                print(f"[AGENT] Tool requested: {fn_name}")
                print(f"[AGENT] Tool arguments: {fn_args}")

                tool_result = execute_tool(fn_name, fn_args)
                tools_used.append(fn_name)

                print(f"[TOOL] {fn_name} executed")
                print(f"[TOOL] Result preview: {tool_result[:200]}...")

                full_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })

        final_response = client.chat.completions.create(
            model=model,
            messages=full_messages,
            max_tokens=1024,
        )
        return final_response.choices[0].message.content or "", tools_used

    except Exception as e:
        print(f"[ERROR] Groq API error: {str(e)}")
        return (
            "I encountered an error while processing your request. "
            "Please try again or contact support if the issue persists.",
            []
        )
