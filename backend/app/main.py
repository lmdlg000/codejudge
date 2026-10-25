# backend/app/main.py —— FastAPI 入口：挂路由 + StaticFiles + 异常→统一错误体
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from .config import VERSION, get_cors_origins, get_frontend_dist
from .errors import ApiError
from .routers import health, problems, submissions

app = FastAPI(title="CodeJudge", version=VERSION, docs_url="/api/docs", openapi_url="/api/openapi.json")

# CORS（Δ3）：JUDGE_CORS_ORIGINS 逗号分隔白名单（GH Pages origin + localhost:5173）；空 = 不限制
_cors_origins = get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins or ["*"],
    allow_credentials=bool(_cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态资源传输压缩（本地演示也走 gzip，减小 JS/CSS 体积）
app.add_middleware(GZipMiddleware, minimum_size=1024)


@app.middleware("http")
async def _asset_cache_headers(request: Request, call_next):
    """带内容哈希的 /assets/* 可长缓存；HTML 不缓存，保证发版即生效。"""
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/assets/"):
        response.headers.setdefault("Cache-Control", "public, max-age=31536000, immutable")
    elif path == "/" or path.endswith(".html"):
        response.headers.setdefault("Cache-Control", "no-cache")
    return response

app.include_router(health.router)
app.include_router(problems.router)
app.include_router(submissions.router)


# ---------- 统一错误体（所有非 2xx → {"error":{"code","message"}}） ----------

@app.exception_handler(ApiError)
async def _api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content=exc.body())


@app.exception_handler(RequestValidationError)
async def _validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    detail = "；".join(
        f"{'.'.join(str(p) for p in e.get('loc', ()))}: {e.get('msg', '')}" for e in exc.errors()
    ) or "请求体格式不符"
    return JSONResponse(
        status_code=400,
        content={"error": {"code": "VALIDATION_ERROR", "message": f"提交内容不合法，请检查后重试：{detail}"}},
    )


@app.exception_handler(StarletteHTTPException)
async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # 前端 history 回退：非 /api 的 GET 404 → index.html
    dist = get_frontend_dist()
    if (
        exc.status_code == 404
        and request.method in ("GET", "HEAD")
        and not request.url.path.startswith("/api")
        and (dist / "index.html").is_file()
    ):
        return FileResponse(dist / "index.html")
    code = "PROBLEM_NOT_FOUND" if exc.status_code == 404 else "INTERNAL_ERROR"
    message = exc.detail if isinstance(exc.detail, str) else "服务异常，请重试"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": message}},
    )


@app.exception_handler(Exception)
async def _unhandled_handler(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": f"服务异常，请重试：{exc}"}},
    )


# ---------- 前端静态资源（单端口演示） ----------
# /api/* 路由优先匹配；dist 不存在时不崩溃，返回起步提示

_DIST = get_frontend_dist()
if _DIST.is_dir() and (_DIST / "index.html").is_file():
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="frontend")
else:
    @app.get("/{full_path:path}", include_in_schema=False)
    async def _no_frontend(full_path: str) -> HTMLResponse:
        return HTMLResponse(
            "<!doctype html><meta charset='utf-8'><title>CodeJudge</title>"
            "<p style='font-family:sans-serif'>后端已就绪，但前端产物 <code>frontend/dist</code> 不存在。"
            "开发模式请运行 <code>npm run dev</code>（:5173）；"
            "或先 <code>cd frontend &amp;&amp; npm run build</code> 再刷新本页。"
            f"（请求路径：/{full_path}）</p>"
        )
