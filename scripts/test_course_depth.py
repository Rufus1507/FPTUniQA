"""Script kiểm thử trực tiếp các câu hỏi xoáy sâu vào nội dung học và giáo trình môn học."""

import sys
from FPTUniQA.pipeline.rag_pipeline import RAGPipeline

def main():
    pipeline = RAGPipeline(use_mock_fallback=False)
    questions = [
        "Môn PRF192 học những gì?",
        "Giáo trình môn PRO192 là sách nào?",
        "Môn CSD201 học về những nội dung gì?",
        "Giáo trình môn MKT101 của ai viết?",
        "Môn DBI202 học những gì?",
        "Giáo trình môn Mật mã học CRY301 dùng sách của tác giả nào?",
        "Môn Võ Vovinam 1 VOV114 học những gì?",
        "Môn Học máy AIL302m học những nội dung kiến thức gì?",
    ]

    for i, q in enumerate(questions, 1):
        print(f"\n=======================================================")
        print(f"CÂU HỎI {i}: {q}")
        print(f"=======================================================")
        res = pipeline.answer(q)
        ans = res.get("answer", "")
        # Print with ascii safe encoding for windows console
        print(ans.encode("ascii", "replace").decode("ascii"))

if __name__ == "__main__":
    main()
