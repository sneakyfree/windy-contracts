# Doctrine-lane progress ledger

Append-only. Newest entry first. Every working session ends by adding an
entry here — a session that didn't update the ledger didn't happen.

---

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
