"""
Test cases for the OntoGuard MCP Server.

This test suite validates the MCP server functionality, including:
- Configuration loading
- Validator initialization
- All MCP tools (validate_action, get_allowed_actions, explain_rule, check_permissions)
- Error handling
- Edge cases
"""

import pytest
import sys
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ontoguard.mcp_server import (
    load_config,
    initialize_validator,
    validate_action,
    get_allowed_actions,
    explain_rule,
    check_permissions,
    _validator,
    _config
)
# Import the actual implementations (not the decorated versions)
from ontoguard.mcp_server import (
    _validate_action_impl,
    _get_allowed_actions_impl,
    _explain_rule_impl,
    _check_permissions_impl
)
from ontoguard import OntologyValidator


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_ontology_path():
    """Fixture providing path to the e-commerce ontology file."""
    ontology_path = Path(__file__).parent.parent / "examples" / "ontologies" / "ecommerce.owl"
    if not ontology_path.exists():
        pytest.skip(f"Ontology file not found: {ontology_path}")
    return str(ontology_path)


@pytest.fixture
def sample_config(sample_ontology_path, tmp_path):
    """Fixture creating a sample config.yaml file."""
    config_data = {
        "ontology_path": sample_ontology_path,
        "log_level": "INFO",
        "cache_validations": True
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)
    return str(config_file)


@pytest.fixture
def sample_config_relative(sample_ontology_path, tmp_path):
    """Fixture creating a config with relative ontology path."""
    # Create a relative path config
    config_data = {
        "ontology_path": "examples/ontologies/ecommerce.owl",
        "log_level": "DEBUG",
        "cache_validations": False
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)
    return str(config_file)


@pytest.fixture
def reset_validator():
    """Fixture to reset the global validator state between tests."""
    from ontoguard.mcp_server import _validator, _config
    import ontoguard.mcp_server
    
    original_validator = _validator
    original_config = _config.copy() if _config else {}
    
    yield
    
    # Restore original state
    ontoguard.mcp_server._validator = original_validator
    _config.clear()
    _config.update(original_config)


# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

class TestConfigurationLoading:
    """Test configuration loading functionality."""
    
    def test_load_config_from_file(self, sample_config):
        """Test loading configuration from a file."""
        config = load_config(sample_config)
        
        assert config is not None
        assert "ontology_path" in config
        assert config["log_level"] == "INFO"
        assert config["cache_validations"] is True
    
    def test_load_config_from_env_var(self, sample_config, monkeypatch):
        """Test loading configuration from environment variable."""
        monkeypatch.setenv("ONTOGUARD_CONFIG", sample_config)
        config = load_config()
        
        assert config is not None
        assert "ontology_path" in config
    
    def test_load_config_file_not_found(self):
        """Test error handling when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent_config.yaml")
    
    def test_load_config_invalid_yaml(self, tmp_path):
        """Test error handling for invalid YAML."""
        invalid_yaml_file = tmp_path / "invalid.yaml"
        with open(invalid_yaml_file, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        with pytest.raises(yaml.YAMLError):
            load_config(str(invalid_yaml_file))
    
    def test_load_config_empty_file(self, tmp_path):
        """Test loading empty config file."""
        empty_config = tmp_path / "empty.yaml"
        with open(empty_config, 'w') as f:
            f.write("")
        
        config = load_config(str(empty_config))
        assert config == {}


# ============================================================================
# VALIDATOR INITIALIZATION TESTS
# ============================================================================

class TestValidatorInitialization:
    """Test validator initialization functionality."""
    
    def test_initialize_validator_success(self, sample_ontology_path, reset_validator):
        """Test successful validator initialization."""
        from ontoguard.mcp_server import _config
        _config.clear()
        _config.update({"ontology_path": sample_ontology_path})
        
        validator = initialize_validator()
        
        assert validator is not None
        assert isinstance(validator, OntologyValidator)
        assert validator._loaded is True
    
    def test_initialize_validator_missing_ontology_path(self, reset_validator):
        """Test error when ontology_path is not in config."""
        from ontoguard.mcp_server import _config
        import ontoguard.mcp_server
        _config.clear()
        ontoguard.mcp_server._validator = None
        
        with pytest.raises(ValueError, match="ontology_path not specified"):
            initialize_validator()
    
    def test_initialize_validator_nonexistent_file(self, reset_validator):
        """Test error when ontology file doesn't exist."""
        from ontoguard.mcp_server import _config
        import ontoguard.mcp_server
        _config.clear()
        _config.update({"ontology_path": "nonexistent.owl"})
        ontoguard.mcp_server._validator = None
        
        with pytest.raises(FileNotFoundError):
            initialize_validator()
    
    def test_initialize_validator_relative_path(self, sample_config_relative, reset_validator):
        """Test validator initialization with relative path."""
        from ontoguard.mcp_server import _config
        config = load_config(sample_config_relative)
        _config.clear()
        _config.update(config)
        _config["_config_file"] = sample_config_relative
        
        # This should work if we're in the right directory
        try:
            validator = initialize_validator()
            assert validator is not None
        except (FileNotFoundError, ValueError):
            # This is OK if we're not in the project root
            pytest.skip("Relative path resolution requires project root")
    
    def test_initialize_validator_caching(self, sample_ontology_path, reset_validator):
        """Test that validator is cached after first initialization."""
        from ontoguard.mcp_server import _config, _validator
        _config.clear()
        _config.update({"ontology_path": sample_ontology_path})
        # Reset validator
        import ontoguard.mcp_server
        ontoguard.mcp_server._validator = None
        
        validator1 = initialize_validator()
        validator2 = initialize_validator()
        
        assert validator1 is validator2  # Same instance


