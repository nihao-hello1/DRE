"""OfficeCLI post-processing integration.

Uses OfficeCLI to refresh TOC, PAGE, and NUMPAGES field codes in the
generated DOCX so the document opens with correct page numbers and
table-of-contents entries.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def _find_officecli() -> str | None:
    """Locate the officecli executable.

    Checks common installation paths.
    """
    # Common paths (Windows + Mac)
    candidates = [
        os.environ.get("OFFICECLI_PATH", ""),
        str(Path.home() / "AppData" / "Local" / "OfficeCLI" / "officecli.exe"),  # Windows
        str(Path.home() / "AppData" / "Local" / "OfficeCLI" / "officecli"),
        str(Path.home() / ".local" / "bin" / "officecli"),                        # Linux local
        "/usr/local/bin/officecli",                                                # macOS Homebrew
        "officecli",
    ]

    for candidate in candidates:
        if not candidate:
            continue
        if shutil.which(candidate) is not None:
            return candidate
        if Path(candidate).exists():
            return candidate

    return None


class OfficePostProcessor:
    """Post-process a DOCX file using OfficeCLI.

    Requires Microsoft Word to be installed (OfficeCLI delegates to Word
    for field-code refresh).
    """

    def __init__(self, officecli_path: str | Path | None = None) -> None:
        self._path = officecli_path or _find_officecli()

    def is_available(self) -> bool:
        """Check whether OfficeCLI is reachable on this system."""
        if self._path is None:
            return False
        return shutil.which(str(self._path)) is not None or Path(str(self._path)).exists()

    def refresh(self, docx_path: str | Path) -> Path:
        """Run ``officecli refresh`` to update TOC and page-number fields.

        Args:
            docx_path: Path to the DOCX file to refresh.

        Returns:
            The same *docx_path* (modified in-place).

        Raises:
            RuntimeError: If OfficeCLI is not available or the command fails.
        """
        if not self.is_available():
            raise RuntimeError(
                "OfficeCLI is not available. "
                "Install from https://clio.officecli.com or set OFFICECLI_PATH."
            )

        path = Path(docx_path)
        if not path.exists():
            raise FileNotFoundError(f"DOCX not found: {path}")

        cmd = [str(self._path), "refresh", str(path)]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2-minute timeout for Word
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"OfficeCLI refresh failed (exit {result.returncode}):\n"
                f"  stderr: {result.stderr.strip()}"
            )

        return path
