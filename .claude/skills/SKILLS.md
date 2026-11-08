# Vendored skills

These skills are **vendored** (copied into the repo) rather than installed by a
package manager, so a clone gets the identical version with no per-machine
install. Each entry records the exact upstream commit it was copied from; treat
this file as the lockfile and update it whenever you re-vendor.

Compare against the pinned upstream copies with:

```bash
./scripts/update-skills.sh
```

## Pinned sources

| Skill | Source | Commit (pinned) | Date vendored |
| --- | --- | --- | --- |
| `frontend-design` | https://github.com/anthropics/claude-code · `plugins/frontend-design/skills/frontend-design/SKILL.md` | `3deb873687379f0c199a69fdaccc65f0865f7a29` | 2026-10-12 |
| `grilling` | https://github.com/mattpocock/skills · `skills/productivity/grilling/SKILL.md` | `49dd158d1076134a641b33efb035946536778336` | 2026-10-12 |
| `domain-modeling` | https://github.com/mattpocock/skills · `skills/engineering/domain-modeling/` | `49dd158d1076134a641b33efb035946536778336` | 2026-10-12 |
| `grill-with-docs` | https://github.com/mattpocock/skills · `skills/engineering/grill-with-docs/` | `49dd158d1076134a641b33efb035946536778336` | 2026-10-12 |

`spec` is project-authored (it replaces Kiro's built-in `/spec`) and has no
upstream. `ponytail` is **not** vendored: install the plugin
(`/plugin install ponytail@ponytail`) to get it along with its `/ponytail-*`
commands.

## Local edits

- Frontmatter `metadata:` blocks (source URL, SHA) were removed; that info lives
  in the table above.
- `grill-with-docs` is project-maintained: it dispatches to `grilling` and
  `domain-modeling` via the Skill tool and is manual-only.
- `domain-modeling` reference files live under `domain-modeling/references/`.

## HyperFrames and Playwright skills (npx-managed, not committed)

The HyperFrames skill set (`hyperframes`, `hyperframes-*`, `embedded-captions`,
`faceless-explainer`, `figma`, `general-video`, `media-use`, `motion-graphics`,
`music-to-video`, `pr-to-video`, `product-launch-video`, `remotion-to-hyperframes`,
`slideshow`, `talking-head-recut`) is managed by the **`npx skills`** tool. The
content lives under `.agents/skills/` (gitignored) and is surfaced into
`.claude/skills/` as gitignored symlinks. Only the lockfile `skills-lock.json`
(repo root) is committed.

After cloning, materialize them once (select Claude Code as the agent):

```bash
npx skills add heygen-com/hyperframes
```

Re-run to update; commit the changed `skills-lock.json`.
