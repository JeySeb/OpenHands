"""
Tool for cloning the base repository for Task-Based Conversational Systems.
This tool handles the initial setup by cloning the llm_automater_graph repository.
"""

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

CloneBaseRepoTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='clone_base_repo',
        description=(
            'Clones the base repository for Task-Based Conversational Systems. '
            'This repository (https://github.com/JeySeb/LangGraph-Interpreter#) contains '
            'the foundational structure and dependencies required for all conversational systems. '
            'This should be the first step when setting up a new conversational system project.'
            'The repository to be cloned is always https://github.com/JeySeb/LangGraph-Interpreter. '
            'No additional parameters are added to the repository name.'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'target_directory': {
                    'type': 'string', 
                    'description': 'Target directory where the project should be cloned (optional, defaults to current directory)',
                    'default': '.'
                },
                'branch': {
                    'type': 'string',
                    'description': 'Branch to clone (optional, defaults to main)',
                    'default': 'main'
                }
            },
            'required': ['target_directory']
        },
    ),
) 