# Scoring Rule: Standards-Conformance Score for Medical and Computer Science Papers

**Version:** 1.2 (October 17, 2026)
**Purpose:** Score a paper's reproducibility and usability by how closely it and its code/tool conform to recognized standards, instead of re-running the code. The score has two parts: code/tool quality (Q) and paper-to-code discrepancy (D). Medicine and CS are scored separately.

**Changes in v1.2**
- A plain-language **Category** column was added to each criteria table (7 categories per field) so non-expert users can see *which angle* a paper scores low on. Categories are for display only: they do not change any weight or the final score (Section 10).

**Changes in v1.1**
- One criteria table per field, each with a **Source reference(s)** column.
- Criteria that duplicated each other across references were **merged into one row that lists every reference sharing it** (CS: 30 criteria became 25; weights of merged rows are the sum of the originals). Medicine keeps its 26 criteria, with every reference that shares each one listed.
- FAIR4RS IDs were renamed `C-FAIR-*` to remove the clash with the ACM IDs.
- Group totals are unchanged: Q = 0.30, D and Q/D = 0.70 in each field.

---

## 1. Scoring scheme at a glance

| Item | Rule |
|---|---|
| Fields | **Medicine** (one scoring standard: TRIPOD+AI) and **CS** (three standards: ACM badges, ML Code Completeness Checklist, FAIR4RS). Each field has its own criteria table and its own final score. |
| Tags | **Q** = code/tool quality. **D** = paper-to-code discrepancy. **Q/D** = both; counted in the D group. |
| Group weights | All **Q** criteria sum to **0.30**. All **D** and **Q/D** criteria sum to **0.70**. This holds in each field. |
| Criterion score | 1 (fully met), 0.5 (partly met), 0 (not met or contradicted), or NA (not applicable). |
| Final score | `S = 0.30 × S_Q + 0.70 × S_D`, range 0 to 1. NA criteria are removed and weights are renormalized *within each group*, so the 0.30/0.70 split is preserved. |
| Consistency with references | Computed per reference (Section 7): conformance, coverage, full-compliance rate and contribution to `S`. |
| Display categories | Each criterion belongs to one plain-language category (Section 10), which gives a category score and the points it cost. Display only. |

Criterion weights are expert-assigned priors, not fitted values. Refit them against the validation sets in Section 8 before production use.

---

## 2. References: where the criteria come from

| ID | Reference | Version / date | Field | Scope | Size | Role in this rule |
|---|---|---|---|---|---|---|
| **R1** | Collins GS, Moons KGM, Dhiman P, et al. *TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods.* BMJ 2024;385:e078378. doi:10.1136/bmj-2023-078378 | April 2024; supersedes TRIPOD 2015, which its authors say should no longer be used | Medicine | Studies developing or evaluating (validating) diagnostic or prognostic prediction models, regression or ML | 27 main items, 52 sub-items; items tagged D (development), E (evaluation) or D;E (both) | Sole source of medical criteria |
| **R2** | กองควบคุมเครื่องมือแพทย์ สำนักงานคณะกรรมการอาหารและยา. *คู่มือระบบวินิจฉัยเครื่องมือแพทย์ ผ่านเว็บไซต์ Privus.fda.moph.go.th* (Thai FDA Medical Device Control Division, system manual for medical-device determination requests) | Updated 23 Aug 2566 (2023) | Medicine (alignment target) | A procedural manual for submitting a determination request: 13 form fields (§2.7) and 9 attachments (§4.1) | Not a technical standard | **Alignment only.** It supplies no criteria or weights. The Source column lists the Thai elements each R1 criterion shares (Section 3.2). |
| **R3** | ACM. *Artifact Review and Badging, Version 1.1.* acm.org/publications/policies/artifact-review-and-badging-current | v1.1 (2020). It swapped the "Reproduced" and "Replicated" definitions of v1.0 to match NISO terminology. | CS | Research artifacts of ACM publications | 3 badge families, 5 badges | CS criteria `C-A1` to `C-A8` |
| **R4** | Papers with Code. *ML Code Completeness Checklist* (releasing-research-code, github.com/paperswithcode/releasing-research-code) | 2020. NeurIPS 2020/2021 code submission guidance recommended it but did not require it. The Papers with Code service itself has been retired; the guidance persists in its GitHub repository. | CS (ML) | Repositories released with ML papers | 5 items | CS criteria `C-M1` to `C-M5` |
| **R5** | Chue Hong NP, et al. *FAIR Principles for Research Software (FAIR4RS Principles) v1.0.* RDA Recommendation, 2022. doi:10.15497/RDA00068. Also Barker M, et al. *Scientific Data* 2022;9:622. doi:10.1038/s41597-022-01710-x | v1.0 (2022) | CS | Research software | 17 principles: 4 foundational plus guiding sub-principles | CS criteria `C-FAIR-*`, plus the shared rows `C-A1` and `C-M1` |

Notes on the references:
- Some ACM conference pages still quote the v1.0 meaning of "Reproduced" and "Replicated". Check which version a source uses before scoring badges.
- FAIR4RS is aspirational by its authors' own description. Several principles (A2, F4, I1) are hard to verify from a repository alone, so they carry low weight and low confidence.
- TRIPOD+AI is a *reporting* guideline, not a quality appraisal tool (PROBAST+AI is the appraisal companion). The score therefore measures completeness and verifiability of reporting.

---

## 3. Medicine: criteria table (scoring reference R1, alignment reference R2)

