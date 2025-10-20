import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import requests
import json
import logging

# Ensure project root is on sys.path so we can import project modules
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP

"""
MCP Server for Agent Builder Backend Integration - OpenHands Builder Mode

This server provides a focused integration between OpenHands (acting as AI builder agent)
and the Agent Builder Backend API. OpenHands uses this MCP server to:

1. Poll for agents needing build (GET /agents/system/pending-builds)
2. Read agent specifications (GET /agents/{agent_id}/specifications)
3. Generate artifacts (MCP servers, JSON configs, etc.)
4. Save artifacts to backend (POST /agents/{agent_id}/artifacts/batch)
5. Mark builds as complete (POST /agents/{agent_id}/build-complete)

This focused implementation includes only the essential endpoints needed for the
OpenHands build workflow, optimizing for the AI agent builder use case.

Authentication is handled via Bearer tokens for admin-level access.
"""

SERVER_NAME = "agent_builder_mcp"
logger = logging.getLogger(SERVER_NAME)

# Authentication token - In production, this should be securely managed
API_TOKEN = os.environ.get("AGENT_BUILDER_API_TOKEN", "your-api-token-here")

def _default_base_url() -> str:
    """Get the base URL for the Agent Builder Backend API."""
    return os.environ.get("AGENT_BUILDER_API_BASE_URL", "http://localhost:8000")

def _resolve_endpoint(endpoint: str) -> str:
    """Resolve endpoint to full URL, allowing absolute URL overrides."""
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint
    base = _default_base_url().rstrip("/")
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    return f"{base}{endpoint}"

