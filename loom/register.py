"""surfaces.json registration helper (ADR-060 §3.8).

Every Class-D product calls `register_surface(...)` at startup and
`deregister_surface(product)` on clean shutdown. The file is a shared,
0600, multi-writer registry, so writes are atomic (temp + replace) and
merge by product name (re-registering a product replaces its entry).

Cloud (Class C) products do NOT use this — they are discovered by the
account-server EPT query. This is loopback-local only.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_SURFACES_PATH = Path(os.path.expanduser("~/.windy/surfaces.json"))


def _read(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {"surfaces": []}


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)  # atomic on POSIX
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def register_surface(entry: dict[str, Any], path: Path | None = None) -> None:
    """Add/replace this product's entry. `entry` must carry at least
    product, version, contract, http (see schema/surfaces.v1.schema.json)."""
    p = path or DEFAULT_SURFACES_PATH
    data = _read(p)
    product = entry["product"]
    others = [s for s in data.get("surfaces", []) if s.get("product") != product]
    data["surfaces"] = others + [entry]
    _atomic_write(p, data)


def deregister_surface(product: str, path: Path | None = None) -> None:
    """Remove this product's entry (clean-shutdown courtesy; readers also
    treat a dead port as stale, so a crash that skips this is survivable)."""
    p = path or DEFAULT_SURFACES_PATH
    data = _read(p)
    data["surfaces"] = [s for s in data.get("surfaces", []) if s.get("product") != product]
    _atomic_write(p, data)
