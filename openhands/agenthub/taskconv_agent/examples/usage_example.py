"""
Example usage of TaskConvAgent for creating a Task-Based Conversational System.

This example demonstrates how TaskConvAgent can be used to create a complete
real estate chatbot with multiple specialized conversation flows.
"""

from typing import Dict, Any
from openhands.agenthub.taskconv_agent import TaskConvAgent
from openhands.core.config import AgentConfig


def create_real_estate_chatbot_example():
    """
    Example: Creating a Real Estate Chatbot with TaskConvAgent
    
    This example shows how to use TaskConvAgent to create a comprehensive
    real estate chatbot with multiple conversation flows.
    """
    
    # Sample user requirements for a real estate chatbot
    user_requirements = """
    I want to build a comprehensive real estate chatbot that helps users with:
    
    1. Property Search and Filtering:
       - Search properties by location, price range, property type
       - Filter by amenities, bedrooms, bathrooms
       - View detailed property information and photos
       - Save favorite properties
       - Schedule property viewings
    
    2. Company Information:
       - Learn about our real estate agency
       - Meet our team of agents
       - Understand our services and specialties
       - Get contact information and office locations
       - Read client testimonials
    
    3. Financing and Pre-approval:
       - Apply for mortgage pre-approval
       - Calculate mortgage payments
       - Understand different loan types
       - Connect with preferred lenders
       - Track application status
    
    4. General Real Estate Guidance:
       - First-time buyer information
       - Market trends and insights
       - Neighborhood information
       - Investment property guidance
       - Selling process assistance
    
    The system should feel natural and conversational while efficiently 
    routing users to the right services based on their needs.
    """
    
    return {
        'domain': 'Real Estate',
        'target_audience': 'Property buyers, sellers, and investors',
        'complexity_level': 'complex',
        'requirements': user_requirements,
        'expected_flows': [
            'main_orchestration',
            'property_search_flow',
            'company_information_flow', 
            'financing_application_flow',
            'guidance_and_support_flow'
        ]
    }


def expected_flow_configurations():
    """
    Expected flow configurations that TaskConvAgent should generate.
    """
    
    return {
        'main_orchestration_config.md': {
            'purpose': 'Handle initial user contact and route to appropriate specialized flows',
            'user_intents': [
                'Welcome and greeting',
                'Intent classification',
                'Flow routing',
                'General fallback'
            ],
            'routing_logic': 'Based on user intent, route to appropriate specialized flow'
        },
        
        'property_search_config.md': {
            'purpose': 'Handle property search, filtering, and viewing requests',
            'user_intents': [
                'Search for properties',
                'Filter by criteria',
                'View property details',
                'Schedule viewings',
                'Save favorites'
            ],
            'integration_points': [
                'Property database API',
                'Mapping service integration',
                'Photo gallery system'
            ]
        },
        
        'company_information_config.md': {
            'purpose': 'Provide comprehensive information about the real estate agency',
            'user_intents': [
                'Learn about company',
                'Meet the team',
                'Understand services',
                'Get contact information',
                'Read testimonials'
            ],
            'response_templates': [
                'Company overview responses',
                'Agent introduction templates',
                'Service description formats'
            ]
        },
        
        'financing_application_config.md': {
            'purpose': 'Guide users through financing and pre-approval processes',
            'user_intents': [
                'Apply for pre-approval',
                'Calculate payments',
                'Learn about loan types',
                'Connect with lenders',
                'Track application status'
            ],
            'integration_points': [
                'Lender partner APIs',
                'Credit check services',
                'Document upload system'
            ]
        },
        
        'guidance_and_support_config.md': {
            'purpose': 'Provide general real estate guidance and market insights',
            'user_intents': [
                'First-time buyer help',
                'Market information',
                'Neighborhood details',
                'Investment guidance',
                'Selling assistance'
            ],
            'context_variables': [
                'User experience level',
                'Property preferences',
                'Budget constraints',
                'Timeline requirements'
            ]
        }
    }


def expected_project_structure():
    """
    Expected project structure that TaskConvAgent should create.
    """
    
    return {
        'directories': [
            'real_estate_chatbot/',
            'real_estate_chatbot/flows_config/',
            'real_estate_chatbot/src/',
            'real_estate_chatbot/config/',
            'real_estate_chatbot/docs/',
            'real_estate_chatbot/tests/'
        ],
        'files': [
            'real_estate_chatbot/README.md',
            'real_estate_chatbot/flows_config/main_orchestration_config.md',
            'real_estate_chatbot/flows_config/property_search_config.md',
            'real_estate_chatbot/flows_config/company_information_config.md',
            'real_estate_chatbot/flows_config/financing_application_config.md',
            'real_estate_chatbot/flows_config/guidance_and_support_config.md'
        ]
    }


