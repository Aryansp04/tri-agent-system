"""
Data models and shared representations for the Tri-Agent System.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DomainType(str, Enum):
    CODING = "CODING"
    FINANCE = "FINANCE"
    GAMING = "GAMING"
    HYBRID = "HYBRID"
    GENERAL = "GENERAL"


class SpoilerLevel(str, Enum):
    NO_SPOILERS = "NO_SPOILERS"
    LIMITED_SPOILERS = "LIMITED_SPOILERS"
    FULL_SPOILERS = "FULL_SPOILERS"


@dataclass
class RouteDecision:
    primary_domain: DomainType
    confidence: float
    secondary_domain: Optional[DomainType] = None
    reasoning: str = ""
    is_hybrid: bool = False
    extracted_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentRequest:
    query: str
    session_id: str = "default_session"
    context: Dict[str, Any] = field(default_factory=dict)
    spoiler_preference: SpoilerLevel = SpoilerLevel.NO_SPOILERS
    api_key: Optional[str] = None


@dataclass
class ToolExecutionResult:
    tool_name: str
    success: bool
    output: Any
    error: Optional[str] = None


@dataclass
class AgentResponse:
    agent_name: str
    domain: DomainType
    content: str
    tools_used: List[ToolExecutionResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_passed: bool = True
