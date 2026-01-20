"""
CrewAI Integration Example for OntoGuard

This example demonstrates how to integrate OntoGuard with CrewAI
to validate tasks and enforce business rules in agent crews.

The example shows:
1. Creating a validation layer for CrewAI tasks
2. Using validation before task assignment
3. Task filtering based on ontology constraints
4. Agent role validation

Usage:
    python examples/integrations/crewai_integration.py

Prerequisites:
    pip install crewai
    (Note: This example uses mock responses for demonstration)
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from ontoguard import OntologyValidator

console = Console()

# Try to import CrewAI components
try:
    from crewai import Agent, Task, Crew
    from crewai.tools import BaseTool
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    console.print("[yellow]Warning: CrewAI not installed. Using mock implementation.[/yellow]")
    console.print("[dim]Install with: pip install crewai[/dim]\n")


class OntoGuardTaskValidator:
    """
    Validator for CrewAI tasks using OntoGuard.
    
    This class validates tasks before they are assigned to agents,
    ensuring they comply with business rules defined in the ontology.
    """
    
    def __init__(self, validator: OntologyValidator):
        """Initialize with an OntologyValidator instance."""
        self.validator = validator
    
    def validate_task(
        self,
        task_description: str,
        agent_role: str,
        entity: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate a task before assignment.
        
        Args:
            task_description: Description of the task (e.g., "delete user", "create order")
            agent_role: Role of the agent (e.g., "Admin", "Customer", "Manager")
            entity: Entity type if applicable
            entity_id: Entity ID if applicable
        
        Returns:
            Validation result dictionary
        """
        # Extract action from task description
        action = self._extract_action(task_description)
        
        if not entity:
            entity = self._infer_entity(task_description)
        
        if not entity_id:
            entity_id = "task_entity"
        
        context = {"role": agent_role}
        
        result = self.validator.validate(
            action=action,
            entity=entity,
            entity_id=entity_id,
            context=context
        )
        
        return {
            "allowed": result.allowed,
            "reason": result.reason,
            "suggested_actions": result.suggested_actions,
            "task": task_description,
            "agent_role": agent_role
        }
    
    def _extract_action(self, description: str) -> str:
        """Extract action from task description."""
        description_lower = description.lower()
        
        # Common action patterns
        if "delete" in description_lower and "user" in description_lower:
            return "delete user"
        elif "create" in description_lower and "order" in description_lower:
            return "create order"
        elif "process" in description_lower and "refund" in description_lower:
            return "process refund"
        elif "cancel" in description_lower and "order" in description_lower:
            return "cancel order"
        elif "modify" in description_lower and "product" in description_lower:
            return "modify product"
        else:
            return description_lower
    
    def _infer_entity(self, description: str) -> str:
        """Infer entity type from task description."""
        description_lower = description.lower()
        
        if "user" in description_lower:
            return "User"
        elif "order" in description_lower:
            return "Order"
        elif "refund" in description_lower:
            return "Refund"
        elif "product" in description_lower:
            return "Product"
        else:
            return "Entity"


