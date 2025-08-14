"""
Tool for decomposing the conversational system into specialized flows.
This tool breaks down complex requirements into manageable, specialized conversation flows.
"""

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

DecomposeFlowsTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='decompose_flows',
        description=(
            'Decomposes the conversational system requirements into specialized flows. '
            'This tool analyzes the requirements and creates a structured breakdown of '
            'conversation flows including a main orchestration flow and specialized sub-flows. '
            'Each flow will have specific responsibilities and handle particular user intents.'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'analyzed_requirements': {
                    'type': 'string',
                    'description': 'Previously analyzed requirements and domain information'
                },
                'main_objectives': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'List of main objectives the conversational system should achieve'
                },
                'user_interactions': {
                    'type': 'array', 
                    'items': {'type': 'string'},
                    'description': 'Types of interactions users will have with the system'
                },
                'business_processes': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Business processes that need to be automated or supported'
                },
                'integration_requirements': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'External systems or APIs that need to be integrated',
                    'default': []
                }
            },
            'required': ['analyzed_requirements', 'main_objectives', 'user_interactions']
        },
    ),
) 