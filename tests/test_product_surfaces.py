"""Product-surface archetype (ADR-061) — the Fable-7.5 cloud/code lane's
agent-first manifests, reconciled into the canon.

These are PRODUCT knobs (buy_domain, publish_site), a distinct archetype from
the ops/healing surfaces (ops.mcp.v1 / control.mcp.v1). They validate against
control-manifest.v1 as a compatible dialect. This test pins that they stay
valid and that the reconciliation invariants hold.
"""

from __future__ import annotations

import json
from pathlib import Path

from loom.validate import validate_manifest

ROOT = Path(__file__).resolve().parent.parent


def _fx(product: str, name: str) -> dict:
    return json.loads((ROOT / "schema" / "fixtures" / product / name).read_text())


def test_domains_and_sites_validate_as_a_dialect():
    for product, name in (
        ("windy-cloud-domains", "domains.mcp.v1.json"),
        ("windy-cloud-sites", "sites.mcp.v1.json"),
    ):
        r = validate_manifest(_fx(product, name))
        assert r.ok, (product, r.errors)


def test_product_surfaces_are_not_baseline_checked():
    # Product manifests (<product>.mcp.v1) are NOT healing surfaces — the
    # 13-knob baseline must not be imposed on them (ADR-061: distinct archetype).
    r = validate_manifest(_fx("windy-cloud-domains", "domains.mcp.v1.json"))
    assert not any(w.startswith("baseline") for w in r.warnings)


def test_tier_vocabulary_matches_the_canon():
    # They use the SAME tier vocabulary as ADR-060 ("Talk vocabulary") — a
    # key reconciliation fact: no third tier language.
    for product, name in (
        ("windy-cloud-domains", "domains.mcp.v1.json"),
        ("windy-cloud-sites", "sites.mcp.v1.json"),
    ):
        tiers = {t["tier"] for t in _fx(product, name)["tools"]}
        assert tiers <= {"auto_allow", "ask_first", "always_confirm"}, (product, tiers)


def test_money_and_publish_knobs_are_always_confirm():
    # ADR-060 invariant: money + destructive-publish ALWAYS confirm. The
    # product lane honors it — assert it so a future edit can't weaken it.
    domains = {t["name"]: t for t in _fx("windy-cloud-domains", "domains.mcp.v1.json")["tools"]}
    sites = {t["name"]: t for t in _fx("windy-cloud-sites", "sites.mcp.v1.json")["tools"]}
    assert domains["buy_domain"]["tier"] == "always_confirm"
    assert sites["publish_site"]["tier"] == "always_confirm"


def test_class_alias_accepted():
    # H1: 'cloud-service' is accepted (deprecated alias for 'cloud').
    assert _fx("windy-cloud-domains", "domains.mcp.v1.json")["class"] == "cloud-service"
    # ...and it validates (proven by test_domains_and_sites_validate_as_a_dialect).
