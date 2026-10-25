# backend/app/routers/submissions.py —— POST/GET /api/submissions(/{sid})（site-spec B3/B4/B5）
from __future__ import annotations

from fastapi import APIRouter, Header, Query

from ..errors import ApiError
from ..schemas.api import (
    SubmissionCreate,
    SubmissionListResponse,
    SubmissionResult,
    SubmissionSummary,
)
from ..services import judge_service, submission_store

router = APIRouter()


@router.post("/api/submissions", response_model=SubmissionResult, status_code=201)
async def create_submission(
    body: SubmissionCreate,
    authorization: str | None = Header(default=None),
) -> SubmissionResult:
    report = await judge_service.run_submission(
        problem_id=body.problem_id,
        source_code=body.source_code,
        filename=body.filename,
        files=[f.model_dump() for f in body.files] if body.files is not None else None,
        mode=body.mode,
        authorization=authorization,
    )
    return SubmissionResult(**report)


@router.get("/api/submissions", response_model=SubmissionListResponse)
def list_submissions(
    problem_id: str | None = Query(default=None),
    limit: int | None = Query(default=None),
    offset: int | None = Query(default=None),
) -> SubmissionListResponse:
    lim = 20 if limit is None else limit
    off = 0 if offset is None else offset
    if lim < 1 or lim > 100:
        raise ApiError("VALIDATION_ERROR", "查询参数不合法，请检查后重试：limit 须在 1–100")
    if off < 0:
        raise ApiError("VALIDATION_ERROR", "查询参数不合法，请检查后重试：offset 须 ≥0")
    items, total = submission_store.list_reports(problem_id, lim, off)
    return SubmissionListResponse(
        items=[SubmissionSummary(**it) for it in items],
        total=total,
    )


@router.get("/api/submissions/{sid}", response_model=SubmissionResult)
def get_submission(sid: str) -> SubmissionResult:
    report = submission_store.load_report(sid)
    return SubmissionResult(**report)
