# ADR-060 — The Agent Control Doctrine

> **v1.0-draft — 2026-07-13.** The ecosystem law for giving agents hands.
> Canonized by the doctrine lane (OC5 Fable) from the Windy 0 handoff draft
> (preserved verbatim at `docs/archive/AGENT_CONTROL_DOCTRINE_DRAFT-windy0-2026-07-13.md`),
> extended with five amendments Grant delegated to Fable's final decision:
> platform classes, the Loom, the Steamroller, the unified trust algebra, and
> unified discovery. Windy Talk's `control.mcp.v1` rev.6 (candidate ADR-059,
> five adversarial review rounds) is the reference implementation this law
> was extracted from.
>
> **Status: DRAFT for Grant's markup — becomes law when the PR merges.**
> Change control thereafter: additive → v1.1 via PR; breaking → v2 file and
> tell Grant. Never silently mutate.

---

## 0. The objective, in Grant's words

The platforms may launch wobbly. That is allowed. What is **not** allowed is
a knob an agent cannot turn. The bet: frontier models are improving so fast
that within ~18 months, grandma's agent can diagnose and fix nearly anything
— **but only on surfaces that give it hands.** A brilliant model with no
control surface is a firefighter locked outside the building. So we ship the
best knobs, dials, and buttons any platform has ever had, and we let the
models compound in value for us instead of against us.

The single success metric, testable on every platform:

> **"Fix this for me."** On any machine or account running any mix of Windy
> products, an agent can enumerate every control surface present, read each
> product's health, and drive it back to green — including restarting,
> reconfiguring, safe-moding, and updating a product **even when that product
> is dead** — with zero human terminal use.

And the moat that makes agent-embrace safe where every other ecosystem
tripwires against bots: **every knob is identity-gated by Eternitas.** A
passport in good standing gets full human parity; no passport gets the
stinky-bot treatment. We can love agents because we can tell them apart.

---

## 1. The core principle — bilingual, co-tenant, one registry

Every knob a human can turn, an agent can turn too, **through the same code
path against the same live state**, in two languages:

1. **MCP** — the agent-standard protocol. How outside agents (Claude,
   ChatGPT, Cursor, whatever 2027 brings) speak. A first-class server, never
   an afterthought.
2. **Native** — direct HTTP (`GET /tools` + `POST /invoke`) and, for Python
   products, an importable in-process API. How Windy products drive each
   other, how tests drive everything, and how a supervisor heals a dead app.

**Both are thin adapters over ONE implementation of ONE knob.** If the two
transports can ever disagree about which tools exist or what they do, that is
a bug the conformance suite must catch — and the Loom (§5) exists so they
*cannot* drift, because both are generated from the same contract.

**Coverage-parity law:** *no dashboard-only actions, ever.* Any action that
exists in a UI exists as an agent-callable knob, or the PR does not merge.
This is the invariant that keeps the 2027 model from finding a locked door.

**Co-tenant rule:** the agent and the user share the same machine and the
same state; neither has a private back door.

---

## 2. The three platform classes

The Windy 0 draft was written for five desktop-era products. The fleet is
~20 platforms, most of them cloud. The doctrine therefore binds by **class**,
not by product — every platform declares its class and inherits that class's
transport, auth, and resurrection regime.

### Class D — Desktop co-tenant
*(Windy Word, Windy Talk, Windy Code desktop, future desktop apps)*

- **Transport:** loopback HTTP + stdio MCP (npm packet on the windy-word-mcp
  skeleton).
- **Auth:** the proven three-part wall — **per-install bearer token** (0600
  file, constant-time compare), **loopback-only bind**, **reject any request
  carrying an Origin header or a non-loopback Host**. No CORS, ever, no
  bypass env var. (Landed for Word in windy-pro #231 — the P0 that preceded
  this document; the no-Origin `<img>`-GET drive-by is the attack the token
  leg exists to stop.)
