"""Round-trip load/save of manual.yaml with ruamel.yaml.

Pydantic validates a plain copy; every write patches the ruamel tree in place so developer comments,
key order and formatting survive. Keys in PROTECTED (and any key an item lists in `locked`) are never
changed once present - that is how developer edits survive regeneration.
"""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from ruamel.yaml import YAML
from pydantic.alias_generators import to_camel
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from guidegen_engine.errors import GuideGenError
from guidegen_engine.manual.models import Manual

PROTECTED = {"override", "exclude", "locked"}
# list key -> identity field. Top-level collections are upserted; nested ones follow the patch order.
KEYED_LISTS = {"screens": "id", "tasks": "id", "troubleshooting": "message", "briefGaps": "item",
               "steps": "id", "elements": "name", "chapters": "id"}
TOP_LEVEL_UPSERT = {"screens", "tasks", "troubleshooting", "briefGaps"}

HEADER = (
    "# GuideGen manual source. Edit freely: set `override:` to replace generated text, `exclude: true`\n"
    "# to drop a screen/task/entry, or `locked: [title]` to keep fields you edited. GuideGen never\n"
    "# changes override/exclude/locked. Re-run `/guidegen --update` to refresh.\n"
)


def _yaml() -> YAML:
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    y.indent(mapping=2, sequence=4, offset=2)
    return y


def camelize(obj: Any) -> Any:
    """Accept snake_case keys from agent patches; the file always uses camelCase."""
    if isinstance(obj, dict):
        return {(to_camel(k) if isinstance(k, str) and "_" in k else k): camelize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [camelize(v) for v in obj]
    return obj


def to_plain(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_plain(v) for v in obj]
    return obj


def to_cm(value: Any, key: str | None = None) -> Any:
    """Convert plain data to ruamel nodes; small action/target/evidence maps are written in flow style."""
    if isinstance(value, dict):
        cm = CommentedMap()
        for k, v in value.items():
            cm[k] = to_cm(v, k)
        if key in ("action", "target") or key in ("navigate", "evidence", "loginSteps"):
            cm.fa.set_flow_style()
        return cm
    if isinstance(value, (list, tuple)):
        seq = CommentedSeq()
        for v in value:
            seq.append(to_cm(v, key))
        if key == "locked" or (key == "source"):
            seq.fa.set_flow_style()
        return seq
    return value


class ManualStore:
    def __init__(self, path: Path, data: CommentedMap) -> None:
        self.path = path
        self.data = data

    # ---------- io ----------
    @classmethod
    def load(cls, path: Path, create: bool = True) -> ManualStore:
        if path.exists():
            data = _yaml().load(path.read_text(encoding="utf-8")) or CommentedMap()
            if not isinstance(data, CommentedMap):
                raise GuideGenError(f"{path.name} must be a YAML mapping")
            return cls(path, data)
        if not create:
            raise GuideGenError(f"{path} does not exist. Run `guidegen manual init`.")
        data = to_cm(Manual().dump())
        data.yaml_set_start_comment(HEADER)
        return cls(path, data)

    def dumps(self) -> str:
        buf = io.StringIO()
        _yaml().dump(self.data, buf)
        return buf.getvalue()

    def save(self) -> None:
        self.model()  # never write a manual that does not validate
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self.dumps(), encoding="utf-8", newline="\n")

    def model(self) -> Manual:
        try:
            m = Manual.model_validate(to_plain(self.data))
        except ValidationError as e:
            raise GuideGenError(
                f"{self.path.name} is invalid",
                errors=[{"field": ".".join(str(p) for p in err["loc"]), "message": err["msg"]} for err in e.errors()],
            ) from e
        dup = m.duplicate_ids()
        if dup:
            raise GuideGenError(f"duplicate ids in {self.path.name}: {', '.join(dup)}")
        return m

    # ---------- lookup ----------
    def collection(self, name: str) -> CommentedSeq:
        if name not in self.data or self.data[name] is None:
            self.data[name] = CommentedSeq()
        return self.data[name]

    def find(self, name: str, ident: str) -> CommentedMap | None:
        key = KEYED_LISTS[name]
        return next((x for x in self.collection(name) if isinstance(x, dict) and x.get(key) == ident), None)

    # ---------- engine writes ----------
    def set_fields(self, name: str, ident: str, **fields: Any) -> None:
        """Set engine-owned fields on one item (status, image, sourceHash...). Protected keys are ignored."""
        item = self.find(name, ident)
        if item is None:
            raise GuideGenError(f"{name} item '{ident}' not found")
        _set(item, fields)

    def set_step_fields(self, task_id: str, step_id: str, **fields: Any) -> None:
        task = self.find("tasks", task_id)
        if task is None:
            raise GuideGenError(f"task '{task_id}' not found")
        step = next((s for s in task.get("steps") or [] if s.get("id") == step_id), None)
        if step is None:
            raise GuideGenError(f"step '{step_id}' not found in task '{task_id}'")
        _set(step, fields)

    def set_meta(self, **fields: Any) -> None:
        if "meta" not in self.data:
            self.data["meta"] = CommentedMap()
        _set(self.data["meta"], fields)

    # ---------- agent writes ----------
    def merge(self, patch: dict[str, Any]) -> dict[str, int]:
        """Deep-merge a patch (as the agent produces it) into the manual. Returns counts of added/updated."""
        stats = {"added": 0, "updated": 0}
        patch = camelize(patch)
        for k, v in patch.items():
            if k in TOP_LEVEL_UPSERT and isinstance(v, list):
                key = KEYED_LISTS[k]
                coll = self.collection(k)
                for item in v:
                    existing = self.find(k, item.get(key))
                    if existing is None:
                        coll.append(to_cm(item, k))
                        stats["added"] += 1
                    else:
                        _merge_map(existing, item)
                        stats["updated"] += 1
            elif k == "chapters" and isinstance(v, list) and isinstance(self.data.get(k), list):
                # the patch decides chapter order and membership; existing chapters keep override/exclude/locked
                self.data[k] = _merge_keyed(self.data[k], v, "id", k)
            elif isinstance(v, dict) and isinstance(self.data.get(k), dict):
                _merge_map(self.data[k], v)
            else:
                self.data[k] = to_cm(v, k)
        return stats

    def remove(self, name: str, ident: str, force: bool = False) -> bool:
        if name not in KEYED_LISTS or name not in TOP_LEVEL_UPSERT:
            raise GuideGenError(f"unknown collection '{name}' (use one of: {', '.join(sorted(TOP_LEVEL_UPSERT))})")
        item = self.find(name, ident)
        if item is None:
            return False
        if _has_protected(item) and not force:
            raise GuideGenError(
                f"{name} item '{ident}' has developer edits (override/exclude/locked); refusing to remove it. "
                "Set `exclude: true` instead, or pass --force if the developer asked for removal."
            )
        self.collection(name).remove(item)
        return True


