"""
Function calling implementation for TaskConvAgent.

This module handles the conversion of LLM responses into OpenHands actions
and provides the specialized tools for Task-Based Conversational System development.
It extends CodeAct's function calling to support both CodeAct and TaskConv tools.
"""

import json
import os

from litellm import (
    ChatCompletionToolParam,
    ModelResponse,
)

from openhands.agenthub.codeact_agent.function_calling import (
    combine_thought,
    response_to_actions as codeact_response_to_actions,
)
from openhands.agenthub.taskconv_agent.tools import (
    CloneBaseRepoTool,
    AnalyzeSpecificationsTool,
    DecomposeFlowsTool,
    GenerateFlowConfigTool,
    SetupProjectStructureTool,
    FinalizeSystemTool,
    CreateMcpServerTool,
    AddMcpToolTool,
    ConfigureMcpServerTool,
    RegisterMcpServerTool,
    VerifyDslIntegrityTool,
)
from openhands.core.exceptions import (
    FunctionCallNotExistsError,
    FunctionCallValidationError,
)
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    Action,
    AgentFinishAction,
    CmdRunAction,
    FileWriteAction,
    IPythonRunCellAction,
    MessageAction,
)
from openhands.events.tool import ToolCallMetadata


def response_to_actions(
    response: ModelResponse,
    mcp_tool_names: list[str] | None = None,
) -> list[Action]:
    """
    Convert LLM response to a list of OpenHands actions.
    
    This function handles both CodeAct tools and TaskConv specialized tools.
    For CodeAct tools, it delegates to the CodeAct function calling module.
    For TaskConv tools, it handles them directly.
    
    Args:
        response: The LLM response containing tool calls or messages
        mcp_tool_names: List of MCP tool names (optional)
        
    Returns:
        List of actions to execute
    """
    actions: list[Action] = []
    assert len(response.choices) == 1, 'Only one choice is supported for now'
    choice = response.choices[0]
    assistant_msg = choice.message

    if hasattr(assistant_msg, 'tool_calls') and assistant_msg.tool_calls:
        # Check if any tool calls are TaskConv-specific
        taskconv_tool_names = {tool['function']['name'] for tool in get_taskconv_tools()}
        
        has_taskconv_tools = any(
            tool_call.function.name in taskconv_tool_names 
            for tool_call in assistant_msg.tool_calls
        )
        
        if not has_taskconv_tools:
            # All tools are CodeAct tools, delegate to CodeAct function calling
            logger.debug('All tools are CodeAct tools, delegating to CodeAct function calling')
            return codeact_response_to_actions(response, mcp_tool_names)
        
        # Mixed or TaskConv-only tools, handle them here
        logger.debug(f'Processing mixed/TaskConv tools: {[tc.function.name for tc in assistant_msg.tool_calls]}')
        
        # Extract thought from assistant message content
        thought = ''
        if isinstance(assistant_msg.content, str):
            thought = assistant_msg.content
        elif isinstance(assistant_msg.content, list):
            for msg in assistant_msg.content:
                if msg['type'] == 'text':
                    thought += msg['text']

        # Process each tool call
        for i, tool_call in enumerate(assistant_msg.tool_calls):
            action: Action
            logger.debug(f'TaskConvAgent tool call: {tool_call}')
            
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.decoder.JSONDecodeError as e:
                raise FunctionCallValidationError(
                    f'Failed to parse tool call arguments: {tool_call.function.arguments}'
                ) from e

            # ================================================
            # TaskConv-Specific Tools
            # ================================================
            if tool_call.function.name in taskconv_tool_names:
                
                # ================================================
                # Repository and Project Setup Tools
                # ================================================
                if tool_call.function.name == 'clone_base_repo':
                    action = _handle_clone_base_repo(arguments)
                    
                elif tool_call.function.name == 'setup_project_structure':
                    action = _handle_setup_project_structure(arguments)
                
                # ================================================
                # Analysis and Design Tools
                # ================================================
                elif tool_call.function.name == 'analyze_specifications':
                    action = _handle_analyze_specifications(arguments)
                    
                elif tool_call.function.name == 'decompose_flows':
                    action = _handle_decompose_flows(arguments)
                    
                elif tool_call.function.name == 'generate_flow_config':
                    action = _handle_generate_flow_config(arguments)
                
                # ================================================
                # System Generation and Finalization Tools  
                # ================================================
                elif tool_call.function.name == 'finalize_system':
                    action = _handle_finalize_system(arguments)
                    
                elif tool_call.function.name == 'verify_dsl_integrity':
                    action = _handle_verify_dsl_integrity(arguments)
                
                # ================================================
                # MCP Server Management Tools
                # ================================================
                elif tool_call.function.name == 'create_mcp_server':
                    action = _handle_create_mcp_server(arguments)
                    
                elif tool_call.function.name == 'add_mcp_tool':
                    action = _handle_add_mcp_tool(arguments)
                    
                elif tool_call.function.name == 'configure_mcp_server':
                    action = _handle_configure_mcp_server(arguments)
                    
                elif tool_call.function.name == 'register_mcp_server':
                    action = _handle_register_mcp_server(arguments)
                    
                else:
                    raise FunctionCallNotExistsError(
                        f'Tool {tool_call.function.name} is not registered. (arguments: {arguments}). Please check the tool name and retry with an existing tool.'
                    )
            else:
                # This is a CodeAct tool, but we're in mixed mode
                # Create a single-tool response and delegate to CodeAct
                single_tool_response = ModelResponse(
                    id=response.id,
                    choices=[
                        response.choices[0].__class__(
                            index=0,
                            message=response.choices[0].message.__class__(
                                role='assistant',
                                content=thought if i == 0 else '',
                                tool_calls=[tool_call]
                            ),
                            finish_reason='tool_calls'
                        )
                    ],
                    created=response.created,
                    model=response.model,
                    object=response.object,
                )
                
                codeact_actions = codeact_response_to_actions(single_tool_response, mcp_tool_names)
                if codeact_actions:
                    action = codeact_actions[0]  # Should only be one action
                else:
                    raise FunctionCallNotExistsError(
                        f'CodeAct tool {tool_call.function.name} returned no actions. '
                        f'(arguments: {arguments}).'
                    )

            # Add thought to the first action only
            if i == 0 and thought:
                action = combine_thought(action, thought)
                
            # Add metadata for tool calling
            action.tool_call_metadata = ToolCallMetadata(
                tool_call_id=tool_call.id,
                function_name=tool_call.function.name,
                model_response=response,
                total_calls_in_response=len(assistant_msg.tool_calls),
            )
            actions.append(action)
    else:
        # Handle non-tool call responses
        actions.append(
            MessageAction(
                content=str(assistant_msg.content) if assistant_msg.content else '',
                wait_for_response=True,
            )
        )

    # Add response id to actions for token usage tracking
    for action in actions:
        action.response_id = response.id

    assert len(actions) >= 1
    return actions