**How to read the table**
- **Source reference(s)** lists every reference that shares the criterion: the TRIPOD+AI item (R1) and the Thai manual elements (R2) it aligns with. "R2: none" means the criterion has no Thai counterpart.
- **Overlap** gives the cluster code from Section 9 (MX = overlapping content, MT = criterion mapped to more than one Thai element). "-" means no flag.
- **App.** is TRIPOD+AI applicability: D = development studies, E = evaluation studies, D;E = both.
- **Evidence:** T = paper text/supplement, R = code repository, M = metadata (registry, DOI, etc.).
- **Category** is the plain-language group used for display (Section 10).
- Rows follow the order of the TRIPOD+AI checklist.

### 3.1 Criteria

| ID | Category | Criterion (paraphrased) | Tag | Weight | App. | Evidence | Source reference(s) | Overlap |
|---|---|---|---|---|---|---|---|---|
| M-Q2 | Purpose & Target Patients | Title identifies the model study, target population and outcome | Q | 0.010 | D;E | T | R1: item 1. R2: §2.7 (11) | MX1 |
| M-Q1 | Purpose & Target Patients | Target population and intended purpose in the care pathway, including intended users | Q | 0.050 | D;E | T | R1: item 3b. R2: §2.7 (10), §4.1 (4) | MX1, MT |
| M-Q3 | Purpose & Target Patients | Study objectives, including development and/or validation | Q | 0.010 | D;E | T | R1: item 4. R2: §2.7 (10) | MX1 |
| M-Q6 | Data Used | Data sources described separately for development and evaluation, with representativeness | Q | 0.020 | D;E | T | R1: item 5a. R2: §4.1 (2) | MX7 |
| M-Q4 | Purpose & Target Patients | Eligibility criteria for participants | Q | 0.020 | D;E | T | R1: item 6b. R2: §2.7 (11), §4.1 (4) | MT |
| M-D5 | Data Used | Data preprocessing and quality checking | D | 0.060 | D;E | T, R | R1: item 7. R2: §2.7 (9), §4.1 (2) | MX4, MT |
| M-Q5 | Purpose & Target Patients | Outcome and time horizon clearly defined, with rationale | Q | 0.020 | D;E | T | R1: item 8a. R2: §2.7 (11), §4.1 (4) | MT |
| M-Q7 | Data Used | All predictors defined, including how and when measured | Q | 0.020 | D;E | T | R1: item 9b. R2: §4.1 (2) | - |
| M-D3 | How the Model Was Built | How data were partitioned and used for development and evaluation | D | 0.080 | D | T, R | R1: item 12a. R2: §2.7 (9), §4.1 (1) | MX4, MT |
| M-D4 | How the Model Was Built | How predictors were handled (functional form, rescaling, transformation) | D | 0.040 | D | T, R | R1: item 12b. R2: §2.7 (9) | MX4 |
| M-D1 | How the Model Was Built | Model type, rationale, all model-building steps, hyperparameter tuning, internal validation method | D | 0.100 | D | T, R | R1: item 12c. R2: §2.7 (8), §4.1 (1) | MX4, MT |
| M-D6 | Performance Results | All performance measures and plots used and why (discrimination, calibration, clinical utility) | D | 0.070 | D;E | T, R | R1: item 12e. R2: §4.1 (3) | MX6 |
| M-Q10 | Code & Model Access | For evaluation: how model predictions were calculated (formula, code, object, API) | Q | 0.030 | E | T, R | R1: item 12g. R2: §4.1 (5) | MX3 |
| M-Q14 | Safe Use & Limits | Approaches to model fairness and their rationale | Q | 0.010 | D;E | T | R1: item 14. R2: §4.1 (6) | - |
| M-D2 | How the Model Was Built | Model output (probabilities/classes) and how classification thresholds were set | D | 0.050 | D | T, R | R1: item 15. R2: §2.7 (8) | - |
| M-D8 | Data Used | Differences between development and evaluation data in setting, eligibility, outcome, predictors | D | 0.030 | D;E | T | R1: item 16. R2: §4.1 (3) | MX7 |
| M-Q13 | Ethics & Registration | Ethics committee/IRB named; consent or waiver described | Q | 0.020 | D;E | T | R1: item 17. R2: §4.1 (6) | - |
| M-Q11 | Ethics & Registration | Where the study protocol can be accessed, or that none was prepared | Q | 0.020 | D;E | T, M | R1: item 18c. R2: §4.1 (6) | MX2 |
| M-Q12 | Ethics & Registration | Registration name and number, or statement of non-registration | Q | 0.020 | D;E | T, M | R1: item 18d. R2: §4.1 (6) | MX2 |
| M-D11 | Data Used | Availability of the study data | D | 0.040 | D;E | T, M | R1: item 18e. R2: none | - |
| M-D10 | Code & Model Access | Availability of the analytical code | D | 0.060 | D;E | T, R, M | R1: item 18f. R2: none | MX3 |
| M-D9 | Code & Model Access | Full model (formula, code, object, API) to allow third-party predictions, with access or reuse restrictions | D | 0.080 | D | T, R | R1: item 22. R2: §4.1 (5) | MX3 |
| M-D7 | Performance Results | Performance estimates with confidence intervals, including key subgroups | D | 0.090 | D;E | T, R | R1: item 23a. R2: §4.1 (3) | MX6 |
| M-Q15 | Safe Use & Limits | Limitations and their effect on bias and generalizability | Q | 0.010 | D;E | T | R1: item 26. R2: §4.1 (6) | - |
| M-Q8 | Safe Use & Limits | How poor-quality or unavailable input data are handled on implementation | Q | 0.020 | D | T | R1: item 27a. R2: §4.1 (5) | - |
| M-Q9 | Safe Use & Limits | Whether users must interact with input handling or the model, and the expertise needed | Q | 0.020 | D | T | R1: item 27b. R2: §4.1 (5) | - |
| | | **Q total (15 criteria)** | | **0.300** | | | | |
| | | **D total (11 criteria)** | | **0.700** | | | | |

