"""Reproducibility-scoring business logic.

Rule-based scorers (``code_quality``, ``completeness``, ``reproducibility``) have
no LLM import — the number is deterministic. The LLM modules (``extractor``,
``explainer``) only produce the structured Experiment Setup and prose; they never
produce or alter a score.
"""
