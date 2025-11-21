"""
Test script for the Deep Research Agent

This script demonstrates how to test the agent locally before deploying to LangGraph Cloud.
"""

import os
from dotenv import load_dotenv
from agent import run_research, create_research_agent
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()

def test_simple_query():
    """Test a simple research query."""
    print("=" * 80)
    print("TEST 1: Simple Research Query")
    print("=" * 80)

    query = "What are the key features of Claude 3.5 Sonnet?"
    print(f"\nQuery: {query}\n")

    result = run_research(query, thread_id="test-1")
    print("\nResult:")
    print(result)
    print("\n" + "=" * 80 + "\n")


def test_streaming():
    """Test streaming responses."""
    print("=" * 80)
    print("TEST 2: Streaming Responses")
    print("=" * 80)

    app = create_research_agent()
    query = "What is LangGraph?"

    print(f"\nQuery: {query}\n")
    print("Streaming response:\n")

    config = {"configurable": {"thread_id": "test-2"}}

    for event in app.stream(
        {
            "messages": [HumanMessage(content=query)],
            "is_research_complete": False,
            "research_content": ""
        },
        config=config
    ):
        if "agent" in event:
            if event["agent"]["messages"]:
                msg = event["agent"]["messages"][-1]
                if hasattr(msg, "content") and msg.content:
                    print(f"\n[Agent]: {msg.content[:200]}...")

        if "tools" in event:
            print(f"\n[Tools]: Executing tools...")

        if "format" in event:
            if event["format"]["messages"]:
                msg = event["format"]["messages"][-1]
                print(f"\n[Format]: {msg.content}")

    print("\n" + "=" * 80 + "\n")


def test_continued_conversation():
    """Test conversation continuation with same thread."""
    print("=" * 80)
    print("TEST 3: Continued Conversation")
    print("=" * 80)

    thread_id = "test-3"

    # First query
    query1 = "Tell me about quantum computing"
    print(f"\nQuery 1: {query1}\n")
    result1 = run_research(query1, thread_id=thread_id)
    print(f"Result 1 (truncated): {result1[:300]}...\n")

    # Follow-up query
    query2 = "What are its practical applications?"
    print(f"\nQuery 2 (follow-up): {query2}\n")
    result2 = run_research(query2, thread_id=thread_id)
    print(f"Result 2 (truncated): {result2[:300]}...")

    print("\n" + "=" * 80 + "\n")


def test_graph_structure():
    """Visualize the graph structure."""
    print("=" * 80)
    print("TEST 4: Graph Structure")
    print("=" * 80)

    app = create_research_agent()

    print("\nGraph Nodes:")
    print(app.get_graph().nodes)

    print("\nGraph Edges:")
    for edge in app.get_graph().edges:
        print(f"  {edge}")

    print("\n" + "=" * 80 + "\n")


def main():
    """Run all tests."""
    # Check for required environment variables
    required_vars = ["TAVILY_API_KEY", "ANTHROPIC_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file")
        return

    print("\nStarting Deep Research Agent Tests\n")

    # Run tests
    try:
        test_graph_structure()
        test_simple_query()
        # Uncomment to test streaming and conversations
        # test_streaming()
        # test_continued_conversation()

    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()

    print("\nAll tests completed!")


if __name__ == "__main__":
    main()
