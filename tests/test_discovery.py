"""Discovery + Steamroller reconcile — 'land on a box, enumerate every knob'.

Proves the reference reader (loom/discovery.py) + the registry writer
(loom/register.py): probe-before-trust (a dead surface reads as stale, not
gospel), version reconciliation against the fleet manifest, and the update
remediation being the LITERAL action (the doctor pattern for updates).
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from loom.discovery import load_surfaces, reconcile
from loom.register import deregister_surface, register_surface

ROOT = Path(__file__).resolve().parent.parent


# ── the fleet version manifest is well-formed ───────────────────────


def test_fleet_version_schema_accepts_a_real_manifest():
    schema = json.loads((ROOT / "schema" / "fleet-version.v1.schema.json").read_text())
    manifest = {
        "schema_version": "fleet-version.v1",
        "products": {
            "windy-word": {
                "doctrine": "ADR-060 v1.0",
                "channels": {
                    "stable": {
                        "current": "1.11.0",
                        "minimum": "1.10.0",
                        "kind": "npm",
                        "source": "windy-word-mcp",
                        "notes": "closes the token drive-by",
                    }
                },
            }
        },
    }
    jsonschema.Draft202012Validator(schema).validate(manifest)


# ── registration (surfaces.json writer) ─────────────────────────────


def test_register_and_deregister_roundtrip(tmp_path):
    p = tmp_path / "surfaces.json"
    register_surface(
        {"product": "windy-word", "version": "1.7.0", "contract": "control.mcp.v1",
         "http": "http://127.0.0.1:18765", "token_path": "~/.windy-word/control.token"},
        path=p,
    )
    register_surface(
        {"product": "windy-talk", "version": "0.9.0", "contract": "control.mcp.v1",
         "http": "http://127.0.0.1:8782"},
        path=p,
    )
    surfaces = load_surfaces(p)
    assert {s["product"] for s in surfaces} == {"windy-word", "windy-talk"}
    assert oct(p.stat().st_mode)[-3:] == "600"

    # re-register replaces, never duplicates
    register_surface(
        {"product": "windy-word", "version": "1.8.0", "contract": "control.mcp.v1",
         "http": "http://127.0.0.1:18765"},
        path=p,
    )
    surfaces = load_surfaces(p)
    words = [s for s in surfaces if s["product"] == "windy-word"]
    assert len(words) == 1 and words[0]["version"] == "1.8.0"

    deregister_surface("windy-word", path=p)
    assert {s["product"] for s in load_surfaces(p)} == {"windy-talk"}


def test_load_surfaces_missing_file_is_empty(tmp_path):
    assert load_surfaces(tmp_path / "nope.json") == []


# ── probe-before-trust ──────────────────────────────────────────────

FLEET = {
    "products": {
        "windy-word": {"channels": {"stable": {
            "current": "1.11.0", "minimum": "1.10.0", "kind": "npm", "source": "windy-word-mcp",
            "notes": "closes the token drive-by"}}},
        "windy-mind": {"channels": {"stable": {
            "current": "0.2.0", "minimum": "0.1.0", "kind": "image", "source": "windy-mind-api"}}},
    }
}


def test_dead_surface_reads_as_stale_not_trusted():
    surfaces = [{"product": "windy-word", "contract": "control.mcp.v1", "version": "1.7.0",
                 "http": "http://127.0.0.1:18765"}]
    # probe returns None → surface did not answer
    report = reconcile(surfaces, probe=lambda e: None, fleet=FLEET)
    assert report.reachable == []
    assert "stale" in report.surfaces[0].detail
    assert report.surfaces[0].reachable is False


def test_live_but_outdated_gets_literal_remediation():
    surfaces = [{"product": "windy-word", "contract": "control.mcp.v1",
                 "http": "http://127.0.0.1:18765"}]
    # probe answers with the installed version
    report = reconcile(surfaces, probe=lambda e: {"version": "1.10.0", "status": "ok"}, fleet=FLEET)
    st = report.surfaces[0]
    assert st.reachable and st.update == "update-available"
    assert st.latest_version == "1.11.0"
    assert st.remediation == "npx windy-word-mcp@1.11.0"   # the doctor pattern: literal action
    assert "closes the token drive-by" in st.detail


def test_below_minimum_is_must_update():
    surfaces = [{"product": "windy-word", "contract": "control.mcp.v1",
                 "http": "http://127.0.0.1:18765"}]
    report = reconcile(surfaces, probe=lambda e: {"version": "1.9.0"}, fleet=FLEET)
    st = report.surfaces[0]
    assert st.update == "must-update"
    assert "below supported minimum" in st.detail


def test_current_version_is_not_flagged():
    surfaces = [{"product": "windy-word", "contract": "control.mcp.v1",
                 "http": "http://127.0.0.1:18765"}]
    report = reconcile(surfaces, probe=lambda e: {"version": "1.11.0"}, fleet=FLEET)
    assert report.surfaces[0].update == "current"
    assert report.needs_update == []


def test_image_kind_remediation_is_redeploy():
    surfaces = [{"product": "windy-mind", "contract": "ops.mcp.v1",
                 "http": "http://127.0.0.1:8900"}]
    report = reconcile(surfaces, probe=lambda e: {"version": "0.1.0"}, fleet=FLEET)
    assert "redeploy windy-mind" in report.surfaces[0].remediation


def test_unknown_product_is_live_but_uncompared():
    surfaces = [{"product": "windy-experiment", "contract": "control.mcp.v1",
                 "http": "http://127.0.0.1:9999"}]
    report = reconcile(surfaces, probe=lambda e: {"version": "0.0.1"}, fleet=FLEET)
    st = report.surfaces[0]
    assert st.reachable and st.update == "unknown"


def test_summary_counts_live_stale_and_updatable():
    surfaces = [
        {"product": "windy-word", "contract": "control.mcp.v1", "http": "http://127.0.0.1:1"},
        {"product": "windy-mind", "contract": "ops.mcp.v1", "http": "http://127.0.0.1:2"},
        {"product": "windy-talk", "contract": "control.mcp.v1", "http": "http://127.0.0.1:3"},
    ]

    def probe(entry):
        return {
            "windy-word": {"version": "1.10.0"},  # update available
            "windy-mind": {"version": "0.2.0"},   # current
            "windy-talk": None,                    # dead/stale
        }[entry["product"]]

    report = reconcile(surfaces, probe=probe, fleet=FLEET)
    s = report.summary()
    assert "2 live surface(s)" in s
    assert "1 listed-but-unreachable" in s
    assert "1 with updates available" in s
