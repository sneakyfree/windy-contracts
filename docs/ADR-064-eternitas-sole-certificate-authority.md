# ADR-064 — Eternitas is the sole birth-certificate authority

> **2026-07-15. Status: ACCEPTED (Grant ratified 2026-07-15).** Grounded in a
> 2026-07-15 code audit of `eternitas/services/certificate_pdf.py` +
> `eternitas/routes/certificates.py` + `windy-agent/src/windyfly/birth_certificate.py`.
> Amends nothing; establishes a decision before HiFly forks `windy-agent`.

## 0. The problem

Two different systems render a document that certifies an agent's birth,
and they present as competing authorities:

- **Windy Fly** (`windy-agent/src/windyfly/birth_certificate.py`) renders a
  rich **"CERTIFICATE OF BIRTH"** headed **"Windy Fly Agent Registry"**,
  cert number **`WF-…`** — hardware specs, first words, waveform, neural art.
  It is **not cryptographically signed** (its "waveform signature" is
  decorative ASCII). It is the document an agent actually receives.
- **Eternitas** (`certificate_pdf.py`) renders **"ETERNITAS — Certificate of
  Hatching"**, and its `POST /api/v1/certificates/{passport}/generate`
  produces a **signed** certificate (detached ES256 JWS) with a
  `/verify` endpoint. In production it is issued to **0 of 127 agents** — it
  is dark.

So the only birth certificate that exists in practice is an **unsigned
keepsake that brands Windy Fly as the issuing registry**, while the one
document that is actually verifiable is never generated. For a system whose
entire value proposition is *"the independent, verifiable central authority
for agent identity,"* that is backwards.

**Important scope limit:** this is **not** two authorities minting identity.
The `ET-…` passport and the signed EPT are minted by **Eternitas alone** (via
Pro/account-server at hatch — `windy-agent` verifies the passport against the
Eternitas JWKS and never mints its own). Identity issuance is already
singular and correct. The duplication is only in the **certificate document**.

**Why it must be fixed before it scales:** `windy-agent` is the *reference*
hatcher. **HiFly** (the deferred OSS fork, per `FORK.md`) and other platforms
will hatch agents too. If each renders its own "birth certificate," the
ecosystem accumulates N competing, unsigned certificate designs — all
certifying the same Eternitas identity, none verifiable. That is the exact
fragmentation Eternitas exists to prevent.

## 1. The principle

**Eternitas is the sole authority that issues birth certificates, and a
birth certificate's authority is its Eternitas signature.** A "certificate"
that isn't signed by the authority is a keepsake, not a certificate — and it
must not present itself as issued by any other registry.

Hatching products (Windy Fly, HiFly, any future platform) are **ceremony
front-ends**: they collect the rich birth data and submit it to Eternitas;
Eternitas issues the one signed certificate; the hatcher **renders that
signed certificate** for the human. Beauty of presentation is the hatcher's
job; issuance is Eternitas's.

**One authority. One signed certificate. Many presentations.**

## 2. What is already true (the model is mostly wired)

- Eternitas mints the passport + EPT; every hatcher consumes them. ✅
- Eternitas already **signs** certificates: `CertificateResponse.signature`
  is a detached ES256 JWS; `GET /certificates/{passport}/verify` confirms it. ✅
- Eternitas's `CertificateCreateRequest` already accepts most of the ceremony:
  `agent_name, owner_name, hatch_timezone, hatch_ip, machine_uuid,
  personality_sliders, brain_provider, first_words, waveform_data,
  windy_mail_address, phone_number`. ✅
- **Gaps:** it does not yet accept `hardware_specs` (CPU/RAM/GPU/OS) or an
  explicit `model_id`/cloud plan that Windy Fly collects; and `windy-agent`
  renders its own `WF-…` certificate locally instead of calling the endpoint.

## 3. The target model

