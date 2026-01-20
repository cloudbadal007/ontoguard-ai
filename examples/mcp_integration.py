"""
OntoGuard MCP Integration Example

This example demonstrates how to use OntoGuard with the Model Context Protocol (MCP)
to validate AI agent actions against an OWL ontology.

The example shows:
1. How an AI agent would interact with OntoGuard through MCP
2. Validation of various actions (allowed, denied, permission-based)
3. Querying allowed actions
4. Getting explanations for denied actions

Usage:
    python examples/mcp_integration.py

Prerequisites:
    - MCP server must be configured (see examples/mcp_config.yaml)
    - Ontology file must exist (examples/ontologies/ecommerce.owl)
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich import box
import time

# Import OntoGuard MCP server tools
# In a real scenario, these would be called via MCP protocol
# For this example, we'll use the implementations directly
from ontoguard.mcp_server import (
    _validate_action_impl as validate_action,
    _get_allowed_actions_impl as get_allowed_actions,
    _check_permissions_impl as check_permissions,
    _explain_rule_impl as explain_rule,
    load_config,
    initialize_validator,
    _config
)

console = Console()


def print_header():
    """Print a nice header for the example."""
    header = """
# OntoGuard MCP Integration Example

This demonstrates how an AI agent would use OntoGuard through MCP
to validate actions against business rules defined in an OWL ontology.
"""
    console.print(Panel(Markdown(header), title="[bold cyan]OntoGuard MCP Demo[/bold cyan]", border_style="cyan"))
    console.print()


def setup_mcp_server():
    """
    Step 1: Setup and initialize the MCP server.
    
    In a real deployment, the MCP server would run as a separate process
    and the agent would connect via MCP protocol. For this example,
    we initialize the server components directly.
    """
    console.print("[bold yellow]Step 1:[/bold yellow] Setting up OntoGuard MCP Server...")
    
    # Load configuration
    config_path = Path(__file__).parent / "mcp_config.yaml"
    if not config_path.exists():
        console.print(f"[red]Error:[/red] Config file not found: {config_path}")
        console.print("Please create examples/mcp_config.yaml")
        sys.exit(1)
    
    try:
        config = load_config(str(config_path))
        _config.clear()
        _config.update(config)
        console.print(f"[green][OK][/green] Configuration loaded from {config_path}")
        
        # Initialize validator
        validator = initialize_validator()
        console.print(f"[green][OK][/green] Ontology loaded: {_config.get('ontology_path')}")
        console.print(f"[green][OK][/green] MCP Server ready")
        console.print()
        
        return True
    except Exception as e:
        console.print(f"[red]Error initializing server:[/red] {e}")
        return False


def simulate_agent_request(action: str, entity: str, entity_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 2: Simulate an AI agent making a request through MCP.
    
    In a real scenario, this would be an MCP tool call:
    {
        "type": "tool",
        "tool": "validate_action",
        "arguments": {
            "action": action,
            "entity": entity,
            "entity_id": entity_id,
            "context": context
        }
    }
    """
    console.print(f"[bold cyan]Agent Request:[/bold cyan]")
    console.print(f"  Action: [yellow]{action}[/yellow]")
    console.print(f"  Entity: [yellow]{entity}[/yellow]")
    console.print(f"  Entity ID: [yellow]{entity_id}[/yellow]")
    console.print(f"  Context: [yellow]{context}[/yellow]")
    console.print()
    
    # Call the MCP tool (validate_action)
    result = validate_action(action, entity, entity_id, context)
    
    return result


def display_validation_result(result: Dict[str, Any]):
    """Display the validation result in a nice format."""
    if result["allowed"]:
        status = "[green][OK] ALLOWED[/green]"
        border_style = "green"
    else:
        status = "[red][X] DENIED[/red]"
        border_style = "red"
    
    panel_content = f"""
[bold]Status:[/bold] {status}

[bold]Reason:[/bold] {result['reason']}
"""
    
    if result.get("suggested_actions"):
        panel_content += f"\n[bold]Suggested Actions:[/bold]\n"
        for action in result["suggested_actions"]:
            panel_content += f"  • {action}\n"
    
    console.print(Panel(panel_content, title="Validation Result", border_style=border_style))
    console.print()


