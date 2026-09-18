"""
Automated unit and integration test suite for the Tri-Agent system.
"""
import unittest
from core.models import AgentRequest, DomainType, SpoilerLevel
from agents.router import SupervisorRouter
from agents.coding_agent import CodingAgent
from agents.finance_agent import FinanceAgent
from agents.gaming_agent import GamingAgent
from orchestrator import MultiAgentOrchestrator


class TestSupervisorRouter(unittest.TestCase):
    def setUp(self):
        self.router = SupervisorRouter()

    def test_route_coding(self):
        req = AgentRequest(query="Can you help me write a Python function to parse JSON with error handling?")
        decision = self.router.route(req)
        self.assertEqual(decision.primary_domain, DomainType.CODING)
        self.assertGreater(decision.confidence, 0.5)

    def test_route_finance(self):
        req = AgentRequest(query="Calculate the CAGR and Sharpe ratio for my equity portfolio.")
        decision = self.router.route(req)
        self.assertEqual(decision.primary_domain, DomainType.FINANCE)
        self.assertGreater(decision.confidence, 0.5)

    def test_route_gaming(self):
        req = AgentRequest(query="What is the best build and strategy to defeat Malenia in Elden Ring?")
        decision = self.router.route(req)
        self.assertEqual(decision.primary_domain, DomainType.GAMING)
        self.assertGreater(decision.confidence, 0.5)

    def test_route_hybrid(self):
        req = AgentRequest(query="Write a Python script to calculate portfolio Sharpe ratio and asset allocation.")
        decision = self.router.route(req)
        self.assertTrue(decision.is_hybrid)
        self.assertIn(decision.primary_domain, [DomainType.CODING, DomainType.FINANCE])
        self.assertIn(decision.secondary_domain, [DomainType.CODING, DomainType.FINANCE])

    def test_route_unclassified_fallback(self):
        req = AgentRequest(query="What is the weather like on Mars today?")
        decision = self.router.route(req)
        self.assertEqual(decision.primary_domain, DomainType.GENERAL)
        self.assertLess(decision.confidence, 0.5)


class TestCodingAgent(unittest.TestCase):
    def setUp(self):
        self.agent = CodingAgent()

    def test_syntax_checker_valid(self):
        code = "def add(a, b):\n    return a + b\n"
        res = self.agent.check_syntax(code)
        self.assertTrue(res["valid"])

    def test_syntax_checker_invalid(self):
        code = "def broken(:\n"
        res = self.agent.check_syntax(code)
        self.assertFalse(res["valid"])
        self.assertIn("SyntaxError", res["error"])

    def test_sandbox_execution(self):
        code = "print(10 + 25)"
        res = self.agent.execute_python_sandbox(code)
        self.assertTrue(res["success"])
        self.assertEqual(res["stdout"], "35")
        self.assertEqual(res["exit_code"], 0)


class TestFinanceAgent(unittest.TestCase):
    def setUp(self):
        self.agent = FinanceAgent()

    def test_cagr_calculation(self):
        # 10,000 -> 20,000 in 3 years => (2)^(1/3) - 1 ≈ 25.99%
        res = self.agent.calculate_cagr(10000.0, 20000.0, 3.0)
        self.assertAlmostEqual(res["cagr_percent"], 25.99, places=1)

    def test_sharpe_ratio(self):
        # Rp = 0.12, Rf = 0.04, StDev = 0.10 => (0.12 - 0.04) / 0.10 = 0.8
        res = self.agent.calculate_sharpe_ratio(0.12, 0.04, 0.10)
        self.assertEqual(res["sharpe_ratio"], 0.8)

    def test_scenario_analysis(self):
        scenarios = self.agent.run_scenarios(10000.0, 5)
        self.assertIn("conservative", scenarios)
        self.assertIn("base", scenarios)
        self.assertIn("bull", scenarios)
        self.assertGreater(scenarios["bull"]["projected_value"], scenarios["base"]["projected_value"])


class TestGamingAgent(unittest.TestCase):
    def setUp(self):
        self.agent = GamingAgent()

    def test_boss_database(self):
        res = self.agent.query_boss_strategy("malenia")
        self.assertIn("Waterfowl Dance", res["key_attack"])
        self.assertIn("Frostbite", res["weakness"])

    def test_spoiler_filtering(self):
        # NO_SPOILERS
        req_no_spoiler = AgentRequest(query="How to beat Malenia", spoiler_preference=SpoilerLevel.NO_SPOILERS)
        resp_no = self.agent.process(req_no_spoiler)
        self.assertIn("NO_SPOILERS", resp_no.content)
        self.assertNotIn("Twin prodigy afflicted", resp_no.content)

        # FULL_SPOILERS
        req_full = AgentRequest(query="How to beat Malenia", spoiler_preference=SpoilerLevel.FULL_SPOILERS)
        resp_full = self.agent.process(req_full)
        self.assertIn("Twin prodigy afflicted", resp_full.content)


class TestOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orchestrator = MultiAgentOrchestrator()

    def test_end_to_end_coding(self):
        req = AgentRequest(query="Write a python function to compute variance")
        resp = self.orchestrator.handle_request(req)
        self.assertEqual(resp.domain, DomainType.CODING)
        self.assertTrue(resp.quality_passed)
        self.assertGreater(len(resp.tools_used), 0)

    def test_end_to_end_finance(self):
        req = AgentRequest(query="Calculate investment returns and CAGR for 5 years")
        resp = self.orchestrator.handle_request(req)
        self.assertEqual(resp.domain, DomainType.FINANCE)
        self.assertTrue(resp.quality_passed)
        self.assertIn("CAGR", resp.content)

    def test_end_to_end_gaming(self):
        req = AgentRequest(query="What is the best build and strategy to beat Malenia?", spoiler_preference=SpoilerLevel.NO_SPOILERS)
        resp = self.orchestrator.handle_request(req)
        self.assertEqual(resp.domain, DomainType.GAMING)
        self.assertTrue(resp.quality_passed)

    def test_end_to_end_hybrid(self):
        req = AgentRequest(query="Write a Python script to calculate portfolio Sharpe ratio and asset allocation")
        resp = self.orchestrator.handle_request(req)
        self.assertEqual(resp.domain, DomainType.HYBRID)
        self.assertIn("Collaborative Multi-Agent Execution", resp.content)
        self.assertTrue(resp.quality_passed)

    def test_end_to_end_unclassified(self):
        req = AgentRequest(query="Tell me an unrelated random fact")
        resp = self.orchestrator.handle_request(req)
        self.assertEqual(resp.domain, DomainType.GENERAL)
        self.assertIn("General Knowledge Agent", resp.content)


if __name__ == "__main__":
    unittest.main()
