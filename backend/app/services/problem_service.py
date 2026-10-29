# backend/app/services/problem_service.py —— 题目加载/样例提取（复用 core.problem + core.importer）
from __future__ import annotations

import shutil
from pathlib import Path

from core.importer import extract_samples
from core.problem import Problem, ProblemError, ProblemNotFound, problem_id_key

from ..config import get_examples_dir, get_problems_dir
from ..errors import ApiError


def engine_status() -> tuple[bool, str]:
    """引擎就绪检查：g++/make 在 PATH 且题目可加载（site-spec B6）。"""
    missing = [tool for tool in ("g++", "make") if shutil.which(tool) is None]
    if missing:
        return False, f"缺少编译工具：{', '.join(missing)}（请安装并加入 PATH）"
    try:
        problems = list_problems_raw()
    except ProblemError as exc:
        return False, f"题目数据加载失败：{exc}"
    if not problems:
        return False, "problems/ 下没有可用题目"
    return True, "ready"


def load_problem(pid: str) -> Problem:
    try:
        return Problem.load(pid, get_problems_dir())
    except ProblemNotFound:
        raise ApiError("PROBLEM_NOT_FOUND", f"题目不存在：{pid}")
    except ProblemError as exc:
        # 题目存在但数据损坏 → 500（site-spec：加载层修复前不外泄细节结构）
        raise ApiError("INTERNAL_ERROR", f"题目数据没读出来：{exc}")


def list_problems_raw() -> list[Problem]:
    problems_dir = get_problems_dir()
    out: list[Problem] = []
    errors: list[str] = []
    if not problems_dir.is_dir():
        raise ProblemError(f"找不到题目目录 {problems_dir}")
    for entry in sorted(problems_dir.iterdir(), key=lambda p: problem_id_key(p.name)):
        if entry.is_dir() and (entry / "problem.json").is_file():
            try:
                out.append(Problem.load(entry.name, problems_dir))
            except (ProblemNotFound, ProblemError) as exc:
                errors.append(str(exc))
    if not out and errors:
        raise ProblemError(errors[0])
    return out


def problem_summary(problem: Problem) -> dict:
    return {
        "id": problem.id,
        "title": problem.title,
        "contest_type": problem.contest_type,
        "score": problem.score,
        "test_count": len(problem.tests),
        "time_limit_ms": problem.default_time_ms,
        "memory_limit_mb": problem.default_memory_mb,
        "build_mode": problem.build_mode,
        "topic": problem.topic,
        "difficulty": problem.difficulty,
    }


def problem_detail(problem: Problem) -> dict:
    statement_md = (problem.root / "statement.md").read_text(encoding="utf-8")
    samples = [
        {"input": i, "output": o} for i, o in extract_samples(statement_md)
    ]
    build = problem.build
    return {
        "id": problem.id,
        "title": problem.title,
        "contest_type": problem.contest_type,
        "score": problem.score,
        "compare_mode": problem.compare_mode,
        "limits": {
            "time_ms": problem.default_time_ms,
            "memory_mb": problem.default_memory_mb,
        },
        "build": {
            "mode": problem.build_mode,
            "command": build.get("command", ""),
            "src": build.get("src"),
            "default_filename": problem.default_filename,
        },
        "statement_md": statement_md,
        "samples": samples,
        "test_count": len(problem.tests),
    }


_EXPECT_BY_SUFFIX = {
    "ac": "AC",
    "wa": "WA",
    "pe": "PE",
    "tle": "TLE",
    "re": "RE",
    "ce": "CE",
}


def examples_for(pid: str) -> list[dict]:
    """examples/ 演示文件（site-spec B10）：P1 六条判定路径 + *_make/ 多文件套件。"""
    problem = load_problem(pid)  # 题目不存在 → 404
    ex_dir = get_examples_dir()
    items: list[dict] = []
    for suffix, expect in _EXPECT_BY_SUFFIX.items():
        path = ex_dir / f"{pid}_{suffix}.cpp"
        if path.is_file():
            items.append({
                "name": path.name,
                "content": path.read_text(encoding="utf-8", errors="replace"),
                "expect": expect,
            })
    make_dir = ex_dir / f"{pid}_make"
    if make_dir.is_dir():
        files: list[dict] = []
        parts: list[str] = []
        for f in sorted(make_dir.iterdir()):
            if f.is_file():
                content = f.read_text(encoding="utf-8", errors="replace")
                files.append({"name": f.name, "content": content})
                parts.append(f"// ===== {f.name} =====\n{content}")
        if files:
            items.append({
                "name": f"{pid}_make/",
                "content": "\n\n".join(parts),
                # make 题的整套示例即可直接判出 AC；g++ 题仅演示构建链路
                "expect": "AC" if problem.build_mode == "make" else "make",
                "files": files,
            })
    return items
