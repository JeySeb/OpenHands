# OpenHands Builder Workflow - Ejemplos Prácticos

Este documento muestra ejemplos específicos de cómo OpenHands usa el servidor MCP para construir agentes conversacionales.

## 🔄 Flujo Completo de Construcción

### Paso 1: Polling Automático por Trabajo

OpenHands ejecuta esta herramienta periódicamente para encontrar agentes que necesitan construcción:

```javascript
// OpenHands busca trabajo cada 5 minutos
get_pending_builds({
    "page": 1,
    "per_page": 50
})

// Respuesta del backend:
{
    "agents": [
        {
            "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "user_id": "user-uuid",
            "handle": "customer_support_v2",
            "graph_name": "CustomerSupportGraph",
            "agent_persona_name": "Asistente Virtual Sarah",
            "personality": "Profesional, empática y orientada a soluciones",
            "general_goal": "Brindar soporte técnico y resolver consultas de usuarios",
            "constraints": {
                "max_response_length": 500,
                "language": "es-ES",
                "escalation_threshold": 3
            },
            "version": "2.1.0",
            "is_built": false,
            "build_status": "pending",
            "created_at": "2024-01-20T10:30:00Z",
            "updated_at": "2024-01-20T10:30:00Z"
        }
    ],
    "total": 1,
    "page": 1,
    "per_page": 50,
    "mcp_server": "agent_builder_mcp",
    "mcp_tool": "get_pending_builds"
}
```

### Paso 2: Obtener Información Detallada del Agente

```javascript
// OpenHands obtiene información completa del agente seleccionado
get_agent_details({
    "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
})

// Información detallada para generar artefactos apropiados
{
    "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "handle": "customer_support_v2",
    "graph_name": "CustomerSupportGraph",
    "agent_persona_name": "Asistente Virtual Sarah",
    "personality": "Profesional, empática y orientada a soluciones. Siempre busca entender el problema del usuario antes de ofrecer ayuda. Mantiene un tono amigable pero profesional.",
    "general_goal": "Brindar soporte técnico eficiente, resolver consultas de usuarios, escalamientos apropiados cuando sea necesario, y mantener alta satisfacción del cliente",
    "constraints": {
        "max_response_length": 500,
        "language": "es-ES",
        "escalation_threshold": 3,
        "business_hours": "09:00-18:00 GMT-5",
        "supported_topics": ["technical_support", "billing", "account_management"]
    },
    "build_status": "pending",
    "mcp_server": "agent_builder_mcp"
}
```

### Paso 3: Obtener Lista de Especificaciones

```javascript
// OpenHands obtiene todas las especificaciones del agente
get_agent_specifications({
    "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
})

// Lista de especificaciones disponibles
[
    {
        "spec_id": "spec-001-subflow",
        "name": "flujo_saludo_inicial",
        "spec_type": "subflow_spec",
        "format": "yaml",
        "version": 1,
        "content_length": 1024,
        "created_at": "2024-01-20T09:00:00Z"
    },
    {
        "spec_id": "spec-002-mcp",
        "name": "integracion_tickets_api",
        "spec_type": "mcp_api_spec",
        "format": "json",
        "version": 1,
        "content_length": 2048,
        "created_at": "2024-01-20T09:15:00Z"
    },
    {
        "spec_id": "spec-003-config",
        "name": "configuracion_escalamiento",
        "spec_type": "agent_config",
        "format": "yaml",
        "version": 1,
        "content_length": 512,
        "created_at": "2024-01-20T09:30:00Z"
    }
]
```

### Paso 4: Leer Contenido de Cada Especificación

