"""
TaskConvAgent - Specialized agent for Task-Based Conversational Systems

This agent is responsible for creating comprehensive Task-Based Conversational Systems
that handle complex multi-step conversations through structured flows and task-oriented interactions.
"""

from typing import TYPE_CHECKING

import openhands.agenthub.taskconv_agent.function_calling as taskconv_function_calling
from openhands.agenthub.codeact_agent import CodeActAgent
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm import LLM

if TYPE_CHECKING: 
    from litellm import ChatCompletionToolParam
    from openhands.events.action import Action
    from openhands.llm.llm import ModelResponse


class TaskConvAgent(CodeActAgent):
    """
    Specialized agent for building Task-Based Conversational Systems.
    
    This agent extends CodeActAgent with specialized tools for:
    - Analyzing user requirements for conversational systems
    - Decomposing complex conversations into manageable flows
    - Creating natural language flow configurations
    - Setting up project structures for conversational systems
    - Integrating with the llm_automater_graph base repository
    
    TaskConvAgent is a superset of CodeActAgent, capable of everything CodeActAgent
    can do plus specialized conversational system development.
    """
    
    VERSION = '1.0'
    DESCRIPTION = (
        'TaskConvAgent extends CodeActAgent with specialized capabilities for creating '
        'Task-Based Conversational Systems. It includes all CodeActAgent functionality '
        '(bash, Python, file editing, etc.) plus specialized tools for conversational '
        'system development, flow decomposition, and project setup.'
    )

    def __init__(
        self,
        llm: LLM,
        config: AgentConfig,
    ) -> None:
        """
        Initialize TaskConvAgent.

        Parameters:
        - llm (LLM): The language model to be used by this agent
        - config (AgentConfig): The configuration for the agent
        """
        super().__init__(llm, config)
        
        # Set agent-specific configuration before getting tools
        self._setup_agent_config()
        
        # Get tools by extending parent's tools with TaskConv-specific tools
        self.tools = self._get_tools()
        
        logger.info(
            f'TaskConvAgent initialized with {len(self.tools)} tools: '
            f'{", ".join([tool.get("function").get("name") for tool in self.tools])}'
        )

    def _get_tools(self) -> list['ChatCompletionToolParam']:
        """
        Get the complete set of tools for TaskConvAgent.
        This extends CodeActAgent's tools with TaskConv-specific tools.
        
        Returns:
            Combined list of CodeAct tools + TaskConv specialized tools
        """
        # Get all the base CodeAct tools
        codeact_tools = super()._get_tools()
        
        # Get TaskConv specialized tools
        taskconv_tools = taskconv_function_calling.get_taskconv_tools()
        
        # Combine both sets of tools
        all_tools = codeact_tools + taskconv_tools
        
        logger.debug(
            f'TaskConvAgent tools: {len(codeact_tools)} CodeAct + '
            f'{len(taskconv_tools)} TaskConv = {len(all_tools)} total'
        )
        
        return all_tools

    def _setup_agent_config(self) -> None:
        """Configure agent-specific settings."""
        # Enable features needed for conversational system development
        self.config.enable_cmd = True  # For git operations and file system management
        self.config.enable_jupyter = True  # For analysis and data processing
        self.config.enable_editor = True  # For file editing capabilities
        
        # TaskConv systems typically don't need browsing by default, but keep it configurable
        if not hasattr(self.config, 'enable_browsing') or self.config.enable_browsing is None:
            self.config.enable_browsing = False
        
        logger.debug('TaskConvAgent configuration set up successfully')

    def response_to_actions(self, response: 'ModelResponse') -> list['Action']:
        """
        Convert LLM response to OpenHands actions using both CodeAct and TaskConv tools.
        
        This method handles both:
        - All standard CodeAct tools (bash, Python, file editing, etc.)
        - TaskConv specialized tools (conversational system development)
        
        Args:
            response: The model response containing tool calls or messages
            
        Returns:
            List of actions to be executed
        """
        return taskconv_function_calling.response_to_actions(
            response,
            mcp_tool_names=list(self.mcp_tools.keys()),
        )

    def get_capabilities(self) -> dict:
        """
        Return the capabilities of TaskConvAgent.
        
        Returns:
            Dictionary describing agent capabilities including both CodeAct and TaskConv features
        """
        return {
            'name': 'TaskConvAgent',
            'version': self.VERSION,
            'description': self.DESCRIPTION,
            'extends': 'CodeActAgent',
            'codeact_capabilities': [
                'Bash command execution',
                'Python/Jupyter code execution', 
                'File reading and editing',
                'Browser interaction',
                'Thinking and reasoning',
                'Task completion signaling'
            ],
            'taskconv_specializations': [
                'Task-Based Conversational System development',
                'Conversation flow decomposition',
                'Natural language flow configuration generation',
                'Conversational system architecture design',
                'Project structure setup for conversational AI',
                'Integration with llm_automater_graph base repository'
            ],
            'specialized_tools': [
                'clone_base_repo',
                'analyze_specifications',
                'decompose_flows',
                'generate_flow_config',
                'setup_project_structure',
                'finalize_system',
                'build_mcp_server'
            ],
            'supported_domains': [
                'Real Estate',
                'E-commerce',
                'Customer Service',
                'Healthcare',
                'Finance',
                'Education',
                'General Business'
            ]
        }

    def get_system_prompt_additions(self) -> str:
        """
        Get additional system prompt content specific to TaskConvAgent.
        
        Returns:
            Additional prompt content for system message
        """
        return """
You are TaskConvAgent, a specialized AI agent for creating Task-Based Conversational Systems.

## Your Mission
Create comprehensive conversational AI systems that handle complex, multi-step interactions through structured conversation flows.

## Your Expertise
- **Flow Architecture**: Design conversation flows that break complex interactions into manageable, specialized sub-conversations
- **Natural Language Processing**: Create systems that maintain natural, human-like conversations while following structured logic
- **Task Decomposition**: Break down complex conversational requirements into specific, focused flows
- **System Integration**: Set up complete project structures with proper organization and documentation

## Your Approach
1. **Analyze Requirements**: Deeply understand what the user wants to build
2. **Decompose Flows**: Break the system into main orchestration + specialized flows
3. **Generate Configurations**: Create detailed natural language specifications for each flow
4. **Structure Project**: Set up organized project structure with proper documentation
5. **Finalize System**: Provide complete setup with deployment and testing guidance

## Flow Types You Create
- **Main Orchestration Flow**: Handles initial user contact and routes to specialized flows
- **Specialized Task Flows**: Handle specific business processes or user intents
- **Information Flows**: Provide information and answer questions
- **Transaction Flows**: Handle business transactions and processes
- **Support Flows**: Provide assistance and troubleshooting

## Key Principles
- Each flow has a single, clear responsibility
- Conversations feel natural and intuitive to users
- System is modular and maintainable
- Documentation is comprehensive and clear
- Testing and deployment are well-defined

Remember: You're building systems that enable natural conversations while achieving specific business objectives.
""" 