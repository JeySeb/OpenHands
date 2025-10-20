"""
Example: Building an MCP Server with HTTP Headers Support

This example demonstrates how to use the build_mcp_server tool with
the new headers feature for authenticated API access.
"""

import os
from openhands.agenthub.taskconv_agent.function_calling import _handle_build_mcp_server

# Example 1: Simple API Key Authentication
# ==========================================

def example_1_api_key_auth():
    """Example of API key authentication using headers."""

    tools_code = '''
@mcp.tool()
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    result = _get_json(
        f'/weather/current',
        params={"city": city, "units": "metric"},
        mcp_tool='get_weather'
    )
    return json.dumps(result)

@mcp.tool()
def get_forecast(city: str, days: int = 5) -> str:
    """Get weather forecast for a city."""
    result = _get_json(
        f'/weather/forecast',
        params={"city": city, "days": days},
        mcp_tool='get_forecast'
    )
    return json.dumps(result)
'''

    arguments = {
        'interpreter_path': 'LangGraph-Interpreter/',
        'agent_name': 'weather_bot',
        'server_name': 'weather_api_mcp',
        'server_description': 'Weather API client with API key authentication',
        'functional_tools_code': tools_code,
        'uses_external_api': True,
        'base_url_env_var': 'WEATHER_API_URL',
        'default_base_url': 'https://api.weather.com',
        'default_headers': {
            'X-API-Key': '${WEATHER_API_KEY}',
            'Accept': 'application/json'
        },
        'api_timeout': 30
    }

    action = _handle_build_mcp_server(arguments)
    print(f"Example 1: {action}")
    return action


# Example 2: Bearer Token Authentication
# =======================================

def example_2_bearer_token():
    """Example of Bearer token authentication."""

    tools_code = '''
@mcp.tool()
def list_repositories(org: str) -> str:
    """List repositories for an organization."""
    result = _get_json(
        f'/orgs/{org}/repos',
        params={"sort": "updated", "per_page": 10},
        mcp_tool='list_repositories'
    )
    return json.dumps(result)

@mcp.tool()
def create_issue(repo: str, title: str, body: str) -> str:
    """Create an issue in a repository."""
    result = _post_json(
        f'/repos/{repo}/issues',
        data={"title": title, "body": body},
        mcp_tool='create_issue'
    )
    return json.dumps(result)

@mcp.tool()
def get_user_info() -> str:
    """Get authenticated user information."""
    result = _get_json('/user', mcp_tool='get_user_info')
    return json.dumps(result)
'''

    arguments = {
        'interpreter_path': 'LangGraph-Interpreter/',
        'agent_name': 'github_bot',
        'server_name': 'github_api_mcp',
        'server_description': 'GitHub API client with OAuth token authentication',
        'functional_tools_code': tools_code,
        'uses_external_api': True,
        'base_url_env_var': 'GITHUB_API_URL',
        'default_base_url': 'https://api.github.com',
        'default_headers': {
            'Authorization': 'Bearer ${GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-MCP-Bot/1.0'
        },
        'api_timeout': 30
    }

    action = _handle_build_mcp_server(arguments)
    print(f"Example 2: {action}")
    return action


# Example 3: Multiple Authentication Headers
# ===========================================

