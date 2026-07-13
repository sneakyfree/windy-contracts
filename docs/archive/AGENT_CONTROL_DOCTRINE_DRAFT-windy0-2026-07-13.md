# AGENT_CONTROL.md — The Windy Ecosystem Agent-Control Doctrine

> **DRAFT v0.1 — 2026-07-13.** Authored by the Windy Talk Fable instance (Windy 0)
> as a handoff to the OC5 Fable instance leading the ecosystem-wide "bilingual
> control" DNA strand. This is a *canon of truth* proposal: make every Windy
> product speak **both languages — MCP and native (Python/HTTP) — over one shared
> control surface**, so that no matter how badly a product is on fire, a future
> capable model (Fable 9 / Opus 7.x, ~18 months out) can reach in, grab every
> knob, dial, and alarm, and put the fire out — by voice, autonomously.
>
> Nothing here is invented from scratch. **Windy Talk already implements ~90% of
> this pattern** (contract-first, dual-transport, tiered, supervised, resurrected).
> The job is to *promote Talk's pattern to ecosystem law* and close the gaps in the
> other four products. This doc = the pattern + the evidence + the punch list.

---

## 0. The fire-alarm thesis (why this is worth doing now)

Look at how far the models came in one year. In ~18 months, grandma will be talking
to something that can diagnose and fix almost anything — **but only if we gave it
hands.** If Windy Word wedges, or her agent's config rots, or the engine box hangs,
the 2027 model is *helpless* unless every one of those surfaces exposes a knob it can
turn. A brilliant model with no MCP/API surface is a firefighter locked outside the
building.

So the doctrine's success metric is a single sentence:

> **"Fix this for me."** — On a machine running any mix of Windy products, an agent
> can enumerate every control surface present, read each product's health, and
> drive it back to green — including restarting, reconfiguring, safe-moding, and
> self-updating a product **even when that product is dead** — with zero human
> terminal use.

Today that's true for **1.5 of 5 products.** This doctrine makes it true for all.

---

## 1. The core principle — BILINGUAL, CO-TENANT control

Every knob a human can turn, an agent can turn too, **through the same code path
against the same live state**, exposed in **two languages**:

1. **MCP** — the agent-standard protocol (JSON-RPC, `initialize` lifecycle,
   `tools/list` + `tools/call`, `structuredContent`). This is how an LLM agent
   speaks. Ship it as a first-class server, not an afterthought wrapper.
2. **Native (Python / local HTTP)** — a direct programmatic path: `GET /tools`
   + `POST /invoke` over loopback HTTP, and/or an in-process Python API. This is
   how the product's own code, tests, other Windy products, and non-MCP callers
   reach the same knobs.

