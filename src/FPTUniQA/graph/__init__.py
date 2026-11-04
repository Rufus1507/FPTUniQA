"""Package Graph RAG cho hệ thống FPTUniQA: Quản lý và suy diễn tri thức quan hệ đồ thị học vụ."""

from FPTUniQA.graph.knowledge_graph import (
    AcademicKnowledgeGraph,
    get_knowledge_graph,
)

__all__ = ["AcademicKnowledgeGraph", "get_knowledge_graph"]
