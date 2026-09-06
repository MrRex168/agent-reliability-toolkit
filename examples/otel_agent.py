"""Minimal OpenTelemetry integration example.

Run with the optional OpenTelemetry dependencies installed:
    pip install -e '.[otel]'
"""

from agent_reliability.otel import instrument_agent


class DemoAgent:
    def run(self, prompt: str) -> str:
        return f"Processed: {prompt}"


if __name__ == "__main__":
    agent = instrument_agent(DemoAgent(), service_name="demo-agent")
    print(agent.run("Where is order 1234?"))
