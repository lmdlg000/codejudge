# core/reporter.py —— 控制台表格 + JSON 报告 + latest.json（requirements.md 三-7 / site-spec 8.3）
# 报告 = requirements 同构 + 扩展字段（submission_id/status/files/message/problem_title/mode/file_label）
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from .verdict import Verdict


def make_sid(pid: str, now: datetime | None = None, hex4: str | None = None) -> str:
    """sid 格式：YYYYMMDD-HHMMSS-<pid>-<4位hex>（site-spec 5.3）。"""
    import secrets

    ts = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    return f"{ts}-{pid}-{hex4 or secrets.token_hex(2)}"


def iso_now() -> str:
    """ISO 8601 本地时间、秒级（site-spec 5 日期格式）。"""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def file_label_of(files: list[dict], default_filename: str | None = None) -> str:
    """提交文件显示名：单文件取文件名；多文件取主文件名，判不出取「N 个文件」。"""
    names = [f["name"] for f in files]
    if len(names) == 1:
        return names[0]
    if not names:
        return "0 个文件"
    if default_filename and default_filename in names:
        return default_filename
    if "main.cpp" in names:
        return "main.cpp"
    cpps = [n for n in names if n.endswith(".cpp")]
    if len(cpps) == 1:
        return cpps[0]
    return f"{len(names)} 个文件"


def make_report(
    *,
    submission_id: str,
    problem_id: str,
    problem_title: str,
    mode: str,
    submission: str,
    started_at: str,
    status: str,
    verdict: str,
    summary: dict,
    cases: list[dict],
    build_log: str | None,
    files: list[dict],
    message: str | None = None,
) -> dict:
    """组装报告 dict（写盘与 API 响应共用一份结构）。"""
    return {
        # requirements 报告字段
        "problem_id": problem_id,
        "contest_type": mode,
        "submission": submission,
        "started_at": started_at,
        "summary": summary,
        "cases": cases,
        # site-spec 8.3 扩展字段
        "submission_id": submission_id,
        "problem_title": problem_title,
        "mode": mode,
        "created_at": started_at,
        "status": status,
        "verdict": verdict,
        "build_log": build_log,
        "files": files,
        "file_label": file_label_of(files),
        "message": message,
    }


def write_report(report: dict, reports_dir: str | Path) -> Path:
    """写 reports/<sid>.json；latest.json 原子替换为最新副本（Windows 无软链权限，用副本）。"""
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    sid = report["submission_id"]
    path = reports_dir / f"{sid}.json"
    _atomic_write_json(path, report)
    latest = reports_dir / "latest.json"
    tmp = reports_dir / "latest.json.tmp"
    _atomic_write_json(tmp, report)
    os.replace(tmp, latest)
    return path


def _atomic_write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def load_report(reports_dir: str | Path, sid: str) -> dict | None:
    path = Path(reports_dir) / f"{sid}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


# ---------------- 控制台输出 ----------------

def _fmt_num(x) -> str:
    """得分/权重显示：整数不带小数点，否则最多 2 位小数。"""
    f = float(x)
    if f == int(f):
        return str(int(f))
    return f"{f:.2f}".rstrip("0").rstrip(".")


def format_banner(summary: dict) -> str:
    """通用横幅（requirements 三-6）：通过 x/y · 通过率 z% · 得分 s/m。"""
    rate = summary["pass_rate"] * 100
    return (
        f"通过 {summary['passed']}/{summary['total']}"
        f" · 通过率 {_fmt_num(rate)}%"
        f" · 得分 {_fmt_num(summary['score'])}/{_fmt_num(summary['max_score'])}"
    )


def _pad(text: str, width: int) -> str:
    """按显示宽度补齐（中文按 2 列估算）。"""
    def w(s: str) -> int:
        return sum(2 if ord(ch) > 0x2E80 else 1 for ch in s)

    text = text if len(text) <= width * 2 else text[: width * 2 - 1] + "…"
    return text + " " * max(0, width - w(text))


def print_table(report: dict) -> None:
    """控制台逐用例表格（requirements 三-7 示例样式）。"""
    cols = [("用例", 10), ("判定", 6), ("耗时", 8), ("权重", 6), ("提示", 46)]
    top = "┬".join("─" * (w + 2) for _, w in cols)
    mid = "┼".join("─" * (w + 2) for _, w in cols)
    bot = "┴".join("─" * (w + 2) for _, w in cols)
    print(f"┌{top}┐")
    print("│ " + " │ ".join(_pad(n, w) for n, w in cols) + " │")
    print(f"├{mid}┤")
    for case in report["cases"]:
        msg = case.get("message") or ""
        row = [
            case["name"],
            str(case["verdict"]),
            f"{_fmt_num(case['time_ms'])}ms",
            _fmt_num(case["weight"]),
            msg.replace("\n", " ")[:60],
        ]
        print("│ " + " │ ".join(_pad(v, w) for v, (_, w) in zip(row, cols)) + " │")
    print(f"└{bot}┘")
    print(format_banner(report["summary"]))
    if report.get("build_log"):
        print("\n编译器输出（末 200 行）：")
        print(report["build_log"])
