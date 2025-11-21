import datetime
import os
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from tools import research_tools, web_search, web_extract, web_crawl


# Define the state for our agent
class AgentState(TypedDict):
    """State definition for the research agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    research_content: str
    is_research_complete: bool


def get_system_prompt() -> str:
    """Generate the system prompt for the research agent."""
    today = datetime.datetime.today().strftime("%A, %B %d, %Y")

    return f"""
You are an expert research assistant specializing in deep, comprehensive information gathering and analysis.
You are equipped with advanced web tools: Web Search, Web Extract, and Web Crawl.
Your mission is to conduct comprehensive, accurate, and up-to-date research, grounding your findings in credible web sources.

**Today's Date:** {today}

Your TOOLS include:

1. WEB SEARCH
- Conduct thorough web searches using the web_search tool.
- You will enter a search query and the web_search tool will return 10 results ranked by semantic relevance.
- Your search results will include the title, url, and content of 10 results ranked by semantic relevance.

2. WEB EXTRACT
- Conduct web extraction with the web_extract tool.
- You will enter a url and the web_extract tool will extract the content of the page.
- Your extract results will include the url and content of the page.
- This tool is great for finding all the information that is linked from a single page.

3. WEB CRAWL
- Conduct deep web crawls with the web_crawl tool.
- You will enter a url and the web_crawl tool will find all the nested links.
- Your crawl results will include the url and content of the pages that were discovered.
- This tool is great for finding all the information that is linked from a single page.

3. FORMATTING RESEARCH RESPONSE
- You will use the format_research_response tool to format your research response.
- This tool will create a well-structured response that is easy to read and understand.
- The response will clearly address the user's query, the research results.
- The response will be in markdown format.

RULES:
- You must start the research process by creating a plan. Think step by step about what you need to do to answer the research question.
- You can iterate on your research plan and research response multiple times, using combinations of the tools available to you until you are satisfied with the results.
- You must use the format_research_response tool at the end of your research process.
"""


def create_research_agent():
    """Create and configure the research agent graph."""

    # Initialize the model
    model_id = os.getenv("MODEL_ID", "claude-sonnet-4-20250514")
    model = ChatAnthropic(
        model=model_id,
        temperature=0,
        max_tokens=4096
    )

    # Bind tools to the model
    model_with_tools = model.bind_tools(research_tools)

    # Define the agent node
    def agent_node(state: AgentState) -> AgentState:
        """Main agent reasoning node."""
        messages = list(state.get("messages", []))

        # Ensure we have messages
        if not messages:
            raise ValueError("No messages provided to agent")

        # Separate system messages from other messages
        system_messages = [m for m in messages if isinstance(m, SystemMessage)]
        non_system_messages = [m for m in messages if not isinstance(m, SystemMessage)]

        # Ensure we have at least one non-system message
        if not non_system_messages:
            raise ValueError("At least one non-system message (human/ai/tool) is required")

        # Add our system prompt if not already present
        if not system_messages:
            system_messages = [SystemMessage(content=get_system_prompt())]

        # Combine: system messages first, then the rest
        messages = system_messages + non_system_messages

        response = model_with_tools.invoke(messages)

        # Check if research is complete
        is_complete = "RESEARCH_COMPLETE" in response.content if response.content else False

        return {
            "messages": [response],
            "is_research_complete": is_complete
        }

    # Define the formatting node
    def format_response_node(state: AgentState) -> AgentState:
        """Format the final research response."""
        messages = state["messages"]
        research_content = state.get("research_content", "")

        format_prompt = f"""
You are a specialized Research Response Formatter Agent. Your role is to transform research content into well-structured, properly cited, and reader-friendly formats.

Core formatting requirements (ALWAYS apply):
1. Include inline citations using [n] notation for EVERY factual claim
2. Provide a complete "Sources" section at the end with numbered references and urls
3. Write concisely - no repetition or filler words
4. Ensure information density - every sentence should add value
5. Maintain professional, objective tone
6. Format your response in markdown

Based on the conversation and research gathered, create a comprehensive, well-formatted response that:
- Directly addresses the user's original question
- Is properly structured with clear sections
- Includes inline citations for all factual claims
- Has a complete sources section at the end
- Is written in a style appropriate to the query (direct answer, report, summary, etc.)

Your response should be polished and contain only information relevant to the user's query.
"""

        format_messages = messages + [HumanMessage(content=format_prompt)]
        response = model.invoke(format_messages)

        return {"messages": [response]}

    # Define routing logic
    def should_continue(state: AgentState) -> str:
        """Determine if we should continue or format the response."""
        messages = state["messages"]
        last_message = messages[-1]

        # If research is marked complete or no tool calls, format the response
        if state.get("is_research_complete", False) or not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            # Check if last message indicates completion
            if isinstance(last_message, AIMessage) and last_message.content:
                if "RESEARCH_COMPLETE" in last_message.content:
                    return "format"
            return "format"

        # Otherwise continue with tool execution
        return "continue"

    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(research_tools))
    workflow.add_node("format", format_response_node)

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "format": "format"
        }
    )

    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")

    # Add edge from format to end
    workflow.add_edge("format", END)

    # Compile with checkpointing
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    return app


def run_research(query: str, thread_id: str = "default") -> str:
    """Run a research query through the agent.

    Args:
        query: The research question or query
        thread_id: Thread ID for conversation persistence

    Returns:
        The final formatted research response
    """
    app = create_research_agent()

    # Create initial state
    config = {"configurable": {"thread_id": thread_id}}

    # Run the agent
    result = app.invoke(
        {"messages": [HumanMessage(content=query)], "is_research_complete": False, "research_content": ""},
        config=config
    )

    # Return the last message content
    return result["messages"][-1].content
