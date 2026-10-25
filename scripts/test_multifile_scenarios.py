# scripts/test_multifile_scenarios.py —— 多文件提交评测 · 常见情景测试
# 对运行中的服务（默认 http://127.0.0.1:8000）逐场景发真实请求并断言。
# 覆盖：单文件回归 / 多文件 g++ / 多文件 make（P6）/ 各类拒绝路径 / 示例 API。
# 用法：python scripts/test_multifile_scenarios.py [base_url]
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")

# 绕过本机 HTTP 代理（代理会劫持 127.0.0.1）
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

P1_AC = """#include <bits/stdc++.h>
using namespace std;
int main() {
    long long w, d;
    cin >> w >> d;
    long long fee = 10;
    if (w > 1000) fee += 3 * ((w - 1000 + 499) / 500);
    if (d > 1000) fee += 12;
    else if (d > 500) fee += 5;
    cout << fee << "\\n";
    return 0;
}
"""

# P1 正确解的多文件拆分（main + 头 + 实现）
MF_MAIN = """#include <bits/stdc++.h>
#include "calc.h"
using namespace std;
int main() {
    long long w, d;
    cin >> w >> d;
    cout << calc_fee(w, d) << "\\n";
    return 0;
}
"""
MF_CALC_H = """#ifndef CALC_H
#define CALC_H
long long calc_fee(long long w, long long d);
#endif
"""
MF_CALC_CPP = """#include "calc.h"
long long calc_fee(long long w, long long d) {
    long long fee = 10;
    if (w > 1000) fee += 3 * ((w - 1000 + 499) / 500);
    if (d > 1000) fee += 12;
    else if (d > 500) fee += 5;
    return fee;
}
"""
# WA 版多文件（费率写错）
MF_CALC_CPP_WA = MF_CALC_CPP.replace("fee += 3 *", "fee += 2 *")
# CE 版多文件（语法错）
MF_MAIN_CE = '#include "calc.h"\nint main() { return 0 }\n'


def call(method: str, path: str, payload=None):
    req = urllib.request.Request(
        BASE + path,
        method=method,
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with OPENER.open(req, timeout=130) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(body) if body else None
        except json.JSONDecodeError:
            return e.code, None


def submit(files=None, source_code=None, filename=None, mode=None, pid="P1"):
    payload = {"problem_id": pid}
    if source_code is not None:
        payload["source_code"] = source_code
        if filename:
            payload["filename"] = filename
    if files is not None:
        payload["files"] = files
    if mode:
        payload["mode"] = mode
    return call("POST", "/api/submissions", payload)


RESULTS = []


def check(name: str, ok: bool, detail: str = ""):
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" —— {detail}" if detail else ""))


def err_code(body):
    return (body or {}).get("error", {}).get("code", "")


def err_msg(body):
    return (body or {}).get("error", {}).get("message", "")