def get_taskconv_tools() -> list[ChatCompletionToolParam]:
    """
    Get only the TaskConv-specific tools (without CodeAct tools).
    
    Returns:
        List of TaskConv specialized tools
    """
    return [
        CloneBaseRepoTool,
        AnalyzeSpecificationsTool,
        DecomposeFlowsTool,
        GenerateFlowConfigTool,
        SetupProjectStructureTool,
        FinalizeSystemTool,
        CreateMcpServerTool,
        AddMcpToolTool,
        ConfigureMcpServerTool,
        RegisterMcpServerTool,
        VerifyDslIntegrityTool,
    ]


def get_tools() -> list[ChatCompletionToolParam]:
    """
    Get all tools available to TaskConvAgent (CodeAct + TaskConv).
    
    Note: This function is kept for backward compatibility but should not be used.
    Use get_taskconv_tools() to get only TaskConv tools, and let the agent combine them.
    
    Returns:
        List of TaskConv specialized tools (CodeAct tools should be added by the agent)
    """
    logger.warning(
        'get_tools() is deprecated. Use get_taskconv_tools() and let the agent combine with CodeAct tools.'
    )
    return get_taskconv_tools()


def _handle_clone_base_repo(arguments: dict) -> Action:
    """Handle the clone_base_repo tool call."""
    target_directory = arguments.get('target_directory', '.')
    branch = arguments.get('branch', 'main')
    from dotenv import load_dotenv
    load_dotenv()
    # TODO: WARNING! Hardcoded GitHub token for private repo access.
    git_url = os.environ.get('TASK_CONV_AGENT__GITHUB_REPO_URL')
    git_token = os.environ.get('TASK_CONV_AGENT__GITHUB_REPO_TOKEN')
    clone_command = f'git clone -b {branch} https://{git_token}@{git_url} {target_directory}'

    return CmdRunAction(command=clone_command)

def _handle_analyze_specifications(arguments: dict) -> Action:
    """Handle the analyze_specifications tool call."""
    if 'user_requirements' not in arguments:
        raise FunctionCallValidationError(
            'Missing required argument "user_requirements" in tool call analyze_specifications'
        )
    user_requirements = arguments['user_requirements']
    domain = arguments.get('domain', 'general')
    target_audience = arguments.get('target_audience', 'general users')
    complexity_level = arguments.get('complexity_level', 'moderate')
    
    # Create Python code to analyze specifications
    analysis_code = f"""
# Analyzing specifications for Task-Based Conversational System

specifications = {{
    'user_requirements': '''{user_requirements}''',
    'domain': '{domain}',
    'target_audience': '{target_audience}',
    'complexity_level': '{complexity_level}'
}}

print("=== SPECIFICATION ANALYSIS ===")
print(f"Domain: {{specifications['domain']}}")
print(f"Target Audience: {{specifications['target_audience']}}")
print(f"Complexity Level: {{specifications['complexity_level']}}")
print("\\nUser Requirements:")
print(specifications['user_requirements'])
print("\\n=== ANALYSIS COMPLETE ===")

# Store analysis results for next steps
specification_analysis = specifications
"""
    
    return IPythonRunCellAction(code=analysis_code)


def _handle_decompose_flows(arguments: dict) -> Action:
    """Handle the decompose_flows tool call."""
    required_args = ['analyzed_requirements', 'main_objectives', 'user_interactions']
    for arg in required_args:
        if arg not in arguments:
            raise FunctionCallValidationError(
                f'Missing required argument "{arg}" in tool call decompose_flows'
            )
    
    analyzed_requirements = arguments['analyzed_requirements']
    main_objectives = arguments['main_objectives']
    user_interactions = arguments['user_interactions']
    business_processes = arguments.get('business_processes', [])
    integration_requirements = arguments.get('integration_requirements', [])
    
    # Create Python code to decompose flows
    decomposition_code = f"""
# Decomposing conversational system into specialized flows

import json

flow_decomposition = {{
    'analyzed_requirements': '''{analyzed_requirements}''',
    'main_objectives': {main_objectives},
    'user_interactions': {user_interactions},
    'business_processes': {business_processes},
    'integration_requirements': {integration_requirements}
}}

print("=== FLOW DECOMPOSITION ===")
print("Main Objectives:")
for i, obj in enumerate(flow_decomposition['main_objectives'], 1):
    print(f"  {{i}}. {{obj}}")

print("\\nUser Interactions:")
for i, interaction in enumerate(flow_decomposition['user_interactions'], 1):
    print(f"  {{i}}. {{interaction}}")

# Generate flow structure
flows = []
flows.append({{
    'name': 'main_orchestration',
    'type': 'orchestration',
    'purpose': 'Handle initial user contact and route to appropriate specialized flows'
}})

for i, obj in enumerate(flow_decomposition['main_objectives']):
    flow_name = obj.lower().replace(' ', '_').replace(',', '').replace('.', '')
    flows.append({{
        'name': f'{{flow_name}}_flow',
        'type': 'specialized',
        'purpose': obj
    }})

print("\\nGenerated Flow Structure:")
for flow in flows:
    print(f"  - {{flow['name']}}: {{flow['purpose']}}")

print("\\n=== DECOMPOSITION COMPLETE ===")

# Store flow structure for next steps
flow_structure = flows
"""
    
    return IPythonRunCellAction(code=decomposition_code)


