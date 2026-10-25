# backend/app/routers/problems.py —— GET /api/problems、GET /api/problems/{pid}、GET /api/examples
from __future__ import annotations

from fastapi import APIRouter, Query

from ..errors import ApiError
from ..schemas.api import (
    ExampleItem,
    ExamplesResponse,
    ProblemDetail,
    ProblemListResponse,
    ProblemSummary,
)
from ..services import problem_service

router = APIRouter()


@router.get("/api/problems", response_model=ProblemListResponse)
def list_problems() -> ProblemListResponse:
    problems = problem_service.list_problems_raw()
    items = [ProblemSummary(**problem_service.problem_summary(p)) for p in problems]
    return ProblemListResponse(items=items, total=len(items))


@router.get("/api/problems/{pid}", response_model=ProblemDetail)
def get_problem(pid: str) -> ProblemDetail:
    problem = problem_service.load_problem(pid)
    return ProblemDetail(**problem_service.problem_detail(problem))


@router.get("/api/examples", response_model=ExamplesResponse)
def get_examples(problem_id: str | None = Query(default=None)) -> ExamplesResponse:
    if not problem_id:
        raise ApiError("VALIDATION_ERROR", "提交内容不合法，请检查后重试：problem_id 必填")
    items = problem_service.examples_for(problem_id)
    return ExamplesResponse(
        items=[
            ExampleItem(
                name=i["name"],
                content=i["content"],
                expect=i["expect"],
                files=i.get("files"),
            )
            for i in items
        ]
    )
