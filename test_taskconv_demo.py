#!/usr/bin/env python3
"""
Quick demonstration of TaskConvAgent functionality
"""

from unittest.mock import Mock
from openhands.agenthub.taskconv_agent import TaskConvAgent
from openhands.core.config import AgentConfig

def demo_taskconv_agent():
    """Demonstrate TaskConvAgent capabilities"""
    
    print("🚀 TaskConvAgent Demo")
    print("=" * 50)
    
    # Create a proper mock LLM
    mock_config = Mock()
    mock_config.model = "gpt-4"
    
    mock_llm = Mock()
    mock_llm.config = mock_config
    
    # Create agent config
    config = AgentConfig()
    config.enable_cmd = True
    config.enable_jupyter = True
    config.enable_browsing = False
    
    # Create TaskConvAgent
    agent = TaskConvAgent(llm=mock_llm, config=config)
    
    print(f"✅ Agent Name: {agent.__class__.__name__}")
    print(f"✅ Version: {agent.VERSION}")
    print(f"✅ Total Tools: {len(agent.tools)}")
    
    # Show capabilities
    capabilities = agent.get_capabilities()
    print(f"✅ CodeAct Capabilities: {len(capabilities['codeact_capabilities'])}")
    print(f"✅ TaskConv Specializations: {len(capabilities['taskconv_specializations'])}")
    print(f"✅ Specialized Tools: {len(capabilities['specialized_tools'])}")
    print(f"✅ Supported Domains: {len(capabilities['supported_domains'])}")
    
    # Show specialized tools
    print("\n🔧 Specialized Tools:")
    for tool in capabilities['specialized_tools']:
        print(f"   - {tool}")
    
    # Show supported domains
    print("\n🏢 Supported Domains:")
    for domain in capabilities['supported_domains']:
        print(f"   - {domain}")
    
    print("\n✅ TaskConvAgent is working correctly!")

if __name__ == "__main__":
    demo_taskconv_agent() 