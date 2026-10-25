# backend/app/schemas/api.py —— Pydantic 模型 = site-spec 第 5 节契约的唯一代码来源
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

VerdictT = Literal["AC", "PE", "WA", "TLE", "RE", "CE", "SE"]
ModeT = Literal["acm", "oi"]


# ---------- 统一错误体 ----------

class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorBody(BaseModel):
    error: ErrorDetail


# ---------- 组件类型（5.3） ----------

class ProblemSummary(BaseModel):
    id: str
    title: str
    contest_type: ModeT
    score: float
    test_count: int
    time_limit_ms: int
    memory_limit_mb: int
    build_mode: Literal["g++", "make"]
    topic: Optional[str] = None
    difficulty: Optional[str] = None


class Limits(BaseModel):
    time_ms: int
    memory_mb: int


class BuildInfo(BaseModel):
    mode: Literal["g++", "make"]
    command: str
    src: Optional[str] = None
    default_filename: Optional[str] = None


class Sample(BaseModel):
    input: str
    output: str


class ProblemDetail(BaseModel):
    id: str
    title: str
    contest_type: ModeT
    score: float
    compare_mode: Literal["exact", "trim"]
    limits: Limits
    build: BuildInfo
    statement_md: str
    samples: list[Sample]
    test_count: int


class CaseResult(BaseModel):
    name: str
    verdict: VerdictT
    time_ms: float
    exit_code: Optional[int] = None
    weight: float
    message: str
    signal: Optional[str] = None
    timed_out: bool = False
    stderr_tail: Optional[str] = None


class Summary(BaseModel):
    total: int
    passed: int
    pass_rate: float
    score: float
    max_score: float
    partial_score: float


class FileItem(BaseModel):
    name: str
    content: str


class SubmissionResult(BaseModel):
    submission_id: str
    problem_id: str
    problem_title: str
    mode: ModeT
    created_at: str
    status: Literal["finished", "failed"]
    verdict: VerdictT
    summary: Summary
    cases: list[CaseResult]
    build_log: Optional[str] = None
    files: list[FileItem]
    message: Optional[str] = None
    # Δ3（G1 增补）：true=已写入 Supabase；false=未入库（未带 token/未配置/写入失败）
    synced: bool = False


class SubmissionSummary(BaseModel):
    submission_id: str
    problem_id: str
    problem_title: str
    file_label: str
    created_at: str
    mode: ModeT
    verdict: VerdictT
    summary: Summary


# ---------- 请求 / 响应包装 ----------

class SubmissionCreate(BaseModel):
    problem_id: str
    source_code: Optional[str] = None
    filename: Optional[str] = None
    files: Optional[list[FileItem]] = None
    mode: Optional[ModeT] = None


class ProblemListResponse(BaseModel):
    items: list[ProblemSummary]
    total: int


class SubmissionListResponse(BaseModel):
    items: list[SubmissionSummary]
    total: int


class ExampleItem(BaseModel):
    name: str
    content: str
    expect: str
    # 多文件示例（如 P6_make）：整套文件可一键载入多文件提交区
    files: Optional[list[FileItem]] = None


class ExamplesResponse(BaseModel):
    items: list[ExampleItem]


class HealthResponse(BaseModel):
    status: str = "ok"
    engine: str = "ready"
    version: str
    problem_count: int
    # Δ3：SUPABASE_URL 与 SUPABASE_SECRET_KEY 均已配置（向后兼容追加字段）
    supabase_configured: bool = False
