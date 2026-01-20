"""
Microsoft AutoGen Integration Example for OntoGuard

This example demonstrates how to integrate OntoGuard with Microsoft AutoGen
multi-agent systems to enforce semantic validation across agent interactions.

The example shows:
1. Creating a validation function for AutoGen agents
2. Using validation before function calls
3. Multi-agent coordination with semantic rules
4. Handling validation results in agent workflows

Usage:
    python examples/integrations/autogen_integration.py

Prerequisites:
    pip install pyautogen
    (Note: This example uses mock responses for demonstration)
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from ontoguard import OntologyValidator

console = Console()

# Try to import AutoGen components
try:
    import autogen
    from autogen import ConversableAgent, GroupChat, GroupChatManager
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    console.print("[yellow]Warning: AutoGen not installed. Using mock implementation.[/yellow]")
    console.print("[dim]Install with: pip install pyautogen[/dim]\n")


def create_validation_function(validator: OntologyValidator):
    """
    Create a validation function for AutoGen agents.
    
    This function can be registered with AutoGen agents to validate
    actions before they are executed.
    """
    
    def validate_action(
        action: str,
        entity: str,
        entity_id: str,
        role: str,
        **context: Any
    ) -> Dict[str, Any]:
        """
        Validate an action using OntoGuard.
        
        Args:
            action: The action to validate
            entity: The entity type
            entity_id: Unique identifier for the entity
            role: User role
            **context: Additional context parameters
        
        Returns:
            Dictionary with validation result
        """
        full_context = {"role": role, **context}
        
        result = validator.validate(
            action=action,
            entity=entity,
            entity_id=entity_id,
            context=full_context
        )
        
        return {
            "allowed": result.allowed,
            "reason": result.reason,
            "suggested_actions": result.suggested_actions,
            "metadata": result.metadata
        }
    
    return validate_action


def demonstrate_autogen_integration():
    """Demonstrate OntoGuard integration with AutoGen."""
    
    console.print(Panel(
        "[bold cyan]AutoGen + OntoGuard Integration[/bold cyan]\n\n"
        "This example shows how to use OntoGuard for semantic validation\n"
        "in Microsoft AutoGen multi-agent systems.",
        title="Integration Example",
        border_style="cyan"
    ))
    console.print()
    
    # Load ontology
    ontology_path = Path(__file__).parent.parent / "ontologies" / "ecommerce.owl"
    if not ontology_path.exists():
        console.print(f"[red]Error:[/red] Ontology not found: {ontology_path}")
        return
    
    console.print("[bold yellow]Step 1:[/bold yellow] Loading OntoGuard validator...")
    validator = OntologyValidator(str(ontology_path))
    console.print(f"[green][OK][/green] Ontology loaded: {ontology_path.name}")
    console.print()
    
    # Create validation function
    console.print("[bold yellow]Step 2:[/bold yellow] Creating validation function...")
    validate_action = create_validation_function(validator)
    console.print("[green][OK][/green] Validation function created")
    console.print()
    
    # Demonstrate validation scenarios
    console.print("[bold yellow]Step 3:[/bold yellow] Testing validation scenarios...")
    console.print()
    
    scenarios = [
        {
            "name": "Customer creates order",
            "action": "create order",
            "entity": "Order",
            "entity_id": "order_001",
            "role": "Customer",
            "agent": "CustomerAgent"
        },
        {
            "name": "Customer deletes user",
            "action": "delete user",
            "entity": "User",
            "entity_id": "user_123",
            "role": "Customer",
            "agent": "CustomerAgent"
        },
        {
            "name": "Admin deletes user",
            "action": "delete user",
            "entity": "User",
            "entity_id": "user_123",
            "role": "Admin",
            "agent": "AdminAgent"
        },
        {
            "name": "Manager processes refund",
            "action": "process refund",
            "entity": "Refund",
            "entity_id": "refund_001",
            "role": "Manager",
            "context": {"refund_amount": 2000.0},
            "agent": "ManagerAgent"
        }
    ]
    
    # Create results table
    table = Table(title="Multi-Agent Validation Results", box=box.ROUNDED)
    table.add_column("Agent", style="cyan", width=15)
    table.add_column("Action", style="yellow", width=20)
    table.add_column("Result", style="green", width=40)
    table.add_column("Status", justify="center")
    
    for scenario in scenarios:
        context = scenario.get("context", {})
        result = validate_action(
            action=scenario["action"],
            entity=scenario["entity"],
            entity_id=scenario["entity_id"],
            role=scenario["role"],
            **context
        )
        
        status = "[green][OK][/green]" if result["allowed"] else "[red][X][/red]"
        reason = result["reason"][:37] + "..." if len(result["reason"]) > 40 else result["reason"]
        
        table.add_row(
            scenario["agent"],
            scenario["action"],
            reason,
            status
        )
    
    console.print(table)
    console.print()
    
    # Show multi-agent coordination example
    console.print("[bold yellow]Step 4:[/bold yellow] Multi-agent coordination example...")
    console.print()
    
    coordination_example = """
