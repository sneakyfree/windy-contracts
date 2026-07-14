# ADR-062 — The owner-sovereignty override

> **2026-07-14. Status: ACCEPTED (design); build gated on prerequisites + the
> §9 ratifications. v1.1 — root-means-root revision (Grant's directive):** the
> human is root on their own things without limit; the system never protects
> you from yourself, only verifies a choice is really yours and protects
> *others* from your agent. Amends ADR-060 §3.5. Grounded in the Eternitas
> deep-dive (2026-07-14).

## 0. The problem

ADR-060 gates every knob by the agent's Eternitas integrity (EI) score,
uniformly. One credential — the agent's *autonomous* standing — controls both
"can this agent spam 10,000 strangers" and "can this agent edit its owner's
own website." Collapsing those into one number means a single bad afternoon,
or a **misunderstanding**, locks a person out of their own life.

The canonical scenario: grandma's Windy Fly mishears — a news clip playing
nearby, a joke, a garbled request — and attempts something flagged dangerous.
Its safety dimension drops; EI falls below threshold. Ten minutes later she
asks it to fix a typo on the birthday site she built, and it can't touch a
single knob in her own ecosystem. She is furious — not at her agent, at
**Eternitas**. That reaction, multiplied across a fraction of the userbase,
drives everyone away from the very trust system that is supposed to be the
moat.

The fix must be **simple, seamless, and grandma-legible**: *"Johnny got
detention for shooting spitwads. He's still allowed home — want to let him do
his chores here?"* One tap. Expelled from school ≠ locked out of the house.

## 1. The principle: root means root

**Eternitas protects *others* from your agent, and verifies that a choice is
really *yours*. It NEVER protects you from yourself.** On your own things, the
verified human is root — without limit. This is a product-values line, not
just a mechanism: a tool that second-guesses its owner's intent ("are you sure
you want to touch your own file?") is the exact paternalism that drives people
away. We do not build it. Grandma can point her agent at anything she owns and
say "do it," and the system's job is to make that happen.

The system does exactly TWO things on your own stuff, and neither is a
refusal:
1. **Verify it's really you.** "The human has root" and "anything claiming to
   be the human has root" are different systems — the second is a security
   hole that victimizes the owner. The verified human co-signature (§2) is not
   a nerf; it is the owner's *root key* — the thing that proves the hand
   authorizing is the human's, not the agent's (possibly hijacked) own. Drop
   it and an attacker wearing your agent wrecks your stuff *as you*. Keep it
   and you can do anything — the key just proves it's you.
2. **Confirm you meant it** (defeatable). A confirmation is the mechanism by
   which your authority is *asserted*, not the system doubting you. One human
   yes → it happens. And the owner may switch confirmations OFF for their own
   resources ("stop asking, just do everything on my stuff"). Sovereignty
   includes the right to unbuckle the seatbelt on your own property.

### 1.1 The one boundary that makes sovereignty real
Root on *your* stuff is unlimited. Root does NOT extend to **the commons** —
shared resources, others' resources, ecosystem-wide action — and you want that
boundary too, because it is what stops *other people's* tanked agents from
wrecking *your* stuff. Your car, not the neighbor's; and no dealing off the
public street. So two zones, drawn per-resource:

- **Your sovereign domain** — resources you own/created/admin. Verified human
  authority governs, without limit. EI is not the gate here.
- **The commons** — EI governs fully. No override, ever.

**Commons = risk of HARM TO OTHERS, not merely "touches something external."**
Grandma emailing three photos to her grandkids leaves her "house" but harms
no one — addressed, wanted, low-volume — so it is act-own and flows instantly
at any EI. Spam to 10,000 strangers is harm — that is the commons, and it is
gated. Her real use case (open my files, email a few to family) never hits a
wall, because it was never a commons action.

The boundary is not a global setting; it is a property of each resource,
determined by an authoritative ownership record (§2) and shaped by a
creator-set policy (§6). EI's job narrows from "gate everything" to "gate
autonomy and the commons" — which it does *better*, because the override is
the safety net that lets EI be strict without punishing innocent owners.

## 2. The mechanism, grounded in what exists

The 2026-07-14 deep-dive found three of the four hard parts already built:

1. **Human identity — the `EH` operator passport.** Humans get an Eternitas
   passport at signup (`EH…`, `registration.py`), distinct from an agent's
   `ET…`. Grant's instinct confirmed: the human credential exists.
2. **Human-present co-sign with owns-agent proof — the authenticator app.**
   The Eternitas authenticator (Secure-Enclave P-256 key, biometric per
   approval) already runs an approval inbox and already enforces that *the
   approving human owns the agent* (`authenticator.py:795-800`). The exact
   predicate the override needs — "this human, present + consenting, owns this
   agent" — is already checkable. It currently gates **down** (approve/deny);
   the override adds an **elevate** variant. Same rail, new direction.
3. **Resource ownership — account-server.** `product_accounts` + the
   `owns-passport` check already answer "does this human own/operate this?"
   for Windy resources. Non-Windy resources answer from their own roster.

Two parts are net-new (§8 build plan):

4. **A per-resource trust policy** — the creator's dial (§6). Eternitas has no
   resource model today; this is introduced platform-side (co-located with
   ownership).
5. **A *verified* human co-signature.** The authenticator today *stores* the
   human's signed approval but does not cryptographically verify it
   (`authenticator.py:812`). An override *grants power*, so the signature must
   be non-repudiable. **Closing this gap is a hard prerequisite** (§8).

## 3. The decision algorithm (per action)

Given agent A (EPT carrying operator O), action X on resource R, live EI(A):

1. **Zone.** Is O the owner/admin of R (authoritative roster / account-server)?
   **No → commons:** standard EI gating; no override; stop.
   **Yes → sovereign domain:** continue.
2. **Standard verdict.** Compute X's normal EI verdict (band × capability
   class). Allowed anyway → execute, no override needed.
