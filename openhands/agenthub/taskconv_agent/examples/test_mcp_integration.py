#!/usr/bin/env python3
"""
Simple integration test for TaskConvAgent MCP server tools.
This script tests the import and basic functionality of the new MCP tools.
"""

import sys
import os
from pathlib import Path

# Add the OpenHands path to sys.path to import the modules
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all MCP tools can be imported successfully."""
    print("Testing imports...")
    
    try:
        # Test importing the tool definitions
        from openhands.agenthub.taskconv_agent.tools import (
            CreateMcpServerTool,
            AddMcpToolTool,
            ConfigureMcpServerTool,
            RegisterMcpServerTool,
        )
        print("✓ All MCP tool imports successful")
        
        # Test importing the function calling module
        from openhands.agenthub.taskconv_agent.function_calling import (
            get_taskconv_tools,
            _handle_create_mcp_server,
            _handle_add_mcp_tool,
            _handle_configure_mcp_server,
            _handle_register_mcp_server,
        )
        print("✓ Function calling imports successful")
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_tool_definitions():
    """Test that tool definitions are properly structured."""
    print("\nTesting tool definitions...")
    
    try:
        from openhands.agenthub.taskconv_agent.tools import (
            CreateMcpServerTool,
            AddMcpToolTool,
            ConfigureMcpServerTool,
            RegisterMcpServerTool,
        )
        
        tools = [CreateMcpServerTool, AddMcpToolTool, ConfigureMcpServerTool, RegisterMcpServerTool]
        
        for tool in tools:
            assert tool['type'] == 'function', f"Tool {tool} should have type 'function'"
            assert 'function' in tool, f"Tool {tool} should have 'function' key"
            assert 'name' in tool['function'], f"Tool {tool} should have function name"
            assert 'description' in tool['function'], f"Tool {tool} should have description"
            assert 'parameters' in tool['function'], f"Tool {tool} should have parameters"
            print(f"✓ {tool['function']['name']} tool definition is valid")
        
        return True
    except Exception as e:
        print(f"✗ Tool definition test failed: {e}")
        return False

def test_get_taskconv_tools():
    """Test that get_taskconv_tools returns all tools including MCP tools."""
    print("\nTesting get_taskconv_tools function...")
    
    try:
        from openhands.agenthub.taskconv_agent.function_calling import get_taskconv_tools
        
        tools = get_taskconv_tools()
        tool_names = [tool['function']['name'] for tool in tools]
        
        # Check that original TaskConv tools are present
        original_tools = [
            'clone_base_repo',
            'analyze_specifications', 
            'decompose_flows',
            'generate_flow_config',
            'setup_project_structure',
            'finalize_system'
        ]
        
        # Check that new MCP tools are present
        mcp_tools = [
            'create_mcp_server',
            'add_mcp_tool',
            'configure_mcp_server',
            'register_mcp_server'
        ]
        
        for tool_name in original_tools + mcp_tools:
            assert tool_name in tool_names, f"Tool {tool_name} not found in tool list"
            print(f"✓ {tool_name} found in tool list")
        
        print(f"✓ Total tools found: {len(tools)}")
        return True
    except Exception as e:
        print(f"✗ get_taskconv_tools test failed: {e}")
        return False

def test_handler_functions():
    """Test that handler functions exist and have correct signatures."""
    print("\nTesting handler functions...")
    
    try:
        from openhands.agenthub.taskconv_agent.function_calling import (
            _handle_create_mcp_server,
            _handle_add_mcp_tool,
            _handle_configure_mcp_server,
            _handle_register_mcp_server,
        )
        
        import inspect
        
        handlers = [
            _handle_create_mcp_server,
            _handle_add_mcp_tool,
            _handle_configure_mcp_server,
            _handle_register_mcp_server,
        ]
        
        for handler in handlers:
            sig = inspect.signature(handler)
            assert 'arguments' in sig.parameters, f"Handler {handler.__name__} should accept 'arguments' parameter"
            print(f"✓ {handler.__name__} has correct signature")
        
        return True
    except Exception as e:
        print(f"✗ Handler function test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    print("=== TaskConvAgent MCP Integration Tests ===\n")
    
    tests = [
        test_imports,
        test_tool_definitions,
        test_get_taskconv_tools,
        test_handler_functions,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("🎉 All tests passed! MCP integration is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)