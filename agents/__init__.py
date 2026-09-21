"""
Agent definitions package.
"""
from agents.coding_agent import CodingAgent
from agents.finance_agent import FinanceAgent
from agents.gaming_agent import GamingAgent
from agents.general_agent import OmniAgent, GeneralAgent
from agents.router import SupervisorRouter

__all__ = [
    "CodingAgent",
    "FinanceAgent",
    "GamingAgent",
    "OmniAgent",
    "GeneralAgent",
    "SupervisorRouter"
]
