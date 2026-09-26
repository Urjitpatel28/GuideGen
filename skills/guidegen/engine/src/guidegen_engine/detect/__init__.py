"""`guidegen detect`: heuristic project detection. The agent confirms the result; we never guess silently."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from guidegen_engine.paths import iter_repo_files, rel

NODE_WEB = [
    # dep, framework, default port, preferred scripts
    ("next", "nextjs", 3000, ("dev", "start")),
    ("@angular/core", "angular", 4200, ("start", "dev")),
    ("nuxt", "nuxt", 3000, ("dev",)),
    ("@sveltejs/kit", "sveltekit", 5173, ("dev",)),
    ("@vue/cli-service", "vue-cli", 8080, ("serve", "dev")),
    ("react-scripts", "create-react-app", 3000, ("start",)),
    ("vite", "vite", 5173, ("dev", "start")),
]


def _read_json(p: Path) -> dict[str, Any]:
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _pkg_manager(d: Path) -> str:
    if (d / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (d / "yarn.lock").exists():
        return "yarn"
    return "npm"


def _run(pm: str, script: str) -> str:
    return f"{pm} run {script}" if pm != "yarn" else f"yarn {script}"


def _port_from_script(script: str) -> int | None:
    m = re.search(r"(?:-p|--port)[ =](\d{2,5})", script)
    return int(m.group(1)) if m else None


def _vite_port(d: Path) -> int | None:
    for name in ("vite.config.ts", "vite.config.js", "vite.config.mjs", "vite.config.mts"):
        p = d / name
        if p.exists():
            m = re.search(r"port\s*:\s*(\d{2,5})", p.read_text(encoding="utf-8", errors="ignore"))
            if m:
                return int(m.group(1))
    return None


def detect_node(repo: Path, pkg: Path) -> dict[str, Any] | None:
    data = _read_json(pkg)
    if not data:
        return None
    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    scripts: dict[str, str] = data.get("scripts", {})
    d = pkg.parent
    pm = _pkg_manager(d)
    wd = rel(d, repo) or "."
    evidence = [f"{rel(pkg, repo)}"]

    if "electron" in deps:
        evidence.append("dependency electron")
        return {
            "kind": "electron",
            "framework": "electron",
            "project": rel(pkg, repo),
            "workingDir": wd,
            "build": f"{pm} install",
            "start": "npx electron .",
            "url": None,
            "executable": None,
            "confidence": 0.9,
            "evidence": evidence,
        }

    for dep, framework, port, prefer in NODE_WEB:
        if dep not in deps:
            continue
        script = next((s for s in prefer if s in scripts), None)
        if not script:
            continue
        evidence.append(f"dependency {dep}, script '{script}': {scripts[script]}")
        p = _port_from_script(scripts[script]) or (_vite_port(d) if framework == "vite" else None) or port
        if framework == "vite":
            framework = "vite-" + ("react" if "react" in deps else "vue" if "vue" in deps else "svelte" if "svelte" in deps else "app")
        url = f"http://localhost:{p}"
        return {
            "kind": "web",
            "framework": framework,
            "project": rel(pkg, repo),
            "workingDir": wd,
            "build": f"{pm} install",
            "start": _run(pm, script),
            "url": url,
            "readyWhen": {"url": url, "timeoutSec": 180},
            "executable": None,
            "confidence": 0.9,
            "evidence": evidence,
        }
    return None


def _xml_props(text: str) -> dict[str, str]:
    props: dict[str, str] = {}
    try:
        root = ET.fromstring(re.sub(r'\sxmlns="[^"]+"', "", text, count=1))
    except ET.ParseError:
        return props
    props["Sdk"] = root.attrib.get("Sdk", "")
    for pg in root.iter("PropertyGroup"):
        for child in pg:
            if child.text and child.tag not in props:
                props[child.tag] = child.text.strip()
    props["_packages"] = " ".join(pr.attrib.get("Include", "") for pr in root.iter("PackageReference"))
    return props


def _launch_url(proj_dir: Path) -> str | None:
    ls = _read_json(proj_dir / "Properties" / "launchSettings.json")
    for prof in (ls.get("profiles") or {}).values():
        if prof.get("commandName") == "Project" and prof.get("applicationUrl"):
            urls = prof["applicationUrl"].split(";")
            return next((u for u in urls if u.startswith("http://")), urls[0])
    return None


def detect_dotnet(repo: Path, csproj: Path) -> dict[str, Any] | None:
    text = csproj.read_text(encoding="utf-8", errors="ignore")
    props = _xml_props(text)
    d = csproj.parent
    name = props.get("AssemblyName") or csproj.stem
    project = rel(csproj, repo)
    is_test = "Microsoft.NET.Test.Sdk" in props["_packages"] or props.get("IsTestProject", "").lower() == "true"
    if is_test:
        return None
    tfm = props.get("TargetFramework") or (props.get("TargetFrameworks", "").split(";") or [""])[0]
    evidence = [project]
    sdk = props.get("Sdk", "")

    if sdk.startswith("Microsoft.NET.Sdk.Web") or sdk.startswith("Microsoft.NET.Sdk.Razor") and props.get("OutputType") == "Exe":
        razor = any(iter_repo_files(d, ("*.razor",)))  # skips bin/obj/node_modules, stops at the first hit
        framework = "blazor" if razor else "aspnet-razor-pages" if (d / "Pages").exists() else "aspnet-mvc"
        url = _launch_url(d) or "http://localhost:5000"
        evidence.append(f"Sdk={sdk}; framework heuristics -> {framework}")
        return {
            "kind": "web",
            "framework": framework,
            "project": project,
            "workingDir": ".",
            "build": f"dotnet build \"{project}\" -c Debug",
            "start": f"dotnet run --no-build --project \"{project}\" --urls {url}",
            "url": url,
            "readyWhen": {"url": url, "timeoutSec": 180},
            "executable": None,
            "confidence": 0.85,
            "evidence": evidence,
        }

    kind = None
    if props.get("UseWPF", "").lower() == "true":
        kind = "wpf"
    elif "Microsoft.WindowsAppSDK" in props["_packages"] or props.get("UseWinUI", "").lower() == "true":
        kind = "winui"
    elif props.get("UseWindowsForms", "").lower() == "true":
        kind = "winforms"
    if kind is None:
        return None
    if props.get("OutputType", "") not in ("WinExe", "Exe"):
        return None  # class library with WPF/WinForms controls
    evidence.append(f"{'UseWPF' if kind == 'wpf' else 'UseWindowsForms' if kind == 'winforms' else 'WindowsAppSDK'}; OutputType={props.get('OutputType')}")
    exe_dir = d / "bin" / "Debug" / tfm
    if props.get("RuntimeIdentifier"):
        exe_dir = exe_dir / props["RuntimeIdentifier"]
    return {
        "kind": kind,
        "framework": kind,
        "project": project,
        "workingDir": ".",
        "build": f"dotnet build \"{project}\" -c Debug",
        "start": None,
        "url": None,
        "executable": rel(exe_dir / f"{name}.exe", repo),
        "readyWhen": {"timeoutSec": 60},
        "confidence": 0.95 if kind != "winui" else 0.7,
        "evidence": evidence,
    }


def seed_candidates(repo: Path) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for p in iter_repo_files(repo, ("seed.ts", "seed.js", "seed.mjs", "seed.py")):
        out.append({"type": "seed-script", "ref": rel(p, repo)})
    for pkg in iter_repo_files(repo, ("package.json",)):
        for name in _read_json(pkg).get("scripts") or {}:
            if "seed" in name.lower():
                wd = rel(pkg.parent, repo) or "."
                prefix = "" if wd == "." else f"cd \"{wd}\" && "
                out.append({"type": "npm-script", "ref": f"{rel(pkg, repo)}#{name}", "command": f"{prefix}{_run(_pkg_manager(pkg.parent), name)}"})
    for proj in iter_repo_files(repo, ("*.csproj",)):
        if "seed" in proj.stem.lower():
            out.append({"type": "dotnet-project", "ref": rel(proj, repo), "command": f"dotnet run --project \"{rel(proj, repo)}\""})
    n = 0
    for cs in iter_repo_files(repo, ("*.cs",)):
        if n >= 5:
            break
        try:
            if ".HasData(" in cs.read_text(encoding="utf-8", errors="ignore"):
                out.append({"type": "ef-core-hasdata", "ref": rel(cs, repo)})
                n += 1
        except OSError:
            pass
    for sql in iter_repo_files(repo, ("*.sql",)):
        if any(part.lower() in ("seed", "seeds", "seeddata", "db", "database", "data") for part in sql.parts[-3:-1]):
            out.append({"type": "sql", "ref": rel(sql, repo)})
    return out[:20]


E2E_PATTERNS = ("*.spec.ts", "*.spec.js", "*.e2e.ts", "*.cy.ts", "*.cy.js", "*.test.tsx", "*.feature")
UI_TEST_PACKAGES = ("FlaUI", "Appium", "WinAppDriver", "Microsoft.Playwright", "Selenium", "TestStack.White")


def test_evidence(repo: Path) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for p in iter_repo_files(repo, ("playwright.config.*", "cypress.config.*")):
        out.append({"type": "e2e-config", "ref": rel(p, repo)})
    for p in iter_repo_files(repo, E2E_PATTERNS):
        out.append({"type": "e2e-test", "ref": rel(p, repo)})
    for proj in iter_repo_files(repo, ("*.csproj",)):
        text = proj.read_text(encoding="utf-8", errors="ignore")
        if "Microsoft.NET.Test.Sdk" in text and any(pk in text for pk in UI_TEST_PACKAGES):
            out.append({"type": "ui-test-project", "ref": rel(proj, repo)})
            for cs in iter_repo_files(proj.parent, ("*.cs",)):
                out.append({"type": "ui-test", "ref": rel(cs, repo)})
    return out[:60]


def auth_hints(repo: Path) -> list[str]:
    hints: list[str] = []
    pat = re.compile(r"log[-_]?in|sign[-_]?in|auth", re.I)
    exts = (".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte", ".cshtml", ".razor", ".xaml", ".cs", ".html")
    for p in iter_repo_files(repo, tuple(f"*{e}" for e in exts)):
        r = rel(p, repo)
        if pat.search(r) and "test" not in r.lower() and "/api/" not in f"/{r}":
            hints.append(r)
    return hints[:10]


def detect(repo: Path) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for pkg in iter_repo_files(repo, ("package.json",)):
        c = detect_node(repo, pkg)
        if c:
            candidates.append(c)
    for proj in iter_repo_files(repo, ("*.csproj",)):
        c = detect_dotnet(repo, proj)
        if c:
            candidates.append(c)
    candidates.sort(key=lambda c: (-c["confidence"], c["project"].count("/"), c["project"]))
    for i, c in enumerate(candidates):
        c["rank"] = i + 1
    graphify = (repo / "graphify-out" / "graph.json").exists() or (repo / "graphify-out" / "GRAPH_REPORT.md").exists()
    return {
        "ok": bool(candidates),
        "repo": str(repo),
        "candidates": candidates,
        "ambiguous": len(candidates) > 1,
        "seedCandidates": seed_candidates(repo),
        "testEvidence": test_evidence(repo),
        "authHints": auth_hints(repo),
        "graphify": graphify,
    }
