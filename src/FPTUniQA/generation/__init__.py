"""Module sinh câu trả lời (LLM Client, Prompt templates, Context Builder, Citation). Phụ trách: TV3."""

from FPTUniQA.generation.citation import extract_citations
from FPTUniQA.generation.context import format_context
from FPTUniQA.generation.llm import LLMClient
from FPTUniQA.generation.prompt import SYSTEM_PROMPT, build_prompt

__all__ = [
    "LLMClient",
    "SYSTEM_PROMPT",
    "build_prompt",
    "format_context",
    "extract_citations",
]
