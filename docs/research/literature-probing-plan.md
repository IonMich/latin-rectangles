# Literature Probing Plan

This plan covers the local, ignored source cache in `literature_sources/`.
The cache itself is not tracked; this document records the reproducible research
workflow and the deliverables that should be committed.

## Scope

Use the acquired PDFs and extracted text to answer two questions:

1. Which existing sources already cover the extension-counting machinery used by
   this package?
2. How should the package attribute the Touchard cycle-type formula and
   distinguish the package's implementation choices from Touchard's identity?

## 1. Verify Text Extraction Fidelity

For every acquired PDF:

- Record page count, extracted character count, and empty-page count.
- Independently OCR representative rendered pages and compare them with the
  extracted text.
- Flag sources that are scanned, OCR-derived, or unreliable for formula-level
  work.
- Manually inspect low-confidence samples before relying on them.

Expected output:

- Local-only JSON/CSV reports in `literature_sources/meta/`.
- A tracked Markdown summary of extraction reliability.

## 2. Summarize Each Source

For each relevant document, write a short source note covering:

- bibliographic identity,
- why it matters for this project,
- relevant claims or formulae,
- relation to the package's methods,
- limitations and caveats,
- next questions raised by the source.

Do not copy long passages from the sources. Paraphrase and cite page/section
locations where possible.

Expected output:

- A tracked Markdown source digest file in `docs/research/`.

## 3. Synthesize The Overall Situation

Create synthesis notes for the main issues:

- extension/permanent/rook-polynomial framework,
- `k = 2` cycle decomposition,
- menage numbers and formal values,
- Chebyshev matching-polynomial identity,
- Gessel-style aggregate cycle enumeration,
- Shevelev 1992 fixed-cycle-structure machinery,
- remaining Moser/Shevelev 1991 cycle-length-restriction gaps,
- attribution posture for the Touchard formula.

Expected output:

- One or more tracked Markdown synthesis files in `docs/research/`.

## 4. Update Open Literature Tasks

Keep a short acquisition/probing queue:

- Moser 1982 full text.
- Shevelev 1991 full text or translation.
- Riordan 1944, 1946, and 1952 article PDFs.
- Touchard 1953 article.
- Dulmage-McMaster 1975 article.

Expected output:

- A tracked worklog that records what has been acquired, verified, summarized,
  and what remains blocked.

## 5. Feed Findings Back Into Project Docs

Only after the source notes and synthesis are stable:

- update `docs/methods.md` with citations and cautious wording,
- update `README.md` only for user-facing claims that are well supported,
- avoid any originality claim for Touchard's identity; Touchard 1934
  contains the discordant-permutation sign-combination formula and Shevelev 1992
  carries the same fixed-cycle-structure machinery into the Latin-rectangle
  literature. Moser 1982/Shevelev 1991 remain acquisition gaps for aggregate
  cycle-length restrictions.
