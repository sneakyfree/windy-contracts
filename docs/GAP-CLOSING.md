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
| **windy-mind** | `~/windy-mind` | ✅ **healing reads SHIPPED 2026-07-13** (windy-mind #60): get_logs (categorized, content-free) + get_config (secrets→booleans) + run_selftest (one real free-chain inference, 60s-cached), all EPT/JWT-gated; manifest 5→8 tools + baseline_mapping. ✅ **pass 2 BUILT 2026-07-13 (#61): the out-of-patient ops-hook** — SSH-free restart/redeploy(rollback+attestation)/allowlisted-config, bearer + single-use-nonce confirm; knobs stay STAGED gaps until installed. 🔴 Grant-gated: mind-api image rebuild (reads) + ops-hook install (unit + Caddy /hook/* + token + verify WINDY_MIND_IMAGE_REF on-host). Remaining code-side: check_for_update wiring | handoff `docs/handoffs/MIND-LANE-2026-07-13.md`. The FIRST cloud template — Search/Mail/Clone replicate the reads pass; the ops-hook pattern generalizes to every Class-C host. |
| **windy-search** | `~/windy-search` | the recurring four | `run_selftest` = canary search per source; cleanest leaf. |
| **windy-mail** | `~/windy-mail` | the recurring four | `run_selftest` = canary send to loopback; `get_logs` MUST scrub mail. |
| **windy-clone** | `~/Windy-Clone` | the recurring four | `run_selftest` = resolve+price a dummy order (no purchase). |
| **windy-registry** (Drops) | `~/windy-registry` | the recurring four (minus the solved probe) | ✅ **R2-404 SOLVED 2026-07-13 (#26): FALSE ALARM** — bucket was healthy all along (bundle downloads sha256-verified); the probe HEAD'd the domain root, which R2 public buckets 404 by design. Probe now HEADs the newest real bundle; r2 joins the overall verdict. 🔴 Grant-gated image rebuild to deploy. Brand=Drops, service=windy-registry. |
| **windy-translate** | `~/windy-pro/services/translate-api` | ✅ **baseline SHIPPED 2026-07-13** (windy-pro #235 + windy-contracts #20): /version (MF1) + opt-in token wall (install_token, not EPT — loopback internal svc) + /ops/logs + /ops/selftest, re-woven to 6 tools. 🔴 Grant-gated: service restart (+ optional WINDY_TRANSLATE_TOKEN env to arm the wall). Remaining: get_config, set_setting, restart_app, check/apply_update | ⚠️ Envelope rule from this retrofit: tool payloads must not use top-level `ok` (reserved by the invoke envelope) — use `passed` etc. |
| **windy-admin** | `~/windy-admin` | get_config, get_logs, run_selftest | Fleet-version PUBLISHER already DONE (`/v1/fleet-versions`). |

## Class C — the special one

| Platform | Repo | THE gap | Notes |
|---|---|---|---|
| **windy-chat** | `~/windy-chat` | ✅ **aggregator SHIPPED 2026-07-13** (windy-chat #143 + #144, windy-contracts #17) — `GET /api/v1/ops/health` built + re-woven (get_health/get_status/get_capabilities bound). 🔴 Grant-gated deploy to go LIVE (onboarding rebuild + live nginx `/api/v1/ops/` route + `WINDY_OPS_FLEET` env). Remaining gaps: per-service reconnect/restart, get_logs (scrubbed), run_selftest (Synapse canary), apply_update | Pattern doc **`docs/MULTI-SERVICE-OPS.md`** proven in production code. |

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

1. ~~**windy-chat aggregator**~~ ✅ DONE 2026-07-13 (#143/#144/windy-contracts #17; Grant-gated deploy pending).
2. ~~**windy-translate `/version`**~~ ✅ DONE 2026-07-13 (windy-pro #235 + windy-contracts #20; Grant-gated restart pending).
3. ~~**windy-registry R2-404**~~ ✅ SOLVED 2026-07-13 (#26): false alarm — probe design, fixed; Grant-gated rebuild pending.
4. The recurring cloud four, one platform at a time (Mind first — it's the template the others copy).
5. **windy-word supervisor + resurrection** — highest value, highest care (dangerous file); do last / with most caution.

## Grant-gated (do NOT do without Grant)

npm publish of `windy-word-mcp@1.11.0` (it's already `current` in the live
fleet manifest); any production deploy; the book-launch rebuild cherry-pick
of windy-pro #231; anything spending money.