**Applicability rules.**
- *Development-only study:* M-Q10 (E-only) is NA.
- *Evaluation-only study:* M-Q8, M-Q9 and the D-only items M-D1, M-D2, M-D3, M-D4, M-D9 are NA.
- *Development-and-evaluation study:* all 26 criteria apply.

**Coverage of the full standard.** These 26 criteria are a subset of TRIPOD+AI: 26 of its 52 sub-items, touching 18 of its 27 main items. Items not selected (e.g., 2, 3a, 3c, 5b, 6a, 6c, 8b, 8c, 9a, 9c, 10, 11, 13, 18a, 18b, 19, 20a to 20c, 21, 23b, 24, 25, 27c) are outside this rule. Section 7 includes an optional full-standard audit.

### 3.2 Alignment with the Thai manual (R2), by Thai element

R2 lists these *content* elements: form fields (8) to (13) in §2.7 and attachments (1) to (8) in §4.1. Fields (1) to (7) are administrative (place, email, phone, product name, owner, country, address), and attachment (9) is "other", so these are not mapped.

| Thai element (R2) | Meaning | Criteria sharing it (R1) |
|---|---|---|
| §2.7 (8) | General product description | M-D1, M-D2 |
| §2.7 (9) | Principle of operation / mechanism | M-D3, M-D4, M-D5 |
| §2.7 (10) | Intended use | M-Q1, M-Q3 |
| §2.7 (11) | Indications | M-Q2, M-Q4, M-Q5 |
| §2.7 (12) | Regulated as a medical device in the country of origin? | **None (gap)** |
| §2.7 (13) | Product type (finished, semi-finished, material, component, spare part, accessory) | **None (gap)** |
| §4.1 (1) | General description and principle of operation | M-D1, M-D3 |
| §4.1 (2) | Components / materials | M-Q6, M-Q7, M-D5 (partial: no software-library item in TRIPOD+AI) |
| §4.1 (3) | Product specification | M-D6, M-D7, M-D8 |
| §4.1 (4) | Intended use and indications | M-Q1, M-Q4, M-Q5 |
| §4.1 (5) | User manual / instructions for use | M-Q8, M-Q9, M-Q10, M-D9 |
| §4.1 (6) | Academic documents and clinical research | M-Q11, M-Q12, M-Q13, M-Q14, M-Q15 |
| §4.1 (7) | Label / package | **None (gap)** |
| §4.1 (8) | Registration documents in the country of origin | **None (gap)** |

- **Thai alignment coverage:** 10 of 14 content elements are mapped (71%). The four gaps are hardware and device-regulation items with no TRIPOD+AI counterpart. They are *not* scored; record them as zero-weight metadata flags (e.g., "regulatory status stated: yes/no") if wanted.
- **Thai-aligned weight share:** 24 of 26 criteria (weight 0.90) share at least one Thai element. M-D10 (18f, code) and M-D11 (18e, data) have no Thai counterpart. They are retained because paper-to-code consistency is a project requirement.
- R2 describes mandatory attachments with an asterisk, but the manual's own text refers to a double asterisk. Treat the list as informative only.

---

## 4. CS: criteria table (references R3, R4, R5)

**How to read the table**
- **Source reference(s)** lists *every* reference that shares the criterion, with the item or principle. Where two references ask the same thing, the criteria are **merged into one row** and both references are listed. Shared rows: `C-A1` (R3 and R5), `C-M1` (R4 and R5).
- **Previous IDs** shows the v1.0 IDs absorbed into a merged row.
- **Partial overlap with** lists other rows that test related but different things (not merged; see Section 9).
- **Category** is the plain-language group used for display (Section 10).
- Q/D criteria sit in the D group. Evidence codes as in Section 3.

### 4.1 Criteria

