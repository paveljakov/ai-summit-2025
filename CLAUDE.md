# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **meta-demonstration project** for AI Summit 2025: an LLM-powered CLI tool that helps present a talk about building LLM CLI tools. The application demonstrates itself being built through incremental git branches, where each branch adds new capabilities.

**Key Concept**: During the demo, this tool will be used to explore and explain its own codebase, performing operations like git checkout, diff, file search, and content search to show how LLM CLI agents work.

## Tech Stack

- **Python 3.13**: Latest Python with modern features
- **Poetry**: Dependency management and packaging
- **Pydantic AI**: LLM interaction and agent framework with tool definitions
- **Textual + Rich**: Terminal UI (TUI) and rich text formatting
- **Docker**: Sandboxed execution environment for security

## Development Commands

### Initial Setup
```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run the CLI tool
poetry run python -m aisummit_cli
```

### Development Workflow
```bash
# Add dependencies
poetry add <package>
poetry add --group dev <dev-package>

# Run tests (when implemented)
poetry run pytest

# Format code (if using)
poetry run black .
poetry run ruff check .

# Type checking (if using)
poetry run mypy .
```

### Docker Usage
```bash
# Build container
docker build -t aisummit-cli .

# Run in sandboxed environment
docker run -it aisummit-cli

# Run with mounted code (for development)
docker run -it -v $(pwd):/app aisummit-cli
```

## Architecture

### Core Components

1. **Agent Loop** (`agent.py` or `main.py`)
   - Initialize Pydantic AI agent with configured LLM
   - Main interaction loop handling user input and agent responses
   - Tool execution and result handling

2. **Tools Module** (`tools/`)
   - `git_tools.py`: Git operations (checkout, diff, log, status)
   - `file_tools.py`: File system operations (glob, grep, read)
   - Each tool is a Pydantic AI tool function with proper type hints and documentation

3. **UI Layer** (`ui/` or `tui/`)
   - Textual-based TUI components
   - Rich formatting for displaying:
     - Agent reasoning/thinking
     - Tool execution results
     - Code diffs with syntax highlighting
     - File trees and search results

4. **Configuration** (`config.py`)
   - LLM provider settings (API keys, model selection)
   - Tool permissions and safety constraints
   - Docker/sandbox configuration

### Tool Implementation Pattern

Each tool should follow this pattern with Pydantic AI:
```python
from pydantic_ai import Agent, RunContext

@agent.tool
def tool_name(ctx: RunContext, param: str) -> str:
    """Clear description for the LLM to understand when to use this tool.

    Args:
        ctx: Pydantic AI context
        param: Description of parameter

    Returns:
        Description of return value
    """
    # Tool implementation
    return result
```

### Git Tools to Implement
- `git_checkout(branch: str)`: Switch branches for demo progression
- `git_diff(file: str | None)`: Show changes between branches
- `git_log(n: int)`: Show recent commits
- `git_status()`: Show working tree status

### File Tools to Implement
- `glob_files(pattern: str)`: Find files matching pattern (e.g., "**/*.py")
- `grep_content(pattern: str, path: str)`: Search file contents with regex
- `read_file(path: str)`: Read and display file contents
- `list_directory(path: str)`: List directory contents

## Demo Branch Structure

The repository uses branches to demonstrate incremental development:

- `main` or `step-0`: Empty project setup with Poetry and basic structure
- `step-1`: Basic agent loop with LLM integration, streaming responses, conversation history
- `step-2`: Add Textual TUI with Rich formatting, three-section layout, real-time streaming
- `step-3`: Add git tools (checkout, diff, log, status)
- `step-4`: Add file search tools (glob, grep, read, list)
- `step-5`: Final polish with Docker containerization

During the demo, the tool can checkout these branches to show its own evolution.

## Safety Considerations

- All operations run in Docker container with limited permissions
- Git operations are read-only during demo (checkout/diff only, no commits/pushes)
- File operations restricted to repository directory only
- No system commands or shell access exposed to LLM

## Key Design Principles

1. **Self-demonstrating**: The tool must be able to explore and explain its own codebase
2. **Incremental**: Each branch should be a working version with added functionality
3. **Clear tool boundaries**: Each tool has a single, well-defined purpose
4. **Observable**: Show LLM reasoning and tool calls in the UI
5. **Safe**: All operations are sandboxed and auditable
