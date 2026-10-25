# backend/app/services/supabase_store.py —— secret 代写 submissions（site-spec 13.5，Δ3）
# 判题完成后经 SUPABASE_SECRET_KEY 管理端写入（绕过 RLS）；失败仅 synced=false + 记日志
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

from ..config import get_supabase_secret_key, get_supabase_url

logger = logging.getLogger("codejudge.supabase")

HTTP_TIMEOUT_S = 5


def _http_insert_submission(payload: dict) -> bool:
    """POST {SUPABASE_URL}/rest/v1/submissions（Bearer + apikey 均为 sb_secret_…）。

    绝不把 secret 写入日志；失败返回 False。
    """
    url = get_supabase_url().rstrip("/") + "/rest/v1/submissions"
    secret = get_supabase_secret_key()
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {secret}",
            "apikey": secret,
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            return 200 <= resp.status < 300
    except urllib.error.HTTPError as exc:
        # 只记状态码与错误码，不记请求头/密钥
        logger.warning("Supabase 写入被拒：HTTP %s（%s）", exc.code, url)
        return False
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        logger.warning("Supabase 写入失败：%s", type(exc).__name__)
        return False


def insert_submission(report: dict, user_id: str) -> bool:
    """把判题结果写入 Supabase submissions（id=sid，单一 ID 空间）。

    仅 status=finished 的结果由调用方送入；任何异常吞掉返回 False。
    """
    try:
        summary = report.get("summary") or {}
        payload = {
            "id": report["submission_id"],
            "user_id": user_id,
            "problem_id": report["problem_id"],
            "verdict": report["verdict"],
            "score": summary.get("score", 0),
            "summary": summary,
            "cases": report.get("cases") or [],
            "files": report.get("files") or [],
            "mode": report.get("mode") or report.get("contest_type"),
            "file_label": report.get("file_label") or "",
            "build_log": report.get("build_log"),
            "created_at": report.get("created_at") or report.get("started_at"),
        }
        return _http_insert_submission(payload)
    except Exception as exc:  # 入库失败绝不影响判题响应
        logger.warning("Supabase 写入异常：%s", type(exc).__name__)
        return False
