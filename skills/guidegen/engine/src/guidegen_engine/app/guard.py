"""Localhost guard: refuse to run against anything but local backends unless safety.allowRemoteBackends."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from guidegen_engine.errors import HardBlocker
from guidegen_engine.paths import iter_repo_files, rel

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0", "[::1]", "(local)", ".", "host.docker.internal"}
SETTINGS_FILES = ("appsettings.json", "appsettings.Development.json", "appsettings.Local.json", ".env", ".env.local", ".env.development", ".env.development.local")
# Environment-specific files override the base appsettings.json in the same folder (ASP.NET layering).
APPSETTINGS_OVERRIDES = ("appsettings.Development.json", "appsettings.Local.json")
# .env keys we treat as backend locations. Third-party SaaS keys (analytics, DSNs) are not backends.
BACKEND_KEY = re.compile(
    r"(DATABASE|(^|_)DB(_|$)|CONN|MONGO|REDIS|POSTGRES|PG(HOST|_URL)|MYSQL|MSSQL|SQL|API_(URL|BASE)|BACKEND|SERVER_URL|(^|_)HOST$"
    r"|SUPABASE|FIREBASE|APPWRITE|HASURA|GRAPHQL|CONVEX|POCKETBASE)",  # hosted backends hold real data too
    re.I,
)
CONN_HOST_KEYS = ("server", "data source", "host", "address", "addr", "network address", "hostname")


def compose_services(repo: Path) -> set[str]:
    names: set[str] = set()
    for f in iter_repo_files(repo, ("docker-compose*.yml", "docker-compose*.yaml", "compose.yml", "compose.yaml"), max_depth=3):
        try:
            from ruamel.yaml import YAML

            data = YAML(typ="safe").load(f.read_text(encoding="utf-8")) or {}
            names |= set((data.get("services") or {}).keys())
        except Exception:
            continue
    return names


def host_of(value: str) -> str | None:
    """Extract a host from a URL or ADO/.NET-style connection string. None = not a network location."""
    v = value.strip().strip('"').strip("'")
    if not v:
        return None
    if "://" in v:
        u = urlparse(v)
        if u.scheme in ("file", "data"):
            return None
        host = u.hostname
        if host is None and "@" in v:  # e.g. postgres://user:pw@host:5432/db parsed oddly
            host = v.split("@", 1)[1].split("/", 1)[0].split(":", 1)[0]
        return host
    if "=" in v and ";" in v or v.lower().startswith(("server=", "data source=", "host=")):
        for part in v.split(";"):
            if "=" not in part:
                continue
            k, _, val = part.partition("=")
            if k.strip().lower() in CONN_HOST_KEYS:
                val = val.strip()
                if val.lower().startswith("tcp:"):
                    val = val[4:]
                if val.lower().startswith(("(localdb)", "(local)", ".")):
                    return "localhost"  # LocalDB, (local), .\SQLEXPRESS
                if re.search(r"\.(db|sqlite|sqlite3|mdf)$", val, re.I) or "/" in val:
                    return None  # file-based database (SQLite etc.)
                return re.split(r"[,:\\]", val)[0] or "localhost"
    return None


def is_local(host: str | None, services: set[str]) -> bool:
    if host is None:
        return True
    h = host.lower().strip("[]")
    return h in LOCAL_HOSTS or h in services or h.endswith(".localhost") or h.startswith("127.")


def _walk_json(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk_json(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_json(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def _overridden_keys(f: Path) -> set[str]:
    """Keys of the base appsettings.json that an environment-specific file next to it replaces."""
    keys: set[str] = set()
    for name in APPSETTINGS_OVERRIDES:
        o = f.with_name(name)
        if o.exists():
            try:
                keys |= {k.lower() for k, _ in _walk_json(json.loads(o.read_text(encoding="utf-8-sig", errors="ignore")))}
            except (json.JSONDecodeError, OSError):
                continue
    return keys


def scan_settings(repo: Path) -> list[dict[str, str]]:
    """Every backend location found in local settings files: [{file, key, host}]."""
    found: list[dict[str, str]] = []
    for f in iter_repo_files(repo, SETTINGS_FILES, max_depth=5):
        if f.name not in SETTINGS_FILES:
            continue
        try:
            text = f.read_text(encoding="utf-8-sig", errors="ignore")
        except OSError:
            continue
        if f.suffix == ".json":
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                continue
            base = f.name == "appsettings.json"
            skip = _overridden_keys(f) if base else set()
            for key, val in _walk_json(data):
                if key.lower() in skip:
                    continue
                in_conn = key.lower().startswith("connectionstrings")
                # the base file also holds unrelated third-party URLs, so only backend keys count there
                if in_conn or BACKEND_KEY.search(key.split(".")[-1]) or (not base and "://" in val):
                    h = host_of(val)
                    if h:
                        found.append({"file": rel(f, repo), "key": key, "host": h})
        else:
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.replace("export ", "").strip()
                if BACKEND_KEY.search(key):
                    h = host_of(val)
                    if h:
                        found.append({"file": rel(f, repo), "key": key, "host": h})
    return found

def check_localhost(repo: Path, app_url: str | None, allow_remote: bool) -> list[dict[str, str]]:
    """Raise HardBlocker(safety) on the first remote backend. Returns what was checked (for the report)."""
    services = compose_services(repo)
    checked: list[dict[str, str]] = []
    if app_url:
        checked.append({"file": "guidegen.config.json", "key": "app.url", "host": urlparse(app_url).hostname or ""})
    checked += scan_settings(repo)
    if allow_remote:
        return checked
    for c in checked:
        if not is_local(c["host"], services):
            raise HardBlocker(
                "safety",
                f"{c['file']} ({c['key']}) points to non-local host '{c['host']}'.",
                question=(
                    f"GuideGen only runs against local backends so it cannot touch real data. Point {c['key']} in "
                    f"{c['file']} at a local/test instance, or - if you are sure '{c['host']}' is a disposable test "
                    "backend - say so and I'll set safety.allowRemoteBackends=true in guidegen-out/guidegen.config.json."
                ),
                tried=["checked app.url and local settings files for backend hosts"],
                save_to="safety.allowRemoteBackends",
                file=c["file"],
                host=c["host"],
            )
    return checked
