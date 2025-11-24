"""Grep tool for searching content within files."""

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class GrepMatch:
    """Represents a single grep match result."""

    file_path: str
    line_number: int
    line_content: str


@dataclass
class GrepResult:
    """Result of a grep search operation."""

    pattern: str
    matches: list[GrepMatch]
    total_matches: int
    strategy_used: str
    search_location: str
    error: Optional[str] = None


def validate_grep_pattern(pattern: str) -> Optional[str]:
    """Validate the regular expression pattern.

    Args:
        pattern: The regex pattern to validate

    Returns:
        Error message if invalid, None if valid
    """
    if not pattern or not pattern.strip():
        return "Pattern cannot be empty"

    try:
        re.compile(pattern)
        return None
    except re.error as e:
        return f"Invalid regular expression: {str(e)}"


def is_command_available(command: str) -> bool:
    """Check if a command is available in the system PATH.

    Args:
        command: Command name to check

    Returns:
        True if command is available, False otherwise
    """
    return shutil.which(command) is not None


def parse_grep_output(output: str, base_path: Path, workspace_root: Path) -> list[GrepMatch]:
    """Parse grep output in the format: filePath:lineNumber:lineContent

    Args:
        output: Raw grep output
        base_path: Base path where grep was run
        workspace_root: Workspace root for relative paths

    Returns:
        List of GrepMatch objects
    """
    matches = []
    if not output.strip():
        return matches

    for line in output.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Find first and second colon
        first_colon = line.find(":")
        if first_colon == -1:
            continue

        second_colon = line.find(":", first_colon + 1)
        if second_colon == -1:
            continue

        file_path_raw = line[:first_colon]
        line_number_str = line[first_colon + 1 : second_colon]
        line_content = line[second_colon + 1 :]

        try:
            line_number = int(line_number_str)

            # Convert to absolute then workspace-relative path
            abs_path = (base_path / file_path_raw).resolve()

            # Make relative to workspace
            try:
                rel_path = abs_path.relative_to(workspace_root)
            except ValueError:
                # File outside workspace, skip
                continue

            matches.append(
                GrepMatch(
                    file_path=str(rel_path), line_number=line_number, line_content=line_content
                )
            )
        except ValueError:
            # Skip malformed lines
            continue

    return matches