```javascript
// OpenHands lee el contenido de la especificación de subflow
get_specification_content({
    "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "spec_id": "spec-001-subflow"
})

// Contenido de la especificación subflow
{
    "spec_id": "spec-001-subflow",
    "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "spec_type": "subflow_spec",
    "name": "flujo_saludo_inicial",
    "content": "# Flujo de Saludo Inicial\n\ngoal: Establecer conexión empática con el usuario\n\nsteps:\n  1. saludo_personalizado:\n     prompt: \"Hola, soy Sarah, tu asistente virtual. ¿En qué puedo ayudarte hoy?\"\n     tone: amigable_profesional\n     \n  2. identificar_categoria:\n     action: classify_request\n     categories: [technical_support, billing, account_management, other]\n     \n  3. confirmar_comprension:\n     prompt: \"Entiendo que necesitas ayuda con {categoria}. ¿Es correcto?\"\n     wait_for_confirmation: true",
    "format": "yaml",
    "version": 1,
    "created_at": "2024-01-20T09:00:00Z"
}

// OpenHands lee el contenido de la especificación MCP
get_specification_content({
    "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "spec_id": "spec-002-mcp"
})

// Contenido de la especificación MCP
{
    "spec_id": "spec-002-mcp",
    "spec_type": "mcp_api_spec",
    "name": "integracion_tickets_api",
    "content": "{\n  \"mcp_server_name\": \"ticket_management_mcp\",\n  \"description\": \"MCP server for ticket system integration\",\n  \"tools\": [\n    {\n      \"name\": \"create_ticket\",\n      \"description\": \"Create a new support ticket\",\n      \"parameters\": {\n        \"type\": \"object\",\n        \"properties\": {\n          \"title\": {\"type\": \"string\"},\n          \"description\": {\"type\": \"string\"},\n          \"priority\": {\"type\": \"string\", \"enum\": [\"low\", \"medium\", \"high\"]},\n          \"category\": {\"type\": \"string\"}\n        }\n      }\n    },\n    {\n      \"name\": \"get_ticket_status\",\n      \"description\": \"Check status of existing ticket\",\n      \"parameters\": {\n        \"type\": \"object\",\n        \"properties\": {\n          \"ticket_id\": {\"type\": \"string\"}\n        }\n      }\n    }\n  ],\n  \"api_config\": {\n    \"base_url\": \"https://api.ticketsystem.com/v1\",\n    \"auth_type\": \"bearer_token\",\n    \"timeout\": 30\n  }\n}",
    "format": "json"
}
```

### Paso 5: Generación de Artefactos (OpenHands internamente)

Basándose en las especificaciones, OpenHands genera múltiples artefactos:

#### Artefacto 1: Servidor MCP generado
```python
# Generated MCP Server: ticket_management_mcp.py
import os
import requests
import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ticket_management_mcp")

@mcp.tool("create_ticket", "Create a new support ticket")
def create_ticket(title: str, description: str, priority: str, category: str) -> str:
    """Create a new support ticket in the system."""
    data = {
        "title": title,
        "description": description,
        "priority": priority,
        "category": category
    }

    response = requests.post(
        "https://api.ticketsystem.com/v1/tickets",
        headers={"Authorization": f"Bearer {os.getenv('TICKET_API_TOKEN')}"},
        json=data,
        timeout=30
    )

    return json.dumps(response.json())

@mcp.tool("get_ticket_status", "Check status of existing ticket")
def get_ticket_status(ticket_id: str) -> str:
    """Get the current status of a ticket."""
    response = requests.get(
        f"https://api.ticketsystem.com/v1/tickets/{ticket_id}",
        headers={"Authorization": f"Bearer {os.getenv('TICKET_API_TOKEN')}"},
        timeout=30
    )

    return json.dumps(response.json())

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

#### Artefacto 2: Configuración DSL JSON
```json
{
  "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "handle": "customer_support_v2",
  "graph_name": "CustomerSupportGraph",
  "version": "2.1.0",
  "persona": {
    "name": "Asistente Virtual Sarah",
    "personality": "Profesional, empática y orientada a soluciones",
    "voice_tone": "amigable_profesional"
  },
  "capabilities": {
    "max_response_length": 500,
    "supported_languages": ["es-ES"],
    "escalation_threshold": 3,
    "business_hours": "09:00-18:00 GMT-5"
  },
  "subflows": {
    "initial_greeting": {
      "spec_id": "spec-001-subflow",
      "implementation": "flujo_saludo_inicial"
    }
  },
  "mcp_integrations": {
    "ticket_management": {
      "server_name": "ticket_management_mcp",
      "spec_id": "spec-002-mcp",
      "tools": ["create_ticket", "get_ticket_status"]
    }
  },
  "deployment": {
    "status": "built",
    "build_timestamp": "2024-01-20T11:45:00Z",
    "artifacts_count": 3
  }
}
```

#### Artefacto 3: Configuración MCP
```json
{
  "mcp_servers": {
    "ticket_management_mcp": {
      "command": "python",
      "args": ["ticket_management_mcp.py"],
      "env": {
        "TICKET_API_TOKEN": "${TICKET_API_TOKEN}"
      },
      "description": "MCP server for ticket system integration"
    }
  },
  "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "generated_by": "OpenHands",
  "generation_timestamp": "2024-01-20T11:45:00Z"
}
```

### Paso 6: Guardar Todos los Artefactos

```javascript
// OpenHands guarda todos los artefactos generados en una sola operación
save_generated_artifacts({
    "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "artifacts": [
        {
            "artifact_type": "mcp_server_code",
            "name": "ticket_management_mcp.py",
            "content": "# Generated MCP Server: ticket_management_mcp.py\nimport os...",
            "mime_type": "text/x-python"
        },
        {
            "artifact_type": "dsl_json",
            "name": "agent_definition.json",
            "content": "{\n  \"agent_id\": \"a1b2c3d4-e5f6-7890-abcd-ef1234567890\",\n  \"handle\": \"customer_support_v2\"...",
            "mime_type": "application/json"
        },
        {
            "artifact_type": "mcp_config",
            "name": "mcp_config.json",
            "content": "{\n  \"mcp_servers\": {\n    \"ticket_management_mcp\": {...",
            "mime_type": "application/json"
        }
    ]
})

