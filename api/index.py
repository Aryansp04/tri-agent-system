"""
Vercel Serverless Function entry point for Tri-Agent System.
Runs with pure Python standard library on Vercel's Serverless Python runtime.
"""
import sys
import os
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.models import AgentRequest, SpoilerLevel
from orchestrator import MultiAgentOrchestrator

# Global orchestrator instance (cached across serverless warm invocations)
orchestrator = MultiAgentOrchestrator()


class handler(BaseHTTPRequestHandler):
    def _get_path(self):
        """
        Determine actual requested API route across Vercel rewrite headers.
        """
        for h in ("x-forwarded-uri", "x-matched-path", "x-vercel-matched-path", "x-original-uri"):
            val = self.headers.get(h)
            if val:
                return urlparse(val).path
        return urlparse(self.path).path

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self):
        req_path = self._get_path()

        if req_path.endswith("/health") or req_path == "/api/health":
            self._send_json({
                "status": "healthy",
                "service": "Tri-Agent System (Vercel Serverless)",
                "model": "gemini-3.6-flash",
                "has_server_key": bool(os.environ.get("GEMINI_API_KEY"))
            })
            return

        if req_path.endswith("/demo-scenarios") or req_path == "/api/demo-scenarios":
            scenarios = [
                {
                    "title": "Pure Coding: Variance Calculation",
                    "domain": "CODING",
                    "query": "Write a Python function to compute the variance of a list of numbers.",
                    "spoiler_level": "NO_SPOILERS"
                },
                {
                    "title": "Pure Finance: Portfolio CAGR & Scenarios",
                    "domain": "FINANCE",
                    "query": "What is the CAGR and risk profile of an investment growing from $10k to $21.5k over 5 years?",
                    "spoiler_level": "NO_SPOILERS"
                },
                {
                    "title": "Pure Gaming: Malenia Boss Strategy (Spoiler Protected)",
                    "domain": "GAMING",
                    "query": "What build and strategy should I use against Malenia in Elden Ring?",
                    "spoiler_level": "NO_SPOILERS"
                },
                {
                    "title": "Hybrid Cross-Domain: Sharpe Ratio Algorithm",
                    "domain": "HYBRID",
                    "query": "Write a Python script to calculate the portfolio Sharpe ratio and asset allocation.",
                    "spoiler_level": "NO_SPOILERS"
                },
                {
                    "title": "Inversion & Error Recovery: Out-of-Domain Query",
                    "domain": "GENERAL",
                    "query": "Can you tell me how to bake sourdough bread?",
                    "spoiler_level": "NO_SPOILERS"
                }
            ]
            self._send_json(scenarios)
            return

        # Fallback / diagnostics
        self._send_json({
            "service": "Tri-Agent System (Vercel Serverless)",
            "detected_path": req_path,
            "raw_path": self.path,
            "has_server_key": bool(os.environ.get("GEMINI_API_KEY")),
            "available_endpoints": ["/api/health", "/api/demo-scenarios", "/api/key-test", "/api/chat"]
        })

    def do_POST(self):
        req_path = self._get_path()
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            data = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            data = {}

        if req_path.endswith("/key-test") or req_path == "/api/key-test":
            try:
                api_key = data.get("api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
                if not api_key:
                    self._send_json({"valid": False, "error": "No API key provided or configured on server."})
                    return
                from core.llm_client import GeminiClient
                client = GeminiClient(api_key=api_key)
                result = client.generate(prompt="Reply with only the word: OK", max_output_tokens=500)
                if result.get("success"):
                    self._send_json({"valid": True, "model": result.get("model")})
                else:
                    self._send_json({"valid": False, "error": result.get("error")})
            except Exception as e:
                self._send_json({"valid": False, "error": str(e)})
            return

        if req_path.endswith("/chat") or req_path == "/api/chat" or req_path == "/api" or req_path == "/api/index.py":
            try:
                query = data.get("query", "").strip()
                spoiler_str = data.get("spoiler_preference", "NO_SPOILERS")

                try:
                    spoiler_pref = SpoilerLevel[spoiler_str]
                except KeyError:
                    spoiler_pref = SpoilerLevel.NO_SPOILERS

                api_key = data.get("api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip() or None

                if not query:
                    self._send_json({"error": "Empty query provided"}, status=400)
                    return

                req = AgentRequest(query=query, spoiler_preference=spoiler_pref, api_key=api_key)
                resp = orchestrator.handle_request(req)

                route_dec = resp.metadata.get("route_decision")
                tools_data = [
                    {
                        "tool_name": t.tool_name,
                        "success": t.success,
                        "output": t.output,
                        "error": t.error
                    } for t in resp.tools_used
                ]

                result_payload = {
                    "agent_name": resp.agent_name,
                    "domain": resp.domain.value,
                    "content": resp.content,
                    "quality_passed": resp.quality_passed,
                    "tools_used": tools_data,
                    "route_decision": {
                        "primary_domain": route_dec.primary_domain.value if route_dec else resp.domain.value,
                        "confidence": route_dec.confidence if route_dec else 1.0,
                        "reasoning": route_dec.reasoning if route_dec else "",
                        "is_hybrid": route_dec.is_hybrid if route_dec else False,
                        "secondary_domain": route_dec.secondary_domain.value if route_dec and route_dec.secondary_domain else None
                    } if route_dec else None
                }
                self._send_json(result_payload)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
            return

        self._send_json({"error": f"Endpoint not found: {req_path}"}, status=404)
