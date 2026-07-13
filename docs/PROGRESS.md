# Doctrine-lane progress ledger

Append-only. Newest entry first. Every working session ends by adding an
entry here — a session that didn't update the ledger didn't happen.

---

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
