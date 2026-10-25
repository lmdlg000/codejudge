# backend/tests/test_contract.py —— 接口契约测试（对照 site-spec 5 逐字段断言）
# 运行方式：cd codejudge && python backend/tests/test_contract.py
# （也可 pytest backend/tests/test_contract.py；判定走真实流水线，约 30s）
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from backend.app.main import app  # noqa: E402

client = TestClient(app)

CASE_FIELDS = {"name", "verdict", "time_ms", "exit_code", "weight", "message", "signal", "timed_out", "stderr_tail"}
SUMMARY_FIELDS = {"total", "passed", "pass_rate", "score", "max_score", "partial_score"}
RESULT_FIELDS = {"submission_id", "problem_id", "problem_title", "mode", "created_at", "status", "verdict",
                 "summary", "cases", "build_log", "files", "message", "synced"}


def _src(name: str) -> str:
    return (ROOT / "examples" / name).read_text(encoding="utf-8")


def test_health_contract() -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    assert set(r.json()) == {"status", "engine", "version", "problem_count", "supabase_configured"}
    assert r.json()["engine"] == "ready"
    assert r.json()["supabase_configured"] is False  # 未配置 Supabase（回归基线）


def test_problems_contract() -> None:
    r = client.get("/api/problems")
    assert r.status_code == 200
    j = r.json()
    assert j["total"] == 6
    assert set(j["items"][0]) == {"id", "title", "contest_type", "score", "test_count", "time_limit_ms",
                                  "memory_limit_mb", "build_mode", "topic", "difficulty"}


def test_problem_detail_and_404() -> None:
    r = client.get("/api/problems/P1")
    j = r.json()
    assert r.status_code == 200
    assert set(j) == {"id", "title", "contest_type", "score", "compare_mode", "limits", "build",
                      "statement_md", "samples", "test_count"}
    assert len(j["samples"]) == 5
    r = client.get("/api/problems/P9")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "PROBLEM_NOT_FOUND"


def test_submission_ac_and_shape() -> None:
    r = client.post("/api/submissions", json={"problem_id": "P1", "source_code": _src("P1_ac.cpp")})
    assert r.status_code == 201
    j = r.json()
    assert set(j) == RESULT_FIELDS
    assert set(j["summary"]) == SUMMARY_FIELDS
    assert all(set(c) == CASE_FIELDS for c in j["cases"])
    assert j["verdict"] == "AC" and j["summary"]["score"] == 100
    assert j["synced"] is False  # 未配置/未带 token → 不入库（G1 口径 2）


def test_submission_rejects() -> None:
    assert client.post("/api/submissions", json={"problem_id": "P1", "source_code": ""}).status_code == 400
    assert client.post("/api/submissions", json={"problem_id": "P1"}).status_code == 400
    r = client.post("/api/submissions", json={"problem_id": "P6", "source_code": "int main(){}"})
    assert r.status_code == 400 and "多文件" in r.json()["error"]["message"]
    r = client.post(
        "/api/submissions",
        json={"problem_id": "P6", "files": [{"name": "inspector.cpp", "content": "int main(){}"}]},
    )
    assert r.status_code == 400 and "Makefile" in r.json()["error"]["message"]
    r = client.post("/api/submissions", json={"problem_id": "P1", "source_code": "a" * 70000})
    assert r.status_code == 413 and r.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
    r = client.post("/api/submissions", json={"problem_id": "P1", "source_code": "x", "filename": "../x.cpp"})
    assert r.status_code == 400


def test_submission_list_and_get() -> None:
    r = client.post("/api/submissions", json={"problem_id": "P1", "source_code": _src("P1_wa.cpp")})
    sid = r.json()["submission_id"]
    assert r.json()["verdict"] == "WA"
    row = client.get("/api/submissions", params={"problem_id": "P1"}).json()
    assert row["total"] >= 1
    item = next(i for i in row["items"] if i["submission_id"] == sid)
    assert set(item) == {"submission_id", "problem_id", "problem_title", "file_label",
                         "created_at", "mode", "verdict", "summary"}
    assert client.get(f"/api/submissions/{sid}").json()["verdict"] == "WA"
    assert client.get("/api/submissions/20250101-000000-P1-dead").status_code == 404
    assert client.get("/api/submissions", params={"limit": 0}).status_code == 400


def test_examples_contract() -> None:
    r = client.get("/api/examples", params={"problem_id": "P1"})
    assert r.status_code == 200
    names = {i["name"]: i["expect"] for i in r.json()["items"]}
    assert names["P1_ac.cpp"] == "AC"
    assert names["P1_make/"] == "make"
    assert client.get("/api/examples").status_code == 400
    assert client.get("/api/examples", params={"problem_id": "P9"}).status_code == 404


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"[OK ] {fn.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"[FAIL] {fn.__name__}: {exc}")
    print(f"== {len(tests) - failed}/{len(tests)} 通过 ==")
    sys.exit(1 if failed else 0)
