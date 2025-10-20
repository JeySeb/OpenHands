"""
Tool for building a complete MCP server with functional tools.
This tool generates a complete, runnable MCP server by injecting functional tool code
into a standardized MCP server structure.
"""

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

BuildMcpServerTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='build_mcp_server',
        description=(
            'Builds a complete, runnable MCP (Model Context Protocol) server with functional tools. '
            'This tool generates a complete MCP server file by injecting the provided functional tools code '
            'into a standardized MCP server structure. The generated server includes all necessary boilerplate, '
            'API calling functions, error handling, and metadata management. The functional tools code should '
            'focus only on the tool logic and use the provided standardized helper functions.'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'interpreter_path': {
                    'type': 'string',
                    'description': 'Path to LangGraph Interpreter (e.g., LangGraph-Interpreter/ folder)',
                    'default': 'LangGraph-Interpreter/',
                },
                'agent_name': {
                    'type': 'string',
                    'description': 'Name of the agent (e.g., "math_explorer", "weather_agent")',
                },
                'server_name': {
                    'type': 'string',
                    'description': 'Name of the MCP server (e.g., "stock_explorer_mcp", "weather_mcp")',
                },
                'server_description': {
                    'type': 'string',
                    'description': 'Brief description of what the MCP server does and its purpose',
                },
                'functional_tools_code': {
                    'type': 'string',
                    'description': (
                        'Complete functional tools code as a string. This should include all @mcp.tool() '
                        'decorated functions that implement the server\'s functionality. The code should use '
                        'standardized helper functions like _get_json(), _post_json(), etc. for API calls '
                        'and return json.dumps() strings with proper metadata.'
                    )
                },
                'environment_variables': {
                    'type': 'object',
                    'description': (
                        'Dictionary of environment variables and their values. Keys are environment variable names, '
                        'values are the actual values to use. These will be used to configure the server\'s '
                        'environment handling and default values.'
                    ),
                    'additionalProperties': {
                        'type': 'string'
                    },
                    'default': {}
                },
                'base_url_env_var': {
                    'type': 'string',
                    'description': 'Environment variable name for the base API URL (if using external APIs)',
                    'default': 'API_BASE_URL'
                },
                'default_base_url': {
                    'type': 'string',
                    'description': 'Base URL for API calls if environment variable is not set, mandatory if uses_external_api is True',
                    'default': 'http://localhost:8080'
                },
                'default_port': {
                    'type': 'integer',
                    'description': 'Default port for HTTP transport',
                    'default': 8000
                },
                'uses_external_api': {
                    'type': 'boolean',
                    'description': 'Whether this server makes calls to external APIs (enables API helper functions)',
                    'default': True
                },
                'api_timeout': {
                    'type': 'integer',
                    'description': 'Timeout in seconds for API requests',
                    'default': 30
                },
                'default_headers': {
                    'type': 'object',
                    'description': (
                        'Default headers to include in all API requests. Common use cases: '
                        '{"Authorization": "Bearer TOKEN"}, {"Content-Type": "application/json"}, '
                        '{"X-API-Key": "your-api-key"}. Headers can reference environment variables '
                        'by using the format "${ENV_VAR_NAME}". Example: {"Authorization": "Bearer ${API_TOKEN}"}'
                    ),
                    'additionalProperties': {
                        'type': 'string'
                    },
                    'default': {}
                }
            },
            'required': ['agent_name', 'server_name', 'server_description', 'functional_tools_code']
        },
    ),
)
