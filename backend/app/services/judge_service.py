# backend/app/services/judge_service.py —— 提交流水线编排（site-spec 8.2）
# 同步判题：asyncio.to_thread 跑流水线；全局单并发（拿不到锁→429）；整单 120s 硬上限（→408）
from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ..config import PROJECT_ROOT, get_max_submit_seconds

if str(PROJECT_ROOT) not in sys.path:  # 允许任意工作目录启动 uvicorn
    sys.path.insert(0, str(PROJECT_ROOT))

from core.problem import is_safe_name  # noqa: E402
from core import reporter  # noqa: E402
from judge import evaluate  # noqa: E402  CLI/API 共用同一条流水线，判定语义单一来源

from ..errors import ApiError  # noqa: E402
from . import auth_service, problem_service, submission_store, supabase_store  # noqa: E402

# 契约冻结的提交体积上限（site-spec 5.2 PAYLOAD_TOO_LARGE）
MAX_FILE_CHARS = 65536
MAX_TOTAL_CHARS = 262144
MAX_FILES = 20

FILE_NAME_HELP = "文件名仅限字母、数字、_ . -，最长 64 字符"

_executor = ThreadPoolExecutor(max_workers=1)  # 判题线程单工：物理上互斥
_busy = threading.Lock()  # 快速拒绝：第 2 单立即 429


def _val_error(detail: str) -> ApiError:
    return ApiError("VALIDATION_ERROR", f"提交内容不合法，请检查后重试：{detail}")


def _check_name(name: str) -> None:
    if not is_safe_name(name):
        raise _val_error(FILE_NAME_HELP)


def validate_submission(problem, source_code, filename, files, mode):
    """入参校验：恰好给 source_code|files 之一、文件名白名单、体积上限。返回 (files 回显列表, mode)。"""
    if (source_code is None) == (files is None):
        raise _val_error("source_code 与 files 必须恰好给其一")

    file_items: list[dict] = []
    if source_code is not None:
        if not isinstance(source_code, str) or source_code.strip() == "":
            raise _val_error("源码为空")
        if len(source_code) > MAX_FILE_CHARS:
            raise ApiError(
                "PAYLOAD_TOO_LARGE",
                f"代码太长，请精简后重试：单文件上限 {MAX_FILE_CHARS} 字符",
            )
        name = filename or problem.default_filename or "main.cpp"
        _check_name(name)
        file_items = [{"name": name, "content": source_code}]
    else:
        if not isinstance(files, list) or not files:
            raise _val_error("files 不能为空")
        if len(files) > MAX_FILES:
            raise ApiError(
                "PAYLOAD_TOO_LARGE",
                f"代码太长，请精简后重试：最多 {MAX_FILES} 个文件",
            )
        total = 0
        seen: set[str] = set()
        for item in files:
            name = item["name"]
            content = item["content"]
            _check_name(name)
            if name in seen:
                raise _val_error(f"文件名重复：{name}")
            seen.add(name)
            if not isinstance(content, str) or content.strip() == "":
                raise _val_error(f"源码为空：{name}")
            if len(content) > MAX_FILE_CHARS:
                raise ApiError(
                    "PAYLOAD_TOO_LARGE",
                    f"代码太长，请精简后重试：单文件上限 {MAX_FILE_CHARS} 字符",
                )
            total += len(content)
            file_items.append({"name": name, "content": content})
        if total > MAX_TOTAL_CHARS:
            raise ApiError(
                "PAYLOAD_TOO_LARGE",
                f"代码太长，请精简后重试：files 合计上限 {MAX_TOTAL_CHARS} 字符",
            )

    if mode is not None and mode not in ("acm", "oi"):
        raise _val_error("mode 只能是 acm 或 oi")

    # 多文件 make 构建题（如 P6）：必须走 files[] 且包含 Makefile
    if problem.build_mode == "make":
        if source_code is not None:
            raise _val_error("该题为多文件 make 构建，请用多文件提交（需包含 Makefile 与源文件）")
        names = {it["name"] for it in file_items}
        if not names & {"Makefile", "makefile", "GNUmakefile"}:
            raise _val_error("多文件 make 构建缺少 Makefile，请在提交文件中包含 Makefile")
    return file_items, (mode or problem.contest_type)


def _failed_report(problem, files: list[dict], mode: str, sid: str, message: str) -> dict:
    zeros = {
        "total": 0,
        "passed": 0,
        "pass_rate": 0.0,
        "score": 0.0,
        "max_score": float(problem.score),
        "partial_score": 0.0,
    }
    return reporter.make_report(
        submission_id=sid,
        problem_id=problem.id,
        problem_title=problem.title,
        mode=mode,
        submission="api",
        started_at=reporter.iso_now(),
        status="failed",
        verdict="SE",
        summary=zeros,
        cases=[],
        build_log=None,
        files=files,
        message=message,
    )


async def run_submission(
    problem_id: str, source_code, filename, files, mode, authorization: str | None = None
) -> dict:
    """POST /api/submissions 同步流水线，返回 SubmissionResult dict（201）。

    Δ3（G1 执行口径）：带 Authorization → 校验（无效/过期 401）→ 判题 + secret 代写入库；
    不带 → 匿名判题照常、不入库。判题结果永不因入库失败而报错。
    """
    ok, reason = problem_service.engine_status()
    if not ok:
        raise ApiError("ENGINE_UNAVAILABLE", f"判题引擎不可用，请检查本机编译环境：{reason}")

    # 认证兜底（前端负责登录拦截；这里 401 拦无效/过期 token），失败不占判题锁
    user_id = await auth_service.resolve_user_id(authorization)

    problem = problem_service.load_problem(problem_id)
    file_items, eff_mode = validate_submission(problem, source_code, filename, files, mode)

    if not _busy.acquire(blocking=False):
        raise ApiError("JUDGE_BUSY")  # 不排队，本地单机有意取舍
    released_by_callback = False
    try:
        sid = submission_store.new_sid(problem.id)
        workdir = Path(tempfile.mkdtemp(prefix="judge-api-"))

        def _pipeline() -> dict:
            try:
                names = []
                for item in file_items:
                    (workdir / item["name"]).write_text(item["content"], encoding="utf-8")
                    names.append(item["name"])
                return evaluate(
                    problem, workdir, names, eff_mode, "api", file_items, sid
                )
            finally:
                shutil.rmtree(workdir, ignore_errors=True)

        future = _executor.submit(_pipeline)
        timeout_s = get_max_submit_seconds()
        report: dict | None = None
        try:
            report = await asyncio.wait_for(asyncio.wrap_future(future), timeout=timeout_s)
        except asyncio.TimeoutError:
            # 整单超时：落 status=failed 报告；后台线程跑完后丢弃结果（不覆盖失败报告）
            future.add_done_callback(lambda _f: _busy.release())
            released_by_callback = True
            failed = _failed_report(problem, file_items, eff_mode, sid, f"整单判题超时（{timeout_s:g} 秒）被中止")
            failed["synced"] = False
            submission_store.save_report(failed)
            raise ApiError("JUDGE_TIMEOUT")
        except Exception as exc:
            raise ApiError("INTERNAL_ERROR", f"服务异常，请重试：{exc}")
    finally:
        if not released_by_callback:
            _busy.release()

    # 判题锁外入库（Δ3）：仅 status=finished 且有 user_id；失败只置 synced=false，绝不影响判题响应
    synced = False
    if report.get("status") == "finished" and user_id:
        synced = supabase_store.insert_submission(report, user_id)
    report["synced"] = bool(synced)
    submission_store.save_report(report)
    return report
