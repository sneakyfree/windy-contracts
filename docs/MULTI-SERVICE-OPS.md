# Multi-service platforms — the fleet-health aggregator pattern

*Discovered during the Windy Chat retrofit (2026-07-13). A doctrine addendum
to ADR-060 §2/§3.4 for any Windy platform that is a constellation of services
rather than a single API.*

## The problem

Most Windy platforms are one service with one `/health`. But some (Chat today;
likely others as they grow) are **N services behind one gateway** — Chat is
~13 Node services (directory, media, hub, backup, …) over a Synapse
homeserver, path-routed by nginx at one hostname. Each service has its own
`/health` and `/version`, but:

- those per-service endpoints are usually **internal-only** (not gateway-
  routed), so an outside agent can't reach them; and
- there is **no single endpoint** that answers "which of my services is down?"

The result: `get_health` can only probe one thing (the gateway, or the core),
and an agent healing the platform is blind to which *piece* failed — exactly
the "firefighter with no view of the building" the doctrine exists to prevent.

## The pattern

A multi-service platform MUST expose a **fleet-health aggregator**: one
gateway-routed, EPT-gated endpoint (convention: `GET /api/v1/ops/health`) that
fans out to every service's internal `/health` plus any datastore/core, and
returns the constellation:

```json
{
  "status": "degraded",
  "services": {
    "synapse":      { "status": "up",   "version": "1.x" },
    "directory":    { "status": "up",   "version": "..." },
    "media":        { "status": "down", "error": "db unreachable" },
    "...":          { "...": "..." }
  }
}
```

This single endpoint satisfies **`get_health`** (overall + per-service),
**`get_status`** (every service's version — did the deploy reach all of
them?), and **`get_capabilities`** (which services/bridges are actually up).
Three baseline knobs, one aggregator.

## Manifest guidance

- Bind `get_health` / `get_status` / `get_capabilities` to the aggregator
  once it exists.
- Until then, bind `get_health` to the most load-bearing reachable core (for
  Chat: Synapse `/_matrix/client/versions`) and mark the aggregator as the
  **headline gap** — an honest thin surface beats a fake broad one.
- Per-service healing knobs (reconnect/restart a single service) can be
  namespaced tools (`reconnect.media`) the aggregator's design informs — a
  later pass, once the read view exists.

## Build order for a multi-service platform

1. Build the aggregator endpoint (fan-out read) + nginx route + EPT gate.
2. Point `get_health`/`get_status`/`get_capabilities` at it; re-weave.
3. (Later) per-service mutation knobs, informed by what the aggregator shows.

The aggregator is cheap (parallel GETs to loopback) and is the single highest-
value ops investment a multi-service platform can make.
