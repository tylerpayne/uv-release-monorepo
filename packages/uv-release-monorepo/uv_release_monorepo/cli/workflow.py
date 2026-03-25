"""The ``uvr workflow`` command and shared YAML CRUD engine."""

from __future__ import annotations

import argparse
import sys
from io import StringIO
from pathlib import Path
from typing import Any

from ..models import ReleaseWorkflow
from ._common import _fatal
from ._yaml import _MISSING, _yaml_delete, _yaml_get, _yaml_set

# Sentinel: when ``nargs="?"`` fires with no value, argparse stores ``const``.
_STDIN = "__STDIN__"


def _load_yaml(path: Path) -> dict:
    """Load a YAML file using ruamel.yaml (preserves order, quotes, comments)."""
    from ruamel.yaml import YAML

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 2**31
    with open(path) as f:
        doc = yaml.load(f)
    return doc or {}


def _dump_yaml(doc: Any) -> str:
    """Serialize a dict to YAML string using ruamel.yaml."""
    from ruamel.yaml import YAML

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 2**31  # effectively infinite -- never line-wrap
    stream = StringIO()
    yaml.dump(doc, stream)
    return stream.getvalue()


def _write_yaml(path: Path, doc: dict) -> None:
    """Write a dict to a YAML file using ruamel.yaml."""
    path.write_text(_dump_yaml(doc))


def _parse_path(path_str: str | None) -> list[str]:
    """Parse a jq-style dot path into a list of keys.

    ``".permissions.contents"`` -> ``["permissions", "contents"]``
    ``""`` or ``None`` -> ``[]``
    """
    if not path_str:
        return []
    # Strip leading dot
    s = path_str.lstrip(".")
    if not s:
        return []
    return [seg for seg in s.split(".") if seg]


def _parse_yaml_value(raw: str) -> Any:
    """Parse a CLI value string as YAML (supports scalars, lists, dicts)."""
    from ruamel.yaml import YAML

    yaml = YAML()
    return yaml.load(raw)


def _read_stdin_value() -> Any:
    """Read YAML from stdin and parse it."""
    raw = sys.stdin.read()
    if not raw.strip():
        _fatal("No input received from stdin.")
    return _parse_yaml_value(raw)


def _resolve_value(raw_value: str | None) -> Any:
    """Resolve a flag value: if it's the _STDIN sentinel, read from stdin.

    If it's a string, parse as YAML. If None, read stdin.
    """
    if raw_value is None or raw_value == _STDIN:
        return _read_stdin_value()
    return _parse_yaml_value(raw_value)


def _has_stdin_data() -> bool:
    """Return True if stdin is a pipe or file redirect (not a tty or char device)."""
    import os
    import stat

    try:
        mode = os.fstat(sys.stdin.fileno()).st_mode
        return stat.S_ISFIFO(mode) or stat.S_ISREG(mode)
    except (OSError, ValueError, AttributeError):
        return False


def _dump_value(val: Any) -> str:
    """Pretty-print a YAML value for terminal output."""
    if isinstance(val, (dict, list)):
        return _dump_yaml(val).rstrip()
    return str(val)


