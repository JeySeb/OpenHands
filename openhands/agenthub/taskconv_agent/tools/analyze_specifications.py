"""
Tool for analyzing user specifications and requirements for the conversational system.
This tool processes the user's natural language requirements and extracts key information.
"""

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

AnalyzeSpecificationsTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='analyze_specifications',
        description=(
            'Analyzes the user specifications for the Task-Based Conversational System. '
            'This tool processes the natural language requirements to identify the domain, '
            'main objectives, target users, expected interactions, and key functionalities. '
            'Use this to understand what type of conversational system needs to be built.'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'user_requirements': {
                    'type': 'string',
                    'description': 'Complete user specifications and requirements in natural language'
                },
                'domain': {
                    'type': 'string', 
                    'description': 'The business domain or industry (e.g., real estate, e-commerce, customer service)',
                    'default': 'general'
                },
                'target_audience': {
                    'type': 'string',
                    'description': 'Description of the target users who will interact with the system',
                    'default': 'general users'
                },
                'complexity_level': {
                    'type': 'string',
                    'enum': ['simple', 'moderate', 'complex'],
                    'description': 'Expected complexity level of the conversational system',
                    'default': 'moderate'
                }
            },
            'required': ['user_requirements']
        },
    ),
) 