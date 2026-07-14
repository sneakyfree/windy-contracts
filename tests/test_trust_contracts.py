"""ADR-062/063 trust contracts — resource-trust-policy.v1 + sovereign-override.v1.

Pins the wire interface platforms + Eternitas build against: the policy schema
validates a sovereign-permissive default and rejects malformed policies; the
override contract carries the normative rules + message shapes, including the
verified-co-sign requirement (the hard prerequisite) and root-means-root.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schema"


def _load(name: str) -> dict:
    return json.loads((SCHEMA / name).read_text())


# ── resource-trust-policy.v1 ─────────────────────────────────────────

def _policy_schema():
    return _load("resource-trust-policy.v1.schema.json")


def test_policy_schema_parses_and_requires_owner():
    s = _policy_schema()
    assert s["required"] == ["resource", "owner"]  # ownership is foundational
    # defaults encode sovereign-permissive
    props = s["properties"]
    assert props["override"]["default"] == "owner-or-admin"
    assert props["confirmations"]["default"] == "default"
    assert props["revoked_agent"]["default"] == "owner-root"
    assert props["session_grants"]["default"] is True
    assert props["min_ei_autonomous"]["default"] == 600


def test_minimal_policy_is_valid_and_means_sovereign_permissive():
    # An owner + resource is enough; the rest defaults to sovereign-permissive.
    v = jsonschema.Draft202012Validator(_policy_schema())
    v.validate({"resource": "grandma/birthday-site", "owner": "EH26-GRAN-DMA1"})


def test_owner_can_lock_themselves_but_that_is_their_choice():
    # Sovereignty includes the freedom to be strict on your own resource.
    v = jsonschema.Draft202012Validator(_policy_schema())
    v.validate({
        "resource": "acme/prod", "owner": "EH26-ACME-0001",
        "override": "none", "confirmations": "default",
        "override_forbidden_actions": ["deploy_prod"], "revoked_agent": "none",
        "min_ei_autonomous": 900,
    })


def test_policy_rejects_bad_enums_and_extra_keys():
    v = jsonschema.Draft202012Validator(_policy_schema())
    for bad in (
        {"resource": "r", "owner": "o", "override": "anyone"},        # bad enum
        {"resource": "r", "owner": "o", "confirmations": "maybe"},    # bad enum
        {"resource": "r", "owner": "o", "revoked_agent": "sometimes"},
        {"resource": "r", "owner": "o", "min_ei_autonomous": 1500},   # out of range
        {"resource": "r", "owner": "o", "surprise": 1},               # extra key
        {"owner": "o"},                                                # missing resource
    ):
        with pytest.raises(jsonschema.ValidationError):
            v.validate(bad)


# ── sovereign-override.v1 ────────────────────────────────────────────

def _override():
    return _load("sovereign-override.v1.json")


def test_override_contract_carries_the_normative_rules():
    c = _override()
    assert c["contract"] == "sovereign-override.v1"
    rules = c["rules"]
    # the load-bearing invariants must be present
    for r in ("root_means_root", "commons_never", "ownership_authoritative",
              "verified_cosign_required", "always_confirm_floor", "scope",
              "audit_to_operator", "revoked", "misunderstanding_path"):
        assert r in rules and rules[r], r


def test_verified_cosign_is_the_hard_prerequisite():
    # The rule must demand a VERIFIED signature (not merely stored) — the
    # authenticator.py:812 gap is the blocking prerequisite.
    r = _override()["rules"]["verified_cosign_required"].lower()
    assert "verified" in r and ("not merely-stored" in r or "not merely" in r or "merely-stored" in r or "812" in r)


def test_override_defines_the_four_flow_messages():
    msgs = _override()["messages"]
    assert set(msgs) == {"override_required", "elevation_request", "override_grant", "attest_misunderstanding"}
    # override_required is an invitation, not an error
    assert msgs["override_required"]["properties"]["sovereign_override_required"]["const"] is True
    # the grant must require a cosign
    assert "cosign" in msgs["override_grant"]["required"]


def test_override_depends_on_the_shared_trust_contracts():
    dep = _override()["depends_on"]
    assert "EI_CAPABILITY_MATRIX.v1" in dep and "resource-trust-policy.v1" in dep
