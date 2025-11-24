"""Main entry point for the AI Summit CLI application."""

import argparse
from typing import NoReturn

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .agent import run_query

console = Console()


def main() -> NoReturn:
    """Run the AI Summit CLI application."""
    parser = argparse.ArgumentParser(
        prog="aisummit",
        description="AI Summit 2025 CLI - LLM-powered assistant for code and git operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  aisummit "What is Python?"
  aisummit "Explain git branches"
  aisummit --model claude-sonnet-4-0 "How do LLM agents work?"

Environment Variables:
  ANTHROPIC_API_KEY    Your Anthropic API key (required)
        """,
    )

    parser.add_argument(
        "query",
        type=str,
        help="The question or prompt to send to the AI agent",
    )

    parser.add_argument(
        "--model",
        type=str,
        default="claude-sonnet-4-5-20250929",
        help="The model to use (default: claude-sonnet-4-5-20250929)",
    )

    # Parse arguments
    args = parser.parse_args()

    # Display header
    console.print(Panel.fit(
        "🚀 [bold cyan]AI Summit 2025 CLI[/bold cyan]",
        subtitle=f"[dim]Model: {args.model}[/dim]",
        border_style="cyan",
    ))
    console.print()

    # Display the query
    console.print("[bold yellow]Query:[/bold yellow]", args.query)
    console.print()

    try:
        # Run the agent
        with console.status("[bold green]Thinking...", spinner="dots"):
            response = run_query(args.query, args.model)

        # Display the response
        console.print("[bold green]Response:[/bold green]")
        console.print(Panel(
            Markdown(response),
            border_style="green",
            padding=(1, 2),
        ))
        console.print()

        raise SystemExit(0)

    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        console.print()
        console.print(
            "[yellow]Tip:[/yellow] Set your API key with: "
            "[cyan]export ANTHROPIC_API_KEY='your-api-key'[/cyan]"
        )
        raise SystemExit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise SystemExit(130)

    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}", style="red")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
