"""Replace tool for editing files with exact literal text replacement."""

from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path
from typing import Optional


@dataclass
class ReplaceResult:
    """Result of a replace operation."""

    success: bool
    message: str
    file_path: str
    occurrences: int = 0
    diff: Optional[str] = None
    error: Optional[str] = None


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


def normalize_line_endings(content: str) -> str:
    """Normalize line endings to LF (\\n).

    Args:
        content: Content with potentially mixed line endings

    Returns:
        Content with normalized line endings
    """
    return content.replace("\r\n", "\n")


def count_occurrences(content: str, search_string: str) -> int:
    """Count the number of times a string appears in content.

    Args:
        content: The content to search
        search_string: The string to count

    Returns:
        Number of occurrences
    """
    if not search_string:
        return 0
    return content.count(search_string)


def generate_diff(old_content: str, new_content: str, file_path: str) -> str:
    """Generate a unified diff between old and new content.

    Args:
        old_content: Original file content
        new_content: Modified file content
        file_path: Path to the file (for diff header)

    Returns:
        Unified diff string
    """
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff = unified_diff(
        old_lines,
        new_lines,
        fromfile=f"{file_path} (current)",
        tofile=f"{file_path} (proposed)",
        lineterm="",
    )

    return "".join(diff)


def replace_text(
    file_path: str,
    workspace_root: Path,
    old_string: str,
    new_string: str,
    expected_replacements: int = 1,
) -> ReplaceResult:
    """Replace text in a file with exact literal matching.

    Args:
        file_path: Relative path from workspace root (e.g., 'src/main.py')
        workspace_root: Root directory of workspace
        old_string: Exact literal text to replace (with context)
        new_string: Exact literal replacement text
        expected_replacements: Expected number of occurrences (default: 1)

    Returns:
        ReplaceResult with operation details

    Key behaviors:
    - If old_string is empty and file doesn't exist: creates new file
    - If old_string is empty and file exists: error
    - Validates that occurrences match expected_replacements
    - Normalizes line endings to LF
    - Creates parent directories as needed
    """
    # Build and validate secure path
    resolved_path, path_error = build_secure_path(file_path, workspace_root)
    if path_error:
        return ReplaceResult(
            success=False, message="", file_path=file_path, error=path_error
        )

    # Check if file exists
    file_exists = resolved_path.exists()
    current_content: Optional[str] = None

    if file_exists:
        # Check if it's a file (not directory)
        if not resolved_path.is_file():
            return ReplaceResult(
                success=False,
                message="",
                file_path=file_path,
                error=f"Path is not a file: {file_path}",
            )

        # Read and normalize current content
        try:
            with open(resolved_path, "r", encoding="utf-8", errors="replace") as f:
                current_content = f.read()
            current_content = normalize_line_endings(current_content)
        except Exception as e:
            return ReplaceResult(
                success=False,
                message="",
                file_path=file_path,
                error=f"Error reading file: {str(e)}",
            )

    # Handle file creation case
    if old_string == "" and not file_exists:
        # Creating a new file
        new_content = new_string
        occurrences = 0
        is_new_file = True

    elif old_string == "" and file_exists:
        # Error: trying to create a file that already exists
        return ReplaceResult(
            success=False,
            message="",
            file_path=file_path,
            error=f"Failed to edit. Attempted to create a file that already exists: {file_path}",
        )

    elif not file_exists:
        # Error: trying to edit a non-existent file
        return ReplaceResult(
            success=False,
            message="",
            file_path=file_path,
            error=f"File not found. Cannot apply edit. Use an empty old_string to create a new file: {file_path}",
        )

    else:
        # Editing existing file
        is_new_file = False
        assert current_content is not None

        # Count occurrences
        occurrences = count_occurrences(current_content, old_string)

        # Validate occurrences
        if occurrences == 0:
            return ReplaceResult(
                success=False,
                message="",
                file_path=file_path,
                error=(
                    f"Failed to edit, could not find the string to replace. "
                    f"The exact text in old_string was not found. "
                    f"Ensure you're not escaping content incorrectly and check whitespace, indentation, and context."
                ),
            )

        if occurrences != expected_replacements:
            occurrence_term = (
                "occurrence" if expected_replacements == 1 else "occurrences"
            )
            return ReplaceResult(
                success=False,
                message="",
                file_path=file_path,
                error=(
                    f"Failed to edit, expected {expected_replacements} {occurrence_term} "
                    f"but found {occurrences} for old_string in file: {file_path}"
                ),
            )

        # Check for no-op changes
        if old_string == new_string:
            return ReplaceResult(
                success=False,
                message="",
                file_path=file_path,
                error="No changes to apply. The old_string and new_string are identical.",
            )

        # Apply replacement (str.replace handles literal strings safely)
        new_content = current_content.replace(old_string, new_string)

        # Check if content actually changed
        if current_content == new_content:
            return ReplaceResult(
                success=False,
                message="",
                file_path=file_path,
                error="No changes to apply. The new content is identical to the current content.",
            )

    # Generate diff
    diff = generate_diff(current_content or "", new_content, str(resolved_path))

    # Write file
    try:
        # Create parent directories if needed
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        with open(resolved_path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        return ReplaceResult(
            success=False,
            message="",
            file_path=file_path,
            error=f"Error writing file: {str(e)}",
        )

    # Create success result
    if is_new_file:
        message = f"Created new file: {file_path}"
    else:
        message = f"Successfully modified file: {file_path} ({occurrences} replacements)"

    return ReplaceResult(
        success=True,
        message=message,
        file_path=file_path,
        occurrences=occurrences,
        diff=diff,
    )


def format_replace_result(result: ReplaceResult) -> str:
    """Format replace result as a readable string.

    Args:
        result: The ReplaceResult to format

    Returns:
        Formatted string with operation details
    """
    if result.error:
        return f"Replace Error: {result.error}"

    lines = [result.message, ""]

    # Add diff if available
    if result.diff:
        lines.append("Changes:")
        lines.append("─" * 80)
        lines.append(result.diff)
        lines.append("─" * 80)

    return "\n".join(lines)
