"""GuideGen engine CLI. Every command supports --json (machine output for the agent), --out <path>
(output folder, default guidegen-out/, must resolve inside the repo) and --repo <path>.
Exit codes: 0 ok, 2 hard blocker (the JSON explains what to ask the developer), 1 other error."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import typer

from guidegen_engine.context import Ctx
from guidegen_engine.errors import GuideGenError
from guidegen_engine.masking import mask

app = typer.Typer(add_completion=False, no_args_is_help=True, pretty_exceptions_enable=False,
                  help="GuideGen engine: detect, run, drive, capture and render end-user manuals.")
app_cmd = typer.Typer(no_args_is_help=True, help="Build/start/stop the target app.")
session_cmd = typer.Typer(no_args_is_help=True, help="Driver daemon for exploration.")
brand_cmd = typer.Typer(no_args_is_help=True, help="Branding.")
config_cmd = typer.Typer(no_args_is_help=True, help="guidegen.config.json helpers.")
manual_cmd = typer.Typer(no_args_is_help=True, help="manual.yaml helpers (comment-preserving).")
brief_cmd = typer.Typer(no_args_is_help=True, help="Read the developer's existing manual, outline or process.")
app.add_typer(app_cmd, name="app")
app.add_typer(session_cmd, name="session")
app.add_typer(brand_cmd, name="brand")
app.add_typer(config_cmd, name="config")
app.add_typer(manual_cmd, name="manual")
app.add_typer(brief_cmd, name="brief")

G: dict[str, Any] = {"json": False, "out": None, "repo": None}


def ctx() -> Ctx:
    from guidegen_engine.paths import init_out_dir

    c = Ctx.create(G["repo"], G["out"], G["json"])
    init_out_dir(c.out)  # the output folder (with its own .gitignore) is the only place we write
    return c


def emit(result: dict[str, Any]) -> None:
    result = mask(result)
    if G["json"]:
        print(json.dumps(result, indent=2, default=str))
    else:
        _human(result)
    if result.get("ok") is False:
        raise typer.Exit(1)


def _human(obj: Any, indent: int = 0) -> None:
    pad = "  " * indent
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("tree", "output") and isinstance(v, str):
                print(f"{pad}{k}:")
                for line in v.splitlines():
                    print(f"{pad}  {line}")
            elif isinstance(v, (dict, list)) and v:
                print(f"{pad}{k}:")
                _human(v, indent + 1)
            else:
                print(f"{pad}{k}: {v}")
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v, dict):
                print(f"{pad}-")
                _human(v, indent + 1)
            else:
                print(f"{pad}- {v}")
    else:
        print(f"{pad}{obj}")


def _cfg(c: Ctx):
    from guidegen_engine.config import load_config

    return load_config(c.config_path)


def _store(c: Ctx, create: bool = True):
    from guidegen_engine.manual import ManualStore

    return ManualStore.load(c.manual_path, create=create)


# ---------------- environment & detection ----------------
@app.command()
def doctor(no_install: bool = typer.Option(False, "--no-install", help="Do not install Playwright Chromium.")) -> None:
    """Check Python, uv, Playwright Chromium, OS and DPI."""
    from guidegen_engine.doctor import run_doctor

    emit(run_doctor(install=not no_install))


@app.command("detect")
def detect_cmd(repo: Path | None = typer.Argument(None, help="Repo root (default: current repo).")) -> None:
    """Detect app kind, build/start commands, URL or executable. Writes .work/detect.json."""
    from guidegen_engine.detect import detect

    if repo:
        G["repo"] = str(repo)
    c = ctx()  # also creates the output folder
    res = detect(c.repo)
    (c.work / "detect.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    emit(res)


@config_cmd.command("init")
def config_init(candidate: int | None = typer.Option(None, help="Rank of the detect candidate to use."),
                force: bool = typer.Option(False, help="Recreate even if a config exists.")) -> None:
    """Create guidegen.config.json from detection (+ brand detection)."""
    from guidegen_engine.configinit import init_config

    emit(init_config(ctx(), candidate, force))


@config_cmd.command("set")
def config_set(key: str, value: str) -> None:
    """Set a dotted key, e.g. `config set auth.required true`. VALUE is JSON or a plain string."""
    from guidegen_engine.configinit import set_value

    emit(set_value(ctx(), key, value))


@config_cmd.command("show")
def config_show() -> None:
    """Print the validated config."""
    emit({"ok": True, "config": _cfg(ctx()).dump()})


@app.command()
def validate() -> None:
    """Validate guidegen.config.json and manual.yaml (field-level errors)."""
    c = ctx()
    problems: list[dict[str, Any]] = []
    for name, fn in (("guidegen.config.json", lambda: _cfg(c)), ("manual.yaml", lambda: _store(c, create=False).model())):
        try:
            fn()
        except GuideGenError as e:
            problems.append({"file": name, "error": e.message, "errors": e.data.get("errors", [])})
    emit({"ok": not problems, "problems": problems})


# ---------------- app ----------------
@app_cmd.command("start")
def app_start(no_build: bool = typer.Option(False, "--no-build")) -> None:
    """Localhost guard, build, seed, start and wait until ready."""
    from guidegen_engine.app import controller

    c = ctx()
    emit(controller(c, _cfg(c)).start(build=not no_build))


@app_cmd.command("stop")
def app_stop() -> None:
    """Stop the app and its whole process tree."""
    from guidegen_engine.app import controller

    c = ctx()
    emit(controller(c, _cfg(c)).stop())


@app_cmd.command("status")
def app_status() -> None:
    from guidegen_engine.app import controller

    c = ctx()
    ctl = controller(c, _cfg(c))
    emit({"ok": True, "running": ctl.is_running(), **ctl.state()})


# ---------------- session / exploration ----------------
@session_cmd.command("start")
def session_start() -> None:
    """Start the driver daemon (127.0.0.1, random port + token). Starts the app if needed."""
    from guidegen_engine.session import client

    emit(client.start(ctx()))


@session_cmd.command("stop")
def session_stop() -> None:
    from guidegen_engine.session import client

    emit(client.stop(ctx()))


@session_cmd.command("status")
def session_status() -> None:
    from guidegen_engine.session import client

    info = client.running(ctx())
    emit({"ok": True, "running": bool(info), **({"port": info["port"], "kind": info["kind"]} if info else {})})


@app.command()
def act(action_json: str = typer.Argument(..., help='e.g. \'{"action":"click","target":{"by":"role","value":"link","name":"Orders"}}\'')) -> None:
    """Perform one action in the live session (destructive-action guard applies)."""
    from guidegen_engine.session import client

    try:
        action = json.loads(action_json)
    except json.JSONDecodeError as e:
        raise GuideGenError(f"action is not valid JSON: {e}") from e
    emit(client.call(ctx(), "act", {"action": action}))


@app.command()
def tree(depth: int = typer.Option(6, help="Max depth of the accessibility tree.")) -> None:
    """Accessibility tree of the current view, trimmed for tokens."""
    from guidegen_engine.session import client

    emit(client.call(ctx(), "tree", {"depth": depth}))


@app.command()
def shot(file: str | None = typer.Option(None, help="Path inside the output folder.")) -> None:
    """Redacted screenshot of the current view for the agent to look at."""
    from guidegen_engine.session import client

    emit(client.call(ctx(), "shot", {"file": file}))


@app.command()
def login(force: bool = typer.Option(False, help="Run loginSteps even if already logged in.")) -> None:
    """Run auth.loginSteps in the live session."""
    from guidegen_engine.session import client

    emit(client.call(ctx(), "login", {"force": force}))


@app.command()
def reset() -> None:
    """Return the live session to the start state (logged in)."""
    from guidegen_engine.session import client

    emit(client.call(ctx(), "reset", {}))


# ---------------- capture / update ----------------
@app.command()
def capture(only: list[str] | None = typer.Option(None, "--only", help="Screen/task id (repeatable)."),
            max_screens: int | None = typer.Option(None, "--max-screens"),
            max_tasks: int | None = typer.Option(None, "--max-tasks")) -> None:
    """Replay navigate/steps from manual.yaml and write redacted, annotated screenshots + capture-log.json."""
    from guidegen_engine.app import controller
    from guidegen_engine.capture import run_capture
    from guidegen_engine.drivers import make_driver
    from guidegen_engine.runtime import Session

    c = ctx()
    cfg = _cfg(c)
    if max_screens is not None:
        cfg.budget.max_screens = max_screens
    if max_tasks is not None:
        cfg.budget.max_tasks = max_tasks
    store = _store(c, create=False)
    ctl = controller(c, cfg)
    if not ctl.is_running():
        ctl.start()
    driver = make_driver(cfg, ctl)
    try:
        driver.launch()
        reseed = ctl.seed if (cfg.seed.enabled and cfg.seed.command and cfg.seed.rerun_before_tasks) else None
        res = run_capture(c, Session(cfg, driver), store, only=only, reseed=reseed)
    finally:
        driver.close()
    emit(res)


@app.command()
def changed() -> None:
    """Screens/tasks whose source changed since capture (for --update)."""
    from guidegen_engine.changed import changed as changed_fn

    c = ctx()
    emit(changed_fn(c.repo, _store(c, create=False).model()))


# ---------------- manual.yaml ----------------
@manual_cmd.command("init")
def manual_init(title: str | None = typer.Option(None)) -> None:
    """Create manual.yaml if missing."""
    c = ctx()
    store = _store(c)
    created = not c.manual_path.exists()
    if title:
        store.set_meta(title=title)
    store.save()
    emit({"ok": True, "created": created, "manual": str(c.manual_path)})


@manual_cmd.command("merge")
def manual_merge(file: str = typer.Argument(..., help="JSON or YAML patch file, or - for stdin.")) -> None:
    """Merge a patch (screens/tasks/troubleshooting upserted by id) preserving comments, override, exclude, locked."""
    from ruamel.yaml import YAML

    c = ctx()
    from guidegen_engine.paths import contained

    text = sys.stdin.read() if file == "-" else contained(file, c.repo, "patch file").read_text(encoding="utf-8")
    try:
        patch = json.loads(text)
    except json.JSONDecodeError:
        patch = YAML(typ="safe").load(text)
    if not isinstance(patch, dict):
        raise GuideGenError("patch must be a mapping")
    store = _store(c)
    stats = store.merge(patch)
    store.save()
    emit({"ok": True, **stats})


@manual_cmd.command("remove")
def manual_remove(
    collection: str = typer.Argument(..., help="screens | tasks | troubleshooting | briefGaps"),
    ident: str = typer.Argument(...),
    force: bool = typer.Option(False, "--force", help="Also remove an item that has developer edits (override/exclude/locked)."),
) -> None:
    """Remove one item (prefer `exclude: true` for anything a developer may want back)."""
    c = ctx()
    store = _store(c, create=False)
    ok = store.remove(collection, ident, force=force)
    store.save()
    emit({"ok": ok, "removed": ident if ok else None})


@manual_cmd.command("show")
def manual_show(ids_only: bool = typer.Option(False, "--ids")) -> None:
    """Print the validated manual (or just screen/task ids and statuses)."""
    m = _store(ctx(), create=False).model()
    if ids_only:
        emit({"ok": True, "screens": {s.id: s.status for s in m.screens}, "tasks": {t.id: t.status for t in m.tasks}})
    else:
        emit({"ok": True, "manual": m.dump()})


# ---------------- brief ----------------
@brief_cmd.command("extract")
def brief_extract(source: str = typer.Argument(..., help="File (.docx, .pdf, .md, .txt, .html) or http(s) URL.")) -> None:
    """Extract text + heading outline from an old manual, reference manual, outline or process document.
    Works before a config exists. Writes .work/brief/<name>.md with redactPatterns applied."""
    from guidegen_engine.brief import extract
    from guidegen_engine.config.models import SafetyConfig

    c = ctx()
    patterns = _cfg(c).safety.redact_patterns if c.config_path.exists() else SafetyConfig().redact_patterns
    emit(extract(c, source, patterns))


# ---------------- brand / render / report ----------------
@brand_cmd.command("detect")
def brand_detect(repo: Path | None = typer.Argument(None),
                 write: bool = typer.Option(False, "--write", help="Fill config.brand fields that are not set yet.")) -> None:
    """Find logo, product/company names, version and colors."""
    from guidegen_engine.brand import detect_brand
    from guidegen_engine.config import merge_config

    if repo:
        G["repo"] = str(repo)
    c = ctx()
    res = detect_brand(c.repo)
    if write:
        merge_config(c.config_path, {"brand": res["brand"]}, overwrite=False)
        res["written"] = True
    emit(res)


@app.command()
def render(format: str = typer.Option("docx,html", "--format"),
           html_single_file: bool = typer.Option(False, "--html-single-file")) -> None:
    """Build manual.docx and manual-html/ from manual.yaml + screens + brand."""
    from guidegen_engine.render import render as render_fn

    c = ctx()
    formats = [f.strip() for f in format.split(",") if f.strip()]
    bad = set(formats) - {"docx", "html"}
    if bad:
        raise GuideGenError(f"unknown format(s): {', '.join(bad)}")
    emit(render_fn(c, _cfg(c), _store(c, create=False).model(), formats, html_single_file))


@app.command()
def report() -> None:
    """Write run-report.md and print the final summary counts."""
    from guidegen_engine.report import write_report

    c = ctx()
    emit(write_report(c, _cfg(c), _store(c, create=False).model()))


@app.command("schema", hidden=True)
def schema_export(dest: Path | None = typer.Argument(None)) -> None:
    """Export JSON schemas for config and manual."""
    from guidegen_engine.config.models import Config
    from guidegen_engine.manual.models import Manual
    from guidegen_engine.paths import skill_dir

    d = dest or skill_dir() / "schema"
    d.mkdir(parents=True, exist_ok=True)
    for name, model in (("config.schema.json", Config), ("manual.schema.json", Manual)):
        sch = model.model_json_schema(by_alias=True)
        sch["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        (d / name).write_text(json.dumps(sch, indent=2) + "\n", encoding="utf-8", newline="\n")
    emit({"ok": True, "dir": str(d)})


# ---------------- entry ----------------
def _extract_globals(argv: list[str]) -> list[str]:
    rest: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--":  # everything after a bare -- is positional, even if it looks like a global flag
            rest += argv[i:]
            break
        if a == "--json":
            G["json"] = True
        elif a in ("--out", "--repo") and i + 1 < len(argv):
            G[a[2:]] = argv[i + 1]
            i += 1
        elif a.startswith(("--out=", "--repo=")):
            k, _, v = a.partition("=")
            G[k[2:]] = v
        else:
            rest.append(a)
        i += 1
    return rest


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    args = _extract_globals(sys.argv[1:])
    try:
        rc = app(args=args, prog_name="guidegen", standalone_mode=False)
        sys.exit(rc if isinstance(rc, int) else 0)
    except GuideGenError as e:
        out = mask(e.to_dict())
        if G["json"]:
            print(json.dumps(out, indent=2, default=str))
        else:
            print(f"error: {out.get('message') or out.get('error')}", file=sys.stderr)
            _human({k: v for k, v in out.items() if k not in ("ok", "error", "message")})
        sys.exit(e.exit_code)
    except typer.Exit as e:
        sys.exit(e.exit_code)
    except SystemExit:
        raise
    except Exception as e:  # usage errors from typer's (vendored) click
        if hasattr(e, "show") and hasattr(e, "exit_code"):
            e.show()
            sys.exit(e.exit_code)
        if type(e).__name__ == "Abort":
            sys.exit(1)
        # Unexpected failure: the agent still gets one masked JSON object (with --json), never a bare traceback.
        import traceback

        print(mask(traceback.format_exc()), file=sys.stderr)
        if G["json"]:
            print(json.dumps({"ok": False, "error": mask(f"{type(e).__name__}: {e}"), "exitCode": 1}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
