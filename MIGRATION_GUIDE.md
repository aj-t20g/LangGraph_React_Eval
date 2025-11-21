# Migration Guide: Strands to LangGraph Cloud

This document outlines the key differences between the original Strands-based agent and the refactored LangGraph Cloud version.

## Overview of Changes

The agent has been refactored from a **Strands framework** implementation deployed on **AWS Bedrock AgentCore** to a **LangGraph** implementation for deployment on **LangGraph Cloud**.

## Architecture Comparison

### Original Architecture (Strands)

```
User Query
    ↓
Agent (Strands)
    ↓
Tools (web_search, web_extract, web_crawl, format_research_response)
    ↓
Response
```

**Characteristics:**
- Linear execution flow
- Simple agent loop
- Tools wrapped with `@strands.tool`
- Uses BedrockModel for Claude access
- Deployed via Bedrock AgentCore

### New Architecture (LangGraph)

```
User Query
    ↓
Agent Node (reasoning)
    ↓
    ├→ Continue? → Tools Node → back to Agent Node
    │
    └→ Complete? → Format Node → End
```

**Characteristics:**
- Graph-based execution with nodes and edges
- Conditional routing between nodes
- State persistence with checkpointing
- Tools wrapped with `@langchain_core.tools.tool`
- Uses ChatAnthropic for Claude access
- Deployed via LangGraph Cloud

## Code-Level Changes

### 1. Framework Imports

**Original (Strands):**
```python
from strands import Agent, tool
from strands.models import BedrockModel
```

**Refactored (LangGraph):**
```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
```

### 2. Agent Definition

**Original (Strands):**
```python
def create_research_agent():
    bedrock_model = BedrockModel(model_id=MODEL_ID, region_name=AWS_REGION)

    return Agent(
        model=bedrock_model,
        system_prompt=get_system_prompt(),
        tools=[web_search, web_extract, web_crawl, format_research_response],
    )
```

**Refactored (LangGraph):**
```python
def create_research_agent():
    model = ChatAnthropic(model=model_id, temperature=0, max_tokens=4096)
    model_with_tools = model.bind_tools(research_tools)

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(research_tools))
    workflow.add_node("format", format_response_node)

    # Add edges and routing logic...

    return workflow.compile(checkpointer=MemorySaver())
```

### 3. State Management

**Original (Strands):**
- No explicit state management
- Implicit conversation history

**Refactored (LangGraph):**
```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    research_content: str
    is_research_complete: bool
```

State is explicitly defined and tracked throughout execution.

### 4. Tool Definitions

**Original (Strands):**
```python
@tool
def web_search(query: str, time_range: str | None = None, ...) -> str:
    """Perform a web search..."""
    # Implementation
```

**Refactored (LangGraph):**
```python
@tool
def web_search(query: str, time_range: Optional[str] = None, ...) -> str:
    """Perform a web search..."""
    # Same implementation, but using Optional for type hints
```

**Key Differences:**
- Type hints changed from `str | None` to `Optional[str]` for broader compatibility
- Tool decorator is from `langchain_core.tools` instead of `strands`
- Tools return the same format but are integrated differently

### 5. Execution Flow

**Original (Strands):**
```python
def run_research(query: str):
    agent = create_research_agent()
    return agent(query)
```

Simple synchronous execution.

**Refactored (LangGraph):**
```python
def run_research(query: str, thread_id: str = "default") -> str:
    app = create_research_agent()
    config = {"configurable": {"thread_id": thread_id}}

    result = app.invoke(
        {
            "messages": [HumanMessage(content=query)],
            "is_research_complete": False,
            "research_content": ""
        },
        config=config
    )

    return result["messages"][-1].content
```

**Enhancements:**
- Thread-based conversation persistence
- Explicit state initialization
- Configuration support for different execution modes

### 6. Response Formatting

**Original (Strands):**
- `format_research_response` was a tool that the agent could call
- Required manual invocation by the agent

**Refactored (LangGraph):**
- Dedicated `format_response_node` that automatically activates when research is complete
- Conditional routing determines when to format
- More consistent output structure

## Deployment Differences

### Original Deployment (Bedrock AgentCore)

1. **Configuration:** `.bedrock_agentcore.yaml`
2. **Command:** `agentcore deploy`
3. **Hosting:** AWS ECS/Fargate
4. **Auth:** AWS IAM roles
5. **Scaling:** Manual configuration

