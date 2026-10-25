# backend/app/config.py —— 环境变量读取（site-spec 6 环境变量表，代码只引用名）
from __future__ import annotations

import os
from pathlib import Path

# codejudge/ 项目根 = 引擎根
PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_HOST = "JUDGE_HOST"
ENV_PORT = "JUDGE_PORT"
ENV_REPORTS_DIR = "JUDGE_REPORTS_DIR"
ENV_MAX_SUBMIT_SECONDS = "JUDGE_MAX_SUBMIT_SECONDS"
# Δ3 用户系统（Supabase，site-spec 13.3）：secret 只在后端环境，绝不进前端/仓库/日志
ENV_SUPABASE_URL = "SUPABASE_URL"
ENV_SUPABASE_SECRET_KEY = "SUPABASE_SECRET_KEY"
ENV_CORS_ORIGINS = "JUDGE_CORS_ORIGINS"

VERSION = "1.0.0"


def get_host() -> str:
    return os.environ.get(ENV_HOST, "127.0.0.1")


def get_port() -> int:
    try:
        return int(os.environ.get(ENV_PORT, "8000"))
    except ValueError:
        return 8000


def get_reports_dir() -> Path:
    """报告目录：JUDGE_REPORTS_DIR 可覆盖（相对项目根或绝对路径），默认 reports/。"""
    raw = os.environ.get(ENV_REPORTS_DIR, "reports")
    p = Path(raw)
    return p if p.is_absolute() else (PROJECT_ROOT / p)


def get_max_submit_seconds() -> float:
    try:
        return float(os.environ.get(ENV_MAX_SUBMIT_SECONDS, "120"))
    except ValueError:
        return 120.0


def get_problems_dir() -> Path:
    return PROJECT_ROOT / "problems"


def get_examples_dir() -> Path:
    return PROJECT_ROOT / "examples"


def get_frontend_dist() -> Path:
    return PROJECT_ROOT / "frontend" / "dist"


# ---------- Supabase（Δ3） ----------

def get_supabase_url() -> str:
    return os.environ.get(ENV_SUPABASE_URL, "").strip()


def get_supabase_secret_key() -> str:
    return os.environ.get(ENV_SUPABASE_SECRET_KEY, "").strip()


def supabase_configured() -> bool:
    """SUPABASE_URL 与 SUPABASE_SECRET_KEY 均已配置（site-spec 13.4 后端判定）。"""
    return bool(get_supabase_url() and get_supabase_secret_key())


def get_cors_origins() -> list[str]:
    """JUDGE_CORS_ORIGINS 逗号分隔；空 = 不限制（本地现状）。"""
    raw = os.environ.get(ENV_CORS_ORIGINS, "")
    return [o.strip() for o in raw.split(",") if o.strip()]
