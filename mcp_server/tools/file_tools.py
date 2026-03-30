"""File system tools exposed via MCP."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_BASE_PATH = Path(os.getenv("FILES_BASE_PATH", "./data/files")).resolve()


def _safe_path(relative: str) -> Path:
    """Resolve path and ensure it stays within the base directory."""
    target = (_BASE_PATH / relative).resolve()
    if not str(target).startswith(str(_BASE_PATH)):
        raise PermissionError(f"Path traversal detected: '{relative}'")
    return target


def list_files(directory: str = ".") -> list[dict]:
    """
    List files available in the data directory.

    Args:
        directory: Subdirectory to list relative to the data root (default '.')
    """
    try:
        target = _safe_path(directory)
        if not target.exists():
            return [{"error": f"Directory '{directory}' does not exist"}]

        entries = []
        for item in sorted(target.iterdir()):
            entries.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size_bytes": item.stat().st_size if item.is_file() else None,
                "path": str(item.relative_to(_BASE_PATH)),
            })
        return entries
    except PermissionError as e:
        return [{"error": str(e)}]


def read_file(filepath: str) -> dict:
    """
    Read the content of a file from the data directory.

    Args:
        filepath: Path to the file relative to the data root
    """
    try:
        target = _safe_path(filepath)
        if not target.exists():
            return {"error": f"File '{filepath}' not found"}
        if not target.is_file():
            return {"error": f"'{filepath}' is not a file"}

        content = target.read_text(encoding="utf-8", errors="replace")
        # Truncate very large files
        if len(content) > 50_000:
            content = content[:50_000] + "\n\n[... truncated at 50KB ...]"

        return {
            "filepath": str(target.relative_to(_BASE_PATH)),
            "size_bytes": target.stat().st_size,
            "content": content,
        }
    except PermissionError as e:
        return {"error": str(e)}
