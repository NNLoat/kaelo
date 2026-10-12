# Vendored skills

These skills are **vendored** (copied into the repo) rather than installed by a
package manager, so every teammate gets the identical version by cloning — no
per-machine install, and it works the same in Kiro IDE and Kiro CLI.

Each entry records where the skill came from and the exact upstream commit it was
copied from. Treat this file as the lockfile: update it whenever you re-vendor.

Re-fetch everything at the pinned commits with:

```bash
./scripts/update-skills.sh
```

## Pinned sources

| Skill | Source | Commit (pinned) | Date vendored |
| --- | --- | --- | --- |
| `ponytail` | https://github.com/DietrichGebert/ponytail · `skills/ponytail/SKILL.md` | `9b58c1ffb790c075ca32e70a89cf1d80588f4abf` | 2026-10-12 |
| `frontend-design` | https://github.com/anthropics/claude-code · `plugins/frontend-design/skills/frontend-design/SKILL.md` | `3deb873687379f0c199a69fdaccc65f0865f7a29` | 2026-10-12 |
| `grilling` | https://github.com/mattpocock/skills · `skills/productivity/grilling/SKILL.md` | `49dd158d1076134a641b33efb035946536778336` | 2026-10-12 |
| `domain-modeling` | https://github.com/mattpocock/skills · `skills/engineering/domain-modeling/` | `49dd158d1076134a641b33efb035946536778336` | 2026-10-12 |
| `grill-with-docs` | https://github.com/mattpocock/skills · `skills/engineering/grill-with-docs/` | `49dd158d1076134a641b33efb035946536778336` | 2026-10-12 |

## Notes on porting

These were authored as Claude Code skills. Changes made when vendoring into Kiro:

- **Frontmatter** trimmed to Kiro's supported fields (`name`, `description`,
  optional `license`/`metadata`). Claude-only keys (`argument-hint`,
  `disable-model-invocation`) were dropped — Kiro has no equivalent. Each `name`
  matches its folder and is lowercase/hyphenated per Kiro's rules.
- **`grill-with-docs`** was a dispatcher that told Claude to "call the Skill tool
  twice". Kiro has no such tool call, so it was rewritten to reference its two
  companion skills (`grilling`, `domain-modeling`) by path. All three are
  vendored so the dispatcher resolves.
- **`domain-modeling`** reference files (`ADR-FORMAT.md`, `GLOSSARY-FORMAT.md`)
  live under `domain-modeling/references/` and are linked relatively, per Kiro's
  progressive-disclosure convention.
- **`ponytail`**: Kiro is an instruction-only adapter for ponytail. The always-on
  ruleset (this skill) works, but ponytail's slash commands (`/ponytail-review`,
  `/ponytail-audit`, etc.) are **not** available in Kiro — only the core skill was
  vendored.
- Harness-specific files from the sources (e.g. `agents/openai.yaml`) were not
  vendored; they are irrelevant to Kiro.
