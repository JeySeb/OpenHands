"""
Unit tests for TaskConvAgent.

These tests validate the basic functionality and tool integration
of the TaskConvAgent specialized for Task-Based Conversational Systems.
"""

import pytest
from unittest.mock import Mock, patch

from openhands.agenthub.taskconv_agent import TaskConvAgent
from openhands.core.config import AgentConfig
from openhands.llm.llm import LLM


class TestTaskConvAgent:
    """Test suite for TaskConvAgent functionality."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for testing."""
        mock_config = Mock()
        mock_config.model = "test-model"
        
        mock_llm = Mock(spec=LLM)
        mock_llm.config = mock_config
        return mock_llm
    
    @pytest.fixture
    def agent_config(self):
        """Create a basic agent configuration."""
        config = AgentConfig()
        config.enable_cmd = True
        config.enable_jupyter = True
        config.enable_browsing = False
        return config
    
    @pytest.fixture
    def taskconv_agent(self, mock_llm, agent_config):
        """Create a TaskConvAgent instance for testing."""
        return TaskConvAgent(llm=mock_llm, config=agent_config)
    
    def test_agent_initialization(self, taskconv_agent):
        """Test that TaskConvAgent initializes correctly."""
        assert taskconv_agent is not None
        assert taskconv_agent.VERSION == '1.0'
        assert 'TaskConvAgent extends CodeActAgent with specialized capabilities' in taskconv_agent.DESCRIPTION
        
    def test_agent_has_required_tools(self, taskconv_agent):
        """Test that TaskConvAgent has all required specialized tools."""
        tool_names = [tool['function']['name'] for tool in taskconv_agent.tools]
        
        expected_tools = [
            'clone_base_repo',
            'analyze_specifications', 
            'decompose_flows',
            'generate_flow_config',
            'setup_project_structure',
            'finalize_system',
            'finish'  # From FinishTool
        ]
        
        for tool in expected_tools:
            assert tool in tool_names, f"Missing required tool: {tool}"
    
    def test_agent_configuration(self, taskconv_agent):
        """Test that agent configuration is set correctly."""
        assert taskconv_agent.config.enable_cmd is True
        assert taskconv_agent.config.enable_jupyter is True
        assert taskconv_agent.config.enable_browsing is False
        
    def test_agent_capabilities(self, taskconv_agent):
        """Test that agent capabilities are correctly defined."""
        capabilities = taskconv_agent.get_capabilities()
        
        assert capabilities['name'] == 'TaskConvAgent'
        assert capabilities['version'] == '1.0'
        assert 'Task-Based Conversational System development' in capabilities['taskconv_specializations']
        assert 'Real Estate' in capabilities['supported_domains']
        assert 'clone_base_repo' in capabilities['specialized_tools']
        
    def test_clone_base_repo_tool_definition(self, taskconv_agent):
        """Test that clone_base_repo tool is properly defined."""
        clone_tool = None
        for tool in taskconv_agent.tools:
            if tool['function']['name'] == 'clone_base_repo':
                clone_tool = tool
                break
                
        assert clone_tool is not None
        assert 'project_name' in clone_tool['function']['parameters']['required']
        assert 'llm_automater_graph' in clone_tool['function']['description']
        
    def test_analyze_specifications_tool_definition(self, taskconv_agent):
        """Test that analyze_specifications tool is properly defined."""
        analyze_tool = None
        for tool in taskconv_agent.tools:
            if tool['function']['name'] == 'analyze_specifications':
                analyze_tool = tool
                break
                
        assert analyze_tool is not None
        assert 'user_requirements' in analyze_tool['function']['parameters']['required']
        assert 'specifications' in analyze_tool['function']['description'].lower()
        
    def test_generate_flow_config_tool_definition(self, taskconv_agent):
        """Test that generate_flow_config tool is properly defined."""
        config_tool = None
        for tool in taskconv_agent.tools:
            if tool['function']['name'] == 'generate_flow_config':
                config_tool = tool
                break
                
        assert config_tool is not None
        required_params = config_tool['function']['parameters']['required']
        assert 'flow_name' in required_params
        assert 'flow_purpose' in required_params
        assert 'user_intents' in required_params
        
    def test_system_prompt_additions(self, taskconv_agent):
        """Test that system prompt additions are comprehensive."""
        prompt_additions = taskconv_agent.get_system_prompt_additions()
        
        assert 'TaskConvAgent' in prompt_additions
        assert 'Mission' in prompt_additions
        assert 'Flow Architecture' in prompt_additions
        assert 'Analyze Requirements' in prompt_additions
        
    @patch('openhands.agenthub.taskconv_agent.function_calling.response_to_actions')
    def test_response_to_actions_delegation(self, mock_response_to_actions, taskconv_agent):
        """Test that response_to_actions delegates correctly."""
        mock_response = Mock()
        mock_response_to_actions.return_value = []
        
        result = taskconv_agent.response_to_actions(mock_response)
        
        mock_response_to_actions.assert_called_once_with(
            mock_response,
            mcp_tool_names=list(taskconv_agent.mcp_tools.keys())
        )
        assert result == []


class TestTaskConvAgentIntegration:
    """Integration tests for TaskConvAgent with other system components."""
    
    def test_agent_can_be_imported(self):
        """Test that TaskConvAgent can be imported successfully."""
        from openhands.agenthub.taskconv_agent import TaskConvAgent
        assert TaskConvAgent is not None
        
    def test_agent_registration(self):
        """Test that TaskConvAgent is properly registered in the system."""
        # This test would need access to the agent registry
        # Implementation depends on how OpenHands handles agent registration
        pass


# Example test data for future functionality testing
SAMPLE_REQUIREMENTS = """
I want to build a real estate chatbot that helps users:
1. Search for properties with filters like location, price, and type
2. Get information about our company and services
3. Apply for financing and pre-approval
4. Schedule property viewings
5. Get general real estate advice
"""

EXPECTED_FLOWS = [
    'main_orchestration',
    'property_search_flow', 
    'information_flow',
    'application_flow',
    'scheduling_flow'
] 