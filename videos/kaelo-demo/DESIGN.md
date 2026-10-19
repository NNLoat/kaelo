# Kaelo Demo — Design Spec (brand truth)

Derived from `DEMO_VIDEO_BRIEF.md` §3 and `frontend/src/index.css`. This is the
design source of truth for the HyperFrames build. Frontmatter tokens are normative.

## Tokens (exact)
- ink `#0f172a` — primary text, headings
- paper `#f8fafc` — page / video background
- accent `#1c6b5a` — teal brand; wordmark, primary buttons, Overall bar, Met/Strong dots
- accent-strong `#15584a` — hover, strong status text
- hairline `#e2e8f0` — borders, dividers, empty bar tracks
- muted `#64748b` — secondary text, labels, source tags
- caution `#b4551d` — ONLY warnings / Partial / Fair / unverified-code disclaimer
- red-700 `#b91c1c` — Unmet / Weak only
- white `#ffffff` — cards

## Type (system/safe fonts only — no custom @font-face needed)
- serif: `Georgia, "Times New Roman", serif` — headings + wordmark
- sans: `ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif` — UI/body
- mono: `ui-monospace, monospace` — code

## Video type scale (1080p)
- title 88px Georgia; section heading 56px Georgia; body 32px sans;
  stat numerals 120px Georgia tabular; captions 28px; source tags 18px muted.

## Components
- Cards: white, 1px hairline border, 8px radius, shadow `0 1px 2px rgba(15,23,42,.06)`.
- Score bars: 4px track in hairline; fill ink@40% except Overall = accent + bold value.
  Values to 2 decimals. Pending reads `scoring…`.
- Status dots (always paired with a word): Met/Strong=accent; Partial/Fair=caution;
  Unmet/Weak=red-700; Not applicable=muted.
- Wordmark: the word "Kaelo" in Georgia, accent. No logo file.

## Motion discipline (brief §2)
- GSAP eases `power2.out` / `power3.inOut`; entrance stagger 0.06–0.1s.
- NO bouncy/elastic eases, NO spinning 3D.
- Default transition: 0.4s cross-fade on paper. Section breaks (S03→S04, S09→S10): 0.6s teal wipe L→R.
- Cursor: macOS-style pointer, 0.5–0.8s smooth moves, 120ms accent press ripple @20% on click.

## Safe area
- Keep text ≥ 96px from every edge.

## Guardrails (brief §8)
- Generated code labelled unverified / never executed; never raises a paper's score.
- All S11 impact figures labelled estimates (muted strip is mandatory).
- Persona avatars = original generic illustrations, not real people.
- Source tags [n] visible on stat scenes.

## Architecture
- Modular: thin `index.html` orchestrator + `compositions/s01..s12.html` sub-comps.
- One track (1) for sequential scenes; root `data-duration="295"`.
- No audio in v1.