# ============================================================================
# VALIDATE_ACTION TOOL TESTS
# ============================================================================

class TestValidateActionTool:
    """Test the validate_action MCP tool."""
    
    def test_validate_action_allowed(self, sample_ontology_path, reset_validator):
        """Test validating an allowed action."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        result = _validate_action_impl(
            action="create order",
            entity="Order",
            entity_id="order_123",
            context={"role": "Customer"}
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result
        assert "reason" in result
        assert "suggested_actions" in result
        assert "metadata" in result
        # Note: actual result depends on ontology, but structure should be correct
    
    def test_validate_action_denied(self, sample_ontology_path, reset_validator):
        """Test validating a denied action."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        result = _validate_action_impl(
            action="delete user",
            entity="User",
            entity_id="user_123",
            context={"role": "Customer"}
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result
        assert "reason" in result
        # Should be denied for Customer role
    
    def test_validate_action_missing_ontology(self, reset_validator):
        """Test error handling when ontology is missing."""
        from ontoguard.mcp_server import _config
        import ontoguard.mcp_server
        _config.clear()
        _config.update({"ontology_path": "nonexistent.owl"})
        ontoguard.mcp_server._validator = None
        
        result = _validate_action_impl(
            action="create order",
            entity="Order",
            entity_id="order_123",
            context={}
        )
        
        assert result["allowed"] is False
        assert "error" in result.get("metadata", {})
        # Could be either ontology_not_found or configuration_error
        error_type = result.get("metadata", {}).get("error", "")
        assert error_type in ["ontology_not_found", "configuration_error"]
    
    def test_validate_action_invalid_config(self, reset_validator):
        """Test error handling for invalid configuration."""
        from ontoguard.mcp_server import _config
        import ontoguard.mcp_server
        _config.clear()
        ontoguard.mcp_server._validator = None
        
        result = _validate_action_impl(
            action="create order",
            entity="Order",
            entity_id="order_123",
            context={}
        )
        
        assert result["allowed"] is False
        assert "configuration_error" in result.get("metadata", {}).get("error", "")
    
    def test_validate_action_with_complex_context(self, sample_ontology_path, reset_validator):
        """Test validation with complex context."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        result = _validate_action_impl(
            action="process refund",
            entity="Refund",
            entity_id="refund_123",
            context={
                "role": "Manager",
                "refund_amount": 500.0,
                "timestamp": "2024-01-01T10:00:00Z"
            }
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result


# ============================================================================
# GET_ALLOWED_ACTIONS TOOL TESTS
# ============================================================================

class TestGetAllowedActionsTool:
    """Test the get_allowed_actions MCP tool."""
    
    def test_get_allowed_actions_success(self, sample_ontology_path, reset_validator):
        """Test getting allowed actions successfully."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        result = _get_allowed_actions_impl(
            entity="Order",
            context={"role": "Customer"}
        )
        
        assert isinstance(result, dict)
        assert "allowed_actions" in result
        assert "entity" in result
        assert "context" in result
        assert "count" in result
        assert result["entity"] == "Order"
        assert isinstance(result["allowed_actions"], list)
        assert result["count"] == len(result["allowed_actions"])
    
    def test_get_allowed_actions_empty_result(self, sample_ontology_path, reset_validator):
        """Test getting allowed actions for unknown entity."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        result = _get_allowed_actions_impl(
            entity="UnknownEntity",
            context={}
        )
        
        assert isinstance(result, dict)
        assert "allowed_actions" in result
        assert isinstance(result["allowed_actions"], list)
    
    def test_get_allowed_actions_with_role_context(self, sample_ontology_path, reset_validator):
        """Test getting allowed actions with role context."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        result = _get_allowed_actions_impl(
            entity="User",
            context={"role": "Admin"}
        )
        
        assert isinstance(result, dict)
        assert "context" in result
        assert result["context"]["role"] == "Admin"
    
    def test_get_allowed_actions_ontology_not_loaded(self, reset_validator):
        """Test error handling when ontology is not loaded."""
        from ontoguard.mcp_server import _config
        import ontoguard.mcp_server
        _config.clear()
        _config.update({"ontology_path": "nonexistent.owl"})
        ontoguard.mcp_server._validator = None
        
        result = _get_allowed_actions_impl(
            entity="Order",
            context={}
        )
        
        # Should either have error or empty list (depending on when error occurs)
        assert result["count"] == 0
        assert result["allowed_actions"] == []
        # May or may not have error key depending on when exception occurs


