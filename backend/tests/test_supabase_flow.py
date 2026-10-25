# backend/tests/test_supabase_flow.py —— Δ3 Supabase 集成流（mock HTTP 层，可复跑）
# 运行：cd codejudge && python backend/tests/test_supabase_flow.py
# 不连真实 Supabase：monkeypatch auth_service._http_get_user / supabase_store._http_insert_submission
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from backend.app.main import app  # noqa: E402
from backend.app.services import auth_service, supabase_store  # noqa: E402

client = TestClient(app)

PASS, FAIL = [], []


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASS if cond else FAIL).append(name)
    print(f"[{'OK ' if cond else 'FAIL'}] {name}" + ("" if cond else f"  {detail}"))


def _src() -> str:
    return (ROOT / "examples" / "P1_ac.cpp").read_text(encoding="utf-8")


def main() -> int:
    saved_env = {k: os.environ.get(k) for k in ("SUPABASE_URL", "SUPABASE_SECRET_KEY")}
    saved_http = (auth_service._http_get_user, supabase_store._http_insert_submission)

    # mock HTTP 层
    captured_payloads: list[dict] = []
    mode = {"auth": "reject", "insert": "ok"}

    def fake_get_user(token: str):
        if mode["auth"] == "raise":
            raise RuntimeError("network down")
        if mode["auth"] == "ok" and token == "good-token":
            return {"id": "11111111-2222-3333-4444-555555555555"}
        return None

    def fake_insert(payload: dict) -> bool:
        if mode["insert"] == "raise":
            raise RuntimeError("boom")
        if mode["insert"] == "fail":
            return False
        captured_payloads.append(dict(payload))
        return True

    auth_service._http_get_user = fake_get_user
    supabase_store._http_insert_submission = fake_insert

    try:
        # ── A. 未配置 Supabase（local 模式基线）────────────────────
        os.environ.pop("SUPABASE_URL", None)
        os.environ.pop("SUPABASE_SECRET_KEY", None)

        j = client.get("/api/health").json()
        check("A1 未配置：health.supabase_configured=false", j.get("supabase_configured") is False, str(j))

        r = client.post("/api/submissions", json={"problem_id": "P1", "source_code": _src()})
        j = r.json()
        check("A2 未配置：匿名提交 201", r.status_code == 201, str(r.status_code))
        check("A3 未配置：synced=false 且判题正常 AC", j.get("synced") is False and j["verdict"] == "AC", str(j.get("synced")))

        # 未配置时即使带无效 token 也照旧匿名判题（13.4 交集降级），不 401
        r = client.post("/api/submissions", json={"problem_id": "P1", "source_code": _src()},
                        headers={"Authorization": "Bearer invalid-token"})
        check("A4 未配置：带 token 不 401、照常判题 synced=false",
              r.status_code == 201 and r.json()["synced"] is False and r.json()["verdict"] == "AC",
              f"{r.status_code} {r.text[:120]}")

        # ── B. 配置态（mock 校验与写入）────────────────────────────
        os.environ["SUPABASE_URL"] = "https://fake-project.supabase.co"
        os.environ["SUPABASE_SECRET_KEY"] = "sb_secret_fake_for_tests_only_not_real"

        j = client.get("/api/health").json()
        check("B1 已配置：health.supabase_configured=true", j.get("supabase_configured") is True, str(j))

        # 无效 token → 401
        r = client.post("/api/submissions", json={"problem_id": "P1", "source_code": _src()},
                        headers={"Authorization": "Bearer invalid-token"})
        e = r.json().get("error", {})
        check("B2 无效 token → 401 UNAUTHORIZED", r.status_code == 401 and e.get("code") == "UNAUTHORIZED",
              f"{r.status_code} {e}")
        check("B3 401 文案冻结", e.get("message") == "请先登录（登录状态可能已过期）", str(e))

        # 非 Bearer 格式 → 401
        r = client.post("/api/submissions", json={"problem_id": "P1", "source_code": _src()},
                        headers={"Authorization": "Token abc"})
        check("B4 非 Bearer 头 → 401", r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHORIZED",
              f"{r.status_code}")

        # 校验层抛异常 → 401（不外泄、不 500）
        mode["auth"] = "raise"
        r = client.post("/api/submissions", json={"problem_id": "P1", "source_code": _src()},
                        headers={"Authorization": "Bearer good-token"})
        check("B5 校验层异常 → 401（不 500）", r.status_code == 401, f"{r.status_code}")
        mode["auth"] = "ok"

        # 有效 token + 写入成功 → synced=true，payload 形态正确
        r = client.post("/api/submissions", json={"problem_id": "P1", "source_code": _src()},
                        headers={"Authorization": "Bearer good-token"})
        j = r.json()
        check("B6 有效 token + 写入成功 → 201 synced=true",
              r.status_code == 201 and j.get("synced") is True and j["verdict"] == "AC", str(j.get("synced")))
        if captured_payloads:
            p = captured_payloads[-1]
            expect_keys = {"id", "user_id", "problem_id", "verdict", "score", "summary", "cases",
                           "files", "mode", "file_label", "build_log", "created_at"}
            check("B7 入库 payload 字段齐全", set(p.keys()) == expect_keys, str(set(p.keys()) ^ expect_keys))
            check("B8 ID 单一空间（id=sid=响应 submission_id）",
                  p["id"] == j["submission_id"] and p["id"] == j["submission_id"],
                  f"{p.get('id')} vs {j.get('submission_id')}")
            check("B9 user_id 取自校验通过的 JWT",
                  p["user_id"] == "11111111-2222-3333-4444-555555555555", str(p.get("user_id")))
            check("B10 payload summary/cases/files 与响应一致",
                  p["summary"] == j["summary"] and len(p["cases"]) == len(j["cases"]) == 8
                  and p["mode"] == j["mode"] and p["file_label"] == "main.cpp",
                  f"{p['mode']} {p['file_label']}")
        else:
            check("B7 入库 payload 字段齐全", False, "未捕获写入 payload")

        # 有效 token + 写入失败 → 201 synced=false（判题结果不受影响）
        mode["insert"] = "fail"
        r = client.post("/api/submissions", json={"problem_id": "P1", "source_code": _src()},
                        headers={"Authorization": "Bearer good-token"})
        j = r.json()
        check("B11 写入失败 → 201 synced=false 且判题正常",
              r.status_code == 201 and j.get("synced") is False and j["verdict"] == "AC"
              and j["summary"]["score"] == 100, f"{r.status_code} {j.get('synced')}")

        # 写入层抛异常 → 同样 201 synced=false
        mode["insert"] = "raise"
        r = client.post("/api/submissions", json={"problem_id": "P1", "source_code": _src()},
                        headers={"Authorization": "Bearer good-token"})
        j = r.json()
        check("B12 写入层异常 → 201 synced=false（永不 500）",
              r.status_code == 201 and j.get("synced") is False and j["verdict"] == "AC", f"{r.status_code}")
        mode["insert"] = "ok"

        # 匿名（配置态下不带头）→ 照常判题不入库
        r = client.post("/api/submissions", json={"problem_id": "P1", "source_code": _src()})
        j = r.json()
        check("B13 配置态匿名提交照常 201 synced=false",
              r.status_code == 201 and j.get("synced") is False, f"{r.status_code} {j.get('synced')}")

        # GET 回查与 POST 同构（含 synced 字段持久化）
        sid = j["submission_id"]
        r2 = client.get(f"/api/submissions/{sid}")
        check("B14 报告回查含 synced（与 POST 同构）",
              r2.status_code == 200 and r2.json().get("synced") is False
              and r2.json()["submission_id"] == sid, str(r2.status_code))

    finally:
        auth_service._http_get_user, supabase_store._http_insert_submission = saved_http
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    print(f"\n== 通过 {len(PASS)} 项 / 失败 {len(FAIL)} 项 ==")
    if FAIL:
        print("失败清单:", FAIL)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
