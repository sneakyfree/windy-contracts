"""Discovery + staleness — "land on a box, enumerate every knob" (ADR-060 §3.8, §5).

This is the reference reader an agent's harness runs. Two jobs:

  1. DISCOVER: read ~/.windy/surfaces.json, and PROBE BEFORE TRUST — a listed
     surface is believed only after its health check answers. A dead port is
     stale, not gospel (products should deregister on clean shutdown, but
     crashes don't, so the reader must not trust the file blindly).

  2. RECONCILE against the Steamroller's fleet version manifest: for each live
     surface, is it current, updatable, or below the supported minimum? The
     agent turns this into "your Windy Word has a fix available — want it?"

Pure logic: the caller injects a `probe` callable and the fleet manifest, so
this is fully testable without a live box or network. The default probe does a
loopback GET; supply your own for remote/EPT surfaces.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# A probe returns the surface's parsed health/version dict, or None if the
# surface did not answer (dead/stale entry).
Probe = Callable[[dict[str, Any]], "dict[str, Any] | None"]

DEFAULT_SURFACES_PATH = Path(os.path.expanduser("~/.windy/surfaces.json"))


@dataclass
class SurfaceStatus:
    product: str
    contract: str
    reachable: bool
    installed_version: str | None = None
    update: str | None = None            # "current" | "update-available" | "must-update" | "unknown"
    latest_version: str | None = None
    remediation: str | None = None       # the literal thing to do — the doctor pattern for updates
    detail: str = ""


@dataclass
class FleetReport:
    surfaces: list[SurfaceStatus] = field(default_factory=list)

    @property
    def reachable(self) -> list[SurfaceStatus]:
        return [s for s in self.surfaces if s.reachable]

    @property
    def needs_update(self) -> list[SurfaceStatus]:
        return [s for s in self.surfaces if s.update in ("update-available", "must-update")]

    def summary(self) -> str:
        live = len(self.reachable)
        stale = len(self.surfaces) - live
        upd = len(self.needs_update)
        parts = [f"{live} live surface(s)"]
        if stale:
            parts.append(f"{stale} listed-but-unreachable (stale)")
        if upd:
            parts.append(f"{upd} with updates available")
        return "; ".join(parts) + "."


def load_surfaces(path: Path | None = None) -> list[dict[str, Any]]:
    p = path or DEFAULT_SURFACES_PATH
    try:
        data = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    return data.get("surfaces", [])


def _semver_tuple(v: str) -> tuple:
    # Lenient: split on dots, numeric where possible, so "1.11.0" > "1.9.0"
    # and pre-release suffixes sort low. Not a full semver impl — enough to
    # compare our own version strings.
    out = []
    for part in str(v).replace("-", ".").split("."):
        out.append((0, int(part)) if part.isdigit() else (1, part))
    return tuple(out)


def _compare(installed: str, current: str, minimum: str | None) -> str:
    try:
        if minimum and _semver_tuple(installed) < _semver_tuple(minimum):
            return "must-update"
        if _semver_tuple(installed) < _semver_tuple(current):
            return "update-available"
        return "current"
    except Exception:
        return "unknown"


def reconcile(
    surfaces: list[dict[str, Any]],
    probe: Probe,
    fleet: dict[str, Any] | None = None,
    *,
    channel: str = "stable",
) -> FleetReport:
    """Probe each surface, then reconcile live ones against the fleet manifest."""
    report = FleetReport()
    products = (fleet or {}).get("products", {})

    for entry in surfaces:
        product = entry.get("product", "?")
        st = SurfaceStatus(product=product, contract=entry.get("contract", "?"), reachable=False)

        health = None
        try:
            health = probe(entry)
        except Exception as e:
            st.detail = f"probe raised: {e}"

        if not health:
            st.detail = st.detail or "listed in surfaces.json but did not answer — stale entry"
            report.surfaces.append(st)
            continue

        st.reachable = True
        st.installed_version = health.get("version") or entry.get("version")

        prod = products.get(product)
        chan = (prod or {}).get("channels", {}).get(channel)
        if not chan or not st.installed_version:
            st.update = "unknown"
            st.detail = "live; no fleet-version entry to compare against" if not chan else "live; version unknown"
            report.surfaces.append(st)
            continue

        st.latest_version = chan.get("current")
        st.update = _compare(st.installed_version, chan["current"], chan.get("minimum"))
        if st.update in ("update-available", "must-update"):
            kind = chan.get("kind", "native")
            src = chan.get("source", product)
            note = chan.get("notes", "")
            # The doctor pattern applied to updates: the remediation is the
            # literal command/action, so the agent can DO it, not just say it.
            st.remediation = {
                "npm": f"npx {src}@{chan['current']}",
                "r2": f"download + install {src} ({chan['current']})",
                "image": f"redeploy {product} to image {src}:{chan['current']}",
                "native": f"apply_update to {chan['current']} via {product}'s own control surface",
            }.get(kind, f"update {product} to {chan['current']}")
            st.detail = (f"{st.installed_version} → {chan['current']}"
                         + (f" — {note}" if note else "")
                         + (" (below supported minimum)" if st.update == "must-update" else ""))
        else:
            st.detail = f"up to date ({st.installed_version})"
        report.surfaces.append(st)

    return report
