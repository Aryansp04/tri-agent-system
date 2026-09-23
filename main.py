"""
Entry point and demonstration runner for NexusAI.
"""
import argparse
import sys
from core.models import AgentRequest, SpoilerLevel
from orchestrator import MultiAgentOrchestrator


def print_banner():
    print("=" * 75)
    print("              NEXUSAI: CODING | FINANCE | GAMING | OMNI")
    print("=" * 75)


def display_response(req: AgentRequest, resp):
    print("\n" + "-" * 75)
    print(f"USER QUERY: {req.query}")
    print(f"DISPATCHED AGENT: {resp.agent_name} | DOMAIN: {resp.domain.value}")
    
    decision = resp.metadata.get("route_decision")
    if decision:
        print(f"ROUTER CONFIDENCE: {decision.confidence * 100:.1f}%")
        print(f"ROUTER REASONING:  {decision.reasoning}")
    
    if resp.tools_used:
        print("\n[TOOLS FIRED]:")
        for tool_res in resp.tools_used:
            status = "SUCCESS" if tool_res.success else "FAIL"
            print(f"  * {tool_res.tool_name} -> {status}")
            if tool_res.error:
                print(f"    Error: {tool_res.error}")

    print(f"\n[QUALITY GATE]: {'PASSED' if resp.quality_passed else 'FAILED'}")
    print("-" * 75)
    print("\n" + resp.content)
    print("=" * 75 + "\n")


def run_demo():
    print_banner()
    print("Running 5 Demonstration Scenarios across the 5 Core Disciplines...\n")
    orchestrator = MultiAgentOrchestrator()

    scenarios = [
        # 1. Pure Coding
        (
            AgentRequest(query="Write a Python function to compute the variance of a list of numbers."),
            "Scenario 1: Pure Coding Task (Algorithm Implementation & Sandbox Verification)"
        ),
        # 2. Pure Finance
        (
            AgentRequest(query="What is the CAGR and risk profile of an investment growing from $10k to $21.5k over 5 years?"),
            "Scenario 2: Pure Finance Research (Compounding, Scenarios & Risk Disclosures)"
        ),
        # 3. Pure Gaming (No Spoilers)
        (
            AgentRequest(
                query="What build and strategy should I use against Malenia in Elden Ring?",
                spoiler_preference=SpoilerLevel.NO_SPOILERS
            ),
            "Scenario 3: Pure Gaming Assistance (Boss Strategy & Strict NO_SPOILERS Gate)"
        ),
        # 4. Cross-Domain Hybrid (Finance + Coding)
        (
            AgentRequest(query="Write a Python script to calculate the portfolio Sharpe ratio and asset allocation."),
            "Scenario 4: Hybrid Collaborative Execution (Finance formulas + Coding implementation)"
        ),
        # 5. Inversion & Fallback Recovery
        (
            AgentRequest(query="Can you tell me how to bake sourdough bread?"),
            "Scenario 5: Inversion & Error Recovery (General Out-of-Domain Fallback)"
        )
    ]

    for req, title in scenarios:
        print(f"\n>>> EXECUTING: {title}")
        resp = orchestrator.handle_request(req)
        display_response(req, resp)


def run_interactive():
    print_banner()
    print("Interactive Mode. Type your query or 'exit' to quit.\n")
    orchestrator = MultiAgentOrchestrator()

    while True:
        try:
            query = input("Prompt > ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit", "q"]:
                print("Exiting NexusAI.")
                break

            spoiler_input = input("Spoiler Level ([1] NO_SPOILERS, [2] LIMITED, [3] FULL) [Default: 1]: ").strip()
            if spoiler_input == "2":
                level = SpoilerLevel.LIMITED_SPOILERS
            elif spoiler_input == "3":
                level = SpoilerLevel.FULL_SPOILERS
            else:
                level = SpoilerLevel.NO_SPOILERS

            req = AgentRequest(query=query, spoiler_preference=level)
            resp = orchestrator.handle_request(req)
            display_response(req, resp)
        except KeyboardInterrupt:
            print("\nSession ended.")
            break


def main():
    parser = argparse.ArgumentParser(description="NexusAI Multi-Agent System")
    parser.add_argument("--demo", action="store_true", help="Run automated demonstration scenarios")
    args = parser.parse_args()

    if args.demo or len(sys.argv) == 1:
        run_demo()
    else:
        run_interactive()


if __name__ == "__main__":
    main()
