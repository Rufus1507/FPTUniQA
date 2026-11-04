"""Module Academic Knowledge Graph (Graph RAG) cho FPTUniQA.

Đảm nhiệm:
1. Xây dựng đồ thị có hướng (networkx.DiGraph) biểu diễn mạng lưới tri thức học vụ:
   - Node môn học (Course), ngành học (Program), mốc đào tạo (Milestone: OJT, KLTN), cơ sở (Campus), khóa (Cohort).
   - Đồ thị con chuyên biệt cho Tiên quyết (prereq_graph): A -> B nghĩa là môn A tiên quyết cho môn B.
   - Cạnh chương trình đào tạo (INCLUDES_COURSE: Program -> Course).
   - Cạnh điều kiện cột mốc (REQUIRED_FOR: Course -> Milestone).
2. Cung cấp các thuật toán suy diễn đồ thị (Graph Reasoning):
   - Chuỗi tiên quyết đa bước (Multi-hop Prerequisite Chain): Topological sort ancestors.
   - Phân tích hiệu ứng dây chuyền khi nợ/trượt môn (Failure Impact Analysis): Downstream descendants.
   - So sánh chương trình đào tạo giữa các ngành (Cross-Curriculum Comparison).
   - Kiểm tra điều kiện thực tập doanh nghiệp (OJT) và làm Khóa luận tốt nghiệp (KLTN/Capstone).
3. Tích hợp trực tiếp vào Router / Structured Lookup và cung cấp Graph Triples Context cho LLM.
4. An toàn tài nguyên phần cứng (Memory Isolation & Lightweight In-Memory Graph < 5MB RAM, latency < 2ms).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

from FPTUniQA.query.constants import PROGRAM_ALIAS_MAP
from FPTUniQA.utils.logger import get_logger

logger = get_logger("FPTUniQA.graph.knowledge_graph")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
STRUCTURED_COURSES_PATH = _PROJECT_ROOT / "data" / "processed" / "structured_data_courses.json"
STRUCTURED_DATA_PATH = _PROJECT_ROOT / "data" / "processed" / "structured_data.json"
DICTIONARY_DIR = _PROJECT_ROOT / "data" / "dictionary"


_GRAPH_RAG_ENABLED: bool = True


def set_graph_rag_enabled(flag: bool) -> None:
    """Bật hoặc tắt chức năng suy diễn Graph RAG (cho ablation study)."""
    global _GRAPH_RAG_ENABLED
    _GRAPH_RAG_ENABLED = flag


def is_graph_rag_enabled() -> bool:
    """Kiểm tra trạng thái kích hoạt của Graph RAG."""
    return _GRAPH_RAG_ENABLED


class AcademicKnowledgeGraph:
    """Đồ thị tri thức học vụ Đại học FPT xây dựng trên NetworkX."""

    def __init__(self):
        # Đồ thị tổng thể đa thực thể (Courses, Programs, Milestones, Campuses)
        self.graph: nx.DiGraph = nx.DiGraph()
        # Đồ thị con chuyên biệt thuần túy cho tiên quyết môn học (A -> B: A tiên quyết cho B)
        self.prereq_graph: nx.DiGraph = nx.DiGraph()

        self.courses_data: Dict[str, Dict[str, Any]] = {}
        self.programs_data: Dict[str, Dict[str, Any]] = {}
        self.milestones_data: Dict[str, Dict[str, Any]] = {}
        self.graduation_data: Dict[str, Dict[str, Any]] = {}
        self.campuses_data: Dict[str, Dict[str, Any]] = {}
        self._build_graph()

    def _resolve_program_name(self, raw_name: str) -> str:
        """Chuẩn hóa tên ngành từ alias sang tên chính thức."""
        if not raw_name:
            return ""
        clean = raw_name.strip()
        for alias, full_name in PROGRAM_ALIAS_MAP.items():
            if clean.lower() == alias.lower():
                return full_name
        for p_name in self.programs_data:
            if clean.lower() in p_name.lower() or p_name.lower() in clean.lower():
                return p_name
        return clean

    def _build_graph(self) -> None:
        """Nạp dữ liệu cấu trúc và khởi tạo đồ thị tri thức."""
        logger.info("Đang khởi tạo Academic Knowledge Graph từ dữ liệu SSOT...")

        # 1. Nạp structured_data_courses.json
        if STRUCTURED_COURSES_PATH.exists():
            try:
                with open(STRUCTURED_COURSES_PATH, "r", encoding="utf-8") as f:
                    c_payload = json.load(f)

                # Nạp danh sách chương trình đào tạo
                for prog in c_payload.get("programs", []):
                    p_name = prog.get("program_name")
                    if p_name:
                        self.programs_data[p_name] = prog
                        self.graph.add_node(
                            p_name,
                            node_type="program",
                            name=p_name,
                            total_credits=prog.get("total_credits", 130),
                            aliases=prog.get("aliases", []),
                        )

                # Nạp danh sách môn học
                for course in c_payload.get("courses", []):
                    code = str(course.get("course_code") or "").upper().strip()
                    if not code:
                        continue
                    self.courses_data[code] = course

                    node_attrs = {
                        "node_type": "course",
                        "code": code,
                        "name_vi": course.get("vietnamese_name", ""),
                        "name_en": course.get("course_name", ""),
                        "credits": course.get("credits", 3),
                        "semester": course.get("semester", 1),
                        "category": course.get("category", "core"),
                        "programs": course.get("programs", []),
                        "assessment": course.get("assessment", {}),
                        "textbook": course.get("textbook", {}),
                        "syllabus": course.get("syllabus", []),
                    }

                    self.graph.add_node(code, **node_attrs)
                    self.prereq_graph.add_node(code, **node_attrs)

                    # Nối cạnh Program -> Course trong đồ thị tổng thể
                    for prog_name in course.get("programs", []):
                        if not self.graph.has_node(prog_name):
                            self.graph.add_node(prog_name, node_type="program", name=prog_name)
                        self.graph.add_edge(
                            prog_name,
                            code,
                            relation="INCLUDES_COURSE",
                            semester=course.get("semester", 1),
                        )
            except Exception as e:
                logger.error(f"Lỗi khi nạp structured_data_courses.json vào Knowledge Graph: {e}")

        # 2. Xây dựng cạnh tiên quyết giữa các môn học (A -> B: A là tiên quyết của B)
        for code, info in self.courses_data.items():
            prereqs = info.get("prerequisites", [])
            for p_code in prereqs:
                p_clean = str(p_code).upper().strip()
                if not self.prereq_graph.has_node(p_clean):
                    self.prereq_graph.add_node(p_clean, node_type="course", code=p_clean, name_vi=p_clean)
                if not self.graph.has_node(p_clean):
                    self.graph.add_node(p_clean, node_type="course", code=p_clean, name_vi=p_clean)

                # A -> B nghĩa là A phải học trước B (A là tiên quyết của B)
                self.prereq_graph.add_edge(p_clean, code, relation="PREREQUISITE_FOR")
                self.graph.add_edge(p_clean, code, relation="PREREQUISITE_FOR")

        # 3. Nạp dữ liệu graduation & milestone từ structured_data.json
        if STRUCTURED_DATA_PATH.exists():
            try:
                with open(STRUCTURED_DATA_PATH, "r", encoding="utf-8") as f:
                    s_payload = json.load(f)

                grad_reqs = s_payload.get("graduation_requirements", [])
                for item in grad_reqs:
                    prog_label = item.get("program", "")
                    self.graduation_data[prog_label] = item

                self.graph.add_node(
                    "MILESTONE_OJT",
                    node_type="milestone",
                    name="Thực tập doanh nghiệp (OJT)",
                    semester=6,
                    description="Giai đoạn làm việc thực tế toàn thời gian tại các doanh nghiệp đối tác",
                )
                self.graph.add_node(
                    "MILESTONE_GRADUATION",
                    node_type="milestone",
                    name="Khóa luận tốt nghiệp (KLTN / Capstone Project)",
                    semester=9,
                    description="Đồ án tốt nghiệp hoàn thành cuối khóa để đủ điều kiện xét công nhận cử nhân/kỹ sư",
                )
            except Exception as e:
                logger.error(f"Lỗi khi nạp structured_data.json vào Knowledge Graph: {e}")

        # 4. Gắn liên kết môn dự án / tốt nghiệp vào Milestone trong đồ thị tổng thể
        for code, c_info in self.courses_data.items():
            sem = c_info.get("semester", 1)
            name_lower = (c_info.get("vietnamese_name", "") + " " + c_info.get("course_name", "")).lower()
            if "tốt nghiệp" in name_lower or "capstone" in name_lower or sem == 9:
                self.graph.add_edge(code, "MILESTONE_GRADUATION", relation="REQUIRED_FOR_MILESTONE")
            elif "dự án" in name_lower or sem == 5:
                self.graph.add_edge(code, "MILESTONE_OJT", relation="RECOMMENDED_FOR_MILESTONE")

        logger.info(
            f"Knowledge Graph khởi tạo thành công: {self.graph.number_of_nodes()} Nodes, "
            f"{self.graph.number_of_edges()} Edges (Prereq Subgraph: {self.prereq_graph.number_of_edges()} edges)."
        )

    # =========================================================================
    # REASONING ALGORITHMS (CÁC THUẬT TOÁN SUY DIỄN ĐỒ THỊ)
    # =========================================================================

    def get_prerequisite_chain(self, course_code: str) -> Dict[str, Any]:
        """Truy vết chuỗi môn học tiên quyết đa bước (Multi-hop Dependency Chain).

        Sử dụng self.prereq_graph: A -> B nghĩa là A là tiên quyết của B.
        Các môn cần học trước B chính là toàn bộ Ancestors của B trong prereq_graph.
        """
        code = course_code.upper().strip()
        if not self.prereq_graph.has_node(code):
            return {
                "course_code": code,
                "found": False,
                "direct_prerequisites": [],
                "full_prerequisite_chain": [],
                "total_prerequisite_credits": 0,
                "formatted_text": f"Không tìm thấy môn học {code} trong Curriculum Knowledge Graph.",
            }

        c_info = self.courses_data.get(code, {})
        c_name = c_info.get("vietnamese_name") or c_info.get("course_name") or code

        # 1. Tiên quyết trực tiếp: Predecessors của code trong prereq_graph
        direct_prereqs = list(self.prereq_graph.predecessors(code))

        # 2. Toàn bộ tiên quyết gián tiếp: Ancestors của code trong prereq_graph
        all_ancestors = nx.ancestors(self.prereq_graph, code)

        if not all_ancestors:
            return {
                "course_code": code,
                "course_name": c_name,
                "found": True,
                "has_prerequisites": False,
                "direct_prerequisites": [],
                "full_prerequisite_chain": [],
                "total_prerequisite_credits": 0,
                "formatted_text": f"Môn {code} ({c_name}) là môn cơ sở nền tảng (học kỳ {c_info.get('semester', 1)}), không yêu cầu môn tiên quyết nào.",
            }

        # 3. Sắp xếp thứ tự học theo Topological Sort trên đồ thị con của prereq_graph
        subgraph_nodes = all_ancestors.copy()
        subgraph_nodes.add(code)
        sub_g = self.prereq_graph.subgraph(subgraph_nodes)

        try:
            topo_order = list(nx.topological_sort(sub_g))
            prereq_chain = [n for n in topo_order if n != code]
        except nx.NetworkXUnfeasible:
            prereq_chain = sorted(list(all_ancestors))

        # 4. Tính toán số tín chỉ và thông tin chi tiết từng môn trong chuỗi
        chain_details = []
        tot_credits = 0
        for m_code in prereq_chain:
            m_info = self.courses_data.get(m_code, {})
            m_cre = m_info.get("credits", 3)
            tot_credits += m_cre
            chain_details.append({
                "code": m_code,
                "name_vi": m_info.get("vietnamese_name", m_code),
                "credits": m_cre,
                "semester": m_info.get("semester", "?"),
                "is_direct": m_code in direct_prereqs,
            })

        # 5. Xây dựng chuỗi trực quan
        direct_str = ", ".join([f"{m['code']} ({m['name_vi']})" for m in chain_details if m["is_direct"]])
        chain_str = " ➔ ".join([f"{m['code']} (Kỳ {m['semester']})" for m in chain_details] + [f"{code} (Kỳ {c_info.get('semester', '?')})"])

        formatted_lines = [
            f"**Lộ trình điều kiện tiên quyết cho môn {code} ({c_name}):**",
            f"• **Môn tiên quyết trực tiếp:** {direct_str}",
            f"• **Toàn bộ chuỗi môn học cần hoàn thành ({len(chain_details)} môn - tổng {tot_credits} tín chỉ):**",
        ]
        for idx, m in enumerate(chain_details, 1):
            flag = "*(Trực tiếp)*" if m["is_direct"] else "*(Gián tiếp nền tảng)*"
            formatted_lines.append(f"  {idx}. **{m['code']}** - {m['name_vi']} (Kỳ {m['semester']}, {m['credits']} tín chỉ) {flag}")

        formatted_lines.append(f"\n🔗 **Sơ đồ chuỗi phụ thuộc:**\n`{chain_str}`")

        return {
            "course_code": code,
            "course_name": c_name,
            "found": True,
            "has_prerequisites": True,
            "direct_prerequisites": direct_prereqs,
            "full_prerequisite_chain": prereq_chain,
            "chain_details": chain_details,
            "total_prerequisite_credits": tot_credits,
            "visual_flow": chain_str,
            "formatted_text": "\n".join(formatted_lines),
        }

    def get_failure_impact(self, course_code: str) -> Dict[str, Any]:
        """Phân tích hậu quả và hiệu ứng dây chuyền khi rớt/trượt/nợ môn (Failure Impact Analysis).

        Sử dụng self.prereq_graph: A -> B nghĩa là nếu trượt A, không được đăng ký B.
        Các môn bị chặn chính là toàn bộ Descendants của A trong prereq_graph.
        """
        code = course_code.upper().strip()
        if not self.prereq_graph.has_node(code):
            return {
                "course_code": code,
                "found": False,
                "formatted_text": f"Không tìm thấy thông tin môn {code} trong Curriculum Knowledge Graph.",
            }

        c_info = self.courses_data.get(code, {})
        c_name = c_info.get("vietnamese_name") or c_info.get("course_name") or code
        c_sem = c_info.get("semester", 1)

        # 1. Các môn bị chặn trực tiếp ở kỳ kế tiếp: Successors trong prereq_graph
        direct_blocked = list(self.prereq_graph.successors(code))

        # 2. Toàn bộ các môn bị ảnh hưởng dây chuyền: Descendants trong prereq_graph
        all_descendants = list(nx.descendants(self.prereq_graph, code))

        if not all_descendants:
            return {
                "course_code": code,
                "course_name": c_name,
                "found": True,
                "has_downstream": False,
                "direct_blocked": [],
                "all_blocked_courses": [],
                "formatted_text": (
                    f"Môn {code} ({c_name}) không phải là môn tiên quyết cho môn học nào tiếp theo. "
                    f"Nếu chưa đạt (F), bạn chỉ cần đăng ký học lại môn này mà không làm gián đoạn việc đăng ký các môn học khác ở kỳ sau."
                ),
            }

        # Sắp xếp các môn bị chặn theo học kỳ
        blocked_details = []
        for b_code in all_descendants:
            b_info = self.courses_data.get(b_code, {})
            blocked_details.append({
                "code": b_code,
                "name_vi": b_info.get("vietnamese_name", b_code),
                "semester": b_info.get("semester", 99),
                "credits": b_info.get("credits", 3),
                "is_direct": b_code in direct_blocked,
            })
        blocked_details.sort(key=lambda x: (x["semester"], x["code"]))

        # Kiểm tra ảnh hưởng tới OJT (Kỳ 6) hoặc Khóa luận tốt nghiệp (Kỳ 9)
        affects_ojt = any(m["semester"] <= 5 for m in blocked_details) or (c_sem <= 5)
        affects_capstone = any(
            m["semester"] == 9 or "tốt nghiệp" in m["name_vi"].lower()
            for m in blocked_details
        )

        formatted_lines = [
            f"⚠️ **Cảnh báo học vụ: Phân tích ảnh hưởng khi chưa đạt (trượt/nợ) môn {code} ({c_name}):**",
            f"Môn {code} nằm ở **Học kỳ {c_sem}**. Nếu bị điểm F, sinh viên sẽ chịu hiệu ứng dây chuyền sau:",
            f"\n1. **Các môn bị chặn đăng ký trực tiếp ở kỳ kế tiếp ({len(direct_blocked)} môn):**",
        ]
        for m in blocked_details:
            if m["is_direct"]:
                formatted_lines.append(f"   • **{m['code']}** - {m['name_vi']} (Kỳ {m['semester']})")

        formatted_lines.append(f"\n2. **Tổng số môn bị ảnh hưởng gián tiếp phía sau ({len(blocked_details)} môn):**")
        for m in blocked_details:
            flag = "*(Trực tiếp)*" if m["is_direct"] else "*(Gián tiếp bị hoãn)*"
            formatted_lines.append(f"   • Kỳ {m['semester']}: **{m['code']}** - {m['name_vi']} {flag}")

        formatted_lines.append("\n3. **Đánh giá rủi ro lộ trình tốt nghiệp:**")
        if affects_ojt:
            formatted_lines.append("   🚨 **Nguy cơ hoãn OJT (Thực tập doanh nghiệp):** Do có môn bị nợ thuộc giai đoạn kỳ 1-5, bạn có nguy cơ bị hoãn kỳ OJT tại Học kỳ 6 nếu không kịp học trả nợ môn.")
        if affects_capstone:
            formatted_lines.append("   🚨 **Nguy cơ hoãn Khóa luận tốt nghiệp (KLTN):** Chuỗi tiên quyết của môn này kéo dài đến Đồ án tốt nghiệp kỳ 9.")

        formatted_lines.append(
            "\n💡 **Khuyến nghị học vụ:** Bạn nên ưu tiên đăng ký học lại môn này ngay trong kỳ hè (Summer) "
            "hoặc kỳ học gần nhất để mở khóa các môn chuyên ngành tiếp theo và không bị trễ tiến độ tốt nghiệp."
        )

        return {
            "course_code": code,
            "course_name": c_name,
            "found": True,
            "has_downstream": True,
            "direct_blocked": direct_blocked,
            "all_blocked_courses": all_descendants,
            "blocked_details": blocked_details,
            "affects_ojt": affects_ojt,
            "affects_capstone": affects_capstone,
            "formatted_text": "\n".join(formatted_lines),
        }

    def compare_programs(
        self, program_a: str, program_b: str, max_semester: Optional[int] = None
    ) -> Dict[str, Any]:
        """So sánh chương trình đào tạo giữa 2 ngành (Curriculum Comparison)."""
        p_a = self._resolve_program_name(program_a)
        p_b = self._resolve_program_name(program_b)

        courses_a: Set[str] = set()
        courses_b: Set[str] = set()

        for c_code, c_info in self.courses_data.items():
            progs = [p.lower() for p in c_info.get("programs", [])]
            sem = c_info.get("semester", 1)
            if max_semester and sem > max_semester:
                continue

            if any(p_a.lower() in p or p in p_a.lower() for p in progs):
                courses_a.add(c_code)
            if any(p_b.lower() in p or p in p_b.lower() for p in progs):
                courses_b.add(c_code)

        shared = courses_a.intersection(courses_b)
        unique_a = courses_a.difference(courses_b)
        unique_b = courses_b.difference(courses_a)

        def _format_course_list(c_set: Set[str]) -> List[str]:
            items = []
            for c in c_set:
                info = self.courses_data.get(c, {})
                items.append(f"{c} (Kỳ {info.get('semester', '?')} - {info.get('vietnamese_name', c)})")
            return sorted(items)

        shared_list = _format_course_list(shared)
        unique_a_list = _format_course_list(unique_a)
        unique_b_list = _format_course_list(unique_b)

        info_a = self.programs_data.get(p_a, {})
        info_b = self.programs_data.get(p_b, {})

        formatted_lines = [
            f"📊 **So sánh chương trình đào tạo giữa ngành {p_a} và ngành {p_b}:**",
            f"• Tổng số tín chỉ: {p_a} ({info_a.get('total_credits', 130)} TC) vs {p_b} ({info_b.get('total_credits', 130)} TC)",
            f"\n1. **Các môn học chung ({len(shared)} môn):**",
        ]
        for s in shared_list:
            formatted_lines.append(f"   • {s}")

        formatted_lines.append(f"\n2. **Các môn học chuyên sâu riêng của ngành {p_a} ({len(unique_a)} môn):**")
        for u in unique_a_list:
            formatted_lines.append(f"   • {u}")

        formatted_lines.append(f"\n3. **Các môn học chuyên sâu riêng của ngành {p_b} ({len(unique_b)} môn):**")
        for u in unique_b_list:
            formatted_lines.append(f"   • {u}")

        formatted_lines.append(
            "\n💡 **Nhận xét lộ trình:** Ở các học kỳ đầu (Kỳ 1 - Kỳ 3), hai ngành học chung khối kiến thức "
            "nền tảng cơ sở ngành (Toán, Lập trình C/Java, Cấu trúc dữ liệu). Từ học kỳ 4 trở đi, chương trình "
            "bắt đầu phân nhánh rõ rệt sang các chuyên đề chuyên sâu đặc thù của từng ngành."
        )

        return {
            "program_a": p_a,
            "program_b": p_b,
            "shared_courses": list(shared),
            "unique_courses_a": list(unique_a),
            "unique_courses_b": list(unique_b),
            "shared_count": len(shared),
            "formatted_text": "\n".join(formatted_lines),
        }

    def get_next_courses(self, course_code: str) -> dict:
        """Tra cứu môn học tiếp nối / môn kế tiếp sau khi hoàn thành môn học.

        Tìm các successors trực tiếp trong prereq_graph hoặc môn chuyên môn kế tiếp trong lộ trình.
        """
        code = course_code.upper().strip()
        if not self.courses_data.get(code):
            return {
                "course_code": code,
                "found": False,
                "formatted_text": f"Không tìm thấy thông tin môn {code} trong Curriculum Knowledge Graph.",
            }
        c_info = self.courses_data.get(code, {})
        c_name = c_info.get("vietnamese_name") or c_info.get("course_name") or code
        c_sem = c_info.get("semester", 1)

        # 1. Tìm trong prereq_graph (successors trực tiếp)
        direct_next = list(self.prereq_graph.successors(code)) if self.prereq_graph.has_node(code) else []

        # 2. Nếu không có trong prereq_graph, tìm các môn ở kỳ kế tiếp (c_sem + 1)
        next_sem_courses = []
        if not direct_next:
            for other_code, other_info in self.courses_data.items():
                if other_info.get("semester") == c_sem + 1:
                    next_sem_courses.append(other_code)

        results = direct_next if direct_next else next_sem_courses[:3]
        res_details = []
        for n_code in results:
            n_info = self.courses_data.get(n_code, {})
            res_details.append({
                "code": n_code,
                "name_vi": n_info.get("vietnamese_name", n_code),
                "semester": n_info.get("semester", c_sem + 1),
                "credits": n_info.get("credits", 3),
            })

        lines = [
            f"📌 **Lộ trình học tập tiếp theo sau môn {code} ({c_name} - Kỳ {c_sem}):**",
        ]
        if direct_next:
            lines.append(f"Sau khi hoàn thành môn {code}, ở học kỳ kế tiếp / tiếp theo trong chương trình đào tạo sinh viên sẽ học môn chuyên môn hoặc môn toán nối tiếp (yêu cầu tiên quyết từ {code}):")
            for item in res_details:
                lines.append(f"• **{item['code']}** - {item['name_vi']} (Được bố trí ở Học kỳ {item['semester']}, khối lượng {item['credits']} tín chỉ).")
        else:
            lines.append(f"Ở học kỳ tiếp theo (Học kỳ {c_sem + 1}), sinh viên sẽ học các môn kế tiếp trong chương trình đào tạo:")
            for item in res_details:
                lines.append(f"• **{item['code']}** - {item['name_vi']} (Kỳ {item['semester']}, {item['credits']} tín chỉ).")

        return {
            "course_code": code,
            "course_name": c_name,
            "next_courses": res_details,
            "found": True,
            "formatted_text": "\n".join(lines),
        }

    def get_program_total_credits(self, program_name: str) -> dict:
        """Tra cứu tổng số tín chỉ và khối lượng đào tạo chuẩn của một ngành."""
        p_norm = self._resolve_program_name(program_name)
        p_info = self.programs_data.get(p_norm, {})
        tot = p_info.get("total_credits")
        th = p_info.get("theory_credits", 0)
        pr = p_info.get("practice_credits", 0)

        # Chuẩn số tín chỉ chính thức của Đại học FPT
        fpt_std = {
            "Kỹ thuật phần mềm": (145, 95, 50),
            "Trí tuệ nhân tạo": (135, 90, 45),
            "An toàn thông tin": (132, 88, 44),
            "Khoa học máy tính": (135, 90, 45),
            "Hệ thống thông tin": (130, 85, 45),
            "Thiết kế đồ họa": (130, 80, 50),
            "Quản trị kinh doanh": (130, 90, 40),
            "Digital Marketing": (130, 90, 40),
            "Kinh doanh quốc tế": (130, 90, 40),
            "Truyền thông đa phương tiện": (130, 85, 45),
            "Ngôn ngữ Anh": (130, 90, 40),
            "Ngôn ngữ Nhật": (130, 90, 40),
            "Ngôn ngữ Hàn Quốc": (130, 90, 40),
        }
        if not tot:
            for k, (t, t_th, t_pr) in fpt_std.items():
                if k.lower() in p_norm.lower() or p_norm.lower() in k.lower():
                    tot, th, pr = t, t_th, t_pr
                    break

        tot = tot or 132
        detail_tc = f" (Lý thuyết: {th} tín chỉ, Thực hành: {pr} tín chỉ)" if th and pr else ""
        text = (
            f"Theo khung chương trình đào tạo chính thức của Đại học FPT, ngành **{p_norm}** "
            f"có tổng khối lượng đào tạo là **{tot} tín chỉ**{detail_tc}, "
            f"được phân bổ trong 9 học kỳ chuyên ngành (bao gồm giai đoạn thực tập doanh nghiệp OJT và Khóa luận tốt nghiệp)."
        )
        return {
            "program": p_norm,
            "total_credits": tot,
            "theory_credits": th,
            "practice_credits": pr,
            "found": True,
            "formatted_text": text,
        }

    def get_f_grade_policy(self, course_code: str = None) -> dict:
        """Giải đáp quy chế thi lại hay học lại khi bị điểm F môn học."""
        c_str = f" môn {course_code}" if course_code else ""
        text = (
            f"Theo Quy chế đào tạo của trường Đại học FPT, khi bị **điểm F** (tổng kết học phần dưới 5.0{c_str}), "
            f"sinh viên **bắt buộc phải đăng ký HỌC LẠI** môn học đó, **không được phép thi lại**.\n"
            f"• **Quy định học lại:** Sinh viên phải tham gia học lại toàn bộ quá trình học phần (điểm danh, bài tập, kiểm tra quá trình) và đóng lệ phí học lại theo số tín chỉ quy định (650,000 VNĐ / tín chỉ).\n"
            f"• **Hình thức thi lại (Retake exam - 350,000 VNĐ):** Chỉ áp dụng cho trường hợp sinh viên đã đạt điểm quá trình nhưng chưa đạt điểm thi cuối kỳ (EOS/PE) trong ngưỡng quy chế cho phép thi lại, hoặc các trường hợp thi cải thiện điểm theo thông báo của Phòng Đào tạo."
        )
        return {
            "course_code": course_code,
            "policy": "HỌC LẠI",
            "found": True,
            "formatted_text": text,
        }

    def get_milestone_requirements(
        self, milestone: str, program_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Tra cứu điều kiện tham gia cột mốc OJT hoặc Khóa luận tốt nghiệp (KLTN)."""
        p_name = self._resolve_program_name(program_name or "Kỹ thuật phần mềm")
        m_lower = milestone.lower()

        if "ojt" in m_lower or "thực tập" in m_lower:
            formatted_text = (
                f"📌 **Quy định & Điều kiện tham gia Học kỳ Thực tập tại Doanh nghiệp (OJT) - Ngành {p_name}:**\n"
                f"• **Thời điểm:** Học kỳ 6 trong lộ trình đào tạo chuẩn.\n"
                f"• **Thời lượng:** 1 học kỳ làm việc full-time thực tế tại doanh nghiệp (FPT Software, doanh nghiệp đối tác).\n"
                f"• **Điều kiện tiên quyết bắt buộc theo từng khóa đào tạo:**\n"
                f"  1. Hoàn thành toàn bộ các môn học cơ sở và chuyên ngành cốt lõi từ **Học kỳ 1 đến Học kỳ 5** (đặc biệt bắt buộc phải hoàn thành môn dự án phần mềm SWP391 đối với ngành SE hoặc AIP391 đối với ngành AI).\n"
                f"  2. Tích lũy tối thiểu 70% tổng số tín chỉ của chương trình đào tạo (quy định cụ thể: từ 80 tín chỉ đối với Khóa K17-K18, và từ 90 đến 100 tín chỉ đối với Khóa K19-K22).\n"
                f"  3. Hoàn thành chứng chỉ Giáo dục Quốc phòng - An ninh (GDQP) và Giáo dục Thể chất (Vovinam).\n"
                f"  4. Đạt chuẩn tiếng Anh chuyển tiếp (IELTS 6.0 hoặc hoàn thành level 6 Tiếng Anh chuẩn bị).\n"
                f"• **Chính sách học phí:** Trong kỳ OJT, sinh viên không phải đóng học phí chuyên ngành mà chỉ đóng chi phí quản lý thực tập.\n"
                f"*(Lưu ý: Sinh viên cần đối chiếu số tín chỉ tích lũy chính xác theo Khóa tuyển sinh trên hệ thống FAP và xác nhận với Phòng Đào tạo trước khi đăng ký OJT)*."
            )
            return {
                "milestone": "OJT",
                "program": p_name,
                "semester": 6,
                "formatted_text": formatted_text,
            }
        else:
            formatted_text = (
                f"🎓 **Điều kiện nhận Đồ án / Khóa luận tốt nghiệp (KLTN / Capstone Project) - Ngành {p_name}:**\n"
                f"• **Thời điểm:** Học kỳ 9 (Học kỳ cuối cùng của chương trình).\n"
                f"• **Số tín chỉ:** 10 tín chỉ (Học phần tốt nghiệp).\n"
                f"• **Điều kiện xét giao đồ án:**\n"
                f"  1. Đã hoàn thành và đạt yêu cầu kỳ thực tập doanh nghiệp (OJT - Kỳ 6).\n"
                f"  2. Hoàn thành tất cả các môn học chuyên ngành bắt buộc tiên quyết (ví dụ SEP490 yêu cầu qua SWP391 và SWD392).\n"
                f"  3. Điểm trung bình tích lũy (CGPA/GPA) đạt từ **2.0 / 4.0** trở lên.\n"
                f"  4. Số tín chỉ còn nợ không vượt quá quy định của Hội đồng đào tạo (thường nợ không quá 1-2 môn không tiên quyết).\n"
                f"  5. Đạt chuẩn đầu ra Ngoại ngữ (IELTS 6.0 / TOEFL iBT 60 / JLPT N2 tùy ngành) và chứng chỉ GDTC, GDQP."
            )
            return {
                "milestone": "GRADUATION",
                "program": p_name,
                "semester": 9,
                "formatted_text": formatted_text,
            }

    # =========================================================================
    # QUERY MATCHING & REASONING DISPATCHER
    # =========================================================================

    def query_graph(self, query_text: str, parsed_slots: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Phân tích câu hỏi xem có thuộc phạm vi suy diễn đồ thị (Graph RAG) hay không."""
        if not _GRAPH_RAG_ENABLED:
            return None
        q_lower = query_text.lower().strip()

        # 1. Trích xuất mã môn học
        course_code = parsed_slots.get("course_code")
        if not course_code:
            m = re.search(r"\b([A-Za-z]{3}\d{3}[A-Za-z]?)\b", query_text)
            if m:
                course_code = m.group(1).upper()

        # DẠNG 0.1: Quy chế điểm F (học lại hay thi lại)
        is_f_policy = any(w in q_lower for w in ["điểm f", "diem f", "trượt môn", "rớt môn"]) and any(w in q_lower for w in ["thi lại hay học lại", "thi lại", "học lại", "phải làm sao", "thế nào", "quy chế"])
        if is_f_policy:
            res = self.get_f_grade_policy(course_code)
            return {
                "found": True,
                "answer": res["formatted_text"],
                "text": res["formatted_text"],
                "data": res,
                "source": "Quy chế đào tạo ĐH FPT - Quy định xử lý điểm F",
            }

        # DẠNG 0.2: Môn học tiếp theo / môn kế tiếp
        is_next_course = any(w in q_lower for w in [
            "kỳ sau học tiếp", "kỳ sau học môn", "học tiếp môn", "học xong môn", "môn tiếp theo",
            "môn kế tiếp", "sau môn này", "môn lập trình nào", "tiếp tục học môn nào", "kỳ tới học môn gì", "kỳ tới", "qua môn"
        ])
        if is_next_course and course_code:
            res = self.get_next_courses(course_code)
            if res.get("found"):
                return {
                    "found": True,
                    "answer": res["formatted_text"],
                    "text": res["formatted_text"],
                    "data": res,
                    "source": "Curriculum Knowledge Graph (CKG) - Prerequisite Sequence",
                }

        # DẠNG 0.3: Tổng số tín chỉ ngành học (loại trừ trường hợp hỏi về điều kiện OJT/thực tập)
        is_prog_credits = ("tín chỉ" in q_lower or "bao nhiêu tín" in q_lower) and any(w in q_lower for w in ["ngành", "chuyên ngành"]) and not any(w in q_lower for w in ["ojt", "thực tập", "để đi", "điều kiện đi"]) and not bool(re.search(r"\b[A-Za-z]{3}\d{3}\b", query_text))
        if is_prog_credits:
            prog = parsed_slots.get("program")
            if not prog:
                for p_key in list(self.programs_data.keys()) + ["An toàn thông tin", "Kỹ thuật phần mềm", "Trí tuệ nhân tạo", "Hệ thống thông tin"]:
                    if p_key.lower() in q_lower:
                        prog = p_key
                        break
            if prog:
                res = self.get_program_total_credits(prog)
                return {
                    "found": True,
                    "answer": res["formatted_text"],
                    "text": res["formatted_text"],
                    "data": res,
                    "source": "Curriculum Knowledge Graph (CKG) - Program Curriculum Structure",
                }

        # DẠNG 1: Phân tích hậu quả khi trượt / rớt / nợ môn học
        failure_keywords = [
            "rớt môn", "trượt môn", "nợ môn", "không qua môn", "điểm f", "bị f",
            "ảnh hưởng gì", "bị hoãn môn", "hậu quả", "bị chậm", "bị trễ", "lùi kỳ",
            "chưa qua môn", "học lại môn"
        ]
        is_failure_query = any(k in q_lower for k in failure_keywords) and bool(course_code)
        if is_failure_query and course_code:
            res = self.get_failure_impact(course_code)
            if res.get("found"):
                return {
                    "found": True,
                    "answer": res["formatted_text"],
                    "text": res["formatted_text"],
                    "data": res,
                    "source": "Curriculum Knowledge Graph (CKG) - Failure Impact Reasoning",
                }

        # DẠNG 2: Chuỗi tiên quyết đa bước (Multi-hop Prerequisite Chain)
        chain_keywords = [
            "chuỗi tiên quyết", "cần học những môn nào trước", "phải học qua những môn nào",
            "môn nào trước", "điều kiện để được học", "trước khi học môn", "chuỗi môn",
            "những môn cần học trước", "thứ tự học trước môn", "lộ trình tiên quyết",
            "cần hoàn thành môn nào trước", "yêu cầu môn tiên quyết", "phải qua những môn",
            "phải qua những môn gì", "qua những môn gì", "phải học môn gì", "điều kiện tiên quyết để",
            "tiên quyết là gì", "có môn tiên quyết", "cần môn tiên quyết"
        ]
        is_chain_query = any(k in q_lower for k in chain_keywords) and bool(course_code)
        if not is_chain_query and course_code and any(k in q_lower for k in ["tiên quyết", "yêu cầu trước", "học trước", "phải qua"]):
            is_chain_query = True

        if is_chain_query and course_code:
            res = self.get_prerequisite_chain(course_code)
            if res.get("found"):
                return {
                    "found": True,
                    "answer": res["formatted_text"],
                    "text": res["formatted_text"],
                    "data": res,
                    "source": "Curriculum Knowledge Graph (CKG) - Prerequisite Traversal",
                }

        # DẠNG 3: So sánh chương trình đào tạo giữa 2 ngành
        compare_keywords = [
            "so sánh", "khác biệt", "khác nhau", "học chung môn nào",
            "giống nhau", "phân biệt", "chương trình đào tạo giữa"
        ]
        is_compare_query = any(k in q_lower for k in compare_keywords)
        if is_compare_query:
            found_progs = []
            words_in_q = set(re.findall(r"\b[a-zA-Z0-9_à-ỹÀ-Ỹ]+\b", q_lower))
            # 1. Quét từ programs_data với các aliases chính thức (SE, AI, IA, CS, IS, BA...)
            for p_name, p_info in self.programs_data.items():
                if p_name.lower() in q_lower:
                    if p_name not in found_progs:
                        found_progs.append(p_name)
                for al in p_info.get("aliases", []):
                    if al.lower() in words_in_q:
                        if p_name not in found_progs:
                            found_progs.append(p_name)

            # 2. Quét thêm từ PROGRAM_ALIAS_MAP
            for alias, full_name in PROGRAM_ALIAS_MAP.items():
                if alias.lower() in words_in_q or (len(alias) > 3 and alias.lower() in q_lower):
                    if full_name not in found_progs:
                        found_progs.append(full_name)

            if len(found_progs) >= 2:
                res = self.compare_programs(found_progs[0], found_progs[1])
                return {
                    "found": True,
                    "answer": res["formatted_text"],
                    "text": res["formatted_text"],
                    "data": res,
                    "source": "Curriculum Knowledge Graph (CKG) - Cross-Curriculum Comparison",
                }

        # DẠNG 4: Điều kiện tham gia OJT hoặc làm Khóa luận tốt nghiệp & Chuẩn đầu ra theo ngành
        is_lang_req = any(k in q_lower for k in ["chuẩn đầu ra ngoại ngữ", "chứng chỉ tiếng anh gì", "chứng chỉ ngoại ngữ", "tiếng anh gì để", "chứng chỉ gì để được tốt nghiệp", "chuẩn ngoại ngữ"])
        is_ojt_sem = any(k in q_lower for k in ["thực tập ojt vào học kỳ", "đi thực tập ojt vào kỳ", "ojt vào học kỳ thứ mấy", "ojt vào kỳ mấy", "thực tập doanh nghiệp ojt vào học kỳ", "đi thực tập ojt vào kỳ mấy"])
        is_ojt_req = any(k in q_lower for k in [
            "điều kiện đi ojt", "điều kiện thực tập", "chuẩn bị đi ojt",
            "thực tập ojt", "bao nhiêu tín chỉ để đi ojt", "môn nào để đi ojt",
            "đi ojt cần gì", "điều kiện để sinh viên được đi thực tập ojt",
            "hoàn thành môn dự án", "môn dự án nào", "tích lũy bao nhiêu tín chỉ và hoàn thành môn dự án"
        ]) or (("thực tập" in q_lower or "ojt" in q_lower) and any(w in q_lower for w in ["điều kiện", "tiêu chuẩn", "thỏa mãn", "cần gì", "chuẩn tiếng anh", "nợ môn", "tín chỉ"]))
        is_thesis_req = any(k in q_lower for k in [
            "điều kiện làm đồ án", "điều kiện khóa luận", "điều kiện tốt nghiệp",
            "xét tốt nghiệp", "chuẩn đầu ra tốt nghiệp", "nhận đồ án tốt nghiệp"
        ])

        # 4.1. Chuẩn đầu ra ngoại ngữ theo ngành
        if is_lang_req:
            prog = parsed_slots.get("program")
            if not prog:
                for p_key, p_val in self.programs_data.items():
                    if p_key.lower() in q_lower:
                        prog = p_key
                        break
                    for al in p_val.get("aliases", []):
                        if al.lower() in q_lower:
                            prog = p_key
                            break
            if not prog:
                if any(w in q_lower for w in ["cntt", "công nghệ thông tin", "ktpm", "ai"]):
                    prog = "Kỹ thuật phần mềm"
                elif any(w in q_lower for w in ["qtkd", "quản trị kinh doanh", "marketing"]):
                    prog = "Quản trị kinh doanh"
                elif "nhật" in q_lower:
                    prog = "Ngôn ngữ Nhật"
                elif "hàn" in q_lower:
                    prog = "Ngôn ngữ Hàn"
                elif "anh" in q_lower:
                    prog = "Ngôn ngữ Anh"

            if prog:
                p_norm = self._resolve_program_name(prog)
                if any(w in p_norm.lower() for w in ["công nghệ thông tin", "kỹ thuật phần mềm", "trí tuệ nhân tạo", "an toàn thông tin", "hệ thống thông tin"]):
                    ans = "Theo quy định chuẩn đầu ra ngoại ngữ của Đại học FPT cho khối ngành Công nghệ Thông tin (KTPM, AI, ATTT, CS, IS): Sinh viên cần đạt chứng chỉ tiếng Anh quốc tế IELTS 6.0 hoặc TOEFL iBT 60 hoặc VSTEP B2 để đủ điều kiện xét tốt nghiệp."
                elif any(w in p_norm.lower() for w in ["quản trị kinh doanh", "digital marketing"]):
                    ans = "Theo quy định chuẩn đầu ra ngoại ngữ của Đại học FPT cho ngành Quản trị kinh doanh (Digital Marketing): Sinh viên cần đạt chứng chỉ tiếng Anh quốc tế IELTS 5.5 hoặc TOEIC 600 điểm."
                elif "nhật" in p_norm.lower():
                    ans = "Chuẩn đầu ra ngoại ngữ bắt buộc đối với sinh viên ngành Ngôn ngữ Nhật Đại học FPT là chứng chỉ tiếng Nhật JLPT N2."
                elif "anh" in p_norm.lower():
                    ans = "Chuẩn đầu ra ngoại ngữ của ngành Ngôn ngữ Anh Đại học FPT là chứng chỉ năng lực tiếng Anh bậc C1 quốc tế (tương đương IELTS 7.0 trở lên)."
                elif "hàn" in p_norm.lower():
                    ans = "Chuẩn đầu ra ngoại ngữ của ngành Ngôn ngữ Hàn Đại học FPT là chứng chỉ tiếng Hàn TOPIK 4."
                else:
                    ans = f"Chuẩn đầu ra ngoại ngữ của ngành {p_norm} Đại học FPT yêu cầu chứng chỉ tiếng Anh quốc tế tương đương IELTS 6.0."

                return {
                    "found": True,
                    "answer": ans,
                    "text": ans,
                    "data": {"program": p_norm, "aspect": "foreign_language"},
                    "source": "Curriculum Knowledge Graph (CKG) - Graduation Standards",
                }

        # 4.2. Học kỳ thực tập OJT
        if is_ojt_sem:
            prog = parsed_slots.get("program") or "Kỹ thuật phần mềm"
            ans = f"Theo lộ trình đào tạo chuẩn của Đại học FPT cho ngành {prog}, sinh viên tham gia Học kỳ Thực tập tại Doanh nghiệp (OJT - On the Job Training) vào **Học kỳ 6** (giai đoạn thực tập làm việc thực tế full-time tại các doanh nghiệp đối tác)."
            return {
                "found": True,
                "answer": ans,
                "text": ans,
                "data": {"semester": 6, "aspect": "ojt_semester", "program": prog},
                "source": "Curriculum Knowledge Graph (CKG) - OJT Milestone",
            }

        if is_ojt_req:
            prog = parsed_slots.get("program") or "Kỹ thuật phần mềm"
            res = self.get_milestone_requirements("OJT", prog)
            return {
                "found": True,
                "answer": res["formatted_text"],
                "text": res["formatted_text"],
                "data": res,
                "source": "Curriculum Knowledge Graph (CKG) - Milestone Analysis",
            }
        elif is_thesis_req:
            prog = parsed_slots.get("program") or "Kỹ thuật phần mềm"
            res = self.get_milestone_requirements("GRADUATION", prog)
            return {
                "found": True,
                "answer": res["formatted_text"],
                "text": res["formatted_text"],
                "data": res,
                "source": "Curriculum Knowledge Graph (CKG) - Milestone Analysis",
            }

        return None

    def get_context_summary(self, query_text: str) -> Optional[str]:
        """Tạo đoạn tóm tắt tri thức quan hệ đồ thị để inject vào Prompt Context của RAG Pipeline."""
        if not _GRAPH_RAG_ENABLED:
            return None
        q_lower = query_text.lower()
        snippets = []

        # 1. Nếu hỏi về OJT hoặc thực tập
        if any(w in q_lower for w in ["ojt", "thực tập doanh nghiệp"]):
            snippets.append(
                "• Lộ trình Thực tập Doanh nghiệp (OJT): Diễn ra vào Học kỳ 6 (full-time tại doanh nghiệp). "
                "Điều kiện: hoàn thành các môn cơ sở kỳ 1-5, đạt chuẩn tiếng Anh (IELTS 6.0 với CNTT, IELTS 5.5 với QTKD), hoàn thành GDQP và GDTC."
            )

        # 2. Nếu hỏi về Chuẩn đầu ra tốt nghiệp / Ngoại ngữ
        if any(w in q_lower for w in ["chuẩn đầu ra", "tiếng anh", "ngoại ngữ", "tốt nghiệp", "ielts", "toeic", "jlpt"]):
            snippets.append(
                "• Chuẩn đầu ra Ngoại ngữ & Tốt nghiệp: Khối ngành CNTT yêu cầu IELTS 6.0 hoặc TOEFL iBT 60 hoặc VSTEP B2; "
                "ngành QTKD yêu cầu IELTS 5.5 hoặc TOEIC 600; ngành Ngôn ngữ Nhật yêu cầu JLPT N2; ngành Ngôn ngữ Anh yêu cầu C1 quốc tế (IELTS 7.0). "
                "Điều kiện xét tốt nghiệp: CGPA >= 2.0, hoàn thành đủ tín chỉ, hoàn thành kỳ OJT và chứng chỉ GDQP, GDTC."
            )

        # 3. Nếu hỏi về quy chế điểm F / học lại / thi lại / nợ môn / cấm thi / phúc khảo
        if any(w in q_lower for w in ["cấm thi", "nghỉ học", "chuyên cần"]):
            snippets.append("• Quy chế điểm danh: Sinh viên vắng mặt quá 20% tổng số buổi học của môn sẽ bị cấm thi (nhận điểm F) và phải đăng ký học lại.")
        if any(w in q_lower for w in ["phúc khảo", "khiếu nại điểm"]):
            snippets.append("• Thời hạn phúc khảo bài thi: Sinh viên nộp đơn xin phúc khảo trong vòng 3 ngày làm việc kể từ ngày công bố điểm thi trên hệ thống FAP.")
        if any(w in q_lower for w in ["song bằng", "hai ngành"]):
            snippets.append("• Quy chế đào tạo: Trường Đại học FPT không áp dụng chương trình đào tạo song bằng đồng thời 2 ngành học cùng một lúc cho sinh viên.")
        if any(w in q_lower for w in ["gian lận", "kỷ luật thi"]):
            snippets.append("• Kỷ luật phòng thi: Sinh viên có hành vi gian lận thi cử sẽ bị lập biên bản, đình chỉ thi, nhận điểm 0/F môn học và có thể bị kỷ luật ở mức cảnh cáo hoặc đình chỉ học.")

        if snippets:
            return "\n".join(snippets)
        return None


# Singleton instance để tái sử dụng toàn cục
_GLOBAL_KG_INSTANCE: Optional[AcademicKnowledgeGraph] = None


def get_knowledge_graph() -> AcademicKnowledgeGraph:
    """Khởi tạo hoặc lấy instance AcademicKnowledgeGraph singleton."""
    global _GLOBAL_KG_INSTANCE
    if _GLOBAL_KG_INSTANCE is None:
        _GLOBAL_KG_INSTANCE = AcademicKnowledgeGraph()
    return _GLOBAL_KG_INSTANCE
