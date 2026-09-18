"""
Supervisor / Router for intelligent domain classification and orchestration.
"""
import re
from typing import List, Tuple
from core.models import AgentRequest, DomainType, RouteDecision


class SupervisorRouter:
    """
    Classifies incoming user intent into CODING, FINANCE, GAMING, or HYBRID.
    Provides confidence scoring and failure recovery reasoning.
    """

    CODING_KEYWORDS = [
        "code", "python", "javascript", "typescript", "java", "c++", "c#", "function",
        "class", "script", "debug", "compile", "syntax", "bug", "algorithm", "database",
        "sql", "api", "backend", "frontend", "html", "css", "git", "refactor", "unit test",
        "optimization", "regex", "array", "binary tree", "async", "exception", "test harness"
    ]

    FINANCE_KEYWORDS = [
        "stock", "shares", "etf", "mutual fund", "bond", "portfolio", "investment",
        "cagr", "sharpe", "dividend", "yield", "valuation", "p/e", "eps", "revenue",
        "balance sheet", "cash flow", "roi", "interest rate", "fixed deposit", "crypto",
        "bitcoin", "risk return", "asset allocation", "drawdown", "financial analysis"
    ]

    GAMING_KEYWORDS = [
        "game", "gaming", "boss", "quest", "elden ring", "dark souls", "build", "weapon",
        "armor", "npc", "puzzle", "moveset", "rpg", "fps", "talismans", "spells",
        "scaling", "attack pattern", "punish window", "lore", "playthrough", "level up",
        "stats", "zelda", "dungeon", "patch notes", "spoiler"
    ]

    def route(self, request: AgentRequest) -> RouteDecision:
        query_lower = request.query.lower()

        # Score domains based on keyword density and regex patterns
        coding_score = self._compute_score(query_lower, self.CODING_KEYWORDS)
        finance_score = self._compute_score(query_lower, self.FINANCE_KEYWORDS)
        gaming_score = self._compute_score(query_lower, self.GAMING_KEYWORDS)

        # Regex boosts for explicit indicators
        if re.search(r"```[a-z]*|\bdef\b|\bfunction\b|\bimport\b|\bclass\b|\bscript\b|\bwrite\s+a\s+python\b|\bcode\b", query_lower):
            coding_score += 2
        if re.search(r"\$\d+|\bpercent\b|%|\bcagr\b|\bsharpe\b|\bp/e\b", query_lower):
            finance_score += 2
        if re.search(r"\bboss\b|\bspoiler\b|\bwalkthrough\b|\bhp\b|\bbuild\b", query_lower):
            gaming_score += 2

        scores = [
            (DomainType.CODING, coding_score),
            (DomainType.FINANCE, finance_score),
            (DomainType.GAMING, gaming_score),
        ]
        scores.sort(key=lambda x: x[1], reverse=True)

        top_domain, top_score = scores[0]
        runner_up_domain, runner_up_score = scores[1]

        # Inversion & Error Recovery: Check for unclassifiable/general input
        if top_score == 0:
            return RouteDecision(
                primary_domain=DomainType.GENERAL,
                confidence=0.1,
                reasoning="Query lacks domain-specific technical, financial, or gaming markers. Fallback triggered.",
                is_hybrid=False
            )

        total_score = sum(s[1] for s in scores)
        confidence = min(0.99, round(top_score / max(1, total_score), 2))

        # Check for cross-domain hybrid condition
        # (e.g., Finance formula + Python script, or Gaming mod in C++)
        if runner_up_score >= 2 and (runner_up_score / top_score) >= 0.35:
            return RouteDecision(
                primary_domain=top_domain,
                secondary_domain=runner_up_domain,
                confidence=confidence,
                reasoning=f"Cross-domain detected between {top_domain.value} ({top_score}) and {runner_up_domain.value} ({runner_up_score}). Initiating collaborative handoff.",
                is_hybrid=True
            )

        return RouteDecision(
            primary_domain=top_domain,
            confidence=confidence,
            reasoning=f"Classified as {top_domain.value} with strong score {top_score} vs competitors ({runner_up_score}).",
            is_hybrid=False
        )

    def _compute_score(self, text: str, keywords: List[str]) -> int:
        score = 0
        for kw in keywords:
            # Word boundary search
            matches = len(re.findall(r"\b" + re.escape(kw) + r"\b", text))
            score += matches
        return score