def _handle_generate_flow_config(arguments: dict) -> Action:
    """Handle the generate_flow_config tool call."""
    required_args = ['flow_name', 'flow_purpose', 'user_intents', 'conversation_patterns', 'routing_logic']
    for arg in required_args:
        if arg not in arguments:
            raise FunctionCallValidationError(
                f'Missing required argument "{arg}" in tool call generate_flow_config'
            )
    
    flow_name = arguments['flow_name']
    flow_purpose = arguments['flow_purpose']
    user_intents = arguments['user_intents']
    conversation_patterns = arguments['conversation_patterns']
    routing_logic = arguments['routing_logic']
    integration_points = arguments.get('integration_points', [])
    response_templates = arguments.get('response_templates', [])
    context_variables = arguments.get('context_variables', [])
    
    # Generate comprehensive flow configuration content
    config_content = f"""# {flow_name.title().replace('_', ' ')} Flow Configuration

## Flow Overview
**Purpose**: {flow_purpose}

## User Intents Handled
{chr(10).join(f'- {intent}' for intent in user_intents)}

## Conversation Patterns
{chr(10).join(f'- {pattern}' for pattern in conversation_patterns)}

## Routing Logic
{routing_logic}

## Integration Points
{chr(10).join(f'- {point}' for point in integration_points) if integration_points else '- None specified'}

## Response Templates
{chr(10).join(f'- {template}' for template in response_templates) if response_templates else '- To be defined during implementation'}

## Context Variables
{chr(10).join(f'- {variable}' for variable in context_variables) if context_variables else '- To be defined during implementation'}

## Implementation Notes
This flow should be implemented as a specialized conversational agent that:
1. Recognizes the specified user intents
2. Follows the defined conversation patterns
3. Maintains required context variables
4. Integrates with specified external systems
5. Routes conversations according to the defined logic

## Testing Scenarios
- Test each user intent recognition
- Validate conversation flow patterns
- Test integration points (if any)
- Verify routing logic works correctly
"""
    
    # Write the configuration file
    file_path = f'flows_config/{flow_name}_config.md'
    return FileWriteAction(path=file_path, content=config_content)


def _handle_setup_project_structure(arguments: dict) -> Action:
    """Handle the setup_project_structure tool call."""
    project_path = arguments['project_path']
    flow_names = arguments['flow_names']
    project_metadata = arguments['project_metadata']
    create_docs = arguments.get('create_docs', True)
    create_tests = arguments.get('create_tests', True)
    
    # Create setup commands
    setup_commands = [
        f'mkdir -p {project_path}/flows_config',
        f'mkdir -p {project_path}/src',
        f'mkdir -p {project_path}/config',
    ]
    
    if create_docs:
        setup_commands.append(f'mkdir -p {project_path}/docs')
        
    if create_tests:
        setup_commands.append(f'mkdir -p {project_path}/tests')
    
    # Join all commands with &&
    full_command = ' && '.join(setup_commands)
    
    return CmdRunAction(command=full_command)


def _handle_finalize_system(arguments: dict) -> Action:
    """Handle the finalize_system tool call."""
    project_path = arguments['project_path']
    system_summary = arguments['system_summary']
    flows_created = arguments['flows_created']
    deployment_type = arguments.get('deployment_type', 'local')
    testing_requirements = arguments.get('testing_requirements', [])
    integration_notes = arguments.get('integration_notes', '')
    
    # Create comprehensive README content
    readme_content = f"""# Task-Based Conversational System

## System Overview
{system_summary}

## Flows Created
{chr(10).join(f'- **{flow}**' for flow in flows_created)}

## Deployment
**Type**: {deployment_type}

### Setup Instructions
1. Navigate to the project directory: `cd {project_path}`
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables (see config/ directory)
4. Run the system: `python main.py`

## Testing
{chr(10).join(f'- {req}' for req in testing_requirements) if testing_requirements else '- Standard conversation flow testing recommended'}

## Integration Notes
{integration_notes if integration_notes else 'No special integration requirements'}

## Flow Configuration Files
Each flow has its detailed configuration in the `flows_config/` directory:
{chr(10).join(f'- `flows_config/{flow}_config.md`' for flow in flows_created)}

## Next Steps
1. Review each flow configuration file
2. Implement the conversation logic based on the specifications
3. Test individual flows
4. Test the complete system integration
5. Deploy according to the chosen deployment method

## Support
Refer to the documentation in the `docs/` directory for detailed implementation guidelines.
"""
    
    return FileWriteAction(path=f'{project_path}/README.md', content=readme_content)


def _handle_create_mcp_server(arguments: dict) -> Action:
    """Handle the create_mcp_server tool call."""
    server_name = arguments['server_name']
    server_description = arguments['server_description']
    file_path = arguments['file_path']
    base_url_env_var = arguments.get('base_url_env_var', 'API_BASE_URL')
    default_base_url = arguments.get('default_base_url', 'http://localhost:8080')
    host = arguments.get('host', '127.0.0.1')
    port = arguments.get('port', 8000)
    http_path = arguments.get('http_path', '/mcp')
    
    # Generate MCP server content based on the provided example
    server_content = f'''import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import requests
import json

# Ensure project root is on sys.path so we can import project modules
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP
from config.logger import get_logger


"""
MCP server for {server_description}.
All tools return plain dicts to avoid strict output schema coupling.
"""

SERVER_NAME = "{server_name}"

logger = get_logger(SERVER_NAME)


def _default_base_url() -> str:
    return os.environ.get("{base_url_env_var}", "{default_base_url}")


def _resolve_endpoint(endpoint: str) -> str:
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint
    base = _default_base_url().rstrip("/")
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    return f"{{base}}{{endpoint}}"


def _get_json(endpoint: str, params: Optional[Dict[str, Any]] = None, mcp_tool: Optional[str] = None) -> Any:
    resolved = _resolve_endpoint(endpoint)
    logger.debug(f"HTTP GET: {{resolved}} params={{params}}")
    response = requests.get(resolved, params=params)
    response.raise_for_status()
    data = response.json()
    data["mcp_server"] = SERVER_NAME
    data["mcp_tool"] = mcp_tool
    data["tool_params"] = params
    return data


def _post_json(endpoint: str, data: Optional[Dict[str, Any]] = None, mcp_tool: Optional[str] = None) -> Any:
    resolved = _resolve_endpoint(endpoint)
    logger.debug(f"HTTP POST: {{resolved}} data={{data}}")
    response = requests.post(resolved, json=data)
    response.raise_for_status()
    result = response.json()
    result["mcp_server"] = SERVER_NAME
    result["mcp_tool"] = mcp_tool
    result["tool_data"] = data
    return result


def _create_mcp() -> FastMCP:
    host = os.environ.get("MCP_HTTP_HOST", "{host}")
    port_str = os.environ.get("MCP_HTTP_PORT", "{port}")
    path = os.environ.get("MCP_HTTP_PATH", "{http_path}")
    try:
        port = int(port_str)
    except ValueError:
        port = {port}
    return FastMCP(
        SERVER_NAME,
        host=host,
        port=port,
        streamable_http_path=path,
    )


mcp = _create_mcp()


# Add your tools here using @mcp.tool() decorator
# Example:
# @mcp.tool()
# def example_tool(param: str) -> str:
#     \"\"\"Example tool description.\"\"\"
#     try:
#         data = _get_json("/api/example", {{"param": param}}, mcp_tool="example_tool")
#         return json.dumps(data, ensure_ascii=False)
#     except requests.RequestException as error:
#         logger.error(f"Failed to call example API: {{str(error)}}")
#         return json.dumps({{"error": str(error)}}, ensure_ascii=False)


def _run_mcp() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "http":
        transport = "streamable-http"
    mcp.run(transport=transport)


if __name__ == "__main__":
    _run_mcp()
'''
    
    return FileWriteAction(path=file_path, content=server_content)


