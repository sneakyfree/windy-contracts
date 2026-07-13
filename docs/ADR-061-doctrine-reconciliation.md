# ADR-061 — Reconciling the two doctrine tracks

> **2026-07-13. Status: ACCEPTED.** Verdict: the two tracks are **complementary
> layers, not competing standards.** All three harmonizations decided:
> **H1** (class alias) done; **H2** — Grant concurred: unify trust vocabulary
> on the **EI_CAPABILITY_MATRIX names** (Platinum/Gold/Standard/Watch/Untrusted),
> ADR-060's SANDBOX/USER/TRUSTED/OWNER become deprecated aliases
> (`schema/band-ei-mapping.v1.json`); **H3** — Grant concurred: **one umbrella**
> — ADR-060 absorbs the Fable-7.5 product law as `AGENT_CONTROL.md §1.1`.

## What happened

Two lanes built agent-control MCP in parallel:

- **This lane (ADR-060, the Agent Control Doctrine)** — the **ops / healing**
  surface: how an agent *heals a platform* (health, restart, logs, redeploy,
  safe-mode). Contract families `ops.mcp.v1` / `control.mcp.v1` / `hands.mcp.v1`.
- **The cloud/code lane (DNA-strand "Fable-7.5 Doctrine" v0.3.0)** — the
  **product / agent-first** surface: how an agent *drives the product* (buy a
  domain, publish a site, create a project). Contract families
  `windy-cloud-domains.mcp.v1` / `windy-cloud-sites.mcp.v1` (+ planned
  code-web).

## The verdict: coexistence

**These are two different surfaces for two different jobs, and both are
right.** The evidence:

1. **Their tools are product + repair-own knobs, not service healing.**
   `buy_domain`, `publish_site`, `create_project` (product); `repair_dns`,
   `resync_domain`, `rebuild_pointer` (repair the *user's own* resources,
   Gold+ EI). There is **no** restart / logs / redeploy / version knob in
   their MCP surface — the ops/healing slot is empty.
2. **They planned my exact surface and left it for later.** DNA codon **D9.8**:
   "every runbook entry becomes an operator-tier tool on a **separate ops
   control surface** (windy-talk control.mcp precedent — *the doctor is not in
   the patient*)." That is verbatim ADR-060 §3.6. My ops surface fills the slot
   they explicitly reserved.
3. **Their implementation already cites ADR-060.** `agent_surface/__init__.py`:
   *"Cloud-class agent surface — Agent Control Doctrine (ADR-060 draft) shape"*
   and names *"The Loom (doctrine L1)"* as its future codegen source. The
   product lane is building **toward** this doctrine, not against it.
4. **Their manifests already 90% conform.** Same `contracts/<name>.mcp.v1.json`
   shape; per-tool `name` / `description` / `inputSchema` / `tier` all match
   control-manifest.v1 (they even call the tier values *"Talk vocabulary"*);
   contract-name pattern matches; streamable-HTTP MCP at `POST /mcp` with
   EPT/JWT bearer = exactly the Class C transport.

So the doctrine gains a **third surface archetype** it hadn't formalized:

| Archetype | Contract | Job | Who built it |
|---|---|---|---|
| **Ops / healing** | `ops.mcp.v1`, `control.mcp.v1` | heal the platform | ADR-060 lane (this one) |
| **Hands** | `hands.mcp.v1` | drive OTHER apps (Talk) | ADR-058 / Talk |
| **Product / agent-first** ⬅ NEW | `<product>.mcp.v1` | drive the product itself | Fable-7.5 lane |

The product archetype is correct **for agent-first product cells** (the
TikTok-twins: domains, sites, code-web) where the whole point is that the
agent *operates the product*. It does NOT replace §2 (for infrastructure
services like Mind/Search, the machine-to-machine product API still stays out
of the ops surface). Both patterns are valid; which one a platform uses
depends on whether its product is meant to be *agent-driven* (product surface)
or *machine-consumed* (ops surface only, product API stays out).

## Harmonizations

### H1 — `class: "cloud-service"` → `"cloud"` *(mechanical; done here)*
Their only hard schema failure. `class` encodes TRANSPORT regime (desktop /
cloud / agent-host), and their surfaces are cloud-transport (streamable-HTTP +
EPT). "cloud-service" is just a longer spelling of "cloud". **This ADR's PR
widens the enum to accept "cloud-service" as a deprecated alias so their real
files validate today; canonical is "cloud"**, and the cloud lane should
normalize with a one-word change at its next touch.

### H2 — Trust vocabulary: two band sets 🔴 **GRANT DECISION**
Both lanes gate by Eternitas EI, but name the tiers differently:

| EI score (approx) | ADR-060 band | Fable-7.5 / EI_CAPABILITY_MATRIX |
|---|---|---|
| ≥ 900 | OWNER | Platinum |
| 700–899 | TRUSTED | Gold |
| 400–699 | USER | Standard |
| < 400 | SANDBOX | Watch / Untrusted |

They are the **same ladder, two names.** They must unify on ONE vocabulary or
the fleet has two trust languages. **Grant: which set is canonical?** My lean:
the **EI_CAPABILITY_MATRIX names (Platinum/Gold/Standard/Watch)** are the
product-facing, grandma-legible ones and are already in the DNA v0.2.0
contracts fleet-wide; ADR-060's SANDBOX/USER/TRUSTED/OWNER came from
windy-agent's internal Capability Plane. Recommend unifying on the EI matrix
names and mapping ADR-060's bands onto them (I'd update `band-ei-mapping.v1`).

### H3 — Doctrine lineage: one umbrella or two docs 🔴 **GRANT DECISION**
There are now two doctrine documents: **ADR-060** (this repo, the ops law) and
the **Fable-7.5 Doctrine / DNA v0.3.0** (§0.6 of the DNA strand plans, the
product law, anchored to ADR-010). They don't conflict, but two canonical
doctrine docs will drift — that violates the one-source-of-truth rule.
**Grant: should ADR-060 become the umbrella "Agent Control Doctrine" with the
Fable-7.5 product law folded in as its product-surface chapter, or stay two
cross-referenced docs?** My lean: **one umbrella** (ADR-060) with a
`§ product-surface archetype` section that vendors the Fable-7.5 rules
(capability-completeness, CONFIRM_FLOW, repair-own class) verbatim, so there's
one law with three surface chapters.

## Follow-ups (not blocking; hand to the gap-closing lane)

- **The cloud cells still need their `ops.mcp.v1` healing surface** (D9.8 —
  the slot they reserved). `/version` + `/health/full` exist as REST; they
  need restart/logs/redeploy + MCP exposure, ops-plane-outside-the-patient.
  This is a normal gap-closing item once H1–H3 land.
- **windy-code / windy-code-web MCP is mostly unbuilt** — code-web is genesis
  (MCP planned Strand B8); windy-code ships an **Agent Bus** (JSON-over-UDS,
  EPT), a *different* transport from MCP. When they build the MCP packet,
  it inherits this reconciled doctrine from birth.
- **Register the product-surface manifests as canon fixtures** (done in this
  PR: `schema/fixtures/windy-cloud-{domains,sites}/`) so the validator +
  coverage checker cover them going forward.

## Decision summary for Grant

1. **H1 (class alias)** — done, mechanical, no decision needed.
2. **H2 (trust vocab)** — 🔴 pick one band vocabulary. Lean: EI matrix names.
3. **H3 (doctrine lineage)** — 🔴 one umbrella doc or two. Lean: one umbrella.

Nothing in the cloud/code repos is changed by this PR — it only adds canon
docs + fixtures + a backward-compatible schema alias. The build follow-ups
wait on H2/H3.
