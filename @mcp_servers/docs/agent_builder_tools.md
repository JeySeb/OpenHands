# Agent Builder MCP Server - Currently Implemented Tools

This document provides detailed descriptions and usage examples for the **currently implemented** tools in the Agent Builder MCP server. This server is specifically designed for OpenHands (AI builder agent) to interact with the Agent Builder Backend API.

## 🔧 Available MCP Tools

The current implementation includes **8 core tools** focused on the OpenHands builder workflow:

---

## 1. `get_pending_builds`

**Purpose**: Primary OpenHands polling endpoint to discover agents that need to be built.

**Description**: OpenHands uses this endpoint to regularly poll for work. It returns a paginated list of agents that are pending build, allowing OpenHands to act as an AI builder agent.

**Parameters**:
- `page` (int, optional): Page number for pagination (default: 1)
- `per_page` (int, optional): Number of agents per page, max 100 (default: 50)

**Usage Example**:
```javascript
// Poll for agents needing build
get_pending_builds({
    "page": 1,
    "per_page": 20
})
```

**Expected Response**:
```json
{
    "agents": [
        {
            "agent_id": "456e7890-e89b-12d3-a456-426614174000",
            "handle": "customer_support_agent",
            "personality": "Friendly and helpful customer service representative",
            "build_status": "pending",
            "created_at": "2024-01-15T10:30:00Z"
        }
    ],
    "total": 5,
    "page": 1,
    "per_page": 20,
    "mcp_server": "agent_builder_mcp",
    "mcp_tool": "get_pending_builds"
}
```

---

## 2. `get_agent_details`

**Purpose**: Get complete information about a specific agent for build preparation.

**Description**: OpenHands uses this to retrieve comprehensive agent information including personality, goals, constraints, and metadata needed for generating appropriate artifacts.

**Parameters**:
- `agent_id` (str, required): UUID of the agent to retrieve

**Usage Example**:
```javascript
// Get detailed agent information
get_agent_details({
    "agent_id": "456e7890-e89b-12d3-a456-426614174000"
})
```

**Expected Response**:
```json
{
    "agent": {
        "agent_id": "456e7890-e89b-12d3-a456-426614174000",
        "handle": "customer_support_agent",
        "graph_name": "CustomerSupportGraph",
        "agent_persona_name": "Customer Service Assistant",
        "personality": "Friendly, patient, and solution-oriented",
        "general_goal": "Provide excellent customer service and resolve issues efficiently",
        "constraints": {
            "max_response_length": 500,
            "language": "en-US",
            "escalation_threshold": 3
        },
        "build_status": "pending",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    },
    "mcp_server": "agent_builder_mcp",
    "mcp_tool": "get_agent_details"
}
```

---

## 3. `get_agent_specifications`

**Purpose**: Retrieve all specification documents that define agent behavior.

**Description**: Essential for OpenHands build process. Returns metadata for all specifications associated with an agent. OpenHands uses these to understand what artifacts need to be generated.

**Parameters**:
- `agent_id` (str, required): UUID of the agent whose specifications to retrieve
- `spec_type` (str, optional): Filter by specification type ("subflow_spec", "mcp_api_spec", "agent_config")

**Usage Example**:
```javascript
// Get all specifications for an agent
get_agent_specifications({
    "agent_id": "456e7890-e89b-12d3-a456-426614174000"
})

// Get only MCP API specifications
get_agent_specifications({
    "agent_id": "456e7890-e89b-12d3-a456-426614174000",
    "spec_type": "mcp_api_spec"
})
```

**Expected Response**:
```json
{
    "specifications": [
        {
            "spec_id": "789e1234-e89b-12d3-a456-426614174000",
            "spec_type": "subflow_spec",
            "name": "greeting_flow",
            "format": "yaml",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z"
        },
        {
            "spec_id": "abc5678-e89b-12d3-a456-426614174000",
            "spec_type": "mcp_api_spec",
            "name": "customer_data_api",
            "format": "json",
            "created_at": "2024-01-15T11:00:00Z",
            "updated_at": "2024-01-15T11:00:00Z"
        }
    ],
    "total": 2,
    "mcp_server": "agent_builder_mcp",
    "mcp_tool": "get_agent_specifications"
}
```

---

## 4. `get_specification_content`

**Purpose**: Get the full content of a specific specification for artifact generation.

**Description**: OpenHands calls this for each specification to get the detailed content needed for generating artifacts. The content contains the actual specification data that drives the generation process.

**Parameters**:
- `agent_id` (str, required): UUID of the agent
- `spec_id` (str, required): UUID of the specification to retrieve

**Usage Example**:
```javascript
// Get full specification content
get_specification_content({
    "agent_id": "456e7890-e89b-12d3-a456-426614174000",
    "spec_id": "789e1234-e89b-12d3-a456-426614174000"
})
```

**Expected Response**:
```json
{
    "specification": {
        "spec_id": "789e1234-e89b-12d3-a456-426614174000",
        "spec_type": "subflow_spec",
        "name": "greeting_flow",
        "format": "yaml",
        "content": "greeting:\n  steps:\n    - welcome_message\n    - identify_customer\n    - offer_assistance\ntriggers:\n  - conversation_start\n  - return_customer",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    },
    "mcp_server": "agent_builder_mcp",
    "mcp_tool": "get_specification_content"
}
```

