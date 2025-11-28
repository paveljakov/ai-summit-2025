# AI Summit 2025 CLI Demo

A meta-demonstration project for AI Summit 2025: an LLM-powered CLI tool that helps present a talk about building LLM CLI applications.

## 🎯 The Meta Concept

This project demonstrates **itself being built**. During the presentation:
- The CLI tool explores its own codebase
- It performs git operations to show incremental development
- It explains its own architecture and implementation
- Each git branch represents a step in building the tool

Think of it as: *"Using an LLM CLI to demonstrate how to build an LLM CLI"* 🤯

## 🛠️ Tech Stack

- **Python 3.13** - Latest Python with modern features
- **Poetry** - Dependency management and packaging
- **Pydantic AI** - LLM interaction and agent framework with tools
- **Textual + Rich** - Terminal UI and rich text formatting
- **Docker** - Sandboxed execution environment

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Poetry 1.8+
- Docker (optional, for sandboxed execution)

### Installation

```bash
# Install dependencies
poetry install

# Run the CLI
poetry run aisummit

# Or use the shorter command
poetry run python -m aisummit_cli
```

### Docker Usage

```bash
# Build the image
docker compose build

# Run interactive demo shell (recommended)
docker compose run demo
# Inside: aisummit, git, java, mvn available system-wide

# Run single query
docker compose run cli "your query here"

# Development mode with live code mounting
docker compose run cli-dev
```

**Note**: Create a `.env` file with your `ANTHROPIC_API_KEY` before running.

## 📚 Demo Branch Structure

The repository is organized into incremental branches, each adding new capabilities:

| Branch | Description | Features Added |
|--------|-------------|----------------|
| `step/step-0` | Initial setup | Poetry config, project structure, Docker |
| `step/step-1` | Agent foundation | Pydantic AI agent, streaming responses, conversation history |
| `step/step-2` | Rich TUI | Three-section Textual interface, real-time streaming, markdown rendering |
| `step/step-3` | Git tools | `git_status`, `git_branch_list`, `git_log`, `git_diff`, `git_checkout` |
| `step/step-4` | File tools | `glob_files`, `grep_content`, `read_file` |
| `step/step-5` | Edit tools | `replace_text` for file editing |

### Checking Out Demo Steps

```bash
# See current step
git branch

# Jump to a specific step
git checkout step/step-2

# Run the tool at that step
poetry run aisummit
```

## 🧰 Tools Overview

### Git Tools (step/step-3)
- `git_status()` - Check working tree status
- `git_branch_list()` - List all branches
- `git_log(count, oneline)` - View commit history
- `git_diff(file, compare_to)` - Show code changes
- `git_checkout(branch_or_tag)` - Switch between branches

### File Tools (step/step-4)
- `glob_files(pattern)` - Find files matching patterns
- `grep_content(pattern, path)` - Search file contents with regex
- `read_file(path, start_line, end_line)` - Display file contents

### Edit Tools (step/step-5)
- `replace_text(file_path, old_string, new_string)` - Edit files with string replacement

## 🎓 Conference Demo Flow

1. **Introduction** - Show step/step-0, explain the meta concept
2. **Agent Setup** - Checkout step/step-1, demonstrate LLM integration with streaming
3. **UI Enhancement** - Checkout step/step-2, show rich TUI with real-time streaming
4. **Git Tools** - Checkout step/step-3, use the tool to explore its own git history
5. **File Tools** - Checkout step/step-4, search and read the tool's own code
6. **Edit Tools** - Checkout step/step-5, make changes with replace_text tool

## 🔒 Safety & Sandboxing

- All operations run in Docker with limited permissions
- Git operations are read-only (no commits/pushes during demo)
- File operations restricted to repository directory
- No system shell access exposed to the LLM

## 📖 Documentation

See [CLAUDE.md](CLAUDE.md) for detailed architecture and development guidance.

## 🤝 Contributing

This is a conference demo project. Feel free to:
- Fork and adapt for your own presentations
- Suggest improvements via issues
- Share your own LLM CLI implementations

## 📝 License

MIT License - See LICENSE file for details

---

**Built for AI Summit 2025** | *Where the demo demonstrates itself* ✨
