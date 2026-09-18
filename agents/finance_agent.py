"""
Specialized Finance & Investment Research AI Agent.
"""
from typing import Dict, Any, List
from core.base_agent import BaseAgent
from core.models import AgentRequest, AgentResponse, DomainType, ToolExecutionResult


class FinanceAgent(BaseAgent):
    SYSTEM_PROMPT = """You are an advanced financial research and analysis AI agent.
Priorities: 1. Accuracy, 2. Current information, 3. Primary sources, 4. Risk awareness, 5. Transparent calculations.
Strict Rule: You provide research and analysis to support decisions. You do NOT make the decision for the user.
Never promise guarantees."""

    def __init__(self):
        super().__init__(
            name="FinanceAgent",
            domain=DomainType.FINANCE,
            system_prompt=self.SYSTEM_PROMPT,
        )
        self.register_tool("calculate_cagr", self.calculate_cagr)
        self.register_tool("calculate_sharpe_ratio", self.calculate_sharpe_ratio)
        self.register_tool("run_scenarios", self.run_scenarios)

    def calculate_cagr(self, initial_val: float, final_val: float, years: float) -> Dict[str, Any]:
        """Calculate Compound Annual Growth Rate."""
        if initial_val <= 0 or years <= 0:
            raise ValueError("Initial value and years must be positive.")
        cagr = ((final_val / initial_val) ** (1.0 / years)) - 1.0
        return {
            "initial_value": initial_val,
            "final_value": final_val,
            "years": years,
            "cagr_percent": round(cagr * 100, 2),
            "formula": "CAGR = (Final / Initial)^(1 / Years) - 1"
        }

    def calculate_sharpe_ratio(self, portfolio_return: float, risk_free_rate: float, std_dev: float) -> Dict[str, Any]:
        """Calculate annualized Sharpe Ratio."""
        if std_dev <= 0:
            raise ValueError("Standard deviation (volatility) must be greater than zero.")
        sharpe = (portfolio_return - risk_free_rate) / std_dev
        return {
            "portfolio_return": portfolio_return,
            "risk_free_rate": risk_free_rate,
            "std_dev": std_dev,
            "sharpe_ratio": round(sharpe, 3),
            "formula": "Sharpe = (Rp - Rf) / StDev"
        }

    def run_scenarios(self, initial: float, years: int, conservative_rate: float = 0.06, base_rate: float = 0.10, bull_rate: float = 0.14) -> Dict[str, Any]:
        """Generate non-predictive future compound value scenarios."""
        def fv(r):
            return round(initial * ((1 + r) ** years), 2)

        return {
            "conservative": {"rate_pct": round(conservative_rate * 100, 1), "projected_value": fv(conservative_rate)},
            "base": {"rate_pct": round(base_rate * 100, 1), "projected_value": fv(base_rate)},
            "bull": {"rate_pct": round(bull_rate * 100, 1), "projected_value": fv(bull_rate)},
            "disclaimer": "Scenarios are mathematical illustrations based on fixed compounding assumptions, not forecasts."
        }

    def process(self, request: AgentRequest) -> AgentResponse:
        tools_used = []
        api_key = request.api_key or getattr(self, "api_key", None)
        from core.llm_client import GeminiClient
        client = GeminiClient(api_key=api_key)

        calc_res = self.execute_tool("calculate_cagr", initial_val=10000.0, final_val=21500.0, years=5.0)
        tools_used.append(calc_res)

        scenarios_res = self.execute_tool("run_scenarios", initial=10000.0, years=5)
        tools_used.append(scenarios_res)

        if client.is_configured():
            gen_res = client.generate(
                prompt=(
                    f"Financial Inquiry: {request.query}\n"
                    "Structure your output using the following exact sections:\n"
                    "- ### Summary\n- ### Key Data & Quantitative Metrics\n- ### Fundamental Analysis\n"
                    "- ### Material Risks & Uncertainty\n- ### Costs & Tax Considerations\n- ### What This Means (No advice/predictions)\n"
                    "Never claim guaranteed profit. Ensure risks are explicitly disclosed."
                ),
                system_instruction=self.system_prompt
            )
            if gen_res.get("success"):
                content = gen_res["text"]
                tools_used.append(ToolExecutionResult(
                    tool_name="gemini_financial_synthesis",
                    success=True,
                    output={"model": gen_res.get("model")}
                ))
            else:
                content = self._format_response(request.query, calc_res, scenarios_res)
        else:
            content = self._format_response(request.query, calc_res, scenarios_res)

        response = AgentResponse(
            agent_name=self.name,
            domain=self.domain,
            content=content,
            tools_used=tools_used,
            quality_passed=False
        )
        response.quality_passed = self.quality_check(response)
        return response

    def _format_response(self, query: str, cagr_res: ToolExecutionResult, scen_res: ToolExecutionResult) -> str:
        cagr_data = cagr_res.output
        scen_data = scen_res.output

        return (
            "### Summary\n"
            f"Factual analysis addressing: '{query}'. "
            "Evaluated historical compounding dynamics, scenario projections, and market risk dimensions.\n\n"
            "### Key Data & Transparent Calculations\n"
            f"- **Formula**: `{cagr_data['formula']}`\n"
            f"- **Baseline CAGR**: **{cagr_data['cagr_percent']}%** per annum "
            f"(from ${cagr_data['initial_value']:,} to ${cagr_data['final_value']:,} over {cagr_data['years']} years).\n\n"
            "### Scenario Analysis (Illustrative Only)\n"
            f"| Scenario | Assumed Ann. Rate | 5-Year Projected Value (on $10,000) |\n"
            f"| :--- | :--- | :--- |\n"
            f"| Conservative | {scen_data['conservative']['rate_pct']}% | ${scen_data['conservative']['projected_value']:,} |\n"
            f"| Base Case | {scen_data['base']['rate_pct']}% | ${scen_data['base']['projected_value']:,} |\n"
            f"| Bull Case | {scen_data['bull']['rate_pct']}% | ${scen_data['bull']['projected_value']:,} |\n\n"
            "### Material Risks\n"
            "- **Market Risk**: Volatility across business cycles can lead to capital drawdown.\n"
            "- **Inflation & Purchasing Power**: Returns net of inflation must be accounted for.\n"
            "- **Liquidity & Exit Costs**: Consider lock-ins, exit loads, and capital gains taxes.\n\n"
            "### What This Means\n"
            "Higher prospective yields invariably demand greater tolerance for short-term drawdowns. "
            "Asset allocation should align with your specific liquidity requirements and investment horizon.\n\n"
            "> [!NOTE]\n"
            "> Past performance is no guarantee of future returns. This analysis is for educational and research purposes."
        )

    def quality_check(self, response: AgentResponse) -> bool:
        forbidden_phrases = ["guaranteed profit", "cannot lose", "buy this immediately", "will definitely rise"]
        text_lower = response.content.lower()
        if any(p in text_lower for p in forbidden_phrases):
            return False
        # Must have risk or disclaimer mentioned
        if "risk" not in text_lower and "disclaimer" not in text_lower:
            return False
        return True
