# ADR-063 — Integrity rehabilitation: no life sentence for a bad afternoon

> **2026-07-14. Status: ACCEPTED (design); build gated (Eternitas-side,
> arms-length).** Companion to ADR-062. Where 062 keeps an owner *housed* while
> their agent's score is low, 063 gives the agent a principled, visible path
> back into the *commons*. Grounded in the Eternitas deep-dive (2026-07-14),
> which found **no rehabilitation mechanism exists today** — a dropped score
> only recovers if positive deltas happen to arrive; the sole formal appeal is
> for full revocation.

## 0. The problem

ADR-062 makes sure grandma's low-EI agent still works fully on her own stuff.
But its *commons* standing — the trust that lets it act in the wider ecosystem
— has no way back. Today a dip is a near-permanent scar: the five integrity
dimensions only climb if good ratings coincidentally accrue, and the only
appeal path (`routes/appeals.py`) is gated on `status == REVOKED`, not on a low
score. So one bad afternoon, or one misunderstanding, permanently caps an
agent's autonomous life. That is the "hate Eternitas" outcome from the other
direction: not "locked out of my house," but "my agent is crippled forever
over a spit-wad."

The fix has two halves, and the first is the deeper one.

## 1. Half one — penalize HARM DONE, not INTENT ATTEMPTED

Most of grandma's nightmare scenario dissolves before rehab is even needed, if
the penalty is calibrated correctly. Her agent misheard and *attempted*
something dangerous — but the commons gate **blocked it**. The gate *worked*.
Cratering the agent's score for a blocked, harmless attempt is what
manufactures the crisis.

**Principle:** an integrity penalty scales with **harm actually done to
others**, not with what was attempted and stopped.

- **Blocked / harmless attempt** (the gate did its job; no one was harmed) →
  a *small, fast-decaying* safety ding, not a cliff. A near-miss, logged, aged
  off in days. Grandma's misheard "hack the Pentagon" was blocked → tiny dent
  → recovered by tomorrow. The moat held AND the agent isn't scarred.
- **Consummated harm** (fraud that moved money, abuse that reached a real
  person, spam that landed) → the real penalty, scaled by severity.

This single calibration change prevents the majority of unjust dips at the
*source*, before the override (062) or the recovery curve (below) has to catch
them.

## 2. Half two — the recovery curve

Trust is **easy to lose, steady to regain** — but *steady*, not glacial. A dip
from a single mistake recovers in days-to-weeks with good behavior; a pattern
of real abuse recovers slowly. Two mechanisms, on the existing `integrity_scores`
+ `integrity_events` machinery:

1. **Time-decay of each event's contribution.** Every penalizing
   `integrity_event` contributes a decaying amount to the current score — its
   weight halves on a per-dimension, per-severity half-life and ages off toward
   zero if not repeated (like a ticket ageing off a driving record). Recurrence
   resets/compounds; clean time heals.
2. **Earn-back accrual.** Successful tasks, honored confirmations, completed
   work without incident, and positive ratings actively rebuild score above the
   passive decay floor. Sustained good behavior *accelerates* recovery.

**Dimensions recover at different rates** (severity × dimension):
`honesty`/fraud recovers **slowest** (the most trust-corrosive; earned back
slowly), `reliability` **fastest** (consistent good performance rebuilds it
quickly), `safety`/`compliance`/`reputation` in between. A flustered mistake
ages off fast; a fraud flag lingers. Matches the credit-record intuition.

**No permanent scar.** After sufficient clean time + good behavior, an agent
returns to its *earned* baseline — never permanently capped by one bad day.
(Revocation is the separate, more serious state — §4.)

## 3. The misunderstanding fast-path (the appeal, wired to 062)

ADR-062's override prompt carries a "What happened?" path where the owner can
attest *"that was a misunderstanding — my agent misheard, I never asked for
that."* That attestation fast-tracks recovery of **that specific event's**
penalty. Guardrails so it isn't a free "undo any penalty" button:

