"""
Prompt templates for LiteLLM service.

All prompts used across the service are centralized here for easy maintenance.
"""

SUMMARIZATION_PROMPT = """You are an expert research analyst. Analyze the following document and create a structured summary.

Document Title: {title}
Source: {source}
Content: {content}

Extract exactly 5 sections:
1. problem: What problem or research question is being addressed?
2. approach: What methods, techniques, or approach is being used?
3. evidence_or_signals: What key evidence, data, signals, or traction is mentioned?
4. result: What are the main outcomes, findings, or achievements?
5. limitations: What limitations, challenges, or open questions remain?

Keep each section concise (1-2 sentences max). Be specific and factual.

You MUST respond with ONLY a valid JSON object in this exact format:
{{
  "problem": "...",
  "approach": "...",
  "evidence_or_signals": "...",
  "result": "...",
  "limitations": "..."
}}
"""

