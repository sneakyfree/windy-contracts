"""Manifest validation — the Loom's gate.

Two severities, deliberately distinct:

- ERROR: the manifest violates control-manifest.v1.schema.json. The Loom
  refuses to weave; a platform's ``make check`` fails.
- WARNING: the manifest is legal v1 but misses something ADR-060 wants
  (doctrine/product/class headers, the 13-knob baseline on a control.*
  surface, missing ``returns``). Warnings are the v1→v2 migration ramp:
  visible every run, fatal only under ``--strict``.

Usage:
    uv run python -m loom.validate <manifest.json> [more.json ...] [--strict]
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "control-manifest.v1.schema.json"

# ADR-060 §3.4 — the minimum vocabulary a fire-fighting agent needs.
# set_<setting> is a shape, not a literal name: any set_* tool satisfies it.
BASELINE_13 = (
    "get_health",
    "get_status",
    "get_config",
    "get_logs",
    "run_selftest",
    "get_capabilities",
    "reconnect",
    "restart_app",
    "enter_safe_mode",
    "exit_safe_mode",
    "set_<setting>",
    "check_for_update",
    "apply_update",
    "reset_to_defaults",
)


@dataclass
class Report:
    path: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _load_schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text())


def validate_manifest(manifest: dict, *, path: str = "<memory>") -> Report:
    report = Report(path=path)
    validator = jsonschema.Draft202012Validator(_load_schema())
    for err in sorted(validator.iter_errors(manifest), key=lambda e: list(e.absolute_path)):
        where = "/".join(str(p) for p in err.absolute_path) or "<root>"
        report.errors.append(f"{where}: {err.message}")
    if report.errors:
        return report  # schema-invalid: doctrine checks would be noise

    # ── doctrine warnings (ADR-060, required in manifest v2) ──
    for key, cite in (("doctrine", "§8.6"), ("product", "§3.1"), ("class", "§2")):
        if key not in manifest:
            report.warnings.append(
                f"missing '{key}' header (ADR-060 {cite}; required in manifest v2)"
            )

    tools = manifest.get("tools", [])
    names = [t["name"] for t in tools]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        report.errors.append(f"duplicate tool names: {sorted(dupes)}")

    # 13-knob baseline — enforced (as warnings) on healing surfaces:
    # control.* (Class D/A) and ops.* (Class C — the ops shim IS the cloud
    # control surface, ADR-060 §2). Companion surfaces (hands.*, telemetry.*)
    # ride alongside a healing surface that carries the baseline.
    if manifest.get("contract", "").startswith(("control.", "ops.")):
        present = set(names)
        for knob in BASELINE_13:
            if knob == "set_<setting>":
                if not any(n.startswith("set_") for n in present):
                    report.warnings.append(
                        "baseline: no set_* tool (typed settings catalog with undo — ADR-060 §3.4)"
                    )
            elif knob not in present:
                report.warnings.append(
                    f"baseline: '{knob}' absent (ADR-060 §3.4 — implement or expose as tri-state unsupported)"
                )

    for t in tools:
        if "returns" not in t:
            report.warnings.append(
                f"tool '{t['name']}': no 'returns' schema — conformance can't assert its result shape"
            )

    return report


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    strict = "--strict" in args
    paths = [a for a in args if a != "--strict"]
    if not paths:
        print(__doc__)
        return 2

    worst = 0
    for p in paths:
        manifest = json.loads(Path(p).read_text())
        r = validate_manifest(manifest, path=p)
        n_tools = len(manifest.get("tools", []))
        status = "OK" if r.ok else "INVALID"
        print(f"[{status}] {p} — {n_tools} tools, {len(r.errors)} errors, {len(r.warnings)} warnings")
        for e in r.errors:
            print(f"  ERROR   {e}")
        for w in r.warnings:
            print(f"  warning {w}")
        if not r.ok or (strict and r.warnings):
            worst = 1
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
