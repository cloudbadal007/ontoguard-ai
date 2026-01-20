"""
MCP Server for OntoGuard - Model Context Protocol integration.

This module provides an MCP server that exposes OntoGuard validation capabilities
as MCP tools, allowing AI agents to validate actions against OWL ontologies
through the Model Context Protocol.

Usage:
    python -m ontoguard.mcp_server
    
    Or configure in MCP client with:
    {
        "mcpServers": {
            "ontoguard": {
                "command": "python",
                "args": ["-m", "ontoguard.mcp_server"],
                "env": {
                    "ONTOGUARD_CONFIG": "path/to/config.yaml"
                }
            }
        }
    }
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

try:
    from fastmcp import FastMCP
except ImportError:
    raise ImportError(
        "fastmcp is required for MCP server. Install with: pip install fastmcp"
    )

try:
    import yaml
except ImportError:
    raise ImportError(
        "PyYAML is required for config loading. Install with: pip install pyyaml"
    )

from ontoguard import OntologyValidator, ValidationResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global validator instance
_validator: Optional[OntologyValidator] = None
_config: Dict[str, Any] = {}


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config.yaml file. If None, checks:
                    1. ONTOGUARD_CONFIG environment variable
                    2. config.yaml in current directory
                    3. examples/config.yaml
    
    Returns:
        Configuration dictionary
    
    Raises:
        FileNotFoundError: If config file is not found
        yaml.YAMLError: If config file is invalid YAML
    """
    if config_path is None:
        # Check environment variable first
        config_path = os.getenv("ONTOGUARD_CONFIG")
        
        # Then check common locations
        if config_path is None or not Path(config_path).exists():
            possible_paths = [
                Path("config.yaml"),
                Path("examples/config.yaml"),
                Path(__file__).parent.parent.parent / "examples" / "config.yaml"
            ]
            
            for path in possible_paths:
                if path.exists():
                    config_path = str(path)
                    break
    
    if config_path is None or not Path(config_path).exists():
        raise FileNotFoundError(
            f"Config file not found. Please create config.yaml or set ONTOGUARD_CONFIG env var."
        )
    
    logger.info(f"Loading configuration from: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if config is None:
            config = {}
        
        logger.info(f"Configuration loaded successfully")
        return config
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML config: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise


def initialize_validator() -> OntologyValidator:
    """
    Initialize the OntologyValidator from configuration.
    
    Returns:
        Initialized OntologyValidator instance
    
    Raises:
        FileNotFoundError: If ontology file is not found
        ValueError: If ontology file cannot be loaded
    """
    global _validator
    
    if _validator is not None:
        return _validator
    
    ontology_path = _config.get("ontology_path")
    if not ontology_path:
        raise ValueError(
            "ontology_path not specified in config.yaml. "
            "Please set ontology_path in your configuration."
        )
    
    ontology_path = Path(ontology_path)
    if not ontology_path.is_absolute():
        # Try relative to config file location
        config_file = Path(_config.get("_config_file", "."))
        ontology_path = config_file.parent / ontology_path
    
    if not ontology_path.exists():
        raise FileNotFoundError(
            f"Ontology file not found: {ontology_path}. "
            "Please check ontology_path in config.yaml"
        )
    
    logger.info(f"Initializing validator with ontology: {ontology_path}")
    
    try:
        _validator = OntologyValidator(str(ontology_path))
        logger.info("Validator initialized successfully")
        return _validator
    except Exception as e:
        logger.error(f"Failed to initialize validator: {e}")
        raise


# Initialize FastMCP server
mcp = FastMCP("OntoGuard")


# Define tool functions (will be decorated)
def _validate_action_impl(
    action: str,
    entity: str,
    entity_id: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validates if an action is semantically allowed by the ontology.
    
    This tool checks whether a proposed action is permitted according to the
    business rules defined in the OWL ontology. It validates:
    - Action existence in the ontology
    - Entity type compatibility
    - Role-based permissions
    - Business rule constraints (amounts, time limits, etc.)
    
    Use this tool before executing any action to ensure compliance with
    your business rules and prevent costly mistakes.
    
    Args:
        action: The action to validate (e.g., "delete user", "process refund")
        entity: The entity type (e.g., "User", "Order", "Refund")
        entity_id: Unique identifier for the specific entity instance
        context: Additional context information as a dictionary. Common keys:
                 - role: User role (e.g., "Admin", "Customer", "Manager")
                 - amount: Transaction amount (for financial rules)
                 - timestamp: Time of action (for temporal constraints)
                 - Any other context relevant to your business rules
    
    Returns:
        Dictionary containing:
        - allowed (bool): Whether the action is allowed
        - reason (str): Human-readable explanation
        - suggested_actions (list): Alternative actions that might be allowed
        - metadata (dict): Additional validation metadata
    
    Example:
        {
            "action": "process refund",
            "entity": "Refund",
            "entity_id": "refund_123",
            "context": {
                "role": "Customer",
                "refund_amount": 2000.0
            }
        }
    """
    logger.info(
        f"Validation request: action='{action}', entity='{entity}', "
        f"entity_id='{entity_id}', context={context}"
    )
    
    try:
        validator = initialize_validator()
        
        # Validate the action
        result: ValidationResult = validator.validate(
            action=action,
            entity=entity,
            entity_id=entity_id,
            context=context
        )
        
        # Convert ValidationResult to dict
        response = {
            "allowed": result.allowed,
            "reason": result.reason,
            "suggested_actions": result.suggested_actions,
            "metadata": result.metadata
        }
        
        log_level = logging.INFO if result.allowed else logging.WARNING
        logger.log(
            log_level,
            f"Validation result: allowed={result.allowed}, reason={result.reason}"
        )
        
        return response
        
    except FileNotFoundError as e:
        error_msg = f"Ontology file not found: {e}"
        logger.error(error_msg)
        return {
            "allowed": False,
            "reason": error_msg,
            "suggested_actions": [],
            "metadata": {"error": "ontology_not_found"}
        }
    except ValueError as e:
        error_msg = f"Invalid configuration: {e}"
        logger.error(error_msg)
        return {
            "allowed": False,
            "reason": error_msg,
            "suggested_actions": [],
            "metadata": {"error": "configuration_error"}
        }
    except Exception as e:
        error_msg = f"Validation error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "allowed": False,
            "reason": error_msg,
            "suggested_actions": [],
            "metadata": {"error": "validation_error", "exception": str(e)}
        }


def _get_allowed_actions_impl(
    entity: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Returns list of actions allowed for this entity and context.
    
    This tool queries the ontology to discover what actions are permitted
    for a given entity type under specific contextual conditions. Use this
    to help AI agents understand what they can do with a particular entity.
    
    Args:
        entity: The entity type to query (e.g., "User", "Order", "Product")
        context: Context information affecting allowed actions. Common keys:
                 - role: User role (e.g., "Admin", "Customer")
                 - Any other context relevant to your business rules
    
    Returns:
        Dictionary containing:
        - allowed_actions (list): List of action names that are allowed
        - entity (str): The entity type that was queried
        - context (dict): The context that was used
        - count (int): Number of allowed actions found
    
    Example:
        {
            "entity": "Order",
            "context": {"role": "Customer"},
            "allowed_actions": ["create order", "cancel order", "view order"],
            "count": 3
        }
    """
    logger.info(f"Querying allowed actions for entity='{entity}', context={context}")
    
    try:
        validator = initialize_validator()
        
        # Get allowed actions
        actions = validator.get_allowed_actions(entity=entity, context=context)
        
        response = {
            "allowed_actions": actions,
            "entity": entity,
            "context": context,
            "count": len(actions)
        }
        
        logger.info(f"Found {len(actions)} allowed actions for entity '{entity}'")
        return response
        
    except RuntimeError as e:
        error_msg = f"Ontology not loaded: {e}"
        logger.error(error_msg)
        return {
            "allowed_actions": [],
            "entity": entity,
            "context": context,
            "count": 0,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Error querying allowed actions: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "allowed_actions": [],
            "entity": entity,
            "context": context,
            "count": 0,
            "error": error_msg
        }


def _explain_rule_impl(rule_name: str) -> Dict[str, Any]:
    """
    Explains what a specific business rule means.
    
    This tool queries the ontology to provide a human-readable explanation
    of a specific business rule, including what it does, when it applies,
    and what constraints it enforces.
    
    Use this tool when you need to understand the meaning and purpose of
    a specific rule in your ontology.
    
    Args:
        rule_name: Name or identifier of the rule to explain. This could be:
                   - An action name (e.g., "DeleteUser", "ProcessRefund")
                   - A constraint name (e.g., "RefundThreshold", "TimeLimit")
                   - A class name (e.g., "User", "Order")
    
    Returns:
        Dictionary containing:
        - rule_name (str): The rule that was queried
        - explanation (str): Human-readable explanation of the rule
        - constraints (list): List of constraints enforced by this rule
        - applies_to (list): Entity types this rule applies to
        - found (bool): Whether the rule was found in the ontology
    
    Example:
        {
            "rule_name": "ProcessRefund",
            "explanation": "Refunds over $1000 require Manager approval...",
            "constraints": ["amount > 1000 requires Manager role"],
            "applies_to": ["Refund"],
            "found": true
        }
    """
    logger.info(f"Explaining rule: {rule_name}")
    
    try:
        validator = initialize_validator()
        
        if validator.graph is None:
            raise RuntimeError("Ontology not loaded")
        
        # Query the ontology for rule information
        # This is a simplified implementation - you may want to enhance
        # this based on your specific ontology structure
        
        explanation_parts = []
        constraints = []
        applies_to = []
        found = False
        
        # Try to find the rule in the ontology
        # Look for classes, properties, or individuals with matching names
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        
        SELECT DISTINCT ?subject ?label ?comment ?type
        WHERE {{
            ?subject rdfs:label ?label .
            FILTER(LCASE(?label) = LCASE("{rule_name}"))
            OPTIONAL {{ ?subject rdfs:comment ?comment }}
            OPTIONAL {{ ?subject rdf:type ?type }}
        }}
        """
        
        try:
            results = validator.graph.query(query)
            for row in results:
                found = True
                if row.comment:
                    explanation_parts.append(str(row.comment))
                if row.label:
                    explanation_parts.append(f"Label: {row.label}")
        except Exception as e:
            logger.debug(f"SPARQL query failed, using fallback: {e}")
        
        # If not found via SPARQL, provide a generic explanation
        if not found:
            explanation_parts.append(
                f"Rule '{rule_name}' was not found in the ontology. "
                "It may be defined with a different name or structure."
            )
        
        explanation = "\n".join(explanation_parts) if explanation_parts else "No explanation available."
        
        response = {
            "rule_name": rule_name,
            "explanation": explanation,
            "constraints": constraints,
            "applies_to": applies_to,
            "found": found
        }
        
        logger.info(f"Rule explanation generated for '{rule_name}' (found: {found})")
        return response
        
    except RuntimeError as e:
        error_msg = f"Ontology not loaded: {e}"
        logger.error(error_msg)
        return {
            "rule_name": rule_name,
            "explanation": error_msg,
            "constraints": [],
            "applies_to": [],
            "found": False,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Error explaining rule: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "rule_name": rule_name,
            "explanation": error_msg,
            "constraints": [],
            "applies_to": [],
            "found": False,
            "error": error_msg
        }


def _check_permissions_impl(
    user_role: str,
    action: str,
    entity: str
) -> Dict[str, Any]:
    """
    Checks if a user role has permission for an action.
    
    This tool specifically checks role-based permissions, determining whether
    a user with a given role is allowed to perform an action on an entity type.
    This is useful for access control checks and permission validation.
    
    Args:
        user_role: The role of the user (e.g., "Admin", "Customer", "Manager")
        action: The action to check (e.g., "delete user", "process refund")
        entity: The entity type (e.g., "User", "Order", "Refund")
    
    Returns:
        Dictionary containing:
        - has_permission (bool): Whether the role has permission
        - role (str): The role that was checked
        - action (str): The action that was checked
        - entity (str): The entity type that was checked
        - reason (str): Explanation of the permission check result
        - required_roles (list): List of roles that are required for this action
    
    Example:
        {
            "has_permission": false,
            "role": "Customer",
            "action": "delete user",
            "entity": "User",
            "reason": "Action requires role 'Admin', but user has role 'Customer'",
            "required_roles": ["Admin"]
        }
    """
    logger.info(
        f"Checking permissions: role='{user_role}', action='{action}', entity='{entity}'"
    )
    
    try:
        validator = initialize_validator()
        
        # Use validation with minimal context to check permissions
        context = {"role": user_role}
        result: ValidationResult = validator.validate(
            action=action,
            entity=entity,
            entity_id="permission_check",
            context=context
        )
        
        # Extract required roles from metadata if available
        required_roles = result.metadata.get("required_roles", [])
        if not required_roles and not result.allowed:
            # Try to infer from the reason
            if "requires role" in result.reason.lower():
                # Extract role from reason (simplified)
                reason_lower = result.reason.lower()
                for role in ["admin", "manager", "customer", "doctor", "nurse"]:
                    if role in reason_lower:
                        required_roles = [role.capitalize()]
                        break
        
        response = {
            "has_permission": result.allowed,
            "role": user_role,
            "action": action,
            "entity": entity,
            "reason": result.reason,
            "required_roles": required_roles
        }
        
        logger.info(
            f"Permission check: role='{user_role}' has permission={result.allowed} "
            f"for action='{action}' on entity='{entity}'"
        )
        
        return response
        
    except Exception as e:
        error_msg = f"Error checking permissions: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "has_permission": False,
            "role": user_role,
            "action": action,
            "entity": entity,
            "reason": error_msg,
            "required_roles": [],
            "error": error_msg
        }


# Export implementations for testing (after all are defined)
validate_action = _validate_action_impl
get_allowed_actions = _get_allowed_actions_impl
explain_rule = _explain_rule_impl
check_permissions = _check_permissions_impl


# Register tools with FastMCP (after implementations are defined)
@mcp.tool()
def validate_action_tool(
    action: str,
    entity: str,
    entity_id: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """MCP tool wrapper for validate_action."""
    return _validate_action_impl(action, entity, entity_id, context)


@mcp.tool()
def get_allowed_actions_tool(
    entity: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """MCP tool wrapper for get_allowed_actions."""
    return _get_allowed_actions_impl(entity, context)


@mcp.tool()
def explain_rule_tool(rule_name: str) -> Dict[str, Any]:
    """MCP tool wrapper for explain_rule."""
    return _explain_rule_impl(rule_name)


@mcp.tool()
def check_permissions_tool(
    user_role: str,
    action: str,
    entity: str
) -> Dict[str, Any]:
    """MCP tool wrapper for check_permissions."""
    return _check_permissions_impl(user_role, action, entity)


def main():
    """Main entry point for the MCP server."""
    global _config
    
    # Load configuration
    try:
        config_path = os.getenv("ONTOGUARD_CONFIG")
        _config = load_config(config_path)
        _config["_config_file"] = config_path or "config.yaml"
        
        # Set log level from config
        log_level = _config.get("log_level", "INFO").upper()
        logging.getLogger().setLevel(getattr(logging, log_level, logging.INFO))
        logger.info(f"Log level set to: {log_level}")
        
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        logger.error("Server will not start without valid configuration.")
        raise
    
    # Pre-initialize validator if cache_validations is enabled
    if _config.get("cache_validations", False):
        try:
            initialize_validator()
            logger.info("Validator pre-initialized (caching enabled)")
        except Exception as e:
            logger.warning(f"Failed to pre-initialize validator: {e}")
    
    # Run the MCP server
    logger.info("Starting OntoGuard MCP Server...")
    mcp.run()


if __name__ == "__main__":
    main()
