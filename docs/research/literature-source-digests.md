# Literature Source Digests

These notes summarize the locally acquired literature in
`literature_sources/`. They are working notes for attribution and method
development, not a complete historical survey.

## Core Latin-Rectangle Sources

### Godsil-McKay 1990, *Asymptotic Enumeration Of Latin Rectangles*

Local text: `literature_sources/text/godsil_mckay_1990_asymptotic_enumeration_latin_rectangles.txt`

Relevance:

- This is the best source currently in hand for the general extension-counting
  framework.
- Section 2 associates a `k x n` Latin rectangle with a `k`-regular bipartite
  graph whose row matchings form a 1-factorization.
- Lemma 2.1 states the one-row extension count as the number of perfect
  matchings in `K_{n,n}` avoiding the forbidden graph.
- Section 3 introduces the rook/matching polynomial machinery for the
  complement perfect-matching count.
- Section 7 mentions cyclic-shift rectangles `M(k,n)` as a much-studied
  generalization of the menage problem, with exact solutions known for small
  `k`.

Impact on this repo:

- The permanent/rook-polynomial framing is standard and should be attributed to
  this framework.
- The general `k -> k + 1` code path is aligned with this graph-theoretic
  formulation.
- In the `k = 2` specialization, the decomposition into even cycles is an
  immediate specialization of this graph model, but this exact fixed-cycle-type
  sentence has not yet been found in a source.

### Riordan 1958, *An Introduction To Combinatorial Analysis*

Local text: `literature_sources/text/riordan_1958_introduction_to_combinatorial_analysis.txt`

Relevance:

- The book treats restricted-position permutations via boards, including the
  rencontre and reduced menage boards.
- It explicitly connects two-line Latin rectangles with derangements and
  three-line Latin rectangles with menage numbers.
- The three-line Latin rectangle section expresses reduced `3 x n` counts in
  terms of derangements and menage numbers, and states the recurrence later
  cited by Stones et al.

Impact on this repo:

- This is a primary source for the classical `K(3,n)` formula involving menage
  numbers.
- It supports the statement that menage numbers are already woven into the
  aggregate three-line Latin rectangle literature.
- It does not appear to give a fixed prescribed second-row cycle-type extension
  formula.

### Gessel 1986, *Counting Three-Line Latin Rectangles*

Local text: `literature_sources/text/gessel_1986_counting_three_line_latin_rectangles.txt`

Relevance:

- A reduced `3 x n` Latin rectangle is represented by a pair `(pi, sigma)` where
  `pi`, `sigma`, and `pi sigma^{-1}` are all derangements.
- Theorem 1 gives a generating function counting such pairs by the number of
  cycles of `pi` and the number of cycles of `sigma`.
- The proof uses colored "Latin configurations" and a generating-function
  transformation that records aggregate cycle counts.

Impact on this repo:

- Gessel is adjacent to our fixed-`pi` problem but not the same problem.
- The theorem records only the number of cycles of `pi`, not the full cycle type
  of a prescribed `pi`.
- This currently supports a cautious distinction: our cycle-type-level signed
  sum is not obviously contained in Gessel's stated theorem, but Gessel should be
  read carefully before making any novelty claim.

### Gessel 1987, *Counting Latin Rectangles*

Local text: `literature_sources/text/gessel_1987_counting_latin_rectangles.txt`

Relevance:

- This short announcement gives a general formula for `k x n` Latin rectangles
  using partition-lattice Mobius functions and colored bipartite graphs.
- It implies P-recursiveness in `n` for fixed `k`.

Impact on this repo:

- Useful context for the broader enumeration landscape.
- Not directly about one-row extensions of a fixed `2 x n` rectangle.

### Stones 2010, *The Many Formulae For The Number Of Latin Rectangles*

Local text: `literature_sources/text/stones_2010_many_formulae_latin_rectangles.txt`

Relevance:

- Broad survey of formulae for Latin rectangle enumeration.
- Good bibliography hub for Riordan, Moser, Yamamoto, Gessel, Doyle, and related
  exact/asymptotic methods.

Impact on this repo:

- Useful for orienting what has been published, but the decisive nearby
  Moser/Shevelev cycle-length discussion is clearer in Stones et al. 2016.

### Stones 2010 PhD, *On The Number Of Latin Rectangles*

Local text: `literature_sources/text/stones_2010_phd_on_the_number_of_latin_rectangles.txt`

Relevance:

- Fuller thesis version of Stones's Latin rectangle work.
- Gives broader bibliography and historical orientation for reduced Latin
  rectangles, three-line formulae, Riordan, Moser, and related computations.

Impact on this repo:

- Useful as a bibliography and context source, especially for checking citation
  trails.
- It is not currently evidence for a fixed prescribed second-row cycle-type
  formula beyond the Moser/Shevelev leads already flagged by the later papers.

### Stones, Lin, Liu, Wang 2016, *On Computing The Number Of Latin Rectangles*

Local text: `literature_sources/text/stones_et_al_2016_on_computing_number_latin_rectangles.txt`

Relevance:

- Summarizes the classical three-line Latin rectangle formulae.
- Gives Riordan's formula for normalized `3 x n` rectangles in terms of
  derangements and menage numbers.
- Notes the formal convention `u_1 = -1` required by Riordan's formula despite
  the direct permutation interpretation.
- States that Moser generalized Riordan's formula by restricting which cycle
  lengths the second-row derangement may avoid, and that Shevelev gave the
  complementary cycle-length-in-`S` generalization.
- Restates Gessel's discordant-derangement pair generating function.

Impact on this repo:

- This is the key secondary source warning us not to overclaim novelty.
- Moser and Shevelev are the highest-priority acquisition targets because their
  results are closest to fixed cycle-length data.
- The formal-value warning matters for our notation: this repo's Touchard
  convention has `M_0 = 2` and `M_1 = -1`, not Riordan's `u_0 = 1` convention.

### Yamamoto 1953, *Symbolic Methods In The Problem Of Three-Line Latin Rectangles*

Local text: `literature_sources/text/yamamoto_1953_symbolic_methods_three_line_latin_rectangles.txt`

Relevance:

- Develops symbolic-method and asymptotic machinery for three-line Latin
  rectangles.
- References Riordan's recurrence work and earlier asymptotic series.

Impact on this repo:

- Useful background for aggregate `3 x n` enumeration.
- Not currently evidence for a fixed-cycle-type extension formula.

### Erdos-Kaplansky 1946, *The Asymptotic Number Of Latin Rectangles*

Local text: `literature_sources/text/erdos_kaplansky_1946_asymptotic_number_latin_rectangles.txt`

Relevance:

- Classical asymptotic source for Latin rectangles.
- Uses inclusion-exclusion/sieve reasoning for adding a row to a Latin
  rectangle.

Impact on this repo:

- Historical background for extension-as-sieve methods.
- Not directly about exact fixed-cycle-type extension counts.

### Doyle 2007, *The Number Of Latin Rectangles*

Local text: `literature_sources/text/doyle_2007_number_latin_rectangles.txt`

Relevance:

- Gives formulae for reduced `k`-line Latin rectangle counts by generalizing
  Ryser-style inclusion-exclusion.
- Includes a concrete discussion of the `3`-line case.

Impact on this repo:

- Helpful for modern inclusion-exclusion context.
- Not a direct substitute for Godsil-McKay's fixed-extension graph framework.

### Spahn-Zeilberger 2022, *Automatic Counting Of Generalized Latin Rectangles And Trapezoids*

Local text: `literature_sources/text/spahn_zeilberger_2022_generalized_latin_rectangles_trapezoids.txt`

Relevance:

- Presents symbolic dynamic programming for generalized Latin rectangles,
  generalized derangements, and generalized three-row Latin rectangles.
- Sketches a generalization of Gessel-style P-recursiveness.

Impact on this repo:

- Useful computational context.
- Not currently evidence for or against the Touchard cycle-type identity.

## Matching-Polynomial And Menage Sources

### Drake 2009, *Higher Order Matching Polynomials And d-Orthogonality*

Local text: `literature_sources/text/drake_2009_higher_order_matching_polynomials.txt`

Relevance:

- States that matching polynomials of paths and cycles correspond to Chebyshev
  polynomials of the second and first kinds, respectively.
- Cites earlier matching-polynomial work by Godsil and Gutman.

Impact on this repo:

- Supports the Chebyshev bridge used in the Touchard derivation.
- It is a modern secondary source for the cycle/Chebyshev fact; a primary
  matching-polynomial citation would still be better for final attribution.

### Kaplansky 1943, *Solution Of The Probleme Des Menages*

Local text: `literature_sources/text/kaplansky_1943_solution_probleme_des_menages.txt`

Relevance:

- Gives a short inclusion-exclusion proof of Touchard's menage formula.
- Establishes the reduced menage problem as a forbidden-neighbor permutation
  problem.

Impact on this repo:

- Useful one-cycle historical source.
- OCR-derived; verify formulae visually in the PDF before citing them.

### Kaplansky-Riordan 1946, *The Probleme Des Menages*

Local text: `literature_sources/text/kaplansky_riordan_probleme_des_menages.txt`

Relevance:

- Historical survey and development of menage polynomials.
- Discusses a compact Chebyshev/Tchebycheff representation.
- Includes a sign-iteration identity for the associated polynomials with formal
  endpoint conventions.
- Connects the menage machinery to Riordan's three-line Latin rectangle formula.

Impact on this repo:

- This is very close to the algebraic shape of our Touchard derivation.
- It strengthens the case that our identity is a natural repackaging of older
  menage/Chebyshev machinery.
- OCR-derived; formulae and signs must be checked visually before final citation.

### Wyman-Moser 1957, *On The Probleme Des Menages*

Local text: `literature_sources/text/wyman_moser_1957_on_the_probleme_des_menages.txt`

Relevance:

- Gives a history of the menage problem up to 1946 and extends the bibliography.
- Credits Touchard for the first explicit solution and Kaplansky for a simple
  derivation.
- Uses formal initial values for a menage-related sequence and discusses
  connections to reduced three-line Latin rectangles.

Impact on this repo:

- Good historical support for Touchard/Kaplansky/Riordan menage attribution.
- Useful warning that formal initial values are not a new phenomenon in this
  literature.

### Bogart-Doyle 1986, *Non-Sexist Solution Of The Menage Problem*

Local text: `literature_sources/text/bogart_doyle_1986_nonsexist_menage.txt`

Relevance:

- Gives an elementary derivation of Touchard's menage formula and surveys the
  older menage-problem tradition.
- Notes the relationship between seating-first reductions, restricted
  positions, rooks, and Latin rectangles.

Impact on this repo:

- Useful expository source but not a primary Latin-rectangle extension source.

### Kirousis-Kontogeorgiou 2016, *The Probleme Des Menages Revisited*

Local text: `literature_sources/text/kirousis_kontogeorgiou_2016_probleme_des_menages_revisited.txt`

Relevance:

- Modern revisiting of the menage problem with concise bibliography.

Impact on this repo:

- Useful for orientation and references.
- Not needed for the core Touchard attribution unless it points to a better
  primary source.

## Missing Or Metadata-Only Sources

### Moser 1982, *A Generalization Of Riordan's Formula For 3xn Latin Rectangles*

Local metadata:

- `literature_sources/meta/moser_1982_crossref_record.json`
- `literature_sources/meta/moser_1982_pascal_francis_record.html`

Citation entries:

- Moser, W. O. J. (1982). A generalization of Riordan's formula for
  `3 x n` Latin rectangles. *Discrete Mathematics*, 40(2-3), 311-313.
  https://doi.org/10.1016/0012-365X(82)90129-7

```bibtex
@article{moser1982generalization,
  author = {Moser, W. O. J.},
  title = {A generalization of Riordan's formula for {3 x n} Latin rectangles},
  journal = {Discrete Mathematics},
  volume = {40},
  number = {2-3},
  pages = {311--313},
  year = {1982},
  doi = {10.1016/0012-365X(82)90129-7}
}
```

Status:

- Full text not acquired.
- Crossref identifies DOI `10.1016/0012-365X(82)90129-7`.
- Elsevier API metadata marks the article as open/archive, but unauthenticated
  retrieval from this environment returned only minimized metadata. ScienceDirect
  itself returned a Cloudflare challenge page.
- No local copy was found in Calibre, Zotero, Downloads, Documents, Desktop, or
  mounted volumes.

Why it matters:

- This is currently the most important missing source.
- Stones et al. say it counts normalized three-line Latin rectangles with
  second-row cycle lengths excluded from a set `S`.
- It may contain aggregate cycle-length-restriction formulae close to our fixed
  cycle-type problem.

### Shevelev 1991, *The Riordan Generalized Formula For Three-Line Latin Rectangles And Its Applications*

Status:

- Full text not acquired.
- Stones et al. identify the 1991 article as a related cycle-length-in-`S`
  generalization.
- Search found secondary references in OEIS, Stones et al., and Math StackExchange,
  but no public PDF or journal archive copy.

Why it matters:

- This remains an important missing source for aggregate cycle-length-restriction
  context.
- The 1991 article is in Russian according to Stones et al.

### Shevelev 1992, *Reduced Latin Rectangles And Square Matrices With Identical Sums In The Rows And Columns*