def demonstrate_crewai_integration():
    """Demonstrate OntoGuard integration with CrewAI."""
    
    console.print(Panel(
        "[bold cyan]CrewAI + OntoGuard Integration[/bold cyan]\n\n"
        "This example shows how to use OntoGuard for task validation\n"
        "in CrewAI agent crews to ensure compliance with business rules.",
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
    
    # Create task validator
    console.print("[bold yellow]Step 2:[/bold yellow] Creating task validator...")
    task_validator = OntoGuardTaskValidator(validator)
    console.print("[green][OK][/green] Task validator created")
    console.print()
    
    # Define crew tasks
    console.print("[bold yellow]Step 3:[/bold yellow] Validating crew tasks...")
    console.print()
    
    tasks = [
        {
            "description": "Create a new order for customer_123",
            "agent_role": "Customer",
            "entity": "Order"
        },
        {
            "description": "Delete user user_456",
            "agent_role": "Customer",
            "entity": "User"
        },
        {
            "description": "Delete user user_789",
            "agent_role": "Admin",
            "entity": "User"
        },
        {
            "description": "Process refund for order_001 (amount: $2000)",
            "agent_role": "Customer",
            "entity": "Refund",
            "context": {"refund_amount": 2000.0}
        },
        {
            "description": "Process refund for order_002 (amount: $2000)",
            "agent_role": "Manager",
            "entity": "Refund",
            "context": {"refund_amount": 2000.0}
        },
        {
            "description": "Modify product product_123",
            "agent_role": "Customer",
            "entity": "Product"
        },
        {
            "description": "Modify product product_456",
            "agent_role": "Admin",
            "entity": "Product"
        }
    ]
    
    # Create results table
    table = Table(title="Crew Task Validation Results", box=box.ROUNDED)
    table.add_column("Task", style="cyan", width=35)
    table.add_column("Agent Role", style="magenta", width=12)
    table.add_column("Result", style="green", width=35)
    table.add_column("Status", justify="center")
    
    for task in tasks:
        result = task_validator.validate_task(
            task_description=task["description"],
            agent_role=task["agent_role"],
            entity=task.get("entity")
        )
        
        status = "[green][OK][/green]" if result["allowed"] else "[red][X][/red]"
        reason = result["reason"][:32] + "..." if len(result["reason"]) > 35 else result["reason"]
        
        table.add_row(
            task["description"][:34] + "..." if len(task["description"]) > 37 else task["description"],
            task["agent_role"],
            reason,
            status
        )
    
    console.print(table)
    console.print()
    
    # Show crew setup example
    console.print("[bold yellow]Step 4:[/bold yellow] Crew setup example...")
    console.print()
    
    crew_example = """
# Example: CrewAI crew with OntoGuard validation

from crewai import Agent, Task, Crew

# Create task validator
task_validator = OntoGuardTaskValidator(validator)

# Define agents with roles
customer_agent = Agent(
    role="Customer Service Agent",
    goal="Help customers with their orders",
    backstory="You are a helpful customer service agent.",
    verbose=True
)

admin_agent = Agent(
    role="Administrator",
    goal="Manage system users and products",
    backstory="You are a system administrator with full access.",
    verbose=True
)

# Define tasks with validation
def create_validated_task(description, agent, agent_role):
    # Validate task before creating
    validation = task_validator.validate_task(
        task_description=description,
        agent_role=agent_role
    )
    
    if not validation["allowed"]:
        # Task is not allowed - create a modified task or skip
        return None
    
    return Task(
        description=description,
        agent=agent
    )

# Create crew with validated tasks
tasks = [
    create_validated_task("Create order", customer_agent, "Customer"),
    create_validated_task("Delete user", admin_agent, "Admin"),
]

crew = Crew(
    agents=[customer_agent, admin_agent],
    tasks=[t for t in tasks if t is not None],  # Filter out invalid tasks
    verbose=True
)

# Execute crew
result = crew.kickoff()
"""
    
    console.print(Panel(crew_example, title="[dim]Code Example[/dim]", border_style="dim"))
    console.print()
    
    # Show task assignment flow
    console.print("[bold yellow]Step 5:[/bold yellow] Task assignment flow...")
    console.print()
    
    flow = """
    +-----------------+
    |  Task Created   |
    |  "Delete user"  |
    +--------+--------+
             |
             v
    +-----------------+
    |  OntoGuard      |
    |  Validation     |
    +--------+--------+
             |
        +----+----+
        |         |
    [ALLOWED]  [DENIED]
        |         |
        v         v
    +--------+  +--------------+
    | Assign |  | Skip/Modify  |
    |  Task  |  |    Task      |
    +--------+  +--------------+
    """
    
    console.print(Panel(flow, title="[dim]Task Flow[/dim]", border_style="dim"))
    console.print()
    
    # Summary
    console.print(Panel(
        "[bold]Key Benefits:[/bold]\n\n"
        "• [green]Task validation[/green] - Tasks validated before assignment\n"
        "• [green]Role-based filtering[/green] - Only valid tasks assigned to agents\n"
        "• [green]Automatic compliance[/green] - Business rules enforced in crew\n"
        "• [green]Task routing[/green] - Tasks routed to authorized agents\n\n"
        "[bold]Integration Pattern:[/bold]\n"
        "1. Create OntoGuardTaskValidator\n"
        "2. Validate tasks before creating Task objects\n"
        "3. Filter out invalid tasks from crew\n"
        "4. Assign validated tasks to appropriate agents",
        title="[bold green]Summary[/bold green]",
        border_style="green"
    ))


def main():
    """Main function."""
    if not CREWAI_AVAILABLE:
        console.print("[yellow]Note: Running in mock mode. Install CrewAI for full functionality.[/yellow]\n")
    
    demonstrate_crewai_integration()


if __name__ == "__main__":
    main()
