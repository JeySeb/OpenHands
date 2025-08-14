"""
Tool for generating flow configuration files in natural language.
This tool creates detailed configuration files for each conversation flow.
"""

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

GenerateFlowConfigTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='generate_flow_config',
        description=(
            'Generates detailed flow configuration files in natural language. '
            'Creates comprehensive specifications for each conversation flow including '
            'conversation patterns, user intents, responses, routing logic, and '
            'integration points. Each flow config file serves as a blueprint for '
            'the conversational sub-agent that will handle that specific flow.'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'flow_name': {
                    'type': 'string',
                    'description': 'Name of the conversation flow (e.g., "main_orchestration", "property_search", "information")'
                },
                'flow_purpose': {
                    'type': 'string',
                    'description': 'Primary purpose and responsibilities of this flow'
                },
                'user_intents': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'List of user intents this flow should handle'
                },
                'conversation_patterns': {
                    'type': 'array',
                    'items': {'type': 'string'}, 
                    'description': 'Expected conversation patterns and message flows'
                },
                'routing_logic': {
                    'type': 'string',
                    'description': 'Logic for routing conversations to other flows or ending conversations'
                },
                'integration_points': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'External systems, APIs, or databases this flow needs to interact with',
                    'default': []
                },
                'response_templates': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Template responses and message patterns for this flow',
                    'default': []
                },
                'context_variables': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Context variables this flow needs to maintain',
                    'default': []
                }
            },
            'required': ['flow_name', 'flow_purpose', 'user_intents', 'conversation_patterns', 'routing_logic']
        },
    ),
) 