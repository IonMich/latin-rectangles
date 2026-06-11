# Literature Probing Worklog

This is the execution log for `docs/research/literature-probing-plan.md`.

## Current Status

- [x] Verify extracted text fidelity for all acquired PDFs.
- [x] Summarize each acquired source.
- [x] Write overall synthesis notes.
- [x] Update the missing-source queue.
- [ ] Decide which findings should be promoted into package docs.

## Completed Artifacts

- `docs/research/literature-extraction-reliability.md`
- `docs/research/literature-source-digests.md`
- `docs/research/literature-synthesis.md`
- `literature_sources/meta/text_fidelity_report.json` (local, ignored)
- `literature_sources/meta/text_fidelity_pages.csv` (local, ignored)
- `literature_sources/meta/text_fidelity_report.md` (local, ignored)
- `literature_sources/meta/verification_samples/` (local, ignored)

## Fidelity Verification

Representative pages from each PDF were rendered to images, OCRed with
Tesseract, and compared to the extracted text. Fourteen sources have
high-confidence embedded text. The two scanned menage sources are OCR-derived
and usable for search, but formulae and tables should be checked against the
PDF before final citation.

The original OCR of `kaplansky_1943_solution_probleme_des_menages` was not
faithful because the scan is a rotated two-page image and the first OCR pass
used the wrong layout mode. It was regenerated with Tesseract page segmentation
mode 3 and rechecked successfully.

## Source Summary

The current digests support this rough classification:

- Godsil-McKay: primary source for the extension/perfect-matching/rook-polynomial
  framework.
- Riordan and the menage literature: primary context for one-cycle values and
  formal-value conventions.
- Drake and matching-polynomial sources: support for the cycle/Chebyshev step,
  though a more primary citation remains desirable.
- Gessel: adjacent aggregate cycle-count enumeration, not yet a fixed-cycle-type
  formula.
- Touchard 1934: acquired from Gallica page images. A direct visual recheck of
  formula (1) shows that the package's Touchard identity is not materially
  distinct from Touchard's formula; it is the `h = 0` specialization written with
  all sign vectors and a `1/2` factor.
- Kaplansky 1944: acquired from the AMS direct PDF endpoint. It is relevant
  symbolic-method background but not currently the closest fixed-cycle-type
  citation.
- Stones 2010 PhD thesis: acquired through the Figshare/Bridges metadata. It is
  useful as a bibliography and context source.
- Shevelev 1992: acquired from Math-Net. It contains an abstract `F`-generalized
  Riordan formula, a refinement by number of cycles in the relative cycle
  structure, and a fixed relative-cycle-structure formula based on Touchard.
- Moser/Shevelev 1991: remaining unresolved context for aggregate
  cycle-length-restriction formulae, because Moser 1982 is the direct source for
  cycle-length sieving and Shevelev 1991 is still only known through secondary
  citations.

## Remaining Blockers

- Moser 1982 full text is still not acquired.
- Shevelev 1991 full text is still not acquired.
- Riordan 1944, 1946, and 1952 article PDFs are still not acquired.
- Touchard 1953 full text is still not acquired.
- Dulmage-McMaster 1975 full text is still not acquired.

## Next Step

Promote only conservative, well-supported claims into `docs/methods.md` and
`README.md`. The strongest safe statement is that the Touchard identity should
be attributed to Touchard 1934, with the package providing a Latin-rectangle
specialization, rook/Chebyshev rederivation, and exact implementation.

## Notes

- Source files live in `literature_sources/`, which is ignored through
  `.git/info/exclude`.
- Tracked docs should paraphrase rather than reproduce source text.
- Treat scanned OCR sources as weaker evidence until manually checked.
