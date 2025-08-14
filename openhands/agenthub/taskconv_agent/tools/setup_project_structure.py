"""
Tool for setting up the project structure for the conversational system.
This tool creates the necessary directories and files for the flow configurations.
"""

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

SetupProjectStructureTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='setup_project_structure',
        description=(
            'Sets up the project structure for the Task-Based Conversational System. '
            'Creates the necessary directories and base files for flow configurations, '
            'including flows_config directory, main configuration files, and '
            'documentation structure. This tool organizes the project to support '
            'the generated conversation flows.'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'project_path': {
                    'type': 'string',
                    'description': 'Path to the project directory'
                },
                'flow_names': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'List of flow names that will be created'
                },
                'project_metadata': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'description': {'type': 'string'},
                        'domain': {'type': 'string'},
                        'version': {'type': 'string', 'default': '1.0.0'}
                    },
                    'description': 'Metadata about the conversational system project'
                },
                'create_docs': {
                    'type': 'boolean',
                    'description': 'Whether to create documentation structure',
                    'default': True
                },
                'create_tests': {
                    'type': 'boolean', 
                    'description': 'Whether to create test structure',
                    'default': True
                }
            },
            'required': ['project_path', 'flow_names', 'project_metadata']
        },
    ),
) 