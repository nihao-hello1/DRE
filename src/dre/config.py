"""Central config for DRE — resolves paths regardless of install method.

When installed via ``pip install -e .``, templates live inside the package as
``src/dre/templates/``.  When run from a git checkout, the ``skills/``
directory is at the project root.
"""

from __future__ import annotations

from pathlib import Path

# Root of the *installed package* (where __init__.py lives).
_PACKAGE_DIR = Path(__file__).resolve().parent

# Project root (only useful in a git checkout / development install).
_PROJECT_ROOT = _PACKAGE_DIR.parent.parent  # src/dre/ -> src/ -> F:/DRE


def templates_dir() -> Path:
    """Return the directory containing YAML style templates."""
    return _PACKAGE_DIR / "templates"


def skills_dir() -> Path:
    """Return the directory containing agent skill files."""
    # In dev layout: skills/ lives at project root.
    p = _PROJECT_ROOT / "skills"
    if p.exists():
        return p
    # Fallback: inside the package for dist installs.
    return _PACKAGE_DIR.parent / "skills"


def skill_file() -> Path:
    """Return the path to the DRE Skill file (SKILL.md)."""
    return _PACKAGE_DIR / "SKILL.md"


def cli_entry() -> str:
    """Return the CLI entry point for MCP server config."""
    return "python -m dre.mcp_server.server"


def dre_root() -> Path:
    """Project root directory (for development / CWD-sensitive tools)."""
    return _PROJECT_ROOT
