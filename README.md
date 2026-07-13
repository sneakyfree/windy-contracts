# windy-contracts — the agent-control canon

**One repo, one source of truth for how every Windy platform gives agents hands.**

This is the shared home the ecosystem-wide Agent Control Doctrine designated
(ADR-060 §8, decision 1). Everything here is law or the machinery that
enforces law:

| What | Where | Status |
|---|---|---|
| **The Doctrine** — what every platform must ship | [`AGENT_CONTROL.md`](AGENT_CONTROL.md) | v1.0-draft, PR #1 |
| Contract schema (the manifest every surface is generated from) | `schema/` | planned — Loom phase |
| Shared conformance suite (extracted from windytalk) | `conformance/` | planned — Loom phase |
| The generator ("the Loom": manifest → MCP packet + Python twin + tests) | `loom/` | planned |
| `surfaces.json` discovery-registry schema | `schema/surfaces/` | planned |
| Provenance / superseded drafts | `docs/archive/` | — |

## The one-sentence objective

> **"Fix this for me."** On any machine or account running any mix of Windy
> products, an agent can enumerate every control surface present, read each
> product's health, and drive it back to green — including restarting,
> reconfiguring, safe-moding, and updating a product **even when that product
> is dead** — with zero human terminal use.

## Rules of this repo

- The doctrine and schemas are **frozen contracts**: additive → minor bump via
  PR; breaking → new major file **and tell Grant**. Never silently mutate.
- Platform repos consume this repo read-only (vendor or submodule). Nothing
  platform-specific lives here.
- No credentials, ever (that's `kit-army-config`'s job — kept deliberately
  separate).
