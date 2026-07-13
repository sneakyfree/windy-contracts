# windy-contracts — the agent-control canon

**One repo, one source of truth for how every Windy platform gives agents hands.**

This is the shared home the ecosystem-wide Agent Control Doctrine designated
(ADR-060 §8, decision 1). Everything here is law or the machinery that
enforces law:

| What | Where | Status |
|---|---|---|
| **The Doctrine** — what every platform must ship | [`AGENT_CONTROL.md`](AGENT_CONTROL.md) | **LAW — v1.0, merged 2026-07-13** |
| Contract schema (the manifest every surface is generated from) | `schema/control-manifest.v1.schema.json` | **v1 pinned** — Talk rev.6 validates as-is |
| Band ↔ EI trust-mapping table (ADR-060 §3.5) | `schema/band-ei-mapping.v1.json` | **v1 pinned** |
| Shared conformance suite (extracted from windytalk @ `9360058`) | `conformance/mcp-conformance.v1.json` | **extracted** — per-platform drivers come with L3 |
| The Loom (`loom/`): validator | `uv run python -m loom.validate <manifest>` | **live** — `make check` gates it |
| The Loom: generator (manifest → MCP packet + Python twin + HTTP skeleton) | `loom/` | next — L1 part 2 |
| `surfaces.json` discovery-registry schema | `schema/surfaces/` | L2 |
| Provenance / superseded drafts | `docs/archive/` | quarantined — banners name ADR-060 as canon |

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
