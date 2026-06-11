# Literature Extraction Reliability

The local PDFs and text files live in `literature_sources/`, which is ignored
through `.git/info/exclude`. This tracked note records whether those local text
files are reliable enough for search and summarization.

## Verification Method

For each acquired PDF, representative pages were rendered to PNG. English
sources were independently OCRed with Tesseract and compared against the stored
extracted text using normalized token overlap. Russian and image-only sources
were rendered for manual visual checks where automatic OCR was not a reliable
formula-level audit. The sampled pages were the first, middle, and last
non-empty embedded-text pages, except for one-page or image-only sources.

Reports generated locally:

- `literature_sources/meta/text_fidelity_report.json`
- `literature_sources/meta/text_fidelity_pages.csv`
- `literature_sources/meta/text_fidelity_report.md`
- `literature_sources/meta/verification_samples/`

## Results

| Source | Pages | Sample Pages | Min Overlap | Assessment |
| --- | ---: | --- | ---: | --- |
| `bogart_doyle_1986_nonsexist_menage` | 6 | 1, 4, 6 | 0.89 | High-confidence embedded text. |
| `doyle_2007_number_latin_rectangles` | 15 | 1, 8, 15 | 0.99 | High-confidence embedded text. |
| `drake_2009_higher_order_matching_polynomials` | 21 | 1, 11, 21 | 0.89 | High-confidence embedded text. |
| `erdos_kaplansky_1946_asymptotic_number_latin_rectangles` | 7 | 1, 4, 7 | 0.84 | High-confidence embedded text. |
| `gessel_1986_counting_three_line_latin_rectangles` | 7 | 1, 4, 7 | 0.92 | High-confidence embedded text. |
| `gessel_1987_counting_latin_rectangles` | 4 | 1, 3, 4 | 0.93 | High-confidence embedded text. |
| `godsil_mckay_1990_asymptotic_enumeration_latin_rectangles` | 26 | 1, 14, 26 | 0.90 | High-confidence embedded text. |
| `kaplansky_1943_solution_probleme_des_menages` | 1 | 1 | 1.00 | OCR-derived. Good for search; check formulae in the PDF. |
| `kaplansky_1944_symbolic_solution_permutations` | 9 | 1, 5, 9 | 0.62 | Searchable embedded text; inspect formula-heavy passages. |
| `kaplansky_riordan_probleme_des_menages` | 12 | 1, 7, 12 | 1.00 | OCR-derived. Good for search; check formulae in the PDF. |
| `kirousis_kontogeorgiou_2016_probleme_des_menages_revisited` | 4 | 1, 3, 4 | 0.94 | High-confidence embedded text. |
| `riordan_1958_introduction_to_combinatorial_analysis` | 256 | 1, 129, 256 | 0.83 | High-confidence embedded text. |
| `spahn_zeilberger_2022_generalized_latin_rectangles_trapezoids` | 7 | 1, 4, 7 | 0.98 | High-confidence embedded text. |
| `stones_2010_many_formulae_latin_rectangles` | 46 | 1, 24, 46 | 0.79 | High-confidence embedded text. |
| `stones_2010_phd_on_the_number_of_latin_rectangles` | 164 | 1, 82, 164 | 0.74 | Searchable embedded text; NUL bytes were stripped from the local text cache. |
| `stones_et_al_2016_on_computing_number_latin_rectangles` | 16 | 1, 9, 16 | 0.90 | High-confidence embedded text. |
| `shevelev_1992_reduced_latin_rectangles_square_matrices` | 20 | 1, 6, 20 | N/A | Searchable embedded text with OCR artifacts; rendered sample pages were spot-checked manually because Russian OCR is not configured locally. |
| `touchard_1934_sur_un_probleme_de_permutations` | 3 | 1, 2, 3 | N/A | Image-only Gallica pages assembled into a PDF; OCR-derived text is useful for search, but formulae must be checked visually. |
| `wyman_moser_1957_on_the_probleme_des_menages` | 13 | 1, 7, 13 | 0.93 | High-confidence embedded text. |
| `yamamoto_1953_symbolic_methods_three_line_latin_rectangles` | 11 | 1, 6, 11 | 0.65 | High-confidence embedded text, but inspect formula-heavy passages. |

## Caveats

- The two Kaplansky/Kaplansky-Riordan scans are OCR-derived. The corrected OCR
  now reads cleanly, but formula-level references should be verified visually in
  the PDF.
- Kaplansky 1944 and Stones's thesis have usable embedded text, but the same
  formula-level caution applies in passages with dense notation.
- Touchard 1934 is an image-only assembled PDF. Its OCR text is good enough for
  discovery; rely on the rendered page images for signs, indices, and formulae.
- Some extracted text files initially contained NUL bytes from the PDF extractor.
  These were stripped from the ignored local text cache so `rg` treats all files
  as text.
- The Shevelev 1992 text is usable for keyword search and rough reading, but
  formula signs and indices should be checked against the rendered PDF pages.
- Automated token overlap is a search/readability test, not a mathematical
  formula audit. Formulae, tables, and signs should still be checked against the
  PDF before being cited in final public documentation.
