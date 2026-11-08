# 2-minute live demo: the postgrad story

One story, four features. About 280 spoken words; don't improvise.

## Before you go on stage

1. `scripts/demo-record.sh` has been run **after** repo-link detection landed, and the Cassette is committed.
2. Run `scripts/demo-reset.sh` just before. Log in as `demo` / `demo-password-1`.
3. Clipboard: the query `Machine Learning Medical Image Segmentation Artificial Intelligence`. Note the writer reference `arxiv:2610.09450` and the PDF location `demo/Iris3B-demo.pdf` (kept local, gitignored).
4. Keep a screen recording as a fallback.

## Re-check after every re-record

Re-recording overwrites the LLM relevance scores, so the numbers below can move. Confirm:

- [ ] The survey "Medical image segmentation using deep learning: A survey" is #1 by Relevance and has a low or zero reproducibility score.
- [ ] MIScnn is #1 by Final score. Read its Final score off the card and say that number.
- [ ] MIScnn's detail page now shows a repository link and "Code available" met. If it still says "no inspectable repository", GitHub rate-limited the record run: set `GITHUB_TOKEN` in `.env` and record again.
- [ ] Both Reproducibility reviews (MIScnn and the Iris-3B manuscript) open and read sensibly.

## Agenda

| Time | On screen | Say |
| --- | --- | --- |
| **0:00–0:10** | Search page, Reader mode. Paste the query and search. | "I'm a postgrad in CS. Last month I lost two weeks on a paper whose results I couldn't reproduce. So I'm searching for medical image segmentation. Data in this demo is pre-recorded, so it's repeatable." |
| **0:10–0:35** F1 | Results sorted by Relevance. Point at the reproducibility bar on a card, then switch to **Final score**. | "Normal results, ranked by relevance. The top hit is a survey, and its reproducibility score is near zero: nothing to build on. Every card carries a rule-based reproducibility score; the AI never invents that number. Switch to Final score, which weights reproducibility, and MIScnn jumps to first." |
| **0:35–1:00** F2 | Open MIScnn. Show the repository link, then the score breakdown. | "Why? I can audit it. The score comes from a published standard: code and docs under 'Run the Code', dependencies and data under 'Reproduce the Results'. Each criterion shows its status and evidence. I don't have to trust a number, I can check it." |
| **1:00–1:20** F3 | Click **Reproducibility review**. | "One click gives me a review: gaps against the standard and specific fixes. It's far cheaper than generating a codebase, and it never runs code." Read one recommendation aloud. |
| **1:20–1:55** F4 | Switch to **Writer**. Claim `arxiv:2610.09450`, upload the PDF, generate the review. | "Now I'm the author. Before I submit my own paper, Iris-3B, I claim it, upload my manuscript and ask for the same review. It tells me what a reader will question about reproducibility before they do." |
| **1:55–2:00** | The report on screen. | "Search finds papers you can trust. Writing helps yours earn that trust. Thank you." |

## If time runs short

Cut F2 to 15 seconds. Don't cut F4: it is the part no other search tool has. If the review is slow to appear, keep talking through the claim and upload and let the poll finish.

## Facts to quote (from the docs)

- Rule-based scoring, LLM only explains it: ADR 0009.
- Final Score = 0.3 × relevance + 0.7 × reproducibility. `GLOSSARY.md` has these two weights backwards; don't quote it.
- The review is findings only, with no code and no score: code-generation requirement 12.
- A Writer's upload is stored on purpose: ADR 0003.
- This paper's domain is "unknown", so the Baseline standard applies, not TRIPOD+AI.

## Not live

Code generation for the Reader and Writer flows is not in the Cassette. Don't click Generate on stage: it would go live.