**Both transports call ONE implementation of ONE knob.** They are thin adapters over
a shared registry — never two parallel code paths that can drift. (Windy Talk's
`hands/surface.py` is the reference: it "exposes the tool list as *both* MCP tools
and local HTTP" — ADR-058 §D4 co-tenant pattern.)

**Co-tenant rule (from the Windy Talk DNA plan §6/§7):** *every action has a human
path AND an agent-callable path sharing state, gated by trust tiers.* The agent and
the user are co-tenants of the same machine — neither has a private back door.

Why "bilingual" and not just MCP? Because (a) MCP servers die when their host
process dies — you need a native/HTTP path that a supervisor can keep alive to heal
a dead app; (b) Windy products call each other's knobs today (Fly already drives
Word's dials) and that's cheaper over HTTP than MCP; (c) tests and CI need the native
path. MCP is the *lingua franca for agents*; native is the *plumbing*. Every knob
must answer in both.

---

## 2. Where we are — the three generations (honest current state)

| Gen | Product | Pattern | Verdict |
|---|---|---|---|
| **Gen 1 — organic** | **Windy Word** (`windy-pro` + `windy-word-mcp`) | An HTTP server that began as a Wayland keybinding workaround and accreted 101 endpoints on `127.0.0.1:18765`; MCP bolted on later as a separate npm package (~115 tools, 22 categories). | Biggest surface, weakest guarantees. No auth token, dies with the app, no self-update, gated off (`AGENT_CONTROL:false`) in free builds. |
| **Gen 2 — chat-native** | **Windy Fly** (`windy-agent`) | 99 slash-commands / 14 categories reachable *only by being a chat participant*; output is **prose for humans**, not a machine envelope. IPC bridge (`uds_server.py`, ~45 JSON-RPC methods) exists but is internal. | Rich + trust-gated, but **no agent-facing machine API.** An external agent must screen-scrape text. |
| **Gen 3 — contract-first** | **Windy Talk** (`windytalk`) | Frozen versioned JSON contracts, **dual MCP + HTTP transport**, per-install bearer token, three trust tiers enforced at the surface, tri-state capabilities, **out-of-process supervisor + OS resurrection**, shared conformance suite, content-free telemetry. Reviewed 5 adversarial rounds. | **This is the doctrine.** The only surface designed so the agent can heal the product *even when the product is dead*. |
| (Gen 4 — cloud REST) | **Windy Mind** (`windy-mind`) | Plain OpenAI-compatible cloud REST. Fine as a *service*, but lacks the ops half (no config-mutation, no logs, redeploy is SSH-only because GitHub Actions is billing-locked). | Observe-only; needs ops hooks. |
| (stub) | **Windy Hand** (`windy-hand`) | 3 files (README + CLAUDE.md + ADR-WH-001). Deliberately parked behind Windy Search's front door — never agent-facing in Phase 1–2. | Nothing to retrofit; inherit doctrine at birth. |

**The work is extraction, not invention:** lift Talk's Gen-3 pattern into a shared law
and retrofit Words/Fly/Mind to it.

---

## 3. THE DOCTRINE — what every Windy product MUST ship

A product is "doctrine-compliant" when it ships all nine of the following. Tri-state
`unsupported` is always allowed (a knob that genuinely doesn't apply reports
`unsupported`, never silently absent) — but the *shape* must be present.

### 3.1 — A frozen, versioned contract file
`contracts/control.mcp.vN.json` in the repo. The contract is the DNA; the
implementation conforms to it, never the reverse. **Change control (verbatim from
Windy Talk):** additive change → bump the minor in place via PR (`v1` → `v1.1`);
breaking change → a **new `v2` file AND tell Grant.** Never silently mutate a frozen
contract. Each tool entry carries: `name`, `description` (agent-facing — this is
what the model reads), `inputSchema`, and a **trust `tier`** (§3.5).

### 3.2 — Bilingual dual transport (MCP + native)
- **MCP server:** JSON-RPC 2.0, protocol `2025-06-18`, full `initialize` handshake,
  `tools/list`, `tools/call`; tool results carry canonical-JSON as `structuredContent`.
- **Native/HTTP:** `GET /tools` (returns the same list the MCP server serves — one
  source) and `POST /invoke {name, arguments}` → `{ok, result?|error?}`. Python
  products additionally expose the registry as an importable in-process API.
- **One registry, two adapters.** If the two transports can ever disagree about
  which tools exist or what they do, that's a bug the conformance suite (§3.7) must
  catch. Cloud services (Mind) substitute their REST API but MUST still publish a
  `GET /tools`-equivalent (OpenAPI) and implement the §3.4 baseline.

### 3.3 — The security wall (identical on every desktop surface)
- **Loopback bind only** (`127.0.0.1`) — never `0.0.0.0`.
- **Per-install bearer token**, compared in **constant time**. Generated at install,
  stored `0600`, path recorded in the discovery registry (§3.8). *(This is the one
  thing even Windy Word lacks today — retrofit it first; a tokenless loopback server
  is reachable by any local process, including a malicious page's localhost fetch.)*
- **Reject any request carrying an `Origin` header, and any non-loopback `Host`.**
  No CORS, ever. (Blocks browser-based DNS-rebinding / drive-by localhost attacks.)
- Cloud surfaces use their existing auth (JWT / EPT / `wm_`/`wk_` keys).

### 3.4 — The 13-knob baseline (every surface implements these, tri-state OK)
This is the minimum vocabulary a fire-fighting agent needs. Names and tiers are
lifted from Windy Talk's `control.mcp.v1`:

| Knob | Tier | Purpose |
|---|---|---|
| `get_health` | auto_allow | **The first tool when anything is wrong.** One call → plain-English "what's broken." |
| `get_status` | auto_allow | Current runtime state (connected? which model? uptime?). |
| `get_config` | auto_allow | The effective config (secrets redacted). |
| `get_logs` | auto_allow | Recent logs, **scrubbed** of secrets/content. |
| `run_selftest` | auto_allow | Actively exercise the product's core path; report pass/fail per stage. |
| `get_capabilities` | auto_allow | Tri-state (`true`/`false`/`unsupported`) per feature — honest, probed not assumed. |
| `reconnect` | auto_allow | Re-establish the product's primary connection. |
| `restart_app` | ask_first | Restart the whole product (see §3.6 — a supervisor does this, not the app itself). |
| `enter_safe_mode` / `exit_safe_mode` | auto / ask_first | A minimal known-good overlay to get back to *some* working state. |
| `set_<setting>` | ask_first | Mutate a setting via a **typed settings catalog with undo** (see below). |
| `check_for_update` | auto_allow | Is a newer version available? |
| `apply_update` | always_confirm | **The one RCE-by-design knob** — ship a fix. MUST be attested + carry Last-Known-Good rollback. |
| `reset_to_defaults` | always_confirm | Factory reset (preserve user data/history). |

**Typed settings catalog with undo** deserves emphasis: Windy Word has the best
settings design in the fleet — a *typed* catalog (`describe_setting` → type + current
+ enum), validated `set_setting`, side-effect propagation (e.g. hot-reloads the STT
engine), and a **50-entry undo ring buffer.** Every product's `set_<setting>` should
follow that shape: validate against a schema, apply with side effects, record an undo
step. A firefighter that can't *un-break* what it just tried is dangerous.

### 3.5 — Trust tiers (enforced at the surface, not by the caller)
Three tiers, per tool, mapped to the autonomy slider (ADR-010 §9):
- **`auto_allow`** — execute immediately (all read/diagnose knobs).
- **`ask_first`** — per-invocation confirmation; user MAY grant a session-scoped
  always-allow (recovery knobs).
- **`always_confirm`** — per-invocation confirmation, no session upgrade possible
  (nuclear knobs: `apply_update`, `reset_to_defaults`, `run_shell`).

A denial returns `{ok:false, error:"denied"}` — **never silence.** The tier is
enforced *at the surface*, so a compromised or confused agent can't escalate itself.

### 3.6 — "The doctor is not in the patient" (supervisor + resurrection)
The control surface MUST be hosted by a process the product **cannot take down.** If
the surface lives inside the app and the app crashes, the surface dies with it —
chicken-and-egg: you can't ask a dead app to restart itself. So:
- **Desktop:** the surface (or a thin supervisor that owns it) runs out-of-process,
  kept alive by an **OS resurrection service** (launchd on macOS / systemd on Linux /
  Task Scheduler on Windows) with **identity-aware, pid-verified kill tiers** so it
  revives the *right* process and never SIGKILLs a stranger. Windy Talk's
  `enter_safe_mode`, `restart_app`, and the resurrection installer are the reference.
- **Cloud:** the surface is the always-on service; "resurrection" = a health-gated
  auto-redeploy hook (see the Mind punch list — the Actions billing-lock makes a
  no-SSH redeploy path *urgent*).

### 3.7 — Shared conformance suite
`contracts/mcp-conformance.vN.json` — **one shared rulebook** that every product's
surface is tested against, in both transports, so implementations can't drift from
the contract. Windy Talk already has this (it catches, e.g., a `str()`-serialization
bug and a missing `initialize` lifecycle). **Action:** extract it from the windytalk
repo to a shared home (proposal: `kit-army-config/contracts/` or a new
`windy-contracts` repo) and have each product add a thin driver.

### 3.8 — The discovery registry (THE ONE GENUINELY NEW PIECE)
Today an agent landing on grandma's box has **no way to know what Windy surfaces
exist, on what ports, behind what tokens.** Fix it: every product, at startup, writes
one entry to a well-known local file:

```
~/.windy/surfaces.json      (0600)
{
  "surfaces": [
    { "product": "windy-word", "version": "1.6.2",
      "mcp": "stdio|ws://127.0.0.1:18765/mcp", "http": "http://127.0.0.1:18765",
      "token_path": "~/.windy-word/control.token", "contract": "control.mcp.v1" },
    { "product": "windy-talk", "http": "http://127.0.0.1:8782",
      "token_path": "~/.windytalk/control.token", "contract": "control.mcp.v1" },
    ...
  ]
}
```

One read → the agent enumerates **every knob on the machine.** Products remove their
entry on clean shutdown (and the reader treats a dead port as stale). Cloud services
register in a well-known DNS/JSON index (e.g. `surfaces.windymind.ai`). *This is what
turns "N isolated products" into "one machine an agent can fully operate."*

### 3.9 — Content-free telemetry
Each surface emits `control.action {product, tool, ok, error?, tier, mode}` per
invocation to `admin.windyword.ai` — **ids/counts/outcomes only, never content.** The
schema must *reject* content. (Windy Talk's `telemetry.v1` is the reference; missing
telemetry is a bug.) This is how we learn which fires actually happen in the field.

---

## 4. Per-product punch list (current → doctrine-compliant)

| Product | Has | Needs to reach compliance |
|---|---|---|
| **Windy Talk** ✅ | The whole Gen-3 pattern (24 control + 12 hands tools, dual transport, token, tiers, supervisor, resurrection, conformance, telemetry). | (a) Build the **engine-box** control surface — `server/` is an empty stub, so a wedged 5090 engine can only be *fallen away from*, not healed. (b) Add account/billing knobs (Word has 6). (c) Register in `surfaces.json`. |
| **Windy Word** ⚠️ | 115 tools / 22 categories; the fleet's **best typed-settings-with-undo** design; `/app/restart` + `/app/quit`; account+billing. | (a) **Add the per-install bearer token** (only live surface without one). (b) Move the surface behind an out-of-process **supervisor + resurrection** (today it dies with Electron). (c) Add `enter/exit_safe_mode`, `reset_to_defaults`, `get_logs`, and a real `apply_update` (only `check` exists). (d) **Freeze a contract file** extracted from `main.js` (the npm wrapper is after-the-fact and can drift). (e) Un-gate for the doctrine baseline: `AGENT_CONTROL:false` currently 404s the control routes in free/reader builds — the *baseline 13 knobs* must be available even there (or the fleet can't be healed). (f) Register in `surfaces.json`. |
| **Windy Fly** ⚠️ | 99 commands / 14 categories, channel policy + Eternitas trust gating, a working IPC bridge (`uds_server.py`, ~45 methods incl. `agent.respond`). Already *consumes* Word's surface. | (a) **Wrap the existing command registry in a `control.mcp` MCP server** with a `{ok,result,error}` envelope — the registry + trust-gating already does the hard part; this is a serialization shim. (b) Emit machine JSON, not prose. (c) Give config a **typed settings catalog + undo** (today it's raw `windyfly.toml` edits). (d) Add a supervisor beyond bare `systemd Restart=`. (e) Register in `surfaces.json`. |
| **Windy Mind** ⚠️ | OpenAI-compatible REST, `/health/providers`, `/version`, `/v1/route`, runtime claim/heartbeat/release, `/admin/keys`. | (a) `get_logs` endpoint. (b) A **validated runtime-config** endpoint (provider keys are env-at-deploy today → any change = redeploy). (c) An **SSH-free redeploy hook** — **urgent** because GitHub Actions is billing-locked, so an agent can *observe* a sick Mind but cannot heal it. (d) Implement the Mistral adapter (catalogued, no adapter). |
| **Windy Hand** ✅(n/a) | Nothing (stub, parked behind Windy Search per ADR-WH-001). | **Inherit the doctrine at birth** when it's built — ship compliant from commit 1. Nothing to retrofit. |

