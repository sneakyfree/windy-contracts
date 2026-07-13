# Doctrine-lane progress ledger

Append-only. Newest entry first. Every working session ends by adding an
entry here — a session that didn't update the ledger didn't happen.

---

## 2026-07-13 (night) — GAP-CLOSING #5: Search healing reads SHIPPED (first template replication — fast + clean)

- **windy-search #61 merged** — mechanical replication of the Mind
  Class-C template (windy-mind #60), proving the "later platforms are
  replication, not new mechanism" bet on the gap-closing side too.
- `GET /ops/logs` (router per-source failures categorized —
  source:quota_429/auth_or_billing/upstream_5xx/exception; bridge bodies
  can echo query text, never stored) + `GET /ops/config` (per-source
  {configured, fallback} booleans, redis/integrity/telemetry/render
  wiring) + `POST /ops/selftest` (one real canary through the router's
  fan-out/merge/dedup; counts/bridges/latency only; **300s verdict
  cache — stricter than Mind's 60s because Brave/Google are METERED**).
  All EPT-required (require_passport). Manifest 5→8 tools, gaps→
  implemented; mutating gaps note the windy-mind ops-hook (#61) as the
  port-ready pattern for this host.
- Proven: 6 new tests (secret sweep, quota-cache single-call), full
  suite 339 passed 0 regress; live 401-wall on real-auth boot; woven
  packet static conformance byte-identical. make check 69 green.
- **🔴 GRANT-GATED:** Search redeploy per its SUBSTRATE.
- **Next:** Mail (get_logs MUST scrub mail — the privacy hard line's
  sharpest platform), then Clone; then windy-admin's three reads.

## 2026-07-13 (night) — GAP-CLOSING #4b: Mind ops-hook BUILT — the doctor is out of the patient (§7 urgent)

- **windy-mind #61 merged: `ops-hook/`** — stdlib-only Python service,
  its own systemd unit OUTSIDE the compose project (no shared container/
  venv/dependency with mind-api), loopback :8901, internet only via a
  Caddy `/hook/*` route. The host-side build for the mutating pair:
  - `POST /hook/redeploy` (**apply_update, the §7-urgent one**): tag
    last-known-good → rebuild from the deploy tree → up → alembic →
    health-gate w/ optional expected_commit_sha ATTESTATION (served
    /version must match) → automatic ROLLBACK to last-good on a failed
    gate, re-gated; a rolled-back redeploy still reports passed=false.
    v1 = rebuild-in-place; code pull to host stays rsync until Grant
    grants a host git credential (documented).
  - `POST /hook/config` (**set_setting**): ALLOWLISTED keys only
    (provider *_API_KEYs + LOG_LEVEL — never hook token/DATABASE_URL/
    REDIS_URL/MIND_HMAC_SECRET), env-injection-proof validation, atomic
    .env write + .env.prev backup, recreate-not-restart (compose restart
    skips env_file — the fleet trap), health-gate, auto-restore on fail.
  - `POST /hook/restart` (**restart_app**): compose restart + gate.
  - **Wall:** bearer token (constant-time, refuses to boot without one,
    held in the unit's 0600 env — never the patient's) + **mechanical
    always_confirm**: single-use 60s nonce from POST /hook/confirm, 428
    w/ literal remediation without it + one-op 409 lock.
- deploy/: systemd unit + Caddy snippet + install runbook. ⚠️ verify
  WINDY_MIND_IMAGE_REF on-host before install (SUBSTRATE's image name is
  ⓘ-inferred).
- **Manifest stance: the three knobs stay honest GAPs w/ STAGED notes** —
  not advertised until the unit is installed (no 404 knobs). Fixture
  synced.
- Proven: 12 tests, full-HTTP fidelity w/ injected runner/prober —
  walls 401/428/409, nonce replay refusal, sha-mismatch rollback,
  dead-gate rollback-and-regate, allowlist + injection guard, failed-
  gate env restore. make check 69 green (post Talk-lane refresh).
- **🔴 GRANT-GATED install:** verify image ref → token to unit env +
  lockbox → systemd unit → Caddy /hook/* → smoke confirm+restart. Then
  bind the 3 tools + re-weave.
- **Mind is now FULLY buildable-side done** (reads #60 + hook #61); what
  remains for Mind is deploys + the check_for_update wiring. **Next:
  replicate the cloud-four across Search/Mail/Clone (mechanical), or
  windy-admin's get_config/get_logs/run_selftest.**

## 2026-07-13 (night) — Talk lane DONE + canon fixtures refreshed

- **windy-talk lane FINISHED its whole punch list** (windytalk PR #55, handoff
  items 1-7): engine-box surface (engine.mcp.v1, 14 tools), account/billing
  knobs (control 24→28, rev.8), surfaces.json + weave.json, canonical POST
  /invoke, Loom validation in its gate. Clean tree, on master, deployed?=Grant.
- **Talk = GOLD STANDARD:** its 3 contracts validate 0 errors + 0 WARNINGS
  against the evolved (post-H2/H3) doctrine — the only platform at zero
  warnings. No trust-vocab conflict (no band_floor use).
- **Canon hygiene (windy-contracts #23):** refreshed the stale rev.6
  first-citizen fixtures → rev.8 (control 28-tool) + added engine.mcp.v1
  fixture. Tests updated (floor 'only rises', zero-warnings pin, engine
  validate, generator count-agnostic). make check 69.
- **Talk needs NOTHING further** (no follow-up prompt, no SSH pass) — release
  the terminal; only Grant-gated deploy remains.

## 2026-07-13 (night) — GAP-CLOSING #4a: Mind healing reads SHIPPED (observable → half-healable)

- **Platform taken: windy-mind** (the recurring cloud four, Mind first —
  the Class-C template others copy). windy-mind #60 merged; fixture +
  coverage test synced here. 3 of 5 MIND-LANE punch-list gaps closed.
- **Shipped:** `GET /ops/logs` (content-free ring; broker error paths
  feed it CATEGORIZED — provider:quota_429/auth/timeout/
  empty_completion — raw provider bodies can embed prompts, never
  stored); `GET /ops/config` (every secret redacted to a boolean:
  per-provider key map via broker.status(), db/redis/telemetry legs,
  environment); `POST /ops/selftest` (ONE real minimal inference through
  the broker with paid_fallback_allowed=False — the canary rides the
  free-biased chain, never spends money; per-stage verdict `passed`;
  detail = model/provider/latency, never completion text; **60s verdict
  cache so polling can't burn quota**). All three require EPT/Pro-JWT
  (require_user) per the handoff guardrail. Manifest gains
  baseline_mapping (fleet convention), 5→8 tools;
  reconnect/safe-mode/reset marked honestly `unsupported` (stateless
  broker).
- **Proven:** 7 new route tests, full Mind suite 403 passed, 0 regress;
  LIVE 401-wall proof on the real-auth boot (/ops/* 401 anonymous,
  /health public); LIVE woven-packet E2E (real MCP client → packet →
  booted real app): 8 tools, redacted config, ring carrying the real
  lifespan server_start, selftest passed + cache hit, completion text
  provably absent; conformance static byte-identical; make check 67.
- **Coverage-sentinel note:** the L5 pinned-route test
  (test_real_fixture_has_no_phantoms…) updated to Mind's grown served
  set — the sentinel correctly caught the manifest/served-set delta.
- **🔴 GRANT-GATED:** mind-api image rebuild to make /ops/* live.
- **Next (Mind pass 2, needs design before code): the mutating pair —**
  `set_setting` (runtime provider-key change w/o redeploy;
  always_confirm + OWNER band) and **`apply_update` (§7 URGENT:
  SSH-free health-gated redeploy; the hook must live OUTSIDE the api
  container it restarts — candidate homes: the Cloud kernel's ops
  plane, admin, or a host-level supervisor unit shipped in-repo).**
  Or continue the recurring four on Search/Mail/Clone (pure
  replication of this pass).

## 2026-07-13 (night) — GAP-CLOSING #3: Drops R2-404 SOLVED — false alarm, probe fixed (windy-registry #26)

- **Investigation verdict (read-only first, per the menu): the R2 bucket
  was NEVER broken.** windy-roster-0.1.0.zip downloads HTTP 200 from
  drops.windydrops.com and its sha256 matches the registry's recorded
  bundle_sha256 exactly; previews serve 200. Root cause: the /health/full
  probe HEAD'd the public-domain ROOT, which an R2 public bucket 404s BY
  DESIGN (no root object, no listings) — a permanent false alarm, and it
  would have read 'ok' mid-outage had any object been named '/'.
  Corroborating smell: r2_status was already excluded from the overall
  verdict (the noise had been noticed and routed around, not diagnosed).
- **Fix (windy-registry #26, merged): probe the true user path.**
  Published bundle exists → HEAD that exact newest bundle_url (domain +
  bucket + real object; 404 there = REAL degradation). Registry empty →
  root-404 maps to 'ok (empty)' (R2's no-such-object answer proves the
  domain is wired). r2 rejoins the overall verdict; 'http NNN' anywhere
  (e.g. a 500ing JWKS) now degrades too, not just connection errors.
- Manifest $comment updated (RESOLVED note + new semantics); fixture
  synced here. 4 new tests pin the semantics; full registry suite 156
  passed / 5 skipped (pre-existing skips).
- **🔴 GRANT-GATED:** image rebuild + redeploy of windy-registry; after
  deploy /health/full should read r2_bucket: 'ok'. (Un-flags the
  standing '🔴 R2-404 finding' from the procession ledger entry —
  nothing was ever down.)
- **Next:** the recurring cloud four (Mind first — SSH-free redeploy is
  the §7-urgent template) or windy-admin's get_config/get_logs/
  run_selftest.

## 2026-07-13 (night) — GAP-CLOSING #2: Translate ops baseline SHIPPED (last MF1 hole closed)

- **Platform taken: windy-translate** (gap-closing lane, impact order #2).
  windy-pro #235 + windy-contracts #20, both merged.
- **Shipped (all additive, services/translate-api/):** `GET /version`
  (MF1 canonical — was missing entirely, the fleet's last MF1
  non-compliance); **opt-in bearer wall** `WINDY_TRANSLATE_TOKEN`
  (per-request read, constant-time; /health + /version exempt; unset =
  today's open loopback, so prod unchanged until the Grant-gated env
  flip); `GET /ops/logs` (500-entry ring, content-free BY CONSTRUCTION
  — fixed event vocabulary + enum codes; worker errors categorized,
  never stored raw, since tracebacks can embed translated text);
  `POST /ops/selftest` (canary through the real NLLB worker + SQLite
  round-trip, per-stage pass/fail). require.main guard + exported app
  makes the service testable without the model; entry path unchanged.
- **Re-weave:** manifest 3→6 tools (get_status/get_logs/run_selftest
  gap→implemented); weave auth ept→install_token (WINDY_TRANSLATE_TOKEN)
  — a loopback internal service's real wall, not aspirational EPT.
- **📐 DOCTRINE CATCH (recorded in the manifest, worth every future
  manifest author knowing):** a tool payload must NOT use top-level
  `ok` — the ADR-060 invoke envelope reserves it, and the woven packet
  (correctly) reported an honest failing selftest as a failed CALL.
  Payload field renamed `passed`. Found only because the E2E drove the
  REAL service through the woven packet.
- **Proven:** 8/8 new node:test (npm test); boot smoke on the real
  entry path (ops ring captured real server_start/worker_start/
  worker_exit); **LIVE E2E** real MCP client → woven packet → the
  actual service with the wall ON (6 tools, MF1 get_status,
  content-free get_logs, honest per-stage selftest, token satisfied);
  conformance static byte-identical; make check green post-ADR-061
  (67 tests, 12 fixtures).
- **🔴 GRANT-GATED to go LIVE:** restart windy-translate.service from
  main; optionally set WINDY_TRANSLATE_TOKEN in its env (+ the same
  value in the ops-shim env) to turn the wall on.
- **Next:** impact order #3 = windy-registry R2-404 investigation
  (live prod degradation, may not be a code change), or the recurring
  cloud four starting with Mind.

## 2026-07-13 (night) — ADR-061 H2+H3 LANDED (Grant concurred): doctrine unified

- **windy-contracts #19.** Both reconciliation decisions canonized.
- **H2 trust vocab:** canonical = EI_CAPABILITY_MATRIX bands (Platinum≥900/
  Gold750-899/Standard600-749/Watch400-599/Untrusted<400). ADR-060
  SANDBOX/USER/TRUSTED/OWNER = deprecated aliases (validator accepts both;
  Mail's TRUSTED still validates). band-ei-mapping.v1 rewritten as canonical
  bridge + capability-class ladder (read→act-own→repair-own[Gold+]→operator).
  KEY: operator class (ops/healing knobs) gated by operator-role EPT, NOT EI —
  even Platinum grandma doesn't restart a service.
- **H3 one umbrella:** AGENT_CONTROL.md §1.1 absorbs the Fable-7.5 product law
  (3 surface archetypes: ops/hands/product); CONFIRM_FLOW.v1 + EI_CAPABILITY_
  MATRIX.v1 = shared consent/trust SoT. §3.5 = tier×band×class. No more 2 docs.
- make check 67. Cloud/code reconciliation COMPLETE.

## 2026-07-13 (night) — cloud/code reconciliation (ADR-061)

- **The cloud/code lane's MCP work RECONCILED** (windy-contracts #18). Verdict:
  COMPLEMENTARY, not competing. They built PRODUCT + repair-own surfaces
  (domains.mcp.v1/sites.mcp.v1: buy_domain, publish_site); ADR-060 built
  OPS/healing. They cite ADR-060 in code + reserved the ops slot (DNA D9.8 =
  §3.6 verbatim). Doctrine gains a 3rd archetype: product/agent-first.
- ADR-061 doc + domains(10)/sites(12) fixtures (validate 0 err, same tier
  vocab, money/publish always_confirm) + class enum alias 'cloud-service'→
  'cloud' (H1). make check 67.
- 🔴 TWO GRANT DECISIONS pending: H2 unify trust vocab (EI-matrix names vs
  SANDBOX/USER/TRUSTED/OWNER — lean EI-matrix); H3 one umbrella doctrine vs
  two docs (lean one umbrella, ADR-060).
- Follow-up (gap-closing): cloud cells still need their ops.mcp.v1 healing
  surface (D9.8 slot); windy-code MCP mostly unbuilt (Agent Bus over UDS).

## 2026-07-13 (night) — 🌟 GAP-CLOSING: Chat fleet-health aggregator SHIPPED (the fleet's biggest blind spot, closed)

- **Platform taken: windy-chat** (gap-closing lane, per GAP-CLOSING.md
  impact order #1). Chat was ~11 services + Synapse with NO externally
  reachable per-service health and NO aggregator — mostly blind.
- **windy-chat #143 (merged): `GET /api/v1/ops/health`** on onboarding
  (8101), the MULTI-SERVICE-OPS pattern made real: parallel fan-out to
  every service's internal /health + /version plus Synapse; overall
  ok/degraded/down (Synapse down ⇒ down); per-service
  status/version/commit/uptime/deps/duration. Auth = EPT (agents) OR
  account JWT / CHAT_API_TOKEN (humans/services), structured 401s name
  the remediation (§3.3). Privacy = WHITELIST-only forwarding (a planted
  content field provably never leaks — tested). Fleet registry =
  compose-DNS defaults, `WINDY_OPS_FLEET` env replaces wholesale
  (per-request read; prod pins the live set). Content-free
  `control.action` telemetry emit (§3.9). nginx `/api/v1/ops/` route
  added to the repo conf (authoritative superset).
- **windy-chat #144 + windy-contracts #17 (merged): re-weave.** Manifest
  now advertises the aggregator triad — get_health + get_status +
  get_capabilities, ALL bound to the one route. baseline_mapping 3 knobs
  gap→implemented; `$headline_gap` CLOSED. Procession test updated to pin
  the triad.
- **Proven:** 7 new node:test cases; onboarding suites 60/60 node:test +
  22/22 jest (1 integration-pro fail = pre-existing on main,
  stash-verified); loom validate 0 errors; woven packet booted; REAL MCP
  client E2E vs mock surface (3 tools, EPT bearer forwarded,
  constellation round-trip, unknown tool rejected); conformance static
  gate byte-identical; make check 62 green.
- **🔴 GRANT-GATED to make it LIVE:** (1) rebuild+`up -d --no-deps
  onboarding` (both compose files + `--env-file .env.production`),
  (2) add `/api/v1/ops/` location to the HAND-MANAGED live nginx conf
  (`nginx -t` + reload, never restart), (3) set `WINDY_OPS_FLEET` in live
  onboarding env to the actual live service set. Manifest honestly says
  "staged until deployed — probe before trusting mid-incident."
- **Next for chat** (informed by the new read view): per-service
  reconnect/restart knobs, get_logs (scrubbed), run_selftest (Synapse
  canary), SSH-free apply_update. Next for this lane: another
  GAP-CLOSING.md pick (Translate /version = smallest win, or Drops
  R2-404 investigation).

## 2026-07-13 (night) — L5 sentinel + gap-closing handoff (parallel lane)

- **Gap-closing FANNED OUT:** Grant handed a fresh Fable terminal the
  onboarding prompt (whole vision + canon pointers + per-platform gaps). It's
  running; it rotates through platform repos closing gaps. docs/GAP-CLOSING.md
  = its master menu.
- **This lane's PARALLEL, non-colliding work (new files only):**
  - `docs/GAP-CLOSING.md` — the master gap menu (every platform: repo, gaps,
    handoff, impact order).
  - **L5 coverage-parity checker** `loom/coverage.py` (+8 tests) — the standing
    sentinel: PHANTOM (manifest binds a dead route = bug) + UNCOVERED (served
    route not in manifest = candidate). Auto-joins make check via pytest.
  - `docs/coverage-report-2026-07-13.md` — ran it fleet-wide: **ZERO real
    phantom bindings** (2 flagged = verified-false extractor artifacts: FastAPI
    prefix non-resolution + Synapse external). Candidate menu per platform.
- make check now 62 tests. **⚠️ Two lanes now write windy-contracts — keep
  parallel work to NEW files; pull before editing PROGRESS.md.**

## 2026-07-13 (night) — Fly native server: FULL Capability Plane (agent-host DONE)

- **windy-agent #286: build_registry() now runs the real boot sequence** →
  the native MCP server exposes ALL 46 of Fly's capabilities across 13
  families (fs, shell, ssh, github, cloudflare, health/doctor, vision, skill,
  fleet, agent, setup, windyword, mcp), not the 6-tool windyword subset.
  Graceful fallback to minimal if substrate unavailable; WINDY_MCP_SERVER_
  MINIMAL=1 forces subset. Band-gating intact. Opt-in entrypoint, not in boot.
- Test isolated to temp db (WINDYFLY_DB_PATH), never touches real data. 441
  mcp/boot/capability tests green.
- **AGENT-HOST FULLY COMPLETE: Fly-as-patient (native server, whole registry,
  #282+#286) + Fly-as-doctor (mcp.* client, #285).**
- **All deferred infrastructure PRs now DONE.** Remaining = per-platform
  gap-closing (Chat aggregator, cloud redeploy hooks, Translate /version+auth,
  Word 8 baseline gaps) + cloud/code alignment + Grant-gated items.

## 2026-07-13 (night) — cloud discovery: /agent-surfaces (surfaces.json twin)

- **windy-pro #234: GET /api/v1/identity/agent-surfaces** — the cloud-side
  discovery primitive (ADR-060 §3.8), last unbuilt discovery piece. Hosted
  agent can't read ~/.windy/surfaces.json → account-server answers "what
  cloud ops surfaces does this human run?" in one authed call. New
  services/agent-surfaces.ts registry (product_accounts product → ops MCP
  descriptor {product,contract,mcp,class}; endpoints only, unknown omitted).
  Read-only, reuses ecosystem-status query (operator-aware, ADR-050), NO
  migration. 5 unit tests + 31 identity hardening green; tsc clean.
- **⚠️ FLAGGED to Grant: pre-existing FAILURE on windy-pro main** —
  `tests/api.test.ts › POST /api/v1/translate/text returns 200 without auth`
  fails on clean main (NOT mine — confirmed by running on main w/o my
  change). Violates "main must be green". Worth a look.
- **Both discovery halves now exist: local surfaces.json (loom/register.py)
  + cloud /agent-surfaces. Discovery layer COMPLETE.**

## 2026-07-13 (night) — Steamroller CLOSED-LOOP: fleet-version publisher

- **windy-admin #25: GET /v1/fleet-versions publisher** — the SENDING half's
  SoT, the last core Steamroller piece. /dashboard/fleet=DEPLOYED;
  /v1/fleet-versions=SHOULD-BE-INSTALLED. Data in app/data/fleet_versions.json
  (ops-maintained, force-added past data/ ignore), Pydantic-validated to
  fleet-version.v1 (no new dep). Public + content-free (+ secret tripwire
  test). Seeded: windy-word npm 1.11.0, windy-registry 0.1.0.
- **Proven E2E across both repos:** admin publisher output → windy-contracts
  loom/discovery.reconcile() → real must-update verdict + literal remediation
  npx windy-word-mcp@1.11.0. The Steamroller is now closed-loop.
- 6 new tests; full admin suite 134 passed, no regress.
- **Remaining deferred: account-server EPT discovery query; Fly native-server
  boot-wiring (build_registry full ctx); per-platform gap-closing (Chat
  aggregator, redeploy hooks, Translate /version+auth, Word 8 baseline gaps);
  cloud/code alignment; Grant-gated (npm publish, deploys, R2-404 finding).**

## 2026-07-13 (night) — 🔑 Fly-as-doctor: the mcp.* client (loop closed)

- **windy-agent #285 merged: the mcp.* client** — Fly can now DRIVE every
  woven surface. `mcp.list_servers` / `mcp.list_tools` / `mcp.call`. This is
  the piece that makes the whole instrumented fleet operable by grandma's
  agent ("fix my VPS" → real tool-call chain).
- Security (foreign servers = prompt-injection surface), all tested:
  ALLOWLIST-only, INDIRECTION (foreign tools never auto-merged into Fly's
  tool list — only via mcp.call; descriptions returned as flagged untrusted
  data), BAND (mcp.* = TRUSTED, per-server band_ceiling clamped ≥ TRUSTED,
  mcp.call floor = strictest server; SANDBOX/USER never see mcp.*), AUDIT on
  every call. Transport behind _CONNECTOR (opt-in mcp SDK). Inert by default
  (no servers configured → nothing connects; WINDY_MCP_CLIENT=0 disables).
  10 new tests incl. an injection-in-description case; 503 boot/capability
  tests green, zero regressions.
- **⚠️ SECURITY-SURFACE PR self-merged per standing authority — worth Grant's
  eyes; inert until he configures [mcp_client.servers].**
- **Both halves of Route C now exist: Fly-as-patient (native MCP server,
  #282) + Fly-as-doctor (mcp.* client, #285).** The agent-host is complete.

## 2026-07-13 (night) — 🏁 FLEET PROCESSION COMPLETE: Translate + Admin

- **Translate** (windy-pro #233): internal Node support svc (loopback:8099).
  3 reads (health w/ NLLB worker state; languages=capability; cache/stats).
  Honest gaps: no /version (MF1) + no auth today.
- **Admin** (windy-contracts #14 + windy-admin #24): super-admin dashboard.
  3 reads (health w/ db; version; dashboard/fleet=live /version fan-out
  @TRUSTED). /dashboard/fleet = natural Steamroller publisher home.
- **🏁 EVERY FLEET PLATFORM NOW HAS A DOCTRINE-COMPLIANT AGENT-CONTROL
  SURFACE.** 11 manifests, all validate, all placed in their repos:
  Word=D, Talk=D | Mind/Search/Mail/Chat/Clone/Drops/Translate/Admin=C | Fly=A.
- make check green (11 fixtures).
- **Campaign status: L0 (law) + L1 (Loom, 3 classes) + L2 (Steamroller) +
  L3 (all reference retrofits) + PROCESSION (whole fleet) = DONE.**
  What remains = the deferred careful PRs (admin fleet-publisher endpoint;
  account-server EPT discovery query; Fly mcp.* client; Fly boot-wiring;
  per-platform gap-closing incl. the multi-service aggregators) + cloud/code
  alignment when the sibling lane finishes + Grant-gated npm/deploy/publish.

## 2026-07-13 (night) — procession: Clone + Drops (live-production proof)

- **Clone** (windy-contracts #12 + Windy-Clone #57): clean Class C, 3 reads on
  windyclone.ai (health, version, providers=capability probe). No wrinkle.
- **Drops** (windy-contracts #13 + windy-registry #25): dev-name/brand split —
  brand=Windy Drops, service=windy-registry (matches /version + fleet key);
  SDK/spec in separate windy-drops repo. 3 reads on api.windydrops.com
  (health, version=MF1, health/full=deep probe Postgres+R2+JWKS).
- **🔴 FIRST LIVE-PRODUCTION PROOF:** the woven Drops packet drove real
  api.windydrops.com over stdio — get_capabilities returned db=ok, jwks
  pro+eternitas ok, and CAUGHT `r2_bucket: 'http 404'` (a genuine production
  degraded signal — flagged to Grant: R2 bundle bucket health probe failing).
- make check green (54, 10 fixtures). Retrofit map: Word=D, Talk=D, Mind=C,
  Search=C, Mail=C, Chat=C, Clone=C, Drops(windy-registry)=C, Fly=A.
- **Remaining procession: Translate, admin.**

## 2026-07-13 (night) — procession: Windy Chat + the multi-service pattern

- **Third procession platform, most instructive** (windy-contracts #11 +
  windy-chat #142). Chat = MULTI-SERVICE constellation (~13 Node services over
  Synapse, nginx path-routed). Finding: per-service /health NOT externally
  routed, no aggregator = biggest structural ops gap in the fleet.
- **New doctrine pattern discovered + canonized:** `docs/MULTI-SERVICE-OPS.md`
  — the fleet-health AGGREGATOR (one fan-out endpoint = get_health +
  get_status + get_capabilities), the template for any multi-service Windy
  platform. Chat's #1 build item.
- Honest thin manifest: 1 tool (get_health → Synapse /_matrix/client/versions,
  the core) + aggregator as $headline_gap. Validates, weaves, node-checks.
  make check green (54, 8 fixtures). Retrofit map: Word=D, Talk=D, Mind=C,
  Search=C, Mail=C, Chat=C, Fly=A.
- **Next: Clone, Drops, Translate, admin remain in the procession.**

## 2026-07-13 (evening) — procession: Windy Mail (Class C, first band_floor)

- **Second procession platform** (windy-contracts #10 + windy-mail #83). Mail
  ops.mcp.v1: 4 read routes on mail.windymail.ai (health incl. Stalwart =
  deliverability dimension, version, ready, stats). Canonical in
  windy-mail/contracts/.
- **Clarifying finding (not a wrinkle):** Mail's account mutations
  (suspend/reinstate/provision) + webmail are product/admin domain → stay out
  per §2 (same line as Mind /v1/chat, Search /v1/search). Reinforces where
  §2 sits. Mail = clean read-ops.
- **First per-tool band_floor:** get_stats = TRUSTED (admin-read); verified it
  rides into the woven Python twin. Trust-algebra caller-band axis exercised.
- make check green (53, 7 fixtures). Retrofit map: Word=D, Talk=D, Mind=C,
  Search=C, Mail=C, Fly=A.
- **Next: continue procession — Chat, Clone, Drops, Translate, admin remain.**

## 2026-07-13 (evening) — procession begins: Windy Search (Class C replication)

- **First fleet-procession platform** (windy-contracts #9 + windy-search #60).
  Pure replication of the Mind Class C pattern — NO new Loom mechanism, just a
  new manifest. Search ops.mcp.v1: 5 real read routes on api.windysearch.com
  (health, version, ready=capabilities, whoami, integrity-budget); product
  API (/v1/search,/fetch,/extract) stays out per §2. Canonical in
  windy-search/contracts/.
- baseline_mapping now exercises `unsupported` (stateless service:
  reconnect/safe-mode/reset) vs `gap` (config/logs/redeploy) — the validator
  warns only on gaps. Weaves remote http.js; all JS node-checks. make check
  green (52 tests, 6 fixtures).
- **Procession cadence proven fast:** validate → weave → node-check → place.
  Remaining fleet: Mail, Chat, Clone, Drops, Translate, admin — same recipe.
- **Next: continue procession (Mail = high value, or another) OR a deferred
  careful PR OR cloud/code alignment when sibling done.**

## 2026-07-13 (evening) — L2: the Steamroller + discovery ("land on a box")

- **The update-percolation half is built** (windy-contracts #8, ADR-060 §5 +
  §3.8). `schema/fleet-version.v1.json` (central version manifest) +
  `loom/register.py` (surfaces.json writer, atomic/0600/merge-by-product) +
  `loom/discovery.py` (reference reader: PROBE BEFORE TRUST → reconcile
  installed-vs-fleet → current/update-available/must-update, each with a
  LITERAL remediation = doctor pattern for updates).
- **Proven end-to-end:** agent lands on a box with Word (stale) + Talk (dead)
  → "Word: npx windy-word-mcp@1.11.0 (security fix); Talk down (resurrect)."
  The §0 promise mechanized. make check green (51 tests).
- `docs/STEAMROLLER.md` documents the flow + deferrals.
- **Deferred (out of this repo, each its own careful PR):** the admin
  publisher of the fleet manifest (windy-admin); cloud discovery via the
  account-server EPT query (identity-critical, windy-pro); per-surface
  check_for_update wiring (per platform).
- **Core infra is now COMPLETE: L1 (Loom, all 3 classes) + L2 (Steamroller +
  discovery) both done.** What remains is the FLEET PROCESSION (replication:
  Mail/Chat/Clone/Search/Drops/Translate...) + the deferred careful PRs +
  cloud/code alignment. **Next: procession, or a deferred PR, or alignment.**

## 2026-07-13 (afternoon) — L3 Class A: Fly retrofit — THE CLASS TRIAD IS COMPLETE

- **Loom learns Class A** (windy-contracts #7 + windy-agent #282). Fly's
  control surface is its in-process Capability Plane, so agent-host uses a
  NATIVE MCP server (a woven proxy would HTTP-hop to itself). Loom now:
  `server: native` → validate + emit ONLY the conformance driver; baseline
  tracked via `baseline_mapping` (role→cap id+status) not tool names;
  dotted capability names allowed; weave http/auth/package required only for
  woven servers.
- **windy-agent native server shipped** (opt-in, isolated, NOT in boot):
  `src/windyfly/mcp_server/` — pure bridge (tools/list = band-filtered
  registry, tools/call = registry.invoke; band-gating+audit free) + stdio
  entrypoint `windy-mcp-server`; `mcp` = optional dep. 8 tests vs Fly's real
  windyword.* caps. Canonical manifest in windy-agent/contracts/.
- **Diagnostic:** Fly rich in agent caps, has 8 healing-baseline gaps (with
  notes). Punch list `docs/handoffs/FLY-LANE-2026-07-13.md` incl. the big
  one: the `mcp.*` CLIENT (Fly-as-doctor, Route C) as its own security PR.
- make check green (41 tests, all 4 fixtures validate).
- **🎯 The Loom has now met all 3 classes: D (stdio+token), C (remote-http+
  EPT), A (native).** Every remaining platform is replication, not new
  mechanism — validating the "free re-weave" plan. **Next: L2 (Steamroller +
  account-server EPT discovery) OR the fleet procession (Mail/Chat/Clone/
  Search/Drops etc., each = author manifest→weave→prove→punch list→place) OR
  cloud/code alignment when sibling done.**

## 2026-07-13 (midday) — L3 Class C: Mind retrofit (Loom learns remote transport)

- **Loom now speaks Class C** (windy-contracts #6 + windy-mind #59). cloud
  weaves emit `src/http.js` — Streamable HTTP MCP at POST /mcp for HOSTED
  agents, with **EPT passthrough** (remote caller's Authorization forwarded
  verbatim; shim holds no ambient creds for remote callers). Emitters split:
  `server.js` (shared builder w/ authOverride) + `index.js` (stdio/local) +
  `http.js` (remote/cloud-only). Fixed http.js real-bound-port logging.
- **Mind `ops.mcp.v1`** authored — 5 real read routes on api.windymind.ai;
  named ops.* (inference API stays out per §2). baseline enforced on ops.*
  too. Canonical in `windy-mind/contracts/`.
- **Proven:** remote MCP client → /mcp → mock backend saw caller's EPT on
  every call (incl. query-arg /v1/route). make check green (37 tests).
- **Diagnostic:** Mind observable-but-not-healable — all 5 tools reads; no
  remote config/logs/redeploy. §7 urgent (Actions billing-lock). Punch list
  `docs/handoffs/MIND-LANE-2026-07-13.md`.
- **The Loom has now met all 3 classes' transport shapes** (D stdio+token,
  C remote+EPT; A = Fly, still pending but its native path already exists).
  Per the "free re-weave" doctrine, later platforms of each class are
  replication, not new mechanism.
- **Next:** Fly (Class A retrofit — completes the class triad) OR L2
  (Steamroller + account-server EPT discovery query) OR cloud/code alignment
  when the sibling lane finishes.

## 2026-07-13 (morning) — L3 begins: Word retrofit (first Gen-1 weave)

- **Loom gains Gen-1 `transport` bindings** (windy-contracts #5) — per-tool
  method+path so a hardened surface (Word :18765, 104 bespoke REST routes)
  is woven WITHOUT rewriting main.js. Client route table (GET→query /
  POST→body / none) + Python twin `_ROUTES`. Greenfield still defaults to
  `/invoke`. `baseline_status` + `transport` added to manifest schema.
- **Word manifest authored** (13 real transport-bound routes: implemented
  baseline + proven sound/settings) — canonical copy now in
  `windy-pro/contracts/control.mcp.v1.json` + weave.json (PR #232, contract
  files only, main.js untouched).
- **Proven end-to-end:** real MCP client → woven Word packet → mock surface;
  GET/query, POST/body, POST/none all dispatched with bearer token.
- **Diagnostic:** Word rich in features, poor in healing baseline — 8 of 13
  baseline knobs are GAPS (not advertised; a 404-ing apply_update mid-
  incident is worse than omission). Punch list:
  `docs/handoffs/WORD-LANE-2026-07-13.md`, matches §7.
- make check green (32 tests). Talk lane working its handoff in parallel;
  cloud/code still the sibling lane's (untouched).
- **Next:** L2 (Steamroller version-manifest + account-server EPT query;
  surfaces.json schema already pinned) OR next reference retrofit (Fly =
  Class A, or Mind = Class C) OR morning cloud/code alignment when that
  lane finishes. Word full-parity enumeration = batched follow-up.

## 2026-07-13 (night) — L1 part 2 shipped: THE LOOM WEAVES

- **`loom/generate.py` live** — one manifest + one weave config →
  (1) MCP packet (windy-word-mcp 3-file skeleton, low-level SDK,
  embedded byte-identical manifest, every tool proxying `POST /invoke`),
  (2) Python twin (windy-agent Capability registrations, band floors from
  the mapping table), (3) conformance driver (static byte-parity gate +
  live GET /tools parity gate). Deterministic output — regenerate-and-diff
  is itself a drift gate. Refuses to weave an invalid manifest.
- `schema/weave-config.v1.schema.json` pinned (product/class/http/auth/
  package; auth kinds: install_token | ept per ADR-060 §3.3).
- **Smoke-proven end-to-end:** wove Talk rev.6 → `npm install` → booted
  the packet → real MCP over stdio: initialize handshake OK, 24 tools
  listed, tools/call returns graceful isError when the surface is down,
  unknown tools rejected.
- `make check` green: 27 tests (16 validator + 11 generator incl.
  node --check, determinism, drift-catch, EPT variant).
- **LANE BOUNDARY (Grant, tonight):** a sibling Fable lane is building
  windy-cloud + windy-code MCPs — DO NOT TOUCH those repos. Morning task:
  align its output with ADR-060 (validate its contracts with the Loom,
  check trust algebra / remote transport / baseline / doctor triad),
  report deltas to Grant before changing anything.
- **Next:** L2 (Steamroller + surfaces.json + account-server EPT query)
  or L3 reference retrofit on a safe repo (Word/Fly/Mind/Search — NOT
  cloud/code).

## 2026-07-13 (later) — ADR-060 IS LAW; L1 part 1 shipped

- **PR #1 merged on Grant's word — the doctrine is law.**
- **L1 part 1 (this entry's PR):** canonical Talk contracts harvested from
  Windy 0 @ `9360058` (Mac tree's hands.mcp.v1 had drifted — trap confirmed);
  conformance suite extracted to `conformance/`; manifest schema v1 pinned
  (`schema/control-manifest.v1.schema.json`) — **first-citizen law proven:
  Talk rev.6 control + hands validate as-is, 0 errors**, and Talk's control
  surface passes the full 13-knob baseline; band↔EI mapping table pinned
  (`schema/band-ei-mapping.v1.json`); Loom validator live
  (`uv run python -m loom.validate`, jsonschema-backed, ERROR vs doctrine-
  WARNING split, `--strict` for v2-era); uv project + pytest; `make check`
  green (16 tests).
- **Next: L1 part 2 — the generator.** Emitters in order: (1) conformance
  driver, (2) MCP packet on the windy-word-mcp 3-file skeleton, (3) Python
  twin (windy-agent Capability registrations). Then L2.
- Open Grant-gates: npm publish windy-word-mcp@1.11.0; book-launch rebuild
  cherry-picks windy-pro #231.

## 2026-07-13 — P0 landed; ADR-060 drafted; lane infrastructure up

- **P0 (Word token wall) CLOSED:** windy-pro #231 (per-install token on
  :18765; the real hole was no-Origin `<img>`-GET drive-bys on the legacy
  action routes), windy-word-mcp #16 (v1.11.0, fresh-read token; **npm
  publish HELD for Grant** — publish before/with the next desktop build),
  windy-agent #281 (windyword.py token + 4xx JSON passthrough). All merged
  same day, local tests green (14 new jest / 12 pytest).
- **ADR-060 v1.0-draft opened as PR #1** in this repo. GATE: Grant's markup
  + merge. Superseded banner added to the archived Windy 0 ancestor.
- Repo genesis: README, archive, this ledger, LANE_KICKOFF.md.
- **Next:** on PR #1 merge → L1 (extract Talk conformance suite; manifest
  schema with Talk rev.6 as first citizen; the generator). Nothing in L1 is
  Grant-gated except the law merge itself.
- Open Grant-gates: PR #1 markup/merge; npm publish word for
  windy-word-mcp@1.11.0; book-launch-hardening rebuild must cherry-pick
  windy-pro #231 when commissioned.