def _handle_add_mcp_tool(arguments: dict) -> Action:
    """Handle the add_mcp_tool tool call."""
    server_file_path = arguments['server_file_path']
    tool_name = arguments['tool_name']
    tool_description = arguments['tool_description']
    endpoint = arguments['endpoint']
    parameters = arguments['parameters']
    http_method = arguments.get('http_method', 'GET')
    
    # Generate function parameters and typing
    param_list = []
    param_docs = []
    param_dict_items = []
    
    for param in parameters:
        param_name = param['name']
        param_type = param['type']
        param_desc = param['description']
        is_required = param['required']
        default_val = param.get('default')
        
        # Convert type names to Python types
        type_mapping = {
            'str': 'str', 'string': 'str',
            'int': 'int', 'integer': 'int',
            'float': 'float',
            'bool': 'bool', 'boolean': 'bool',
            'list': 'List[str]', 'array': 'List[str]',
            'dict': 'Dict[str, Any]', 'object': 'Dict[str, Any]'
        }
        python_type = type_mapping.get(param_type.lower(), 'Any')
        
        if not is_required:
            python_type = f'Optional[{python_type}]'
            if default_val is not None:
                if isinstance(default_val, str):
                    param_list.append(f'{param_name}: {python_type} = "{default_val}"')
                else:
                    param_list.append(f'{param_name}: {python_type} = {default_val}')
            else:
                param_list.append(f'{param_name}: {python_type} = None')
        else:
            param_list.append(f'{param_name}: {python_type}')
        
        param_docs.append(f'    {param_name}: {param_desc}')
        param_dict_items.append(f'        "{param_name}": {param_name}')
    
    # Generate the tool function
    tool_function = f'''

@mcp.tool()
def {tool_name}(
    {",\\n    ".join(param_list)},
    endpoint: Optional[str] = None,
) -> str:
    """
    {tool_description}
    
    Args:
{chr(10).join(param_docs)}
        endpoint: API endpoint override (optional)
    
    Returns:
        JSON string with the API response
    """
    try:
        effective_endpoint = endpoint or "{endpoint}"
        params: Dict[str, Any] = {{
{chr(10).join(param_dict_items)}
        }}
        # Remove None values to avoid sending empty params
        params = {{k: v for k, v in params.items() if v is not None}}
        
        {'data = _get_json(effective_endpoint, params=params, mcp_tool="' + tool_name + '")' if http_method.upper() == 'GET' else 'data = _post_json(effective_endpoint, data=params, mcp_tool="' + tool_name + '")'}
        return json.dumps(data, ensure_ascii=False)
    except requests.RequestException as error:
        logger.error(f"Failed to call {tool_name}: {{str(error)}}")
        return json.dumps({{"error": str(error)}}, ensure_ascii=False)
'''
    
    # Create Python script to append the tool to the server file
    append_code = f'''
# Adding new tool to MCP server
server_file_path = "{server_file_path}"
tool_function = """{tool_function}"""

# Read the current file content
with open(server_file_path, 'r') as f:
    content = f.read()

# Find the position to insert the new tool (before _run_mcp function)
insert_position = content.find('def _run_mcp() -> None:')
if insert_position == -1:
    # If _run_mcp is not found, append at the end
    new_content = content + tool_function
else:
    # Insert before _run_mcp function
    new_content = content[:insert_position] + tool_function + "\\n\\n" + content[insert_position:]

# Write the updated content back
with open(server_file_path, 'w') as f:
    f.write(new_content)

print(f"Successfully added tool '{{tool_function.split('def ')[1].split('(')[0]}}' to {{server_file_path}}")
'''
    
    return IPythonRunCellAction(code=append_code)


