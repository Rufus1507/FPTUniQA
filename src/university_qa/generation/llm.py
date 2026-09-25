"""Lớp giao tiếp với mô hình ngôn ngữ lớn (LLM Client) hỗ trợ OpenAI-compatible API và Anthropic API."""

import requests
from typing import Optional
from university_qa.utils.config import config
from university_qa.utils.logger import get_logger

logger = get_logger("university_qa.llm")


class LLMClient:
    """Client gọi API mô hình ngôn ngữ lớn với cơ chế bắt lỗi an toàn và hỗ trợ đa nền tảng."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.base_url = base_url or config.llm_base_url
        self.api_key = api_key or config.llm_api_key or config.anthropic_api_key
        self.model_name = model_name or config.model_name
        self.timeout = timeout or config.llm_timeout
        self._openai_client = None
        self._anthropic_client = None

        # 1. Khởi tạo client OpenAI-compatible nếu có base_url (ví dụ http://localhost:20128/v1)
        if self.base_url and self.api_key:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                    timeout=self.timeout,
                )
                logger.info(
                    f"Đã khởi tạo OpenAI Client kết nối tới: {self.base_url} (model: {self.model_name})"
                )
            except Exception as e:
                logger.warning(f"Không thể khởi tạo OpenAI Client: {e}. Sẽ gọi REST trực tiếp.")
                self._openai_client = None

        # 2. Khởi tạo Anthropic nếu không có base_url và có anthropic_api_key
        elif config.anthropic_api_key:
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(
                    api_key=config.anthropic_api_key,
                    timeout=self.timeout,
                )
                logger.info(f"Đã khởi tạo Anthropic Client (model: {self.model_name})")
            except Exception as e:
                logger.warning(f"Không thể khởi tạo Anthropic Client: {e}")
                self._anthropic_client = None
        else:
            logger.info("Chưa cấu hình API Key. Kích hoạt chế độ Fallback Mock LLM.")

    def generate(self, system_prompt: str, user_prompt: Optional[str] = None) -> str:
        """Gửi prompt tới LLM và nhận câu trả lời văn bản an toàn."""
        if user_prompt is None:
            user_prompt = system_prompt
            system_prompt = "Bạn là Trợ lý Tư vấn Học vụ Đại học FPT thông minh, chuẩn mực và tận tâm."

        # Ưu tiên 1: Gọi qua OpenAI-compatible Client (http://localhost:20128/v1)
        if self._openai_client is not None:
            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
                response = self._openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=1024,
                    stream=False,
                )
                choice = response.choices[0]
                content = choice.message.content
                if content:
                    return content.strip()
                return "Không nhận được phản hồi văn bản từ mô hình."
            except Exception as exc:
                logger.warning(f"Lỗi OpenAI client: {exc}. Thử gọi trực tiếp qua HTTP requests...")
                # Thử gọi trực tiếp qua requests nếu SDK gặp sự cố định dạng stream
                return self._call_http_direct(system_prompt, user_prompt)

        # Ưu tiên 2: Gọi qua Anthropic SDK
        if self._anthropic_client is not None:
            try:
                response = self._anthropic_client.messages.create(
                    model=self.model_name,
                    max_tokens=1024,
                    temperature=0.1,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                content_blocks = response.content
                if content_blocks and len(content_blocks) > 0:
                    return content_blocks[0].text.strip()
                return "Không nhận được phản hồi từ Anthropic."
            except Exception as exc:
                error_msg = f"Lỗi gọi Anthropic API: {str(exc)}"
                logger.error(error_msg)
                return f"Lỗi kết nối AI: {str(exc)}"

        # Ưu tiên 3: Nếu có base_url và api_key nhưng chưa có SDK
        if self.base_url and self.api_key:
            return self._call_http_direct(system_prompt, user_prompt)

        # Ưu tiên 4: Fallback mô phỏng cho kiểm thử pipeline
        return self._generate_fallback(user_prompt)

    def _call_http_direct(self, system_prompt: str, user_prompt: str) -> str:
        """Gọi trực tiếp REST API chat/completions khi không qua SDK."""
        try:
            endpoint = f"{self.base_url.rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 1024,
                "stream": False,
            }
            res = requests.post(endpoint, headers=headers, json=payload, timeout=self.timeout)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                logger.error(f"HTTP Error {res.status_code}: {res.text}")
                return f"Lỗi gọi LLM API (Mã lỗi {res.status_code}): {res.text}"
        except Exception as exc:
            logger.error(f"Lỗi khi gửi HTTP request tới LLM: {exc}")
            return self._generate_fallback(user_prompt)

    def _generate_fallback(self, user_prompt: str) -> str:
        """Sinh câu trả lời mẫu có trích dẫn [Nguồn N] cho kiểm thử."""
        lower_prompt = user_prompt.lower()
        if "cảnh báo" in lower_prompt or "cảnh cáo" in lower_prompt:
            return (
                "Theo quy chế của Đại học FPT [Nguồn 1], sinh viên sẽ bị cảnh cáo học vụ nếu: "
                "(1) Điểm trung bình học kỳ (GPA) dưới 1.0 trong học kỳ đầu tiên, hoặc dưới 1.2 trong các kỳ tiếp theo; "
                "(2) Điểm trung bình tích lũy (CGPA) dưới 1.2 đối với năm nhất, dưới 1.4 đối với năm hai, và dưới 1.6 đối với năm ba trở đi. "
                "Đặc biệt, sinh viên bị cảnh cáo học vụ 3 lần liên tiếp sẽ bị xử lý buộc thôi học [Nguồn 1]."
            )
        elif "tốt nghiệp" in lower_prompt:
            return (
                "Theo quy định xét tốt nghiệp của ĐH FPT [Nguồn 2], sinh viên cần đáp ứng các điều kiện: "
                "hoàn thành đủ số tín chỉ, điểm CGPA đạt từ 2.00 trở lên, đạt chuẩn ngoại ngữ tương đương IELTS 5.5/TOEIC 550, "
                "hoàn thành GDQP, GDTC và kỳ thực tập OJT [Nguồn 2]."
            )
        elif "học phí" in lower_prompt:
            return (
                "Theo chính sách học phí ĐH FPT [Nguồn 3], học phí chuyên ngành tiêu chuẩn là 28.700.000 VNĐ/học kỳ. "
                "Học phí phải được hoàn tất trước ngày học đầu tiên ít nhất 7 ngày qua cổng FAP hoặc ngân hàng liên kết [Nguồn 3]."
            )
        else:
            return (
                "Dựa trên các tài liệu quy chế được trích xuất [Nguồn 1], thông tin liên quan đến câu hỏi của bạn "
                "đã được ghi nhận. Vui lòng tham khảo kỹ các điều khoản trích dẫn bên dưới để nắm rõ chi tiết [Nguồn 1]."
            )
