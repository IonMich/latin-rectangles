# Produce and verify the mathematical presentation

These maintainer scripts record the macOS environment used to generate the
committed assets. They are not a portable, fully pinned build pipeline. Using
or building the Python package does not require running them; the release
ships the reviewed GIFs, stills, SVGs and self-contained player directly.

Run from the repository root. Use the installed Node runtime and its
`node_modules` directory (Sharp, marked and Playwright), a local KaTeX 0.16.22
ESM bundle, ffmpeg, and the installed macOS Google Chrome. The Python scene
generator uses the standard library. No project dependencies were added.

```console
uv run --frozen tools/math_presentation/scene.py
node tools/math_presentation/build.mjs /absolute/katex.mjs
node tools/math_presentation/inspect.mjs /absolute/node_modules
node tools/math_presentation/export.mjs /absolute/node_modules
node tools/math_presentation/package.mjs /absolute/node_modules /absolute/katex.mjs
node tools/math_presentation/review.mjs /absolute/node_modules
```

`scene.py` derives and verifies the scene from the preserved mathematical
README data. `build.mjs` compiles all mathematical expressions to native
MathML and embeds the data into `interactive.template.html`, producing the
self-contained player. `inspect.mjs` exercises the player and saves evidence.

`export.mjs` samples that same player at six frames per second, checks that
each frame fits, and exports the finite GIFs and still PNGs. Intermediate
frames live in the ignored `benchmark_results/math-presentation/` directory.

`package.mjs` renders `README.md` (or the optional source argument), follows its local
asset/document references, and creates a relocatable bundle with two review
views. `review.mjs` temporarily serves the bundle on loopback, exercises its
controls, checks its links and responsive rendering, and saves screenshots.

Outputs are in `docs/assets/math-motion/` and
`docs/evidence/math-presentation/`. The accepted source is `README.md`.
These commands read the README and do not replace it. The bundled
`readme.css` retains the typography of the accepted review rendering.