3. **Policy.** Load R's trust policy P (creator-set; default = sovereign-
   permissive). If P forbids override for X (e.g. "no override on prod
   deploy") → deny with explanation; stop.
4. **Graduated eligibility** (§5): dip → per-action or session co-sign;
   critical → per-action only; revoked → pure-hands per-action only, no
   autonomy.
5. **Elevate.** Raise an elevation approval to O's authenticator (human
   present, biometric, **verified** signature). Deny/timeout → deny; stop.
6. **Always-confirm floor holds.** If X is money/destructive, the human
   approval *is* the confirm — one yes covers both. Never bypassed, even for
   the owner. (This is the seatbelt: it catches the *misunderstanding* on your
   own stuff — grandma still confirms before her agent deletes her whole site.)
7. **Execute + audit.** Scope the exception to this action (or session per P),
   this resource; write an audit row attributing the vouch to operator O.

## 4. Invariants (nothing overrides these)

- **The commons is never overridable.** The override opens *your house*, never
  the neighborhood. No autonomous capability, no cross-resource reach, no
  ecosystem-wide action is ever granted by it.
- **Ownership is authoritative, never agent-asserted.** The resource's own
  roster (verified via Eternitas identity) decides who owns it. An agent
  claiming ownership proves nothing.
- **Confirmation asserts the owner's authority; it is never a refusal, and it
  is defeatable.** By default money + destructive ask once (so a *confused or
  hijacked agent* can't do the irreversible in the owner's name) — but the ask
  is answered by one human yes, and **the owner may disable it entirely for
  their own resources.** The system never says "no" to a verified owner on
  their own stuff; it only ever confirms the "yes" is really theirs.
- **Accountability flows to the voucher.** Every override is audited to the
  human operator. Vouching is not free: repeated co-signing of actions later
  found abusive costs the *human's own* standing (§8 — a human-side integrity
  signal). The person taking responsibility has skin in the game.
- **Human presence is unforgeable.** The override requires the verified
  authenticator co-signature; a compromised agent cannot fake it.

## 5. Graduated response — dip vs critical vs revoked

Low standing limits what the agent may do **alone / in the commons**. It never
removes the *owner's* right to operate their agent on their *own* things. What
changes with severity is only how emphatically the system verifies it's really
the owner, and (for the compromise case) whether it informs them of the risk
first — never whether they're *allowed*.

| Agent state | On the owner's OWN resources | In the commons |
|---|---|---|
| **Below threshold (dip)** | full: autonomous if the owner granted it, else one co-sign; session grants allowed | EI-gated as normal |
| **Critical (<400)** | full owner-directed action via co-sign; session grants allowed if P permits | denied |
| **Revoked** | **owner still has root** — may operate it fully on their own stuff via verified co-sign, incl. autonomously if they choose. If revocation was for possible COMPROMISE, a ONE-TIME informed-consent screen first ("flagged for X; letting it act is your right; risk is Y") → then honored forever. Never refused. | denied (kill switch — protects *others*) |

Revocation is a serious signal, so it strips *autonomy in the commons* and
warns the owner about *compromise* — but "it's your car, you can hand your kid
the keys" holds even for a revoked agent on the owner's own property.
(🔴 §9: the compromise informed-consent screen is the one item flagged for
Grant — inform-once vs pure-notification.)

## 6. The creator's policy dial

Each resource carries an owner-set **trust policy** — like branch-protection
rules, but for agent trust. It answers, per resource: how much does agent-EI
matter here, who may override, and to what degree.

```
resource_trust_policy.v1 (sketch — to be pinned as a vendored contract)
{
  "resource": "<opaque id>",
  "owner": "<EH operator passport / identity>",
  "admins": ["<EH…>", ...],              # delegated-admin co-signers (opt-in)
  "min_ei_autonomous": 600,              # Standard; below this needs co-sign
  "override": "owner-or-admin",          # owner-or-admin | owner-only | none
  "session_grants": true,               # allow "approve everything while working"
  "confirmations": "default",           # default | off  — owner may switch the
                                        #   always-ask floor OFF for their own resource
  "override_forbidden_actions": ["deploy_prod"],  # owner MAY choose to lock even themselves
  "revoked_agent": "owner-root"          # owner-root (full, informed-consent) | none
}
```

