"""Git operations tools for the AI agent using GitPython."""

from pathlib import Path
from typing import Optional

import git
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError


def get_work_directory() -> Path:
    """Get the current working directory where the CLI was invoked.

    Returns:
        Path object representing the current working directory
    """
    return Path.cwd()


def is_git_repository(path: Optional[Path] = None) -> bool:
    """Check if the given path (or current directory) is a git repository.

    Args:
        path: Optional path to check. If None, uses current working directory.

    Returns:
        True if the path is inside a git repository, False otherwise
    """
    if path is None:
        path = get_work_directory()

    try:
        git.Repo(path, search_parent_directories=True)
        return True
    except (InvalidGitRepositoryError, NoSuchPathError):
        return False


def _get_repo(path: Optional[Path] = None) -> tuple[bool, git.Repo | str]:
    """Get a git repository object.

    Args:
        path: Optional path to repository. If None, uses current directory.

    Returns:
        Tuple of (success: bool, repo: Repo | error_message: str)
    """
    if path is None:
        path = get_work_directory()

    try:
        repo = git.Repo(path, search_parent_directories=True)
        return True, repo
    except InvalidGitRepositoryError:
        return False, f"Error: {path} is not a git repository"
    except NoSuchPathError:
        return False, f"Error: Path {path} does not exist"
    except Exception as e:
        return False, f"Error accessing repository: {str(e)}"


def git_status() -> str:
    """Get the current git repository status.

    Returns:
        String with git status output or error message
    """
    success, result = _get_repo()
    if not success:
        return result

    repo: git.Repo = result

    try:
        # Get current branch
        try:
            branch = repo.active_branch.name
            branch_info = f"On branch {branch}\n"
        except TypeError:
            # Detached HEAD state
            branch_info = f"HEAD detached at {repo.head.commit.hexsha[:7]}\n"

        # Check for changes
        changed_files = [item.a_path for item in repo.index.diff(None)]
        untracked_files = repo.untracked_files
        staged_files = [item.a_path for item in repo.index.diff("HEAD")]

        status_lines = [branch_info]

        # Staged changes
        if staged_files:
            status_lines.append("Changes to be committed:")
            status_lines.append("  (use \"git restore --staged <file>...\" to unstage)\n")
            for file in staged_files:
                status_lines.append(f"\tmodified:   {file}")
            status_lines.append("")

        # Unstaged changes
        if changed_files:
            status_lines.append("Changes not staged for commit:")
            status_lines.append("  (use \"git add <file>...\" to update what will be committed)")
            status_lines.append("  (use \"git restore <file>...\" to discard changes in working directory)\n")
            for file in changed_files:
                status_lines.append(f"\tmodified:   {file}")
            status_lines.append("")

        # Untracked files
        if untracked_files:
            status_lines.append("Untracked files:")
            status_lines.append("  (use \"git add <file>...\" to include in what will be committed)\n")
            for file in untracked_files:
                status_lines.append(f"\t{file}")
            status_lines.append("")

        # Clean status
        if not staged_files and not changed_files and not untracked_files:
            status_lines.append("nothing to commit, working tree clean")
        elif not staged_files:
            status_lines.append("no changes added to commit (use \"git add\" and/or \"git commit -a\")")

        return "Git Status:\n\n" + "\n".join(status_lines)

    except Exception as e:
        return f"Error getting status: {str(e)}"


def git_branch_list() -> str:
    """List all branches in the repository.

    Returns:
        String with branch list or error message
    """
    success, result = _get_repo()
    if not success:
        return result

    repo: git.Repo = result

    try:
        current_branch = repo.active_branch.name if not repo.head.is_detached else None
        branches = []

        # Local branches
        for branch in repo.branches:
            marker = "* " if branch.name == current_branch else "  "
            commit_sha = branch.commit.hexsha[:7]
            commit_msg = branch.commit.message.split('\n')[0][:50]
            branches.append(f"{marker}{branch.name} {commit_sha} {commit_msg}")

        # Remote branches
        for remote in repo.remotes:
            for ref in remote.refs:
                branch_name = f"remotes/{ref.name}"
                commit_sha = ref.commit.hexsha[:7]
                commit_msg = ref.commit.message.split('\n')[0][:50]
                branches.append(f"  {branch_name} {commit_sha} {commit_msg}")

        return "Git Branches:\n\n" + "\n".join(branches)

    except Exception as e:
        return f"Error listing branches: {str(e)}"


def git_log(count: int = 10, oneline: bool = False) -> str:
    """Show recent git commits.

    Args:
        count: Number of commits to show (default: 10, max: 50)
        oneline: If True, show compact one-line format

    Returns:
        String with git log output or error message
    """
    success, result = _get_repo()
    if not success:
        return result

    repo: git.Repo = result

    # Limit count to reasonable maximum
    count = min(max(1, count), 50)

    try:
        commits = list(repo.iter_commits('HEAD', max_count=count))
        log_lines = []

        for commit in commits:
            sha = commit.hexsha[:7]
            author = commit.author.name
            date = commit.committed_datetime.strftime('%Y-%m-%d %H:%M:%S')
            message = commit.message.split('\n')[0]

            if oneline:
                log_lines.append(f"{sha} {message}")
            else:
                # Format similar to git log --pretty=format:"%h - %an, %ar : %s"
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                time_diff = now - commit.committed_datetime

                if time_diff.days > 365:
                    time_ago = f"{time_diff.days // 365} year{'s' if time_diff.days // 365 > 1 else ''} ago"
                elif time_diff.days > 30:
                    time_ago = f"{time_diff.days // 30} month{'s' if time_diff.days // 30 > 1 else ''} ago"
                elif time_diff.days > 0:
                    time_ago = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
                elif time_diff.seconds > 3600:
                    time_ago = f"{time_diff.seconds // 3600} hour{'s' if time_diff.seconds // 3600 > 1 else ''} ago"
                else:
                    time_ago = f"{time_diff.seconds // 60} minute{'s' if time_diff.seconds // 60 > 1 else ''} ago"

                log_lines.append(f"{sha} - {author}, {time_ago} : {message}")

        return f"Git Log (last {count} commits):\n\n" + "\n".join(log_lines)

    except Exception as e:
        return f"Error getting log: {str(e)}"


