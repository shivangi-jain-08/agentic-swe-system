from __future__ import annotations

import tempfile
from collections.abc import Iterable
from pathlib import Path

import git


def apply_diff(repo_path: str, branch_name: str, diffs: Iterable) -> None:
    """Create a branch, apply unified diffs, and commit.

    `diffs` is expected to be an iterable of objects with `.unified_diff`.
    """

    repo = git.Repo(repo_path)
    repo.git.checkout("-b", branch_name)

    with tempfile.TemporaryDirectory() as tmp:
        patch_path = Path(tmp) / f"{branch_name}.patch"
        for diff in diffs:
            patch_path.write_text(diff.unified_diff, encoding="utf-8")
            repo.git.apply(str(patch_path))

    repo.index.add(["--all"])
    repo.index.commit(f"agentic-swe: {branch_name}")


def cleanup(repo_path: str, branch_name: str, main_branch: str = "main") -> None:
    repo = git.Repo(repo_path)
    repo.git.checkout(main_branch)
    repo.delete_head(branch_name, force=True)
    if repo.is_dirty(untracked_files=True):
        raise RuntimeError("Repo is not clean after cleanup")
