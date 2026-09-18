"""
Specialized General Knowledge & Open-Ended Inquiry AI Agent.
"""
from typing import Dict, Any
from core.base_agent import BaseAgent
from core.models import AgentRequest, AgentResponse, DomainType, ToolExecutionResult
from core.llm_client import GeminiClient


class GeneralAgent(BaseAgent):
    SYSTEM_PROMPT = """You are a helpful, accurate, and articulate general intelligence AI agent.
Your purpose is to assist the user with open-ended inquiries, science, history, recipes, writing, explanations, and creative problem solving.
Be concise, clear, and structured in your explanations."""

    def __init__(self):
        super().__init__(
            name="GeneralAgent",
            domain=DomainType.GENERAL,
            system_prompt=self.SYSTEM_PROMPT,
        )
        self.llm_client = GeminiClient()

    def process(self, request: AgentRequest) -> AgentResponse:
        tools_used = []
        api_key = request.api_key

        # Check if Gemini can be called
        if api_key or self.llm_client.is_configured():
            gen_res = self.llm_client.generate(
                prompt=request.query,
                system_instruction=self.system_prompt,
                api_key_override=api_key
            )
            if gen_res.get("success"):
                content = gen_res["text"]
                tools_used.append(ToolExecutionResult(
                    tool_name="gemini_generate",
                    success=True,
                    output={"model": gen_res.get("model", "gemini-3.6-flash")}
                ))
            else:
                content = (
                    f"### General Knowledge Inquiry\n"
                    f"Attempted to process your question via Google Gemini, but encountered an error:\n"
                    f"> `{gen_res.get('error')}`\n\n"
                    f"**Your Query**: {request.query}\n\n"
                    f"Please verify your Gemini API key in the dashboard header or set `GEMINI_API_KEY`."
                )
                tools_used.append(ToolExecutionResult(
                    tool_name="gemini_generate",
                    success=False,
                    output=None,
                    error=gen_res.get("error")
                ))
        else:
            # Fallback when no Gemini API key is configured
            content = (
                "### General Knowledge Agent (Key Required for Open-Ended Web Queries)\n"
                f"You asked: *\"{request.query}\"*\n\n"
                "This query lies outside our dedicated local offline domains (Coding, Finance, Gaming).\n"
                "To answer general knowledge, recipes, history, and unrestricted questions, please provide your **Gemini API Key** in the header at the top of the dashboard.\n\n"
                "Once saved, this agent will immediately synthesize dynamic answers for any subject."
            )

        response = AgentResponse(
            agent_name=self.name,
            domain=self.domain,
            content=content,
            tools_used=tools_used,
            quality_passed=True
        )
        return response

    def quality_check(self, response: AgentResponse) -> bool:
        return True
