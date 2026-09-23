"""
Central MultiAgentOrchestrator implementing lifecycle, collaboration, and error recovery.
NexusAI — Supervised Multi-Agent Orchestration System
"""
from typing import Dict, Any
from core.models import AgentRequest, AgentResponse, DomainType, RouteDecision, ToolExecutionResult
from agents.router import SupervisorRouter
from agents.coding_agent import CodingAgent
from agents.finance_agent import FinanceAgent
from agents.gaming_agent import GamingAgent
from agents.general_agent import OmniAgent


class MultiAgentOrchestrator:
    """
    Coordinates intent routing, specialized agent dispatch, cross-domain handoffs,
    and output validation.
    """

    def __init__(self):
        self.router = SupervisorRouter()
        self.coding_agent = CodingAgent()
        self.finance_agent = FinanceAgent()
        self.gaming_agent = GamingAgent()
        self.omni_agent = OmniAgent()

        self.agent_map = {
            DomainType.CODING: self.coding_agent,
            DomainType.FINANCE: self.finance_agent,
            DomainType.GAMING: self.gaming_agent,
            DomainType.GENERAL: self.omni_agent,
        }

    def handle_request(self, request: AgentRequest) -> AgentResponse:
        """Route and execute an incoming user query."""
        # 1. Intent Classification
        decision: RouteDecision = self.router.route(request)

        # 2. Open-ended general query handling via OmniAgent
        if decision.primary_domain == DomainType.GENERAL:
            resp = self.omni_agent.process(request)
            resp.metadata["route_decision"] = decision
            return resp

        # 3. Cross-Domain Collaborative Handoff
        if decision.is_hybrid and decision.secondary_domain in self.agent_map:
            return self._handle_hybrid(request, decision)

        # 4. Standard Single-Domain Dispatch
        agent = self.agent_map.get(decision.primary_domain)
        if not agent:
            return AgentResponse(
                agent_name="NexusAI Supervisor",
                domain=DomainType.GENERAL,
                content=f"Error: No registered agent for domain {decision.primary_domain.value}.",
                quality_passed=False
            )

        response = agent.process(request)
        response.metadata["route_decision"] = decision
        return response

    def _handle_hybrid(self, request: AgentRequest, decision: RouteDecision) -> AgentResponse:
        """
        Orchestrates multi-agent handoff.
        Example: Finance Agent provides mathematical formulation,
        Coding Agent implements and tests the Python algorithm.
        """
        primary_agent = self.agent_map[decision.primary_domain]
        secondary_agent = self.agent_map[decision.secondary_domain]

        # Domain knowledge phase
        secondary_resp = secondary_agent.process(request)
        
        # Implementation phase with context injection
        enriched_request = AgentRequest(
            query=f"{request.query}\nDomain Context Provided by {secondary_agent.name}:\n{secondary_resp.content[:400]}...",
            session_id=request.session_id,
            spoiler_preference=request.spoiler_preference
        )
        primary_resp = primary_agent.process(enriched_request)

        # Synthesize collaborative output
        combined_content = (
            f"> [!IMPORTANT]\n"
            f"> **Collaborative Multi-Agent Execution**: Query routed to `{primary_agent.name}` (Lead) "
            f"collaborating with `{secondary_agent.name}` (Consultant).\n\n"
            f"## Part 1: Domain Specifications & Formulas ({secondary_agent.name})\n"
            f"{secondary_resp.content}\n\n"
            f"---\n\n"
            f"## Part 2: Technical Implementation & Validation ({primary_agent.name})\n"
            f"{primary_resp.content}"
        )

        all_tools = secondary_resp.tools_used + primary_resp.tools_used

        return AgentResponse(
            agent_name=f"{primary_agent.name} + {secondary_agent.name}",
            domain=DomainType.HYBRID,
            content=combined_content,
            tools_used=all_tools,
            metadata={"route_decision": decision, "collaborators": [primary_agent.name, secondary_agent.name]},
            quality_passed=primary_resp.quality_passed and secondary_resp.quality_passed
        )

    def _handle_unclassified(self, request: AgentRequest, decision: RouteDecision) -> AgentResponse:
        return AgentResponse(
            agent_name="NexusAI Router",
            domain=DomainType.GENERAL,
            content=(
                "### NexusAI — Query Not Classified\n"
                f"Your query could not be definitively routed to one of our specialized domains:\n"
                "- **Coding Agent**: Architecture, debugging, software implementation, algorithms, testing.\n"
                "- **Finance Agent**: Investment analysis, CAGR, Sharpe ratio, portfolio scenario modeling.\n"
                "- **Gaming Agent**: Boss strategies, build synergies, item comparisons, spoiler protection.\n"
                "- **OmniAgent**: Science, history, philosophy, creative reasoning, and open inquiries.\n\n"
                "Please rephrase your query with more context."
            ),
            metadata={"route_decision": decision},
            quality_passed=True
        )
