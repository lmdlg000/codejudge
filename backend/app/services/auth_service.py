# backend/app/services/auth_service.py —— Supabase JWT 校验（site-spec 13.1/13.5，Δ3）
# 有 Authorization 头 + supabase 已配置 → GET {SUPABASE_URL}/auth/v1/user 解析 user.id
# 失败/超时 → 401 UNAUTHORIZED；无头 → user_id=None 匿名继续
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

from ..config import get_supabase_secret_key, get_supabase_url, supabase_configured
from ..errors import ApiError

logger = logging.getLogger("codejudge.auth")

HTTP_TIMEOUT_S = 5  # 短超时：认证失败快速反馈，不拖判题

UNAUTHORIZED_MSG = "请先登录（登录状态可能已过期）"


def extract_bearer(authorization: str | None) -> str | None:
    """解析 Authorization: Bearer <token>。无头 → None；格式非法 → 401。"""
    if authorization is None or authorization.strip() == "":
        return None
    parts = authorization.strip().split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise ApiError("UNAUTHORIZED", UNAUTHORIZED_MSG)
    return parts[1].strip()


def _http_get_user(token: str) -> dict | None:
    """GET {SUPABASE_URL}/auth/v1/user（apikey=secret，Authorization=用户 access_token）。

    返回 {"id": ...}；网络失败/超时/非 200 → None（调用方转 401）。
    注意：绝不把 token / secret 写入日志。
    """
    url = get_supabase_url().rstrip("/") + "/auth/v1/user"
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "apikey": get_supabase_secret_key(),
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            if resp.status != 200:
                return None
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return None
    if isinstance(data, dict) and isinstance(data.get("id"), str) and data["id"]:
        return {"id": data["id"]}
    return None


async def resolve_user_id(authorization: str | None) -> str | None:
    """按 G1 执行口径解析提交者身份。

    - supabase 未配置：忽略任何头 → None（匿名判题不入库，13.4 交集降级）
    - 无 Authorization 头：None（匿名判题照常、不入库）
    - 有头且已配置：校验失败/超时 → 401 UNAUTHORIZED；成功 → user.id
    """
    if not supabase_configured():
        return None
    token = extract_bearer(authorization)
    if token is None:
        return None
    import asyncio

    try:
        user = await asyncio.to_thread(_http_get_user, token)
    except Exception:  # 认证层任何异常都视为无法认证（不外泄细节）
        raise ApiError("UNAUTHORIZED", UNAUTHORIZED_MSG)
    if not user:
        raise ApiError("UNAUTHORIZED", UNAUTHORIZED_MSG)
    return user["id"]
