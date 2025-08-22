# TaskConvAgent - Task-Based Conversational Systems + MCP Server Development

TaskConvAgent is a specialized AI agent that extends CodeActAgent with capabilities for:
1. **Task-Based Conversational Systems Development** - Original functionality
2. **MCP (Model Context Protocol) Server Development** - New functionality

## Features

### Conversational Systems Development
- Analyzing user requirements for conversational systems
- Decomposing complex conversations into manageable flows
- Creating natural language flow configurations
- Setting up project structures for conversational systems
- Integrating with the llm_automater_graph base repository

### MCP Server Development
- **Creating MCP Servers**: Generate complete MCP server files with FastMCP integration
- **Adding Tools**: Add new @mcp.tool() decorated functions to existing servers
- **Server Configuration**: Configure environment variables, host/port settings, and transport options
- **Server Registration**: Track all MCP servers in a centralized MCP_CONFIG.json file

## Tools Overview

### Conversational Systems Tools
- `clone_base_repo`: Clone the base repository for conversational systems
- `analyze_specifications`: Analyze user requirements for conversational systems
- `decompose_flows`: Break down complex conversations into specialized flows
- `generate_flow_config`: Create detailed flow configurations
- `setup_project_structure`: Set up organized project structure
- `finalize_system`: Generate comprehensive documentation and deployment instructions

### MCP Server Tools
- `create_mcp_server`: Create a new MCP server with basic structure
- `add_mcp_tool`: Add a new tool to an existing MCP server
- `configure_mcp_server`: Configure server settings and environment variables
- `register_mcp_server`: Register server in MCP_CONFIG.json for tracking

## Usage Examples

### Creating an MCP Server

```python
# Create a new MCP server
create_mcp_server(
    server_name="weather_mcp",
    server_description="Weather data and forecasting tools",
    file_path="mcp_servers/weather.py",
    base_url_env_var="WEATHER_API_BASE_URL",
    default_base_url="http://localhost:8080",
    port=8001
)

# Add a tool to the server
add_mcp_tool(
    server_file_path="mcp_servers/weather.py",
    tool_name="get_weather",
    tool_description="Get current weather for a location",
    endpoint="/api/weather",
    parameters=[
        {
            "name": "location",
            "type": "str",
            "description": "Location to get weather for",
            "required": True
        },
        {
            "name": "units",
            "type": "str",
            "description": "Temperature units (celsius/fahrenheit)",
            "required": False,
            "default": "celsius"
        }
    ]
)

# Register the server
register_mcp_server(
    server_name="weather_mcp",
    server_file_path="mcp_servers/weather.py",
    description="Weather data and forecasting tools",
    port=8001,
    tools=[
        {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "endpoint": "/api/weather"
        }
    ]
)
```

## MCP_CONFIG.json

The `MCP_CONFIG.json` file tracks all created MCP servers and their configuration:

```json
{
  "mcp_servers": [
    {
      "name": "weather_mcp",
      "file_path": "mcp_servers/weather.py",
      "description": "Weather data and forecasting tools",
      "host": "127.0.0.1",
      "port": 8001,
      "http_path": "/mcp",
      "transport": "stdio",
      "tools": [...],
      "environment_variables": {...},
      "created_at": "2024-01-15T10:30:00.000Z",
      "url": "http://127.0.0.1:8001/mcp"
    }
  ],
  "metadata": {
    "created_at": "2024-01-15T10:30:00.000Z",
    "last_updated": "2024-01-15T10:30:00.000Z",
    "version": "1.0.0"
  }
}
```

## Generated MCP Server Structure

Each generated MCP server includes:
- FastMCP integration
- Configurable transport (stdio/HTTP)
- Environment variable handling
- Request/response logging
- Error handling
- JSON response formatting
- Tool metadata injection

## Architecture

TaskConvAgent extends CodeActAgent and includes all its capabilities:
- Bash command execution
- Python/Jupyter code execution
- File reading and editing
- Browser interaction
- Thinking and reasoning
- Task completion signaling

Plus specialized tools for both conversational systems and MCP server development.

## Getting Started

1. Initialize TaskConvAgent with your LLM and configuration
2. Use conversational system tools for building chat systems
3. Use MCP server tools for creating API integration servers
4. All tools can be used together in complex workflows

The agent automatically handles tool execution and provides comprehensive feedback throughout the development process.