def _get_auth_headers() -> Dict[str, str]:
    """Get authentication headers for API requests."""
    return {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

def _make_request(
    method: str,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    mcp_tool: Optional[str] = None,
    timeout: int = 30
) -> Any:
    """Make an HTTP request and return JSON with metadata."""
    resolved = _resolve_endpoint(endpoint)
    headers = _get_auth_headers()

    # Prepare request arguments
    request_args = {"timeout": timeout, "headers": headers}
    payload_for_logging = {}

    if method.upper() in ["GET", "DELETE"]:
        clean_payload = {k: v for k, v in (params or {}).items() if v is not None}
        request_args["params"] = clean_payload
        payload_for_logging = {"params": clean_payload}
    else:  # POST, PUT, etc.
        clean_payload = {k: v for k, v in (json_data or {}).items() if v is not None}
        request_args["json"] = clean_payload
        payload_for_logging = {"json": clean_payload}

    logger.debug(f"HTTP {method.upper()}: {resolved} {payload_for_logging}")

    response = None
    try:
        response = requests.request(method, resolved, **request_args)
        response.raise_for_status()

        # Handle empty responses (e.g., 204 No Content for DELETE)
        if response.status_code == 204 or not response.content:
            result = {"success": True, "status_code": response.status_code}
        else:
            result = response.json()

        # Add metadata
        if isinstance(result, dict):
            result["mcp_server"] = SERVER_NAME
            result["mcp_tool"] = mcp_tool
            result["tool_params"] = clean_payload
            result["endpoint"] = resolved

        return result

    except requests.RequestException as exc:
        # Return structured error payload for HTTP/Network errors
        status_code = getattr(response, "status_code", None)
        return {
            "error": str(exc),
            "status_code": status_code,
            "mcp_server": SERVER_NAME,
            "mcp_tool": mcp_tool,
            "tool_params": clean_payload,
            "endpoint": resolved,
        }
    except json.JSONDecodeError as exc:
        # Handle cases where the response is not valid JSON
        return {
            "error": f"Failed to decode JSON response: {exc}",
            "status_code": getattr(response, "status_code", 500),
            "response_text": response.text if response else "No response",
            "mcp_server": SERVER_NAME,
            "mcp_tool": mcp_tool,
            "tool_params": clean_payload,
            "endpoint": resolved,
        }

def _get_json(endpoint: str, params: Optional[Dict[str, Any]] = None, mcp_tool: Optional[str] = None) -> Any:
    """Make GET request and return JSON with metadata."""
    return _make_request('GET', endpoint, params=params, mcp_tool=mcp_tool)

def _post_json(endpoint: str, data: Optional[Dict[str, Any]] = None, mcp_tool: Optional[str] = None) -> Any:
    """Make POST request and return JSON with metadata."""
    return _make_request('POST', endpoint, json_data=data, mcp_tool=mcp_tool)

def _put_json(endpoint: str, data: Optional[Dict[str, Any]] = None, mcp_tool: Optional[str] = None) -> Any:
    """Make PUT request and return JSON with metadata."""
    return _make_request('PUT', endpoint, json_data=data, mcp_tool=mcp_tool)

def _delete_json(endpoint: str, params: Optional[Dict[str, Any]] = None, mcp_tool: Optional[str] = None) -> Any:
    """Make DELETE request and return JSON with metadata."""
    return _make_request('DELETE', endpoint, params=params, mcp_tool=mcp_tool)

def _create_mcp() -> FastMCP:
    """Create and configure FastMCP instance."""
    host = os.environ.get("MCP_HTTP_HOST", "127.0.0.1")
    port_str = os.environ.get("MCP_HTTP_PORT", "8001")
    path = os.environ.get("MCP_HTTP_PATH", "/mcp")
    try:
        port = int(port_str)
    except ValueError:
        port = 8001
    return FastMCP(
        SERVER_NAME,
        host=host,
        port=port,
        streamable_http_path=path,
    )

mcp = _create_mcp()

# ============================================================
# CORE OPENHANDS BUILDER WORKFLOW TOOLS
# ============================================================

@mcp.tool()
def get_pending_builds(page: int = 1, per_page: int = 50) -> str:
    """
    Get list of agents pending build - Primary OpenHands polling endpoint.

    This is the main endpoint OpenHands uses to discover agents that need to be built.
    OpenHands polls this endpoint regularly to find work to do as an AI builder agent.

    Args:
        page: Page number for pagination (default: 1)
        per_page: Number of agents per page, max 100 (default: 50)

    Returns:
        JSON string containing paginated list of agents pending build with full metadata
    """
    try:
        params = {
            "page": page,
            "per_page": min(per_page, 100)
        }
        result = _get_json("/api/v1/agents/system/pending-builds", params=params, mcp_tool="get_pending_builds")
        return json.dumps(result, ensure_ascii=False)
    except Exception as error:
        logger.error(f"Failed to get pending builds: {str(error)}")
        return json.dumps({"error": str(error), "agents": [], "total": 0}, ensure_ascii=False)

@mcp.tool()
def get_agent_details(agent_id: str) -> str:
    """
    Get detailed information about a specific agent by its ID.

    OpenHands uses this to get complete agent information including personality,
    goals, constraints, and metadata needed for generating appropriate artifacts.

    Args:
        agent_id: UUID of the agent to retrieve

    Returns:
        JSON string containing complete agent information including build status
    """
    try:
        # Validate agent_id is provided and not empty
        if not agent_id or not agent_id.strip():
            error_msg = "Validation failed: agent_id is mandatory and cannot be empty. Please provide a valid agent UUID."
            logger.error(error_msg)
            return json.dumps({
                "error": error_msg,
                "validation_error": True,
                "agent": None
            }, ensure_ascii=False)

        result = _get_json(f"/api/v1/agents/{agent_id.strip()}", mcp_tool="get_agent_details")
        return json.dumps(result, ensure_ascii=False)
    except Exception as error:
        logger.error(f"Failed to get agent {agent_id}: {str(error)}")
        return json.dumps({"error": str(error), "agent": None}, ensure_ascii=False)

@mcp.tool()
def complete_agent_build(agent_id: str, success: bool = True) -> str:
    """
    Mark an agent build as complete - Final step in OpenHands build workflow.

    OpenHands calls this after successfully generating and saving all artifacts
    to notify the backend that the build process is complete. This updates the
    agent's build status and makes it available for deployment.

    Args:
        agent_id: UUID of the agent whose build is complete
        success: Whether the build was successful (default: True)

    Returns:
        JSON string containing updated agent information with new build status
    """
    try:
        params = {"success": success}
        result = _post_json(f"/api/v1/agents/{agent_id}/build-complete",
                           data={}, params=params, mcp_tool="complete_agent_build")
        return json.dumps(result, ensure_ascii=False)
    except Exception as error:
        logger.error(f"Failed to complete build for agent {agent_id}: {str(error)}")
        return json.dumps({"error": str(error), "build_completed": False}, ensure_ascii=False)

@mcp.tool()
def get_agent_specifications(
    agent_id: str,
    spec_type: Optional[str] = None
) -> str:
    """
    Get all specifications for an agent - Essential for OpenHands build process.

    OpenHands uses this to retrieve all specification documents that define how
    the agent should behave. These specifications are used to generate the
    appropriate artifacts (MCP servers, configs, etc.).

    Args:
        agent_id: UUID of the agent whose specifications to retrieve
        spec_type: Optional filter by specification type (subflow_spec, mcp_api_spec, agent_config)

    Returns:
        JSON string containing list of specifications with metadata (content not included for efficiency)
    """
    try:
        # Validate agent_id is provided
        if not agent_id or not agent_id.strip():
            error_msg = "Validation failed: agent_id is mandatory and cannot be empty. Please provide a valid agent UUID."
            logger.error(error_msg)
            return json.dumps({
                "error": error_msg,
                "validation_error": True,
                "specifications": []
            }, ensure_ascii=False)

        # Validate spec_type if provided
        VALID_SPEC_TYPES = ["subflow_spec", "mcp_api_spec", "agent_config"]
        if spec_type and spec_type not in VALID_SPEC_TYPES:
            error_msg = f"Validation failed: spec_type must be one of {VALID_SPEC_TYPES}. Received: '{spec_type}'. Please provide a valid specification type or omit the parameter to get all types."
            logger.error(error_msg)
            return json.dumps({
                "error": error_msg,
                "validation_error": True,
                "valid_spec_types": VALID_SPEC_TYPES,
                "received_spec_type": spec_type,
                "specifications": []
            }, ensure_ascii=False)

        params = {}
        if spec_type:
            params["spec_type"] = spec_type

        result = _get_json(f"/api/v1/agents/{agent_id.strip()}/specifications/",
                          params=params, mcp_tool="get_agent_specifications")
        return json.dumps(result, ensure_ascii=False)
    except Exception as error:
        logger.error(f"Failed to get specifications for agent {agent_id}: {str(error)}")
        return json.dumps({"error": str(error), "specifications": []}, ensure_ascii=False)

@mcp.tool()
def get_specification_content(agent_id: str, spec_id: str) -> str:
    """
    Get the full content of a specific specification - Required for OpenHands generation.

    OpenHands calls this for each specification to get the detailed content needed
    for generating artifacts. The content contains the actual specification data
    that drives the artifact generation process.

    Args:
        agent_id: UUID of the agent
        spec_id: UUID of the specification to retrieve

    Returns:
        JSON string containing complete specification data including full content
    """
    try:
        # Validate agent_id is provided
        if not agent_id or not agent_id.strip():
            error_msg = "Validation failed: agent_id is mandatory and cannot be empty. Please provide a valid agent UUID."
            logger.error(error_msg)
            return json.dumps({
                "error": error_msg,
                "validation_error": True,
                "specification": None
            }, ensure_ascii=False)

        # Validate spec_id is provided
        if not spec_id or not spec_id.strip():
            error_msg = "Validation failed: spec_id is mandatory and cannot be empty. Please provide a valid specification UUID."
            logger.error(error_msg)
            return json.dumps({
                "error": error_msg,
                "validation_error": True,
                "specification": None
            }, ensure_ascii=False)

        result = _get_json(f"/api/v1/agents/{agent_id.strip()}/specifications/{spec_id.strip()}",
                          mcp_tool="get_specification_content")
        return json.dumps(result, ensure_ascii=False)
    except Exception as error:
        logger.error(f"Failed to get specification content {spec_id} for agent {agent_id}: {str(error)}")
        return json.dumps({"error": str(error), "specification": None}, ensure_ascii=False)

@mcp.tool()
def save_generated_artifacts(
    agent_id: str,
    artifacts: List[Dict[str, Any]]
) -> str:
    """
    Save multiple generated artifacts in batch - Core OpenHands output endpoint.

    This is the primary endpoint OpenHands uses to save all generated artifacts
    after processing the agent specifications. OpenHands generates multiple
    artifacts (MCP servers, configs, DSL JSON) and saves them all at once.

    Args:
        agent_id: UUID of the agent to save artifacts for
        artifacts: List of artifact dictionaries, each containing:
                  - artifact_type: Type ("dsl_json", "mcp_server_code", "mcp_config", "agent_config", "mcp_server_code_docs","mcp_server_code_tests","other")
                  - name: Artifact name (e.g., "agent_definition.json")
                  - content: The actual artifact content
                  - mime_type: Content MIME type (e.g., "application/json", "text/x-python")
                  - file_path: Optional file path

    Returns:
        JSON string containing list of created artifacts with metadata and validation details
    """
    try:
        # Validate agent_id is provided
        if not agent_id or not agent_id.strip():
            error_msg = "Validation failed: agent_id is mandatory and cannot be empty. Please provide a valid agent UUID."
            logger.error(error_msg)
            return json.dumps({
                "error": error_msg,
                "validation_error": True,
                "artifacts_saved": False
            }, ensure_ascii=False)

        # Validate artifacts list exists and has at least one element
        if not artifacts:
            error_msg = "Validation failed: artifacts list is mandatory and must contain at least one artifact. Please provide a non-empty list of artifacts to save."
            logger.error(error_msg)
            return json.dumps({
                "error": error_msg,
                "validation_error": True,
                "artifacts_saved": False
            }, ensure_ascii=False)

        # Validate each artifact and separate valid from invalid ones
        REQUIRED_FIELDS = ["artifact_type", "name", "content", "mime_type"]
        VALID_ARTIFACT_TYPES = ["dsl_json", "mcp_server_code", "mcp_config", "other"]

        valid_artifacts = []
        invalid_artifacts = []

        for idx, artifact in enumerate(artifacts):
            validation_errors = []

            # Check if artifact is a dictionary
            if not isinstance(artifact, dict):
                invalid_artifacts.append({
                    "index": idx,
                    "artifact": str(artifact),
                    "reason": "Artifact must be a dictionary object."
                })
                continue

            # Check for missing required fields
            missing_fields = [field for field in REQUIRED_FIELDS if field not in artifact or not artifact[field]]
            if missing_fields:
                validation_errors.append(f"Missing required fields: {', '.join(missing_fields)}")

            # Validate artifact_type if present
            if "artifact_type" in artifact and artifact["artifact_type"]:
                if artifact["artifact_type"] not in VALID_ARTIFACT_TYPES:
                    validation_errors.append(f"Invalid artifact_type '{artifact['artifact_type']}'. Must be one of: {', '.join(VALID_ARTIFACT_TYPES)}")

            if validation_errors:
                invalid_artifacts.append({
                    "index": idx,
                    "artifact": {
                        "name": artifact.get("name", "<missing>"),
                        "artifact_type": artifact.get("artifact_type", "<missing>")
                    },
                    "reason": "; ".join(validation_errors)
                })
            else:
                valid_artifacts.append(artifact)

        # If no valid artifacts, return detailed error
        if not valid_artifacts:
            error_msg = f"Validation failed: No valid artifacts to save. All {len(artifacts)} artifact(s) failed validation."
            logger.error(error_msg)
            return json.dumps({
                "error": error_msg,
                "validation_error": True,
                "artifacts_saved": False,
                "total_submitted": len(artifacts),
                "valid_count": 0,
                "invalid_count": len(invalid_artifacts),
                "invalid_artifacts": invalid_artifacts,
                "validation_details": {
                    "required_fields": REQUIRED_FIELDS,
                    "valid_artifact_types": VALID_ARTIFACT_TYPES
                }
            }, ensure_ascii=False)

        # Save valid artifacts
        data = {"artifacts": valid_artifacts}
        result = _post_json(f"/api/v1/agents/{agent_id.strip()}/artifacts/batch",
                           data=data, mcp_tool="save_generated_artifacts")

        # Enhance result with validation details
        if isinstance(result, dict):
            result["validation_summary"] = {
                "total_submitted": len(artifacts),
                "valid_count": len(valid_artifacts),
                "invalid_count": len(invalid_artifacts),
                "artifacts_saved": True
            }

            if invalid_artifacts:
                result["invalid_artifacts"] = invalid_artifacts
                result["warning"] = f"{len(invalid_artifacts)} artifact(s) failed validation and were not saved."

        return json.dumps(result, ensure_ascii=False)

    except Exception as error:
        logger.error(f"Failed to save artifacts for agent {agent_id}: {str(error)}")
        return json.dumps({
            "error": f"Exception occurred while saving artifacts: {str(error)}",
            "artifacts_saved": False
        }, ensure_ascii=False)

@mcp.tool()
def get_existing_artifacts(
    agent_id: str,
    artifact_type: Optional[str] = None
) -> str:
    """
    Get list of existing artifacts for an agent - Optional helper for OpenHands.

    OpenHands can use this to check what artifacts already exist before generating
    new ones, useful for incremental builds or avoiding duplicates.

    Args:
        agent_id: UUID of the agent whose artifacts to list
        artifact_type: Optional filter by artifact type

    Returns:
        JSON string containing list of existing artifacts (metadata only)
    """
    try:
        params = {}
        if artifact_type:
            params["artifact_type"] = artifact_type

        result = _get_json(f"/api/v1/agents/{agent_id}/artifacts/",
                          params=params, mcp_tool="get_existing_artifacts")
        return json.dumps(result, ensure_ascii=False)
    except Exception as error:
        logger.error(f"Failed to get existing artifacts for agent {agent_id}: {str(error)}")
        return json.dumps({"error": str(error), "artifacts": []}, ensure_ascii=False)

@mcp.tool()
def get_artifact_content(agent_id: str, artifact_id: str) -> str:
    """
    Get the content of a specific existing artifact - Optional helper for OpenHands.

    OpenHands can use this to retrieve existing artifact content if needed
    for reference or incremental generation.

    Args:
        agent_id: UUID of the agent
        artifact_id: UUID of the artifact to retrieve

    Returns:
        JSON string containing artifact data including full content
    """
    try:
        result = _get_json(f"/api/v1/agents/{agent_id}/artifacts/{artifact_id}",
                          params={"include_content": True}, mcp_tool="get_artifact_content")
        return json.dumps(result, ensure_ascii=False)
    except Exception as error:
        logger.error(f"Failed to get artifact {artifact_id} for agent {agent_id}: {str(error)}")
        return json.dumps({"error": str(error), "artifact": None}, ensure_ascii=False)

def _run_mcp() -> None:
    """Run the MCP server with appropriate transport."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "http":
        transport = "streamable-http"
    mcp.run(transport=transport)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, help="Port to run MCP server on")
    args = parser.parse_args()

    if args.port:
        os.environ["MCP_HTTP_PORT"] = str(args.port)

    _run_mcp()
