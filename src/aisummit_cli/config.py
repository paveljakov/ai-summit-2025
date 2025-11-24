"""Configuration management for the AI Summit CLI."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: Literal["anthropic", "openai"] = "anthropic"
    model: str = Field(default="claude-sonnet-4-5-20250929")
    api_key: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.7


class ToolsConfig(BaseModel):
    """Tools and permissions configuration."""

    enable_git_tools: bool = True
    enable_file_tools: bool = True
    git_read_only: bool = True  # Safety: prevent commits/pushes
    allowed_paths: list[Path] = Field(default_factory=lambda: [Path.cwd()])


class AppConfig(BaseModel):
    """Main application configuration."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    debug: bool = False


def load_config() -> AppConfig:
    """Load configuration from environment or defaults."""
    # TODO: Load from environment variables or config file
    return AppConfig()