- **Owner-attested, and logged to the owner's standing.** Crying
  "misunderstanding" is a *vouch* — and per ADR-062 vouch-accountability
  (commons-only), an owner who repeatedly false-attests to wipe penalties for
  actions that were genuinely harmful-in-the-commons takes their *own* standing
  hit. The appeal has a cost that scales with abuse of it.
- **Discounts, never erases consummated harm.** A misunderstanding attestation
  can fast-recover a *blocked/harmless* event to near-zero; it can only
  *discount*, not delete, an event where real harm reached a real other party.
- **Rate-limited.** You cannot cry misunderstanding every day; the fast-path
  throttles, and repeated use itself becomes a reliability signal.

## 4. Revocation is separate

Score *recovery* (this ADR) is for dips. **Revocation** — a deliberate kill for
serious/repeated abuse — keeps its existing, more serious appeal
(`routes/appeals.py`, 30-day window, manual review). An agent doesn't
"decay back" out of revocation; that requires the human process. (And per
ADR-062, even a revoked agent stays fully owner-operable on the owner's own
resources meanwhile — the two ADRs interlock.)

## 5. Transparency — you can see the healing

Opacity breeds resentment; a visible end-date breeds patience. Both the agent
and the owner can query a **recovery projection**: *"Trust 620, recovering. Was
380 after [event] on [date]. +X/week with good behavior. Back to [baseline] by
~[date]."* This grandma-legible view is itself pro-adoption — people tolerate a
penalty they can watch ending. Expose it on the Trust API alongside the current
score.

## 6. How 062 and 063 interlock (the complete promise)

- **062 — you are never homeless.** A low or even revoked agent works fully on
  *your own things*, under your verified authority.
- **063 — you are never exiled forever.** A misunderstanding barely dents
  (§1); a real dip heals on a visible timeline (§2, §5); a false-positive can
  be attested away (§3).

Together they deliver the whole emotional promise: your agent is never useless
to you, a spit-wad doesn't cripple it, and real mistakes heal on a schedule you
can see. That is what makes a *strict* trust system feel *fair* — and fair is
what makes people keep it instead of fleeing it.

## 7. Build (Eternitas-side, arms-length — spec here, implement in a gated PR)

On the existing registry mechanics (`integrity_index.py`, `integrity_events`,
`trust_api.py`):
- **Penalty calibration:** make `apply_report_penalty` scale by *harm-done*
  (consummated vs blocked/harmless), not attempt. Blocked attempts → small,
  fast-decay safety deltas.
- **Time-decay:** the live score sums each event's *decayed* contribution
  (per-dimension, per-severity half-life) rather than a static running total.
- **Earn-back accrual:** positive-signal deltas above the decay floor.
- **Misunderstanding fast-path:** an owner-attestation endpoint (wired to the
  062 override prompt) that discounts a specific event, logged to the owner's
  standing, rate-limited.
- **Recovery-projection API:** current + trajectory + projected-baseline-date,
  exposed on `build_trust_view`.
Defaults (half-lives, rates) are tunable; ship sensible starts (e.g. a
blocked-attempt safety ding ~half-lives in days; a fraud honesty penalty in
months).

## 8. Decisions

**Taken (Grant concurred 2026-07-14):**
- Rehab ships in tandem with ADR-062.
- Penalty scales with harm-done, not intent-attempted (the deeper fix).
- Trust is easy to lose, steady (not glacial) to regain; no permanent scar for
  a dip; revocation stays a separate, human-reviewed state.
- The misunderstanding fast-path is owner-attested, logged to owner standing
  (vouch-accountability), discounts-not-erases consummated harm, rate-limited.
- Recovery is transparent (visible projection).

**Tunable at build (not decisions):** the exact half-lives, earn-back rates,
per-dimension recovery curves, and fast-path throttle.
