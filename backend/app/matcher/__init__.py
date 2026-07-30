"""
Matching engine — hybrid job-resume matching.

This package implements the three-stage matching pipeline:

1. Rule-Based Scoring: Deterministic scoring based on
   skills, role, experience, location, keywords, etc.

2. Embedding Similarity: Semantic similarity between
   resume and job embeddings using cosine distance.

3. LLM Analysis: Deep analysis of match quality using
   structured Resume JSON and Job JSON (conditional,
   only for high-scoring matches).

The matching engine produces:
- Composite match score (0-100)
- Match explanation
- Missing skills analysis
- Apply recommendation
"""