def demonstrate_scenario_1():
    """
    Scenario 1: Agent attempts a valid action.
    
    A Customer tries to create an order - this should be allowed.
    """
    console.print(Panel(
        "[bold]Scenario 1: Valid Action[/bold]\n\n"
        "Agent (Customer) wants to create an order.",
        title="[cyan]Scenario 1[/cyan]",
        border_style="cyan"
    ))
    console.print()
    
    result = simulate_agent_request(
        action="create order",
        entity="Order",
        entity_id="order_001",
        context={"role": "Customer", "user_id": "customer_123"}
    )
    
    display_validation_result(result)
    
    time.sleep(1)


def demonstrate_scenario_2():
    """
    Scenario 2: Agent attempts an invalid action.
    
    A Customer tries to delete a user - this should be denied.
    This demonstrates the conversation flow from the requirements.
    """
    console.print(Panel(
        "[bold]Scenario 2: Invalid Action (Permission Denied)[/bold]\n\n"
        "Agent (Customer) wants to delete a user.\n"
        "This should be blocked because only Admins can delete users.",
        title="[cyan]Scenario 2[/cyan]",
        border_style="cyan"
    ))
    console.print()
    
    # Agent: "I want to delete user_123"
    console.print("[bold magenta]Agent:[/bold magenta] \"I want to delete user_123\"")
    console.print()
    
    result = simulate_agent_request(
        action="delete user",
        entity="User",
        entity_id="user_123",
        context={"role": "Customer", "user_id": "customer_123"}
    )
    
    display_validation_result(result)
    
    # Agent: "What CAN I do with user_123?"
    console.print("[bold magenta]Agent:[/bold magenta] \"What CAN I do with user_123?\"")
    console.print()
    
    # Query allowed actions
    console.print("[bold cyan]Agent Request:[/bold cyan]")
    console.print("  Query: [yellow]get_allowed_actions[/yellow]")
    console.print("  Entity: [yellow]User[/yellow]")
    console.print("  Context: [yellow]{'role': 'Customer'}[/yellow]")
    console.print()
    
    allowed_result = get_allowed_actions(
        entity="User",
        context={"role": "Customer"}
    )
    
    # Display allowed actions
    if allowed_result.get("allowed_actions"):
        table = Table(title="Allowed Actions for User (Customer role)", box=box.ROUNDED)
        table.add_column("Action", style="cyan")
        table.add_column("Description", style="white")
        
        for action in allowed_result["allowed_actions"][:10]:  # Show first 10
            table.add_row(action, "Action available for this entity")
        
        console.print(table)
        console.print(f"[dim]Total: {allowed_result['count']} actions found[/dim]")
    else:
        console.print("[yellow]No specific actions found. The agent may have limited permissions.[/yellow]")
    
    console.print()
    time.sleep(1)


def demonstrate_scenario_3():
    """
    Scenario 3: Action requiring special permissions.
    
    A Customer tries to process a large refund - this requires Manager approval.
    """
    console.print(Panel(
        "[bold]Scenario 3: Action Requiring Special Permissions[/bold]\n\n"
        "Agent (Customer) wants to process a $2000 refund.\n"
        "This should be denied because refunds over $1000 require Manager approval.",
        title="[cyan]Scenario 3[/cyan]",
        border_style="cyan"
    ))
    console.print()
    
    result = simulate_agent_request(
        action="process refund",
        entity="Refund",
        entity_id="refund_001",
        context={
            "role": "Customer",
            "user_id": "customer_123",
            "refund_amount": 2000.0
        }
    )
    
    display_validation_result(result)
    
    # Show what permissions are needed
    console.print("[bold cyan]Checking Required Permissions:[/bold cyan]")
    console.print()
    
    perm_result = check_permissions(
        user_role="Customer",
        action="process refund",
        entity="Refund"
    )
    
    if perm_result.get("required_roles"):
        console.print(f"[yellow]Required Roles:[/yellow] {', '.join(perm_result['required_roles'])}")
    console.print(f"[yellow]Current Role:[/yellow] Customer")
    console.print(f"[yellow]Has Permission:[/yellow] {'Yes' if perm_result['has_permission'] else 'No'}")
    console.print()
    
    time.sleep(1)


