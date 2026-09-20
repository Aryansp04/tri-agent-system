"""
Local HTTP Server serving the Tri-Agent Interactive Web Dashboard and REST API.
Runs with zero external dependencies using Python standard library.
"""
import http.server
import json
import os
import socketserver
import sys
from urllib.parse import urlparse

from core.models import AgentRequest, SpoilerLevel
from orchestrator import MultiAgentOrchestrator

PORT = 8080
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")


def load_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and v and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

load_env()


class TriAgentHandler(http.server.SimpleHTTPRequestHandler):
    orchestrator = MultiAgentOrchestrator()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send_json({
                "status": "healthy",
                "service": "Tri-Agent System",
                "model": "gemini-3.6-flash",
                "has_server_key": bool(os.environ.get("GEMINI_API_KEY"))
            })
        elif parsed.path == "/api/demo-scenarios":
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
        else:
            # Fallback to serving static files from web/
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)

        # Dedicated endpoint to validate Gemini API key
        if parsed.path == "/api/key-test":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                data = json.loads(body.decode("utf-8")) if body else {}
                api_key = data.get("api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
                if not api_key:
                    self._send_json({"valid": False, "error": "No API key provided or configured."})
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

        if parsed.path == "/api/chat":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                data = json.loads(body.decode("utf-8")) if body else {}
                query = data.get("query", "").strip()
                spoiler_str = data.get("spoiler_preference", "NO_SPOILERS")

                try:
                    spoiler_pref = SpoilerLevel[spoiler_str]
                except KeyError:
                    spoiler_pref = SpoilerLevel.NO_SPOILERS

                api_key = data.get("api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip() or None
                print(f"[server] api_key in use: {'SET (len={})'.format(len(api_key)) if api_key else 'NONE'}")

                if not query:
                    self._send_json({"error": "Empty query provided"}, status=400)
                    return

                req = AgentRequest(query=query, spoiler_preference=spoiler_pref, api_key=api_key)
                resp = self.orchestrator.handle_request(req)

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
        else:
            self.send_error(404, "Endpoint not found")

    def _send_json(self, data: any, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.end_headers()
        self.wfile.write(body)


def run_server(port: int = PORT):
    os.makedirs(WEB_DIR, exist_ok=True)
    server_address = ("", port)
    
    # Allow address reuse
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(server_address, TriAgentHandler) as httpd:
        print(f"============================================================")
        print(f" Tri-Agent Web Dashboard running at: http://127.0.0.1:{port}")
        print(f" Web UI: Open http://localhost:{port} in your browser")
        print(f" Press Ctrl+C to stop the server.")
        print(f"============================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(p)
