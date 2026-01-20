# OntoGuard MCP Server Usage

## Overview

The OntoGuard MCP server exposes semantic validation capabilities through the Model Context Protocol, allowing AI agents to validate actions against OWL ontologies.

## Configuration

Create a `config.yaml` file (see `examples/config.yaml` for template):

```yaml
ontology_path: "examples/ontologies/ecommerce.owl"
log_level: INFO
cache_validations: true
```

## Running the Server

### Option 1: Direct execution
```bash
python -m ontoguard.mcp_server
```

### Option 2: With custom config
```bash
export ONTOGUARD_CONFIG=/path/to/config.yaml
python -m ontoguard.mcp_server
```

### Option 3: MCP Client Configuration

Add to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "ontoguard": {
      "command": "python",
      "args": ["-m", "ontoguard.mcp_server"],
      "env": {
        "ONTOGUARD_CONFIG": "examples/config.yaml"
      }
    }
  }
}
```

## Available Tools

### 1. validate_action

Validates if an action is semantically allowed by the ontology.

**Parameters:**
- `action` (str): The action to validate (e.g., "delete user", "process refund")
- `entity` (str): The entity type (e.g., "User", "Order", "Refund")
- `entity_id` (str): Unique identifier for the entity instance
- `context` (dict): Additional context (role, amount, timestamp, etc.)

**Returns:**
```json
{
  "allowed": true,
  "reason": "Action 'delete user' is allowed for entity type 'User'",
  "suggested_actions": [],
  "metadata": {}
}
```

### 2. get_allowed_actions

Returns list of actions allowed for an entity and context.

**Parameters:**
- `entity` (str): The entity type to query
- `context` (dict): Context information (role, etc.)

**Returns:**
```json
{
  "allowed_actions": ["create order", "cancel order", "view order"],
  "entity": "Order",
  "context": {"role": "Customer"},
  "count": 3
}
```

### 3. explain_rule

Explains what a specific business rule means.

**Parameters:**
- `rule_name` (str): Name of the rule to explain

**Returns:**
```json
{
  "rule_name": "ProcessRefund",
  "explanation": "Refunds over $1000 require Manager approval...",
  "constraints": [],
  "applies_to": [],
  "found": true
}
```

### 4. check_permissions

Checks if a user role has permission for an action.

**Parameters:**
- `user_role` (str): The role of the user
- `action` (str): The action to check
- `entity` (str): The entity type

**Returns:**
```json
{
  "has_permission": false,
  "role": "Customer",
  "action": "delete user",
  "entity": "User",
  "reason": "Action requires role 'Admin', but user has role 'Customer'",
  "required_roles": ["Admin"]
}
```

## Example Usage

### Using with Claude Desktop

1. Configure the MCP server in Claude Desktop settings
2. Start a conversation with Claude
3. Ask Claude to validate actions:

```
"Can a Customer delete a User? Use the validate_action tool."
```

### Using Programmatically

```python
from ontoguard.mcp_server import validate_action

result = validate_action(
    action="process refund",
    entity="Refund",
    entity_id="refund_123",
    context={"role": "Customer", "refund_amount": 2000.0}
)

print(f"Allowed: {result['allowed']}")
print(f"Reason: {result['reason']}")
```

## Logging

The server logs all validation requests. Set `log_level` in config.yaml:
- `DEBUG`: Detailed debugging information
- `INFO`: General information (default)
- `WARNING`: Warnings only
- `ERROR`: Errors only

## Error Handling

All tools return error information in the response dictionary:
- `error` key contains error type
- `reason` contains human-readable error message
- Tools never raise exceptions, always return dict responses

## Performance

- Set `cache_validations: true` to pre-load the validator at startup
- Set `cache_validations: false` for lazy loading (saves memory if server is idle)
