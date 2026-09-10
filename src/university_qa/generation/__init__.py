"""Module sinh câu trả lời (LLM Client, Prompt templates, Context Builder, Citation). Phụ trách: TV3."""

from university_qa.generation.citation import CitationExtractor
from university_qa.generation.context import ContextBuilder
from university_qa.generation.llm import LLMClient
from university_qa.generation.prompt import PromptManager

__all__ = ["LLMClient", "PromptManager", "ContextBuilder", "CitationExtractor"]