- **Resurrection:** "the doctor is not in the patient" (§3.6) — out-of-process
  supervisor + OS resurrection service (launchd / systemd / Task Scheduler),
  serving-path heartbeat, pid-verified kill tiers, ≤45 s relaunch budget.
  Windy Talk's supervisor + resurrection installer is the reference.

### Class C — Cloud service
*(Mind, Search, Mail, Chat, Clone, Cloud kernel + domains/sites/vps/code-web
cells, Drops, Translate, account-server, admin)*

- **Transport:** **remote MCP over Streamable HTTP** — a hosted agent must be
  able to reach grandma's cloud knobs over the internet; stdio-only MCP is a
  desktop luxury. Plus the platform's normal REST API. The MCP ops shim is
  **separate from the product API** (Mind's inference API is not its control
  surface).
- **Auth:** EPT (Eternitas passport) via the existing identity spine
  (`wi_` account → EPT → `wk_` bot key). Sensitive mutations confirm via
  **CONFIRM_FLOW.v1** (single-use HMAC tokens, voice-yes first-class).
- **Resurrection:** the ops plane lives **outside the patient** — health-gated
  redeploy, config-mutation, and log access are served by a different service
  (admin / the Cloud kernel) than the one being healed. An agent must be able
  to redeploy a dead cloud service without SSH. (The GitHub Actions billing
  lock makes this urgent, not optional — today a sick Mind can be observed
  but not healed.)

### Class A — Agent-host
*(Windy Fly / windy-agent)*

Fly is both patient and doctor, so it wears both faces:

- **As a surface:** wrap the existing command/capability registry in a
  `control.mcp` server with machine JSON envelopes (`{ok, result?, error?}`)
  — the trust gating already exists; this is a serialization shim. Fly must
  be healable by an outside agent like any other product.
- **As a client:** native Python tool modules remain the premium path to
  Windy family surfaces (deepest trust integration), **plus** a generic
  `mcp.*` client capability family — connect / list / call against
  allowlisted external MCP servers, every foreign tool wrapped as a
  Capability with an assigned band, sandboxed, audited. Foreign tool
  descriptions are untrusted input (prompt-injection surface); the allowlist
  and band ceiling are the whole point.

---

## 3. The nine things every platform ships

A platform is **doctrine-compliant** when all nine are true. Tri-state
`unsupported` is always allowed — a knob that genuinely doesn't apply reports
`unsupported`, never silently absent.

### 3.1 A frozen, versioned contract file
`contracts/control.mcp.vN.json` in the repo — and under the Loom (§5) this
file is not documentation, it is the **generative source** both adapters and
the conformance driver are woven from. Every tool entry: `name`,
utterance-first plain-English `description` (grandma-English — this is what
the model reads AND what Grant reviews), `inputSchema`, trust `tier`, and
`returns`. Change control: additive → minor bump via PR; breaking → new vN+1
file and tell Grant.

### 3.2 Bilingual dual transport
MCP server (JSON-RPC 2.0, full `initialize` lifecycle, `tools/list`,
`tools/call`, `structuredContent`) + native HTTP (`GET /tools` returning the
same list from the same registry, `POST /invoke {name, arguments}` →
`{ok, result?|error?}`). Python products additionally export the registry
in-process. Class C substitutes its REST API for loopback HTTP but must
still serve the `GET /tools` equivalent and the remote-MCP shim.

### 3.3 The security wall, per class
Class D: token + loopback + Origin/Host reject (§2). Class C: EPT +
CONFIRM_FLOW. Both: **structured, agent-readable errors** — a 401 names the
token path and the exact remediation; a denial returns
`{ok:false, error:"denied"}`, never silence. The wall's error messages are
themselves knobs: they tell the locked-out agent how to get the key.

### 3.4 The 13-knob baseline
The minimum vocabulary a fire-fighting agent needs, names and tiers lifted
from Windy Talk's contract. Every surface implements all thirteen (tri-state
where genuinely N/A):