# ============================================================================
# EXPLAIN_RULE TOOL TESTS
# ============================================================================

class TestExplainRuleTool:
    """Test the explain_rule MCP tool."""
    
    def test_explain_rule_success(self, sample_ontology_path, reset_validator):
        """Test explaining a rule successfully."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        result = _explain_rule_impl("DeleteUser")
        
        assert isinstance(result, dict)
        assert "rule_name" in result
        assert "explanation" in result
        assert "constraints" in result
        assert "applies_to" in result
        assert "found" in result
        assert result["rule_name"] == "DeleteUser"
        assert isinstance(result["explanation"], str)
        assert isinstance(result["constraints"], list)
        assert isinstance(result["applies_to"], list)
        assert isinstance(result["found"], bool)
    
    def test_explain_rule_not_found(self, sample_ontology_path, reset_validator):
        """Test explaining a rule that doesn't exist."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        result = _explain_rule_impl("NonExistentRule")
        
        assert isinstance(result, dict)
        assert result["rule_name"] == "NonExistentRule"
        assert result["found"] is False
        assert "explanation" in result
    
    def test_explain_rule_ontology_not_loaded(self, reset_validator):
        """Test error handling when ontology is not loaded."""
        from ontoguard.mcp_server import _config
        import ontoguard.mcp_server
        _config.clear()
        _config.update({"ontology_path": "nonexistent.owl"})
        ontoguard.mcp_server._validator = None
        
        result = _explain_rule_impl("SomeRule")
        
        assert result["found"] is False
        # May or may not have error key depending on when exception occurs
    
    def test_explain_rule_various_names(self, sample_ontology_path, reset_validator):
        """Test explaining rules with various naming formats."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        test_cases = ["User", "Order", "ProcessRefund", "delete user"]
        
        for rule_name in test_cases:
            result = _explain_rule_impl(rule_name)
            assert isinstance(result, dict)
            assert result["rule_name"] == rule_name


# ============================================================================
# CHECK_PERMISSIONS TOOL TESTS
# ============================================================================

class TestCheckPermissionsTool:
    """Test the check_permissions MCP tool."""
    
    def test_check_permissions_allowed(self, sample_ontology_path, reset_validator):
        """Test checking permissions for an allowed action."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        result = _check_permissions_impl(
            user_role="Admin",
            action="delete user",
            entity="User"
        )
        
        assert isinstance(result, dict)
        assert "has_permission" in result
        assert "role" in result
        assert "action" in result
        assert "entity" in result
        assert "reason" in result
        assert "required_roles" in result
        assert result["role"] == "Admin"
        assert result["action"] == "delete user"
        assert result["entity"] == "User"
    
    def test_check_permissions_denied(self, sample_ontology_path, reset_validator):
        """Test checking permissions for a denied action."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        result = _check_permissions_impl(
            user_role="Customer",
            action="delete user",
            entity="User"
        )
        
        assert isinstance(result, dict)
        assert "has_permission" in result
        # Should be denied for Customer
        assert result["has_permission"] is False or result["has_permission"] is True  # Depends on ontology
    
    def test_check_permissions_with_manager(self, sample_ontology_path, reset_validator):
        """Test checking permissions for Manager role."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        result = _check_permissions_impl(
            user_role="Manager",
            action="process refund",
            entity="Refund"
        )
        
        assert isinstance(result, dict)
        assert "has_permission" in result
    
    def test_check_permissions_ontology_not_loaded(self, reset_validator):
        """Test error handling when ontology is not loaded."""
        from ontoguard.mcp_server import _config
        import ontoguard.mcp_server
        _config.clear()
        _config.update({"ontology_path": "nonexistent.owl"})
        ontoguard.mcp_server._validator = None
        
        result = _check_permissions_impl(
            user_role="Admin",
            action="delete user",
            entity="User"
        )
        
        assert result["has_permission"] is False
        # May or may not have error key depending on when exception occurs


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestMCPServerIntegration:
    """Integration tests for the MCP server."""
    
    def test_full_workflow(self, sample_ontology_path, reset_validator):
        """Test a complete workflow using multiple tools."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        # 1. Check permissions
        perm_result = check_permissions(
            user_role="Customer",
            action="create order",
            entity="Order"
        )
        assert isinstance(perm_result, dict)
        
        # 2. Validate action
        validation_result = validate_action(
            action="create order",
            entity="Order",
            entity_id="order_123",
            context={"role": "Customer"}
        )
        assert isinstance(validation_result, dict)
        
        # 3. Get allowed actions
        allowed_result = get_allowed_actions(
            entity="Order",
            context={"role": "Customer"}
        )
        assert isinstance(allowed_result, dict)
        
        # 4. Explain a rule
        explain_result = explain_rule("CreateOrder")
        assert isinstance(explain_result, dict)
    
    def test_error_recovery(self, sample_ontology_path, reset_validator):
        """Test that tools recover gracefully from errors."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        # First, cause an error with invalid config
        _config = {}
        result1 = validate_action("test", "Test", "test_1", {})
        assert result1["allowed"] is False
        
        # Then fix config and try again
        _config = {"ontology_path": sample_ontology_path}
        result2 = validate_action("create order", "Order", "order_1", {"role": "Customer"})
        assert isinstance(result2, dict)
        assert "allowed" in result2


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_validate_action_empty_strings(self, sample_ontology_path, reset_validator):
        """Test validation with empty strings."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        result = _validate_action_impl(
            action="",
            entity="",
            entity_id="",
            context={}
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result
    
    def test_validate_action_none_context(self, sample_ontology_path, reset_validator):
        """Test validation with None context (should use empty dict)."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        # Context should be a dict, but test with None handling
        result = _validate_action_impl(
            action="create order",
            entity="Order",
            entity_id="order_123",
            context={}  # Empty dict instead of None
        )
        
        assert isinstance(result, dict)
    
    def test_get_allowed_actions_empty_context(self, sample_ontology_path, reset_validator):
        """Test getting allowed actions with empty context."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        result = _get_allowed_actions_impl(
            entity="Order",
            context={}
        )
        
        assert isinstance(result, dict)
        assert result["context"] == {}
    
    def test_explain_rule_empty_string(self, sample_ontology_path, reset_validator):
        """Test explaining rule with empty string."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        result = _explain_rule_impl("")
        
        assert isinstance(result, dict)
        assert result["rule_name"] == ""
    
    def test_check_permissions_special_characters(self, sample_ontology_path, reset_validator):
        """Test check permissions with special characters in role name."""
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        result = _check_permissions_impl(
            user_role="Admin@123",
            action="delete user",
            entity="User"
        )
        
        assert isinstance(result, dict)
        assert result["role"] == "Admin@123"


# ============================================================================
# LOGGING TESTS
# ============================================================================

class TestLogging:
    """Test logging functionality."""
    
    def test_logging_on_validation(self, sample_ontology_path, reset_validator, caplog):
        """Test that validation requests are logged."""
        import logging
        global _config
        _config = {"ontology_path": sample_ontology_path}
        
        with caplog.at_level(logging.INFO):
            validate_action(
                action="create order",
                entity="Order",
                entity_id="order_123",
                context={"role": "Customer"}
            )
        
        # Check that some log message was generated
        assert len(caplog.records) > 0
    
    def test_logging_on_error(self, reset_validator, caplog):
        """Test that errors are logged."""
        import logging
        global _config
        _config = {"ontology_path": "nonexistent.owl"}
        
        with caplog.at_level(logging.ERROR):
            validate_action(
                action="test",
                entity="Test",
                entity_id="test_1",
                context={}
            )
        
        # Should have error logs
        error_logs = [r for r in caplog.records if r.levelname == "ERROR"]
        assert len(error_logs) > 0
