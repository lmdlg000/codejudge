# backend/app/routers/health.py —— GET /api/health（site-spec B6）
from __future__ import annotations

from fastapi import APIRouter

from ..config import VERSION, supabase_configured
from ..errors import ApiError
from ..schemas.api import HealthResponse
from ..services import problem_service

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    ok, reason = problem_service.engine_status()
    if not ok:
        raise ApiError("ENGINE_UNAVAILABLE", f"判题引擎不可用，请检查本机编译环境：{reason}")
    problems = problem_service.list_problems_raw()
    return HealthResponse(
        status="ok",
        engine="ready",
        version=VERSION,
        problem_count=len(problems),
        supabase_configured=supabase_configured(),
    )