def _handle_configure_mcp_server(arguments: dict) -> Action:
    """Handle the configure_mcp_server tool call."""
    server_file_path = arguments['server_file_path']
    env_vars = arguments.get('environment_variables', {})
    default_config = arguments.get('default_config', {})
    logging_config = arguments.get('logging_config', {})
    
    # Create Python script to update server configuration
    config_code = f'''
# Configuring MCP server
import re

server_file_path = "{server_file_path}"
env_vars = {env_vars}
default_config = {default_config}
logging_config = {logging_config}

# Read the current file content
with open(server_file_path, 'r') as f:
    content = f.read()

# Update environment variables if provided
if env_vars:
    for env_key, env_value in env_vars.items():
        if env_key == 'base_url_var' and env_value:
            # Update base URL environment variable
            pattern = r'os\\.environ\\.get\\("[^"]+", "[^"]+"\\)'
            replacement = f'os.environ.get("{{env_value}}", "http://localhost:8080")'
            content = re.sub(pattern, replacement, content, count=1)

# Update default configuration if provided
if default_config:
    if 'host' in default_config:
        content = re.sub(
            r'host = os\\.environ\\.get\\("MCP_HTTP_HOST", "[^"]+"\\)',
            f'host = os.environ.get("MCP_HTTP_HOST", "{default_config["host"]}")',
            content
        )
    if 'port' in default_config:
        content = re.sub(
            r'port_str = os\\.environ\\.get\\("MCP_HTTP_PORT", "[^"]+"\\)',
            f'port_str = os.environ.get("MCP_HTTP_PORT", "{default_config["port"]}")',
            content
        )
        content = re.sub(
            r'port = \\d+',
            f'port = {default_config["port"]}',
            content
        )
    if 'path' in default_config:
        content = re.sub(
            r'path = os\\.environ\\.get\\("MCP_HTTP_PATH", "[^"]+"\\)',
            f'path = os.environ.get("MCP_HTTP_PATH", "{default_config["path"]}")',
            content
        )

# Write the updated content back
with open(server_file_path, 'w') as f:
    f.write(content)

print(f"Successfully configured MCP server at {{server_file_path}}")
'''
    
    return IPythonRunCellAction(code=config_code)


def _handle_register_mcp_server(arguments: dict) -> Action:
    """Handle the register_mcp_server tool call."""
    server_name = arguments['server_name']
    server_file_path = arguments['server_file_path']
    description = arguments['description']
    host = arguments.get('host', '127.0.0.1')
    port = arguments['port']
    http_path = arguments.get('http_path', '/mcp')
    transport = arguments.get('transport', 'stdio')
    tools = arguments.get('tools', [])
    environment_variables = arguments.get('environment_variables', {})
    config_file_path = arguments.get('config_file_path', 'MCP_CONFIG.json')
    
    # Create Python script to update MCP_CONFIG.json
    register_code = f'''
import json
import os
from datetime import datetime

config_file_path = "{config_file_path}"
server_info = {{
    "name": "{server_name}",
    "file_path": "{server_file_path}",
    "description": "{description}",
    "host": "{host}",
    "port": {port},
    "http_path": "{http_path}",
    "transport": "{transport}",
    "tools": {tools},
    "environment_variables": {environment_variables},
    "created_at": datetime.now().isoformat(),
    "url": f"http://{host}:{port}{http_path}" if "{transport}" == "http" else None
}}

# Load existing config or create new one
if os.path.exists(config_file_path):
    with open(config_file_path, 'r') as f:
        config = json.load(f)
else:
    config = {{
        "mcp_servers": [],
        "metadata": {{
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }}
    }}

# Update or add server
existing_server = None
for i, server in enumerate(config["mcp_servers"]):
    if server["name"] == "{server_name}":
        existing_server = i
        break

if existing_server is not None:
    config["mcp_servers"][existing_server] = server_info
    print(f"Updated existing server '{{server_info['name']}}' in {{config_file_path}}")
else:
    config["mcp_servers"].append(server_info)
    print(f"Added new server '{{server_info['name']}}' to {{config_file_path}}")

# Update metadata
config["metadata"]["last_updated"] = datetime.now().isoformat()

# Write updated config
with open(config_file_path, 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"MCP server registration complete. Config saved to {{config_file_path}}")
print(f"Server details:")
print(f"  Name: {{server_info['name']}}")
print(f"  Host: {{server_info['host']}}")
print(f"  Port: {{server_info['port']}}")
print(f"  Transport: {{server_info['transport']}}")
print(f"  Tools: {{len(server_info['tools'])}}")
'''
    
    return IPythonRunCellAction(code=register_code)


