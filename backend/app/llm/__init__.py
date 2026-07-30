"""
LLM integration layer — provider-independent AI interface.

This package implements the LLM abstraction layer:

- LLMProvider interface (ABC)
- Provider implementations (OpenRouter, OpenAI-compatible, Ollama)
- Fallback chain (automatic failover between providers)
- Response caching (keyed by job_hash + task_type + resume_version)
- Prompt templates for each task type

Supported LLM tasks:
- Match explanation
- Job summarization
- Missing skills analysis
- Cover letter generation
- Recruiter message generation
- Interview preparation
- Company summary
- Resume improvement suggestions

The LLM layer NEVER receives raw PDF data.
It always works with structured JSON representations.
"""