---

## 5. `save_generated_artifacts`

**Purpose**: Save multiple generated artifacts in batch - Core OpenHands output endpoint.

**Description**: This is the primary endpoint OpenHands uses to save all generated artifacts after processing agent specifications. OpenHands generates multiple artifacts (MCP servers, configs, DSL JSON) and saves them all at once.

**Parameters**:
- `agent_id` (str, required): UUID of the agent to save artifacts for
- `artifacts` (List[Dict], required): List of artifact objects with the following structure:
  - `artifact_type`: Type ("dsl_json", "mcp_server_code", "mcp_config", "other")
  - `name`: Artifact name (e.g., "agent_definition.json")
  - `content`: The actual artifact content
  - `mime_type`: Content MIME type (e.g., "application/json", "text/x-python")
  - `file_path` (optional): File path

**Usage Example**:
```javascript
// Save multiple artifacts for an agent
save_generated_artifacts({
    "agent_id": "456e7890-e89b-12d3-a456-426614174000",
    "artifacts": [
        {
            "artifact_type": "dsl_json",
            "name": "agent_definition.json",
            "content": "{\"version\": \"1.0\", \"agent_config\": {\"personality_weight\": 0.8}}",
            "mime_type": "application/json",
            "file_path": "agents/customer_support/definition.json"
        },
        {
            "artifact_type": "mcp_server_code",
            "name": "customer_tools_mcp.py",
            "content": "from fastmcp import FastMCP\n\nmcp = FastMCP('customer_tools')\n\n@mcp.tool()\ndef get_order_status(order_id: str):\n    return f\"Order {order_id} status\"",
            "mime_type": "text/x-python",
            "file_path": "mcp_servers/customer_tools_mcp.py"
        },
        {
            "artifact_type": "mcp_config",
            "name": "customer_tools_config.json",
            "content": "{\"server_name\": \"customer_tools\", \"tools\": [\"get_order_status\", \"process_refund\"]}",
            "mime_type": "application/json"
        }
    ]
})
```

**Expected Response**:
```json
{
    "artifacts_created": [
        {
            "artifact_id": "def7890-e89b-12d3-a456-426614174000",
            "artifact_type": "dsl_json",
            "name": "agent_definition.json",
            "created_at": "2024-01-15T12:00:00Z"
        },
        {
            "artifact_id": "ghi1234-e89b-12d3-a456-426614174000",
            "artifact_type": "mcp_server_code",
            "name": "customer_tools_mcp.py",
            "created_at": "2024-01-15T12:00:00Z"
        },
        {
            "artifact_id": "jkl5678-e89b-12d3-a456-426614174000",
            "artifact_type": "mcp_config",
            "name": "customer_tools_config.json",
            "created_at": "2024-01-15T12:00:00Z"
        }
    ],
    "total_saved": 3,
    "mcp_server": "agent_builder_mcp",
    "mcp_tool": "save_generated_artifacts"
}
```

---

## 6. `complete_agent_build`

**Purpose**: Mark an agent build as complete - Final step in OpenHands build workflow.

**Description**: OpenHands calls this after successfully generating and saving all artifacts to notify the backend that the build process is complete. This updates the agent's build status and makes it available for deployment.

**Parameters**:
- `agent_id` (str, required): UUID of the agent whose build is complete
- `success` (bool, optional): Whether the build was successful (default: True)

**Usage Example**:
```javascript
// Mark successful build completion
complete_agent_build({
    "agent_id": "456e7890-e89b-12d3-a456-426614174000",
    "success": true
})

// Mark failed build
complete_agent_build({
    "agent_id": "456e7890-e89b-12d3-a456-426614174000",
    "success": false
})
```

**Expected Response**:
```json
{
    "agent": {
        "agent_id": "456e7890-e89b-12d3-a456-426614174000",
        "build_status": "built",
        "build_completed_at": "2024-01-15T12:30:00Z",
        "build_successful": true
    },
    "build_completed": true,
    "mcp_server": "agent_builder_mcp",
    "mcp_tool": "complete_agent_build"
}
```

---

## 7. `get_existing_artifacts`

**Purpose**: Get list of existing artifacts for an agent - Optional helper for OpenHands.

**Description**: OpenHands can use this to check what artifacts already exist before generating new ones, useful for incremental builds or avoiding duplicates.

**Parameters**:
- `agent_id` (str, required): UUID of the agent whose artifacts to list
- `artifact_type` (str, optional): Filter by artifact type

**Usage Example**:
```javascript
// Get all existing artifacts
get_existing_artifacts({
    "agent_id": "456e7890-e89b-12d3-a456-426614174000"
})

// Get only MCP server code artifacts
get_existing_artifacts({
    "agent_id": "456e7890-e89b-12d3-a456-426614174000",
    "artifact_type": "mcp_server_code"
})
```