| ID | Category | Criterion (paraphrased) | Tag | Weight | Evidence | Source reference(s) | Partial overlap with | Previous IDs |
|---|---|---|---|---|---|---|---|---|
| C-A1 | Get the Code | Artifacts archived in a publicly accessible repository with a DOI or persistent identifier, retrievable by that identifier, with metadata that stay accessible if the software disappears | Q | 0.070 | M | **R3:** Artifacts Available. **R5:** F1, A1, A2 | - | C-A1, C-F1, C-A1P, C-A2P |
| C-A2 | Read the Docs | Documented: inventory of artifacts plus enough description to exercise them | Q | 0.020 | R | **R3:** Functional, Documented | C-FAIR-R1, C-A6 | - |
| C-A3 | Match the Paper | Consistent: artifacts are relevant to the paper and contribute to generating its main results | D | 0.070 | T, R | **R3:** Functional, Consistent | C-M2, C-M3, C-M5 | - |
| C-A4 | Match the Paper | Complete: all components relevant to the paper are included, or documented proxies for proprietary parts | D | 0.070 | T, R | **R3:** Functional, Complete | C-M2, C-M3, C-M4 | - |
| C-A5 | Run the Code | Exercisable: scripts/software that generate the paper's results run; included data can be accessed | Q/D | 0.100 | R, sandbox | **R3:** Functional, Exercisable | C-M2, C-M3, C-M5 | - |
| C-A6 | Read the Docs | Reusable: quality significantly exceeds minimal functionality (carefully documented, well structured for reuse) | Q | 0.030 | R | **R3:** Reusable | C-A2, C-FAIR-R1 | - |
| C-A7 | Independent Check | Results Reproduced: an independent team validated the results, in part with the authors' artifacts | D | 0.050 | M | **R3:** Results Reproduced | - | - |
| C-A8 | Independent Check | Results Replicated: an independent team validated the results without the authors' artifacts | D | 0.050 | M | **R3:** Results Replicated | - | - |
| C-M1 | Install & Set Up | Dependencies specified (requirements/environment file, install instructions), with pinned versions | Q | 0.060 | R | **R4:** item 1, Specification of dependencies. **R5:** R2 | C-A4 | C-M1, C-R2 |
| C-M2 | Run the Code | Training code that can obtain the paper's principal results, including hyperparameters | D | 0.100 | T, R | **R4:** item 2, Training code | C-A3, C-A4, C-A5 | - |
| C-M3 | Run the Code | Evaluation code that computes the reported metrics under the paper's protocol | D | 0.080 | T, R | **R4:** item 3, Evaluation code | C-A3, C-A4, C-A5 | - |
| C-M4 | Get the Code | Pre-trained models hosted or linked | Q | 0.030 | R, M | **R4:** item 4, Pre-trained models | C-A4 | - |
| C-M5 | Match the Paper | README with a results table and precise commands that produce those results | D | 0.080 | T, R | **R4:** item 5, README results table with commands | C-A3, C-A5 | - |
| C-FAIR-F1.1 | Find, Cite & License | Components at different granularity get distinct identifiers (NA if monolithic) | Q | 0.005 | M | **R5:** F1.1 | - | C-F1.1 |
| C-FAIR-F1.2 | Match the Paper | The version of the code used in the paper is identifiable and linked to the paper (distinct version identifiers; detailed provenance) | D | 0.100 | T, R, M | **R5:** F1.2, R1.2 | - | C-F1.2, C-R1.2 |
| C-FAIR-F2 | Find, Cite & License | Software described with rich metadata (CITATION.cff, codemeta.json) | Q | 0.010 | M | **R5:** F2 | C-FAIR-F3, C-FAIR-F4 | C-F2 |
| C-FAIR-F3 | Find, Cite & License | Metadata explicitly include the software's identifier | Q | 0.005 | M | **R5:** F3 | C-FAIR-F2, C-FAIR-F4 | C-F3 |
| C-FAIR-F4 | Find, Cite & License | Metadata are FAIR, searchable and indexable | Q | 0.005 | M | **R5:** F4 | C-FAIR-F2, C-FAIR-F3 | C-F4 |
| C-FAIR-A1.1 | Get the Code | Retrieval protocol is open, free and universally implementable | Q | 0.005 | M | **R5:** A1.1 | - | C-A1.1 |
| C-FAIR-A1.2 | Get the Code | Authentication/authorization where necessary (NA if public) | Q | 0.005 | M | **R5:** A1.2 | - | C-A1.2 |
| C-FAIR-I1 | Install & Set Up | Reads/writes data in domain-community standard formats | Q | 0.005 | R | **R5:** I1 | - | C-I1 |
| C-FAIR-I2 | Install & Set Up | Qualified references to other objects (datasets, resources) | Q | 0.005 | R, T | **R5:** I2 | - | C-I2 |
| C-FAIR-R1 | Read the Docs | Described with accurate, relevant attributes (README completeness) | Q | 0.015 | R | **R5:** R1 | C-A2, C-A6 | C-R1 |
| C-FAIR-R1.1 | Find, Cite & License | Clear, accessible license | Q | 0.020 | R | **R5:** R1.1 | - | C-R1.1 |
| C-FAIR-R3 | Find, Cite & License | Meets domain-relevant community standards | Q | 0.010 | R | **R5:** R3 | - | C-R3 |
| | | **Q total (16 criteria)** | | **0.300** | | | | |
| | | **D and Q/D total (9 criteria)** | | **0.700** | | | | |

### 4.2 Weight check by reference

A merged row counts toward every reference that shares it, so the reference columns add up to more than 1.

| Reference | Criteria where it participates | Participating weight | Of which shared with another reference |
|---|---|---|---|
| R3 ACM badges | C-A1 to C-A8 | 0.460 | 0.070 (C-A1, with R5) |
| R4 ML Code Completeness | C-M1 to C-M5 | 0.350 | 0.060 (C-M1, with R5) |
| R5 FAIR4RS | C-A1, C-M1 and all 12 C-FAIR criteria in the table (C-FAIR-F1.1 to C-FAIR-R3) | 0.320 | 0.130 (C-A1 and C-M1) |
| **Field total (each criterion counted once)** | 25 criteria | **1.000** | Q = 0.300, D and Q/D = 0.700 |

Medicine weight check: Q = 0.300 (15 criteria), D = 0.700 (11 criteria), total 1.000, all scored against R1.

---

## 5. Criterion scoring rules

### 5.1 Scale

| Score | Meaning |
|---|---|
| **1** | Fully met, with evidence (a location, file path, URL or identifier) that can be shown. |
| **0.5** | Partly met, or reported but not verifiable. |
| **0** | Not reported or not present, or **contradicted** (paper and code disagree). |
| **NA** | Not applicable under the rules in Sections 3.1, 5.3 and 5.4. NA is never a default for missing evidence. |

### 5.2 D-group rule (paper-to-code discrepancy)

