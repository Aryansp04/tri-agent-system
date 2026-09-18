"""
Base class for domain-specialized agents.
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
from core.models import AgentRequest, AgentResponse, DomainType, ToolExecutionResult


class BaseAgent(ABC):
    def __init__(self, name: str, domain: DomainType, system_prompt: str):
        self.name = name
        self.domain = domain
        self.system_prompt = system_prompt
        self.tools: Dict[str, Callable] = {}
        self.memory: Dict[str, Any] = {}

    def register_tool(self, name: str, func: Callable):
        """Register a tool available to this agent."""
        self.tools[name] = func

    def execute_tool(self, tool_name: str, **kwargs) -> ToolExecutionResult:
        """Safely execute an authorized tool."""
        if tool_name not in self.tools:
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                output=None,
                error=f"Tool '{tool_name}' is not registered for agent '{self.name}'."
            )
        try:
            res = self.tools[tool_name](**kwargs)
            return ToolExecutionResult(tool_name=tool_name, success=True, output=res)
        except Exception as e:
            return ToolExecutionResult(tool_name=tool_name, success=False, output=None, error=str(e))

    def update_memory(self, key: str, value: Any):
        """Update domain-specific isolated memory."""
        self.memory[key] = value

    def get_memory(self, key: str, default: Any = None) -> Any:
        return self.memory.get(key, default)

    @abstractmethod
    def process(self, request: AgentRequest) -> AgentResponse:
        """Process the domain-specific request and return an AgentResponse."""
        pass

    @abstractmethod
    def quality_check(self, response: AgentResponse) -> bool:
        """Domain-specific validation gate before delivering output to user."""
        pass
