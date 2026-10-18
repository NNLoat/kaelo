# Kaelo — Demo Video Brief (for HyperFrames)

> **Purpose:** a ≤ 5:00 pitch-style demo video for the **Mahidol AI Community 2026: AI Adoption Challenge with Kiro**, **Track B (students)**, category **การสนับสนุนการพัฒนางานวิจัยและนวัตกรรม (supporting research and innovation)**.
> **Production mode:** animated **HTML mockups** of the Kaelo UI (no screen recordings), **no narration** in v1 (on-screen text carries the story), a **voice-over script** is included (§9) in case the team records one later.
> **Target runtime:** **4:55** (hard cap 5:00 per the rules [16]).

---

## 0. How to use this brief (read first, HyperFrames agent)

1. Build **one HyperFrames composition per scene** (S01–S12 in §5), then stitch them in order. Use HyperFrames' own conventions (HTML + CSS + GSAP, timing via its data attributes, per the HyperFrames skill) — this brief only specifies *what* happens *when*.
2. All UI mockups must **recreate the real Kaelo screens** described in §4, using the exact tokens in §3. Do not invent features, buttons or screens that the prototype doesn't have (see guardrails, §8).
3. Anything marked **`TODO(team)`** is content a teammate will supply (real paper titles, scores, team names). Until then, render the placeholder text shown, styled exactly as the final content would be, so swapping is a text edit.
4. Every number shown on screen carries a small source tag like `[1]` that maps to §10. Keep the tag visible (bottom-right of the stat, `muted` colour, 18 px).
5. No voice in v1 ⇒ on-screen text must be readable on its own. Rule of thumb: hold every text block for **at least 1 s + 1 s per 3 words** (English), and never show more than ~18 words at once.

---

## 1. What the judges score, and where the video answers it

The video is the "Presentation / Demo Video (ไม่เกิน 5 นาที)" item and should flow **Problem → Solution → AI/Kiro → Prototype → Expected Impact** [16]. It is read by the Round 1 Technical Review committee and supports the Round 2 pitch. Track A and Track B use the same rubric but are judged separately; Track B finalists may apply for follow-on development funding toward an MVP and a pilot inside the university [16].

| Round 1 criterion (points) [16] | Where the video earns it |
|---|---|
| Fit with theme & use of Kiro as the main tool (20) | S10: spec-driven build in Kiro (5 specs, steering, hook, skills, 9 ADRs); research & innovation category framing in S03 |
| Creativity & innovation (20) | S04/S06/S09: standards-based reproducibility score (TRIPOD+AI, ACM/ML/FAIR4RS), code generation for code-less papers, pre-submission review |
| Feasibility in a university context (30) — **largest weight** | S03 (Mahidol scale), S10 (sound architecture, security/privacy), S11 (quantified impact), S12 (pilot path) |
| Prototype quality (20) | S06, S07, S09: three end-to-end demos of working flows |
| Documentation & presentation (10) | Clear structure, cited numbers, tidy visuals throughout |

Round 2 adds Impact (25), Implementation readiness (20), AI & Kiro use (15), Innovation (15), Prototype & demo (15), Q&A (10) [16] — the same scenes cover these.

---

## 2. Production specs

| Item | Value |
|---|---|
| Resolution / fps | 1920 × 1080, 30 fps, 16:9 |
| Duration | 4:55 (295 s); hard cap 5:00 |
| Audio | Soft instrumental music bed (`TODO(team)`: pick a royalty-free track, ~90–100 BPM, calm/optimistic), light UI SFX on clicks (optional, −18 dB). No voice in v1. |
| Language | On-screen text in **English** (concise). Thai VO script in §9 for an optional later recording; if a VO is added, burn-in English subtitles from the §9 English column. |
| Safe area | Keep text ≥ 96 px from every edge |
| Motion | Calm, editorial. GSAP eases `power2.out` / `power3.inOut`; entrance stagger 0.06–0.1 s; no bouncy/elastic eases, no spinning 3D. |
| Transitions | Default: 0.4 s cross-fade on `paper` background. Section breaks (S03→S04, S09→S10): 0.6 s teal wipe left-to-right. |
| Cursor | Mockup demos use a simulated macOS-style pointer that moves on a smooth curve (0.5–0.8 s per move) and shows a 120 ms press ripple in `accent` at 20 % opacity on click. |

---

## 3. Visual system (match the app exactly)

Taken from `frontend/src/index.css` and the components.

| Token | Hex | Use |
|---|---|---|
| `ink` | `#0f172a` | Primary text, headings |
| `paper` | `#f8fafc` | Page / video background |
| `accent` | `#1c6b5a` | Teal brand: wordmark, primary buttons, "Overall" bar, "Met"/"Strong" dots |
| `accent-strong` | `#15584a` | Button hover, strong status text |
| `hairline` | `#e2e8f0` | Borders, dividers, empty bar tracks |
| `muted` | `#64748b` | Secondary text, labels, source tags |
| `caution` | `#b4551d` | **Only** warnings / "Partial" / "Fair" / the unverified-code disclaimer. Never decoration. |
| `red-700` | `#b91c1c` | "Unmet" / "Weak" status only |
| White | `#ffffff` | Cards |