| Knob | Tier | Purpose |
|---|---|---|
| `get_health` | auto_allow | First call when anything is wrong; plain-English "what's broken." |
| `get_status` | auto_allow | Runtime state — connected, which model, uptime. |
| `get_config` | auto_allow | Effective config, secrets redacted. |
| `get_logs` | auto_allow | Recent logs, scrubbed of secrets and content. |
| `run_selftest` | auto_allow | Exercise the core path; pass/fail per stage. |
| `get_capabilities` | auto_allow | Tri-state per feature — probed, not assumed. |
| `reconnect` | auto_allow | Re-establish the primary connection. |
| `restart_app` | ask_first | The supervisor does this, never the app itself. |
| `enter_safe_mode` / `exit_safe_mode` | auto / ask_first | Minimal known-good overlay. |
| `set_<setting>` | ask_first | Typed settings catalog **with undo** (Word's `describe_setting` + validated `set_setting` + 50-entry undo ring is the fleet's best — copy it). A firefighter that can't un-break what it just tried is dangerous. |
| `check_for_update` | auto_allow | Is a newer version available? (Wired to the Steamroller, §6.) |
| `apply_update` | always_confirm | The one RCE-by-design knob: attested, with last-known-good rollback. |
| `reset_to_defaults` | always_confirm | Factory reset, preserving user data. |

**The doctor triad, stated once:** every surface must answer *what's my
state* (health/status), *what's wrong* (doctor findings, structured), and
*here's the wrench* — every finding carries its remediation **as a literal
tool call**. That triad is what turns a frontier model from a smart observer
into a mechanic.

### 3.5 The unified trust algebra
The fleet currently speaks three trust dialects — Talk's tiers + autonomy
slider, Fly's bands, the cloud cells' EI-FICO matrix. The doctrine crowns
one algebra with **two axes**:

- **Knob danger tier** (in the contract, per tool): `auto_allow` /
  `ask_first` / `always_confirm`. Talk's vocabulary wins.
- **Caller identity band**: EPT integrity score (the EI_CAPABILITY_MATRIX
  bands), or "local co-tenant" on Class D where the human is present.

Effective behavior = tier × band. Fly's SANDBOX/USER/TRUSTED/OWNER bands map
onto EI score ranges (mapping table to be pinned in `schema/` during the
Loom phase). Confirmation UX differs by class — voice/tap on desktop,
CONFIRM_FLOW HMAC tokens in the cloud — but the algebra is one.

**Invariants no combination can override:** money actions and `apply_update`
always confirm, at every autonomy level, for every band. Agents can never
self-escalate — a standing grant is given by the USER via the confirmer,
never assumed. Denials are structured, never silent. Band filtering applies
to *discovery* too: a low-band caller never even sees the high-tier tools.

### 3.6 The doctor is not in the patient
The control surface must be hosted by a process the product cannot take
down. Class D: out-of-process supervisor + OS resurrection (heartbeat file
attesting the *serving* path, not a free-running timer; two staleness tiers;
pid-identity verification before any kill; a bare TCP accept never vetoes a
kill). Class C: the ops plane lives in a different service than the patient.
Either way, "the app is dead" is a condition the agent can *fix*, not a wall
it hits.

### 3.7 The shared conformance suite
`conformance/` in this repo (extracted from windytalk's
`mcp-conformance.v1.json`) — one rulebook every surface is tested against in
**both transports**, driven per-platform by a thin driver in each repo's
`make check`. While GitHub Actions is billing-locked, local gates ARE the
gates; the conformance driver is part of every platform's `make check`, no
exceptions.

### 3.8 The discovery registry — one read, every knob
**Local (Class D):** every product on startup writes one entry to
`~/.windy/surfaces.json` (0600): product, version, MCP endpoint, HTTP base,
token path, contract name+version. Products remove their entry on clean
shutdown; readers treat a dead port as stale and **probe before trust** — an
entry is believed only after its `get_health` answers.