For every D and Q/D criterion, compare what the paper states with what the code or artifact contains:
- **1** = the paper-stated value or protocol is found in the code, config or outputs and matches (e.g., hyperparameters, data splits, seeds, metric definitions, reported numbers), or the artifact is independently verified.
- **0.5** = reported in the paper, but the code is unavailable, the value cannot be found in the code, or only partly matches. A value reachable by configuration (the code supports the paper's setting through a config file or flag) counts as **supported**, not as a discrepancy: score 1 if the config or command for the paper's setting is shipped, 0.5 if it is not.
- **0** = not reported, absent from the repository for an applicable paper, or **contradicted** (list it in the discrepancy report).

### 5.3 CS-specific rules

- **No code released for an empirical or computational paper:** score all CS criteria 0 (including C-A1). This is a real observation, not a missing one.
- **Non-computational paper (e.g., pure theory):** no CS score; mark "not assessable".
- **Merged row C-A1:** 1 = deposit in an archival repository (e.g., Zenodo) with a resolving DOI or persistent identifier; 0.5 = a persistent link that is not archival (e.g., a plain GitHub URL); 0 = none.
- **Merged row C-M1:** 1 = dependency file with pinned versions (or a lockfile) plus install instructions; 0.5 = dependencies listed without versions, or versions without install instructions; 0 = none.
- **Merged row C-FAIR-F1.2:** 1 = a tag, release or commit hash is cited in the paper (or clearly matches the paper's date) and the repository links back to the paper; 0.5 = only one of the two; 0 = neither.
- **Badge shortcuts:** an ACM "Available" badge awarded by an independent evaluation sets C-A1 = 1. A "Functional" badge sets C-A2, C-A3, C-A4, C-A5 = 1. A "Reusable" badge also sets C-A6 = 1.
- **Without a badge or a successful sandbox run,** C-A5 (Exercisable) is capped at 0.5.
- **C-A7 and C-A8 (Results Reproduced/Replicated):** require a later independent study. If no such evidence exists, mark **NA**, not 0, so that almost all papers are not penalized for lacking one.
- **C-FAIR-F1.1** is NA for single-component software. **C-FAIR-A1.2** is NA for publicly accessible software. **C-FAIR-F2 to C-FAIR-F4** may share evidence from one metadata check.

### 5.4 Medicine-specific rules

- **No code repository:** M-D9 and M-D10 = 0. M-Q10 (12g) = 0.5 at most when predictions are described in text but no code is available. Other D items that need code to verify cap at 0.5, because the text cannot be checked against code.
- **Restricted data (M-D11):** a documented, restricted access procedure scores 0.5 ("restricted but documented"). Open data with a persistent link scores 1.
- **Study types TRIPOD+AI does not cover** (RCTs, non-prediction studies): not assessable under this rule.

### 5.5 Confidence

Each criterion gets an extraction confidence `c_i` in [0, 1] from extractor agreement (e.g., agreement across several LLM judge samples) or rule specificity.
- Confidence-adjusted score: `ŝ_i = c_i · s_i + (1 − c_i) · π_i`, where `π_i` is the base rate of that criterion in the paper's field/venue/year cohort. Use `π_i = 0.5` when no cohort data exist.
- Never use an author's self-reported checklist tick as evidence. It is a pointer to where to look.
- A "not detected" result from a high-specificity, moderate-sensitivity text tool should receive low `c_i`.

---

## 6. Computing the final score

Apply separately for each field. Let `W_i` be the base weight (Sections 3.1 and 4.1).

1. **Select the field and applicable criteria.** Medicine uses M-* criteria (only for prediction-model studies). CS uses C-* criteria (only for computational papers). A paper in both fields (e.g., a medical ML paper with a public repository) receives both scores, reported separately.
2. **Set NA** using Sections 3.1, 5.3 and 5.4. Let `A_Q` and `A_D` be the applicable Q criteria and the applicable D/Q-D criteria.
3. **Extract evidence** and assign `s_i` and `c_i`; compute `ŝ_i` (Section 5.5).
4. **Group scores, renormalized within each group:**

   ```
   S_Q = Σ_{i ∈ A_Q} W_i · ŝ_i  /  Σ_{i ∈ A_Q} W_i
   S_D = Σ_{i ∈ A_D} W_i · ŝ_i  /  Σ_{i ∈ A_D} W_i
   ```

5. **Final score:**

   ```
   S = 0.30 · S_Q + 0.70 · S_D
   ```

   If a whole group is NA, set `S` to the other group's score and flag it (e.g., "D not assessable").
6. **Effective weights** (used in Section 7): `w̃_i = 0.30 · W_i / Σ_{A_Q} W` for Q criteria and `w̃_i = 0.70 · W_i / Σ_{A_D} W` for D and Q/D criteria. Then `S = Σ_i w̃_i · ŝ_i`.
7. **Report:** `S`, `S_Q`, `S_D`, overall confidence `κ = Σ w̃_i c_i`, the list of NA criteria, any contradictions, the per-reference consistency in Section 7, and the category view in Section 10.

### Worked example (CS paper with partial NA)

A paper has code and an ACM "Available" badge but no independent reproduction. C-A7 and C-A8 are NA. Suppose the remaining applicable D criteria total weight 0.600 with weighted mean score 0.50, and Q criteria total 0.300 with weighted mean 0.70.

- `S_Q = 0.70`, `S_D = 0.50`.
- `S = 0.30 × 0.70 + 0.70 × 0.50 = 0.21 + 0.35 = 0.56`.

Because NA weights were removed from the D group only, the 0.30/0.70 split is unchanged.

---

## 7. Measuring consistency with each reference

For each reference `r` (R1 for medicine; R3, R4, R5 for CS), let `I_r` be its applicable criteria, taken from the **Source reference(s)** column. A merged CS row belongs to every reference listed for it (`C-A1` is in both `I_R3` and `I_R5`; `C-M1` is in both `I_R4` and `I_R5`). Compute:

| Metric | Formula | Meaning |
|---|---|---|
| **Conformance** `C_r` | `Σ_{I_r} W_i ŝ_i / Σ_{I_r} W_i` | How closely the paper/code follows reference `r`, using the base weights |
| **Q-side / D-side conformance** `C_r^Q`, `C_r^D` | Same, restricted to Q or D criteria | Shows whether the gap is in code/tool quality or in paper-to-code agreement |
| **Score-consistent conformance** `C'_r` | `Σ_{I_r} w̃_i ŝ_i / Σ_{I_r} w̃_i` | Conformance under the 0.30/0.70 balance actually used in `S` |
| **Contribution** `Δ_r` | `Σ_{I_r} w̃_i ŝ_i / n_i`, where `n_i` is the number of references listing criterion `i` | Points of the final score contributed by `r`. A shared criterion's points are split equally among its references, so the `Δ_r` across references add up to `S`. |
| **Coverage** `Cov_r` | `Σ_{I_r} W_i c_i / Σ_{I_r} W_i` | Share of the reference that could be assessed with reasonable confidence |
| **Full-compliance rate** `F_r` | `#{i ∈ I_r : s_i = 1} / |I_r|` | Fraction of applicable criteria fully met (unweighted) |

**Consistency label per reference:**

| Label | Rule |
|---|---|
| High | `C'_r ≥ 0.85` and `Cov_r ≥ 0.80` |
| Moderate | `0.60 ≤ C'_r < 0.85` and `Cov_r ≥ 0.50` |
| Low | `C'_r < 0.60` and `Cov_r ≥ 0.50` |
| Not assessable | `Cov_r < 0.50` |

These thresholds are starting points; calibrate them on the validation sample in Section 8.

**Additional checks:**

- **Discrepancy report.** List every D criterion scored 0 because of a contradiction, with the paper-stated value, the code value, and the reference criterion (e.g., "R1 12c: paper learning rate 3e-4; config 1e-3").
- **Medicine, standard coverage.** The rule covers 26 of 52 TRIPOD+AI sub-items (18 of 27 main items). Optionally audit the remaining sub-items and compute `A_full` = full-standard adherence. Check on a validation sample that `S` correlates with `A_full` (rank correlation), so that the subset is representative.
- **Medicine, Thai alignment.**
  - *Static:* 10 of 14 Thai content elements mapped (71%); Thai-aligned weight share 0.90.
  - *Per paper:* for each mapped Thai element `e`, compute `E_e` = weighted mean of `ŝ_i` over the criteria that list `e` in their Source column (Section 3.2). Report the mean `E_e` over the 10 mapped elements, and list the four unmapped elements as "not covered" rather than scoring them. Criteria that list several Thai elements (flag MT) enter several `E_e`.
- **CS, per-reference balance.** Report `C_r` for R3, R4 and R5 side by side. A large spread (e.g., high FAIR4RS but low ML Code Completeness) shows the repository is well archived but not complete for the paper's results.
- **CS, remaining overlap.** The unmerged overlaps (clusters CX3, CX5, CX6 in Section 9) are intentional: a gap then shows up in more than one criterion. Do not merge them without refitting the weights.

---

## 8. Validation, limitations and version control

**Validation plan**
1. Annotate about 100 papers per field by two independent human raters; target agreement (Cohen's κ) of at least 0.6 per criterion. Require the automated judge to match human-human agreement before running at full weight.
2. Compare `S`, `S_Q`, `S_D` and the per-reference `C_r` with external signals: ACM Results badges, independent replication reports, and (for medicine) full-standard adherence `A_full`.
3. Check discrimination: `S_D` should relate more strongly to independent reproduction than `S_Q`; `S_Q` should relate to ease of reuse.
4. Test adversarially: add boilerplate README sections, empty config files and placeholder tests, and confirm `S` does not rise.
5. Refit the criterion weights, keeping the group totals at 0.30 and 0.70.

**Limitations**
- Conformance with a reporting standard is a proxy for reproducibility, not proof of it.
- TRIPOD+AI covers prediction-model studies only. RCTs, systematic reviews and device hardware studies need other standards.
- Text tools for open data/code have high specificity but only moderate sensitivity, so absence of detection is uncertain evidence. LLM judges can overestimate adherence and can be manipulated, so keep human spot checks.
- Release rates, link rot and empty "coming soon" repositories change over time; re-crawl periodically and record the commit scored.
- Weights are priors. The Thai manual (R2) is used for alignment only, and its regulatory elements (origin-country status, label, product type) are outside this score.

**Version control.** Record the version of each reference with every score (TRIPOD+AI 2024; ACM v1.1; ML Code Completeness 2020; FAIR4RS v1.0) and the version of this rule (1.2). For papers published before a reference existed, note this and consider scoring only the criteria that were achievable at that time. Review the item bank at least annually, and re-check for updates to TRIPOD+AI (e.g., generative-AI extensions such as TRIPOD-LLM) and ACM badging.

---

## 9. Duplicate and overlapping criteria flags

**Literal ID check:** each field's IDs are unique (Medicine: 26 IDs, 26 unique; CS: 25 IDs, 25 unique). The flags below are about **duplicated or overlapping content**: different criteria that test the same thing, so one weakness is counted more than once.

**Flag types**
- **Duplicate:** two or more criteria ask essentially the same thing.
- **Shared evidence:** different questions answered by the same piece of evidence (one gap lowers several scores).
- **Multi-mapped:** one criterion maps to several Thai elements (Medicine only), so it counts more than once in the Thai-alignment average `E_e`.

**Handling rule.** Duplicates across references were merged in v1.1 (see 9.2). Remaining flagged criteria stay separate: extract the evidence once, reuse the same evidence record for every ID in a cluster (so judgments agree), and review the weights of high-share clusters during refitting. Clusters with a combined weight of 0.15 or more are marked **High**.

### 9.1 Medicine (reference R1)

| Cluster | Type | Criteria IDs | Why they overlap | Combined weight | Risk |
|---|---|---|---|---|---|
| **MX1** | Shared evidence | M-Q1 (3b), M-Q2 (1), M-Q3 (4) | Intended purpose, title and objectives all restate the same population, outcome and study type | 0.070 | Low |
| **MX2** | Shared evidence | M-Q11 (18c), M-Q12 (18d) | Protocol access and registration are usually evidenced by the same registry entry | 0.040 | Low |
| **MX3** | **Duplicate** (code/model access) | M-Q10 (12g), M-D9 (22), M-D10 (18f) | All check whether the model/analysis code is available. In a development-and-evaluation study 12g and 22 both apply. TRIPOD+AI separates analytical code (18f) from code that implements the model (22), but a repository check covers both. Tags differ (Q and D), so they are not merged without changing the 0.30/0.70 totals. | 0.170 | **High** |
| **MX4** | **Duplicate** (model-building description) | M-D1 (12c), M-D3 (12a), M-D4 (12b), M-D5 (7) | Model-building steps, data partitioning, predictor handling and preprocessing describe one pipeline. The closest pair is M-D4 (rescaling/transformation) and M-D5 (preprocessing). | 0.280 | **High** |
| **MX6** | Shared evidence | M-D6 (12e), M-D7 (23a) | Measures chosen and estimates reported for those measures; one results table and the same evaluation output serve both | 0.160 | **High** |
| **MX7** | Shared evidence (weak) | M-Q6 (5a), M-D8 (16) | Data sources and development-vs-evaluation differences are read from the same data description | 0.050 | Low |
| **MT** | Multi-mapped to Thai elements | M-Q1 (§2.7 (10), §4.1 (4)), M-Q4 (§2.7 (11), §4.1 (4)), M-Q5 (§2.7 (11), §4.1 (4)), M-D1 (§2.7 (8), §4.1 (1)), M-D3 (§2.7 (9), §4.1 (1)), M-D5 (§2.7 (9), §4.1 (2)) | The same criterion feeds two Thai elements, so its score enters the Thai-alignment average twice | n/a (does not change `S`) | Low |

Medicine has a single scoring reference (R1), so no criterion could be merged across references. Its overlaps are between different TRIPOD+AI items and remain separate rows; the Source column lists R1 and every Thai element each criterion shares. No other medicine criterion is flagged.

### 9.2 CS (references R3, R4, R5)

**Resolved in v1.1 by merging** (the merged row lists all sharing references in the Source column):

| Former cluster | Former IDs | Merged into | Shared by | Combined weight |
|---|---|---|---|---|
| CX1 availability/persistence | C-A1, C-F1, C-A1P, C-A2P | **C-A1** | R3 (Artifacts Available), R5 (F1, A1, A2) | 0.070 |
| CX2 dependencies | C-M1, C-R2 | **C-M1** | R4 (item 1), R5 (R2) | 0.060 |
| CX4 version/provenance | C-F1.2, C-R1.2 | **C-FAIR-F1.2** | R5 (F1.2, R1.2) | 0.100 |
| CN1 ID naming clash | C-A1.1, C-A1.2, C-A2P (FAIR) vs C-A1, C-A2 (ACM) | FAIR rows renamed `C-FAIR-*` | n/a | n/a |

**Still open (partial overlap, kept separate):**

| Cluster | Type | Criteria IDs | Why they overlap | Combined weight | Risk |
|---|---|---|---|---|---|
| **CX3** | **Duplicate** (code produces the paper's results) | C-A3 (Consistent), C-A4 (Complete), C-A5 (Exercisable), C-M2 (training code), C-M3 (evaluation code), C-M5 (README results and commands) | Each asks, from a different angle, whether the released code can generate the paper's reported results. A missing training script or a broken run lowers all of them. They come from different references (R3 and R4) and test different things, so they were not merged. | **0.500** | **High (half the CS score)** |
| **CX5** | Shared evidence (documentation) | C-A2 (Documented), C-A6 (Reusable), C-FAIR-R1 (README attributes) | One README review informs all three | 0.065 | Low |
| **CX6** | Shared evidence (metadata) | C-FAIR-F2, C-FAIR-F3, C-FAIR-F4 | One metadata record (CITATION.cff, DOI landing page, index entry) answers all three | 0.020 | Low |

Notes:
- CX3 interacts with the 0.30/0.70 split: all six criteria are D or Q/D, so a single missing result-generating script can remove up to 0.50 of the final CS score. Consider capping the combined cluster weight, or merging the six into fewer criteria, when refitting weights.
- C-A5 is the only Q/D criterion; it belongs to cluster CX3 and sits in the D group.
- No criterion in one field duplicates a criterion in the other field.

---

## 10. Display categories (plain-language view)

### 10.1 Purpose and rules

- Categories answer one question for a non-expert reader: **"From which angle did this paper lose points?"**
- Every criterion belongs to **exactly one** category (the **Category** column in Sections 3.1 and 4.1). Categories mix Q and D criteria.
- Categories are **display only**. They do not change any criterion weight, the 0.30/0.70 split, or the final score `S`.
- Each field has seven categories. Medicine and CS use different names because they ask different questions.

### 10.2 Medicine categories

| Category | What it asks (plain language) | Criteria IDs | Q weight | D weight | Total | A low score means... |
|---|---|---|---|---|---|---|
| **Purpose & Target Patients** | What is the tool for, which patients, and what does it predict? | M-Q1, M-Q2, M-Q3, M-Q4, M-Q5 | 0.110 | 0.000 | 0.110 | It is unclear what the tool is for, which patients it applies to, or what outcome it predicts. |
| **Data Used** | Is the data described, prepared in a stated way, and obtainable? | M-Q6, M-Q7, M-D5, M-D8, M-D11 | 0.040 | 0.130 | 0.170 | The data behind the model is poorly described or not obtainable, or the preprocessing is unclear. |
| **How the Model Was Built** | Can someone repeat the build, and check it against the code? | M-D1, M-D2, M-D3, M-D4 | 0.000 | 0.270 | 0.270 | The build steps (settings, data splits, output rules) are not fully reported, so the work cannot be repeated or checked against the code. |
| **Performance Results** | Are the results reported fully and honestly? | M-D6, M-D7 | 0.000 | 0.160 | 0.160 | Results are incomplete (missing measures, uncertainty ranges or subgroup results), so claims cannot be checked. |
| **Code & Model Access** | Can others get the code and the finished model? | M-Q10, M-D9, M-D10 | 0.030 | 0.140 | 0.170 | The code or the finished model cannot be obtained, so others cannot run or test it. |
| **Safe Use & Limits** | Is there guidance for real use, and are fairness and limits stated? | M-Q8, M-Q9, M-Q14, M-Q15 | 0.060 | 0.000 | 0.060 | Guidance for real use is thin: unclear handling of missing inputs, who operates it, fairness, and limitations. |
| **Ethics & Registration** | Was it approved, and is the protocol or registration stated? | M-Q11, M-Q12, M-Q13 | 0.060 | 0.000 | 0.060 | No clear ethics approval, protocol or registration is stated. |
| | **Total (26 criteria)** | | **0.300** | **0.700** | **1.000** | |

### 10.3 CS categories

| Category | What it asks (plain language) | Criteria IDs | Q weight | D weight | Total | A low score means... |
|---|---|---|---|---|---|---|
| **Get the Code** | Can I get the code and trained models, and will they stay available? | C-A1, C-M4, C-FAIR-A1.1, C-FAIR-A1.2 | 0.110 | 0.000 | 0.110 | The code, trained models or an archived copy are hard to get, or may disappear. |
| **Install & Set Up** | Can I set it up on my machine? | C-M1, C-FAIR-I1, C-FAIR-I2 | 0.070 | 0.000 | 0.070 | Setup is hard: dependencies are missing or not version-pinned, or inputs and formats are unclear. |
| **Run the Code** | Does the code actually run and produce results? | C-A5, C-M2, C-M3 | 0.000 | 0.280 | 0.280 | The code does not run, or the training or evaluation scripts are missing. |
| **Match the Paper** | Does the released code match what the paper reports? | C-A3, C-A4, C-M5, C-FAIR-F1.2 | 0.000 | 0.320 | 0.320 | The code does not clearly match the paper: parts are missing, settings or numbers differ, or the version used is unknown. |
| **Read the Docs** | Is it explained well enough to use? | C-A2, C-A6, C-FAIR-R1 | 0.065 | 0.000 | 0.065 | Documentation is thin or unclear (README, usage instructions, structure). |
| **Independent Check** | Has someone else confirmed the results? | C-A7, C-A8 | 0.000 | 0.100 | 0.100 | An independent reproduction was only partly successful or disagreed with the paper. If no independent check exists, the category shows **Not yet checked** (NA), not a low score. |
| **Find, Cite & License** | Can I find it, cite it, and legally reuse it? | C-FAIR-F1.1, C-FAIR-F2, C-FAIR-F3, C-FAIR-F4, C-FAIR-R1.1, C-FAIR-R3 | 0.055 | 0.000 | 0.055 | It is hard to find, cite or legally reuse: no license, citation file or searchable metadata. |
| | **Total (25 criteria)** | | **0.300** | **0.700** | **1.000** | |

### 10.4 Computing and showing category results

For each category `k`, using the criterion scores `ŝ_i` and effective weights `w̃_i` from Section 6 (NA criteria excluded):

| Metric | Formula | Use |
|---|---|---|
| **Category score** `S_k` | `Σ_{i ∈ k} W_i · ŝ_i / Σ_{i ∈ k} W_i` | Shown as a percentage (0 to 100%). |
| **Points lost** `L_k` | `Σ_{i ∈ k} w̃_i · (1 − ŝ_i)` | How much of the final score this category cost. The `L_k` across categories add up to `1 − S`. |
| **Share of loss** | `L_k / (1 − S)` (undefined if `S = 1`) | Tells the reader where most of the lost points came from. |

**Level labels for `S_k`**

| Label | Rule |
|---|---|
| Strong | `S_k ≥ 0.85` |
| Fair | `0.60 ≤ S_k < 0.85` |
| Weak | `S_k < 0.60` |
| Not assessed | Every criterion in the category is NA, or the category confidence (`Σ W_i c_i / Σ W_i`) is below 0.50 |

**Display guideline**
1. Show the seven category names with `S_k` and its label. Order them by points lost, largest first, so the weakest angle is on top.
2. Under each Weak or Fair category, show the **"A low score means..."** sentence from Section 10.2 or 10.3.
3. Add up to two drill-down lines: the criteria in that category with the largest `w̃_i (1 − ŝ_i)`, using the criterion text from the table and, for D criteria, the paper-stated value versus the code value if a contradiction was found.
4. Headline sentence: "Biggest loss: *<category>* (<share>% of lost points)."
5. Because categories can hold different criterion counts and weights, compare papers on `S_k` and share of loss, not on raw counts.

**Example (CS).** A paper scores `S = 0.56`, so `1 − S = 0.44`. The "Match the Paper" category cost 0.19 points: headline "Biggest loss: Match the Paper (43% of lost points)". The reader sees that the released code does not clearly match the paper, and the drill-down lines name the criteria that lost the most points, such as a hyperparameter in the paper that does not match the config.
