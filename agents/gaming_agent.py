"""
Specialized Gaming AI Assistant.
"""
from typing import Dict, Any, List
from core.base_agent import BaseAgent
from core.models import AgentRequest, AgentResponse, DomainType, SpoilerLevel, ToolExecutionResult


class GamingAgent(BaseAgent):
    SYSTEM_PROMPT = """You are an advanced gaming assistant designed to help players understand, complete, optimize, and enjoy video games.
Spoiler Tiers: NO_SPOILERS (default), LIMITED_SPOILERS, FULL_SPOILERS.
Always explain WHY an option or build synergy works."""

    BOSS_DATABASE = {
        "malenia": {
            "name": "Malenia, Blade of Miquella",
            "game": "Elden Ring",
            "weakness": "Frostbite, Bleed, Fire",
            "key_attack": "Waterfowl Dance (3-stage flurry)",
            "punish_window": "Immediately after her scarlet flower recovery and ground-thrusts.",
            "spoiler_lore": "Twin prodigy afflicted with scarlet rot, guarding Miquella's Haligtree in the subterranean roots.",
            "strategy": (
                "1. **Spacing**: Keep mid-distance to bait thrust attacks.\n"
                "2. **Waterfowl Counter**: Sprint backward on first flurry, dodge forward-right through the second, pivot on the third.\n"
                "3. **Damage Type**: Use Frost pots to instantly stagger her out of airborne startup animations."
            )
        },
        "default": {
            "name": "Target Boss / Encounter",
            "game": "Action RPG",
            "weakness": "Elemental or posture break",
            "key_attack": "Telegraphed heavy charge",
            "punish_window": "Post-combo recovery frames.",
            "spoiler_lore": "Endgame narrative reveal.",
            "strategy": (
                "1. Observe rhythm of swing combos before committing to heavy attacks.\n"
                "2. Conserve stamina bar for defensive i-frame roll.\n"
                "3. Exploit status buildup during extended recovery animations."
            )
        }
    }

    def __init__(self):
        super().__init__(
            name="GamingAgent",
            domain=DomainType.GAMING,
            system_prompt=self.SYSTEM_PROMPT,
        )
        self.register_tool("query_boss_strategy", self.query_boss_strategy)
        self.register_tool("analyze_build_synergy", self.analyze_build_synergy)

    def query_boss_strategy(self, boss_key: str) -> Dict[str, Any]:
        """Fetch boss mechanics, weaknesses, and attack patterns."""
        key = boss_key.lower().strip()
        for k, v in self.BOSS_DATABASE.items():
            if k in key:
                return v
        return self.BOSS_DATABASE["default"]

    def analyze_build_synergy(self, main_stat: str, playstyle: str) -> Dict[str, Any]:
        """Evaluate stat scaling and weapon/talisman synergy."""
        stat = main_stat.lower()
        if "dex" in stat:
            return {
                "stat": "Dexterity",
                "recommended_weapons": ["Nagakiba", "Rivers of Blood", "Keen Uchigatana"],
                "synergy_reason": "High attack speed triggers percentage-based bleed procs rapidly, mitigating boss health scaling.",
                "key_talismans": ["Lord of Blood's Exultation", "Winged Sword Insignia"],
            }
        else:
            return {
                "stat": "Strength",
                "recommended_weapons": ["Greatsword (Colossal)", "Giant-Crusher"],
                "synergy_reason": "Heavy stagger poise damage interrupts enemy attacks and creates frequent critical riposte windows.",
                "key_talismans": ["Claw Talisman", "Axe Talisman", "Dragoncrest Greatshield"],
            }

    def process(self, request: AgentRequest) -> AgentResponse:
        tools_used = []
        spoiler_pref = request.spoiler_preference
        api_key = request.api_key or getattr(self, "api_key", None)
        from core.llm_client import GeminiClient
        client = GeminiClient(api_key=api_key)

        boss_res = self.execute_tool("query_boss_strategy", boss_key=request.query)
        tools_used.append(boss_res)

        build_res = self.execute_tool("analyze_build_synergy", main_stat=request.query, playstyle="melee")
        tools_used.append(build_res)

        if client.is_configured():
            gen_res = client.generate(
                prompt=(
                    f"Gaming Question: {request.query}\n"
                    f"STRICT ENFORCED SPOILER POLICY: {spoiler_pref.value}.\n"
                    "- If NO_SPOILERS: Reveal only immediate mechanical steps, boss moveset telegraphs, and punish windows. ZERO narrative spoilers or future plot points.\n"
                    "- If LIMITED_SPOILERS: Reveal necessary location and minor context.\n"
                    "- If FULL_SPOILERS: Full story and lore permissible.\n"
                    "Always explain WHY equipment/build synergies work."
                ),
                system_instruction=self.system_prompt
            )
            if gen_res.get("success"):
                content = (
                    f"**Enforced Spoiler Protection**: `{spoiler_pref.value}`\n\n"
                    f"{gen_res['text']}"
                )
                tools_used.append(ToolExecutionResult(
                    tool_name="gemini_gaming_synthesis",
                    success=True,
                    output={"model": gen_res.get("model")}
                ))
            else:
                content = self._format_gaming_response(request.query, spoiler_pref, boss_res.output, build_res.output)
        else:
            content = self._format_gaming_response(request.query, spoiler_pref, boss_res.output, build_res.output)

        response = AgentResponse(
            agent_name=self.name,
            domain=self.domain,
            content=content,
            tools_used=tools_used,
            quality_passed=False
        )
        response.quality_passed = self.quality_check(response)
        return response

    def _format_gaming_response(self, query: str, spoiler_level: SpoilerLevel, boss_data: Dict[str, Any], build_data: Dict[str, Any]) -> str:
        out = [
            f"### Game Context & Objective",
            f"Request: '{query}'",
            f"**Enforced Spoiler Protection**: `{spoiler_level.value}`\n",
            f"### 1. Boss Strategy: {boss_data['name']}",
            f"- **Effective Damage Elements**: {boss_data['weakness']}",
            f"- **Critical Attack to Watch**: {boss_data['key_attack']}",
            f"- **Punish Window**: {boss_data['punish_window']}",
            "",
            "### 2. Tactical Execution Plan",
            boss_data["strategy"],
            "",
            f"### 3. Recommended Build Synergy ({build_data['stat']})",
            f"- **Weapons**: {', '.join(build_data['recommended_weapons'])}",
            f"- **Why this synergy works**: {build_data['synergy_reason']}",
            f"- **Key Accessories/Talismans**: {', '.join(build_data['key_talismans'])}",
        ]

        if spoiler_level == SpoilerLevel.FULL_SPOILERS:
            out.extend([
                "",
                "### 4. Narrative & Lore Context (Full Spoilers Active)",
                f"> {boss_data['spoiler_lore']}"
            ])
        elif spoiler_level == SpoilerLevel.NO_SPOILERS:
            out.extend([
                "",
                "> [!NOTE]",
                "> *Lore, narrative outcomes, and future cutscene details are strictly redacted under NO_SPOILERS mode.*"
            ])

        return "\n".join(out)

    def quality_check(self, response: AgentResponse) -> bool:
        if not response.content or len(response.content) < 20:
            return False
        return True