### New Deployment (LangGraph Cloud)

1. **Configuration:** `langgraph.json`
2. **Command:** `langgraph deploy`
3. **Hosting:** LangGraph Cloud infrastructure
4. **Auth:** LangGraph Cloud API keys
5. **Scaling:** Automatic

## Feature Additions

### New Capabilities in LangGraph Version

1. **State Persistence**
   - Conversations can be resumed using thread IDs
   - State is checkpointed between invocations

2. **Streaming Support**
   ```python
   for event in app.stream(input, config):
       print(event)
   ```

3. **Visual Debugging**
   - LangGraph Studio provides visual graph inspection
   - Step-by-step execution tracing
   - State inspection at each node

4. **Flexible Routing**
   - Conditional logic based on agent state
   - Dynamic decision-making about next steps

5. **Better Error Handling**
   - Node-level error isolation
   - Retry mechanisms
   - Graceful degradation

## Environment Variables

### Original
```env
TAVILY_API_KEY=...
AWS_REGION=us-east-1
MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
```

### Refactored
```env
TAVILY_API_KEY=...
ANTHROPIC_API_KEY=...
MODEL_ID=claude-sonnet-4-20250514
```

**Key Change:** Direct Anthropic API access instead of AWS Bedrock (though Bedrock can still be used with modifications).

## Testing Differences

### Original
```python
from agent import create_research_agent

agent = create_research_agent()
result = agent("What is AI?")
```

### Refactored
```python
from agent import run_research

# Simple usage
result = run_research("What is AI?")

# With conversation persistence
result1 = run_research("What is AI?", thread_id="user-123")
result2 = run_research("Tell me more", thread_id="user-123")  # Continues context
```

## Cost Implications

### Original (Bedrock AgentCore)
- Pay for ECS/Fargate compute time
- AWS Bedrock API costs
- Data transfer costs
- ECR storage costs

### Refactored (LangGraph Cloud)
- Pay per invocation
- Direct Anthropic API costs (typically cheaper)
- No infrastructure management overhead
- Free tier available

## Monitoring and Observability

### Original
- AWS CloudWatch logs
- Custom metrics via AWS
- Manual log parsing

### Refactored
- Built-in LangGraph Cloud dashboards
- Execution traces in LangGraph Studio
- Automatic performance metrics
- Visual graph execution flow

## Migration Checklist

If migrating from the original to LangGraph:

- [ ] Install LangGraph CLI: `pip install langgraph-cli`
- [ ] Update dependencies in `requirements.txt`
- [ ] Obtain Anthropic API key (if not using Bedrock)
- [ ] Update environment variables
- [ ] Test locally with `test_agent.py`
- [ ] Deploy with `langgraph deploy`
- [ ] Set environment variables in cloud
- [ ] Update client code to use new API endpoints
- [ ] Monitor initial deployments for issues

## Backward Compatibility

The refactored version is **not directly backward compatible** with the Strands version. Client code will need to be updated to:

1. Use new API endpoints (LangGraph Cloud vs AgentCore)
2. Format requests according to LangGraph input schema
3. Handle responses in the new format
4. Use thread IDs for conversation persistence

## Recommended Next Steps

1. **Test locally** using `test_agent.py` to verify functionality
2. **Deploy to staging** environment first
3. **Run comparison tests** between old and new versions
4. **Update documentation** for end users
5. **Migrate gradually** using traffic splitting if possible

## Performance Considerations

- **Latency:** LangGraph Cloud typically has lower cold start times
- **Throughput:** Automatic scaling handles bursts better
- **State Management:** Checkpointing adds minimal overhead (~10ms per save)
- **Tool Execution:** Similar performance to original

## Rollback Strategy

If you need to rollback:

1. Original code is preserved in the parent directory
2. Bedrock AgentCore deployment configuration is in `.bedrock_agentcore.yaml`
3. Can run both versions in parallel during migration
4. DNS/routing can be switched back if needed

## Support

For issues specific to:
- **Original version:** Check Bedrock AgentCore documentation
- **Refactored version:** Check LangGraph Cloud documentation
- **Tools (Tavily):** Check Tavily API documentation
- **Model (Claude):** Check Anthropic documentation