def get_previous_step_branch(current_branch: str) -> Optional[str]:
    """Detect the previous step branch based on naming pattern.

    Args:
        current_branch: Current branch name (e.g., 'step/step-3' or 'step-3')

    Returns:
        Previous step branch name or None if not a step branch or step-0

    Examples:
        'step/step-3' -> 'step/step-2'
        'step-3' -> 'step-2'
        'step/step-0' -> None
        'main' -> None
    """
    import re

    # Pattern: step/step-N or step-N
    pattern = r'^(step/)?step-(\d+)$'
    match = re.match(pattern, current_branch)

    if not match:
        return None

    prefix = match.group(1) or ""  # 'step/' or ''
    step_num = int(match.group(2))

    if step_num == 0:
        return None

    return f"{prefix}step-{step_num - 1}"


def git_diff(
    file_path: Optional[str] = None,
    staged: bool = False,
    from_ref: Optional[str] = None,
    to_ref: Optional[str] = None,
) -> str:
    """Show git diff for changes.

    Supports multiple diff modes:
    1. Working directory changes (default): unstaged changes
    2. Staged changes: staged but not committed
    3. Branch-to-branch: compare two branches/commits
    4. Previous step: automatic comparison with previous step branch

    Args:
        file_path: Optional specific file to diff. If None, shows all changes.
        staged: If True, show staged changes (git diff --cached)
        from_ref: Branch/commit to compare from (e.g., 'step/step-2')
        to_ref: Branch/commit to compare to (default: current HEAD)

    Returns:
        String with diff output or error message

    Examples:
        git_diff() -> unstaged changes in working directory
        git_diff(staged=True) -> staged changes
        git_diff(from_ref='step/step-2', to_ref='step/step-3') -> branch comparison
        git_diff(from_ref='HEAD~1') -> changes since last commit
    """
    success, result = _get_repo()
    if not success:
        return result

    repo: git.Repo = result

    try:
        # Branch-to-branch or commit-to-commit comparison
        if from_ref is not None:
            # Default to_ref is current HEAD
            if to_ref is None:
                to_ref = "HEAD"

            # Use git.diff for commit/branch comparisons
            # Only pass file_path if it's specified (avoid passing empty string)
            if file_path:
                diff_output = repo.git.diff(from_ref, to_ref, file_path)
            else:
                diff_output = repo.git.diff(from_ref, to_ref)

            if not diff_output:
                return f"No differences between {from_ref} and {to_ref}."

            return f"Git Diff: {from_ref}..{to_ref}\n\n{diff_output}"

        # Working directory diffs (original behavior)
        if staged:
            # Diff between HEAD and staged changes
            diff = repo.index.diff("HEAD", paths=file_path)
        else:
            # Diff between staged and working directory
            diff = repo.index.diff(None, paths=file_path)

        if not diff:
            status = "staged" if staged else "unstaged"
            return f"No {status} changes to show."

        # Format diff output
        diff_text = []
        for diff_item in diff:
            diff_text.append(f"diff --git a/{diff_item.a_path} b/{diff_item.b_path}")
            diff_text.append(f"--- a/{diff_item.a_path}")
            diff_text.append(f"+++ b/{diff_item.b_path}")
            diff_text.append(diff_item.diff.decode('utf-8', errors='replace'))

        return f"Git Diff{' (staged)' if staged else ''}:\n\n" + "\n".join(diff_text)

    except Exception as e:
        return f"Error getting diff: {str(e)}"


def git_checkout(branch_or_tag: str, create_new: bool = False) -> str:
    """Checkout a git branch or tag.

    Args:
        branch_or_tag: Name of the branch or tag to checkout
        create_new: If True, create a new branch with -b flag

    Returns:
        String with checkout result or error message
    """
    success, result = _get_repo()
    if not success:
        return result

    repo: git.Repo = result

    try:
        # Check if there are uncommitted changes
        has_changes = repo.is_dirty(untracked_files=True)

        if has_changes:
            # For demo mode, do a hard reset to discard all changes
            # This allows seamless branch switching
            repo.head.reset(index=True, working_tree=True)

            # Clean untracked files
            repo.git.clean('-fd')

            message_parts = ["⚠️  Discarded uncommitted changes (demo mode)"]
        else:
            message_parts = []

        # Checkout or create branch
        if create_new:
            new_branch = repo.create_head(branch_or_tag)
            new_branch.checkout()
            message_parts.append(f"✓ Created and checked out new branch: {branch_or_tag}")
        else:
            # Try to checkout existing branch or tag
            try:
                repo.git.checkout(branch_or_tag)
                message_parts.append(f"✓ Successfully checked out: {branch_or_tag}")
            except GitCommandError as e:
                return f"Error checking out '{branch_or_tag}':\n{str(e)}"

        return "\n".join(message_parts)

    except Exception as e:
        return f"Error during checkout: {str(e)}"
