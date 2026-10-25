# backend/app/services/submission_store.py —— reports/ 读写、sid 生成、历史查询（site-spec B8）
from __future__ import annotations

from core import reporter

from ..config import get_reports_dir
from ..errors import ApiError


def new_sid(pid: str) -> str:
    return reporter.make_sid(pid)


def save_report(report: dict) -> str:
    """写 reports/<sid>.json + latest.json 同步副本，返回 sid。"""
    try:
        reporter.write_report(report, get_reports_dir())
    except OSError as exc:
        raise ApiError("INTERNAL_ERROR", f"报告写入失败：{exc}")
    return report["submission_id"]


def load_report(sid: str) -> dict:
    report = reporter.load_report(get_reports_dir(), sid)
    if report is None:
        raise ApiError("SUBMISSION_NOT_FOUND", f"找不到该次提交：{sid}")
    return report


def _summary_of(report: dict) -> dict:
    return {
        "submission_id": report["submission_id"],
        "problem_id": report["problem_id"],
        "problem_title": report.get("problem_title", report["problem_id"]),
        "file_label": report.get("file_label") or reporter.file_label_of(report.get("files") or []),
        "created_at": report.get("created_at") or report.get("started_at", ""),
        "mode": report.get("mode") or report.get("contest_type", "oi"),
        "verdict": report.get("verdict", "SE"),
        "summary": report["summary"],
    }


def list_reports(problem_id: str | None, limit: int, offset: int) -> tuple[list[dict], int]:
    """倒序（新→旧）历史列表；total 为过滤后总数（site-spec B5）。"""
    reports_dir = get_reports_dir()
    items: list[dict] = []
    if reports_dir.is_dir():
        for path in reports_dir.glob("*.json"):
            if path.name == "latest.json":
                continue
            report = reporter.load_report(reports_dir, path.stem)
            if report is None:
                continue
            if problem_id and report.get("problem_id") != problem_id:
                continue
            items.append(_summary_of(report))
    items.sort(key=lambda r: (r["created_at"], r["submission_id"]), reverse=True)
    total = len(items)
    return items[offset : offset + limit], total