def git_grep_search(
    pattern: str, search_path: Path, workspace_root: Path, include: Optional[str] = None
) -> Optional[list[GrepMatch]]:
    """Perform search using git grep.

    Args:
        pattern: Regex pattern to search for
        search_path: Directory to search in
        workspace_root: Workspace root directory
        include: Optional glob pattern to filter files

    Returns:
        List of matches if successful, None if git grep unavailable
    """
    if not is_command_available("git"):
        return None

    # Check if we're in a git repository
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=search_path,
            capture_output=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return None

    cmd = ["git", "grep", "--untracked", "-n", "-E", "--ignore-case", pattern]

    if include:
        cmd.extend(["--", include])

    try:
        result = subprocess.run(cmd, cwd=search_path, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            return parse_grep_output(result.stdout, search_path, workspace_root)
        elif result.returncode == 1:
            return []  # No matches found
        else:
            return None  # Error occurred

    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return None


def system_grep_search(
    pattern: str, search_path: Path, workspace_root: Path, include: Optional[str] = None
) -> Optional[list[GrepMatch]]:
    """Perform search using system grep.

    Args:
        pattern: Regex pattern to search for
        search_path: Directory to search in
        workspace_root: Workspace root directory
        include: Optional glob pattern to filter files

    Returns:
        List of matches if successful, None if system grep unavailable
    """
    if not is_command_available("grep"):
        return None

    cmd = ["grep", "-r", "-n", "-H", "-E", "-i"]

    # Add exclude directories
    for exclude_dir in [".git", "node_modules", "__pycache__"]:
        cmd.append(f"--exclude-dir={exclude_dir}")

    if include:
        cmd.append(f"--include={include}")

    cmd.extend([pattern, "."])

    try:
        result = subprocess.run(cmd, cwd=search_path, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            return parse_grep_output(result.stdout, search_path, workspace_root)
        elif result.returncode == 1:
            return []  # No matches found
        else:
            return None  # Error occurred

    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return None


def python_grep_search(
    pattern: str, search_path: Path, workspace_root: Path, include: Optional[str] = None
) -> list[GrepMatch]:
    """Perform search using pure Python implementation.

    Args:
        pattern: Regex pattern to search for
        search_path: Directory to search in
        workspace_root: Workspace root directory
        include: Optional glob pattern to filter files

    Returns:
        List of matches
    """
    matches = []
    compiled_pattern = re.compile(pattern, re.IGNORECASE)

    # Default excludes
    default_excludes = [
        ".git",
        "node_modules",
        "__pycache__",
        ".vscode",
        ".idea",
        "dist",
        "build",
        "*.pyc",
    ]

    # Determine which files to search
    if include:
        # Use glob pattern
        import glob

        glob_pattern = str(search_path / include)
        file_paths = [Path(p) for p in glob.glob(glob_pattern, recursive=True)]
    else:
        # Search all files recursively
        file_paths = list(search_path.rglob("*"))

    for file_path in file_paths:
        if not file_path.is_file():
            continue

        # Get workspace-relative path
        try:
            rel_path = file_path.resolve().relative_to(workspace_root)
        except ValueError:
            continue

        # Check excludes
        if any(exclude in str(rel_path) for exclude in default_excludes):
            continue

        # Try to read and search file
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_number, line in enumerate(f, 1):
                    if compiled_pattern.search(line):
                        matches.append(
                            GrepMatch(
                                file_path=str(rel_path),
                                line_number=line_number,
                                line_content=line.rstrip("\n\r"),
                            )
                        )
        except (IOError, UnicodeDecodeError):
            # Skip binary or unreadable files
            continue

    return matches


def grep_content(
    pattern: str, workspace_root: Path, path: Optional[str] = None, include: Optional[str] = None
) -> GrepResult:
    """Search for regular expression patterns within file contents.

    Uses a three-tier fallback strategy:
    1. Git grep (fastest, when in git repo)
    2. System grep (Unix-like systems)
    3. Python implementation (fallback)

    Args:
        pattern: Regular expression pattern to search for
        workspace_root: Root directory of workspace
        path: Optional subdirectory to search in
        include: Optional glob pattern to filter files (e.g., "*.py", "*.{ts,tsx}")

    Returns:
        GrepResult with matches and metadata
    """
    # Validate pattern
    error = validate_grep_pattern(pattern)
    if error:
        return GrepResult(
            pattern=pattern,
            matches=[],
            total_matches=0,
            strategy_used="none",
            search_location="",
            error=error,
        )

    # Determine search path
    if path:
        search_path = (workspace_root / path).resolve()
        if not search_path.exists():
            return GrepResult(
                pattern=pattern,
                matches=[],
                total_matches=0,
                strategy_used="none",
                search_location="",
                error=f"Path does not exist: {path}",
            )
        if not search_path.is_dir():
            return GrepResult(
                pattern=pattern,
                matches=[],
                total_matches=0,
                strategy_used="none",
                search_location="",
                error=f"Path is not a directory: {path}",
            )
        # Validate within workspace
        try:
            search_path.relative_to(workspace_root)
        except ValueError:
            return GrepResult(
                pattern=pattern,
                matches=[],
                total_matches=0,
                strategy_used="none",
                search_location="",
                error=f"Path is outside workspace: {path}",
            )
        search_location = f'in path "{path}"'
    else:
        search_path = workspace_root
        search_location = "in workspace directory"

    # Try git grep first
    matches = git_grep_search(pattern, search_path, workspace_root, include)
    if matches is not None:
        strategy_used = "git grep"
    else:
        # Try system grep
        matches = system_grep_search(pattern, search_path, workspace_root, include)
        if matches is not None:
            strategy_used = "system grep"
        else:
            # Fall back to Python
            matches = python_grep_search(pattern, search_path, workspace_root, include)
            strategy_used = "python fallback"

    # Add include filter to search location
    if include:
        search_location += f' (filter: "{include}")'

    return GrepResult(
        pattern=pattern,
        matches=matches,
        total_matches=len(matches),
        strategy_used=strategy_used,
        search_location=search_location,
    )


def format_grep_result(result: GrepResult) -> str:
    """Format grep search results as a readable string.

    Args:
        result: The GrepResult to format

    Returns:
        Formatted string with matches
    """
    if result.error:
        return f"Grep Search Error: {result.error}"

    lines = [f"Grep Search: /{result.pattern}/", ""]

    if result.total_matches == 0:
        lines.append("No matches found.")
        return "\n".join(lines)

    lines.append(
        f"Found {result.total_matches} match{'es' if result.total_matches != 1 else ''} "
        f"using {result.strategy_used} {result.search_location}:"
    )
    lines.append("")

    # Group matches by file
    files_with_matches: dict[str, list[GrepMatch]] = {}
    for match in result.matches:
        if match.file_path not in files_with_matches:
            files_with_matches[match.file_path] = []
        files_with_matches[match.file_path].append(match)

    # Format output by file
    for file_path in sorted(files_with_matches.keys()):
        file_matches = files_with_matches[file_path]
        lines.append(f"📄 {file_path} ({len(file_matches)} matches):")

        # Show up to 5 matches per file
        for match in file_matches[:5]:
            lines.append(f"  Line {match.line_number}: {match.line_content.strip()}")

        if len(file_matches) > 5:
            lines.append(f"  ... and {len(file_matches) - 5} more matches")

        lines.append("")

    return "\n".join(lines)
