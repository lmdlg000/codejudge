# core/generator.py —— gen 子命令（requirements.md 三-8）
# 编译参考实现 → 遍历 .in 限时运行 → stdout 原样写入 .out（临时文件 + 原子替换）
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .problem import Problem, ProblemError
from .runner import run

REF_COMPILE_TIMEOUT_S = 60


@dataclass
class GenItem:
    name: str
    verdict: str  # "OK" | "RE" | "TLE" | ...
    time_ms: float
    message: str = ""


class GenError(Exception):
    pass


def _compile_ref(ref: Path, out_bin: Path) -> str:
    argv = ["g++", "-O2", "-std=c++17", "-o", str(out_bin), str(ref)]
    proc = subprocess.run(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=REF_COMPILE_TIMEOUT_S,
    )
    log = proc.stdout.decode("utf-8", errors="replace")
    if proc.returncode != 0:
        raise GenError(f"参考实现编译失败：\n{log}")
    return log


def generate(problem: Problem, ref_path: str | Path, keep_going: bool = False) -> list[GenItem]:
    """用参考实现刷新全部 .out；参考实现 RE/TLE 时中止并保留旧 .out（keep_going=True 则跳过该用例）。"""
    ref = Path(ref_path)
    if not ref.is_file():
        cand = problem.root / ref_path
        if cand.is_file():
            ref = cand
        else:
            raise GenError(f"找不到参考实现：{ref_path}")

    workdir = problem.root / "tests"
    exe_suffix = ".exe" if os.name == "nt" else ""
    out_bin = problem.root / "reference" / f"_gen_bin{exe_suffix}"
    out_bin.parent.mkdir(parents=True, exist_ok=True)
    try:
        _compile_ref(ref, out_bin)
    except subprocess.TimeoutExpired as exc:
        raise GenError("参考实现编译超时（60s）") from exc

    results: list[GenItem] = []
    try:
        for case in problem.tests:
            input_data = case.input_path.read_bytes()
            time_ms = problem.case_time_ms(case)
            rr = run(out_bin, input_data, time_ms, problem.default_memory_mb)
            if rr.timed_out:
                item = GenItem(case.name, "TLE", rr.time_ms, "参考实现超时，旧 .out 已保留")
                results.append(item)
                if not keep_going:
                    raise GenError(f"{case.name}：参考实现超时，中止（旧 .out 已保留）")
                continue
            if rr.signal is not None or (rr.exit_code not in (0, None)):
                item = GenItem(
                    case.name,
                    "RE",
                    rr.time_ms,
                    f"参考实现异常退出（exit={rr.exit_code} signal={rr.signal}），旧 .out 已保留",
                )
                results.append(item)
                if not keep_going:
                    raise GenError(f"{case.name}：参考实现异常退出，中止（旧 .out 已保留）")
                continue
            # 原子写：先写临时文件再 os.replace，避免半截数据
            tmp = case.output_path.with_suffix(".out.tmp")
            tmp.write_bytes(rr.stdout)
            os.replace(tmp, case.output_path)
            results.append(GenItem(case.name, "OK", rr.time_ms))
    finally:
        try:
            out_bin.unlink(missing_ok=True)
        except OSError:
            pass
    return results