def main():
    print(f"== 多文件提交评测场景测试 · {BASE} ==")

    # 0. 健康检查
    st, body = call("GET", "/api/health")
    check("健康检查 /api/health", st == 200 and body and body.get("status") == "ok", f"status={st}")

    # 1. 回归：单文件提交 P1 → AC
    st, body = submit(source_code=P1_AC, filename="main.cpp")
    check(
        "回归·单文件提交 P1 → AC",
        st == 201 and body.get("verdict") == "AC" and body.get("summary", {}).get("passed", 0) == body.get("summary", {}).get("total", -1),
        f"status={st} verdict={body.get('verdict') if body else None}",
    )

    # 2. 多文件 g++ 提交 P1（main.cpp + calc.h + calc.cpp）→ AC
    st, body = submit(files=[
        {"name": "main.cpp", "content": MF_MAIN},
        {"name": "calc.h", "content": MF_CALC_H},
        {"name": "calc.cpp", "content": MF_CALC_CPP},
    ])
    check(
        "多文件 g++ 提交 P1 → AC",
        st == 201 and body.get("verdict") == "AC",
        f"status={st} verdict={body.get('verdict') if body else None} files={len((body or {}).get('files', []))}",
    )

    # 3. 多文件 make 提交 P6（Makefile + inspector.cpp + util.h）→ AC【新能力核心】
    make_files = []
    import pathlib
    ex = pathlib.Path(__file__).resolve().parent.parent / "examples" / "P6_make"
    for f in sorted(ex.iterdir()):
        if f.is_file():
            make_files.append({"name": f.name, "content": f.read_text(encoding="utf-8")})
    st, body = submit(files=make_files, pid="P6")
    check(
        "多文件 make 提交 P6 → AC（P6 可在线交）",
        st == 201 and body.get("verdict") == "AC",
        f"status={st} verdict={body.get('verdict') if body else None} 用例={(body or {}).get('summary', {}).get('passed')}/{(body or {}).get('summary', {}).get('total')}",
    )

    # 4. P6 单文件提交 → 400（提示走多文件）
    st, body = submit(source_code=P1_AC, filename="main.cpp", pid="P6")
    check(
        "P6 单文件提交 → 400 并提示多文件",
        st == 400 and err_code(body) == "VALIDATION_ERROR" and "多文件" in err_msg(body),
        f"status={st} msg={err_msg(body)}",
    )

    # 5. P6 多文件缺 Makefile → 400
    st, body = submit(files=[{"name": "inspector.cpp", "content": "int main(){return 0;}"}], pid="P6")
    check(
        "P6 多文件缺 Makefile → 400",
        st == 400 and "Makefile" in err_msg(body),
        f"status={st} msg={err_msg(body)}",
    )

    # 6. 文件重名 → 400
    st, body = submit(files=[
        {"name": "a.cpp", "content": "int main(){}"},
        {"name": "a.cpp", "content": "int main(){}"},
    ])
    check("文件重名 → 400", st == 400 and "重复" in err_msg(body), f"status={st} msg={err_msg(body)}")

    # 7. 不安全文件名 → 400
    st, body = submit(files=[{"name": "../evil.cpp", "content": "int main(){}"}])
    check("路径穿越文件名 → 400", st == 400 and "文件名" in err_msg(body), f"status={st} msg={err_msg(body)}")

    # 8. 空内容文件 → 400
    st, body = submit(files=[
        {"name": "main.cpp", "content": "int main(){}"},
        {"name": "empty.h", "content": "   "},
    ])
    check("空内容文件 → 400", st == 400 and "空" in err_msg(body), f"status={st} msg={err_msg(body)}")

    # 9. 超过 20 个文件 → 413
    many = [{"name": f"f{i:02d}.cpp", "content": "int x;"} for i in range(21)]
    st, body = submit(files=many)
    check("21 个文件 → 413", st == 413 and err_code(body) == "PAYLOAD_TOO_LARGE", f"status={st}")

    # 10. 空源码 → 400
    st, body = submit(source_code="   ", filename="main.cpp")
    check("空源码 → 400", st == 400 and err_code(body) == "VALIDATION_ERROR", f"status={st}")

    # 11. files 与 source_code 同给 → 400
    st, body = call("POST", "/api/submissions", {
        "problem_id": "P1", "source_code": P1_AC,
        "files": [{"name": "a.cpp", "content": "int main(){}"}],
    })
    check("source_code 与 files 同给 → 400", st == 400, f"status={st} msg={err_msg(body)}")

    # 12. mode 覆盖：多文件 + mode=acm → 响应 mode=acm
    st, body = submit(files=[
        {"name": "main.cpp", "content": MF_MAIN},
        {"name": "calc.h", "content": MF_CALC_H},
        {"name": "calc.cpp", "content": MF_CALC_CPP},
    ], mode="acm")
    check(
        "多文件 + mode=acm 覆盖生效",
        st == 201 and body.get("mode") == "acm",
        f"status={st} mode={body.get('mode') if body else None}",
    )

    # 13. 多文件 CE → CE + build_log
    st, body = submit(files=[
        {"name": "main.cpp", "content": MF_MAIN_CE},
        {"name": "calc.h", "content": MF_CALC_H},
        {"name": "calc.cpp", "content": MF_CALC_CPP},
    ])
    check(
        "多文件 CE → CE 且 build_log 非空",
        st == 201 and body.get("verdict") == "CE" and bool(body.get("build_log")),
        f"status={st} verdict={body.get('verdict') if body else None}",
    )

    # 14. 多文件 WA → WA 且含行号提示（WA 用例未必排第一，逐用例找）
    st, body = submit(files=[
        {"name": "main.cpp", "content": MF_MAIN},
        {"name": "calc.h", "content": MF_CALC_H},
        {"name": "calc.cpp", "content": MF_CALC_CPP_WA},
    ])
    wa_msgs = [c.get("message", "") for c in (body or {}).get("cases", []) if c.get("verdict") == "WA"]
    msg = wa_msgs[0] if wa_msgs else ""
    check(
        "多文件 WA → WA 且提示含行号",
        st == 201 and body.get("verdict") == "WA" and any("行" in m for m in wa_msgs),
        f"status={st} verdict={body.get('verdict') if body else None} msg={msg[:60]}",
    )

    # 15. P6 示例 API 返回多文件结构（files[] 含 Makefile，expect=AC）
    st, body = call("GET", "/api/examples?problem_id=P6")
    items = (body or {}).get("items", [])
    mk = next((i for i in items if i.get("files")), None)
    names = {f["name"] for f in (mk.get("files") if mk else [])}
    check(
        "P6 示例 API 返回结构化多文件",
        st == 200 and mk is not None and "Makefile" in names and mk.get("expect") == "AC",
        f"status={st} files={sorted(names)} expect={mk.get('expect') if mk else None}",
    )

    # 16. 未知题目 → 404
    st, body = call("GET", "/api/problems/P9")
    check("未知题目 → 404", st == 404 and err_code(body) == "PROBLEM_NOT_FOUND", f"status={st}")

    # 17. 多文件提交回显（files[] 逐个回显）
    st, body = submit(files=[
        {"name": "main.cpp", "content": MF_MAIN},
        {"name": "calc.h", "content": MF_CALC_H},
        {"name": "calc.cpp", "content": MF_CALC_CPP},
    ])
    fnames = [f["name"] for f in (body or {}).get("files", [])]
    check(
        "提交结果回显全部文件",
        st == 201 and sorted(fnames) == ["calc.cpp", "calc.h", "main.cpp"],
        f"files={fnames}",
    )

    # 汇总
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print(f"\n== 汇总：{passed}/{total} 通过 ==")
    for name, ok, detail in RESULTS:
        if not ok:
            print(f"  ✗ {name} —— {detail}")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