def _yaml_crud(  # noqa: C901, PLR0912
    release_yml: Path,
    doc: dict,
    args: argparse.Namespace,
) -> None:
    """Shared CRUD engine for ``uvr workflow`` and ``uvr hooks``.

    Reads ``args.path``, ``args.set_value``, ``args.append_value``,
    ``args.insert_value``, ``args.remove_value``, ``args.at_index``,
    and ``args.clear`` to determine the operation.
    """
    path_str: str | None = getattr(args, "path", None)
    parts = _parse_path(path_str)

    set_value: str | None = getattr(args, "set_value", None)
    append_value: str | None = getattr(args, "append_value", None)
    insert_value: str | None = getattr(args, "insert_value", None)
    remove_value: str | None = getattr(args, "remove_value", None)
    at_index: int | None = getattr(args, "at_index", None)
    clear: bool = getattr(args, "clear", False)

    has_flag = (
        set_value is not None
        or append_value is not None
        or insert_value is not None
        or remove_value is not None
        or clear
    )

    has_stdin = _has_stdin_data()

    def _validate_and_write() -> None:
        from pydantic import ValidationError

        try:
            model = ReleaseWorkflow.model_validate(dict(doc))
        except ValidationError as e:
            _fatal(f"Invalid workflow structure:\n{e}")
        _write_yaml(release_yml, model.model_dump(by_alias=True, exclude_none=True))

    # No flag and no stdin -> read
    # No flag and stdin -> set from stdin
    if not has_flag:
        if has_stdin:
            # Set from stdin
            if not parts:
                _fatal("Cannot set root from stdin. Provide a path.")
            value = _read_stdin_value()
            _yaml_set(doc, parts, value)
            _validate_and_write()
            print(f"Set '{path_str}' from stdin.")
            return
        # Read
        if not parts:
            print(_dump_value(doc))
            return
        val = _yaml_get(doc, parts)
        if val is not _MISSING:
            print(_dump_value(val))
        else:
            print(f"'{path_str}': not found")
        return

    # --clear
    if clear:
        if not parts:
            _fatal("Cannot clear the root document.")
        current = _yaml_get(doc, parts)
        if current is _MISSING:
            print(f"'{path_str}': not found")
            return
        # Empty the collection (list -> [], dict -> {}) or delete scalar
        if isinstance(current, list):
            current.clear()
        elif isinstance(current, dict):
            current.clear()
        else:
            _yaml_delete(doc, parts)
        _validate_and_write()
        print(f"Cleared '{path_str}'.")
        return

    # --set
    if set_value is not None:
        if not parts:
            _fatal("Cannot set the root document.")
        value = _resolve_value(set_value)
        if at_index is not None:
            # --set with --at: update element in list
            target = _yaml_get(doc, parts)
            if target is _MISSING:
                _fatal(f"'{path_str}': not found")
            if not isinstance(target, list):
                _fatal(f"'{path_str}' is not a list (got {type(target).__name__})")
            if at_index < 0 or at_index >= len(target):
                _fatal(
                    f"Index {at_index} out of range for list of length {len(target)}"
                )
            target[at_index] = value
        else:
            _yaml_set(doc, parts, value)
        _validate_and_write()
        print(f"Set '{path_str}'.")
        return

    # --append
    if append_value is not None:
        if not parts:
            _fatal("Cannot append to the root document.")
        value = _resolve_value(append_value)
        current = _yaml_get(doc, parts)
        if current is _MISSING:
            _yaml_set(doc, parts, [value])
        elif isinstance(current, list):
            current.append(value)
        else:
            _fatal(f"'{path_str}' is not a list (got {type(current).__name__})")
        _validate_and_write()
        print(f"Appended to '{path_str}'.")
        return

    # --insert (requires --at)
    if insert_value is not None:
        if not parts:
            _fatal("Cannot insert into the root document.")
        if at_index is None:
            _fatal("--insert requires --at INDEX")
        value = _resolve_value(insert_value)
        current = _yaml_get(doc, parts)
        if current is _MISSING:
            _yaml_set(doc, parts, [value])
        elif isinstance(current, list):
            current.insert(at_index, value)
        else:
            _fatal(f"'{path_str}' is not a list (got {type(current).__name__})")
        _validate_and_write()
        print(f"Inserted into '{path_str}' at index {at_index}.")
        return

    # --remove
    if remove_value is not None:
        if not parts:
            _fatal("Cannot remove from the root document.")
        if at_index is not None:
            # Remove by index from list
            current = _yaml_get(doc, parts)
            if current is _MISSING:
                _fatal(f"'{path_str}': not found")
            if not isinstance(current, list):
                _fatal(f"'{path_str}' is not a list (got {type(current).__name__})")
            if at_index < 0 or at_index >= len(current):
                _fatal(
                    f"Index {at_index} out of range for list of length {len(current)}"
                )
            current.pop(at_index)
            _validate_and_write()
            print(f"Removed index {at_index} from '{path_str}'.")
            return
        # remove_value is _STDIN sentinel means no value provided, which
        # is an error for --remove without --at
        if remove_value == _STDIN:
            _fatal("--remove requires a VALUE or --at INDEX")
        # Remove key from dict or value from list
        value = _parse_yaml_value(remove_value)
        current = _yaml_get(doc, parts)
        if current is _MISSING:
            _fatal(f"'{path_str}': not found")
        if isinstance(current, dict):
            key = str(value)
            if key not in current:
                _fatal(f"Key '{key}' not found in '{path_str}'")
            current.pop(key)
        elif isinstance(current, list):
            try:
                current.remove(value)
            except ValueError:
                _fatal(f"'{remove_value}' not found in '{path_str}'")
        else:
            _fatal(f"'{path_str}' is not a dict or list (got {type(current).__name__})")
        _validate_and_write()
        print(f"Removed from '{path_str}'.")
        return


def cmd_workflow(args: argparse.Namespace) -> None:
    """Read, write, or delete any key in the release workflow YAML."""
    root = Path.cwd()
    workflow_dir = getattr(args, "workflow_dir", ".github/workflows")
    release_yml = root / workflow_dir / "release.yml"
    if not release_yml.exists():
        _fatal("No release.yml found. Run `uvr init` first to generate the workflow.")

    doc = _load_yaml(release_yml)
    _yaml_crud(release_yml, doc, args)
