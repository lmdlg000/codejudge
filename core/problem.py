# core/problem.py —— 题目加载 + 用例发现 + 单用例 json 覆盖（requirements.md 三-2 / site-spec 9）
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# 文件名白名单（site-spec B11）：拒绝 ..、路径分隔符、绝对路径
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


class ProblemError(Exception):
    """题目数据不可用（缺文件 / json 非法 / 缺 .out 等）。"""


class ProblemNotFound(Exception):
    """题目 id 不存在。"""


def is_safe_name(name: str) -> bool:
    """文件名白名单校验：字母数字 _ . -，1–64 字符；显式拒绝 . 与 ..。"""
    if not isinstance(name, str) or not SAFE_NAME_RE.match(name):
        return False
    if name in (".", ".."):
        return False
    return True


@dataclass
class TestCase:
    name: str
    input_path: Path
    output_path: Path
    weight: float = 1.0
    time_limit_ms: int | None = None  # None → 用题目默认时限
    note: str = ""


@dataclass
class Problem:
    id: str
    root: Path
    title: str
    contest_type: str  # "acm" | "oi"
    build: dict  # {"command":..., "src":..., "target":..., "output":...}
    default_time_ms: int = 1000
    default_memory_mb: int = 256
    tests: list[TestCase] = field(default_factory=list)
    score: float = 100.0
    compare_mode: str = "trim"  # "exact" | "trim"
    topic: str | None = None
    difficulty: str | None = None

    # ---- 派生属性 ----
    @property
    def build_mode(self) -> str:
        return "make" if self.build.get("target") or self.build.get("command") == "make" else "g++"

    @property
    def default_filename(self) -> str | None:
        """单文件提交的默认文件名（make 题无单文件默认名）。"""
        if self.build_mode == "make":
            return None
        return self.build.get("src") or "main.cpp"

    def case_time_ms(self, case: TestCase) -> int:
        return case.time_limit_ms or self.default_time_ms

    # ---- 加载 ----
    @classmethod
    def load(cls, pid: str, problems_dir: str | Path, require_output: bool = True) -> "Problem":
        """加载题目。require_output=True（判题路径）：缺 .out 直接拒绝；
        False（gen 刷 .out）：允许 .out 暂缺，由 generator 生成。"""
        problems_dir = Path(problems_dir)
        root = problems_dir / pid
        meta_path = root / "problem.json"
        if not root.is_dir() or not meta_path.is_file():
            raise ProblemNotFound(f"题目不存在：{pid}")
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ProblemError(f"题目数据没读出来：{pid}/problem.json 非法（{exc}）") from exc

        for key in ("id", "title", "contest_type", "build"):
            if key not in meta:
                raise ProblemError(f"题目数据没读出来：{pid}/problem.json 缺字段 {key!r}")
        if meta["contest_type"] not in ("acm", "oi"):
            raise ProblemError(f"题目数据没读出来：{pid} contest_type 必须是 acm|oi")
        if not isinstance(meta["build"], dict) or not meta["build"].get("command"):
            raise ProblemError(f"题目数据没读出来：{pid} build.command 缺失")

        limits = meta.get("limits") or {}
        problem = cls(
            id=meta["id"],
            root=root,
            title=meta["title"],
            contest_type=meta["contest_type"],
            build=meta["build"],
            default_time_ms=int(limits.get("time_ms", 1000)),
            default_memory_mb=int(limits.get("memory_mb", 256)),
            score=float(meta.get("score", 100)),
            compare_mode=meta.get("compare_mode", "trim"),
            topic=meta.get("topic"),
            difficulty=meta.get("difficulty"),
        )
        if problem.compare_mode not in ("exact", "trim"):
            raise ProblemError(f"题目数据没读出来：{pid} compare_mode 必须是 exact|trim")
        problem.tests = discover_tests(root, require_output=require_output)
        return problem


def discover_tests(root: Path, require_output: bool = True) -> list[TestCase]:
    """扫描 tests/*.in（文件名字典序），同名 .out 缺失直接拒绝；<stem>.json 覆盖 weight/time_ms/note。"""
    tests_dir = root / "tests"
    if not tests_dir.is_dir():
        raise ProblemError(f"题目数据没读出来：{root.name}/tests/ 目录缺失")
    cases: list[TestCase] = []
    for in_path in sorted(tests_dir.glob("*.in"), key=lambda p: p.name):
        stem = in_path.stem
        out_path = tests_dir / f"{stem}.out"
        if require_output and not out_path.is_file():
            raise ProblemError(
                f"题目数据没读出来：{root.name}/tests/{in_path.name} 缺同名 .out（每个 .in 必须有同名 .out）"
            )
        case = TestCase(name=in_path.name, input_path=in_path, output_path=out_path)
        override = tests_dir / f"{stem}.json"
        if override.is_file():
            try:
                data = json.loads(override.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ProblemError(f"题目数据没读出来：{root.name}/tests/{override.name} 非法（{exc}）") from exc
            if not isinstance(data, dict):
                raise ProblemError(f"题目数据没读出来：{root.name}/tests/{override.name} 必须是 JSON 对象")
            if "weight" in data:
                case.weight = float(data["weight"])
            if "time_ms" in data:
                case.time_limit_ms = int(data["time_ms"])
            if "note" in data:
                case.note = str(data["note"])
        cases.append(case)
    if not cases:
        raise ProblemError(f"题目数据没读出来：{root.name}/tests/ 没有 .in 用例")
    return cases