**Expected Response**:
```json
{
    "artifacts": [
        {
            "artifact_id": "def7890-e89b-12d3-a456-426614174000",
            "artifact_type": "dsl_json",
            "name": "agent_definition.json",
            "mime_type": "application/json",
            "file_path": "agents/customer_support/definition.json",
            "created_at": "2024-01-15T12:00:00Z"
        },
        {
            "artifact_id": "ghi1234-e89b-12d3-a456-426614174000",
            "artifact_type": "mcp_server_code",
            "name": "customer_tools_mcp.py",
            "mime_type": "text/x-python",
            "file_path": "mcp_servers/customer_tools_mcp.py",
            "created_at": "2024-01-15T12:00:00Z"
        }
    ],
    "total": 2,
    "mcp_server": "agent_builder_mcp",
    "mcp_tool": "get_existing_artifacts"
}
```

---

## 8. `get_artifact_content`

**Purpose**: Get the content of a specific existing artifact - Optional helper for OpenHands.

**Description**: OpenHands can use this to retrieve existing artifact content if needed for reference or incremental generation.

**Parameters**:
- `agent_id` (str, required): UUID of the agent
- `artifact_id` (str, required): UUID of the artifact to retrieve

**Usage Example**:
```javascript
// Get specific artifact content
get_artifact_content({
    "agent_id": "456e7890-e89b-12d3-a456-426614174000",
    "artifact_id": "def7890-e89b-12d3-a456-426614174000"
})
```

**Expected Response**:
```json
{
    "artifact": {
        "artifact_id": "def7890-e89b-12d3-a456-426614174000",
        "artifact_type": "dsl_json",
        "name": "agent_definition.json",
        "content": "{\"version\": \"1.0\", \"agent_config\": {\"personality_weight\": 0.8, \"technical_knowledge\": 0.9}}",
        "mime_type": "application/json",
        "file_path": "agents/customer_support/definition.json",
        "created_at": "2024-01-15T12:00:00Z",
        "updated_at": "2024-01-15T12:00:00Z"
    },
    "mcp_server": "agent_builder_mcp",
    "mcp_tool": "get_artifact_content"
}
```

---

## 🔄 Complete OpenHands Build Workflow

Here's how OpenHands would use these tools in a typical build workflow:

```javascript
// 1. Poll for pending builds
const pendingBuilds = get_pending_builds({"page": 1, "per_page": 10});

// 2. For each pending agent, get details
const agentDetails = get_agent_details({"agent_id": "456e7890-e89b-12d3-a456-426614174000"});

// 3. Get all specifications for the agent
const specs = get_agent_specifications({"agent_id": "456e7890-e89b-12d3-a456-426614174000"});

// 4. Get content for each specification
for (const spec of specs.specifications) {
    const content = get_specification_content({
        "agent_id": "456e7890-e89b-12d3-a456-426614174000",
        "spec_id": spec.spec_id
    });
    // Process specification content and generate artifacts
}

// 5. Check existing artifacts (optional)
const existing = get_existing_artifacts({"agent_id": "456e7890-e89b-12d3-a456-426614174000"});

// 6. Generate and save all artifacts
const savedArtifacts = save_generated_artifacts({
    "agent_id": "456e7890-e89b-12d3-a456-426614174000",
    "artifacts": [/* generated artifacts */]
});

// 7. Mark build as complete
const completion = complete_agent_build({
    "agent_id": "456e7890-e89b-12d3-a456-426614174000",
    "success": true
});
```

## 🔧 Configuration and Authentication

### Environment Variables

The MCP server requires these environment variables:

```bash
# Required: API authentication token
AGENT_BUILDER_API_TOKEN=your-actual-api-token-here

# Optional: Backend API base URL (default: http://localhost:8000)
AGENT_BUILDER_API_BASE_URL=https://your-backend-api.com

# Optional: MCP server configuration
MCP_TRANSPORT=stdio  # or "http"
MCP_HTTP_HOST=127.0.0.1  # if using HTTP transport
MCP_HTTP_PORT=8001       # if using HTTP transport
MCP_HTTP_PATH=/mcp       # if using HTTP transport
```

### Error Handling

All tools return structured error responses when something goes wrong:

```json
{
    "error": "Agent not found",
    "status_code": 404,
    "mcp_server": "agent_builder_mcp",
    "mcp_tool": "get_agent_details",
    "tool_params": {"agent_id": "invalid-id"},
    "endpoint": "http://localhost:8000/api/v1/agents/invalid-id"
}
```

## 📋 Supported Artifact Types

The `save_generated_artifacts` tool supports these artifact types:

- **`dsl_json`**: Agent definition and configuration in JSON format
- **`mcp_server_code`**: Python code for MCP server implementations
- **`mcp_config`**: Configuration files for MCP servers
- **`other`**: Any other type of generated artifact

## 📋 Supported Specification Types

The `get_agent_specifications` tool can filter by these specification types:

- **`subflow_spec`**: Conversation flow specifications
- **`mcp_api_spec`**: API integration specifications
- **`agent_config`**: Agent configuration specifications

---

This documentation covers all currently implemented tools in the Agent Builder MCP server. The server is specifically designed for the OpenHands builder workflow and provides a focused set of tools for that use case.
