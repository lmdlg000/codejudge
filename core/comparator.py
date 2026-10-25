# core/comparator.py —— 输出比对（requirements.md 三-5）
# 比对顺序：逐字符 → token（空白差异 PE）→ 首差行号（WA）
# compare_mode: "trim"（默认，CRLF 归一 + 末尾多余换行无害）| "exact"（原样逐字符）
from __future__ import annotations

from .verdict import Verdict


def _normalize(text: str, compare_mode: str) -> str:
    if compare_mode == "exact":
        return text
    # trim：忽略行尾 \r\n 与末尾多余空行（requirements 三-5 约定）
    return text.replace("\r\n", "\n").rstrip("\n")


def compare(actual: str, expected: str, compare_mode: str = "trim") -> tuple[Verdict, str]:
    """返回 (判定, 提示)。AC 提示为空串。"""
    a = _normalize(actual, compare_mode)
    e = _normalize(expected, compare_mode)

    if a == e:  # 逐字符一致（trim 模式已去掉末尾空行）
        return Verdict.AC, ""

    a_tokens, e_tokens = a.split(), e.split()
    if a_tokens == e_tokens:  # 只有空白差异
        return Verdict.PE, "仅空白差异（PE）：内容相同但换行/空格不一致"

    a_lines = a.split("\n")
    e_lines = e.split("\n")
    for i, (al, el) in enumerate(zip(a_lines, e_lines), 1):
        if al != el:
            return Verdict.WA, f"第 {i} 行不一致：期望 {el!r}，实际 {al!r}"
    if len(a_lines) != len(e_lines):
        return Verdict.WA, f"行数不一致：期望 {len(e_lines)} 行，实际 {len(a_lines)} 行"
    # 理论到不了：token 不同必然在某行不同或行数不同，兜底给 WA
    return Verdict.WA, f"行数不一致：期望 {len(e_lines)} 行，实际 {len(a_lines)} 行"
