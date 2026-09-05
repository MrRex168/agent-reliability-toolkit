from __future__ import annotations


def agent(prompt: str) -> dict:
    """Example structured-output agent used by the v0.2 demo."""
    if "refund" in prompt.lower():
        return {"answer": "Refunds are available within 30 days.", "category": "policy"}
    if "order" in prompt.lower():
        return {"answer": "Order 1234 is shipped.", "category": "order"}
    return {"answer": "I don't know.", "category": "unknown"}
