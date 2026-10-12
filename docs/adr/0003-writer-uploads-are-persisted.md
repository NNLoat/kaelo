# Writer uploads (manuscript + source) are persisted; Reader index stays link-only

The product's baseline rule is "store only index/links, never full text or code"
(product.md). We carve out one deliberate exception: for a **Writer**'s own
claimed paper, we persist the uploaded manuscript text (extracted server-side
from a PDF) and the uploaded source code. Rationale: a Writer owns and consents
to storing their own work, and the Writer reproducibility and code-generation
features need that material across sessions, not just in-request. The index-only
rule still governs everything on the Reader/search side (externally indexed
Papers reference OpenAlex/arXiv and repo links, never stored full text).

A future reader will expect the blanket index-only rule to apply everywhere, so
this exception — and its boundary (Writer-owned content only) — is recorded here.
Consequence: product.md must reflect that Writer-owned content is stored.
