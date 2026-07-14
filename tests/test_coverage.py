"""Coverage-parity checker (L5 sentinel) tests.

Proves: manifest paths are extracted + normalized, phantom bindings (manifest
→ dead route) are caught as failures, uncovered served routes surface as
candidates, product prefixes are filtered from the noise, and native servers
are handled (no HTTP routes to diff).
"""

from __future__ import annotations

import json
from pathlib import Path

from loom.coverage import (
    coverage_report,
    extract_routes_from_text,
    manifest_route_paths,
)

ROOT = Path(__file__).resolve().parent.parent


def _fx(product: str, name: str) -> dict:
    return json.loads((ROOT / "schema" / "fixtures" / product / name).read_text())


# ── path extraction / normalization ─────────────────────────────────

def test_manifest_paths_extracted_and_normalized():
    m = {"product": "x", "tools": [
        {"name": "a", "tier": "auto_allow", "description": "d" * 45, "inputSchema": {},
         "transport": {"method": "GET", "path": "/accounts/{id}/"}},
    ]}
    assert manifest_route_paths(m) == {"/accounts/{}"}  # param collapsed, slash trimmed


def test_param_styles_compare_equal():
    m = {"product": "x", "tools": [
        {"name": "a", "tier": "auto_allow", "description": "d" * 45, "inputSchema": {},
         "transport": {"method": "GET", "path": "/u/{userId}"}}]}
    r = coverage_report(m, [{"method": "GET", "path": "/u/:userId"}])
    assert r.covered == ["/u/{}"] and not r.phantom


# ── phantom bindings (the load-bearing failure) ─────────────────────

def test_phantom_binding_is_a_failure():
    # manifest binds /health/full but the platform only serves /health
    m = {"product": "windy-x", "tools": [
        {"name": "h", "tier": "auto_allow", "description": "d" * 45, "inputSchema": {},
         "transport": {"method": "GET", "path": "/health/full"}}]}
    r = coverage_report(m, [{"method": "GET", "path": "/health"}])
    assert not r.ok
    assert r.phantom == ["/health/full"]


def test_real_fixture_has_no_phantoms_against_its_own_routes():
    # Mind's manifest bound to the routes it actually declares → zero phantom.
    # (Served set grew 2026-07-13: windy-mind #60 shipped the /ops/* healing
    # reads — get_logs, get_config, run_selftest.)
    m = _fx("windy-mind", "ops.mcp.v1.json")
    served = [{"method": "GET", "path": p} for p in
              ("/health", "/version", "/health/providers", "/v1/models", "/v1/route",
               "/ops/logs", "/ops/config", "/ops/check-update")]
    served.append({"method": "POST", "path": "/ops/selftest"})
    r = coverage_report(m, served)
    assert r.ok and not r.phantom
    assert set(r.covered) == {"/health", "/version", "/health/providers", "/v1/models",
                              "/v1/route", "/ops/logs", "/ops/config", "/ops/selftest",
                              "/ops/check-update"}


# ── uncovered candidates + product filtering ────────────────────────

def test_uncovered_routes_surface_as_candidates():
    m = _fx("windy-mind", "ops.mcp.v1.json")
    served = [{"method": "GET", "path": "/health"},
              {"method": "POST", "path": "/v1/chat/completions"},   # product — but not a filtered prefix
              {"method": "GET", "path": "/admin/keys"}]             # candidate ops knob
    r = coverage_report(m, served)
    assert "/admin/keys" in r.uncovered
    assert "/v1/chat/completions" in r.uncovered  # surfaced for a human to classify


def test_product_prefixes_are_filtered_from_noise():
    m = {"product": "x", "tools": [
        {"name": "h", "tier": "auto_allow", "description": "d" * 45, "inputSchema": {},
         "transport": {"method": "GET", "path": "/health"}}]}
    served = [{"method": "GET", "path": "/health"},
              {"method": "GET", "path": "/.well-known/jwks.json"},
              {"method": "POST", "path": "/api/v1/webhooks/stripe"},
              {"method": "GET", "path": "/_matrix/client/versions"}]
    r = coverage_report(m, served)
    assert r.uncovered == []  # all served extras are always-product prefixes


# ── native servers (agent-host) ─────────────────────────────────────

def test_native_server_has_no_route_diff():
    m = _fx("windy-agent", "control.mcp.v1.json")  # server: native
    r = coverage_report(m, [{"method": "GET", "path": "/whatever"}])
    assert r.native and r.ok
    assert r.phantom == [] and r.uncovered == []


# ── the extractor (best-effort convenience) ─────────────────────────

def test_extractor_reads_fastapi_and_express():
    text = '''
    @router.get("/health")
    @app.post("/api/v1/thing")
    app.get('/languages', (req, res) => {})
    router.delete("/webmail/message/{id}")
    '''
    routes = extract_routes_from_text(text)
    paths = {(r["method"], r["path"]) for r in routes}
    assert ("GET", "/health") in paths
    assert ("POST", "/api/v1/thing") in paths
    assert ("GET", "/languages") in paths
    assert ("DELETE", "/webmail/message/{id}") in paths
