# backend/app/errors.py —— 统一错误体（site-spec 5.2 全 8 码，冻结）
from __future__ import annotations

# code → (HTTP 状态码, 前端提示主文案)
ERROR_TABLE = {
    "VALIDATION_ERROR": (400, "提交内容不合法，请检查后重试"),
    "UNAUTHORIZED": (401, "请先登录（登录状态可能已过期）"),  # Δ1 新增（site-spec 13.1）
    "PROBLEM_NOT_FOUND": (404, "题目不存在"),
    "SUBMISSION_NOT_FOUND": (404, "找不到该次提交"),
    "PAYLOAD_TOO_LARGE": (413, "代码太长，请精简后重试"),
    "JUDGE_TIMEOUT": (408, "判题超时，请检查死循环后重试"),
    "JUDGE_BUSY": (429, "判题进行中，请稍候重试"),
    "ENGINE_UNAVAILABLE": (503, "判题引擎不可用，请检查本机编译环境"),
    "INTERNAL_ERROR": (500, "服务异常，请重试"),
}


class ApiError(Exception):
    """带错误码的 API 异常，由全局 handler 转统一错误体。"""

    def __init__(self, code: str, message: str | None = None):
        status, default_msg = ERROR_TABLE[code]
        self.code = code
        self.status = status
        self.message = message or default_msg
        super().__init__(self.message)

    def body(self) -> dict:
        return {"error": {"code": self.code, "message": self.message}}
