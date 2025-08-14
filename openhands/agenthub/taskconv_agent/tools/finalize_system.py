"""
Tool for finalizing the Task-Based Conversational System.
This tool completes the setup and provides instructions for deployment and testing.
"""

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

FinalizeSystemTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='finalize_system',
        description=(
            'Finalizes the Task-Based Conversational System setup. '
            'Creates final configuration files, deployment instructions, '
            'testing guidelines, and provides a comprehensive summary of '
            'the created system including how to run, test, and deploy it.'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'project_path': {
                    'type': 'string',
                    'description': 'Path to the project directory'
                },
                'system_summary': {
                    'type': 'string',
                    'description': 'Summary of the created conversational system and its capabilities'
                },
                'flows_created': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'List of conversation flows that were created'
                },
                'deployment_type': {
                    'type': 'string',
                    'enum': ['local', 'cloud', 'docker', 'kubernetes'],
                    'description': 'Preferred deployment method for the system',
                    'default': 'local'
                },
                'testing_requirements': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Specific testing requirements or scenarios to validate',
                    'default': []
                },
                'integration_notes': {
                    'type': 'string',
                    'description': 'Special notes about integrations or dependencies',
                    'default': ''
                }
            },
            'required': ['project_path', 'system_summary', 'flows_created']
        },
    ),
) 