"""
Deep Research Agent - LangGraph Cloud Edition

A comprehensive research agent built with LangGraph for deployment on LangGraph Cloud.
Features web search, extraction, and crawling capabilities powered by Tavily and Claude.
"""

from .agent import create_research_agent, run_research
from .tools import web_search, web_extract, web_crawl, research_tools

__version__ = "1.0.0"
__all__ = [
    "create_research_agent",
    "run_research",
    "web_search",
    "web_extract",
    "web_crawl",
    "research_tools",
]