Local files:

- `literature_sources/pdfs/shevelev_1992_reduced_latin_rectangles_square_matrices.pdf`
- `literature_sources/text/shevelev_1992_reduced_latin_rectangles_square_matrices.txt`
- `literature_sources/meta/shevelev_1992_mathnet_eng_record.html`
- `literature_sources/meta/shevelev_1992_mathnet_rus_record.html`

Status:

- Full text acquired from Math-Net.Ru.
- Embedded text extracted. It is searchable, but the source is Russian and the
  text layer has OCR artifacts; formula-level citations should be checked against
  the rendered PDF pages.

What it says:

- Gives a countably parameterized abstract generalization of Riordan's formula
  for reduced `3 x n` Latin rectangles.
- Defines `F`-reduced classes, generalized derangement numbers `D_n(F)`, and
  `F`-associated Stirling numbers `d(F; n, k)`.
- Theorem 1 gives the generalized Riordan form
  `sum_k binom(n,k) D_k(F) D_{n-k}(F) u_{n-2k}` and its refinement by number of
  cycles in the relative cycle structure of the first two rows.
- Lemma 1 gives a fixed relative-cycle-structure formula using Touchard's
  count for permutations discordant with two given permutations. In modern
  notation it sums over sub-multivectors of the cycle-count vector and weights
  them by products of binomial choices and the menage/Lucas values `u_{n-2m}`.
- Section 3 states that Riordan's formula is the specialization
  `f_n = (1 - delta_{n,1})/n`, and that Moser's formula is obtained from the
  cycle-sieving specialization
  `f_n = (1 - sum_j delta_{n,a_j})/n`.

Why it matters:

- This is no longer merely adjacent literature. It confirms that the fixed
  relative-cycle-structure machinery was already part of the Latin-rectangle
  literature.
- After checking Touchard 1934 directly, the right posture is stronger than
  "nearby prior art": the Touchard identity itself should be attributed to
  Touchard, with Shevelev as the closest acquired Latin-rectangle bridge.

### Riordan 1944, 1946, 1952 Monthly Articles

Status:

- Full PDFs not acquired; Taylor & Francis URLs returned HTTP 403 and JSTOR
  stable PDF URLs returned access pages from this environment.
- Riordan's book gives the relevant formulae in a later consolidated form.

Why they matter:

- Primary sources for the classical three-line Latin rectangle formulae.

### Touchard 1934

Local files:

- `literature_sources/pdfs/touchard_1934_sur_un_probleme_de_permutations.pdf`
- `literature_sources/text/touchard_1934_sur_un_probleme_de_permutations.txt`

Status:

- Original note acquired from Gallica page images through the Wikisource/BnF
  volume metadata.
- The cached PDF is an assembled three-page image PDF; the text file is OCR
  output and is useful for search but not formula-level citation without visual
  checking.

What it says:

- Poses the problem of counting permutations discordant with two given
  permutations.
- States a general solution in terms of the cycle structure of the relative
  substitution between the two given permutations.
- Gives a sign-combination formula over the nontrivial relative cycle lengths,
  expressed using a simpler one-cycle function `phi(h; n)`.
- Uses `2^(s-1)` sign choices by fixing the sign of the first nontrivial cycle.
  With Touchard's convention `phi(h; -n) = phi(h; n)`, this is exactly the same
  as the package's `1/2` times the sum over all `2^s` sign vectors.

Why it matters:

- This is the primary acquired source for the Touchard identity itself.
- In the package's setting, the first row is normalized to the identity and the
  second row is a derangement `pi`. Therefore Touchard's relative substitution
  has no fixed points (`h = 0`) and nontrivial cycle lengths equal to the cycle
  type of `pi`.
- The package formula is not materially distinct from Touchard's formula; it is
  the `h = 0` specialization written with modern cycle-type notation and
  implemented through cached one-cycle values.

### Kaplansky 1944

Local files:

- `literature_sources/pdfs/kaplansky_1944_symbolic_solution_permutations.pdf`
- `literature_sources/text/kaplansky_1944_symbolic_solution_permutations.txt`

Status:

- Full PDF acquired from the AMS direct PDF endpoint.
- Embedded text was extracted and is searchable.

Why it matters:

- A nearby symbolic restricted-position source, but less urgent than Moser and
  Shevelev for the fixed-cycle-type question.
- It reinforces that symbolic restricted-permutation methods were active in the
  same period as the menage/Latin-rectangle work, but it does not currently look
  like the decisive fixed-cycle-type citation.
