# ops-hook — the fleet-canonical out-of-patient doctor (ADR-060 §3.6)

The host-side build for every Class-C platform's mutating baseline knobs:
SSH-free **restart**, **redeploy** (rebuild + health-gate + last-known-good
rollback + optional `expected_commit_sha` attestation), and **allowlisted
runtime-config edit** — served by a stdlib-only Python process running as
its own systemd unit, sharing **no container, venv, or dependency** with
the patient it operates on.

**One implementation, no drift:** this file (`hook.py`) is canonical.
Platform repos vendor it **byte-identical** into their own `ops-hook/`
directory and guard the copy with a local drift test (the ecosystem's
vendor+drift-guard pattern, cf. canonical-domains lint). Per-host
differences live entirely in the systemd unit's env file — see the header
of `hook.py` for every `OPS_HOOK_*` variable. Extracted from the
windy-mind donor implementation (windy-mind #61, 12-test proven), then
generalized: compose invocation, allowlist, migrate step, bind port, and
patient URL are all env-driven.

## Port checklist (per platform)

1. Read the platform's `SUBSTRATE.md`; every env value below must come from
   there or a live host check — **never guess the image ref**
   (`docker compose <args> images` on the host).
2. Vendor `hook.py` byte-identical into `<repo>/ops-hook/hook.py`; add the
   drift test to the platform's local gate.
3. Write `<repo>/ops-hook/deploy/ops-hook.env.example` with the host's
   verified values (compose cmd exactly as the SUBSTRATE documents it,
   allowlist = that platform's provider-key class only) and a systemd unit
   (unique `OPS_HOOK_PORT` per platform — consolidated hosts run several
   hooks side by side).
4. Manifest: `restart_app`/`set_setting`/`apply_update` stay **gap
   (STAGED)** until the unit is installed and reachable; then bind + re-weave.
5. Install is **Grant-gated** (unit + proxy `/hook/*` route + token minted
   to the unit env + lockbox).

## Security model (all layers required)

Loopback bind (TLS via the host proxy only) → constant-time bearer
(`OPS_HOOK_TOKEN`, boot-refusal without it, never stored in the patient's
env) → mechanical always_confirm (single-use 60s nonce from
`POST /hook/confirm`; 428 with the literal remediation otherwise) →
one-op-at-a-time 409 lock. Config edits: allowlist only (provider keys +
LOG_LEVEL class — never DB/redis URLs or signing secrets), single-line
printable <256-char values (env-injection guard), atomic write with
`.prev` backup and auto-restore on a failed health gate. Verdicts are
`{passed, stages, duration_ms}` — `passed`, never top-level `ok`.

## Tests

Canonical suite: `uv run pytest tests/test_ops_hook.py` (part of
`make check`). Injected runner/prober — no docker or network needed.
