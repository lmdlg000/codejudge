# core/builder.py —— 编译/构建（requirements.md 三-3）
# g++ 模板：g++ -O2 -std=c++17 -o {bin} {src}；make 模式：make <target> → <output>
# 安全红线（requirements §八）：shell=False；{bin}/{src} 只代入白名单文件名（非路径）
from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .problem import Problem, is_safe_name

BUILD_TIMEOUT_S = 60  # 构建超时 60s 判 CE（requirements 三-3）
BUILD_LOG_MAX_LINES = 200  # CE 提示保留末 200 行

BIN_NAME = "judge_bin"  # g++ 模式产物名（Windows 下 g++ 自动补 .exe）


class BuildError(Exception):
    """构建配置非法（模板/文件名不安全等）。"""


@dataclass
class BuildResult:
    ok: bool
    binary: Path | None
    log: str  # stdout+stderr 合并，末 200 行
    timed_out: bool = False


def _tail_log(text: str) -> str:
    lines = text.replace("\r\n", "\n").split("\n")
    return "\n".join(lines[-BUILD_LOG_MAX_LINES:])


def _resolve_binary(workdir: Path, name: str) -> Path | None:
    """产物可能带 .exe 后缀（Windows/MinGW）。"""
    for candidate in (workdir / name, workdir / f"{name}.exe"):
        if candidate.is_file():
            return candidate
    return None


def build(problem: Problem, workdir: Path, src_names: list[str]) -> BuildResult:
    """在 workdir 内构建提交。src_names 为已落盘的文件名（非路径）。"""
    for name in src_names:
        if not is_safe_name(name):
            raise BuildError(f"文件名不合法：{name!r}（仅限字母、数字、_ . -，最长 64 字符）")

    cfg = problem.build
    if problem.build_mode == "make":
        return _build_make(problem, workdir)
    return _build_gpp(problem, workdir, src_names)


def _build_gpp(problem: Problem, workdir: Path, src_names: list[str]) -> BuildResult:
    cfg = problem.build
    template = cfg.get("command") or "g++ -O2 -std=c++17 -o {bin} {src}"
    if not is_safe_name(BIN_NAME):
        raise BuildError("内部错误：产物名不合法")
    # 只把源文件交给编译器（.h 等头文件通过 #include 引用，不进编译行）
    compiles = [n for n in src_names if n.endswith((".cpp", ".cc", ".cxx", ".C"))]
    src_list = compiles or src_names
    # {src} = 提交的源码文件名列表（白名单已校验，绝不代入用户路径）
    src = " ".join(src_list) if src_list else (cfg.get("src") or "main.cpp")
    for name in src.split():
        if not is_safe_name(name):
            raise BuildError(f"文件名不合法：{name!r}")
    cmd_str = template.replace("{bin}", BIN_NAME).replace("{src}", src)
    try:
        argv = shlex.split(cmd_str, posix=os.name != "nt")
    except ValueError as exc:
        raise BuildError(f"构建命令模板非法：{exc}") from exc
    if not argv:
        raise BuildError("构建命令模板为空")
    return _run_build(argv, workdir, BIN_NAME)


def _build_make(problem: Problem, workdir: Path) -> BuildResult:
    cfg = problem.build
    make_bin = shutil.which(cfg.get("command") or "make") or (cfg.get("command") or "make")
    target = cfg.get("target")
    output = cfg.get("output") or target or "a.out"
    if not is_safe_name(str(output)):
        raise BuildError(f"build.output 不合法：{output!r}")
    argv = [make_bin] + ([str(target)] if target else [])
    return _run_build(argv, workdir, str(output))


def _run_build(argv: list[str], workdir: Path, output_name: str) -> BuildResult:
    try:
        proc = subprocess.run(
            argv,
            cwd=str(workdir),
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=BUILD_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return BuildResult(
            ok=False,
            binary=None,
            log=_tail_log(
                f"$ {' '.join(argv)}\n构建超过 60 秒被中止。检查模板递归或宏展开。"
            ),
            timed_out=True,
        )
    except OSError as exc:
        return BuildResult(
            ok=False,
            binary=None,
            log=_tail_log(f"$ {' '.join(argv)}\n无法执行构建命令：{exc}"),
            timed_out=False,
        )

    log_text = proc.stdout.decode("utf-8", errors="replace") if proc.stdout else ""
    log = _tail_log(f"$ {' '.join(argv)}\n{log_text}")
    if proc.returncode != 0:
        return BuildResult(ok=False, binary=None, log=log, timed_out=False)

    binary = _resolve_binary(workdir, output_name)
    if binary is None:
        return BuildResult(
            ok=False,
            binary=None,
            log=_tail_log(log + f"\n构建成功但找不到产物 {output_name}"),
            timed_out=False,
        )
    return BuildResult(ok=True, binary=binary, log=log, timed_out=False)
