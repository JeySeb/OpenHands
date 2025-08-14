"""
Function calling implementation for TaskConvAgent.

This module handles the conversion of LLM responses into OpenHands actions
and provides the specialized tools for Task-Based Conversational System development.
It extends CodeAct's function calling to support both CodeAct and TaskConv tools.
"""

import json
import os
from typing import List

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
)
from openhands.core.exceptions import (
    FunctionCallNotExistsError,
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
    mcp_tool_names: List[str] | None = None,
) -> List[Action]:
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
    actions: List[Action] = []
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
                raise RuntimeError(
                    f'Failed to parse tool call arguments: {tool_call.function.arguments}'
                ) from e

            # Check if this is a TaskConv-specific tool
            if tool_call.function.name in taskconv_tool_names:
                # Handle TaskConv-specific tools
                if tool_call.function.name == 'clone_base_repo':
                    action = _handle_clone_base_repo(arguments)
                    
                elif tool_call.function.name == 'analyze_specifications':
                    action = _handle_analyze_specifications(arguments)
                    
                elif tool_call.function.name == 'decompose_flows':
                    action = _handle_decompose_flows(arguments)
                    
                elif tool_call.function.name == 'generate_flow_config':
                    action = _handle_generate_flow_config(arguments)
                    
                elif tool_call.function.name == 'setup_project_structure':
                    action = _handle_setup_project_structure(arguments)
                    
                elif tool_call.function.name == 'finalize_system':
                    action = _handle_finalize_system(arguments)
                else:
                    raise FunctionCallNotExistsError(
                        f'TaskConv tool {tool_call.function.name} is not implemented. '
                        f'(arguments: {arguments}).'
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


def get_taskconv_tools() -> List[ChatCompletionToolParam]:
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
    ]


def get_tools() -> List[ChatCompletionToolParam]:
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
    git_url = os.getenv('GIT_URL')  
    clone_command = f'git clone -b {branch} {git_url} {target_directory}'

    return CmdRunAction(command=clone_command)

def _handle_analyze_specifications(arguments: dict) -> Action:
    """Handle the analyze_specifications tool call."""
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