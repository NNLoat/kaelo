---
name: grill-with-docs
description: >
  A relentless interview to sharpen a plan or design that also captures docs
  (ADRs and a glossary) as you go. Invoke manually with /grill-with-docs when
  starting a feature or stress-testing a design.
disable-model-invocation: true
---

# Grill with docs

Run two companion skills together for this session by invoking each with the
Skill tool:

1. **grilling**: interview the user relentlessly, in rounds, until you reach a
   shared understanding of the plan or design.
2. **domain-modeling**: as terms and decisions crystallise during the grilling,
   capture them: sharpen vocabulary into `GLOSSARY.md` and record hard-to-reverse
   trade-offs as ADRs under `docs/adr/`.

Apply both at once: grill to surface the decisions, and write the glossary/ADR
entries inline the moment each decision is settled. Do not act on the plan until
the user confirms you have reached shared understanding (the grilling frontier is
empty).
