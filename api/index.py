"""
Vercel Serverless Function entry point for Tri-Agent System.
"""
import sys
import os

# Add root directory to sys.path so agents, core, and orchestrator can be resolved
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from server import TriAgentHandler

# Vercel serverless Python runtime expects `handler` inheriting from BaseHTTPRequestHandler
class handler(TriAgentHandler):
    pass