- **Type:** headings and wordmark in **Georgia** (serif, the app's `--font-serif`); UI/body in the system sans stack (`ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif`); code in `ui-monospace, monospace`. Thai text (if any appears): `"Noto Sans Thai", "Sarabun", sans-serif`.
- **Video type scale (1080p):** title 88 px Georgia; section heading 56 px Georgia; body 32 px sans; stat numerals 120 px Georgia, tabular; captions 28 px; source tags 18 px `muted`.
- **Cards:** white, 1 px `hairline` border, 8 px radius, soft shadow `0 1px 2px rgba(15,23,42,.06)`.
- **Score bars:** 4 px tall rounded track in `hairline`; fill `ink` at 40 % opacity, except **Overall** which fills `accent` and has a bold value. Values always shown to 2 decimals (e.g. `0.82`). Pending state reads `scoring…`.
- **Status dots** (always paired with a word so colour is never the only signal): Met / Strong = `accent`; Partial / Fair = `caution`; Unmet / Weak = `red-700`; Not applicable = `muted`.
- **Logo:** there is no logo file; the wordmark is the word **Kaelo** in Georgia, `accent`.
- **Mood:** a quiet academic journal, not a flashy SaaS ad. Lots of `paper` white space, hairline rules, serif headlines.

---

## 4. Mockup screen library (recreate these)

Build these as reusable HTML components at app scale (content column ≈ 768 px wide for Reader/Writer, centred, then scaled ×1.35–1.6 in the frame so it reads at 1080p). Labels in quotes are the **exact UI strings**.

**M1 — Landing (signed out).** Left: "Kaelo" (teal serif) → headline two lines: "Most papers don't reproduce." / "Find the ones that do." → muted sub-copy: "Kaelo searches the literature, scores each paper's reproducibility, and generates the missing code when a repo isn't there." Right: white card "Sign in" with username/password fields.

**M2 — AuthBar (top of every signed-in screen).** "Kaelo" serif wordmark left; right: username (`muted`), a segmented toggle "reader | writer" (active segment teal with white text), and a "Sign out" outline button. Hairline rule underneath.

**M3 — Reader search.** Input with placeholder "Search papers by topic, method, or keyword" + teal "Search" button (shows "Searching…" while loading). Skeleton cards while loading. "Sort by" control (Relevance / …). Result cards: serif title, muted authors, source badges (**OpenAlex**, **arXiv**), a one-line AI relevance blurb, then three bars in a row: "Relevance", "Reproducibility", "Overall" (Overall emphasised). Reproducibility may first show "scoring…" then fill in (it's computed asynchronously).

**M4 — Paper detail.** Title, authors, "Abstract", "Scores", "Repository" (link, or "No repository associated with this paper."), "Source links", "Experiment setup" (rows: Hyperparameters / Datasets / Environment, or "Not provided"). Then the breakdown card:
- "How the reproducibility score was reached"
- muted line: "Evaluated against ‹standard name› in ‹field›" and "Quality 0.xx · Agreement 0.xx"
- two bars: "Code quality", "Setup completeness"
- (if no repo) "No code repository was found, which lowered the code-quality contribution."
- "Where this paper lost points": category rows sorted worst-first, each with a bar + status word (Strong ≥ 0.85, Fair 0.60–0.85, Weak < 0.60)
- criterion rows with Met / Partial / Unmet / Not applicable dots and a short evidence note
- "Paper-to-code discrepancies" list
- a short plain-language explanation paragraph
Below: "Code generation" section with button "Generate code" (no repo) or "Align code" (has repo) and the small note "Opt-in. Generated code is unverified and never executed."; "Reproducibility review" section with button "Review manuscript & code".

CS categories (exact names from `scoring_rule.md` §10.3): Get the Code · Install & Set Up · Run the Code · Match the Paper · Read the Docs · Independent Check · Find, Cite & License.
Medicine categories (§10.2): Purpose & Target Patients · Data Used · How the Model Was Built · Performance Results · Code & Model Access · Safe Use & Limits · Ethics & Registration.

**M5 — Job status.** "Queued…" → "Generating…" with a "Cancel" button.

**M6 — Artifact view.** Amber disclaimer box (caution border/tint): "Unverified, machine-generated code. It was not executed, compiled, or verified." Row: "Code quality 0.xx" (monospace number) + muted one-line rationale; "Download code" outline button. Two-pane: left file nav (e.g. `README.md`, `train.py`, `model.py`, `config.yaml`, `requirements.txt`), right monospace code view.

**M7 — Writer workspace.** Heading "Your workspace"; sub-copy "Add a paper you've written and upload its manuscript and code to evaluate its reproducibility."; input "arXiv ID, DOI, or paper URL" + "Add paper"; list of claimed papers.

**M8 — Claim workspace.** "Back to your papers"; paper reference in monospace as the title; "Remove paper". Cards: **Manuscript** ("Upload manuscript" → shows stored filename) and **Source code** (tabs "Archive file | Git URL"; URL field "https://github.com/owner/repo"; "Fetch" → list of stored file paths). Sections "Generate code" (button "Generate from upload") and "Reproducibility review" (button "Review manuscript & code").

**M9 — Review report.** Header "Reproducibility review", disclaimer line, "Download report" button; left "On this page" jump-nav listing the report's sections (e.g. "Gaps and inconsistencies", "Recommended improvements"); right a readable Markdown report with serif headings.

**Do not show** the ⓘ score tooltips: their copy is still placeholder text in the app.

---

## 5. Timeline at a glance

| # | Scene | In | Out | Dur | Arc beat |
|---|---|---|---|---|---|
| S01 | Hook | 0:00 | 0:15 | 15 s | Problem (universal) |
| S02 | The reproducibility crisis | 0:15 | 0:50 | 35 s | Problem (evidence) |
| S03 | Why it matters at Mahidol | 0:50 | 1:05 | 15 s | Problem → context |
| S04 | Meet Kaelo | 1:05 | 1:30 | 25 s | Solution |
| S05 | Persona 1: พล (CS) | 1:30 | 1:40 | 10 s | Prototype |
| S06 | Demo 1 — Search & score | 1:40 | 2:25 | 45 s | Prototype |
| S07 | Demo 2 — Generate missing code | 2:25 | 3:00 | 35 s | Prototype |
| S08 | Persona 2: น้ำ (Medicine) | 3:00 | 3:10 | 10 s | Prototype |
| S09 | Demo 3 — Writer review (TRIPOD+AI) | 3:10 | 3:55 | 45 s | Prototype |
| S10 | How it's built (Kiro, design, security) | 3:55 | 4:25 | 30 s | AI / Kiro |
| S11 | Expected impact (numbers) | 4:25 | 4:45 | 20 s | Impact |
| S12 | Close: Mahidol research ecosystem | 4:45 | 4:55 | 10 s | Impact / CTA |
| | **Total** | | | **295 s = 4:55** | |

Split: Problem 65 s (22 %) · Solution 25 s (8 %) · Demos 145 s (49 %) · Kiro/design 30 s (10 %) · Impact & close 30 s (10 %).

---

## 6. Personas (user stories)

**พล (Pol) — Computer Science (Reader mode)**
Master's student, Faculty of ICT, Mahidol (`TODO(team)`: confirm faculty wording). Needs to reproduce a recent ML paper as the baseline for his thesis.
*User story:* "As a CS grad student, I want to find papers I can actually reproduce, see why a paper is or isn't reproducible, and get starter code when the authors released none, so I don't lose weeks on a dead-end baseline."

**น้ำ (Nam) — Medicine (Writer mode)**
Medical resident / clinical researcher at a Mahidol teaching hospital (`TODO(team)`: e.g. Siriraj or Ramathibodi). She built a clinical prediction model, posted it as a **preprint**, and is revising it for journal submission.
*User story:* "As a clinical researcher, I want to check my own prediction-model paper and code against TRIPOD+AI before I submit, so reviewers don't find the gaps first."

> Why a preprint: in the prototype, a Writer claims a paper by DOI / arXiv id / URL, and the review is grounded in that paper's indexed record (OpenAlex/arXiv). A preprint with a DOI (e.g. medRxiv, indexed by OpenAlex) fits that flow honestly. `TODO(team)`: confirm the chosen paper resolves and gets the Medicine domain → TRIPOD+AI.

---

## 7. Scene-by-scene storyboard

Format per scene: **Visual** · **On-screen text** (exact copy) · **Motion & timing** (seconds relative to scene start) · **Notes**.

### S01 — Hook (0:00–0:15, 15 s)
- **Visual:** `paper` background. A single journal-style paper page (abstract block, a figure, a "Results" table) fades in centre, slightly tilted. Thin hairline lines suggest text.
- **On-screen text:**
  - 0.5–6 s: **"Every discovery is built on someone else's paper."** (Georgia 72 px, ink)
  - 6.5–13 s: **"But what if you can't reproduce it?"** — as it appears, the paper's "Results" table desaturates and a small amber `?` badge pops onto it.
- **Motion:** paper drifts up 20 px over the scene; text lines fade/slide up 24 px with `power2.out`.
- **Notes:** deliberately cross-disciplinary: no CS or medical imagery yet.

### S02 — The reproducibility crisis (0:15–0:50, 35 s)
- **Visual:** a sequence of four stat cards, each full-frame, big Georgia numeral + one line + source tag. Simple icon top-left of each card (flask, coin stack, notebook, clock), drawn as thin `ink` line icons.
- **On-screen text (one card at a time):**
  1. 0–8 s: **">70%"** — "of researchers have tried and failed to reproduce another scientist's experiments." `[1]`
  2. 8–16 s: **"US$28B / year"** — "spent in the US alone on preclinical research that can't be reproduced." `[2]`
  3. 16–25 s: **"4%"** — "of 1.4 million public Jupyter notebooks reproduced their original results." `[3]` (subline, muted: "74% of research R scripts crashed on first run." `[4]`)
  4. 25–35 s: **"53.5 days"** — "median time to independently reproduce an ML paper — and over a third never reproduce." `[6][7]`
- **Motion:** numerals count up (0 → value) over 0.8 s, tabular figures; card swap = 0.35 s cross-fade + 16 px slide.
- **Notes:** keep every claim exactly as worded here; the sources support these phrasings (see §10).

### S03 — Why it matters at Mahidol (0:50–1:05, 15 s)
- **Visual:** a calm "map" composition: on the left, a big numeral **"4,909"** with label "Mahidol publications indexed in Scopus, 2025" `[13]`; on the right, two tag chips side by side: **Medicine** and **Computer Science & AI**, joined by a thin teal line.
- **On-screen text:**
  - 0–7 s: "4,909 Mahidol publications in Scopus in 2025." `[13]`
  - 7–15 s: "World-class research means research others can **verify and build on**." `[12]` — chips "Medicine" + "Computer Science & AI" animate in beneath, with a muted caption: "Two fields at the heart of Mahidol's research and AI-in-healthcare push." `[12][14]`
- **Notes:** S01–S02 stay universal; this scene narrows to the two fields the demos cover.

### S04 — Meet Kaelo (1:05–1:30, 25 s)
- **Visual:** 0–8 s: recreate **M1 Landing** hero full-frame (wordmark, two-line headline, sub-copy). 8–25 s: the hero shrinks to the left third; on the right, three feature rows build in, each with a line icon:
  1. **Search that ranks by reproducibility** — "OpenAlex + arXiv, ranked by relevance *and* reproducibility."
  2. **Scores grounded in published standards** — "TRIPOD+AI for Medicine · ACM Badging + ML Code Completeness + FAIR4RS for CS." `[15]`
  3. **Closes the gap** — "Generates starter code when no repo exists, and reviews your own manuscript before submission."
- Bottom strip: the "reader | writer" toggle from **M2**, with captions "Reader — evaluate others' papers" / "Writer — check your own".
- **Motion:** rows stagger in 0.15 s apart; the toggle flips reader→writer once at ~22 s.

### S05 — Persona 1: พล (1:30–1:40, 10 s)
- **Visual:** persona card: a simple flat illustrated avatar (original, neutral style; young man, laptop), name **"พล (Pol)"**, role "CS master's student · Faculty of ICT" `TODO(team) confirm`, and his user story in one line: *"I need a baseline I can actually reproduce for my thesis."*
- **Motion:** card slides in from the right; a small "Reader mode" pill appears in teal.

### S06 — Demo 1: Search & reproducibility score (1:40–2:25, 45 s)
- **Visual (mockups M2 → M3 → M4):**
  - 0–6 s: signed-in Reader screen (M2+M3 empty state). Cursor clicks the search box; the query types itself: **`TODO(team): CS query`** (placeholder: "graph neural networks for molecular property prediction").
  - 6–9 s: click "Search" → "Searching…" → skeleton cards.
  - 9–20 s: 3–4 result cards cascade in with source badges and bars. Reproducibility on one card shows "scoring…" then fills. A callout bubble points at the bars: **"Ranked by relevance *and* reproducibility."**
  - 20–24 s: cursor opens the top card (`TODO(team): CS paper title`).
  - 24–42 s: **M4 detail**, slow vertical scroll: "Evaluated against ‹CS standard› in Computer Science", "Quality 0.xx · Agreement 0.xx"; then "Where this paper lost points" rows (example order: **Match the Paper — Fair**, **Run the Code — Weak**, **Get the Code — Strong** …); then 2–3 criterion rows with Met/Partial/Unmet dots; then "Paper-to-code discrepancies" (one item highlighted with a soft teal outline).
  - 42–45 s: hold on the discrepancy.
- **On-screen captions (lower third, 28 px):**
  - 9 s: "One search across OpenAlex and arXiv."
  - 24 s: "See exactly *why* a paper scores the way it does."
  - 34 s: "Spot where the code doesn't match the paper, before you clone it."
- **Data:** all titles, authors and scores = `TODO(team)` (render placeholders like "0.82"). Keep the arithmetic believable: Overall should sit between Relevance and Reproducibility, nearer Relevance (the default blend is 0.7 relevance / 0.3 reproducibility).

### S07 — Demo 2: Generate the missing code (2:25–3:00, 35 s)
- **Visual (M4 → M5 → M6):**
  - 0–6 s: back on results, open a second paper (`TODO(team): CS paper with no repo`). Detail shows "No repository associated with this paper." and the breakdown line "No code repository was found, which lowered the code-quality contribution."
  - 6–9 s: "Experiment setup" rows visible (Hyperparameters / Datasets / Environment filled with `TODO(team)` values).
  - 9–12 s: cursor clicks **"Generate code"**; the note "Opt-in. Generated code is unverified and never executed." is briefly highlighted.
  - 12–17 s: **M5** "Queued…" → "Generating…" (show the "Cancel" button; don't click it). Compress the wait with a subtle 3-dot progress and a "⏩" time-skip chip.
  - 17–33 s: **M6 Artifact view**: amber disclaimer on top, "Code quality 0.xx", file nav; click `README.md` then `train.py` (type-on effect for the first ~12 lines of code).
  - 33–35 s: cursor hovers "Download code".
- **On-screen captions:**
  - 3 s: "No code released? Kaelo drafts it from the paper's experiment setup."
  - 20 s: "Clearly labelled: unverified, never executed, and never used to inflate the paper's score." `ADR-0004`
- **Optional 2 s insert** (if time allows, else skip): a chip "Has a repo? → **Align code** refines the existing source to match the paper."

### S08 — Persona 2: น้ำ (3:00–3:10, 10 s)
- **Visual:** persona card like S05: avatar (original style; young woman in a doctor's coat), **"น้ำ (Nam)"**, "Medical resident & clinical researcher" `TODO(team): hospital/faculty`, one-liner: *"I want reviewers to find nothing I could have fixed myself."*
- **Motion:** card slides in from the left; the AuthBar toggle flips **reader → writer**.

### S09 — Demo 3: Writer review against TRIPOD+AI (3:10–3:55, 45 s)
- **Visual (M7 → M8 → M9):**
  - 0–6 s: **M7 Your workspace**. Cursor types into "arXiv ID, DOI, or paper URL": `TODO(team): DOI of the medical preprint` (placeholder "10.1101/2026.xx.xx.xxxxxxx") → "Add paper".
  - 6–16 s: **M8 Claim workspace**. Click "Upload manuscript" → a PDF icon drops in (`TODO(team): filename.pdf`) → stored filename appears. Switch to the "Git URL" tab, type `TODO(team): https://github.com/…` → "Fetch" → a list of stored source paths appears (`.py`/`.R` files; skipped binaries not shown).
  - 16–20 s: click **"Review manuscript & code"** → M5 "Generating…" (compressed).
  - 20–40 s: **M9 Review report**. "On this page" nav lists sections (e.g. "Gaps and inconsistencies", "Recommended improvements"). Scroll through 2–3 findings; highlight one recommendation per TRIPOD+AI area, e.g. **How the Model Was Built**, **Performance Results**, **Ethics & Registration** (`TODO(team)`: use real findings from a real run).
  - 40–45 s: side overlay card: "Evaluated against **TRIPOD+AI** — 26 weighted criteria" with the seven Medicine category names listed in muted text. Hover "Download report".
- **On-screen captions:**
  - 2 s: "Writer mode: check your *own* paper before submission."
  - 10 s: "Upload the manuscript PDF and point to the code."
  - 22 s: "A review against TRIPOD+AI, the BMJ reporting guideline for clinical prediction models." `[15]`
  - 34 s: "Published ML prediction-model papers report a median of only 38.7% of TRIPOD items." `[9]`
- **Notes:** The Writer workspace in the prototype shows the **review report** (not the score breakdown card); don't put the M4 breakdown in Writer mode.

### S10 — How it's built: Kiro, design, security & privacy (3:55–4:25, 30 s)
Three quick panels, 10 s each, on `paper`, diagram-style.
- **Panel A — Built spec-first with Kiro (0–10 s).** Animated file tree of `.kiro/`: `steering/` (product, tech, structure, workflow), `specs/` (accounts, paper-search, reproducibility-scoring, code-generation, writer-workspace), each spec expanding to `requirements.md → design.md → tasks.md` with arrows, `hooks/spec-nudge.json`, `skills/`. Side column: `docs/adr/` ×9 and `GLOSSARY.md`. Caption: **"5 features, each specified in Kiro: requirements → design → tasks → code. 9 architecture decisions on record."**
- **Panel B — Sound architecture (10–20 s).** Box-and-arrow diagram: React UI → FastAPI → PostgreSQL; FastAPI → OpenAlex / arXiv (sources) · Amazon Bedrock via LangChain (LLM) · GitHub (repo signals); background jobs for scoring and generation. Highlight one principle with a teal outline: **"AI supplies the evidence. The score is computed by a fixed, auditable rule: S = 0.30·Quality + 0.70·Agreement."** (ADR-0009). Small chips: "Pluggable standards (adapter)" (ADR-0008) · "132 automated tests, property-based" `TODO(team): re-run and confirm count`.
- **Panel C — Security & privacy by design (20–30 s).** Six compact rows, each with a line icon:
  1. Passwords hashed with **Argon2**; sessions in signed, **HTTP-only** cookies.
  2. Writer manuscripts & code are **owner-only**: another user's data looks like "not found".
  3. Reader side stores **only index metadata and links**, never others' full text (ADR-0001/0003).
  4. Writer uploads are stored **with the owner's consent** and can be deleted any time.
  5. Uploads are **size- and file-count-capped**, path-traversal-safe, binaries dropped; public repos only (ADR-0006).
  6. Generated code is **never executed** on our servers; secrets live in environment config, never in code.
- **Motion:** each panel builds in ≤ 2 s, holds, cross-fades. Keep text ≥ 28 px.

### S11 — Expected impact (4:25–4:45, 20 s)
- **Visual:** three impact tiles in a row (white cards), each a big numeral + one line + tag. Below them, a thin muted strip: "Estimates: inputs from cited studies; Kaelo's effect assumed, to be validated in a pilot."
  1. **"21–49 h"** — "saved per researcher per year on finding papers" `[10][11]` (model in §8.1)
  2. **"1 in 3"** — "papers flagged as high-risk *before* you invest weeks reproducing them" `[6][7]`
  3. **"26 criteria"** — "TRIPOD+AI pre-submission check, where the published median adherence is 38.7%" `[9][15]`
- **Motion:** tiles rise in with a 0.12 s stagger; numerals count up.

### S12 — Close: Mahidol's research ecosystem (4:45–4:55, 10 s)
- **Visual:** 0–6 s: the line **"Research that others can verify, reproduce, and build on."** followed by muted sub-line **"Kaelo: helping Mahidol research create real-world impact."** `[12][14]`. 6–10 s: end card: teal "Kaelo" wordmark, tagline "Find the ones that do.", team line `TODO(team): team name · members · faculties`, footer "Mahidol AI Community 2026 · Track B · Built with Kiro", and a small "Next: pilot with ICT grad students and a clinical research unit" `TODO(team) confirm`.
- **Motion:** slow 3 % push-in; music resolves.

---

## 8. Impact model and claims guardrails

### 8.1 How the S11 numbers are derived (keep this in the concept paper, too)

| Stage | Baseline evidence | Kaelo mechanism | Estimate shown | Confidence |
|---|---|---|---|---|
| **Finding papers** | Academics read ~22 articles/month and spend ~16 min browsing/searching per article read [10] ⇒ 22 × 12 × 16 min ≈ **70 h/year** on finding articles. | AI query expansion + one merged OpenAlex/arXiv search + per-result relevance blurb + reproducibility ranking. | If Kaelo reaches the **30–70 %** workload reduction reported for AI-assisted study screening [11]: 70.4 h × 0.30–0.70 ≈ **21–49 h saved / researcher / year**. | Medium-low: [11] measures systematic-review screening, used here as an analogue. |
| **Choosing what to reproduce** | 36.5 % of 255 ML papers could not be independently reproduced [6]; successful reproductions took a median of **53.5 days** (mean 218.8) [7]; only 32 % of 601 systems papers' code could be built within 30 min [8]. | Standards-based score + "where it lost points" + repo signals, shown *before* the user invests effort. | **"1 in 3"** papers at high risk can be flagged up front (from the 36.5 % failure rate [6]). Time saved depends on how many dead-end attempts are avoided: each avoided one is weeks of effort [7]. | Medium: the base rate is sourced; Kaelo's flagging accuracy still needs validation. |
| **Checking code against claims** | 74 % of research R files crashed on first run (56 % after cleaning) [4]; 4 % of Jupyter notebooks reproduced their results [3]. | "Paper-to-code discrepancies" + Run the Code / Match the Paper categories; Align code. | Qualitative: discrepancies are surfaced in minutes instead of being found mid-reproduction. | Qualitative only: no time figure claimed. |
| **Own-paper quality (Writer, Medicine)** | ML clinical prediction-model papers report a median of 38.7 % of TRIPOD items [9]. | Pre-submission review against all 26 TRIPOD+AI criteria [15]. | Illustrative scale: if 10 % of Mahidol's ~4,909 annual Scopus papers [13] used it ⇒ **~490 pre-submission checks a year**. | Illustrative (adoption rate is an assumption). |

### 8.2 Guardrails (the video must not cross these)
- Show only what the prototype actually does. No mobile app, no SSO, no "one-click reproduce" or code execution, no private-repo support, no full-text hosting for Reader papers.
- Don't claim regulatory compliance (e.g. PDPA, HIPAA) or encryption at rest; the slide says only what's in §7 S10 Panel C.
- Generated code is always described as **unverified / not executed**; it never raises a paper's score (ADR-0004).
- The reproducibility score is described as **standards-conformance** (how well a paper and its code meet TRIPOD+AI / ACM-ML-FAIR4RS), **not** a guarantee that results replicate.
- All S11 figures are labelled as estimates (the muted strip in S11 is mandatory).
- Persona avatars are original, generic illustrations, not real people, mascots or stock-photo look-alikes.

---

## 9. Voice-over script (optional; for a later recording)

Thai VO for recording; the English column doubles as subtitles if a VO is added. Pace ≈ 2.5–3 Thai words/second; lines fit their scene windows.

| Scene | Thai VO | English (subtitle / translation) |
|---|---|---|
| S01 | ทุกการค้นพบ ล้วนต่อยอดจากงานวิจัยของคนอื่น… แต่ถ้าเราทำซ้ำผลลัพธ์นั้นไม่ได้ล่ะ? | Every discovery builds on someone else's paper… but what if you can't reproduce it? |
| S02 | นักวิจัยกว่าเจ็ดสิบเปอร์เซ็นต์ เคยพยายามทำซ้ำการทดลองของผู้อื่นแล้วไม่สำเร็จ เฉพาะในสหรัฐฯ งานวิจัยพรีคลินิกที่ทำซ้ำไม่ได้ สิ้นเปลืองราวสองหมื่นแปดพันล้านดอลลาร์ต่อปี แม้แต่โค้ดที่เผยแพร่แล้ว จากโน้ตบุ๊กกว่าหนึ่งล้านสี่แสนไฟล์ มีเพียงสี่เปอร์เซ็นต์ที่ได้ผลเหมือนเดิม และการทำซ้ำงาน ML หนึ่งชิ้นให้สำเร็จ ใช้เวลาราวห้าสิบสามวัน | Over 70% of researchers have failed to reproduce another scientist's experiments. In the US alone, irreproducible preclinical research costs about 28 billion dollars a year. Of 1.4 million public notebooks, only 4% reproduced their results. And reproducing one ML paper takes a median of 53 days. |
| S03 | ในปี 2025 มหาวิทยาลัยมหิดลมีผลงานตีพิมพ์ในฐานข้อมูล Scopus กว่า 4,900 เรื่อง งานวิจัยระดับโลก ต้องเป็นงานที่ผู้อื่นตรวจสอบและต่อยอดได้ โดยเฉพาะด้านการแพทย์ และวิทยาการคอมพิวเตอร์และ AI | In 2025, Mahidol had over 4,900 publications in Scopus. World-class research must be research others can verify and build on, especially in medicine, computer science and AI. |
| S04 | ขอแนะนำ Kaelo เครื่องมือค้นหางานวิจัยด้วย AI ที่จัดอันดับตามความสามารถในการทำซ้ำ ให้คะแนนตามมาตรฐานสากล และช่วยปิดช่องว่าง ด้วยการร่างโค้ดเมื่อไม่มีโค้ด และตรวจงานของเราเองก่อนส่งตีพิมพ์ มีสองโหมด คือ Reader และ Writer | Meet Kaelo: AI-assisted paper search that ranks by reproducibility, scores papers against published standards, and closes the gap — drafting code when none exists and reviewing your own work before submission. Two modes: Reader and Writer. |
| S05 | พบกับพล นักศึกษาปริญญาโท คณะ ICT ที่ต้องหางานวิจัยต้นแบบที่ทำซ้ำได้จริง มาใช้ในวิทยานิพนธ์ | Meet Pol, an ICT master's student who needs a baseline he can actually reproduce for his thesis. |
| S06 | พลค้นหาครั้งเดียว Kaelo ดึงผลจาก OpenAlex และ arXiv พร้อมกัน แล้วจัดอันดับด้วยทั้งความเกี่ยวข้องและความสามารถในการทำซ้ำ เมื่อเปิดดู จะเห็นว่าคะแนนมาจากไหน งานนี้เสียคะแนนในมุมใด และจุดที่โค้ดไม่ตรงกับเปเปอร์ ก่อนจะเสียเวลาโคลนโค้ดมาลอง | One search covers OpenAlex and arXiv, ranked by relevance and reproducibility. Open a paper to see where the score comes from, where it lost points, and where the code disagrees with the paper, before you clone anything. |
| S07 | บางเปเปอร์ไม่มีโค้ดให้เลย พลกด Generate code Kaelo ร่างโค้ดตั้งต้นพร้อม README จาก Experiment Setup ของเปเปอร์ โดยระบุชัดว่ายังไม่ผ่านการตรวจสอบ ไม่เคยถูกรัน และไม่ถูกนำไปเพิ่มคะแนนของเปเปอร์ | Some papers ship no code. Pol clicks Generate code, and Kaelo drafts starter code and a README from the paper's experiment setup, clearly labelled unverified, never executed, and never used to boost the paper's score. |
| S08 | ส่วนน้ำ แพทย์ประจำบ้านและนักวิจัยคลินิก กำลังปรับปรุงพรีปรินต์โมเดลทำนายทางคลินิก ก่อนส่งวารสาร | Nam, a medical resident and clinical researcher, is revising her clinical prediction-model preprint before journal submission. |
| S09 | น้ำเปลี่ยนเป็นโหมด Writer เพิ่มงานด้วย DOI อัปโหลดต้นฉบับ PDF และลิงก์โค้ดบน GitHub Kaelo ตรวจตามแนวทาง TRIPOD+AI แล้วสรุปช่องว่างพร้อมข้อเสนอแนะ เพราะงานโมเดลทำนายที่ตีพิมพ์แล้ว รายงานตามเกณฑ์ TRIPOD ได้เพียงราวสามสิบเก้าเปอร์เซ็นต์ | Nam switches to Writer mode, adds her paper by DOI, uploads the manuscript and links her GitHub code. Kaelo reviews it against TRIPOD+AI and lists the gaps and fixes, because published prediction-model papers report only about 39% of TRIPOD items. |
| S10 | เราพัฒนา Kaelo ด้วย Kiro แบบ spec-driven ทุกฟีเจอร์เริ่มจาก requirements, design และ tasks พร้อมบันทึกการตัดสินใจเชิงสถาปัตยกรรม AI มีหน้าที่ให้หลักฐาน แต่คะแนนคำนวณด้วยกฎที่ตายตัวและตรวจสอบได้ รหัสผ่านถูกแฮชด้วย Argon2 ข้อมูลของผู้เขียนเห็นได้เฉพาะเจ้าของ ฝั่งผู้อ่านเก็บเพียงข้อมูลอ้างอิงและลิงก์ และโค้ดที่สร้างขึ้นจะไม่ถูกรันบนเซิร์ฟเวอร์ของเรา | We built Kaelo spec-first with Kiro: every feature went from requirements to design to tasks, with architecture decisions on record. AI supplies the evidence; a fixed, auditable rule computes the score. Passwords are hashed with Argon2, Writer data is owner-only, the Reader side stores only references and links, and generated code never runs on our servers. |
| S11 | หากลดภาระการคัดกรองได้ตามที่งานวิจัยด้าน AI รายงาน นักวิจัยหนึ่งคนจะประหยัดเวลาค้นหาได้ราว 21 ถึง 49 ชั่วโมงต่อปี รู้ล่วงหน้าว่าเปเปอร์ไหนเสี่ยงทำซ้ำไม่ได้ และตรวจงานตัวเองครบ 26 เกณฑ์ก่อนส่ง | If Kaelo matches the screening savings reported for AI tools, one researcher saves about 21 to 49 hours a year on search, knows which papers are risky before investing weeks, and checks their own work against all 26 criteria before submitting. |
| S12 | Kaelo ช่วยให้งานวิจัยของมหิดล ตรวจสอบได้ ทำซ้ำได้ และต่อยอดสู่ผลกระทบจริง | Kaelo helps Mahidol research become verifiable, reproducible, and ready for real-world impact. |

---

## 10. References

Numbers on screen map to these. "Used for" says exactly which claim each supports.

1. Baker M. *1,500 scientists lift the lid on reproducibility.* Nature. 2016;533:452–454. https://doi.org/10.1038/533452a — Used for: >70% failed to reproduce others' experiments; >50% failed to reproduce their own.
2. Freedman LP, Cockburn IM, Simcoe TS. *The economics of reproducibility in preclinical research.* PLOS Biology. 2015;13(6):e1002165. https://doi.org/10.1371/journal.pbio.1002165 — Used for: >50% irreproducibility; ~US$28B/year in the US.
3. Pimentel JF, Murta L, Braganholo V, Freire J. *A Large-scale Study about Quality and Reproducibility of Jupyter Notebooks.* MSR 2019. https://2019.msrconf.org/details/msr-2019-papers/36/A-Large-scale-Study-about-Quality-and-Reproducibility-of-Jupyter-Notebooks — Used for: 1.4M notebooks; 24% ran without errors; 4% reproduced the same results.
4. Trisovic A, Lau MK, Pasquier T, Crosas M. *A large-scale study on research code quality and execution.* Scientific Data. 2022;9:60. https://doi.org/10.1038/s41597-022-01143-6 — Used for: 74% of 9,000+ R files failed on first run, 56% after code cleaning.
5. Gundersen OE, Kjensmo S. *State of the Art: Reproducibility in Artificial Intelligence.* AAAI-18, pp. 1644–1651. https://ojs.aaai.org/index.php/AAAI/article/view/11503 — Background (optional): of 400 AI conference papers surveyed, none documented all the variables needed for reproduction.
6. Raff E. *A Step Toward Quantifying Independently Reproducible Machine Learning Research.* NeurIPS 2019. https://proceedings.neurips.cc/paper/2019/file/c429429bf1f2af051f2021dc92a8ebea-Paper.pdf — Used for: 162 of 255 (63.5%) reproduced ⇒ 36.5% not ("over a third", "1 in 3").
7. Raff E. *Research Reproducibility as a Survival Analysis.* AAAI 2021. https://arxiv.org/abs/2012.09932 — Used for: median 53.5 days (mean 218.8 days) to reproduce, among reproduced papers with dates.
8. Collberg C, Proebsting TA. *Repeatability in computer systems research.* Communications of the ACM. 2016;59(3):62–69. https://doi.org/10.1145/2812803 — Used for: of 601 papers, 32% built within 30 min; 54% in total even with author help.
9. Andaur Navarro CL, Damen JAA, Takada T, et al. *Completeness of reporting of clinical prediction models developed using supervised machine learning: a systematic review.* BMC Medical Research Methodology. 2022;22. https://doi.org/10.1186/s12874-021-01469-6 — Used for: median TRIPOD adherence 38.7% across 152 studies.
10. Tenopir C, Volentine R, King DW. *Scholarly reading and the value of academic library collections: results of a study in six UK universities.* Insights. 2012;25(2):130–149. https://doi.org/10.1629/2048-7754.25.2.130 — Used for: ~22 articles/month; 16 min browsing/searching per article (basis for ~70 h/year).
11. O'Mara-Eves A, Thomas J, McNaught J, Miwa M, Ananiadou S. *Using text mining for study identification in systematic reviews: a systematic review of current approaches.* Systematic Reviews. 2015;4:5. https://doi.org/10.1186/2046-4053-4-5 — Used for: 30–70% screening workload reduction (at ~95% recall).
12. Mahidol University. *Mahidol University Strategic Plan 2024–2027.* https://op.mahidol.ac.th/pl/wp-content/uploads/2024/07/MAHIDOL-UNIVERSITY-STRATEGIC-PLAN-2024-2027.pdf — Used for: pillar "World Class Research & Innovation"; research value chain for societal benefit; quality-research targets; health sciences as core strength.
13. Mahidol University Research Administration. *International publications (Scopus/WoS), updated 23 Dec 2025.* https://op.mahidol.ac.th/ra/contents/research_output/INTER-PUB/20251223_MU_PUB_CITED.pdf — Used for: 4,909 Scopus publications (all document types) in 2025.
14. Bangkok Post (PR). *Mahidol University Leads Health Transformation for Real Impact.* https://bangkokpost.com/thailand/pr/2988916/mahidol-university-leads-health-transformation-for-real-impact — Used for: the "Real World Impact" theme; AI-integrated healthcare as a priority.
15. Collins GS, Moons KGM, Dhiman P, et al. *TRIPOD+AI statement.* BMJ. 2024;385:e078378. https://doi.org/10.1136/bmj-2023-078378 — Used for: TRIPOD+AI as the reporting guideline for clinical prediction models (Kaelo uses 26 weighted criteria derived from it; see `scoring_rule.md`).
16. Mahidol University IT Division. *Mahidol AI Community 2026: AI Adoption Challenge with Kiro.* https://muit.mahidol.ac.th/mu-ai-community-2026/ — Used for: ≤5-min video, Problem→Solution→AI/Kiro→Prototype→Impact flow, judging rubrics, Track B support.
17. HeyGen HyperFrames overview (tooling reference). https://www.noqta.tn/en/blog/heygen-hyperframes-html-to-mp4-ai-agent-video-2026

Internal project sources: `README.md`, `.kiro/steering/*`, `.kiro/specs/*`, `GLOSSARY.md`, `scoring_rule.md` v1.2, `docs/adr/0001–0009`, `summary-1st-prototype.md`, `frontend/src/**`.

---

## 11. Open TODOs for the team

| # | Item | Scene |
|---|---|---|
| 1 | CS search query + 3–4 result cards (titles, authors, sources, blurbs, three scores each) from a real run | S06 |
| 2 | CS paper detail: standard line, Quality/Agreement, category scores, 2–3 criteria with evidence notes, 1 discrepancy | S06 |
| 3 | CS paper with **no repo**: experiment-setup values, generated file list, ~12 lines of `train.py`, code-quality score + rationale | S07 |
| 4 | Medical preprint DOI, PDF filename, GitHub URL, stored source paths; confirm it resolves to Medicine → TRIPOD+AI | S09 |
| 5 | 2–3 real findings from the review report | S09 |
| 6 | Re-run `cd backend && uv run pytest` and confirm the test count (last recorded: 132 passed) | S10 |
| 7 | Team name, members, faculties; confirm the persona affiliations (ICT; hospital) | S05, S08, S12 |
| 8 | Pilot / next-step line for the end card | S12 |
| 9 | Music track (royalty-free) | all |
| 10 | Before submitting source code: rotate the AWS key noted in `TODO.md` and exclude `.env` | — |
