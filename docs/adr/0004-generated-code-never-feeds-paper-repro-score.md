# Generated code never feeds a Paper's Reproducibility Score

Code Generation produces candidate code we never execute or verify (see
`product.md`). We decided that the Artifact Code-Quality Score computed over a
generated or aligned artifact lives on the `Generation` record only and never
feeds back into the associated Paper's Reproducibility Score. The alternative —
letting generated code raise a Paper's repro score, since the glossary lists
Code-Quality Score as an input to Reproducibility Score — was rejected because it
would let unverified, machine-produced code inflate a Paper's standing in search
ranking, which is misleading. The glossary's "Code-Quality Score is an input to
Reproducibility Score" relationship therefore holds only for the *Repository*
Code-Quality Score (existing, real code), not the *Artifact* one.

## Consequences

- The `Generation` record carries its own Artifact Code-Quality Score,
  independent of any Paper score.
- A future reader will expect Code-Quality Score to always feed Reproducibility
  Score (per the glossary); this ADR records the deliberate carve-out so that
  expectation does not drive a "fix."
