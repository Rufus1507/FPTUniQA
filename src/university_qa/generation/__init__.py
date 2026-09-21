"""Module sinh câu trả lời (LLM Client, Prompt templates, Context Builder, Citation). Phụ trách: TV3."""

from university_qa.generation.citation import extract_citations
from university_qa.generation.context import format_context
from university_qa.generation.llm import LLMClient
from university_qa.generation.prompt import SYSTEM_PROMPT, build_prompt

__all__ = [
    "LLMClient",
    "SYSTEM_PROMPT",
    "build_prompt",
    "format_context",
    "extract_citations",
]
