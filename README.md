# Deep Research Agent - LangGraph Cloud Deployment

This is a refactored version of the Deep Research Agent optimized for deployment on LangGraph Cloud. The agent specializes in comprehensive web-based research using advanced tools like web search, web extraction, and web crawling.

## Architecture Overview

The agent is built using LangGraph's StateGraph architecture with the following components:

### Key Components

1. **State Management** (`AgentState`)
   - `messages`: Conversation history with message annotations
   - `research_content`: Accumulated research findings
   - `is_research_complete`: Flag to track research completion

2. **Nodes**
   - `agent`: Main reasoning node that plans and coordinates research
   - `tools`: Tool execution node for web search, extract, and crawl operations
   - `format`: Response formatting node that creates structured, cited outputs

3. **Tools** (from `tools.py`)
   - `web_search`: Semantic web search via Tavily API (returns top 10 results)
   - `web_extract`: Deep content extraction from specific URLs
   - `web_crawl`: Recursive crawling with configurable depth

4. **Workflow**
   ```
   Start → Agent → (Tools ↔ Agent)* → Format → End
   ```

## Migration Changes from Original

### From Strands Framework to LangGraph

| Original (Strands) | LangGraph Cloud |
|-------------------|-----------------|
| `strands.Agent` | `StateGraph` with nodes |
| `strands.tool` decorator | `langchain_core.tools.tool` |
| `BedrockModel` | `ChatAnthropic` |
| Linear agent flow | Graph-based workflow with conditional routing |
| No state persistence | Built-in checkpointing with `MemorySaver` |
| AgentCore deployment | LangGraph Cloud deployment |

### Key Improvements

1. **State Persistence**: Built-in checkpointing allows conversation resumption
2. **Flexible Routing**: Conditional logic determines when to continue research vs format response
3. **Tool Integration**: Native LangChain tool integration
4. **Scalability**: LangGraph Cloud handles scaling automatically
5. **Monitoring**: Better observability through LangGraph Studio

## Prerequisites

- Python 3.11+
- [LangGraph CLI](https://langchain-ai.github.io/langgraph/cloud/reference/cli/) installed
- API Keys:
  - Anthropic API Key (for Claude)
  - Tavily API Key (for web search)

## Local Development Setup

### 1. Install Dependencies

```bash
cd LangGraph
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
TAVILY_API_KEY=tvly-xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx
MODEL_ID=claude-sonnet-4-20250514
```

### 3. Test Locally

```python
from agent import run_research

# Run a research query
result = run_research("What are the latest developments in AI agents?")
print(result)
```

Or use the LangGraph CLI:

```bash
langgraph test
```

## LangGraph Cloud Deployment

### 1. Install LangGraph CLI

```bash
pip install langgraph-cli
```

### 2. Login to LangGraph Cloud

```bash
langgraph login
```

### 3. Create a New Deployment

```bash
langgraph deploy
```

This will:
- Package your agent code
- Upload to LangGraph Cloud
- Set up the infrastructure
- Provide you with an API endpoint

### 4. Configure Environment Variables in Cloud

After deployment, set your environment variables in the LangGraph Cloud dashboard:

```bash
langgraph env set TAVILY_API_KEY=tvly-xxxxx
langgraph env set ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### 5. Test Your Deployment

```bash
langgraph invoke research_agent '{"messages": [{"role": "human", "content": "Latest AI trends 2025"}]}'
```

## Using the Deployed Agent

### Via API (HTTP)

```python
import requests

url = "https://your-deployment.langgraph.app/research_agent/invoke"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "your-api-key"
}

payload = {
    "input": {
        "messages": [
            {"role": "human", "content": "What are quantum computers?"}
        ],
        "is_research_complete": False,
        "research_content": ""
    },
    "config": {
        "configurable": {
            "thread_id": "user-123"
        }
    }
}

response = requests.post(url, json=payload, headers=headers)
result = response.json()
print(result["output"]["messages"][-1]["content"])
```

### Via LangGraph SDK

```python
from langgraph_sdk import get_client

client = get_client(url="https://your-deployment.langgraph.app")

thread = client.threads.create()

result = client.runs.create(
    thread_id=thread["thread_id"],
    assistant_id="research_agent",
    input={
        "messages": [{"role": "human", "content": "Latest AI trends?"}],
        "is_research_complete": False,
        "research_content": ""
    }
)

print(result)
```

## Configuration Files

### `langgraph.json`

This file defines the deployment configuration:

```json
{
  "dependencies": ["."],
  "graphs": {
    "research_agent": "./agent.py:create_research_agent"
  },
  "env": ".env"
}
```

- `dependencies`: Python package dependencies
- `graphs`: Maps graph names to their factory functions
- `env`: Environment file for local development

## Advanced Features

### Conversation Persistence

The agent uses checkpointing to maintain conversation state:

```python
# Same thread_id continues the conversation
result1 = run_research("Tell me about quantum computing", thread_id="user-123")
result2 = run_research("What are its applications?", thread_id="user-123")
```

### Streaming Responses

For real-time updates, use streaming:

```python
from agent import create_research_agent

app = create_research_agent()

for event in app.stream(
    {"messages": [HumanMessage(content="Your query")]},
    config={"configurable": {"thread_id": "123"}}
):
    print(event)
```

### Custom Model Configuration

Modify `agent.py` to use different models:

```python
model = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",  # Different model
    temperature=0.3,  # Adjust temperature
    max_tokens=8192   # Increase token limit
)
```

## Monitoring and Debugging

### LangGraph Studio

Access LangGraph Studio for visual debugging:

```bash
langgraph studio
```

This provides:
- Visual graph representation
- Step-by-step execution tracing
- State inspection at each node
- Tool call monitoring

### Logging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure environment variables are set correctly
   - Verify API keys are active and have sufficient credits

2. **Tool Execution Failures**
   - Check Tavily API rate limits
   - Verify network connectivity
   - Review tool call parameters

3. **Deployment Errors**
   - Ensure all dependencies are in `requirements.txt`
   - Check Python version compatibility
   - Verify `langgraph.json` syntax

### Debug Mode

Run with debug output:

```bash
langgraph test --verbose
```

## Cost Optimization

- Use `claude-3-haiku` for cheaper operations
- Implement caching for frequently accessed data
- Set appropriate `max_tokens` limits
- Monitor API usage through dashboards

## Security Best Practices

1. **API Keys**: Never commit `.env` files to version control
2. **Rate Limiting**: Implement rate limiting in production
3. **Input Validation**: Sanitize user inputs before processing
4. **Access Control**: Use LangGraph Cloud's authentication features

## Scaling Considerations

LangGraph Cloud automatically handles:
- Load balancing
- Auto-scaling based on demand
- Concurrent request handling
- State persistence across instances

## Support and Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph Cloud Docs](https://langchain-ai.github.io/langgraph/cloud/)
- [Anthropic Claude Docs](https://docs.anthropic.com/)
- [Tavily API Docs](https://docs.tavily.com/)

## License

Same as the original project.

## Contributing

Contributions welcome! Please ensure:
1. Tests pass locally
2. Code follows project style
3. Documentation is updated
4. Environment variables are documented
