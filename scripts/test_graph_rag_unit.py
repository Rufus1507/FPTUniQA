import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

import psutil

process = psutil.Process(os.getpid())
ram_before = process.memory_info().rss / (1024 * 1024)
t0 = time.time()

from FPTUniQA.graph.knowledge_graph import get_knowledge_graph

kg = get_knowledge_graph()
t_build = (time.time() - t0) * 1000
ram_after = process.memory_info().rss / (1024 * 1024)

print(f"[*] Knowledge Graph build time: {t_build:.2f} ms")
print(f"[*] RAM footprint of Graph: {ram_after - ram_before:.2f} MB")
print(f"[*] Total Nodes: {kg.graph.number_of_nodes()}, Total Edges: {kg.graph.number_of_edges()}")

# Test 1: Chuỗi tiên quyết SWP391
t1 = time.time()
res1 = kg.get_prerequisite_chain("SWP391")
t1_lat = (time.time() - t1) * 1000
print(f"\n[Test 1] Prerequisite chain for SWP391 (Latency: {t1_lat:.3f} ms):")
print(res1["formatted_text"])

# Test 2: Chuỗi tiên quyết SEP490 (Khóa luận tốt nghiệp)
t2 = time.time()
res2 = kg.get_prerequisite_chain("SEP490")
t2_lat = (time.time() - t2) * 1000
print(f"\n[Test 2] Prerequisite chain for SEP490 (Latency: {t2_lat:.3f} ms):")
print(res2["formatted_text"])

# Test 3: Hậu quả rớt môn PRF192
t3 = time.time()
res3 = kg.get_failure_impact("PRF192")
t3_lat = (time.time() - t3) * 1000
print(f"\n[Test 3] Failure impact of PRF192 (Latency: {t3_lat:.3f} ms):")
print(res3["formatted_text"])

# Test 4: So sánh KTPM và AI
t4 = time.time()
res4 = kg.compare_programs("KTPM", "AI")
t4_lat = (time.time() - t4) * 1000
print(f"\n[Test 4] Compare KTPM and AI (Latency: {t4_lat:.3f} ms):")
print(f"Shared courses count: {res4['shared_count']}")
print(f"Unique SE: {len(res4['unique_courses_a'])}, Unique AI: {len(res4['unique_courses_b'])}")

# Test 5: query_graph dispatcher
queries = [
    "Muốn học môn SWP391 thì cần học qua những môn nào trước?",
    "Nếu bị rớt môn PRF192 thì có bị ảnh hưởng gì đến các kỳ sau không?",
    "Điều kiện để sinh viên được đi thực tập OJT là gì?",
    "So sánh chương trình đào tạo giữa ngành SE và AI",
]

print("\n[Test 5] Query Graph Dispatcher:")
for q in queries:
    tq = time.time()
    g_res = kg.query_graph(q, {})
    lat = (time.time() - tq) * 1000
    status = "FOUND" if (g_res and g_res.get("found")) else "NOT FOUND"
    src = g_res.get("source", "") if g_res else ""
    print(f"Query: '{q}' -> [{status}] ({lat:.2f} ms) | Source: {src}")