# Example: Multi-agent system with OntoGuard validation

import autogen
from autogen import ConversableAgent, GroupChat, GroupChatManager

# Create validation function
validate_action = create_validation_function(validator)

# Define agent functions with validation
def customer_action(action, entity, entity_id):
    result = validate_action(action, entity, entity_id, role="Customer")
    if not result["allowed"]:
        return f"Action denied: {result['reason']}"
    return f"Executing {action} on {entity} {entity_id}"

def admin_action(action, entity, entity_id):
    result = validate_action(action, entity, entity_id, role="Admin")
    if not result["allowed"]:
        return f"Action denied: {result['reason']}"
    return f"Executing {action} on {entity} {entity_id}"

# Create agents
customer_agent = ConversableAgent(
    name="CustomerAgent",
    system_message="You are a customer service agent. Always validate actions.",
    function_map={"customer_action": customer_action}
)

admin_agent = ConversableAgent(
    name="AdminAgent",
    system_message="You are an admin agent. You have elevated permissions.",
    function_map={"admin_action": admin_action}
)

# Create group chat with validation
groupchat = GroupChat(
    agents=[customer_agent, admin_agent],
    messages=[],
    max_round=10
)

manager = GroupChatManager(groupchat=groupchat)

# Agents coordinate with semantic validation
response = manager.initiate_chat(
    customer_agent,
    message="I need to delete user_123. Can you help?"
)
"""
    
    console.print(Panel(coordination_example, title="[dim]Code Example[/dim]", border_style="dim"))
    console.print()
    
    # Show workflow diagram
    console.print("[bold yellow]Step 5:[/bold yellow] Agent workflow with validation...")
    console.print()
    
    workflow = """
    +-------------+
    |   Agent 1   |
    |  (Customer) |
    +------+------+
           | Request: delete user
           v
    +------------------+
    |  OntoGuard       |
    |  Validation      |
    +------+-----------+
           | Result: DENIED
           v
    +-------------+
    |   Agent 2   |
    |   (Admin)   |
    +------+------+
           | Request: delete user
           v
    +------------------+
    |  OntoGuard       |
    |  Validation      |
    +------+-----------+
           | Result: ALLOWED
           v
    +-------------+
    |  Execute    |
    |  Action     |
    +-------------+
    """
    
    console.print(Panel(workflow, title="[dim]Workflow[/dim]", border_style="dim"))
    console.print()
    
    # Summary
    console.print(Panel(
        "[bold]Key Benefits:[/bold]\n\n"
        "• [green]Multi-agent safety[/green] - All agents validate before acting\n"
        "• [green]Role-based coordination[/green] - Agents respect permission boundaries\n"
        "• [green]Semantic consistency[/green] - Business rules enforced across agents\n"
        "• [green]Automatic escalation[/green] - Agents can route to authorized agents\n\n"
        "[bold]Integration Pattern:[/bold]\n"
        "1. Create validation function from OntoGuard\n"
        "2. Register function with AutoGen agents\n"
        "3. Agents call validation before actions\n"
        "4. Validation results guide agent coordination",
        title="[bold green]Summary[/bold green]",
        border_style="green"
    ))


def main():
    """Main function."""
    if not AUTOGEN_AVAILABLE:
        console.print("[yellow]Note: Running in mock mode. Install AutoGen for full functionality.[/yellow]\n")
    
    demonstrate_autogen_integration()


if __name__ == "__main__":
    main()
