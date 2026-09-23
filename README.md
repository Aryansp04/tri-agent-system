# 🧠 NexusAI — Multi-Agent Orchestration System

An enterprise-grade, production-ready **Multi-Agent Orchestration System** written in pure Python (zero mandatory external dependencies) featuring dynamic intent routing, sub-domain specialization, deterministic guardrails, financial math solvers, AST sandboxed execution, and live integration with Google's Gemini models (`gemini-3.6-flash`).

---

## 🚀 Features

- **Supervisor Orchestrator Router**: Intelligent confidence scoring, keyword scoring, regex intent analysis, and hybrid cross-domain decomposition.
- **Specialized AI Agents**:
  - **Coding Agent**: AST syntax validation, sandboxed Python code execution, automated metric calculation, and quality verification.
  - **Finance Agent**: Deterministic CAGR calculation, Sharpe ratio solver, asset allocation modeling, and risk disclosures.
  - **Gaming Agent**: Boss strategy engine, equipment synergy solver, and strict 3-tier spoiler policy protection (`NO_SPOILERS`, `LIGHT_HINTS`, `FULL_WALKTHROUGH`).
  - **OmniAgent**: Live open-ended inquiry engine powered directly by Google Gemini (`gemini-3.6-flash` / `gemini-3.8-flash`).
- **Live Google Gemini Integration**: Built-in direct REST client using standard library `urllib` — zero third-party packages required.
- **Interactive Dark-Mode Web Dashboard**: Premium glassmorphism UI with animated gradient backgrounds, agent trace inspector, and scenario launcher.
- **CLI Runner**: Interactive and demo modes for headless and terminal usage.
- **Test Suite**: 18 comprehensive automated unit tests covering all routing, agents, tools, guardrails, and error recovery paths.

---

## 📁 Repository Structure

```
nexusai/
├── core/
│   ├── models.py           # DomainType, SpoilerLevel, RouteDecision, AgentRequest, AgentResponse
│   ├── base_agent.py       # Abstract BaseAgent with tool registry and quality gates
│   └── llm_client.py       # Lightweight urllib client for Google Gemini API
├── agents/
│   ├── router.py           # SupervisorRouter with multi-domain confidence scoring
│   ├── coding_agent.py     # Python AST analysis & sandboxed execution
│   ├── finance_agent.py    # Deterministic financial math & scenario analysis
│   ├── gaming_agent.py     # Boss strategy engine & spoiler enforcement
│   └── general_agent.py    # OmniAgent — live open-ended inquiry engine
├── web/
│   └── index.html          # Interactive responsive web UI & dashboard
├── tests/
│   └── test_tri_agent.py   # Full test suite (18 unit tests)
├── orchestrator.py         # Multi-Agent coordinator & fallback handling
├── server.py               # Standard library HTTP API and web server
├── main.py                 # CLI interface
├── start_web_ui.bat        # Windows one-click launcher
└── run_cli.bat             # Terminal launcher
```

---

## ⚡ Quick Start

### 1. Run the Web Dashboard
```bash
python server.py 8080
```
Open **[http://localhost:8080](http://localhost:8080)** in your browser.

### 2. Run the CLI
```bash
# Automated demo across all domains
python main.py --demo

# Interactive prompt
python main.py
```

### 3. Run the Unit Tests
```bash
python -m unittest discover -s tests
```

---

## 🔑 Activating Google Gemini Live AI

Set the `GEMINI_API_KEY` environment variable:

```bash
# Windows PowerShell
$env:GEMINI_API_KEY="your-api-key"

# Linux / macOS
export GEMINI_API_KEY="your-api-key"
```

Or create a `.env` file in the project root:
```
GEMINI_API_KEY=your-api-key
```

For Vercel deployment, add `GEMINI_API_KEY` as an environment variable in your project settings.

---

## 🛡️ Engineering Disciplines Implemented

1. **Problem Decomposition**: Hybrid cross-domain queries are routed and answered with collaborative agent handoffs.
2. **Context Engineering**: Strict system prompts, role boundaries, and isolated memory per agent.
3. **Deterministic Tools**: Python AST syntax checks, execution sandboxes, and financial mathematical formulas execute locally rather than relying on LLM hallucinations.
4. **Inversion & Guardrails**: Automatic fallbacks for out-of-domain queries and spoiler protection policies.
5. **Quality Verification**: Quality gates validate non-empty structured responses and tool execution status before returning responses to the user.
