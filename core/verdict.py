# core/verdict.py —— 判定枚举 + 信号翻译表（requirements.md 三-1）
from __future__ import annotations

import signal as _signal
import sys
from enum import Enum


class Verdict(str, Enum):
    AC = "AC"
    PE = "PE"
    WA = "WA"
    TLE = "TLE"
    RE = "RE"
    CE = "CE"
    SE = "SE"


# 信号翻译表（requirements.md 三-1，文案冻结，前端/CLI/报告三处一致）
SIGNAL_MSG = {
    "SIGSEGV": "段错误（SIGSEGV）：非法内存访问——常见于空指针解引用或数组越界",
    "SIGFPE": "算术异常（SIGFPE）：除零或整数溢出",
    "SIGABRT": "程序中止（SIGABRT）：assert 失败或显式 abort()",
    "SIGBUS": "总线错误（SIGBUS）：地址未对齐 / 非法映射",
    "SIGKILL": "被强制终止（SIGKILL）：疑似内存超限或被系统回收",
    "SIGXCPU": "CPU 时间超限（SIGXCPU）",
}

# 信号编号 → 名称（仅 POSIX 有效；Windows 不细分信号）
_SIGNAL_NAMES = {
    getattr(_signal, name): name
    for name in SIGNAL_MSG
    if hasattr(_signal, name)
}


def signal_name(sig: int | None) -> str | None:
    """信号编号 → 信号名（如 "SIGSEGV"）；未知或 None 返回 None。"""
    if sig is None:
        return None
    name = _SIGNAL_NAMES.get(sig)
    if name is not None:
        return name
    try:
        return _signal.Signals(sig).name
    except ValueError:
        return None


def translate_signal(sig: int) -> str:
    """信号编号 → 中文翻译句（SIGNAL_MSG 原文）；未知信号给通用描述。"""
    name = _SIGNAL_NAMES.get(sig)
    if name is None:
        try:
            name = _signal.Signals(sig).name
        except ValueError:
            return f"进程被信号 {sig} 终止"
    return SIGNAL_MSG.get(name, f"进程被信号 {name} 终止")


def windows_re_message(exit_code: int) -> str:
    """Windows 降级 RE 文案（content-plan §4 冻结句式）。"""
    return (
        f"进程非 0 退出码（exit code {exit_code}）：Windows 下不细分信号，请看 stderr 定位。"
    )


IS_WINDOWS = sys.platform == "win32"