// Respuesta de confirmación
[
    {
        "artifact_id": "artifact-001",
        "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "artifact_type": "mcp_server_code",
        "name": "ticket_management_mcp.py",
        "size_bytes": 2048,
        "checksum": "sha256:abc123...",
        "version": 1,
        "created_at": "2024-01-20T11:45:00Z"
    },
    {
        "artifact_id": "artifact-002",
        "artifact_type": "dsl_json",
        "name": "agent_definition.json",
        "size_bytes": 1024,
        "checksum": "sha256:def456...",
        "version": 1,
        "created_at": "2024-01-20T11:45:00Z"
    },
    {
        "artifact_id": "artifact-003",
        "artifact_type": "mcp_config",
        "name": "mcp_config.json",
        "size_bytes": 512,
        "checksum": "sha256:ghi789...",
        "version": 1,
        "created_at": "2024-01-20T11:45:00Z"
    }
]
```

### Paso 7: Completar la Construcción

```javascript
// OpenHands marca la construcción como exitosa
complete_agent_build({
    "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "success": true
})

// Confirmación del backend
{
    "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "user_id": "user-uuid",
    "handle": "customer_support_v2",
    "build_status": "built",
    "is_built": true,
    "last_built_at": "2024-01-20T11:45:00Z",
    "artifacts_count": 3,
    "mcp_server": "agent_builder_mcp",
    "mcp_tool": "complete_agent_build"
}
```

## 🔧 Casos de Error y Recuperación

### Error en Construcción

```javascript
// Si OpenHands encuentra un error durante la generación
complete_agent_build({
    "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "success": false
})

// El agente vuelve a estado "failed" y puede ser reintentado
{
    "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "build_status": "failed",
    "is_built": false,
    "last_built_at": "2024-01-20T11:45:00Z",
    "error_details": "Generation failed during MCP server creation"
}
```

### Construcción Incremental

```javascript
// OpenHands puede verificar artefactos existentes antes de generar
get_existing_artifacts({
    "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "artifact_type": "mcp_server_code"
})

// Si ya existen, puede decidir regenerar solo algunos o todos
```

## 🎯 Puntos Clave para OpenHands

1. **Polling Inteligente**: Usar `get_pending_builds` cada 5-10 minutos
2. **Lectura Completa**: Siempre leer todas las especificaciones antes de generar
3. **Generación Atómica**: Generar todos los artefactos antes de guardar
4. **Manejo de Errores**: Siempre marcar el resultado final con `complete_agent_build`
5. **Metadatos Ricos**: Incluir MIME types apropiados para cada artefacto

Este flujo garantiza que OpenHands funcione como un constructor eficiente y confiable de agentes conversacionales.