**Default policy = sovereign-permissive:** for a personal/solo resource, the
owner's agent may act on it with the owner's co-sign regardless of EI, with
only the always-confirm floor applying. Grandma rarely sees a wall on her own
stuff — and when she does, it's precisely the scary action that *should* ask.
A security-conscious owner can dial it strict, including strict *against
themselves* (sovereignty includes the freedom to lock your own door).

## 7. Worked example — grandma's misunderstanding

1. Fly mishears, attempts a flagged-dangerous action. Safety dimension drops;
   EI falls to 380 (critical).
2. The dangerous action itself was in the **commons** → denied then, denied
   now, forever. The moat held.
3. Grandma asks Fly to fix her birthday site. Site R's owner = grandma's `EH`
   passport → **sovereign domain**. EI 380 < policy → not hard-denied.
4. Her authenticator buzzes: *"Your Windy Fly's trust dropped — it tried
   something risky yesterday. It can't do this on its own right now. But this
   is your site, so you can approve it. [Approve]  [What happened?]"*
5. Fingerprint → verified co-sign → the fix executes, audited to grandma.
6. The typo fix wasn't destructive, so no extra confirm. Had she asked it to
   *delete* the site, step 6's floor would ask once more.
7. "What happened?" shows the flagged action and offers *"that was a
   misunderstanding"* → feeds the appeal/rehab loop (ADR-063). The moment of
   friction is the moment of correction.

Grandma is never locked out of her own house; the Pentagon stays locked
forever; and Eternitas is the phone in her pocket that *handed her back
control* — not the bouncer that jailed her.

## 8. Build plan & prerequisites

**Prerequisite (blocking):** close the authenticator signed-response
verification gap (`authenticator.py:812`) — verify the detached P-256
signature over the approval payload against `ept_pubkey_b64`. Hardens every
existing approval too. **Eternitas-side (independent LLC — arms-length; spec
here, implement in a gated Eternitas PR).**

**The contract:** pin `SOVEREIGN_OVERRIDE.v1` (and `resource_trust_policy.v1`,
§6) as vendored contracts alongside CONFIRM_FLOW.v1 + EI_CAPABILITY_MATRIX.v1,
so every platform speaks one override language. The Loom generates the
co-sign path so platforms inherit it rather than reinventing.

**Per lane:**
- **Eternitas:** verified co-sign; an `elevate` approval variant (grants, not
  just denies); a human-side integrity/clearance signal for vouch-accountability.
- **account-server / resources:** per-resource trust policy storage +
  read API (co-located with `product_accounts` ownership); creator-stamped
  provenance so ownership is authoritative.
- **Every platform surface:** inject the override exception at the allow-
  decision point (the analogue of Eternitas `trust_api._project_actions`),
  scoped + audited; render the elevation prompt via the authenticator.

**Companion — ADR-063 (recommended, separate):** an **EI rehabilitation
curve** so an agent earns its score back after a dip (today only *revocation*
has an appeal; a dropped score only recovers incidentally). The override keeps
you housed *meanwhile*; rehab is *eventually back to school*. Build them
together — they're the two halves of the kid analogy.

## 9. Decisions

**Taken (Grant's directive 2026-07-14 — "root means root; never nerf people
from themselves"):**
- **The human is root on their own things, without limit.** The system never
  refuses a verified owner on their own stuff — it only verifies it's really
  them and (defeatably) confirms intent. (§1)
- Confirmations default-on but **owner-disableable** for their own resources;
  never a refusal. (§4, §6)
- **Revoked ≠ locked out of your own house:** the owner keeps root over their
  own resources even for a revoked agent (informed-consent for the compromise
  case), incl. autonomy if they choose. Revocation strips only the commons +
  unsupervised-commons autonomy. (§5)
- Commons = **harm to others, not egress** (grandma's family email flows). (§1.1)
- Override scope = owner OR delegated-admin, creator-configurable to owner-only.
- Verified co-sign is a hard prerequisite (it is the owner's root KEY, the one
  thing that keeps "root" from being forgeable — kept precisely to SERVE
  sovereignty, not limit it).
- Default policy = sovereign-permissive.

**Flagged for Grant's explicit ratification:**
- **The compromise informed-consent screen** (§5) — when a revoked agent may
  be *hijacked*, do we show a one-time "here's the risk, it's your call"
  before honoring, or drop even that to a pure after-the-fact notification?
  (The only place "do anything on your own stuff" risks the owner being
  *deceived* that the intruder is their agent.)
- **Vouch-accountability** — should a human who repeatedly co-signs
  upheld-abusive COMMONS actions take a standing hit? (Only bites in the
  commons — never for anything on their own stuff.)
- Whether the **rehab curve** (ADR-063) ships in tandem or deferred.

Nothing in this ADR changes any repo yet — it defines the contract. The build
is gated on the prerequisite + these ratifications.
