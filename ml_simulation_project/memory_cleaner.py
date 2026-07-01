"""Safe cleanup helpers for project-local junk files.

This module removes known Python/test/cache artifacts under the project root.
It avoids deleting anything outside the repository and skips system trash
cleanup on Windows unless explicitly requested on Linux.
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import stat
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent
EXCLUDED_DIRS = {".git", ".venv", "venv", "env"}
JUNK_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".ipynb_checkpoints",
    "htmlcov",
}
JUNK_FILE_SUFFIXES = {".pyc", ".pyo", ".pyd", ".tmp", ".temp", ".log", ".bak"}
JUNK_FILE_NAMES = {".coverage", "coverage.xml", ".DS_Store", "Thumbs.db"}


def _is_within_project(path: Path) -> bool:
    """Return True when `path` is inside the project root."""

    try:
        path.resolve().relative_to(PROJECT_ROOT)
        return True
    except (ValueError, OSError):
        return False


def _is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.relative_to(PROJECT_ROOT).parts)


def _safe_rmtree(path: Path) -> bool:
    """Remove a directory only if it is a known project-local junk folder."""

    if not path.exists() or not path.is_dir():
        return False

    if path.name not in JUNK_DIR_NAMES:
        return False

    if not _is_within_project(path) or _is_excluded(path):
        logger.warning("Skipped removal outside project root: %s", path)
        return False

    try:
        shutil.rmtree(path, onerror=_handle_readonly_remove)
        logger.debug("Removed: %s", path)
        return True
    except FileNotFoundError:
        return False
    except PermissionError:
        logger.warning("Permission denied: %s", path)
        return False
    except OSError as exc:
        logger.error("Error removing %s: %s", path, exc)
        return False


def _handle_readonly_remove(func, path, _exc_info):
    """Retry removal after clearing read-only bits on known junk paths."""

    retry_path = Path(path)
    if not _is_within_project(retry_path):
        raise PermissionError(path)

    os.chmod(path, stat.S_IWRITE)
    func(path)


def _safe_unlink(path: Path) -> bool:
    """Remove a file only if it is a known project-local junk file."""

    if not path.exists() or not path.is_file():
        return False

    if path.name not in JUNK_FILE_NAMES and path.suffix not in JUNK_FILE_SUFFIXES:
        return False

    if not _is_within_project(path) or _is_excluded(path):
        logger.warning("Skipped removal outside project root: %s", path)
        return False

    try:
        os.chmod(str(path), stat.S_IWRITE)
        path.unlink(missing_ok=True)
        logger.debug("Removed: %s", path)
        return True
    except PermissionError:
        logger.warning("Permission denied: %s", path)
        return False
    except OSError as exc:
        logger.error("Error removing %s: %s", path, exc)
        return False


def clear_junk_directories():
    """Remove known project-local junk directories across the full tree.

    Returns the number of directories removed.
    """

    removed_count = 0

    for dir_path in sorted(PROJECT_ROOT.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if not dir_path.is_dir() or dir_path.name not in JUNK_DIR_NAMES:
            continue
        if _is_excluded(dir_path):
            continue
        if _safe_rmtree(dir_path):
            removed_count += 1

    if removed_count > 0:
        logger.info("Memory cleared: %s junk directories removed.", removed_count)
    else:
        logger.info("No junk directories found.")

    return removed_count


def clear_junk_files():
    """Remove known project-local junk files across the full tree.

    Returns the number of files removed.
    """

    removed_count = 0

    for file_path in PROJECT_ROOT.rglob("*"):
        if not file_path.is_file():
            continue
        if _is_excluded(file_path):
            continue
        if _safe_unlink(file_path):
            removed_count += 1

    if removed_count > 0:
        logger.info("Memory cleared: %s junk files removed.", removed_count)
    else:
        logger.info("No junk files found.")

    return removed_count


def clear_trash_files():
    """Skip system trash cleanup on Windows and other non-Linux platforms.

    The project should not try to delete user trash on Windows because the
    trash location is platform-specific and cleanup semantics are risky.
    """

    if platform.system() != "Linux":
        logger.debug("Trash cleanup skipped: not on Linux system.")
        return 0

    trash_path = Path.home() / ".local" / "share" / "Trash" / "files"
    if not trash_path.exists():
        logger.debug("Trash directory not found.")
        return 0

    removed_count = 0
    for item_path in trash_path.iterdir():
        try:
            if item_path.is_dir() and not item_path.is_symlink():
                shutil.rmtree(item_path)
            else:
                item_path.unlink(missing_ok=True)
            removed_count += 1
            logger.debug("Removed from trash: %s", item_path.name)
        except PermissionError:
            logger.warning("Permission denied: %s", item_path)
        except OSError as exc:
            logger.error("Error removing %s: %s", item_path, exc)

    if removed_count > 0:
        logger.info("Memory cleared: %s trash items removed.", removed_count)
    else:
        logger.info("No trash items found.")

    return removed_count


def clear_memory(clean_trash=False):
    """Clear safe project-local caches and optionally Linux trash."""

    logger.info("Starting memory cleanup...")
    logger.info("TEMP START clear_memory clean_trash=%s", clean_trash)

    results = {
        "junk_directories_removed": clear_junk_directories(),
        "junk_files_removed": clear_junk_files(),
        "trash_removed": clear_trash_files() if clean_trash else 0,
    }

    total_items = sum(results.values())
    logger.info("Cleanup complete. Total items removed: %s", total_items)
    logger.info("TEMP END clear_memory results=%s", results)

    return results


def clean():
    """Entry point for running cleanup from the command line."""

    clean_trash = "--trash" in sys.argv or "-t" in sys.argv

    try:
        results = clear_memory(clean_trash=clean_trash)
        print("\nMemory cleanup completed successfully!")
        print(f"  - Junk directories removed: {results['junk_directories_removed']}")
        print(f"  - Junk files removed: {results['junk_files_removed']}")
        if clean_trash:
            print(f"  - Trash items removed: {results['trash_removed']}")
    except Exception as exc:
        logger.error("Fatal error during cleanup: %s", exc)
        print(f"\nMemory cleanup failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    clean()


