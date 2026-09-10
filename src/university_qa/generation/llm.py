"""Interface kết nối các nhà cung cấp LLM (Gemini, OpenAI) kèm chế độ mock/offline. Phụ trách: TV3."""

import os
from typing import Any, Dict, Optional


class LLMClient:
    """Bộ bọc thống nhất gọi LLM APIs."""

    def __init__(
        self,
        provider: str = "gemini",
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ):
        self.provider = provider.lower()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        if self.provider == "gemini":
            self.model = model or "gemini-1.5-flash"
            self._api_key = os.environ.get("GEMINI_API_KEY")
        elif self.provider == "openai":
            self.model = model or "gpt-4o-mini"
            self._api_key = os.environ.get("OPENAI_API_KEY")
        else:
            self.model = "mock"
            self._api_key = None

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Gửi prompt tới mô hình ngôn ngữ và nhận câu trả lời."""
        if not self._api_key:
            # Fallback an toàn khi chưa cấu hình API key
            return (
                f"[Chế độ mô phỏng - Chưa cài đặt {self.provider.upper()}_API_KEY]\n"
                f"Hệ thống đã nhận diện truy vấn và tổng hợp từ tài liệu tra cứu được."
            )

        if self.provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=self._api_key)
                gemini_model = genai.GenerativeModel(
                    model_name=self.model,
                    system_instruction=system_instruction,
                )
                response = gemini_model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.temperature,
                        max_output_tokens=self.max_tokens,
                    ),
                )
                return response.text.strip()
            except Exception as e:
                return f"Lỗi gọi Gemini API: {str(e)}"

        elif self.provider == "openai":
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self._api_key)
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                messages.append({"role": "user", "content": prompt})

                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                return f"Lỗi gọi OpenAI API: {str(e)}"

        return "Không xác định được LLM provider."
