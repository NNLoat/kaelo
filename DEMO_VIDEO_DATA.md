# Kaelo — Demo Video Data (fills DEMO_VIDEO_BRIEF.md §11 TODOs)

> Real data harvested from the live Kaelo app (http://localhost:5173, account
> `test`) via Playwright on 2026-10-19, plus team facts and concept-paper
> inferences. This file is the content source for the HyperFrames build; the
> brief (`DEMO_VIDEO_BRIEF.md`) remains the source for *what happens when*.
>
> **S06 approach: Option A (real data), updated query.** The search query is
> `Machine learning Image Segmentation Artificial intelligence`. The lead paper
> ("Capsules for Biomedical Image Segmentation") scores a **nonzero, partial**
> reproducibility of **0.36** (Relevance 0.95 / Overall 0.54) — it references its
> datasets but ships no runnable code. This is a more nuanced, less jarring story
> than three flat zeros, and still fully real. It flows into S07 (generate the
> missing code).

---

## TODO 1 — CS search: query + result cards (S06)  [UPDATED 2026-10-19]

**Query typed into the search box:** `Machine learning Image Segmentation Artificial intelligence`

> Re-harvested per user feedback: the previous molecular-GNN query gave three
> flat 0.00 reproducibility scores, which read as jarring. This query returns a
> lead paper with a **nonzero, partial** reproducibility score (0.36) — a more
> nuanced, less jarring story while staying fully real (Option A).