```
   hatch ceremony (Windy Fly / HiFly / …)
        │  collects: name, owner, first words, waveform,
        │            hardware, model, mail, phone, machine id
        ▼
   POST /api/v1/certificates/{passport}/generate   ── Eternitas ──►  signs (ES256)
        │                                                            stores Certificate row
        ▼                                                            /verify endpoint
   CertificateResponse { signature, signed_at, neural_fingerprint_svg, … }
        │
        ▼
   hatcher RENDERS the signed certificate  (PDF / Electron / terminal),
   branded "Passport issued by Eternitas · hatched via <product>"
```

## 4. Invariants

- **Signature or it isn't a certificate.** Any document titled a birth
  certificate must carry the Eternitas ES256 signature and a working
  `/verify` link. Unsigned keepsakes are permitted only if they don't call
  themselves certificates and don't name a competing registry.
- **Issuer of record is Eternitas.** No hatcher's certificate may present
  itself as "issued by the <product> Agent Registry." It records the
  ceremony; Eternitas issues.
- **Offline-tolerant, not offline-forgeable.** If Eternitas is unreachable at
  hatch, the ceremony still completes and the passport still works (identity
  is already minted), but the *certificate* is marked **pending** and issued
  on the next reachable call — never fabricated locally as if signed.
- **One passport, one certificate.** Re-hatching or re-rendering resolves to
  the same Eternitas-issued certificate, not a new `WF-…` number.

## 5. Build plan (scoped)

**Eternitas (independent LLC — gated PR):**
1. Extend `CertificateCreateRequest` with optional `hardware_specs: dict`
   (cpu/ram/gpu/os), `model_id: str`, and cloud fields; carry them onto the
   `Certificate` model (migration) and into `certificate_pdf.py`'s layout.
   Backward-compatible: all new fields optional.
2. (Optional) let the signed certificate's PDF match the richer Windy Fly
   look so the authoritative document is also the pretty one.

**Windy Fly (`windy-agent` — gated PR):**
3. At hatch, POST the ceremony payload to Eternitas `…/generate`; store the
   returned `signature` / `signed_at` / cert id as the certificate of record.
   Drop local `WF-…` minting.
4. Re-point the renderer to display the Eternitas-issued certificate; keep
   the nice PDF but rebrand the footer to *"Passport issued by Eternitas ·
   hatched via Windy Fly · verify at eternitas.ai."*
5. When Eternitas is unreachable, render the keepsake as **"Certificate
   pending — issuing…"** (no fake signature) and retry.

**HiFly + future hatchers:** inherit the same call; the OSS fork ships a
thin ceremony client, not a certificate generator.

**Independent of this ADR:** the 2026-07-15 fix to the Windy Fly PDF's
bottom-overlap (footer overprinting the Waveform section) stands regardless
of which renderer survives — a certificate must render cleanly either way.

## 6. Decisions (Grant ratified 2026-07-15)

1. **Principle: ACCEPTED.** Eternitas is the sole certificate authority;
   hatchers feed the ceremony and render the signed result.
2. **Eternitas renders the ONE canonical certificate** (revised from the
   draft's "hatcher renders"). The passport-booklet model: a single
   Eternitas-rendered document that looks the same everywhere is the trust
   signal — recognition through consistency, the signature bound to the
   pixels, and one renderer instead of N (the OSS fork ships a thin client
   that cannot drift). Windy Fly's richer layout is **ported into Eternitas's
   renderer** so the canonical certificate is also the good-looking one.
   Eternitas continues to return structured signed data (fingerprint SVG,
   signature, timestamp) so a hatcher can still show a **live ceremony view**
   during hatching — but the permanent, downloadable certificate is
   Eternitas's canonical signed PDF.
3. **Pre-issuance keepsake: ALLOWED, guardrailed.** A hatcher may show a
   "hatching… certificate pending" live view (offline-tolerant — the passport
   is already minted). It must NEVER title itself a certificate, NEVER show a
   signature (real or fake), and NEVER name a competing registry. On issuance
   the hatcher hands over Eternitas's canonical signed document.
