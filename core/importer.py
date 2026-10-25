# core/importer.py —— import-samples 子命令（requirements.md 三-9）
# 解析题面 markdown 的样例块；problem_service 复用 extract_samples 产出 samples[]
from __future__ import annotations

import re
from pathlib import Path

from .problem import ProblemError

_HEADING_RE = re.compile(r"^##\s*样例(输入|输出)(?:\s+(\d+))?\s*$")
_FENCE_RE = re.compile(r"^(`{3,}|~{3,})")


def extract_samples(md: str) -> list[tuple[str, str]]:
    """从题面 Markdown 提取样例对 [(input, output), ...]，按出现顺序。

    规则（requirements 三-9）：
    - 匹配 `## 样例输入( \\d+)?` 与 `## 样例输出( \\d+)?` 标题下的 fenced code block；
    - 无标题时按「输入块 → 输出块」顺序配对。
    """
    lines = md.replace("\r\n", "\n").split("\n")
    entries: list[tuple[str, int | None, str]] = []  # (kind, num, content)
    i = 0
    while i < len(lines):
        m = _HEADING_RE.match(lines[i].strip())
        if m:
            kind = "input" if m.group(1) == "输入" else "output"
            num = int(m.group(2)) if m.group(2) else 1
            i += 1
            # 跳过空行找围栏
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines):
                fence = _FENCE_RE.match(lines[i])
                if fence:
                    marker = fence.group(1)[0] * len(fence.group(1))
                    i += 1
                    buf: list[str] = []
                    while i < len(lines) and not lines[i].strip().startswith(marker):
                        buf.append(lines[i])
                        i += 1
                    i += 1  # 吃掉收尾围栏
                    entries.append((kind, num, "\n".join(buf)))
                    continue
        i += 1

    samples: list[tuple[str, str]] = []
    if entries:
        inputs = [(n, c) for k, n, c in entries if k == "input"]
        outputs = [(n, c) for k, n, c in entries if k == "output"]
        # 按编号配对；编号缺失/不匹配时按出现顺序配对
        out_by_num = {}
        for idx, (n, c) in enumerate(outputs):
            out_by_num.setdefault(n, idx)
        used = set()
        for n, in_c in inputs:
            if n in out_by_num and out_by_num[n] not in used:
                j = out_by_num[n]
                used.add(j)
                samples.append((in_c, outputs[j][1]))
            else:
                # 顺序配对：取第一个未用的输出
                for j, (_, out_c) in enumerate(outputs):
                    if j not in used:
                        used.add(j)
                        samples.append((in_c, out_c))
                        break
        return samples

    # 无标题：所有 fenced code block 按「输入块 → 输出块」交替配对
    blocks = _all_fenced_blocks(lines)
    for k in range(0, len(blocks) - 1, 2):
        samples.append((blocks[k], blocks[k + 1]))
    return samples


def _all_fenced_blocks(lines: list[str]) -> list[str]:
    blocks: list[str] = []
    i = 0
    while i < len(lines):
        fence = _FENCE_RE.match(lines[i])
        if fence:
            marker = fence.group(1)[0] * len(fence.group(1))
            i += 1
            buf: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith(marker):
                buf.append(lines[i])
                i += 1
            i += 1
            blocks.append("\n".join(buf))
        else:
            i += 1
    return blocks


def _pick_free_name(tests_dir: Path, index: int) -> str:
    """命名：首选 <index>；已被占用则 sample-1、sample-2… 依次避让（防覆盖）。"""
    candidates = [str(index)] + [f"sample-{k}" for k in range(1, 1000)]
    for stem in candidates:
        if not (tests_dir / f"{stem}.in").exists() and not (tests_dir / f"{stem}.out").exists():
            return stem
    raise ProblemError(f"无法为样例分配文件名（{tests_dir} 中冲突过多）")


def import_samples(md_path: str | Path, target_root: str | Path, problems_dir: str | Path | None = None) -> list[str]:
    """解析题面并写入 <target>/tests/，返回写入的用例名列表。"""
    md_path = Path(md_path)
    if not md_path.is_file():
        raise ProblemError(f"找不到题面文件：{md_path}")
    text = md_path.read_text(encoding="utf-8")
    samples = extract_samples(text)
    if not samples:
        raise ProblemError(f"题面中没有可解析的样例块：{md_path.name}")

    target_root = Path(target_root)
    tests_dir = target_root / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    for idx, (in_c, out_c) in enumerate(samples, 1):
        stem = _pick_free_name(tests_dir, idx)
        (tests_dir / f"{stem}.in").write_text(in_c + ("\n" if not in_c.endswith("\n") else ""), encoding="utf-8")
        (tests_dir / f"{stem}.out").write_text(out_c + ("\n" if not out_c.endswith("\n") else ""), encoding="utf-8")
        written.append(f"{stem}.in")
    return written


def infer_target(md_path: str | Path, problems_dir: str | Path) -> Path | None:
    """从文件名前缀 Pn-* 推导题目目录（requirements 三-9）。"""
    import re

    m = re.match(r"^(P\d+)-", Path(md_path).name)
    if not m:
        return None
    cand = Path(problems_dir) / m.group(1)
    return cand if cand.is_dir() else None
