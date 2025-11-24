"""Glob tool for finding files by pattern."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional


@dataclass
class FileMetadata:
    """Metadata for a file found by glob search."""

    path: str
    size: int
    mtime: datetime
    is_recent: bool


@dataclass
class GlobResult:
    """Result of a glob search operation."""

    pattern: str
    files: list[FileMetadata]
    total_count: int


def validate_glob_pattern(pattern: str) -> tuple[bool, str]:
    """Validate a glob pattern for security and correctness.

    Args:
        pattern: The glob pattern to validate

    Returns:
        Tuple of (is_valid, error_message). error_message is empty if valid.
    """
    if not pattern or not pattern.strip():
        return False, "Pattern cannot be empty"

    # Security: prevent path traversal
    if ".." in pattern:
        return False, "Pattern cannot contain '..' (path traversal)"

    # Security: must be relative pattern
    if pattern.startswith("/"):
        return False, "Pattern must be relative (cannot start with '/')"

    return True, ""


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


def glob_files(pattern: str, workspace_root: Path) -> GlobResult:
    """Search for files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g., "**/*.py", "src/**/*.ts")
        workspace_root: Root directory to search from

    Returns:
        GlobResult with matching files and metadata
    """
    # Validate pattern
    is_valid, error = validate_glob_pattern(pattern)
    if not is_valid:
        raise ValueError(f"Invalid glob pattern: {error}")

    # Perform glob search
    matching_paths = list(workspace_root.glob(pattern))

    # Filter to files only (exclude directories)
    file_paths = [p for p in matching_paths if p.is_file()]

    # Collect metadata
    now = datetime.now(timezone.utc)
    recent_threshold = now - timedelta(days=7)

    file_metadata: list[FileMetadata] = []

    for file_path in file_paths:
        # Security check: ensure file is within workspace
        if not validate_path_in_workspace(file_path, workspace_root):
            continue

        try:
            stat = file_path.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

            # Make path relative to workspace
            try:
                relative_path = file_path.relative_to(workspace_root)
            except ValueError:
                # Skip files that aren't relative to workspace
                continue

            file_metadata.append(
                FileMetadata(
                    path=str(relative_path),
                    size=stat.st_size,
                    mtime=mtime,
                    is_recent=mtime > recent_threshold,
                )
            )
        except (OSError, PermissionError):
            # Skip files we can't access
            continue

    # Smart sorting: recent files first, then alphabetical
    file_metadata.sort(key=lambda f: (not f.is_recent, f.path))

    return GlobResult(
        pattern=pattern,
        files=file_metadata,
        total_count=len(file_metadata),
    )


def format_glob_result(result: GlobResult) -> str:
    """Format glob search results as a readable string.

    Args:
        result: The GlobResult to format

    Returns:
        Formatted string with file list and metadata
    """
    lines = [f"Glob Search: {result.pattern}", ""]

    if result.total_count == 0:
        lines.append("No files found matching pattern.")
        return "\n".join(lines)

    lines.append(f"Found {result.total_count} file{'s' if result.total_count != 1 else ''}:")
    lines.append("")

    # Group by recent/not recent
    recent_files = [f for f in result.files if f.is_recent]
    older_files = [f for f in result.files if not f.is_recent]

    if recent_files:
        lines.append("📌 Recent files (modified within 7 days):")
        for file in recent_files:
            size_kb = file.size / 1024
            time_ago = _format_time_ago(file.mtime)
            lines.append(f"  {file.path} ({size_kb:.1f}KB, {time_ago})")
        lines.append("")

    if older_files:
        if recent_files:
            lines.append("📁 Older files:")
        for file in older_files:
            size_kb = file.size / 1024
            time_ago = _format_time_ago(file.mtime)
            lines.append(f"  {file.path} ({size_kb:.1f}KB, {time_ago})")

    return "\n".join(lines)


def _format_time_ago(dt: datetime) -> str:
    """Format a datetime as a human-readable 'time ago' string.

    Args:
        dt: The datetime to format

    Returns:
        Human-readable time difference (e.g., "2 hours ago", "3 days ago")
    """
    now = datetime.now(timezone.utc)
    diff = now - dt

    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"
