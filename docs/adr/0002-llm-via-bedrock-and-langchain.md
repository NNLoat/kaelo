# LLM access via Amazon Bedrock through LangChain

All AI features (search query assist, reproducibility/code-quality scoring, code
generation) call Amazon Bedrock models through the LangChain abstraction, from
the backend. Bedrock was chosen as the primary provider; LangChain gives us a
provider-agnostic seam so a model swap does not ripple through feature code.
Credentials are supplied via environment config, never committed. This carries
AWS lock-in for inference and adds LangChain as a core dependency, so it is
recorded here.
