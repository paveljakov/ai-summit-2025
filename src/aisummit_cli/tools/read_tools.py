"""Read tool for reading individual text files with pagination support."""

import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ReadFileResult:
    """Result of a file read operation."""

    content: str
    encoding: str
    lines_read: Optional[int] = None
    total_lines: Optional[int] = None
    is_truncated: bool = False
    file_size: int = 0
    error: Optional[str] = None


def is_text_file(file_path: Path) -> bool:
    """Check if a file is likely to be a text file.

    Args:
        file_path: Path to the file to check

    Returns:
        True if file appears to be text, False otherwise
    """
    # First check MIME type
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type and mime_type.startswith("text/"):
        return True

    # Try to read a small portion to see if it's text
    try:
        with open(file_path, "r", encoding="utf-8", errors="strict") as f:
            f.read(1024)  # Test read
        return True
    except (UnicodeDecodeError, OSError):
        return False


def validate_path_in_workspace(file_path: Path, workspace_root: Path) -> bool:
    """Validate that a file path is within the workspace.

    Args:
        file_path: The file path to validate
        workspace_root: The workspace root directory

    Returns:
        True if the path is within workspace, False otherwise
    """
    try:
        # Resolve to absolute paths
        abs_file = file_path.resolve()
        abs_workspace = workspace_root.resolve()

        # Check if file is within workspace
        return abs_file.is_relative_to(abs_workspace)
    except (ValueError, OSError):
        return False


def build_secure_path(
    relative_path: str, workspace_root: Path
) -> tuple[Optional[Path], Optional[str]]:
    """Build absolute path from relative path and validate security.

    Args:
        relative_path: Relative path from workspace root
        workspace_root: Workspace root directory

    Returns:
        Tuple of (resolved_path, error_message) - error_message is None if successful
    """
    try:
        # Remove any leading slashes to ensure it's treated as relative
        clean_relative_path = relative_path.lstrip("/")

        # Build absolute path
        absolute_path = workspace_root / clean_relative_path

        # Resolve to handle any .. or . components
        resolved_path = absolute_path.resolve()

        # Security check: ensure resolved path is still within workspace
        try:
            resolved_path.relative_to(workspace_root)
            return resolved_path, None
        except ValueError:
            return (
                None,
                f"Security violation: path '{relative_path}' resolves outside workspace "
                f"(attempted directory traversal)",
            )

    except Exception as e:
        return None, f"Invalid path '{relative_path}': {str(e)}"


def read_file(
    file_path: str,
    workspace_root: Path,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    max_file_size_mb: int = 50,
) -> ReadFileResult:
    """Read a text file with optional pagination.

    Args:
        file_path: Relative path from workspace root (e.g., 'src/main.py')
        workspace_root: Root directory of workspace
        offset: Optional 0-based line number to start reading from
        limit: Optional maximum number of lines to read (requires offset)
        max_file_size_mb: Maximum file size to read in MB

    Returns:
        ReadFileResult with file contents and metadata
    """
    # Validate offset/limit parameters
    if offset is not None:
        if offset < 0:
            return ReadFileResult(
                content="", encoding="utf-8", error="Offset must be a non-negative number"
            )
        if limit is None:
            return ReadFileResult(
                content="",
                encoding="utf-8",
                error="Limit must be provided when offset is specified",
            )

    if limit is not None:
        if limit <= 0:
            return ReadFileResult(
                content="", encoding="utf-8", error="Limit must be a positive number"
            )

    # Build and validate secure path
    resolved_path, path_error = build_secure_path(file_path, workspace_root)
    if path_error:
        return ReadFileResult(content="", encoding="utf-8", error=path_error)

    # Check if file exists
    if not resolved_path.exists():
        return ReadFileResult(
            content="", encoding="utf-8", error=f"File does not exist: {file_path}"
        )

    # Check if it's a file (not directory)
    if not resolved_path.is_file():
        return ReadFileResult(content="", encoding="utf-8", error=f"Path is not a file: {file_path}")

    # Check file size
    max_file_size = max_file_size_mb * 1024 * 1024  # Convert to bytes
    try:
        file_size = resolved_path.stat().st_size
        if file_size > max_file_size:
            size_mb = file_size / (1024 * 1024)
            max_mb = max_file_size / (1024 * 1024)
            return ReadFileResult(
                content="",
                encoding="utf-8",
                error=f"File too large: {size_mb:.1f}MB (max: {max_mb}MB)",
            )
    except OSError as e:
        return ReadFileResult(content="", encoding="utf-8", error=f"Cannot access file: {str(e)}")

    # Check if file is text
    if not is_text_file(resolved_path):
        return ReadFileResult(
            content="",
            encoding="utf-8",
            error=f"File does not appear to be a text file: {file_path}",
        )

    # Read the text file
    try:
        with open(resolved_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total_lines = len(lines)

        # Apply offset and limit if specified
        if offset is not None and limit is not None:
            end_line = offset + limit
            selected_lines = lines[offset:end_line]
            content = "".join(selected_lines)
            lines_read = len(selected_lines)
            is_truncated = end_line < total_lines
        else:
            content = "".join(lines)
            lines_read = total_lines
            is_truncated = False

        return ReadFileResult(
            content=content,
            encoding="utf-8",
            lines_read=lines_read,
            total_lines=total_lines,
            is_truncated=is_truncated,
            file_size=file_size,
        )

    except Exception as e:
        return ReadFileResult(
            content="", encoding="utf-8", error=f"Error reading text file: {str(e)}"
        )


def format_read_result(result: ReadFileResult, file_path: str) -> str:
    """Format read file results as a readable string.

    Args:
        result: The ReadFileResult to format
        file_path: Original file path requested

    Returns:
        Formatted string with file contents or error
    """
    if result.error:
        return f"Read File Error: {result.error}"

    lines = [f"File: {file_path}", ""]

    # Add metadata
    size_kb = result.file_size / 1024
    meta_parts = [f"Size: {size_kb:.1f}KB", f"Encoding: {result.encoding}"]

    if result.lines_read is not None and result.total_lines is not None:
        if result.is_truncated:
            meta_parts.append(f"Lines: {result.lines_read}/{result.total_lines} (truncated)")
        else:
            meta_parts.append(f"Lines: {result.total_lines}")

    lines.append(" | ".join(meta_parts))
    lines.append("")
    lines.append("─" * 80)
    lines.append("")

    # Add content
    lines.append(result.content)

    if result.is_truncated:
        lines.append("")
        lines.append("─" * 80)
        lines.append(
            f"⚠️  Content truncated - showing {result.lines_read} of {result.total_lines} lines"
        )

    return "\n".join(lines)
