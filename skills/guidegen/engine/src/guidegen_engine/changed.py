"""Source hashing for `--update`: which screens/tasks changed since they were captured."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from guidegen_engine.manual.models import Manual
from guidegen_engine.paths import contained


def hash_sources(repo: Path, sources: list[str]) -> str | None:
    if not sources:
        return None
    h = hashlib.sha256()
    for s in sorted(sources):
        h.update(s.encode())
        try:
            p = contained(s, repo, "source")
            data = p.read_bytes().replace(b"\r\n", b"\n") if p.is_file() else b"<missing>"
        except Exception:
            data = b"<outside-repo>"
        h.update(hashlib.sha256(data).digest())
    return "sha256:" + h.hexdigest()


def changed(repo: Path, manual: Manual) -> dict[str, Any]:
    stale_screens: list[dict[str, str]] = []
    unknown: list[str] = []
    for s in manual.screens:
        if s.exclude:
            continue
        current = hash_sources(repo, s.source)
        if s.status != "captured":
            stale_screens.append({"id": s.id, "reason": f"status {s.status}"})
        elif current is None:
            unknown.append(s.id)  # no `source` listed: cannot tell, keep the existing capture
        elif current != s.source_hash:
            stale_screens.append({"id": s.id, "reason": "source changed" if s.source_hash else "no sourceHash"})
    ids = {s["id"] for s in stale_screens}
    stale_tasks = []
    for t in manual.tasks:
        if t.exclude:
            continue
        used = {st.screen for st in t.steps if st.screen}
        hit = sorted(used & ids)
        if hit:
            stale_tasks.append({"id": t.id, "reason": f"uses changed screen(s): {', '.join(hit)}"})
        elif t.status not in ("captured",):
            stale_tasks.append({"id": t.id, "reason": f"status {t.status}"})
    return {
        "ok": True,
        "screens": stale_screens,
        "tasks": stale_tasks,
        "noSource": unknown,
        "only": sorted(ids | {t["id"] for t in stale_tasks}),
    }
