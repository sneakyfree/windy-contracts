# Per-platform gap-closing — the master menu

*After the fleet procession (2026-07-13), every platform has a doctrine-
compliant agent-control MANIFEST. This is the punch list of what each
platform still needs to BUILD so its knobs are real, not just declared.*

**How to use this:** pick ONE platform, read its row + linked handoff, close
its gaps in that platform's own repo (feature branch + PR + local tests
green), then re-weave and verify. One platform per terminal. Cross-platform
design is frozen — do not re-open the doctrine; if you think it's wrong,
propose a windy-contracts PR, don't deviate.

Load first: `AGENT_CONTROL.md` (ADR-060, the law), `docs/LANE_KICKOFF.md`
(who you are + non-negotiables), this file, then the platform's manifest
(`schema/fixtures/<product>/*.mcp.v1.json`, its `baseline_mapping` lists the
gaps with engineering notes) and its handoff doc if one exists.

Two universal principles for every gap:
- **A gap knob is NEVER advertised until it's real** — implement the route,
  add the tool to the manifest, re-weave. Don't add a tool that 404s.
- **Content-free / privacy hard line** — `get_logs` never exposes message
  bodies, mail, transcripts, prompts; scrub before returning.

---

## Class C (cloud) — the common shape

Most cloud platforms share the same gaps. The recurring four, in priority
order:

1. **SSH-free redeploy hook = `apply_update`** (§7, *urgent* — GitHub Actions
   is billing-locked, so today a sick service can be observed but not healed).
   Health-gated, attested, last-known-good rollback. The ops plane lives
   OUTSIDE the patient (a different service triggers the redeploy).
2. **Runtime config: `get_config` + `set_setting`** — read the effective
   config (secrets redacted) and change a provider key / rule WITHOUT a
   redeploy (today most are env-at-deploy).
3. **`get_logs`** — content-free recent logs.
4. **`run_selftest`** — actively exercise the core path (a canary call), not
   just probe liveness.

Plus, when convenient: the uniform native shape `GET /tools` + `POST /invoke`
(§3.2) so the conformance driver's LIVE gate runs, and deploy the woven ops
shim behind the platform's TLS proxy at `/mcp`.

| Platform | Repo | Gaps (see manifest `baseline_mapping`) | Notes |
|---|---|---|---|
| **windy-mind** | `~/windy-mind` | the recurring four | §7 urgent redeploy; handoff `docs/handoffs/MIND-LANE-2026-07-13.md`. The FIRST cloud template. |
| **windy-search** | `~/windy-search` | the recurring four | `run_selftest` = canary search per source; cleanest leaf. |
| **windy-mail** | `~/windy-mail` | the recurring four | `run_selftest` = canary send to loopback; `get_logs` MUST scrub mail. |
| **windy-clone** | `~/Windy-Clone` | the recurring four | `run_selftest` = resolve+price a dummy order (no purchase). |
| **windy-registry** (Drops) | `~/windy-registry` | the recurring four | 🔴 **LIVE: `/health/full` reports `r2_bucket: http 404` in production** — investigate first (bundle storage). Brand=Drops, service=windy-registry. |
| **windy-translate** | `~/windy-pro/services/translate-api` | **`/version` (MF1 — missing entirely)** + **EPT auth** + get_logs + run_selftest | Internal Node svc, loopback:8099. Adding `/version` is the smallest, highest-value first win. |
| **windy-admin** | `~/windy-admin` | get_config, get_logs, run_selftest | Fleet-version PUBLISHER already DONE (`/v1/fleet-versions`). |

## Class C — the special one

| Platform | Repo | THE gap | Notes |
|---|---|---|---|
| **windy-chat** | `~/windy-chat` | 🌟 **the fleet-health AGGREGATOR** | Chat is ~13 services over Synapse; per-service `/health` isn't externally routed and there's no aggregator, so it's mostly BLIND. **Highest-impact gap in the fleet.** Build `GET /api/v1/ops/health` (fan-out to every service + Synapse, nginx-routed, EPT-gated) per **`docs/MULTI-SERVICE-OPS.md`** — it becomes get_health + get_status + get_capabilities at once. Then re-weave with those three tools bound to it. |

## Class D (desktop)

| Platform | Repo | Gaps | Notes |
|---|---|---|---|
| **windy-word** | `~/windy-pro` | 8 baseline gaps (get_logs, run_selftest, get_capabilities, reconnect, safe-mode, apply_update, reset_to_defaults) + **supervisor + OS resurrection** (§3.6 "doctor not in the patient") + `GET /tools`+`/invoke` + full ~115-tool enumeration + surfaces.json registration | Handoff `docs/handoffs/WORD-LANE-2026-07-13.md`. ⚠️ **`main.js` is the most dangerous file in the ecosystem** (its paste path killed Grant's terminals twice 2026-07-12 — see windy-pro CLAUDE.md). New baseline routes are ADDITIVE handlers; touch NOTHING in recording/paste/Wayland/focus. Reference for supervisor+resurrection: windytalk. |
| **windy-talk** | Windy 0 `~/Desktop/Grant's Folder/windytalk` (Mac tree `~/windytalk-build`) | engine-box surface, account/billing knobs, v1→v2 ramp, /tools+/invoke, surfaces.json, weave.json, Loom in make check | Handoff `docs/handoffs/TALK-LANE-2026-07-13.md`. **A dedicated Talk terminal already owns this** — coordinate, don't collide. |

## Class A (agent-host)

| Platform | Repo | Gaps | Notes |
|---|---|---|---|
| **windy-agent** (Fly) | `~/windy-agent` | Fly's OWN baseline gaps as capabilities: get_config, reconnect, restart_app (needs a supervisor beyond bare systemd `Restart=`), safe-mode, check/apply_update (attested self-update, delicate — always_confirm/OWNER), reset_to_defaults | Handoff `docs/handoffs/FLY-LANE-2026-07-13.md`. Native server (both halves) + full-registry wiring are DONE (#282/#285/#286). Adding a capability makes it appear over MCP automatically. |

---

## Recommended order (by impact)

1. **windy-chat aggregator** — the one platform that's still mostly blind; highest impact.
2. **windy-translate `/version`** — smallest win, removes an MF1 non-compliance.
3. **windy-registry R2-404** — a real live production degradation (investigate, may not be a code change).
4. The recurring cloud four, one platform at a time (Mind first — it's the template the others copy).
5. **windy-word supervisor + resurrection** — highest value, highest care (dangerous file); do last / with most caution.

## Grant-gated (do NOT do without Grant)

npm publish of `windy-word-mcp@1.11.0` (it's already `current` in the live
fleet manifest); any production deploy; the book-launch rebuild cherry-pick
of windy-pro #231; anything spending money.
