# Paper data sources: OpenAlex and arXiv, scoped to CS and Medicine

We feed paper search from two external indexes — OpenAlex (broad, keyless REST
API with abstracts and open-access links) and arXiv (preprints, strong in CS) —
and scope coverage to the Computer Science and Medicine domains. We store only
index metadata and links, never full text (see product.md). Chosen over
single-source options because OpenAlex gives breadth and reproducible metadata
while arXiv adds timely CS preprints; Semantic Scholar was set aside to avoid an
API-key rate-limit dependency during the hackathon. Reconsidering later means
re-deriving the merged Paper schema and de-duplication logic, so it is recorded
here.
