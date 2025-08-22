"""
Tool for verifying Agents DSL integrity in conversational system definitions.
This tool validates the complete DSL structure including agent configuration,
flow definitions, node types, and routing logic according to specifications.
"""

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

VerifyDslIntegrityTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='verify_dsl_integrity',
        description=(
            'Verifies the integrity and correctness of Agents DSL definitions in a given folder. '
            'This tool validates agent configuration files (agent_config.json) and all flow '
            'definition files (graph/*.json) against the DSL specification. It checks syntax, '
            'structure, node types, routing logic, and references. Returns detailed validation '
            'results with specific error descriptions if any issues are found.'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'dsl_folder_path': {
                    'type': 'string',
                    'description': 'Path to the folder containing DSL files (agent_config.json and graph/ subfolder with .json files)'
                },
                'strict_mode': {
                    'type': 'boolean',
                    'description': 'Enable strict validation mode that checks additional best practices and recommendations',
                    'default': True
                },
                'check_tool_references': {
                    'type': 'boolean', 
                    'description': 'Whether to validate that tool references in tool_node elements exist in availableServersMCP',
                    'default': True
                },
                'output_format': {
                    'type': 'string',
                    'enum': ['detailed', 'summary', 'json'],
                    'description': 'Format for validation output: detailed (full descriptions), summary (brief), or json (structured)',
                    'default': 'detailed'
                }
            },
            'required': ['dsl_folder_path']
        },
    ),
)