**Cloud (Class C):** one query, not twenty — **account-server answers "what
does this human run?"** keyed by EPT. Account-server is already the identity
spine; it is the natural owner of the answer. No per-product DNS indexes.

Together: an agent landing anywhere enumerates every Windy knob the user
owns in one local read plus one authenticated query. This is what turns
twenty products into one machine an agent can fully operate.

### 3.9 Content-free telemetry
Every surface emits `control.action {product, tool, ok, error?, tier, mode}`
per invocation to the admin ingest — ids/counts/outcomes only, never
content; the schema rejects content keys. Fire-and-forget, inert unless
configured. This is how we learn which fires actually happen and which knobs
agents fumble — and it feeds the Steamroller's version census.

---

## 4. The Loom — why twenty surfaces stay one surface

Windy Talk froze its contract by hand at the cost of five adversarial review
rounds. Magnificent once; unaffordable twenty times over years of revisions.
The Loom industrializes it:

- **One manifest per platform** (`contracts/control.mcp.vN.json`), written in
  grandma-English utterances. The manifest is the ONLY artifact a human
  edits — and because it is plain English, **Grant can personally read and
  certify every knob in the fleet without reading code.**
- **The generator** (this repo, `loom/`) weaves from it: the MCP packet
  (npm, windy-word-mcp 3-file skeleton), the Python twin (Fly Capability
  registrations), the HTTP router skeleton, and the conformance driver.
- **Parity is a test, not a hope:** floor-count + schema equality across
  both transports, generated alongside the adapters.
- Hand-written escape hatches are allowed for bespoke tools (doctor
  internals), but they still appear in the manifest and still pass
  conformance.

Sequencing note: Talk's rev.6 contract becomes the manifest schema's first
citizen. Word's 115-tool surface (currently hand-mirrored in the npm
wrapper, "after-the-fact and can drift" per the Windy 0 draft) is the first
Gen-1 → Loom migration, done carefully — the packet is live on npm.

---

## 5. The Steamroller — updates that percolate everywhere

The receiving knobs (`check_for_update` / `apply_update`) are §3.4. This
section is the **sending** half — without it, twenty platforms' fixes reach
nobody:

- **Release rails, by class:** npm + MCP registry for packets; R2 +
  `downloads.<domain>` for desktop builds (the proven pattern); image
  rebuild for cloud services.
- **The fleet version manifest:** one service (admin) publishes
  current/minimum versions per product per channel. `check_for_update` on
  every surface resolves against it.
- **Self-describing staleness:** every surface serves its live contract
  version; every packet compares itself on connect and reports its own
  staleness *with the remediation as a literal command*
  (`npx windy-word-mcp@latest`). A stale client is a doctor finding like any
  other.
- **`apply_update` is attested + rolls back:** signed artifact, checksum
  verified, last-known-good preserved, health-gated post-update, automatic
  rollback on a failed gate. This knob is RCE-by-design; it gets the most
  paranoid treatment in the fleet.
- **Staged rollout + census:** telemetry (§3.9) reports version distribution
  in the wild to an admin tile; rollouts go rings (Windy 0 fleet → early →
  everyone) with the census as the gate.
- **The agent is the update channel.** Grandma never reads a changelog. Her
  agent tells her: *"Windy Word has a fix for the thing that glitched
  yesterday — want me to apply it?"* — and the always_confirm tier makes
  that exchange safe. Updates become a conversation, which is the most
  Windy sentence in this document.

---

## 6. What this doctrine deliberately does NOT do

- It does not add a fourth trust dialect (§3.5 unifies the three that
  exist).
- It does not put the doctrine's machinery in `kit-army-config` (credentials
  SoT stays clean) nor in any product repo (no product owns the law).
- It does not require MCP for product-to-product calls — Windy products
  drive each other over native HTTP/Python (cheaper, deeper); MCP is the
  lingua franca for *outside* agents.
