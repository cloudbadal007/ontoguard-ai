"""
Test cases for CrewAI integration with OntoGuard.

This test suite validates the CrewAI integration functionality,
including task validation, role-based filtering, and error handling.
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
from crewai_integration import OntoGuardTaskValidator


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
def task_validator(validator):
    """Fixture creating an OntoGuardTaskValidator instance."""
    return OntoGuardTaskValidator(validator)


class TestOntoGuardTaskValidator:
    """Test the OntoGuardTaskValidator class."""
    
    def test_validator_initialization(self, task_validator):
        """Test that the validator initializes correctly."""
        assert task_validator is not None
        assert task_validator.validator is not None
        assert isinstance(task_validator.validator, OntologyValidator)
    
    def test_validate_task_allowed(self, task_validator):
        """Test validating an allowed task."""
        result = task_validator.validate_task(
            task_description="Create a new order",
            agent_role="Customer",
            entity="Order"
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result
        assert "reason" in result
        assert "task" in result
        assert "agent_role" in result
    
    def test_validate_task_denied(self, task_validator):
        """Test validating a denied task."""
        result = task_validator.validate_task(
            task_description="Delete user user_123",
            agent_role="Customer",
            entity="User"
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result
    
    def test_validate_task_with_entity(self, task_validator):
        """Test validating task with explicit entity."""
        result = task_validator.validate_task(
            task_description="Process refund",
            agent_role="Manager",
            entity="Refund"
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result
        assert "reason" in result
        # Entity may be in metadata or inferred from description
    
    def test_validate_task_without_entity(self, task_validator):
        """Test validating task without explicit entity (should infer)."""
        result = task_validator.validate_task(
            task_description="Create a new order for customer",
            agent_role="Customer"
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result


class TestTaskValidationScenarios:
    """Test various task validation scenarios."""
    
    def test_customer_creates_order(self, task_validator):
        """Test customer creating an order."""
        result = task_validator.validate_task(
            task_description="Create a new order for customer_123",
            agent_role="Customer",
            entity="Order"
        )
        
        assert isinstance(result, dict)
        assert result["agent_role"] == "Customer"
        assert "order" in result["task"].lower()
    
    def test_customer_deletes_user(self, task_validator):
        """Test customer trying to delete a user."""
        result = task_validator.validate_task(
            task_description="Delete user user_456",
            agent_role="Customer",
            entity="User"
        )
        
        assert isinstance(result, dict)
        assert result["agent_role"] == "Customer"
    
    def test_admin_deletes_user(self, task_validator):
        """Test admin deleting a user."""
        result = task_validator.validate_task(
            task_description="Delete user user_789",
            agent_role="Admin",
            entity="User"
        )
        
        assert isinstance(result, dict)
        assert result["agent_role"] == "Admin"
    
    def test_manager_processes_refund(self, task_validator):
        """Test manager processing a refund."""
        result = task_validator.validate_task(
            task_description="Process refund for order_001 (amount: $2000)",
            agent_role="Manager",
            entity="Refund"
        )
        
        assert isinstance(result, dict)
        assert result["agent_role"] == "Manager"
    
    def test_customer_modifies_product(self, task_validator):
        """Test customer trying to modify a product."""
        result = task_validator.validate_task(
            task_description="Modify product product_123",
            agent_role="Customer",
            entity="Product"
        )
        
        assert isinstance(result, dict)
        assert result["agent_role"] == "Customer"
    
    def test_admin_modifies_product(self, task_validator):
        """Test admin modifying a product."""
        result = task_validator.validate_task(
            task_description="Modify product product_456",
            agent_role="Admin",
            entity="Product"
        )
        
        assert isinstance(result, dict)
        assert result["agent_role"] == "Admin"


class TestActionExtraction:
    """Test action extraction from task descriptions."""
    
    def test_extract_delete_user_action(self, task_validator):
        """Test extracting delete user action."""
        action = task_validator._extract_action("Delete user user_123")
        assert "delete" in action.lower()
        assert "user" in action.lower()
    
    def test_extract_create_order_action(self, task_validator):
        """Test extracting create order action."""
        action = task_validator._extract_action("Create a new order")
        assert "create" in action.lower()
        assert "order" in action.lower()
    
    def test_extract_process_refund_action(self, task_validator):
        """Test extracting process refund action."""
        action = task_validator._extract_action("Process refund for order")
        assert "process" in action.lower()
        assert "refund" in action.lower()
    
    def test_extract_cancel_order_action(self, task_validator):
        """Test extracting cancel order action."""
        action = task_validator._extract_action("Cancel order order_123")
        assert "cancel" in action.lower()
        assert "order" in action.lower()
    
    def test_extract_modify_product_action(self, task_validator):
        """Test extracting modify product action."""
        action = task_validator._extract_action("Modify product details")
        assert "modify" in action.lower()
        assert "product" in action.lower()


class TestEntityInference:
    """Test entity inference from task descriptions."""
    
    def test_infer_user_entity(self, task_validator):
        """Test inferring User entity."""
        entity = task_validator._infer_entity("Delete user user_123")
        assert entity == "User"
    
    def test_infer_order_entity(self, task_validator):
        """Test inferring Order entity."""
        entity = task_validator._infer_entity("Create a new order")
        assert entity == "Order"
    
    def test_infer_refund_entity(self, task_validator):
        """Test inferring Refund entity."""
        entity = task_validator._infer_entity("Process refund")
        assert entity == "Refund"
    
    def test_infer_product_entity(self, task_validator):
        """Test inferring Product entity."""
        entity = task_validator._infer_entity("Modify product")
        assert entity == "Product"
    
    def test_infer_default_entity(self, task_validator):
        """Test default entity when none can be inferred."""
        entity = task_validator._infer_entity("Some random task")
        assert entity == "Entity"


class TestCrewAIIntegrationErrorHandling:
    """Test error handling in CrewAI integration."""
    
    def test_validator_with_invalid_validator(self):
        """Test validator initialization with invalid validator."""
        # Validator may or may not raise exception immediately
        # It will fail when validate_task is called
        try:
            validator = OntoGuardTaskValidator(validator=None)
            # If it doesn't raise, it should fail on use
            with pytest.raises((AttributeError, TypeError)):
                validator.validate_task("test", "Test")
        except (AttributeError, TypeError):
            # If it raises during initialization, that's also acceptable
            pass
    
    def test_validate_task_missing_parameters(self, task_validator):
        """Test validation with missing parameters."""
        with pytest.raises((TypeError, KeyError)):
            task_validator.validate_task()  # Missing all parameters


class TestCrewAIIntegrationEdgeCases:
    """Test edge cases for CrewAI integration."""
    
    def test_validate_task_empty_description(self, task_validator):
        """Test validation with empty task description."""
        result = task_validator.validate_task(
            task_description="",
            agent_role="Customer"
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result
    
    def test_validate_task_special_characters(self, task_validator):
        """Test validation with special characters."""
        result = task_validator.validate_task(
            task_description="Test@task#123 with_special-chars",
            agent_role="Role@123"
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result
    
    def test_validate_task_very_long_description(self, task_validator):
        """Test validation with very long task description."""
        long_description = "Create order " * 100
        result = task_validator.validate_task(
            task_description=long_description,
            agent_role="Customer"
        )
        
        assert isinstance(result, dict)
        assert "allowed" in result
    
    def test_validate_task_multiple_calls(self, task_validator):
        """Test multiple consecutive task validations."""
        for i in range(5):
            result = task_validator.validate_task(
                task_description=f"Create order {i}",
                agent_role="Customer",
                entity="Order"
            )
            assert isinstance(result, dict)
            assert "allowed" in result


class TestCrewAIIntegrationResultStructure:
    """Test validation result structure."""
    
    def test_result_has_required_keys(self, task_validator):
        """Test that result has all required keys."""
        result = task_validator.validate_task(
            task_description="Create order",
            agent_role="Customer",
            entity="Order"
        )
        
        required_keys = ["allowed", "reason", "suggested_actions", "task", "agent_role"]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
    
    def test_result_types(self, task_validator):
        """Test that result has correct types."""
        result = task_validator.validate_task(
            task_description="Create order",
            agent_role="Customer",
            entity="Order"
        )
        
        assert isinstance(result["allowed"], bool)
        assert isinstance(result["reason"], str)
        assert isinstance(result["suggested_actions"], list)
        assert isinstance(result["task"], str)
        assert isinstance(result["agent_role"], str)


@pytest.mark.parametrize("description,role,entity,expected_keys", [
    ("Create a new order", "Customer", "Order", ["allowed", "reason", "task"]),
    ("Delete user user_123", "Admin", "User", ["allowed", "reason", "task"]),
    ("Process refund", "Manager", "Refund", ["allowed", "reason", "task"]),
])
def test_task_validation_scenarios_parametrized(task_validator, description, role, entity, expected_keys):
    """Parametrized test for various task validation scenarios."""
    result = task_validator.validate_task(
        task_description=description,
        agent_role=role,
        entity=entity
    )
    
    assert isinstance(result, dict)
    for key in expected_keys:
        assert key in result