def example_3_multiple_headers():
    """Example with multiple authentication headers."""

    tools_code = '''
@mcp.tool()
def get_stocks(symbols: str) -> str:
    """Get stock prices for given symbols."""
    result = _get_json(
        '/stocks/quotes',
        params={"symbols": symbols},
        mcp_tool='get_stocks'
    )
    return json.dumps(result)

@mcp.tool()
def place_order(symbol: str, quantity: int, order_type: str) -> str:
    """Place a stock order."""
    result = _post_json(
        '/orders',
        data={
            "symbol": symbol,
            "quantity": quantity,
            "order_type": order_type
        },
        mcp_tool='place_order'
    )
    return json.dumps(result)
'''

    arguments = {
        'interpreter_path': 'LangGraph-Interpreter/',
        'agent_name': 'trading_bot',
        'server_name': 'trading_api_mcp',
        'server_description': 'Trading API client with multi-header authentication',
        'functional_tools_code': tools_code,
        'uses_external_api': True,
        'base_url_env_var': 'TRADING_API_URL',
        'default_base_url': 'https://api.trading.com',
        'default_headers': {
            'Authorization': 'Bearer ${TRADING_API_TOKEN}',
            'X-API-Key': '${TRADING_API_KEY}',
            'X-Client-ID': '${TRADING_CLIENT_ID}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        'api_timeout': 30
    }

    action = _handle_build_mcp_server(arguments)
    print(f"Example 3: {action}")
    return action


# Example 4: Custom Headers Per Request
# ======================================

def example_4_custom_headers():
    """Example showing custom headers for specific requests."""

    tools_code = '''
@mcp.tool()
def list_users() -> str:
    """List all users (uses default headers)."""
    result = _get_json('/api/users', mcp_tool='list_users')
    return json.dumps(result)

@mcp.tool()
def create_user(name: str, email: str, request_id: str) -> str:
    """Create user with request tracking."""
    # Adds custom X-Request-ID header for this specific request
    result = _post_json(
        '/api/users',
        data={"name": name, "email": email},
        headers={"X-Request-ID": request_id},
        mcp_tool='create_user'
    )
    return json.dumps(result)

@mcp.tool()
def admin_delete_user(user_id: int, admin_token: str) -> str:
    """Delete user with admin privileges."""
    # Overrides default Authorization header with admin token
    result = _delete_json(
        f'/api/users/{user_id}',
        headers={"Authorization": f"Bearer {admin_token}"},
        mcp_tool='admin_delete_user'
    )
    return json.dumps(result)

@mcp.tool()
def upload_avatar(user_id: int, image_data: str) -> str:
    """Upload user avatar (different content type)."""
    # Overrides default Content-Type for file upload
    result = _post_json(
        f'/api/users/{user_id}/avatar',
        data={"image": image_data},
        headers={"Content-Type": "multipart/form-data"},
        mcp_tool='upload_avatar'
    )
    return json.dumps(result)
'''

    arguments = {
        'interpreter_path': 'LangGraph-Interpreter/',
        'agent_name': 'user_manager',
        'server_name': 'user_api_mcp',
        'server_description': 'User management API with flexible header support',
        'functional_tools_code': tools_code,
        'uses_external_api': True,
        'default_headers': {
            'Authorization': 'Bearer ${USER_API_TOKEN}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    }

    action = _handle_build_mcp_server(arguments)
    print(f"Example 4: {action}")
    return action


# Example 5: API Versioning with Headers
# =======================================

def example_5_api_versioning():
    """Example showing API versioning through headers."""

    tools_code = '''
@mcp.tool()
def get_products_v2() -> str:
    """Get products using API v2 (default)."""
    result = _get_json('/products', mcp_tool='get_products_v2')
    return json.dumps(result)

@mcp.tool()
def get_products_v1() -> str:
    """Get products using legacy API v1."""
    # Override API version for legacy endpoint
    result = _get_json(
        '/products',
        headers={"X-API-Version": "v1"},
        mcp_tool='get_products_v1'
    )
    return json.dumps(result)

@mcp.tool()
def create_product(name: str, price: float) -> str:
    """Create product using latest API."""
    result = _post_json(
        '/products',
        data={"name": name, "price": price},
        mcp_tool='create_product'
    )
    return json.dumps(result)
'''

    arguments = {
        'interpreter_path': 'LangGraph-Interpreter/',
        'agent_name': 'ecommerce_bot',
        'server_name': 'ecommerce_api_mcp',
        'server_description': 'E-commerce API client with version control',
        'functional_tools_code': tools_code,
        'uses_external_api': True,
        'default_headers': {
            'Authorization': 'Bearer ${ECOMMERCE_API_TOKEN}',
            'X-API-Version': 'v2',
            'Accept': 'application/vnd.ecommerce.v2+json',
            'Content-Type': 'application/json'
        }
    }

    action = _handle_build_mcp_server(arguments)
    print(f"Example 5: {action}")
    return action


# Example 6: No Authentication (Public API)
# ==========================================

def example_6_public_api():
    """Example of a public API that doesn't need authentication."""

    tools_code = '''
@mcp.tool()
def get_random_quote() -> str:
    """Get a random inspirational quote."""
    result = _get_json('/quotes/random', mcp_tool='get_random_quote')
    return json.dumps(result)

@mcp.tool()
def search_quotes(keyword: str) -> str:
    """Search quotes by keyword."""
    result = _get_json(
        '/quotes/search',
        params={"q": keyword},
        mcp_tool='search_quotes'
    )
    return json.dumps(result)
'''

    arguments = {
        'interpreter_path': 'LangGraph-Interpreter/',
        'agent_name': 'quote_bot',
        'server_name': 'quotes_api_mcp',
        'server_description': 'Public quotes API client (no authentication)',
        'functional_tools_code': tools_code,
        'uses_external_api': True,
        'base_url_env_var': 'QUOTES_API_URL',
        'default_base_url': 'https://api.quotable.io',
        # No default_headers needed for public API
    }

    action = _handle_build_mcp_server(arguments)
    print(f"Example 6: {action}")
    return action


# Environment Setup Helper
# =========================

def setup_environment_variables():
    """Helper to set up environment variables for examples."""

    # Example 1: Weather API
    os.environ['WEATHER_API_KEY'] = 'your-weather-api-key-here'
    os.environ['WEATHER_API_URL'] = 'https://api.weather.com'

    # Example 2: GitHub API
    os.environ['GITHUB_TOKEN'] = 'your-github-token-here'
    os.environ['GITHUB_API_URL'] = 'https://api.github.com'

    # Example 3: Trading API
    os.environ['TRADING_API_TOKEN'] = 'your-trading-token-here'
    os.environ['TRADING_API_KEY'] = 'your-trading-api-key-here'
    os.environ['TRADING_CLIENT_ID'] = 'your-client-id-here'
    os.environ['TRADING_API_URL'] = 'https://api.trading.com'

    # Example 4: User API
    os.environ['USER_API_TOKEN'] = 'your-user-api-token-here'

    # Example 5: E-commerce API
    os.environ['ECOMMERCE_API_TOKEN'] = 'your-ecommerce-token-here'

    # Example 6: Quotes API (public, no token needed)
    os.environ['QUOTES_API_URL'] = 'https://api.quotable.io'

    print("✅ Environment variables set up")


# Main execution
# ==============

if __name__ == "__main__":
    print("=" * 80)
    print("MCP Server Headers Feature - Examples")
    print("=" * 80)
    print()

    # Setup environment (in real use, load from .env file)
    print("Setting up environment variables...")
    setup_environment_variables()
    print()

    # Run examples
    examples = [
        ("API Key Authentication", example_1_api_key_auth),
        ("Bearer Token Authentication", example_2_bearer_token),
        ("Multiple Headers", example_3_multiple_headers),
        ("Custom Headers Per Request", example_4_custom_headers),
        ("API Versioning", example_5_api_versioning),
        ("Public API (No Auth)", example_6_public_api),
    ]

    for name, example_func in examples:
        print(f"\n{'=' * 80}")
        print(f"Running: {name}")
        print('=' * 80)
        try:
            example_func()
            print(f"✅ {name} completed successfully")
        except Exception as e:
            print(f"❌ {name} failed: {str(e)}")

    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80)
    print("\nNote: These examples generate MCP server files.")
    print("To run a generated server:")
    print("  1. Set the required environment variables")
    print("  2. Run: python path/to/generated_mcp_server.py")
    print("  3. Check logs for header resolution and API calls")