Three real result cards (scores = Relevance / Reproducibility / Overall, the
app's own settled values):

| # | Title | Authors | Source | Relevance | Reproducibility | Overall |
|---|---|---|---|---|---|---|
| 1 | Capsules for Biomedical Image Segmentation | Rodney LaLonde, Ziyue Xu, Ismail Irmakci, Sanjay Jain, Ulas Bagci | arXiv | 0.95 | 0.36 | 0.54 |
| 2 | Image Segmentation Using Deep Learning: A Survey | Shervin Minaee, Yuri Y. Boykov, Fatih Porikli, Antonio Plaza, Nasser Kehtarnavaz, Demetri Terzopoulos | arXiv | 0.95 | 0.00 | 0.28 |
| 3 | Understanding Deep Learning Techniques for Image Segmentation | Swarnendu Ghosh, Nibaran Das, Ishita Das, Ujjwal Maulik | arXiv | 0.95 | 0.00 | 0.28 |

**Relevance blurb for card 1 (real, shown on the card / detail):**
> "Highly relevant paper introducing SegCaps, a capsule network architecture for
> biomedical image segmentation that achieves state-of-the-art results with
> minimal parameters across multiple medical imaging datasets."

Arithmetic is the app's real blend (0.3·relevance + 0.7·reproducibility):
card 1 = 0.3·0.95 + 0.7·0.36 = 0.54. Overall now sits sensibly between relevance
and reproducibility — the intended demo shape.

---

## TODO 2 — CS paper detail breakdown (S06)  [UPDATED 2026-10-19]

Use **card 1** ("Capsules for Biomedical Image Segmentation", arXiv, published
2020-04-09). All values below are real.

- **Standard line:** `Evaluated against Baseline in unknown`
- **Quality / Agreement:** `Quality 0.05 · Agreement 0.50`
- **Breakdown bars:** Code quality `0.00` · Setup completeness `0.33`
- **No-repo note (shown):** "No code repository was found, which lowered the code-quality contribution."

**"Where this paper lost points" — category rows (real):**
- Reproduce the Results — **Weak, 50%**
- Run the Code — **Weak, 5%**

**Criterion rows (status · category · evidence note) — real:**
- Unmet · Run the Code — "Code available" → *no inspectable repository*
- Unmet · Run the Code — "Documentation present" → *no README found*
- Unmet · Reproduce the Results — "Dependencies / environment described" → *no environment described*
- **Met** · Reproduce the Results — "Data referenced" → *datasets referenced in setup*

> This is the key nuance for S06: the paper scores **0.36, not 0.00**, because it
> has strong methodological + dataset detail (one **Met** criterion, Agreement
> 0.50) even though no code was released. The honest message: "high relevance,
> partial reproducibility — datasets are referenced, but there's no runnable
> code." It flows naturally into S07 (generate the missing code).

**Experiment setup (real, shown on this paper's detail — good for the S07 setup beat):**
- Hyperparameters: Not provided
- Datasets: "Five lung segmentation datasets from clinical and pre-clinical thoracic CT scans (nearly 2000 CT scans), MRI scans of human subjects' thighs for muscle and adipose tissue segmentation, and natural images for rotation/reflection generalization"
- Environment: Not provided

**Plain-language explanation (real, verbatim — good for a hold/caption):**
> "This paper presents significant barriers to reproduction. The most critical
> gaps are the complete absence of a code repository and any environment
> documentation—you cannot access or run the implementation at all… While the
> paper apparently provides enough methodological detail to partially reconstruct
> the approach (hence the 0.50 score for reproducing results), building on this
> work would require you to essentially re-implement the method from scratch
> without reference implementations or validated environments."

---

## TODO 3 — No-repo CS paper + generated code (S07)

**Paper (real, no repo):** "Kolmogorov–Arnold graph neural networks for molecular
property prediction" — Longlong Li, Yipeng Zhang, Guanghui Wang, Kelin Xia
(OpenAlex, published 2025-08-11). Detail shows "No repository associated with this
paper." and the breakdown note "No code repository was found…". The button reads
**"Generate code"** with the caption "Opt-in. Generated code is unverified and
never executed."

**Experiment setup rows (real, from card 1's detail — card 2 showed "Not yet
available", so use card 1's setup values for the S07 setup beat):**
- Hyperparameters: Not provided
- Datasets: `48 different datasets`
- Environment: Not provided

**Generated artifact (real, from an existing generation in the seed):**
- Files: `README.md`, `config.py`
- **Code quality: 0.65**
- Rationale (real): "The code demonstrates a reasonable understanding of
  curriculum learning and optimizer design with clear documentation and
  configuration structure, but lacks actual implementation files (main.py,
  optimizer code, model definitions), error handling, and validation…"
- Disclaimer banner (real): "Unverified, machine-generated code. It was not
  executed, compiled, or verified."

**`config.py` (first ~18 lines, real — use for the type-on in S07):**
```python
"""Configuration for curriculum learning experiment."""

# Training phases
PHASES = [
    {"hidden_dim": 256, "epochs": 20, "learning_rate": 0.001},
    {"hidden_dim": 512, "epochs": 20, "learning_rate": 0.0005},
    {"hidden_dim": 1024, "epochs": 20, "learning_rate": 0.0002},
]

# Dataset and model
INPUT_DIM = 3072  # CIFAR-10: 32x32x3
OUTPUT_DIM = 10
BATCH_SIZE = 128
NUM_WORKERS = 4

# OneIG optimizer
ONEIG_BETA = 0.9  # Importance weighting parameter
ONEIG_EPSILON = 1e-8  # Numerical stability
```

> Brief's S07 referenced `train.py`; the real seeded artifact ships `README.md` +
> `config.py`. Use the real file nav (README.md → config.py) and type-on `config.py`.

---

## TODO 4 — Medical preprint claim (S09)

The live Writer workspace for account `test` currently has **no claims** ("No
papers yet. Add one above."), so there is no real stored manuscript/source to
screen-harvest. For S09, render the Writer flow with these placeholders styled as
final (swap later once a real claim is added), consistent with the real review
report below:

- Paper ref input (`arXiv ID, DOI, or paper URL`): `10.1101/2026.xx.xx.xxxxxxx` *(placeholder DOI)*
- Manuscript filename shown after upload: `manuscript.pdf` *(placeholder)*
- Source tab: Git URL → `https://github.com/owner/repo` → Fetch → stored paths list *(placeholder)*
- Button: **"Review manuscript & code"**

> The review *report* (TODO 5) is real and from an actual run; only the claim
> inputs are placeholders because the seeded Writer account has no claim yet.

---

## TODO 5 — Review report findings (S09, real)

Real TRIPOD-AI review report harvested from an existing "Reviewed" generation.
Section nav ("On this page"): **Gaps and inconsistencies**, **Recommended improvements**.

**Real findings to surface (pick 2–3 for the scroll):**
- *Document type mismatch* — "The provided evidence is a review article… not a
  model development or validation study. TRIPOD-AI criteria are designed for
  original empirical studies presenting predictive models, not literature
  reviews."
- *Model development gaps (M-D1–M-D5)* — "No model type selected or justified; no
  hyperparameter tuning methodology documented; no internal validation method
  described."
- *Model evaluation (M-D6, M-D7)* — "No performance metrics (discrimination,
  calibration, clinical utility) reported; no confidence intervals or subgroup
  analyses."
- *Equity & limitations (M-Q14, M-Q15)* — "No fairness assessment or mitigation
  strategies; no discussion of model limitations specific to generalizability or
  bias."

**Recommended-improvements example (real):** "Provide complete model card:
document model type and architecture, all hyperparameters and tuning rationale,
mathematical specification or reference implementation, input data requirements…"

**Side overlay (from the brief, confirmed by concept paper):** "Evaluated against
**TRIPOD+AI** — 26 weighted criteria" with the seven Medicine categories: Purpose
& Target Patients · Data Used · How the Model Was Built · Performance Results ·
Code & Model Access · Safe Use & Limits · Ethics & Registration.

---

## TODO 6 — Backend test count (S10)

`cd backend && uv run pytest` → **132 passed** (confirmed 2026-10-19, ~103 s,
Hypothesis + testcontainers). Matches the brief and concept paper. The S10 Panel B
chip should read "132 automated tests, property-based".

---

## TODO 7 — Team, members, faculties (S05, S08, S12)

- **Team name:** Kaelo
- **Members:**
  1. NOPPACHANIN KONGSATHITPORN
  2. PISUT MANORAT
  3. KRISANAKORN RUGBUMROONG
- **Faculty:** Faculty of Information and Communication Technology (ICT), Mahidol University

**Persona affiliations (per brief personas, aligned to the team's faculty):**
- S05 — พล (Pol): CS master's student, Faculty of ICT, Mahidol University.
- S08 — น้ำ (Nam): Medical resident & clinical researcher, Mahidol teaching
  hospital. *(The team is ICT; Nam is an illustrative Medicine-side persona. Keep
  the hospital generic unless the team wants to name Siriraj/Ramathibodi.)*

**End-card team line (S12):**
> Team Kaelo — Noppachanin Kongsathitporn · Pisut Manorat · Krisanakorn Rugbumroong
> Faculty of ICT, Mahidol University

---

## TODO 8 — Pilot / next-step line (S12, inferred from docs/concept-paper.pdf §4)

Drawn from the concept paper's near-term plan (validation study) and deployment
section (institutional dashboard, pre-submission checker):

> **Next:** a 100-paper-per-field validation study, then a pilot with ICT
> graduate students and a Mahidol clinical research unit — toward a
> pre-submission reproducibility checker and an institutional dashboard.

---

## TODOs 9 & 10 — out of scope for this pass

- **TODO 9 (music):** not provided; v1 renders without a music bed (no narration).
- **TODO 10 (rotate AWS key / exclude `.env`):** security cleanup, handled
  separately from the video.

---

## Consistency notes for the HyperFrames build

- CS standard string is the app's real label: **"ACM + ML Code Completeness +
  FAIR4RS"** (concept paper: 25 merged CS criteria). Medicine = **TRIPOD+AI, 26
  criteria**.
- Scoring formula (S10 Panel B): **S = 0.30·Quality + 0.70·Agreement** (confirmed
  in concept paper + live detail "Quality … · Agreement …").
- Ranking blend: **0.3·relevance + 0.7·reproducibility** (matches the live Overall
  arithmetic: 0.3·0.98 + 0.7·0.00 = 0.29).
- Guardrails still apply: generated code labelled unverified/never executed and
  never raises a paper's score; all S11 figures labelled estimates.
