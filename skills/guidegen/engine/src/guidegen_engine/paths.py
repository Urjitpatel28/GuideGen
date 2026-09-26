"""Repo-root containment. The engine reads only inside the repo + skill folder and writes only in the output folder."""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

from guidegen_engine.errors import GuideGenError

DEFAULT_OUT = "guidegen-out"

OUT_GITIGNORE = "*\n!.gitignore\n!guidegen.config.json\n!manual.yaml\n!brief.md\n"
# earlier defaults, upgraded in place (a developer-edited .gitignore is never touched)
_OLD_OUT_GITIGNORES = ("*\n!.gitignore\n!guidegen.config.json\n!manual.yaml\n",)

SKIP_DIRS = {
    ".git", "node_modules", "bin", "obj", ".next", "dist", "build", "out", ".venv", "venv",
    "__pycache__", ".vs", ".idea", "packages", "coverage", DEFAULT_OUT, "graphify-out", ".turbo",
    "target", ".svelte-kit", ".angular", "TestResults", "playwright-report", "test-results",
}


def skill_dir() -> Path:
    """skills/guidegen/ - the engine lives at skills/guidegen/engine/src/guidegen_engine."""
    env = os.environ.get("GUIDEGEN_SKILL_DIR")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[3]


def templates_dir() -> Path:
    return skill_dir() / "templates"


def find_repo_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    for p in [start, *start.parents]:
        if (p / ".git").exists():
            return p
    return start


def is_inside(path: Path, root: Path) -> bool:
    """True if path is inside root after `..` normalisation AND after following symlinks/junctions, so a
    link inside the repo that points elsewhere does not count as inside."""
    root = root.resolve()
    try:
        Path(os.path.normpath(path.absolute())).relative_to(root)
        path.resolve().relative_to(root)
        return True
    except (ValueError, OSError):
        return False


def contained(path: str | Path, root: Path, what: str = "path") -> Path:
    """Resolve path (relative to root) and reject it if it escapes root after `..` normalisation."""
    p = Path(path)
    if not p.is_absolute():
        p = root / p
    p = Path(os.path.normpath(p))
    if not is_inside(p, root):
        raise GuideGenError(f"{what} '{path}' resolves outside {root}; refused.", path=str(path))
    return p


def resolve_out(repo: Path, out: str | None) -> Path:
    return contained(out or DEFAULT_OUT, repo, "--out")


def init_out_dir(out: Path) -> bool:
    """Create the output folder with its own .gitignore. Returns True if created now."""
    created = not out.exists()
    (out / ".work").mkdir(parents=True, exist_ok=True)
    gi = out / ".gitignore"
    if not gi.exists() or gi.read_text(encoding="utf-8") in _OLD_OUT_GITIGNORES:
        gi.write_text(OUT_GITIGNORE, encoding="utf-8", newline="\n")
    return created


def restrict_to_user(path: Path) -> None:
    """Make a file readable only by the current user (session token file)."""
    if sys.platform == "win32":
        user = os.environ.get("USERNAME")
        if user:
            subprocess.run(
                ["icacls", str(path), "/inheritance:r", "/grant:r", f"{user}:F"],
                capture_output=True,
                check=False,
            )
    else:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def iter_repo_files(root: Path, patterns: tuple[str, ...] = ("*",), max_depth: int = 8):
    """Walk the repo skipping build/vendor/hidden folders."""
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        rel_depth = len(Path(dirpath).relative_to(root).parts)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        if rel_depth >= max_depth:
            dirnames[:] = []
        for f in filenames:
            p = Path(dirpath) / f
            if any(p.match(pat) for pat in patterns):
                yield p


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
