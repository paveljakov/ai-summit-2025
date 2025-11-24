"""Main entry point for the AI Summit CLI application."""

import argparse
import os
from typing import NoReturn

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .agent import run_query
from .ui import run_tui

console = Console()


def main() -> NoReturn:
    """Run the AI Summit CLI application."""
    parser = argparse.ArgumentParser(
        prog="aisummit",
        description="AI Summit 2025 CLI - LLM-powered assistant for code and git operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive TUI mode (default)
  aisummit

  # Single query mode
  aisummit "What is Python?"
  aisummit "Explain git branches"
  aisummit --model claude-sonnet-4-0 "How do LLM agents work?"

  # Debug mode - Method 1: Attach to Process (debugpy)
  aisummit --debug

  # Debug mode - Method 2: PyCharm Debug Server (pydevd-pycharm)
  aisummit --pycharm-debug

Environment Variables:
  ANTHROPIC_API_KEY    Your Anthropic API key (required)
        """,
    )

    parser.add_argument(
        "query",
        type=str,
        nargs="?",
        help="The question or prompt to send to the AI agent (optional, launches TUI if omitted)",
    )

    parser.add_argument(
        "--model",
        type=str,
        default="claude-sonnet-4-5-20250929",
        help="The model to use (default: claude-sonnet-4-5-20250929)",
    )

    parser.add_argument(
        "--tui",
        action="store_true",
        help="Force TUI mode (interactive interface)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (starts debugpy server, use with 'Attach to Process')",
    )

    parser.add_argument(
        "--pycharm-debug",
        action="store_true",
        help="Connect to PyCharm debug server (use with 'Python Debug Server' config)",
    )

    parser.add_argument(
        "--debug-port",
        type=int,
        default=5678,
        help="Debug server port (default: 5678)",
    )

    # Parse arguments
    args = parser.parse_args()

    # Enable PyCharm debug server connection if requested
    if args.pycharm_debug:
        try:
            import pydevd_pycharm

            console.print(Panel.fit(
                f"🐛 [bold yellow]PyCharm Debug Mode[/bold yellow]\n\n"
                f"[dim]Connecting to PyCharm debug server on port {args.debug_port}...[/dim]\n\n"
                f"[yellow]Make sure PyCharm debug server is running![/yellow]\n"
                f"In PyCharm: Run → Debug → Python Debug Server",
                border_style="yellow",
            ))

            # Connect to PyCharm's debug server
            pydevd_pycharm.settrace(
                'localhost',
                port=args.debug_port,
                stdout_to_server=True,
                stderr_to_server=True,
                suspend=False
            )
            console.print("[green]✓[/green] Connected to PyCharm debug server!\n")

        except ImportError:
            console.print("[bold red]Error:[/bold red] pydevd-pycharm not installed", style="red")
            console.print("[yellow]Install it with:[/yellow] [cyan]poetry add --group dev pydevd-pycharm[/cyan]")
            raise SystemExit(1)
        except Exception as e:
            console.print(f"[bold red]Failed to connect to PyCharm debug server:[/bold red] {e}", style="red")
            console.print("[yellow]Make sure PyCharm debug server is running on port {args.debug_port}[/yellow]")
            raise SystemExit(1)

    # Enable debug mode if requested
    elif args.debug:
        try:
            import debugpy

            console.print(Panel.fit(
                f"🐛 [bold yellow]Debug Mode Enabled[/bold yellow]\n\n"
                f"[dim]Debugpy server starting on port {args.debug_port}...[/dim]\n\n"
                f"[cyan]In PyCharm:[/cyan]\n"
                f"1. Run → Attach to Process\n"
                f"2. Or configure: Run → Edit Configurations → Python Remote Debug\n"
                f"   - Host: localhost\n"
                f"   - Port: {args.debug_port}",
                border_style="yellow",
            ))

            debugpy.listen(("0.0.0.0", args.debug_port))
            console.print(f"[green]✓[/green] Debug server listening on port {args.debug_port}")
            console.print("[yellow]Waiting for debugger to attach...[/yellow]")
            debugpy.wait_for_client()
            console.print("[green]✓[/green] Debugger attached!\n")

        except ImportError:
            console.print("[bold red]Error:[/bold red] debugpy not installed", style="red")
            console.print("[yellow]Install it with:[/yellow] [cyan]poetry add --group dev debugpy[/cyan]")
            raise SystemExit(1)
        except Exception as e:
            console.print(f"[bold red]Debug setup error:[/bold red] {e}", style="red")
            raise SystemExit(1)

    # Launch TUI if no query provided or --tui flag is set
    if args.tui or args.query is None:
        try:
            run_tui(model=args.model)
            raise SystemExit(0)
        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting...[/yellow]")
            raise SystemExit(0)
        except Exception as e:
            console.print(f"[bold red]TUI Error:[/bold red] {e}", style="red")
            raise SystemExit(1)

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


def dev_main() -> NoReturn:
    """Run the TUI in development mode with textual console connection.

    This uses textual's dev mode which connects to a running textual console.

    Usage:
        Terminal 1: poetry run textual console
        Terminal 2: poetry run aisummit-dev
    """
    # Display instructions
    console.print(Panel.fit(
        "🚀 [bold cyan]AI Summit 2025 CLI - Dev Mode[/bold cyan]\n\n"
        "[dim]Connecting to Textual console...[/dim]",
        border_style="cyan",
    ))
    console.print()
    console.print("[yellow]Tip:[/yellow] Make sure you have [cyan]textual console[/cyan] running in another terminal")
    console.print()

    # Use textual run --dev to launch the app with console connection
    # This replaces the current process with textual run
    try:
        os.execvp("textual", [
            "textual",
            "run",
            "--dev",
            "aisummit_cli.ui.app:AISummitApp"
        ])
    except FileNotFoundError:
        console.print("[bold red]Error:[/bold red] textual command not found", style="red")
        console.print("[yellow]Make sure textual-dev is installed:[/yellow]")
        console.print("  [cyan]poetry add --group dev textual-dev[/cyan]")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
