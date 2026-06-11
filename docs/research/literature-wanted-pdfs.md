# Wanted Literature PDFs

This is the acquisition checklist for literature that is missing or was recently
acquired into the ignored local cache in `literature_sources/`. Use legitimate
public, publisher, library, author, or user-provided copies only.

## Highest Priority

| Status | Key | Citation | Why We Want It | Search Notes |
| --- | --- | --- | --- | --- |
| Wanted | `moser_1982_generalization_riordan_formula` | W. O. J. Moser, "A generalization of Riordan's formula for 3 x n Latin rectangles", *Discrete Mathematics* 40(2-3), 311-313 (1982). DOI: `10.1016/0012-365X(82)90129-7`. | Direct Moser cycle-length-sieving source cited by Shevelev and Stones et al. | Metadata found; PDF not yet acquired. |
| Wanted | `shevelev_1991_riordan_generalized_formula` | V. S. Shevelev, "The Riordan generalized formula for three-line Latin rectangles and its applications", *DAN of the Ukraine* 2, 8-12 (1991), in Russian. | Direct Shevelev note cited by Stones et al.; may clarify the 1991/1992 relationship. | Secondary citations found; PDF not yet acquired. |
| Wanted | `touchard_1953_permutations_discordant_two_given` | Jacques Touchard, "Permutations discordant with two given permutations", *Scripta Mathematica* 19, 109-119 (1953). Some references list 108-119. | Later full treatment may clarify notation and formal values beyond the 1934 note. | Bibliographic references found; PDF not yet acquired. |
| Blocked | `riordan_1944_three_line_latin_rectangles` | John Riordan, "Three-line Latin rectangles", *American Mathematical Monthly* 51(8), 450-452 (1944). | Original three-line Latin rectangle formula source. | Taylor PDF returned HTTP 403; JSTOR stable page is not open access from this environment. |
| Blocked | `riordan_1946_three_line_latin_rectangles_ii` | John Riordan, "Three-line Latin rectangles-II", *American Mathematical Monthly* 53(1), 18-20 (1946). | Follow-up Riordan source cited directly by Moser and Gessel. | Taylor PDF returned HTTP 403; JSTOR stable page is not open access from this environment. |
| Blocked | `riordan_1952_recurrence_three_line_latin_rectangles` | John Riordan, "A recurrence relation for three-line Latin rectangles", *American Mathematical Monthly* 59(3), 159-162 (1952). | Original recurrence source for `K_n`. | Taylor PDF returned HTTP 403; JSTOR stable page is not open access from this environment. |

## Still Useful

| Status | Key | Citation | Why We Want It | Search Notes |
| --- | --- | --- | --- | --- |
| Found | `touchard_1934_sur_un_probleme_de_permutations` | Jacques Touchard, "Sur un probleme de permutations", *C. R. Acad. Sci. Paris* 198, 631-633 (1934). | Announcement/source cited by Shevelev for the discordant-permutation count. | Gallica page images 631-633 were assembled into `literature_sources/pdfs/touchard_1934_sur_un_probleme_de_permutations.pdf`; OCR text is searchable but formulae need visual checks. |
| Found | `kaplansky_1944_symbolic_solution_permutations` | Irving Kaplansky, "Symbolic solution of certain problems in permutations", *Bulletin of the American Mathematical Society* 50(12), 906-914 (1944). DOI: `10.1090/S0002-9904-1944-08261-X`. | Classical symbolic-method source around menage and restricted permutations. | Acquired from the AMS direct PDF and extracted to `literature_sources/text/kaplansky_1944_symbolic_solution_permutations.txt`. |
| Found | `stones_2010_phd_on_the_number_of_latin_rectangles` | Douglas S. Stones, *On the Number of Latin Rectangles*, Ph.D. thesis, Monash University (2010). | Broad thesis version may contain extra bibliography and context. | Acquired through Figshare/Bridges metadata and extracted to `literature_sources/text/stones_2010_phd_on_the_number_of_latin_rectangles.txt`. |

## Lower Priority

| Status | Key | Citation | Why We Want It | Search Notes |
| --- | --- | --- | --- | --- |
| Wanted | `dulmage_mcmaster_1975_formula_counting_three_line_latin_rectangles` | A. L. Dulmage and G. E. McMaster, "A formula for counting three-line Latin rectangles", *Congressus Numerantium* 14, 279-289 (1975). | Another three-line Latin rectangle formula source cited by OEIS/Stones. | Bibliographic references found; PDF not yet acquired. |

## Search Pass, 2026-06-11

Found and cached:

- Touchard 1934: Wikisource identifies the 1934 *Comptes rendus* volume and the
  table of contents entry at page 631; Gallica page images 631-633 were assembled
  into the local PDF.
  - <https://fr.wikisource.org/wiki/Comptes_rendus_de_l%E2%80%99Acad%C3%A9mie_des_sciences/Tome_198%2C_1934/Table_des_mati%C3%A8res>
  - <https://gallica.bnf.fr/ark:/12148/bpt6k31506/f631.image>
- Kaplansky 1944: AMS direct PDF was cached locally.
  - <https://www.ams.org/journals/bull/1944-50-12/S0002-9904-1944-08261-X/S0002-9904-1944-08261-X.pdf>
- Stones 2010 thesis: Bridges/Figshare metadata led to the PDF download.
  - <https://bridges.monash.edu/articles/thesis/On_the_number_of_Latin_rectangles/5044384>

Blocked or still missing:

- Riordan 1944, 1946, 1952: Taylor direct PDF URLs returned HTTP 403 from this
  environment; JSTOR stable pages were not open-access PDF downloads.
- Moser 1982: metadata found through DOI/Crossref/Elsevier leads, but no
  downloadable full text found.
- Shevelev 1991: only secondary citations found so far.
- Touchard 1953: bibliography entries found, but no full PDF found.
- Dulmage-McMaster 1975: secondary bibliography entries found, but no full PDF
  found.
