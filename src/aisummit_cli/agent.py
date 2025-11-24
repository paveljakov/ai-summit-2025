"""Pydantic AI agent implementation for the AI Summit CLI."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator

from dotenv import load_dotenv
from pydantic_ai import Agent, ModelMessage, RunContext
from langfuse import get_client

from .tools import git_tools, glob_tools, grep_tools, read_tools

# Load environment variables from .env file
load_dotenv()

langfuse = get_client()
Agent.instrument_all()


@dataclass
class AgentDeps:
    """Dependencies available to all agent tools."""

    workspace_root: Path


def create_agent(model: str = "claude-sonnet-4-5-20250929") -> Agent[AgentDeps, str]:
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
        deps_type=AgentDeps,
        output_type=str,
        system_prompt=(
            "You are a presentation assistant for AI Summit 2025 - a live demo CLI tool.\n\n"
            "You are an AI based CLI tool that will be demonstrated during the presentation as an example "
            "of building custom AI CLI by giving you more and more tools to show increase in capabilities. "
            "Progress of demo: no tools -> +simple git tools -> +file search tools\n\n"
            "🎯 PRESENTATION STYLE GUIDELINES:\n"
            "- Think of each response as a PowerPoint slide - concise and visual\n"
            "- Use ASCII graphics, diagrams, and boxes instead of long descriptions\n"
            "- Prefer bullet points and structured layouts over paragraphs\n"
            "- Use emojis sparingly for visual markers (✓, ✗, ➜, 📁, 🔧, etc.)\n"
            "- Keep explanations brief - this is a demo, not documentation\n"
            "- Use box drawing characters (─, │, ┌, ┐, └, ┘, ├, ┤, ┬, ┴, ┼) for visual structure\n\n"
            "📝 OUTPUT FORMAT:\n"
            "- ALWAYS format your responses using Markdown syntax\n"
            "- Use headings (#, ##, ###), code blocks (```), lists (-, *), **bold**, *italic*, etc.\n"
            "- The UI renders markdown, so leverage it for better formatting\n"
            "- Code snippets must use fenced code blocks with language identifiers: ```python, ```bash, etc.\n"
            "- Use tables for structured data when appropriate\n\n"
            "📊 EXAMPLE FORMATS:\n"
            "┌─────────────────────────┐\n"
            "│  Concept Visualization │\n"
            "└─────────────────────────┘\n\n"
            "Component A  ──➜  Component B  ──➜  Output\n\n"
            "    ┌─── Feature 1\n"
            "────┼─── Feature 2\n"
            "    └─── Feature 3\n\n"
            "🛠️  AVAILABLE TOOLS:\n"
            "Git Operations:\n"
            "  • get_git_info - Repository status and branches\n"
            "  • show_git_diff - View changes (working dir OR branch comparisons)\n"
            "  • checkout_branch - Switch branches/tags\n\n"
            "File Operations:\n"
            "  • search_files - Find files (glob patterns: '**/*.py')\n"
            "  • search_content - Search code (regex patterns)\n"
            "  • read_file - Read file contents\n\n"
            "📍 DEMO WORKFLOW (Step-by-Step Branches):\n"
            "This repository uses step branches: step/step-0, step/step-1, step/step-2, etc.\n"
            "Each step demonstrates incremental feature development.\n\n"
            "When user asks to:\n"
            "  • 'Move to step 3' → checkout_branch('step/step-3')\n"
            "  • 'What changed in this step?':\n"
            "    1. get_git_info() to get current branch (e.g., 'step/step-3')\n"
            "    2. Calculate previous: step-3 → step-2\n"
            "    3. show_git_diff(from_ref='step/step-2', to_ref='step/step-3')\n\n"
            "After showing a diff, provide a CONCISE summary (slide format):\n"
            "  ✓ Files changed\n"
            "  ✓ Key features added\n"
            "  ✓ Visual diagram if helpful\n\n"
            "Always use tools when asked about git, files, or code operations."
        ),
        instrument=True
    )

    # Register git tools (async to prevent blocking the event loop)
    @agent.tool
    async def get_git_info(ctx: RunContext[AgentDeps]) -> str:
        """Get comprehensive git repository information including status and branches.

        Use this when the user asks about:
        - Current git status
        - Repository state
        - What files have been modified
        - Current branch information
        - Available branches
        - Uncommitted changes
        - General repository information

        Returns:
            String with git status and branch information
        """
        import asyncio

        # Get status and branches in parallel
        status_task = asyncio.create_task(asyncio.to_thread(git_tools.git_status))
        branches_task = asyncio.create_task(asyncio.to_thread(git_tools.git_branch_list))

        status, branches = await asyncio.gather(status_task, branches_task)

        return f"{status}\n\n{branches}"

    @agent.tool
    async def show_git_diff(
        ctx: RunContext[AgentDeps],
        file_path: str | None = None,
        from_ref: str | None = None,
        to_ref: str | None = None,
    ) -> str:
        """Show git diff - supports working directory changes and branch comparisons.

        Use this when the user asks about:
        - What changes have been made (working directory)
        - Differences between branches (e.g., "compare step-2 and step-3")
        - What was added/changed in a specific step
        - Differences in specific files

        For step comparisons:
        - First use get_git_info to get current branch
        - Calculate previous step (if on step/step-3, previous is step/step-2)
        - Call show_git_diff(from_ref='step/step-2', to_ref='step/step-3')

        Args:
            file_path: Optional specific file to diff
            from_ref: Branch/commit to compare from (e.g., 'step/step-2', 'HEAD~1')
            to_ref: Branch/commit to compare to (default: current HEAD)

        Returns:
            String with diff output

        Examples:
            show_git_diff() -> unstaged working directory changes
            show_git_diff(from_ref='step/step-2', to_ref='step/step-3') -> branch comparison
            show_git_diff(from_ref='step/step-2') -> compare step-2 with current HEAD
        """
        import asyncio
        return await asyncio.to_thread(
            git_tools.git_diff,
            file_path=file_path,
            from_ref=from_ref,
            to_ref=to_ref,
        )

    @agent.tool
    async def checkout_branch(ctx: RunContext[AgentDeps], branch_or_tag: str) -> str:
        """Checkout a git branch or tag to switch to a different version of the code.

        Use this when the user asks to:
        - Switch to a different branch
        - Checkout a tag
        - View code from a different branch

        IMPORTANT: Demo mode - automatically discards any uncommitted changes to allow seamless branch switching.

        Args:
            branch_or_tag: Name of the branch or tag to checkout (e.g., "step-1", "main")

        Returns:
            String with checkout result (includes warning if changes were discarded)
        """
        import asyncio
        return await asyncio.to_thread(git_tools.git_checkout, branch_or_tag)

    @agent.tool
    async def search_files(ctx: RunContext[AgentDeps], pattern: str) -> str:
        """Search for files matching a glob pattern.

        Use this when the user asks to:
        - Find files by name or extension
        - List files in a directory
        - Search for specific file types
        - Locate files matching a pattern

        IMPORTANT - Supported glob patterns:
            * - matches any characters in a filename
            ** - matches directories recursively
            ? - matches a single character
            [abc] - matches any character in brackets

        IMPORTANT - NOT supported:
            {a,b} - brace expansion (shell feature, not available in Python glob)
            For OR patterns, make separate search_files calls instead

        Args:
            pattern: Glob pattern to match files (e.g., "**/*.py", "src/**/*.ts", "*.md")
                    Use ** for recursive search, * for any characters in filename
                    Do NOT use brace expansion like {*.py,*.ts}

        Returns:
            String with formatted list of matching files with metadata (size, modification time)

        Examples:
            - "**/*.py" - All Python files recursively
            - "src/**/*.ts" - TypeScript files in src/ directory
            - "*.md" - Markdown files in current directory
            - "tests/**/test_*.py" - Test files in tests/ directory
        """
        import asyncio

        def _search():
            result = glob_tools.glob_files(pattern, ctx.deps.workspace_root)
            return glob_tools.format_glob_result(result)

        return await asyncio.to_thread(_search)

    @agent.tool
    async def search_content(
        ctx: RunContext[AgentDeps],
        pattern: str,
        path: str | None = None,
        include: str | None = None,
    ) -> str:
        """Search for regular expression patterns within file contents.

        Use this when the user asks to:
        - Find specific functions, classes, or variables in code
        - Locate where certain APIs or patterns are used
        - Search for import statements or dependencies
        - Find configuration values or constants
        - Identify code patterns across multiple files

        Args:
            pattern: Regular expression pattern to search for (case-insensitive)
            path: Optional subdirectory to search in (relative to workspace root)
            include: Optional glob pattern to filter files (e.g., "*.py", "*.{ts,tsx}")

        Returns:
            String with formatted list of matches showing file, line number, and content

        Examples:
            - Find function definitions: pattern="def\\s+\\w+", include="*.py"
            - Find class declarations: pattern="class\\s+\\w+"
            - Find import statements: pattern="from\\s+\\w+\\s+import"
            - Search in specific directory: pattern="TODO", path="src"
            - Filter by file type: pattern="console\\.log", include="*.js"

        Uses a three-tier fallback strategy for best performance:
        git grep (fastest) → system grep → Python implementation (most compatible)
        """
        import asyncio

        def _search():
            result = grep_tools.grep_content(
                pattern=pattern,
                workspace_root=ctx.deps.workspace_root,
                path=path,
                include=include,
            )
            return grep_tools.format_grep_result(result)

        return await asyncio.to_thread(_search)

    @agent.tool
    async def read_file(
        ctx: RunContext[AgentDeps],
        file_path: str,
        offset: int | None = None,
        limit: int | None = None,
    ) -> str:
        """Read and return the complete contents of a specific text file.

        Use this when the user asks to:
        - Read a specific file
        - View the contents of a file
        - Examine implementation details
        - Understand code structure or configuration
        - Analyze file contents after finding it with search_files or search_content

        Features:
        - Pagination support for large files (use offset/limit)
        - Automatic text file detection (rejects binary files)
        - Security validation (files must be within workspace)
        - File size limits (max 50MB by default)

        Args:
            file_path: Relative path from workspace root (e.g., "src/main.py", "README.md")
            offset: Optional 0-based line number to start reading from (requires limit)
            limit: Optional maximum number of lines to read (use with offset for pagination)

        Returns:
            String with file contents and metadata, or error message

        Examples:
            - Read a file: file_path="src/agent.py"
            - Read part of large file: file_path="logs/debug.log", offset=100, limit=50
            - Read config: file_path="pyproject.toml"

        IMPORTANT: Always use relative paths from workspace root, not absolute paths.
        """
        import asyncio

        def _read():
            result = read_tools.read_file(
                file_path=file_path,
                workspace_root=ctx.deps.workspace_root,
                offset=offset,
                limit=limit,
            )
            return read_tools.format_read_result(result, file_path)

        return await asyncio.to_thread(_read)

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
    deps = AgentDeps(workspace_root=Path.cwd())
    result = agent.run_sync(query, deps=deps)
    return result.output


class StreamingResponse:
    """Wrapper for streaming response with history tracking."""

    def __init__(
        self,
        agent,
        query: str,
        deps: AgentDeps,
        message_history: list[ModelMessage] | None = None,
    ):
        """Initialize streaming response.

        Args:
            agent: The Pydantic AI agent
            query: User query
            deps: Agent dependencies (workspace_root, etc.)
            message_history: Optional conversation history
        """
        self.agent = agent
        self.query = query
        self.deps = deps
        self.message_history = message_history
        self._stream_cm = None  # Context manager
        self._response = None  # The actual response object
        self._updated_history: list[ModelMessage] = []

    async def __aenter__(self):
        """Enter async context."""
        # Store the context manager
        self._stream_cm = self.agent.run_stream(
            self.query, deps=self.deps, message_history=self.message_history
        )
        # Enter it and get the response
        self._response = await self._stream_cm.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context and capture history."""
        if self._response:
            # Capture history before exiting
            self._updated_history = self._response.all_messages()

        # Exit the context manager properly
        if self._stream_cm:
            return await self._stream_cm.__aexit__(exc_type, exc_val, exc_tb)

    async def stream_text(self) -> AsyncIterator[str]:
        """Stream text chunks."""
        if self._response:
            async for chunk in self._response.stream_text():
                yield chunk

    def get_history(self) -> list[ModelMessage]:
        """Get updated message history after streaming completes."""
        return self._updated_history


async def run_query_stream(
    query: str,
    model: str = "claude-sonnet-4-5-20250929",
    message_history: list[ModelMessage] | None = None,
) -> StreamingResponse:
    """Stream a query through the agent and maintain conversation history.

    Args:
        query: The user's question or prompt
        model: The model to use (default: claude-sonnet-4-5-20250929)
        message_history: Optional conversation history to maintain context

    Returns:
        StreamingResponse object that can be used as an async context manager
        to stream text and then retrieve updated history

    Example:
        async with await run_query_stream("Hello", history) as stream:
            async for chunk in stream.stream_text():
                print(chunk)
        updated_history = stream.get_history()
    """
    agent = create_agent(model)
    deps = AgentDeps(workspace_root=Path.cwd())
    return StreamingResponse(agent, query, deps, message_history)
