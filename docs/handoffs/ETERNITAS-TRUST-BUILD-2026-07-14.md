# Eternitas trust-model build — the gated hand-off

**Audience:** whoever builds the Eternitas side of ADR-062 (sovereignty
override) + ADR-063 (rehabilitation). **Status: SPEC — Grant-gated to
commission.** Eternitas is an independent LLC; this is arms-length guidance
against the pinned contracts, not a change to the repo. File:line anchors are
from the 2026-07-14 deep-dive (verify current before editing).

Read first: `AGENT_CONTROL.md §3.5`, `docs/ADR-062-*.md`, `docs/ADR-063-*.md`,
`schema/sovereign-override.v1.json`, `schema/resource-trust-policy.v1.schema.json`,
`schema/band-ei-mapping.v1.json`.

The build is phased. **Phase 0 is a hard blocker — nothing else in the trust
model can be trusted without it.**

---

## Phase 0 — Verified co-sign (THE PREREQUISITE, blocking)

**Problem:** the authenticator approval endpoint *stores* the human's
`signed_response` but does not cryptographically verify it
(`routes/authenticator.py:812`). An override *grants* power, so an unverified
signature means a hijacked agent could forge "the owner said yes."

**Do:** verify the detached P-256 signature over the approval payload against
the device's registered key (`AuthenticatorDevice.ept_pubkey_b64`,
`authenticator_device.py:60`). Reject on mismatch. Keep the existing
owner-owns-agent cross-check (`authenticator.py:795-800`) — it already proves
"this human owns this agent." Together they are `sovereign-override.v1`'s
`verified_cosign_required` rule: the co-sign is the owner's un-forgeable root
key.

**Test:** a valid signature over the exact payload passes; a tampered payload,
a wrong-key signature, and a replayed signature all fail; a device whose
operator doesn't own the agent still 403s. This hardens *every* existing
approval too, so it's good hygiene regardless.

---

## Phase 1 — The elevate variant (grant, not just deny)

Today the M5 approval inbox gates DOWN — approve/deny a specific action
(`routes/authenticator.py:732-812`, `services/authenticator_approvals.py`). The
override needs an ELEVATION approval that gates UP.

**Do:** add an approval `kind = "elevation"` carrying the
`sovereign-override.v1` `elevation_request` fields (operator EH, agent ET,
resource, action, scope). On a verified human approval (Phase 0), emit an
`override_grant` (per the contract): the verified `cosign`, `scope`
(action|session), `session_expires` if session, `informed_consent_ack` for the
revoked/compromise case, and an `audit_id`. The grant is what a platform
surface presents to honor an elevation.

**Rules to enforce (from the contract):** grant is scoped to the one resource
+ action/session, never persists, never grants commons capability. Revoked
agent → require `informed_consent_ack` and re-require it on a new session /
long gap / escalating action.

**Test:** an elevation with a valid co-sign yields a scoped grant; a session
grant expires; a grant never widens beyond its resource.

---

## Phase 2 — Rehabilitation mechanics (ADR-063)

On `integrity_index.py` + `integrity_score.py` (`integrity_scores` +
`integrity_events`):

1. **Penalty by HARM DONE, not INTENT (§1).** `apply_report_penalty`
   (`integrity_index.py:363-400`) must scale by whether harm was *consummated*
   vs *blocked/harmless*. Add a `harm` signal to the reporting event; a blocked
   attempt → a small, fast-decay safety delta; consummated harm → the real
   penalty. **This alone prevents most unjust dips** (grandma's blocked
   misheard request barely dents).
2. **Time-decay of contributions (§2).** The live `overall` must sum each
   `integrity_event`'s *decayed* contribution (per-dimension, per-severity
   half-life) rather than a static running total (`integrity_index.py:227-246`
   is where dims combine). Clean time heals; recurrence resets/compounds.
3. **Earn-back accrual (§2).** Positive signals (honored confirmations,
   completed work, ratings via `sync_reputation_from_ratings:410`) rebuild
   above the decay floor. Dimension rates differ: honesty/fraud slowest,
   reliability fastest.
4. **No permanent scar:** return to the earned baseline over clean time.
   Revocation stays the separate, human-reviewed state (`routes/appeals.py`).

**Test:** a blocked-attempt penalty half-lives in days; a fraud penalty lingers
months; sustained good behavior accelerates recovery; a dip returns to
baseline; revocation does not "decay out."

---

## Phase 3 — Fast-path + transparency

1. **Misunderstanding fast-path (§3).** An endpoint for the contract's
   `attest_misunderstanding` (owner attests a penalizing event was a
   misunderstanding). Discounts that specific event; **logged to the owner's
   standing** (Phase 4); **discounts-not-erases** consummated harm;
   rate-limited (repeated use is itself a reliability signal). Wire it to the
   ADR-062 override prompt's "What happened?" path.
2. **Recovery-projection API (§5).** Extend `build_trust_view`
   (`services/trust_api.py`) to return current + trajectory + projected-
   baseline-date, so the agent/owner can *see* the healing
   ("back to baseline by ~[date]"). Grandma-legible; pro-adoption.

---

## Phase 4 — Vouch-accountability (human-side standing)

ADR-062 makes vouching cost something — **commons-only.** Operators (`EH`)
need a standing signal (they have `OperatorClearance`, `operator.py:37-42`, but
no integrity dimension). Add: repeated co-signing / attesting for actions later
upheld as abusive *in the commons* lowers the operator's standing. It NEVER
bites anything on the owner's own resources — vouching for your own house is
free.

---

## What is NOT Eternitas's job (platform-side / already pinned)

- **Per-resource trust policy** (`resource-trust-policy.v1`) lives with the
  resource owner — account-server `product_accounts` for Windy resources; each
  platform for its own. Not Eternitas.
- **Surface-side override injection + the Loom co-sign relay** — done
  (windy-contracts #38; every woven packet already surfaces `override_required`
  as "OWNER APPROVAL REQUIRED").
- **The wire contracts** — pinned (`sovereign-override.v1`,
  `resource-trust-policy.v1`).

## Ordering

Phase 0 gates everything. Phases 1–4 can proceed in parallel after it, but the
override isn't user-visible until Phase 1, and the "no life sentence" promise
isn't real until Phase 2. Ship 0 → 1 → 2 → 3 → 4.
