# scripts/smoke_api.py —— API 冒烟矩阵（对照 site-spec 5 契约逐字段断言）
# 前置：uvicorn backend.app.main:app 已在 127.0.0.1:8000 运行
from __future__ import annotations

import copy
import json
import sys
import threading
import time

import httpx

BASE = "http://127.0.0.1:8000"
PASS, FAIL = [], []

CASE_FIELDS = ["name", "verdict", "time_ms", "exit_code", "weight", "message", "signal", "timed_out", "stderr_tail"]
SUMMARY_FIELDS = ["total", "passed", "pass_rate", "score", "max_score", "partial_score"]
RESULT_FIELDS = ["submission_id", "problem_id", "problem_title", "mode", "created_at", "status", "verdict",
                 "summary", "cases", "build_log", "files", "message", "synced"]
SUMMARY_ROW_FIELDS = ["submission_id", "problem_id", "problem_title", "file_label", "created_at", "mode", "verdict", "summary"]
PROBLEM_SUMMARY_FIELDS = ["id", "title", "contest_type", "score", "test_count", "time_limit_ms",
                          "memory_limit_mb", "build_mode", "topic", "difficulty"]


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASS if cond else FAIL).append(name)
    print(f"[{'OK ' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail and not cond else ""))


def err_of(resp) -> dict:
    try:
        return resp.json().get("error", {})
    except Exception:
        return {}


def main() -> int:
    # trust_env=False：忽略 HTTP_PROXY 等环境变量，强制本机直连
    c = httpx.Client(base_url=BASE, timeout=180, trust_env=False)

    # 1. health
    r = c.get("/api/health")
    j = r.json()
    check("GET /api/health 200", r.status_code == 200, str(r.status_code))
    check("health 字段齐全", set(j) == {"status", "engine", "version", "problem_count", "supabase_configured"}, str(j))
    check("health.engine=ready problem_count=6", j.get("engine") == "ready" and j.get("problem_count") == 6, str(j))
    check("health.supabase_configured=false（未配置基线）", j.get("supabase_configured") is False, str(j))

    # 2. problems 列表
    r = c.get("/api/problems")
    j = r.json()
    check("GET /api/problems 200", r.status_code == 200)
    check("problems total=6", j.get("total") == 6, str(j.get("total")))
    ok_fields = all(set(item) == set(PROBLEM_SUMMARY_FIELDS) for item in j["items"])
    check("ProblemSummary 字段逐名一致", ok_fields, str(j["items"][0] if j["items"] else j))
    p1 = next(i for i in j["items"] if i["id"] == "P1")
    check("P1 topic/difficulty 非空（G2 增补）", p1["topic"] == "分支/分段计费" and p1["difficulty"] == "入门", str(p1))
    check("P3 acm/1500ms、P5 acm/2000ms",
          next(i for i in j["items"] if i["id"] == "P3")["contest_type"] == "acm"
          and next(i for i in j["items"] if i["id"] == "P3")["time_limit_ms"] == 1500
          and next(i for i in j["items"] if i["id"] == "P5")["time_limit_ms"] == 2000)

    # 3. 问题详情
    r = c.get("/api/problems/P1")
    j = r.json()
    check("GET /api/problems/P1 200", r.status_code == 200)
    detail_fields = ["id", "title", "contest_type", "score", "compare_mode", "limits", "build",
                     "statement_md", "samples", "test_count"]
    check("ProblemDetail 字段逐名一致", set(j) == set(detail_fields), str(set(j)))
    check("samples 5 组且含 input/output", len(j["samples"]) == 5
          and set(j["samples"][0]) == {"input", "output"}, str(len(j.get("samples", []))))
    check("build.mode=g++ default_filename=main.cpp",
          j["build"]["mode"] == "g++" and j["build"]["default_filename"] == "main.cpp", str(j["build"]))

    # 4. 404 PROBLEM_NOT_FOUND
    r = c.get("/api/problems/P9")
    e = err_of(r)
    check("GET /api/problems/P9 → 404 PROBLEM_NOT_FOUND", r.status_code == 404 and e.get("code") == "PROBLEM_NOT_FOUND", str((r.status_code, e)))

    # 5. 提交判题（AC 全过）
    src_ac = open("examples/P1_ac.cpp", encoding="utf-8").read()
    r = c.post("/api/submissions", json={"problem_id": "P1", "source_code": src_ac})
    j = r.json()
    check("POST /api/submissions 201", r.status_code == 201, str(r.status_code))
    check("SubmissionResult 字段逐名一致", set(j) == set(RESULT_FIELDS), str(set(j) ^ set(RESULT_FIELDS)))
    check("summary 字段逐名一致", set(j["summary"]) == set(SUMMARY_FIELDS), str(j["summary"]))
    check("CaseResult 字段逐名一致", all(set(c1) == set(CASE_FIELDS) for c1 in j["cases"]), str(j["cases"][0]))
    sid_ok = len(j["submission_id"].split("-")) == 4 and j["submission_id"].split("-")[2] == "P1"
    check("sid 格式 YYYYMMDD-HHMMSS-P1-xxxx", sid_ok, j["submission_id"])
    check("AC 提交：8/8 全 AC 得 100", j["verdict"] == "AC" and j["summary"]["score"] == 100
          and j["summary"]["passed"] == j["summary"]["total"] == 8, str(j["summary"]))
    check("不带 Authorization 提交 201 且 synced=false（Δ3）", j.get("synced") is False, str(j.get("synced")))
    check("files 回显 1 项（单文件）", len(j["files"]) == 1 and j["files"][0]["name"] == "main.cpp", str(j["files"][:1]))
    check("created_at ISO 秒级", len(j["created_at"]) == 19 and "T" in j["created_at"], j["created_at"])
    sid_ac = j["submission_id"]

    # 6. 空源码 → 400
    r = c.post("/api/submissions", json={"problem_id": "P1", "source_code": ""})
    e = err_of(r)
    check("POST 空源码 → 400 VALIDATION_ERROR", r.status_code == 400 and e.get("code") == "VALIDATION_ERROR", str((r.status_code, e)))

    # 7. source_code 与 files 都给 / 都不给 → 400
    r = c.post("/api/submissions", json={"problem_id": "P1"})
    check("POST 两者皆空 → 400", r.status_code == 400 and err_of(r).get("code") == "VALIDATION_ERROR", str(r.status_code))
    r = c.post("/api/submissions", json={"problem_id": "P1", "source_code": "int main(){}", "files": [{"name": "a.cpp", "content": "x"}]})
    check("POST 两者都给 → 400", r.status_code == 400 and err_of(r).get("code") == "VALIDATION_ERROR", str(r.status_code))

    # 8. P6 多文件 make 构建：单文件拒绝 / 缺 Makefile 拒绝（多文件提交已开放）
    r = c.post("/api/submissions", json={"problem_id": "P6", "source_code": "int main(){}"})
    e = err_of(r)
    check("POST P6 单文件 → 400 提示多文件", r.status_code == 400 and e.get("code") == "VALIDATION_ERROR"
          and "多文件" in e.get("message", ""), str((r.status_code, e)))
    r = c.post("/api/submissions", json={"problem_id": "P6", "files": [{"name": "inspector.cpp", "content": "int main(){}"}]})
    e = err_of(r)
    check("POST P6 缺 Makefile → 400", r.status_code == 400 and "Makefile" in e.get("message", ""),
          str((r.status_code, e)))

    # 9. 文件名非法 → 400
    r = c.post("/api/submissions", json={"problem_id": "P1", "source_code": "int main(){}", "filename": "../evil.cpp"})
    check("POST 非法文件名 → 400", r.status_code == 400 and err_of(r).get("code") == "VALIDATION_ERROR", str(r.status_code))

    # 10. 体积超限 → 413
    r = c.post("/api/submissions", json={"problem_id": "P1", "source_code": "a" * 70000})
    e = err_of(r)
    check("POST 单文件 >65536 → 413 PAYLOAD_TOO_LARGE", r.status_code == 413 and e.get("code") == "PAYLOAD_TOO_LARGE", str((r.status_code, e)))
    r = c.post("/api/submissions", json={"problem_id": "P1", "files": [{"name": f"f{i}.cpp", "content": "x" * 60000} for i in range(5)]})
    check("POST files 合计 >262144 → 413", r.status_code == 413 and err_of(r).get("code") == "PAYLOAD_TOO_LARGE", str(r.status_code))

    # 11. WA 提交（判定语义走 API）
    src_wa = open("examples/P1_wa.cpp", encoding="utf-8").read()
    r = c.post("/api/submissions", json={"problem_id": "P1", "source_code": src_wa})
    j = r.json()
    check("WA 提交 verdict=WA 且 message 含行号", r.status_code == 201 and j["verdict"] == "WA"
          and "第 1 行不一致" in j["cases"][0]["message"], str(j.get("cases", [{}])[0].get("message")))
    sid_wa = j["submission_id"]

    # 12. CE 提交（build_log 非空）
    src_ce = open("examples/P1_ce.cpp", encoding="utf-8").read()
    r = c.post("/api/submissions", json={"problem_id": "P1", "source_code": src_ce})
    j = r.json()
    check("CE 提交：全用例 CE + build_log 非空", r.status_code == 201 and j["verdict"] == "CE"
          and j["build_log"] and all(c1["verdict"] == "CE" for c1 in j["cases"]), str(j.get("build_log", ""))[:80])

    # 13. 历史列表
    r = c.get("/api/submissions")
    j = r.json()
    check("GET /api/submissions 200 {items,total}", r.status_code == 200 and set(j) == {"items", "total"})
    check("SubmissionSummary 字段逐名一致", all(set(it) == set(SUMMARY_ROW_FIELDS) for it in j["items"]), str(j["items"][0]))
    check("file_label 已持久化", all("file_label" in it and it["file_label"] for it in j["items"]), str(j["items"][0]))
    times = [it["created_at"] for it in j["items"]]
    check("历史倒序（新→旧）", times == sorted(times, reverse=True), str(times[:3]))
    r = c.get("/api/submissions", params={"problem_id": "P2"})
    check("problem_id 过滤 total=0", r.json()["total"] == 0, str(r.json()))
    r = c.get("/api/submissions", params={"limit": 2})
    check("limit 生效（items≤2）", len(r.json()["items"]) <= 2)
    r = c.get("/api/submissions", params={"limit": 0})
    check("limit=0 → 400 VALIDATION_ERROR", r.status_code == 400 and err_of(r).get("code") == "VALIDATION_ERROR", str(r.status_code))
    r = c.get("/api/submissions", params={"offset": -1})
    check("offset=-1 → 400", r.status_code == 400, str(r.status_code))

    # 14. 单条查询（与 POST 同构）
    r = c.get(f"/api/submissions/{sid_ac}")
    j = r.json()
    check("GET /api/submissions/{sid} 200 与 POST 同构", r.status_code == 200 and set(j) == set(RESULT_FIELDS)
          and j["submission_id"] == sid_ac and j["verdict"] == "AC", str(r.status_code))
    r = c.get("/api/submissions/20250101-000000-P1-dead")
    check("未知 sid → 404 SUBMISSION_NOT_FOUND", r.status_code == 404
          and err_of(r).get("code") == "SUBMISSION_NOT_FOUND", str((r.status_code, err_of(r))))

    # 15. examples
    r = c.get("/api/examples", params={"problem_id": "P1"})
    j = r.json()
    expects = {i["name"]: i["expect"] for i in j["items"]}
    check("GET /api/examples?problem_id=P1 → 7 项", r.status_code == 200 and len(j["items"]) == 7, str(list(expects)))
    check("expect 映射 ac→AC … ce→CE，P1_make/→make",
          expects.get("P1_ac.cpp") == "AC" and expects.get("P1_wa.cpp") == "WA"
          and expects.get("P1_ce.cpp") == "CE" and expects.get("P1_make/") == "make", str(expects))
    r = c.get("/api/examples")
    check("examples 缺 problem_id → 400", r.status_code == 400 and err_of(r).get("code") == "VALIDATION_ERROR")
    r = c.get("/api/examples", params={"problem_id": "P9"})
    check("examples 未知题 → 404", r.status_code == 404)

    # 16. 并发 429 JUDGE_BUSY
    results = {}

    def _slow():
        t0 = time.time()
        resp = c.post("/api/submissions", json={"problem_id": "P1", "source_code": src_ac})
        results["slow"] = (resp.status_code, time.time() - t0)

    th = threading.Thread(target=_slow)
    th.start()
    time.sleep(0.8)  # 等第一单进入判题
    r = c.post("/api/submissions", json={"problem_id": "P1", "source_code": src_ac})
    e = err_of(r)
    check("并发第二单 → 429 JUDGE_BUSY", r.status_code == 429 and e.get("code") == "JUDGE_BUSY", str((r.status_code, e)))
    th.join()
    check("第一单正常完成 201", results.get("slow", (0,))[0] == 201, str(results))

    # 17. 历史可查（B8 重启后仍可查——落盘校验）
    r = c.get(f"/api/submissions/{sid_wa}")
    check("报告落盘可回查", r.status_code == 200 and r.json()["verdict"] == "WA")

    print(f"\n== 通过 {len(PASS)} 项 / 失败 {len(FAIL)} 项 ==")
    if FAIL:
        print("失败清单:", FAIL)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
