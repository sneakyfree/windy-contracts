# The Steamroller — how a fix reaches every box (ADR-060 §5)

The doctrine's SENDING half. Receiving knobs (`check_for_update` /
`apply_update`) live on each surface (§3.4). This is how a fix, once merged,
percolates to everyone running the platform.

## The three parts, and what's built

1. **Discovery — `~/.windy/surfaces.json`** (schema `surfaces.v1`, writer
   `loom/register.py`). Every Class-D product registers at startup,
   deregisters on clean shutdown. **Built + tested.**
2. **The fleet version manifest** (schema `fleet-version.v1`). ONE document,
   published by admin, that says per product per channel: current version,
   minimum supported, distribution kind (npm / R2 / image / native), source,
   and a grandma-English "what this fixes." **Schema built + tested.** The
   admin publisher endpoint (`admin.windyword.ai/v1/fleet-versions`) is a
   small admin PR — not yet wired (admin is out of this repo).
3. **Reconcile — `loom/discovery.py`.** The reference reader an agent's
   harness runs: probe every surface (PROBE BEFORE TRUST — a dead port is
   stale, not gospel), then diff installed-vs-fleet to produce, per surface:
   `current` / `update-available` / `must-update` / `unknown`, each with a
   **literal remediation** (the doctor pattern for updates:
   `npx windy-word-mcp@1.11.0`, `redeploy windy-mind to image …`, etc.).
   **Built + tested, proven end-to-end.**

## The flow, in one picture

```
merge a fix ─▶ publish rail (npm / R2 / image)      [§5 rails]
            ─▶ bump admin fleet-version.v1 manifest  [the SoT for "current"]

agent lands on a box:
  read surfaces.json ─▶ probe each (before trust) ─▶ reconcile vs fleet manifest
                                                   ─▶ "Word has a security fix —
                                                       want me to apply it?"  (apply_update, always_confirm)
```

## What's deliberately NOT built here

- **The admin publisher** of the fleet manifest — a small endpoint in
  `windy-admin`, its own PR.
- **Cloud discovery** — Class C surfaces are found via the **account-server
  EPT query** ("what does this human run?"), NOT surfaces.json. That endpoint
  is identity-critical and lives in windy-pro's account-server; specced here,
  built in a focused, careful PR (it touches the identity spine).
- **`check_for_update` wiring** on each surface to resolve against the fleet
  manifest — per-platform, part of each platform's retrofit.

## Invariants (from ADR-060 §5)

- `apply_update` is attested + carries last-known-good rollback + is
  health-gated; it is the one RCE-by-design knob and always_confirm.
- Rollouts go in rings (canary = the Windy-0 fleet → early → all); the
  telemetry census (§3.9) is the gate.
- The agent is the update channel: grandma never reads a changelog — her
  agent offers the fix in one sentence and applies it on her yes.