def _handle_verify_dsl_integrity(arguments: dict) -> Action:
    """Handle the verify_dsl_integrity tool call."""
    if 'dsl_folder_path' not in arguments:
        raise FunctionCallValidationError(
            'Missing required argument "dsl_folder_path" in tool call verify_dsl_integrity'
        )
    
    dsl_folder_path = arguments['dsl_folder_path']
    strict_mode = arguments.get('strict_mode', True)
    check_tool_references = arguments.get('check_tool_references', True)
    output_format = arguments.get('output_format', 'detailed')
    
    # Create comprehensive DSL validation code
    validation_code = f'''
import json
import os
import glob
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
import re

class DSLValidator:
    """Comprehensive DSL validator for Task-Based Conversational System."""
    
    def __init__(self, folder_path: str, strict_mode: bool = True, check_tool_refs: bool = True):
        self.folder_path = Path(folder_path)
        self.strict_mode = strict_mode
        self.check_tool_refs = check_tool_refs
        self.errors = []
        self.warnings = []
        self.agent_config = None
        self.flows = {{}}
        self.all_flow_names = set()
        self.all_node_ids = {{}}  # flow_name -> set of node_ids
        
    def validate(self) -> Dict[str, Any]:
        """Run complete DSL validation."""
        try:
            # Check folder structure
            self._validate_folder_structure()
            
            # Load and validate agent config
            self._validate_agent_config()
            
            # Load and validate all flows
            self._load_flows()
            self._validate_flows()
            
            # Cross-reference validation
            self._validate_cross_references()
            
            return self._generate_report()
            
        except Exception as e:
            self.errors.append(f"Critical validation error: {{str(e)}}")
            return self._generate_report()
    
    def _validate_folder_structure(self):
        """Validate expected folder structure."""
        if not self.folder_path.exists():
            self.errors.append(f"DSL folder does not exist: {{self.folder_path}}")
            return
            
        if not self.folder_path.is_dir():
            self.errors.append(f"DSL path is not a directory: {{self.folder_path}}")
            return
            
        # Check for agent_config.json
        agent_config_path = self.folder_path / "agent_config.json"
        if not agent_config_path.exists():
            self.errors.append("Missing required file: agent_config.json")
            
        # Check for graph directory
        graph_dir = self.folder_path / "graph"
        if not graph_dir.exists():
            self.errors.append("Missing required directory: graph/")
        elif not graph_dir.is_dir():
            self.errors.append("graph/ is not a directory")
        else:
            # Check for at least one .json file in graph/
            json_files = list(graph_dir.glob("*.json"))
            if not json_files:
                self.errors.append("No .json flow definition files found in graph/ directory")
    
    def _validate_agent_config(self):
        """Validate agent_config.json structure and content."""
        config_path = self.folder_path / "agent_config.json"
        if not config_path.exists():
            return  # Already reported in folder structure validation
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.agent_config = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in agent_config.json: {{str(e)}}")
            return
        except Exception as e:
            self.errors.append(f"Error reading agent_config.json: {{str(e)}}")
            return
            
        # Validate required fields
        required_fields = ['graph_name', 'agent_name', 'personality', 'general_goal', 'constrains']
        for field in required_fields:
            if field not in self.agent_config:
                self.errors.append(f"Missing required field in agent_config.json: {{field}}")
            elif not isinstance(self.agent_config[field], (str, list)):
                self.errors.append(f"Field '{{field}}' in agent_config.json must be string or list")
            elif field == 'constrains' and not isinstance(self.agent_config[field], list):
                self.errors.append("Field 'constrains' in agent_config.json must be a list of strings")
            elif field != 'constrains' and not isinstance(self.agent_config[field], str):
                self.errors.append(f"Field '{{field}}' in agent_config.json must be a string")
            elif not self.agent_config[field]:
                self.errors.append(f"Field '{{field}}' in agent_config.json cannot be empty")
                
        # Validate constrains array
        if 'constrains' in self.agent_config and isinstance(self.agent_config['constrains'], list):
            for i, constraint in enumerate(self.agent_config['constrains']):
                if not isinstance(constraint, str):
                    self.errors.append(f"Constraint {{i}} in agent_config.json must be a string")
                elif not constraint.strip():
                    self.errors.append(f"Constraint {{i}} in agent_config.json cannot be empty")
    
    def _load_flows(self):
        """Load all flow definition files."""
        graph_dir = self.folder_path / "graph"
        if not graph_dir.exists():
            return
            
        json_files = list(graph_dir.glob("*.json"))
        for json_file in json_files:
            flow_name = json_file.stem
            self.all_flow_names.add(flow_name)
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    flow_data = json.load(f)
                    self.flows[flow_name] = flow_data
                    
                    # Extract node IDs for cross-reference validation
                    if 'nodes' in flow_data and isinstance(flow_data['nodes'], list):
                        node_ids = set()
                        for node in flow_data['nodes']:
                            if isinstance(node, dict) and 'id' in node:
                                node_ids.add(node['id'])
                        self.all_node_ids[flow_name] = node_ids
                        
            except json.JSONDecodeError as e:
                self.errors.append(f"Invalid JSON in {{json_file.name}}: {{str(e)}}")
            except Exception as e:
                self.errors.append(f"Error reading {{json_file.name}}: {{str(e)}}")
    
    def _validate_flows(self):
        """Validate all flow definitions."""
        start_flows = []
        
        for flow_name, flow_data in self.flows.items():
            self._validate_flow_metadata(flow_name, flow_data)
            self._validate_flow_nodes(flow_name, flow_data)
            
            # Track start flows
            if isinstance(flow_data, dict) and flow_data.get('isStartFlow'):
                start_flows.append(flow_name)
        
        # Validate that exactly one flow is marked as start flow
        if len(start_flows) == 0:
            self.errors.append("No flow is marked as start flow (isStartFlow: true)")
        elif len(start_flows) > 1:
            self.errors.append(f"Multiple flows marked as start flow: {{', '.join(start_flows)}}")
    
    def _validate_flow_metadata(self, flow_name: str, flow_data: Dict):
        """Validate flow-level metadata."""
        if not isinstance(flow_data, dict):
            self.errors.append(f"Flow {{flow_name}}: Root must be an object/dictionary")
            return
            
        # Required fields
        required_fields = {{
            'id': str,
            'name': str, 
            'kind': str,
            'isActive': bool,
            'isStartFlow': bool,
            'goalDescription': str,
            'availableServersMCP': list,
            'startNodeId': str,
            'nodes': list
        }}
        
        for field, expected_type in required_fields.items():
            if field not in flow_data:
                self.errors.append(f"Flow {{flow_name}}: Missing required field '{{field}}'")
            elif not isinstance(flow_data[field], expected_type):
                self.errors.append(f"Flow {{flow_name}}: Field '{{field}}' must be {{expected_type.__name__}}")
            elif expected_type == str and not flow_data[field]:
                self.errors.append(f"Flow {{flow_name}}: Field '{{field}}' cannot be empty")
        
        # Optional fields validation
        if 'isGloballyAccessible' in flow_data and not isinstance(flow_data['isGloballyAccessible'], bool):
            self.errors.append(f"Flow {{flow_name}}: Field 'isGloballyAccessible' must be boolean")
            
        # Validate availableServersMCP content
        if 'availableServersMCP' in flow_data and isinstance(flow_data['availableServersMCP'], list):
            for i, server in enumerate(flow_data['availableServersMCP']):
                if not isinstance(server, str):
                    self.errors.append(f"Flow {{flow_name}}: availableServersMCP[{{i}}] must be string")
                elif not server.strip():
                    self.errors.append(f"Flow {{flow_name}}: availableServersMCP[{{i}}] cannot be empty")
    
    def _validate_flow_nodes(self, flow_name: str, flow_data: Dict):
        """Validate all nodes within a flow."""
        if 'nodes' not in flow_data or not isinstance(flow_data['nodes'], list):
            return
            
        nodes = flow_data['nodes']
        if not nodes:
            self.errors.append(f"Flow {{flow_name}}: Must contain at least one node")
            return
            
        node_ids_in_flow = set()
        start_node_found = False
        
        # Validate startNodeId exists
        start_node_id = flow_data.get('startNodeId')
        if start_node_id:
            start_node_found = any(node.get('id') == start_node_id for node in nodes if isinstance(node, dict))
            if not start_node_found:
                self.errors.append(f"Flow {{flow_name}}: startNodeId '{{start_node_id}}' not found in nodes")
        
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                self.errors.append(f"Flow {{flow_name}}: Node {{i}} must be an object")
                continue
                
            # Validate node structure
            self._validate_node_structure(flow_name, i, node)
            
            # Track unique node IDs
            node_id = node.get('id')
            if node_id:
                if node_id in node_ids_in_flow:
                    self.errors.append(f"Flow {{flow_name}}: Duplicate node ID '{{node_id}}'")
                node_ids_in_flow.add(node_id)
    
    def _validate_node_structure(self, flow_name: str, node_index: int, node: Dict):
        """Validate individual node structure."""
        node_id = node.get('id', f'node_{{node_index}}')
        
        # Required fields for all nodes
        required_fields = ['id', 'type', 'name', 'data']
        for field in required_fields:
            if field not in node:
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: Missing required field '{{field}}'")
            elif field != 'data' and not isinstance(node[field], str):
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: Field '{{field}}' must be string")
            elif field == 'data' and not isinstance(node[field], dict):
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: Field 'data' must be object")
                
        # Validate node type and ID prefix
        node_type = node.get('type')
        if node_type == 'basic_node':
            if not node_id.startswith('basic_node__'):
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: basic_node ID must start with 'basic_node__'")
            self._validate_basic_node_data(flow_name, node_id, node.get('data', {{}}))
        elif node_type == 'tool_node':
            if not node_id.startswith('tool_node__'):
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: tool_node ID must start with 'tool_node__'")
            self._validate_tool_node_data(flow_name, node_id, node.get('data', {{}}))
        else:
            self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: Invalid node type '{{node_type}}'. Must be 'basic_node' or 'tool_node'")
    
    def _validate_basic_node_data(self, flow_name: str, node_id: str, data: Dict):
        """Validate basic_node data structure."""
        required_fields = ['instruction', 'extract_data', 'how_to_route']
        
        for field in required_fields:
            if field not in data:
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: Missing required field 'data.{{field}}'")
            elif field == 'instruction' and not isinstance(data[field], str):
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: 'data.instruction' must be string")
            elif field == 'extract_data' and not isinstance(data[field], dict):
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: 'data.extract_data' must be object")
            elif field == 'how_to_route' and not isinstance(data[field], dict):
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: 'data.how_to_route' must be object")
                
        # Validate instruction content
        if 'instruction' in data and isinstance(data['instruction'], str):
            if not data['instruction'].strip():
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: 'data.instruction' cannot be empty")
            elif self.strict_mode and len(data['instruction']) < 10:
                self.warnings.append(f"Flow {{flow_name}}, Node {{node_id}}: 'data.instruction' seems too brief (< 10 chars)")
                
        # Validate extract_data content  
        if 'extract_data' in data and isinstance(data['extract_data'], dict):
            if not data['extract_data']:
                self.warnings.append(f"Flow {{flow_name}}, Node {{node_id}}: 'data.extract_data' is empty - consider adding fields")
            for key, value in data['extract_data'].items():
                if not isinstance(value, str):
                    self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: extract_data['{{key}}'] must be string description")
                    
        # Validate optional text_format
        if 'text_format' in data:
            self._validate_text_format(flow_name, node_id, data['text_format'])
            
        # Validate routing
        if 'how_to_route' in data and isinstance(data['how_to_route'], dict):
            self._validate_routing(flow_name, node_id, data['how_to_route'])
    
    def _validate_tool_node_data(self, flow_name: str, node_id: str, data: Dict):
        """Validate tool_node data structure."""
        required_fields = ['tool', 'instruction', 'how_to_route']
        
        for field in required_fields:
            if field not in data:
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: Missing required field 'data.{{field}}'")
            elif field in ['tool', 'instruction'] and not isinstance(data[field], str):
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: 'data.{{field}}' must be string")
            elif field == 'how_to_route' and not isinstance(data[field], dict):
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: 'data.how_to_route' must be object")
                
        # Validate tool name
        if 'tool' in data and isinstance(data['tool'], str):
            if not data['tool'].strip():
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: 'data.tool' cannot be empty")
            elif self.check_tool_refs and flow_name in self.flows:
                # Check if tool is available in flow's MCP servers
                available_servers = self.flows[flow_name].get('availableServersMCP', [])
                if not available_servers:
                    self.warnings.append(f"Flow {{flow_name}}, Node {{node_id}}: No MCP servers available for tool '{{data['tool']}}'")
                    
        # Validate instruction
        if 'instruction' in data and isinstance(data['instruction'], str):
            if not data['instruction'].strip():
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: 'data.instruction' cannot be empty")
                
        # Validate routing
        if 'how_to_route' in data and isinstance(data['how_to_route'], dict):
            self._validate_routing(flow_name, node_id, data['how_to_route'])
    
    def _validate_text_format(self, flow_name: str, node_id: str, text_format: Any):
        """Validate text_format structure."""
        if not isinstance(text_format, dict):
            self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: 'data.text_format' must be object")
            return
            
        if 'instruction' in text_format and not isinstance(text_format['instruction'], str):
            self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: 'text_format.instruction' must be string")
            
        if 'items' in text_format:
            if not isinstance(text_format['items'], dict):
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: 'text_format.items' must be object")
            elif 'buttons' in text_format['items']:
                self._validate_buttons(flow_name, node_id, text_format['items']['buttons'])
    
    def _validate_buttons(self, flow_name: str, node_id: str, buttons: Any):
        """Validate button definitions."""
        if not isinstance(buttons, list):
            self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: 'text_format.items.buttons' must be array")
            return
            
        for i, button in enumerate(buttons):
            if not isinstance(button, dict):
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: button {{i}} must be object")
                continue
                
            if 'id' not in button:
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: button {{i}} missing 'id' field")
            elif not isinstance(button['id'], str):
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: button {{i}} 'id' must be string")
                
            if 'suggested_text' not in button:
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: button {{i}} missing 'suggested_text' field")
            elif not isinstance(button['suggested_text'], str):
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: button {{i}} 'suggested_text' must be string")
    
    def _validate_routing(self, flow_name: str, node_id: str, routing: Dict):
        """Validate routing logic."""
        if not routing:
            self.warnings.append(f"Flow {{flow_name}}, Node {{node_id}}: 'how_to_route' is empty - node might be a dead end")
            return
            
        for target, condition in routing.items():
            if not isinstance(target, str):
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: routing target must be string")
                continue
                
            if not isinstance(condition, str):
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: routing condition for '{{target}}' must be string")
                continue
                
            if not condition.strip():
                self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: routing condition for '{{target}}' cannot be empty")
                
            # Validate routing target format
            if '.' in target:
                # Cross-flow routing: "flow_name.node_id"
                target_flow, target_node = target.split('.', 1)
                if target_flow not in self.all_flow_names:
                    self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: routing target flow '{{target_flow}}' does not exist")
                elif target_flow in self.all_node_ids and target_node not in self.all_node_ids[target_flow]:
                    self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: routing target node '{{target_node}}' not found in flow '{{target_flow}}'")
            elif target.startswith('this.'):
                # Same-flow routing: "this.node_id"
                target_node = target[5:]  # Remove "this."
                if flow_name in self.all_node_ids and target_node not in self.all_node_ids[flow_name]:
                    self.errors.append(f"Flow {{flow_name}}, Node {{node_id}}: routing target node '{{target_node}}' not found in current flow")
            else:
                self.warnings.append(f"Flow {{flow_name}}, Node {{node_id}}: routing target '{{target}}' should use 'this.' prefix for same-flow or 'flow.node' for cross-flow")
    
    def _validate_cross_references(self):
        """Validate cross-references between flows and configuration."""
        # 1) Ensure node IDs are globally unique across ALL flows
        #    According to the new restriction: node ids should be unique even between flows
        global_node_id_to_locations: Dict[str, list[tuple[str, str]]] = {{}}
        for flow_name, nodes in self.all_node_ids.items():
            for node_id in nodes:
                global_node_id_to_locations.setdefault(node_id, []).append((flow_name, node_id))

        duplicates = {{nid: locs for nid, locs in global_node_id_to_locations.items() if len(locs) > 1}}
        for dup_node_id, locations in duplicates.items():
            flows_list = ', '.join(sorted({{flow for flow, _ in locations}}))
            self.errors.append(
                f"Global uniqueness violation: node id '{{dup_node_id}}' appears in multiple flows: {{flows_list}}. "
                f"Node ids must be unique across all flows."
            )

        # 2) Validate that every flow's startNodeId references an existing node (redundant guard)
        for flow_name, flow_data in self.flows.items():
            start_node_id = flow_data.get('startNodeId')
            if isinstance(start_node_id, str):
                if flow_name not in self.all_node_ids or start_node_id not in self.all_node_ids[flow_name]:
                    self.errors.append(
                        f"Flow {{flow_name}}: startNodeId '{{start_node_id}}' does not reference an existing node in this flow"
                    )
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        is_valid = len(self.errors) == 0
        
        report = {{
            'is_valid': is_valid,
            'folder_path': str(self.folder_path),
            'total_flows': len(self.flows),
            'total_nodes': sum(len(nodes) for nodes in self.all_node_ids.values()),
            'errors': self.errors,
            'warnings': self.warnings,
            'summary': {{
                'agent_config_found': self.agent_config is not None,
                'flows_found': list(self.all_flow_names),
                'start_flows': [name for name, data in self.flows.items() if data.get('isStartFlow')],
                'error_count': len(self.errors),
                'warning_count': len(self.warnings)
            }}
        }}
        
        return report

# Run the validation
validator = DSLValidator(
    folder_path="{dsl_folder_path}",
    strict_mode={strict_mode},
    check_tool_refs={check_tool_references}
)

validation_result = validator.validate()

# Format output based on requested format
output_format = "{output_format}"

if output_format == "json":
    import json
    print(json.dumps(validation_result, indent=2, ensure_ascii=False))
elif output_format == "summary":
    print("=== DSL Validation Summary ===")
    print(f"Folder: {{validation_result['folder_path']}}")
    print(f"Valid: {{validation_result['is_valid']}}")
    print(f"Flows: {{validation_result['total_flows']}}")
    print(f"Nodes: {{validation_result['total_nodes']}}")
    print(f"Errors: {{validation_result['summary']['error_count']}}")
    print(f"Warnings: {{validation_result['summary']['warning_count']}}")
    
    if validation_result['errors']:
        print("\\n=== ERRORS ===")
        for error in validation_result['errors']:
            print(f"❌ {{error}}")
            
    if validation_result['warnings']:
        print("\\n=== WARNINGS ===")
        for warning in validation_result['warnings']:
            print(f"⚠️  {{warning}}")
else:
    # Detailed format (default)
    print("=" * 80)
    print("DSL INTEGRITY VALIDATION REPORT")
    print("=" * 80)
    print(f"Folder Path: {{validation_result['folder_path']}}")
    print(f"Validation Status: {{'✅ PASSED' if validation_result['is_valid'] else '❌ FAILED'}}")
    print(f"Total Flows: {{validation_result['total_flows']}}")
    print(f"Total Nodes: {{validation_result['total_nodes']}}")
    print(f"Strict Mode: {strict_mode}")
    print(f"Tool Reference Check: {check_tool_references}")
    
    print("\\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    summary = validation_result['summary']
    print(f"Agent Config Found: {{'✅' if summary['agent_config_found'] else '❌'}}")
    print(f"Flows Found: {{', '.join(summary['flows_found']) if summary['flows_found'] else 'None'}}")
    print(f"Start Flows: {{', '.join(summary['start_flows']) if summary['start_flows'] else 'None'}}")
    print(f"Error Count: {{summary['error_count']}}")
    print(f"Warning Count: {{summary['warning_count']}}")
    
    if validation_result['errors']:
        print("\\n" + "=" * 80)
        print("ERRORS FOUND")
        print("=" * 80)
        for i, error in enumerate(validation_result['errors'], 1):
            print(f"{{i:3d}}. ❌ {{error}}")
    
    if validation_result['warnings']:
        print("\\n" + "=" * 80)
        print("WARNINGS")
        print("=" * 80)
        for i, warning in enumerate(validation_result['warnings'], 1):
            print(f"{{i:3d}}. ⚠️  {{warning}}")
    
    if validation_result['is_valid']:
        print("\\n" + "=" * 80)
        print("🎉 DSL VALIDATION PASSED!")
        print("All DSL files are properly structured and follow the specification.")
        print("=" * 80)
    else:
        print("\\n" + "=" * 80)
        print("💥 DSL VALIDATION FAILED!")
        print("Please fix the errors above before proceeding.")
        print("=" * 80)

# Store validation result for potential further processing
dsl_validation_result = validation_result
'''
    
    return IPythonRunCellAction(code=validation_code) 