---

## 5. Reference implementation — copy Windy Talk

The OC5 lead should read these files as the canonical pattern (all in
`~/Desktop/Grant's Folder/windytalk/`):

- `contracts/control.mcp.v1.json` — the 24-tool contract, rev.6, 5 adversarial
  review rounds. **The template for every product's contract.**
- `contracts/hands.mcp.v1.json` — the 12-tool "drive OTHER apps" surface + trust
  tiers + the co-tenant `$comment` describing the dual MCP/HTTP exposure.
- `contracts/mcp-conformance.v1.json` — the shared rulebook to extract fleet-wide.
- `apps/desktop/electron/control/tools.ts` — all 24 control tools implemented; the
  MUTATING / SET_TOOLS sets, the CONFIRM_MESSAGES map, tier enforcement.
- `apps/desktop/electron/control/supervisor.ts` + `resurrection/installer.ts` — "the
  doctor is not in the patient" + OS resurrection with pid-verified kill tiers.
- `hands/surface.py` — the Python side of the co-tenant pattern (one registry served
  as both MCP and HTTP).
- `docs/CONTROL_BUILD_NOTES.md` + `docs/CONTROL_SURFACE_DESIGN.md` — the design
  rationale and the five-round review history.

For the "best settings design" to copy: **Windy Word's** `main.js` settings catalog
(`describe_setting` / `set_setting` with validation + side-effect propagation +
50-entry undo ring) — and its MCP wrapper `windy-word-mcp/src/index.js`.