def _set(item: CommentedMap, fields: dict[str, Any]) -> None:
    locked = set(item.get("locked") or [])
    for k, v in fields.items():
        if (k in PROTECTED and k in item) or k in locked:
            continue
        if isinstance(v, datetime):
            v = v.replace(microsecond=0)
        if v is None and k not in item:
            continue
        if isinstance(v, dict) and isinstance(item.get(k), dict):
            _merge_map(item[k], v)  # nested maps are merged so protected keys inside survive
        else:
            item[k] = to_cm(v, k)


def _merge_map(dst: CommentedMap, src: dict[str, Any]) -> None:
    locked = set(dst.get("locked") or [])
    for k, v in src.items():
        if (k in PROTECTED and k in dst) or k in locked:
            continue
        cur = dst.get(k)
        if isinstance(v, dict) and isinstance(cur, dict):
            _merge_map(cur, v)
        elif isinstance(v, list) and k in KEYED_LISTS and isinstance(cur, list):
            dst[k] = _merge_keyed(cur, v, KEYED_LISTS[k], k)
        else:
            dst[k] = to_cm(v, k)


def _has_protected(item: Any) -> bool:
    """True when the developer customised an item (override text, exclude flag or locked fields)."""
    return isinstance(item, dict) and any(item.get(k) not in (None, False, [], "") for k in PROTECTED)


def _merge_keyed(cur: list, new: list, key: str, list_key: str) -> CommentedSeq:
    """Nested keyed list: the patch decides order/membership, existing items keep their protected fields.

    Items the patch leaves out are dropped, except ones the developer customised (override/exclude/locked):
    those stay near their old position, so regeneration never silently deletes a developer edit.
    """
    by_id = {x.get(key): x for x in cur if isinstance(x, dict)}
    out = CommentedSeq()
    sent = set()
    for item in new:
        existing = by_id.get(item.get(key)) if isinstance(item, dict) else None
        if isinstance(item, dict):
            sent.add(item.get(key))
        if existing is not None:
            _merge_map(existing, item)
            out.append(existing)
        else:
            out.append(to_cm(item, list_key))
    for pos, x in enumerate(cur):
        if isinstance(x, dict) and x.get(key) not in sent and _has_protected(x):
            out.insert(min(pos, len(out)), x)
    return out
