"""
LangChain Integration Example for OntoGuard

This example demonstrates how to integrate OntoGuard with LangChain agents
to validate actions against OWL ontologies before execution.

The example shows:
1. Creating a custom LangChain tool that wraps OntoGuard validation
2. Using the tool in a LangChain agent
3. The agent checking permissions before taking actions
4. Handling both allowed and denied actions

Usage:
    python examples/integrations/langchain_integration.py

Prerequisites:
    pip install langchain langchain-openai langchain-community
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

# Try to import LangChain components
try:
    from langchain.tools import BaseTool
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import HumanMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    console.print("[yellow]Warning: LangChain not installed. Using mock implementation.[/yellow]")
    console.print("[dim]Install with: pip install langchain langchain-openai langchain-community[/dim]\n")


class OntoGuardValidationTool(BaseTool if LANGCHAIN_AVAILABLE else object):
    """
    LangChain tool that wraps OntoGuard validation.
    
    This tool allows LangChain agents to validate actions against
    an OWL ontology before executing them.
    """
    
    name: str = "validate_action"
    description: str = (
        "Validates if an action is allowed according to business rules. "
        "Use this before executing any action to ensure compliance. "
        "Input should be: action, entity, entity_id, and context (including user role)."
    )
    
    def __init__(self, validator: OntologyValidator, **kwargs):
        """Initialize the tool with an OntologyValidator instance."""
        if LANGCHAIN_AVAILABLE:
            super().__init__(**kwargs)
        self.validator = validator
    
    def _run(
        self,
        action: str,
        entity: str,
        entity_id: str,
        role: str,
        **kwargs: Any
    ) -> str:
        """
        Execute the validation tool.
        
        Args:
            action: The action to validate (e.g., "delete user", "create order")
            entity: The entity type (e.g., "User", "Order")
            entity_id: Unique identifier for the entity
            role: User role (e.g., "Admin", "Customer", "Manager")
            **kwargs: Additional context parameters
        
        Returns:
            Human-readable validation result
        """
        context = {"role": role, **kwargs}
        
        result = self.validator.validate(
            action=action,
            entity=entity,
            entity_id=entity_id,
            context=context
        )
        
        if result.allowed:
            return f"✓ ALLOWED: {result.reason}"
        else:
            suggestions = ""
            if result.suggested_actions:
                suggestions = f"\nSuggested alternatives: {', '.join(result.suggested_actions[:3])}"
            return f"✗ DENIED: {result.reason}{suggestions}"
    
    async def _arun(
        self,
        action: str,
        entity: str,
        entity_id: str,
        role: str,
        **kwargs: Any
    ) -> str:
        """Async version of _run."""
        return self._run(action, entity, entity_id, role, **kwargs)


def demonstrate_langchain_integration():
    """Demonstrate OntoGuard integration with LangChain."""
    
    console.print(Panel(
        "[bold cyan]LangChain + OntoGuard Integration[/bold cyan]\n\n"
        "This example shows how to use OntoGuard as a validation tool\n"
        "in LangChain agents to prevent unauthorized actions.",
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
    
    # Create the validation tool
    console.print("[bold yellow]Step 2:[/bold yellow] Creating LangChain tool...")
    validation_tool = OntoGuardValidationTool(validator=validator)
    console.print(f"[green][OK][/green] Tool created: {validation_tool.name}")
    console.print(f"[dim]Description: {validation_tool.description}[/dim]")
    console.print()
    
    # Demonstrate validation scenarios
    console.print("[bold yellow]Step 3:[/bold yellow] Demonstrating validation scenarios...")
    console.print()
    
    scenarios = [
        {
            "name": "Customer tries to create order",
            "action": "create order",
            "entity": "Order",
            "entity_id": "order_001",
            "role": "Customer",
            "expected": "ALLOWED"
        },
        {
            "name": "Customer tries to delete user",
            "action": "delete user",
            "entity": "User",
            "entity_id": "user_123",
            "role": "Customer",
            "expected": "DENIED"
        },
        {
            "name": "Admin tries to delete user",
            "action": "delete user",
            "entity": "User",
            "entity_id": "user_123",
            "role": "Admin",
            "expected": "ALLOWED"
        },
        {
            "name": "Customer processes large refund",
            "action": "process refund",
            "entity": "Refund",
            "entity_id": "refund_001",
            "role": "Customer",
            "context": {"refund_amount": 2000.0},
            "expected": "DENIED"
        },
        {
            "name": "Manager processes large refund",
            "action": "process refund",
            "entity": "Refund",
            "entity_id": "refund_001",
            "role": "Manager",
            "context": {"refund_amount": 2000.0},
            "expected": "ALLOWED"
        }
    ]
    
    # Create results table
    table = Table(title="Validation Results", box=box.ROUNDED)
    table.add_column("Scenario", style="cyan", width=30)
    table.add_column("Action", style="yellow")
    table.add_column("Role", style="magenta")
    table.add_column("Result", style="green")
    table.add_column("Status", justify="center")
    
    for scenario in scenarios:
        context = scenario.get("context", {})
        result = validation_tool._run(
            action=scenario["action"],
            entity=scenario["entity"],
            entity_id=scenario["entity_id"],
            role=scenario["role"],
            **context
        )
        
        is_allowed = "✓ ALLOWED" in result
        status = "[green][OK][/green]" if is_allowed else "[red][X][/red]"
        expected_match = scenario["expected"] in result
        
        table.add_row(
            scenario["name"],
            scenario["action"],
            scenario["role"],
            result.split(":")[1].strip() if ":" in result else result,
            status if expected_match else "[yellow]?[/yellow]"
        )
    
    console.print(table)
    console.print()
    
    # Show how it would be used in an agent
    console.print("[bold yellow]Step 4:[/bold yellow] Agent usage example...")
    console.print()
    
    agent_example = """
# Example: Using OntoGuard in a LangChain agent

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# Create agent with validation tool
tools = [validation_tool]
llm = ChatOpenAI(model="gpt-4", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Always validate actions using validate_action tool before executing them."),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Agent will now validate actions before executing
response = agent_executor.invoke({
    "input": "I want to delete user_123. Can I do that?"
})
"""
    
    console.print(Panel(agent_example, title="[dim]Code Example[/dim]", border_style="dim"))
    console.print()
    
    # Summary
    console.print(Panel(
        "[bold]Key Benefits:[/bold]\n\n"
        "• [green]Prevents unauthorized actions[/green] - Agent validates before acting\n"
        "• [green]Automatic compliance[/green] - Business rules enforced automatically\n"
        "• [green]Clear feedback[/green] - Agent gets detailed denial explanations\n"
        "• [green]Self-healing[/green] - Agent can query allowed actions\n\n"
        "[bold]Integration Pattern:[/bold]\n"
        "1. Wrap OntoGuard as a LangChain tool\n"
        "2. Add tool to agent's tool list\n"
        "3. Agent automatically uses tool before actions\n"
        "4. Validation results guide agent behavior",
        title="[bold green]Summary[/bold green]",
        border_style="green"
    ))


def main():
    """Main function."""
    if not LANGCHAIN_AVAILABLE:
        console.print("[yellow]Note: Running in mock mode. Install LangChain for full functionality.[/yellow]\n")
    
    demonstrate_langchain_integration()


if __name__ == "__main__":
    main()
