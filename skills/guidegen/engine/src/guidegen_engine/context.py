"""Run context shared by all commands: repo root, output folder, json mode."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from guidegen_engine.paths import find_repo_root, resolve_out


@dataclass
class Ctx:
    repo: Path
    out: Path
    json: bool = False

    @property
    def work(self) -> Path:
        return self.out / ".work"

    @property
    def config_path(self) -> Path:
        return self.out / "guidegen.config.json"

    @property
    def manual_path(self) -> Path:
        return self.out / "manual.yaml"

    @property
    def screens_dir(self) -> Path:
        return self.out / "screens"

    @classmethod
    def create(cls, repo: str | None = None, out: str | None = None, json: bool = False) -> Ctx:
        # An explicit --repo is taken as-is (e.g. an example app inside a bigger repo); otherwise the git root.
        root = Path(repo).resolve() if repo else find_repo_root()
        return cls(repo=root, out=resolve_out(root, out), json=json)