- It does not gate the healing floor. **The 13-knob baseline is free in
  every build of every product, forever** — including Word's reader/free
  editions. The full deluxe panel (Word's 115) may be entitlement-gated;
  the ability to be *healed* is a right, not a product. (Decision 3, §8.)
- It does not wait for stability. Knobs first, polish forever after — the
  whole point is that the platforms are allowed to be baby giraffes while
  the knobs are bulletproof.

---

## 7. Fleet punch list (roll-up)

Class D — **Word**: token wall LANDED (windy-pro #231 + windy-word-mcp #16 +
windy-agent #281, all merged 2026-07-13); needs supervisor+resurrection,
safe-mode/reset/logs knobs, real `apply_update`, contract extraction into
the Loom, `surfaces.json` registration, and the free-build baseline un-gate.
**Talk**: the reference; needs engine-box surface, account/billing knobs,
`surfaces.json`. **Code desktop**: inherits at its next milestone.

Class A — **Fly**: `control.mcp` server shim over the existing registry;
machine JSON envelopes; typed settings catalog + undo for `windyfly.toml`;
supervisor beyond bare systemd `Restart=`; the `mcp.*` client family;
`surfaces.json`.

Class C — **Mind** first (ops shim = the cloud-class template; SSH-free
redeploy is urgent), then Search (cleanest leaf, first full Loom
pilot), then Mail / Chat / Clone / Cloud kernel + cells (cells inherit at
birth per their DNA v0.2.0 MCP-packet law — this doctrine supersedes and
absorbs that clause), then the rest. **Hand**: inherits at birth, nothing to
retrofit.

Per-product detail lives in each repo's punch-list issue, opened when its
procession slot arrives (§9).

---

## 8. Decisions log (the six open questions, closed)

1. **Home for the canon:** this repo (`windy-contracts`). Not
   kit-army-config (credentials stay separate); not any product repo.
2. **`surfaces.json`:** schema owned here; local file per box; cloud side
   answered by account-server keyed by EPT; stale entries reaped by
   probe-then-expire.
3. **Word's `AGENT_CONTROL` gate:** the 13-knob healing floor is free in
   every build forever; the deluxe panel stays entitlement-gated. Healing is
   a right; power is a product.
4. **Tokens:** per-product, least-privilege, paths recorded in
   `surfaces.json`. Never shared across products.
5. **Mind and MCP:** a real thin MCP shim over its ops endpoints on remote
   transport, separate from the inference API — and that shim is the
   Class C template.
6. **Versioning:** one doctrine version (this file), independent per-product
   contract versions. A product states which doctrine version it complies
   with in its contract's header.

---

## 9. Build order (one lane, canon-first, no clock)

- ~~**P0** — Word's token wall~~ **DONE 2026-07-13** (windy-pro #231,
  windy-word-mcp #16 / v1.11.0, windy-agent #281).
- **L0 — this document** merges after Grant's markup. The doctrine is law.
- **L1 — the Loom:** extract Talk's conformance suite into `conformance/`;
  pin the manifest schema (Talk rev.6 = first citizen); build the generator;
  pin the band↔EI mapping table.
- **L2 — the Steamroller + the registries:** version-manifest service,
  `surfaces.json` schema + writers, account-server EPT query.
- **L3 — reference retrofits, one per class:** Word (D), Fly (A), Mind or
  Search (C). Each ends in a certification: manifest blessed by Grant,
  conformance green in `make check`, doctor triad answering all three
  questions, telemetry flowing.
- **L4 — the procession:** the remaining fleet, launch-priority order, one
  platform at a time, same certification each.
- **L5 — the standing sentinel:** coverage-parity lint (no endpoint merges
  without a manifest entry), fleet census tile, telemetry-fed manifest
  revisions. Never ends.

---

*Provenance: extracted from Windy Talk's proven Gen-3 pattern (ADR-058,
candidate ADR-059) via the Windy 0 handoff draft, archived unmodified in
`docs/archive/`. Amended and canonized by the doctrine lane. The Windy Talk
lane remains the pattern donor and owns nothing here; this repo owns the
law; each platform owns its compliance.*
