from __future__ import annotations


class UnreliableAgent:
    """Deterministic demo agent that fails intermittently."""

    def __init__(self) -> None:
        self.calls = 0

    def run(self, prompt: str) -> str:
        self.calls += 1
        if "refund" in prompt.lower():
            if self.calls % 5 == 0:
                return "I can help with your request."
            return "Refunds are available within 30 days to the original payment method."

        if "order" in prompt.lower():
            if self.calls % 7 == 0:
                return "I cannot determine the order status."
            return "Order 1234 has shipped and is on the way."

        return "I don't know."


agent = UnreliableAgent()