def demonstration_workflow():
    """
    Demonstrates the complete workflow of TaskConvAgent.
    
    This shows the sequence of tool calls that would be made
    to create a complete Task-Based Conversational System.
    """
    
    workflow_steps = [
        {
            'step': 1,
            'tool': 'analyze_specifications',
            'purpose': 'Analyze user requirements and extract key information',
            'input': 'User requirements for real estate chatbot',
            'output': 'Structured analysis of domain, complexity, and objectives'
        },
        {
            'step': 2,
            'tool': 'clone_base_repo',
            'purpose': 'Set up foundational project structure',
            'input': 'Project name: real_estate_chatbot',
            'output': 'Cloned llm_automater_graph repository as base'
        },
        {
            'step': 3,
            'tool': 'decompose_flows',
            'purpose': 'Break down requirements into specialized flows',
            'input': 'Analyzed requirements and objectives',
            'output': 'Flow structure with main orchestration + specialized flows'
        },
        {
            'step': 4,
            'tool': 'generate_flow_config',
            'purpose': 'Create detailed configuration for each flow',
            'input': 'Flow specifications (called multiple times)',
            'output': 'Natural language configuration files for each flow'
        },
        {
            'step': 5,
            'tool': 'setup_project_structure',
            'purpose': 'Organize project directories and files',
            'input': 'Project path and flow names',
            'output': 'Complete directory structure with organized files'
        },
        {
            'step': 6,
            'tool': 'finalize_system',
            'purpose': 'Complete setup with documentation and instructions',
            'input': 'Project summary and deployment preferences',
            'output': 'Final documentation, setup guides, and deployment instructions'
        }
    ]
    
    return workflow_steps


def expected_business_value():
    """
    Expected business value and capabilities of the generated system.
    """
    
    return {
        'user_experience': [
            'Natural, conversational interactions',
            'Efficient routing to appropriate services',
            'Comprehensive assistance across all real estate needs',
            'Consistent experience across different conversation types'
        ],
        'business_benefits': [
            'Automated lead qualification and routing',
            'Reduced response time for customer inquiries',
            'Improved customer satisfaction through immediate assistance',
            'Scalable customer service without additional staff',
            'Data collection on customer preferences and behaviors'
        ],
        'technical_advantages': [
            'Modular, maintainable conversation architecture',
            'Easy to add new flows or modify existing ones',
            'Clear separation of concerns between different conversation types',
            'Comprehensive documentation for ongoing development',
            'Integration-ready with existing business systems'
        ]
    }


if __name__ == "__main__":
    """
    Example execution flow showing how TaskConvAgent would be used.
    """
    
    print("=== TaskConvAgent Usage Example ===")
    print("Creating a Real Estate Chatbot with Task-Based Conversational System")
    print()
    
    # 1. Show example requirements
    example = create_real_estate_chatbot_example()
    print(f"Domain: {example['domain']}")
    print(f"Target Audience: {example['target_audience']}")
    print(f"Complexity: {example['complexity_level']}")
    print(f"Expected Flows: {', '.join(example['expected_flows'])}")
    print()
    
    # 2. Show workflow
    print("=== TaskConvAgent Workflow ===")
    workflow = demonstration_workflow()
    for step in workflow:
        print(f"Step {step['step']}: {step['tool']}")
        print(f"  Purpose: {step['purpose']}")
        print(f"  Input: {step['input']}")
        print(f"  Output: {step['output']}")
        print()
    
    # 3. Show expected outputs
    print("=== Expected Flow Configurations ===")
    configs = expected_flow_configurations()
    for config_name, details in configs.items():
        print(f"{config_name}:")
        print(f"  Purpose: {details['purpose']}")
        print(f"  User Intents: {len(details['user_intents'])} defined")
        print()
    
    # 4. Show business value
    print("=== Business Value ===")
    value = expected_business_value()
    print(f"User Experience Benefits: {len(value['user_experience'])} key improvements")
    print(f"Business Benefits: {len(value['business_benefits'])} operational advantages")
    print(f"Technical Advantages: {len(value['technical_advantages'])} architectural benefits")
    print()
    
    print("TaskConvAgent enables rapid development of sophisticated conversational systems!") 