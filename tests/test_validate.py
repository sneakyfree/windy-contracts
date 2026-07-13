"""Loom validator tests.

The first-citizen law (ADR-060 §4): windytalk's frozen rev.6 contracts must
validate AS-IS against manifest schema v1 — zero errors. Warnings are
allowed (they are the v1→v2 ramp: doctrine/product/class headers).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from loom.validate import BASELINE_13, validate_manifest

FIXTURES = Path(__file__).resolve().parent.parent / "schema" / "fixtures" / "windytalk"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


# ── first citizens ──────────────────────────────────────────────────


def test_talk_control_rev6_validates_as_is():
    r = validate_manifest(_load("control.mcp.v1.json"), path="control.mcp.v1.json")
    assert r.ok, r.errors
    # Frozen at 24 tools, five adversarial rounds — the floor holds.
    assert len(_load("control.mcp.v1.json")["tools"]) == 24


def test_talk_hands_v1_validates_as_is():
    r = validate_manifest(_load("hands.mcp.v1.json"), path="hands.mcp.v1.json")
    assert r.ok, r.errors


def test_talk_control_gets_migration_warnings_not_errors():
    r = validate_manifest(_load("control.mcp.v1.json"))
    joined = " ".join(r.warnings)
    for header in ("doctrine", "product", "class"):
        assert f"missing '{header}'" in joined


def test_talk_control_satisfies_the_13_knob_baseline():
    r = validate_manifest(_load("control.mcp.v1.json"))
    assert not any(w.startswith("baseline:") for w in r.warnings), [
        w for w in r.warnings if w.startswith("baseline:")
    ]


def test_hands_surface_is_exempt_from_baseline():
    r = validate_manifest(_load("hands.mcp.v1.json"))
    assert not any(w.startswith("baseline:") for w in r.warnings)


# ── error paths ─────────────────────────────────────────────────────


def _minimal() -> dict:
    return {
        "contract": "control.mcp.v1",
        "tools": [
            {
                "name": "get_health",
                "tier": "auto_allow",
                "description": "Full health snapshot with a plain-English summary to read aloud.",
                "inputSchema": {"type": "object", "properties": {}},
            }
        ],
    }


def test_minimal_manifest_is_legal():
    assert validate_manifest(_minimal()).ok


def test_bad_tier_is_an_error():
    m = _minimal()
    m["tools"][0]["tier"] = "yolo"
    r = validate_manifest(m)
    assert not r.ok and any("yolo" in e for e in r.errors)


def test_lazy_description_is_an_error():
    m = _minimal()
    m["tools"][0]["description"] = "does stuff"
    assert not validate_manifest(m).ok


def test_bad_tool_name_is_an_error():
    m = _minimal()
    m["tools"][0]["name"] = "Get-Health"
    assert not validate_manifest(m).ok


def test_duplicate_tool_names_are_an_error():
    m = _minimal()
    m["tools"].append(copy.deepcopy(m["tools"][0]))
    r = validate_manifest(m)
    assert not r.ok and any("duplicate" in e for e in r.errors)


def test_bad_contract_name_is_an_error():
    m = _minimal()
    m["contract"] = "ControlSurface"
    assert not validate_manifest(m).ok


def test_bad_band_floor_is_an_error():
    m = _minimal()
    m["tools"][0]["band_floor"] = "GODMODE"
    assert not validate_manifest(m).ok


# ── baseline coverage on non-first-citizen control surfaces ────────


def test_control_surface_missing_baseline_warns_per_knob():
    r = validate_manifest(_minimal())
    missing = [w for w in r.warnings if w.startswith("baseline:")]
    # get_health present; the other 12 baseline shapes absent.
    assert len(missing) == len(BASELINE_13) - 1


def test_ops_surface_gets_baseline_too():
    # Class C: the ops shim IS the cloud control surface (ADR-060 §2).
    m = _minimal()
    m["contract"] = "ops.mcp.v1"
    r = validate_manifest(m)
    assert any(w.startswith("baseline:") for w in r.warnings)


def test_companion_surfaces_skip_baseline():
    m = _minimal()
    m["contract"] = "hands.mcp.v1"
    r = validate_manifest(m)
    assert not any(w.startswith("baseline:") for w in r.warnings)


# ── the mapping table is well-formed ────────────────────────────────


def test_band_ei_mapping_parses_and_covers_all_bands():
    mapping = json.loads(
        (Path(__file__).resolve().parent.parent / "schema" / "band-ei-mapping.v1.json").read_text()
    )
    bands = [b["band"] for b in mapping["bands"]]
    assert bands == ["SANDBOX", "USER", "TRUSTED", "OWNER"]
    floor_keys = {k for k in mapping["band_floor_defaults"] if not k.startswith("$")}
    assert floor_keys == {"auto_allow", "ask_first", "always_confirm"}
    for b in mapping["bands"]:
        assert set(b["tiers"]) == {"auto_allow", "ask_first", "always_confirm"}


def test_conformance_suite_parses():
    conf = json.loads(
        (Path(__file__).resolve().parent.parent / "conformance" / "mcp-conformance.v1.json").read_text()
    )
    assert conf["cases"], "conformance suite must carry cases"