def demonstrate_scenario_4():
    """
    Scenario 4: Manager successfully processes refund.
    
    A Manager processes the same refund - this should be allowed.
    """
    console.print(Panel(
        "[bold]Scenario 4: Manager Action (Allowed)[/bold]\n\n"
        "Agent (Manager) processes the same $2000 refund.\n"
        "This should be allowed because Managers have the required permissions.",
        title="[cyan]Scenario 4[/cyan]",
        border_style="cyan"
    ))
    console.print()
    
    result = simulate_agent_request(
        action="process refund",
        entity="Refund",
        entity_id="refund_001",
        context={
            "role": "Manager",
            "user_id": "manager_456",
            "refund_amount": 2000.0
        }
    )
    
    display_validation_result(result)
    
    time.sleep(1)


def demonstrate_rule_explanation():
    """
    Bonus: Explaining a business rule.
    
    The agent asks what a specific rule means.
    """
    console.print(Panel(
        "[bold]Bonus: Rule Explanation[/bold]\n\n"
        "Agent asks: \"What does the DeleteUser rule mean?\"",
        title="[cyan]Rule Explanation[/cyan]",
        border_style="cyan"
    ))
    console.print()
    
    console.print("[bold magenta]Agent:[/bold magenta] \"What does the DeleteUser rule mean?\"")
    console.print()
    
    console.print("[bold cyan]Agent Request:[/bold cyan]")
    console.print("  Query: [yellow]explain_rule[/yellow]")
    console.print("  Rule: [yellow]DeleteUser[/yellow]")
    console.print()
    
    explanation = explain_rule("DeleteUser")
    
    panel_content = f"""
[bold]Rule:[/bold] {explanation['rule_name']}

[bold]Explanation:[/bold]
{explanation['explanation']}

[bold]Found in Ontology:[/bold] {'Yes' if explanation['found'] else 'No'}
"""
    
    console.print(Panel(panel_content, title="Rule Explanation", border_style="blue"))
    console.print()


def print_summary():
    """Print a summary of what was demonstrated."""
    summary = """
## Summary

This example demonstrated:

1. **MCP Server Setup**: How to initialize and configure the OntoGuard MCP server
2. **Action Validation**: How agents validate actions before execution
3. **Permission Checking**: How role-based permissions are enforced
4. **Query Allowed Actions**: How agents discover what they can do
5. **Rule Explanation**: How agents understand business rules

## Key Benefits

- **Prevents Costly Mistakes**: Actions are validated before execution
- **Clear Feedback**: Agents get detailed explanations for denied actions
- **Self-Discovery**: Agents can query what actions are allowed
- **Business Rule Enforcement**: Rules defined in OWL are automatically enforced

## Next Steps

1. Deploy the MCP server as a separate service
2. Connect your AI agent framework to the MCP server
3. Configure your ontology with your business rules
4. Start validating agent actions in production!
"""
    
    console.print(Panel(Markdown(summary), title="[bold green]Summary[/bold green]", border_style="green"))


def main():
    """Main function to run the MCP integration example."""
    print_header()
    
    # Setup MCP server
    if not setup_mcp_server():
        console.print("[red]Failed to setup MCP server. Exiting.[/red]")
        sys.exit(1)
    
    # Demonstrate various scenarios
    console.print(Panel(
        "[bold]Demonstrating AI Agent Interactions with OntoGuard MCP[/bold]",
        border_style="yellow"
    ))
    console.print()
    
    demonstrate_scenario_1()
    demonstrate_scenario_2()
    demonstrate_scenario_3()
    demonstrate_scenario_4()
    demonstrate_rule_explanation()
    
    # Print summary
    print_summary()
    
    console.print("\n[bold green]Example completed successfully![/bold green]\n")


if __name__ == "__main__":
    main()
