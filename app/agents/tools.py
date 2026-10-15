"""
Tool registry — simulated "function tools" that agents can call.
In a real deployment these would hit actual internal APIs (billing system,
account service, etc). Here they're stubbed with realistic mock logic so
the architecture is demonstrable end-to-end.
"""

import random


def check_account_status(ticket_id: str) -> str:
    """Simulate looking up account status for the user behind a ticket."""
    statuses = ["active", "active", "active", "payment_failed", "suspended"]
    status = random.choice(statuses)
    return f"Account status: {status}. Ticket reference: {ticket_id}."


def check_subscription_plan(ticket_id: str) -> str:
    """Simulate fetching the user's current subscription plan."""
    plans = ["Free", "Pro Monthly", "Pro Annual", "Enterprise"]
    plan = random.choice(plans)
    return f"Current plan: {plan}."


def check_recent_payment(ticket_id: str) -> str:
    """Simulate checking the most recent payment/invoice status."""
    outcomes = ["succeeded", "succeeded", "failed - card declined", "pending"]
    outcome = random.choice(outcomes)
    return f"Most recent payment status: {outcome}."


def create_refund_request(ticket_id: str, amount: float) -> str:
    """Simulate creating a refund request for the billing team."""
    return f"Refund request of ${amount:.2f} created for ticket {ticket_id}. Reference: REF-{random.randint(10000, 99999)}."


TOOL_REGISTRY = {
    "check_account_status": check_account_status,
    "check_subscription_plan": check_subscription_plan,
    "check_recent_payment": check_recent_payment,
    "create_refund_request": create_refund_request,
}

TOOL_DESCRIPTIONS = {
    "check_account_status": "Checks whether a user's account is active, suspended, or has payment issues.",
    "check_subscription_plan": "Fetches the user's current subscription plan tier.",
    "check_recent_payment": "Checks the status of the user's most recent payment/invoice.",
    "create_refund_request": "Files a refund request for the billing team to process.",
}


def get_tool_descriptions() -> str:
    return "\n".join(f"- {name}: {desc}" for name, desc in TOOL_DESCRIPTIONS.items())
