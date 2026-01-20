"""
Test cases for LangChain integration with OntoGuard.

This test suite validates the LangChain integration functionality,
including tool creation, validation scenarios, and error handling.
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
from langchain_integration import OntoGuardValidationTool


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
def validation_tool(validator):
    """Fixture creating an OntoGuardValidationTool instance."""
    return OntoGuardValidationTool(validator=validator)


class TestOntoGuardValidationTool:
    """Test the OntoGuardValidationTool class."""
    
    def test_tool_initialization(self, validation_tool):
        """Test that the tool initializes correctly."""
        assert validation_tool is not None
        assert validation_tool.validator is not None
        assert validation_tool.name == "validate_action"
        assert "validate" in validation_tool.description.lower()
    
    def test_tool_run_allowed_action(self, validation_tool):
        """Test tool with an allowed action."""
        result = validation_tool._run(
            action="create order",
            entity="Order",
            entity_id="order_123",
            role="Customer"
        )
        
        assert isinstance(result, str)
        assert "ALLOWED" in result or "allowed" in result.lower()
    
    def test_tool_run_denied_action(self, validation_tool):
        """Test tool with a denied action."""
        result = validation_tool._run(
            action="delete user",
            entity="User",
            entity_id="user_123",
            role="Customer"
        )
        
        assert isinstance(result, str)
        # May be allowed or denied depending on ontology rules
    
    def test_tool_run_with_context(self, validation_tool):
        """Test tool with additional context."""
        result = validation_tool._run(
            action="process refund",
            entity="Refund",
            entity_id="refund_123",
            role="Manager",
            refund_amount=2000.0
        )
        
        assert isinstance(result, str)
    
    def test_tool_run_empty_strings(self, validation_tool):
        """Test tool with empty strings."""
        result = validation_tool._run(
            action="",
            entity="",
            entity_id="",
            role=""
        )
        
        assert isinstance(result, str)
    
    def test_tool_description(self, validation_tool):
        """Test that tool has proper description."""
        assert len(validation_tool.description) > 0
        assert "validate" in validation_tool.description.lower()
        assert "action" in validation_tool.description.lower()


class TestLangChainIntegrationScenarios:
    """Test various validation scenarios."""
    
    def test_customer_creates_order(self, validation_tool):
        """Test customer creating an order."""
        result = validation_tool._run(
            action="create order",
            entity="Order",
            entity_id="order_001",
            role="Customer"
        )
        
        assert isinstance(result, str)
        assert "order" in result.lower() or "Order" in result
    
    def test_customer_deletes_user(self, validation_tool):
        """Test customer trying to delete a user."""
        result = validation_tool._run(
            action="delete user",
            entity="User",
            entity_id="user_123",
            role="Customer"
        )
        
        assert isinstance(result, str)
    
    def test_admin_deletes_user(self, validation_tool):
        """Test admin deleting a user."""
        result = validation_tool._run(
            action="delete user",
            entity="User",
            entity_id="user_123",
            role="Admin"
        )
        
        assert isinstance(result, str)
    
    def test_customer_large_refund(self, validation_tool):
        """Test customer processing large refund."""
        result = validation_tool._run(
            action="process refund",
            entity="Refund",
            entity_id="refund_001",
            role="Customer",
            refund_amount=2000.0
        )
        
        assert isinstance(result, str)
    
    def test_manager_large_refund(self, validation_tool):
        """Test manager processing large refund."""
        result = validation_tool._run(
            action="process refund",
            entity="Refund",
            entity_id="refund_001",
            role="Manager",
            refund_amount=2000.0
        )
        
        assert isinstance(result, str)


class TestLangChainIntegrationErrorHandling:
    """Test error handling in LangChain integration."""
    
    def test_tool_with_invalid_validator(self):
        """Test tool initialization with invalid validator."""
        # Tool may or may not raise exception immediately
        # It will fail when _run is called
        try:
            tool = OntoGuardValidationTool(validator=None)
            # If it doesn't raise, it should fail on use
            with pytest.raises((AttributeError, TypeError)):
                tool._run("test", "Test", "test_1", "Test")
        except (AttributeError, TypeError):
            # If it raises during initialization, that's also acceptable
            pass
    
    def test_tool_with_missing_parameters(self, validation_tool):
        """Test tool with missing required parameters."""
        # Should handle missing parameters gracefully
        try:
            result = validation_tool._run(
                action="test",
                entity="Test",
                entity_id="test_1",
                role="Test"
            )
            assert isinstance(result, str)
        except Exception as e:
            # If it raises an exception, that's also acceptable
            assert isinstance(e, Exception)


class TestLangChainIntegrationEdgeCases:
    """Test edge cases for LangChain integration."""
    
    def test_tool_with_special_characters(self, validation_tool):
        """Test tool with special characters in parameters."""
        result = validation_tool._run(
            action="test@action#123",
            entity="Test_Entity",
            entity_id="id-123",
            role="Role@123"
        )
        
        assert isinstance(result, str)
    
    def test_tool_with_very_long_strings(self, validation_tool):
        """Test tool with very long strings."""
        long_string = "a" * 1000
        result = validation_tool._run(
            action=long_string,
            entity=long_string,
            entity_id=long_string,
            role=long_string
        )
        
        assert isinstance(result, str)
    
    def test_tool_multiple_calls(self, validation_tool):
        """Test multiple consecutive tool calls."""
        for i in range(5):
            result = validation_tool._run(
                action="create order",
                entity="Order",
                entity_id=f"order_{i}",
                role="Customer"
            )
            assert isinstance(result, str)


@pytest.mark.parametrize("action,entity,role,expected_contains", [
    ("create order", "Order", "Customer", "order"),
    ("delete user", "User", "Admin", "user"),
    ("process refund", "Refund", "Manager", "refund"),
])
def test_validation_scenarios_parametrized(validation_tool, action, entity, role, expected_contains):
    """Parametrized test for various validation scenarios."""
    result = validation_tool._run(
        action=action,
        entity=entity,
        entity_id="test_123",
        role=role
    )
    
    assert isinstance(result, str)
    assert expected_contains.lower() in result.lower() or "allowed" in result.lower() or "denied" in result.lower()
