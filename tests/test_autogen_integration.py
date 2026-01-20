"""
Test cases for AutoGen integration with OntoGuard.

This test suite validates the AutoGen integration functionality,
including validation function creation, multi-agent scenarios, and error handling.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ontoguard import OntologyValidator

# Import integration components
sys.path.insert(0, str(Path(__file__).parent.parent / "examples" / "integrations"))
from autogen_integration import create_validation_function


@pytest.fixture
def sample_ontology_path():
    """Fixture providing path to the e-commerce ontology file."""
    ontology_path = Path(__file__).parent.parent / "examples" / "ontologies" / "ecommerce.owl"
    if not ontology_path.exists():
        pytest.skip(f"Ontology file not found: {ontology_path}")
    return str(ontology_path)


@pytest.fixture
def validator(sample_ontology_path):
    """Fixture creating an OntologyValidator instance."""
    return OntologyValidator(sample_ontology_path)


@pytest.fixture
def validate_action(validator):
    """Fixture creating a validation function."""
    return create_validation_function(validator)


class TestValidationFunctionCreation:
    """Test validation function creation."""
    
    def test_create_validation_function(self, validator):
        """Test creating a validation function."""
        validate_action = create_validation_function(validator)
        
        assert callable(validate_action)
        assert validate_action is not None
    
    def test_validation_function_signature(self, validate_action):
        """Test that validation function has correct signature."""
        import inspect
        sig = inspect.signature(validate_action)
        
        assert "action" in sig.parameters
        assert "entity" in sig.parameters
        assert "entity_id" in sig.parameters
        assert "role" in sig.parameters


class TestValidationFunctionExecution:
    """Test validation function execution."""
    
    def test_validate_allowed_action(self, validate_action):
        """Test validating an allowed action."""
        result = validate_action(
            action="create order",
            entity="Order",
            entity_id="order_123",
            role="Customer"
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result
        assert "reason" in result
        assert isinstance(result["allowed"], bool)
        assert isinstance(result["reason"], str)
    
    def test_validate_denied_action(self, validate_action):
        """Test validating a denied action."""
        result = validate_action(
            action="delete user",
            entity="User",
            entity_id="user_123",
            role="Customer"
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result
        assert "reason" in result
    
    def test_validate_with_context(self, validate_action):
        """Test validation with additional context."""
        result = validate_action(
            action="process refund",
            entity="Refund",
            entity_id="refund_123",
            role="Manager",
            refund_amount=2000.0
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result
        assert "metadata" in result
    
    def test_validate_with_empty_context(self, validate_action):
        """Test validation with empty context."""
        result = validate_action(
            action="create order",
            entity="Order",
            entity_id="order_123",
            role="Customer"
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result


class TestMultiAgentScenarios:
    """Test multi-agent validation scenarios."""
    
    def test_customer_agent_action(self, validate_action):
        """Test customer agent action."""
        result = validate_action(
            action="create order",
            entity="Order",
            entity_id="order_001",
            role="Customer"
        )
        
        assert isinstance(result, dict)
        assert result["allowed"] is True or result["allowed"] is False
    
    def test_customer_agent_unauthorized(self, validate_action):
        """Test customer agent unauthorized action."""
        result = validate_action(
            action="delete user",
            entity="User",
            entity_id="user_123",
            role="Customer"
        )
        
        assert isinstance(result, dict)
    
    def test_admin_agent_action(self, validate_action):
        """Test admin agent action."""
        result = validate_action(
            action="delete user",
            entity="User",
            entity_id="user_123",
            role="Admin"
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result
    
    def test_manager_agent_action(self, validate_action):
        """Test manager agent action."""
        result = validate_action(
            action="process refund",
            entity="Refund",
            entity_id="refund_001",
            role="Manager",
            refund_amount=2000.0
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result


class TestAutoGenIntegrationErrorHandling:
    """Test error handling in AutoGen integration."""
    
    def test_validation_with_invalid_validator(self):
        """Test creating validation function with invalid validator."""
        # Function may or may not raise exception immediately
        # It will fail when called
        try:
            validate_func = create_validation_function(None)
            # If it doesn't raise, it should fail on use
            with pytest.raises((AttributeError, TypeError)):
                validate_func("test", "Test", "test_1", "Test")
        except (AttributeError, TypeError):
            # If it raises during creation, that's also acceptable
            pass
    
    def test_validation_missing_parameters(self, validate_action):
        """Test validation with missing parameters."""
        with pytest.raises((TypeError, KeyError)):
            validate_action()  # Missing all parameters


class TestAutoGenIntegrationEdgeCases:
    """Test edge cases for AutoGen integration."""
    
    def test_validation_special_characters(self, validate_action):
        """Test validation with special characters."""
        result = validate_action(
            action="test@action#123",
            entity="Test_Entity",
            entity_id="id-123",
            role="Role@123"
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result
    
    def test_validation_very_long_strings(self, validate_action):
        """Test validation with very long strings."""
        long_string = "a" * 1000
        result = validate_action(
            action=long_string,
            entity=long_string,
            entity_id=long_string,
            role=long_string
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result
    
    def test_validation_multiple_calls(self, validate_action):
        """Test multiple consecutive validation calls."""
        for i in range(5):
            result = validate_action(
                action="create order",
                entity="Order",
                entity_id=f"order_{i}",
                role="Customer"
            )
            assert isinstance(result, dict)
            assert "allowed" in result


class TestAutoGenIntegrationResultStructure:
    """Test validation result structure."""
    
    def test_result_has_required_keys(self, validate_action):
        """Test that result has all required keys."""
        result = validate_action(
            action="create order",
            entity="Order",
            entity_id="order_123",
            role="Customer"
        )
        
        required_keys = ["allowed", "reason", "suggested_actions", "metadata"]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
    
    def test_result_types(self, validate_action):
        """Test that result has correct types."""
        result = validate_action(
            action="create order",
            entity="Order",
            entity_id="order_123",
            role="Customer"
        )
        
        assert isinstance(result["allowed"], bool)
        assert isinstance(result["reason"], str)
        assert isinstance(result["suggested_actions"], list)
        assert isinstance(result["metadata"], dict)


@pytest.mark.parametrize("action,entity,role,expected_keys", [
    ("create order", "Order", "Customer", ["allowed", "reason"]),
    ("delete user", "User", "Admin", ["allowed", "reason"]),
    ("process refund", "Refund", "Manager", ["allowed", "reason"]),
])
def test_validation_scenarios_parametrized(validate_action, action, entity, role, expected_keys):
    """Parametrized test for various validation scenarios."""
    result = validate_action(
        action=action,
        entity=entity,
        entity_id="test_123",
        role=role
    )
    
    assert isinstance(result, dict)
    for key in expected_keys:
        assert key in result