For the cross-product-control precedent: `windy-agent/src/windyfly/agent/capabilities/windyword.py`
(Fly reaching over to turn Word's dials on `127.0.0.1:18765`).

---

## 6. Open design decisions for the lead (flag to Grant)

1. **Where does the shared conformance suite + contract templates live?** Proposal:
   a new `windy-contracts` repo (or `kit-army-config/contracts/`) that all products
   git-submodule or vendor, so `control.mcp.vN.json` + `mcp-conformance.vN.json` +
   the doctrine itself are one source of truth. **This IS the "DNA strand master
   plan" home.**
2. **`surfaces.json` schema + ownership** — who defines it, where cloud services
   register, how stale entries are reaped. It's new; get it right once.
3. **Word's `AGENT_CONTROL` gate.** The baseline 13 knobs must work even in
   free/reader builds (else the fleet can't be healed), while the *full* 115-tool
   surface can stay entitlement-gated. Decide the split.
4. **Token distribution across products** — one shared `~/.windy/` token dir vs
   per-product tokens. Per-product (recorded in `surfaces.json`) is cleaner and
   least-privilege; confirm.
5. **Bilingual for cloud (Mind):** does Mind ship a real MCP server, or is
   OpenAPI + the baseline REST endpoints "MCP-equivalent enough"? (Leaning: a thin
   MCP shim over its ops endpoints, separate from the `/v1/chat` inference API.)
6. **Versioning across five products** — do they share one doctrine version, or does
   each product's `control.mcp.vN` version independently against a shared doctrine
   spec version? (Leaning: independent tool contracts, shared doctrine version.)

---

## 7. Appendix — the compute/consolidation context (why this matters for the whole vision)

This doctrine is one half of a bigger consolidation the Windy Talk instance mapped.
Context the OC5 lead should hold:

- **Windy Word's "7 local LLMs" are STT (Whisper/CT2) engines, not reasoning brains.**
  Talk/Word/Fly are three *jobs* sharing layers: local STT + local TTS + a cloud
  brain via **windy-mind** (the BYOM broker — one account/key powers all three).
- **"Voice = your agent" is already built:** Windy Talk's `agents/windyfly.py` drives
  the user's real Fly agent via `agent.respond` (Talk is a *channel*, not a second
  brain). Pre-hatch, `brains/mind.py` is a generic "Windy Buddy" on the user's own
  windy-mind account.
- **One identity spine** already spans the ecosystem: Windy account (`wi_`) →
  Eternitas passport (`EPT`, the compute credential Mind honors) → bot key (`wk_`).
- The agent-control doctrine is what lets that consolidated system be **operated and
  healed by voice** — the knobs half of "voice = your agent." Without it, the
  consolidation is drivable but not *fixable*.

**Bottom line for the lead:** the thesis is already proven once (Talk's control
surface is exactly the "hands on every knob" a 2027 model needs, and Fly already
demonstrates cross-product control). ~1.5 of 5 products are compliant. Your DNA strand
= promote Talk's Gen-3 pattern to law, add the `surfaces.json` discovery registry,
extract the shared conformance suite, and run the per-product punch list in §4.

---

*— Handoff from the Windy Talk Fable instance. Questions / the live reference impl are
on Windy 0; I'm continuing to focus on Windy Talk. This draft is yours to own, rewrite,
and canonize.*
