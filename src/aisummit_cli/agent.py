"""Pydantic AI agent implementation for the AI Summit CLI."""

import os

from dotenv import load_dotenv
from pydantic_ai import Agent

# Load environment variables from .env file
load_dotenv()


def create_agent(model: str = "claude-sonnet-4-5-20250929") -> Agent[None, str]:
    """Create and configure the Pydantic AI agent.

    Args:
        model: The model to use (default: claude-sonnet-4-5-20250929)

    Returns:
        Configured Agent instance

    Raises:
        ValueError: If ANTHROPIC_API_KEY environment variable is not set
    """
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is not set. "
            "Please set it in a .env file or as an environment variable:\n"
            "  1. Create a .env file with: ANTHROPIC_API_KEY=your-api-key\n"
            "  2. Or export it: export ANTHROPIC_API_KEY='your-api-key'"
        )

    # Create the agent with system instructions
    agent = Agent(
        f"anthropic:{model}",
        deps_type=None,
        output_type=str,
        system_prompt=(
            "You are a helpful AI assistant for the AI Summit 2025 demo. "
            "You help users understand and work with code, git repositories, "
            "and software development tasks. Be concise and helpful."
        ),
    )

    return agent


def run_query(query: str, model: str = "claude-sonnet-4-5-20250929") -> str:
    """Run a query through the agent and return the response.

    Args:
        query: The user's question or prompt
        model: The model to use (default: claude-sonnet-4-5-20250929)

    Returns:
        The agent's response as a string
    """
    agent = create_agent(model)
    result = agent.run_sync(query)
    return result.output
