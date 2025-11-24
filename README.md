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
# Build the container
docker build -t aisummit-cli .

# Run in container
docker run -it aisummit-cli

# Run with API key
docker run -it -e ANTHROPIC_API_KEY=your_key aisummit-cli
```

## 📚 Demo Branch Structure

The repository is organized into incremental branches, each adding new capabilities:

| Branch | Description | Features Added |
|--------|-------------|----------------|
| `step-0` | Initial setup | Poetry config, project structure, Docker |
| `step-1` | Agent foundation | Pydantic AI agent, streaming responses, conversation history |
| `step-2` | Rich TUI | Three-section Textual interface, real-time streaming, markdown rendering |
| `step-3` | Git tools | `git checkout`, `git diff`, `git log`, `git status` |
| `step-4` | File tools | `glob`, `grep`, `read_file`, `list_directory` |
| `step-5` | Final polish | Error handling, Docker optimization, demo scripts |

### Checking Out Demo Steps

```bash
# See current step
git branch

# Jump to a specific step
git checkout step-2

# Run the tool at that step
poetry run aisummit
```

## 🧰 Tools Overview

### Git Tools (step-3)
- `git_checkout(branch)` - Switch between demo branches
- `git_diff(file)` - Show code changes
- `git_log(n)` - View commit history
- `git_status()` - Check working tree

### File Tools (step-4)
- `glob_files(pattern)` - Find files matching patterns
- `grep_content(pattern, path)` - Search file contents
- `read_file(path)` - Display file contents
- `list_directory(path)` - Browse directories

## 🎓 Conference Demo Flow

1. **Introduction** - Show step-0, explain the meta concept
2. **Agent Setup** - Checkout step-1, demonstrate LLM integration with streaming
3. **UI Enhancement** - Checkout step-2, show rich TUI with real-time streaming
4. **Git Tools** - Checkout step-3, use the tool to explore its own git history
5. **File Tools** - Checkout step-4, search and read the tool's own code
6. **Live Coding** - Make a small change and watch the tool discover it

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
