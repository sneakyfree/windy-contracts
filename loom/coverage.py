"""Coverage-parity checker — the L5 standing sentinel (ADR-060 §1, §9).

The coverage-parity law says: no dashboard-only actions — anything a human
can do exists as an agent-callable knob. This tool is how you KNOW a
platform's ops manifest is honest, by diffing it against the routes the
platform actually serves. Two findings, both load-bearing:

  - PHANTOM: a manifest tool bound to a route the platform does NOT serve.
    That's drift — an advertised knob that 404s. A bug, always.
  - UNCOVERED: a route the platform serves that is NOT in the manifest.
    A CANDIDATE, not a verdict — it may be a legit product route that stays
    out per §2 (Mind's /v1/chat, Search's /v1/search), or it may be an ops
    knob someone forgot to expose. A human classifies; the tool surfaces.

Pure logic: it takes a manifest and a list of the platform's routes (each
`{method, path}`), so it is fully testable and repo-agnostic. A best-effort
route extractor (`extract_routes_*`) is provided for FastAPI/Express so it's
runnable against a real repo, but the diff is what matters.

Usage:
    uv run python -m loom.coverage <manifest.json> <routes.json>
    # routes.json: [{"method":"GET","path":"/health"}, ...]
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Prefixes that are ALWAYS product/infra, never ops knobs — excluded from
# "uncovered" noise so the signal is the routes a human should actually judge.
_ALWAYS_PRODUCT_PREFIXES = (
    "/.well-known",
    "/_matrix",
    "/_synapse",
    "/webhooks",
    "/api/v1/webhooks",
    "/oauth",
    "/api/v1/oauth",
    "/.identity/callback",
)


def _norm(path: str) -> str:
    # Collapse path params so /accounts/{id} and /accounts/:id compare equal,
    # and trailing slashes don't split a route in two.
    p = re.sub(r"\{[^}]+\}", "{}", path)
    p = re.sub(r":[A-Za-z_][A-Za-z0-9_]*", "{}", p)
    p = p.rstrip("/") or "/"
    return p


@dataclass
class CoverageReport:
    product: str
    covered: list[str] = field(default_factory=list)      # manifest paths that exist
    phantom: list[str] = field(default_factory=list)      # manifest paths with NO matching route (BUG)
    uncovered: list[str] = field(default_factory=list)    # served routes not in manifest (candidates)
    native: bool = False

    @property
    def ok(self) -> bool:
        # Phantom bindings are always a failure; uncovered is advisory.
        return not self.phantom


def manifest_route_paths(manifest: dict) -> set[str]:
    """The normalized paths a manifest binds via transport. Empty for native
    servers (they project an in-process registry, not HTTP routes)."""
    out: set[str] = set()
    for t in manifest.get("tools", []):
        tr = t.get("transport")
        if tr and tr.get("path"):
            out.add(_norm(tr["path"]))
    return out


def coverage_report(
    manifest: dict,
    actual_routes: list[dict],
    *,
    ignore_product_prefixes: bool = True,
) -> CoverageReport:
    product = manifest.get("product", "?")
    native = manifest.get("server") == "native" or not manifest.get("tools", [{}])[0].get("transport")

    manifest_paths = manifest_route_paths(manifest)
    served = {_norm(r["path"]) for r in actual_routes if r.get("path")}

    report = CoverageReport(product=product, native=native)

    # Native servers bind no routes; a phantom/uncovered diff is meaningless.
    if native and not manifest_paths:
        report.native = True
        return report

    for mp in sorted(manifest_paths):
        (report.covered if mp in served else report.phantom).append(mp)

    def is_product(p: str) -> bool:
        return ignore_product_prefixes and any(p.startswith(_norm(pre)) for pre in _ALWAYS_PRODUCT_PREFIXES)

    for sp in sorted(served - manifest_paths):
        if not is_product(sp):
            report.uncovered.append(sp)

    return report


# ── best-effort route extraction (runnable convenience; the diff is canon) ──

_FASTAPI_RE = re.compile(r"""@(?:app|router)\.(get|post|put|delete|patch)\(\s*["']([^"']+)["']""")
_EXPRESS_RE = re.compile(r"""\.(get|post|put|delete|patch)\(\s*["']([^"']+)["']""")


def extract_routes_from_text(text: str) -> list[dict]:
    routes: list[dict] = []
    for rx in (_FASTAPI_RE, _EXPRESS_RE):
        for m in rx.finditer(text):
            method, path = m.group(1).upper(), m.group(2)
            if path.startswith("/"):
                routes.append({"method": method, "path": path})
    return routes


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print(__doc__)
        return 2
    manifest = json.loads(Path(args[0]).read_text())
    routes = json.loads(Path(args[1]).read_text())
    r = coverage_report(manifest, routes)
    status = "OK" if r.ok else "PHANTOM-BINDINGS"
    print(f"[{status}] {r.product} — {len(r.covered)} covered, "
          f"{len(r.phantom)} phantom, {len(r.uncovered)} uncovered candidates"
          + (" (native server)" if r.native else ""))
    for p in r.phantom:
        print(f"  PHANTOM  {p}  — manifest binds a route the platform does not serve (fix or remove)")
    for p in r.uncovered:
        print(f"  candidate {p}  — served but not in the ops manifest; ops knob or product route?")
    return 0 if r.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
