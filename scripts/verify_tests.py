# scripts/verify_tests.py —— 核对 tests/ 正确性：
# 1) 1–5 号样例与 statement.md 题面样例逐字一致（importer 解析同源）
# 2) 隐藏小用例与人工核对的预期值一致（压力用例由参考实现生成，另行抽查）
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.importer import extract_samples  # noqa: E402

# 人工核对的隐藏用例预期（题面数据范围内的手算/独立计算）
HAND_CHECKED = {
    ("P1", "hidden-1"): "15\n",
    ("P1", "hidden-2"): "18\n",
    ("P1", "hidden-3"): "616\n",
    ("P2", "hidden-1"): "a1b1\n",
    ("P2", "hidden-2"): "a100000\n",
    ("P3", "hidden-1"): "3\n",
    ("P4", "hidden-1"): "1900-01-01\n",
    ("P4", "hidden-2"): "2000-02-29\n",
    ("P4", "hidden-3"): "4838-11-27\n",  # 与 Python datetime 独立计算一致
    ("P5", "hidden-1"): "7\n",
    ("P6", "hidden-1"): "OK\n1 2 4 3\n",
    ("P6", "hidden-2"): "CYCLE\n",
}

fail = 0
for pid in ("P1", "P2", "P3", "P4", "P5", "P6"):
    root = ROOT / "problems" / pid
    md = (root / "statement.md").read_text(encoding="utf-8")
    samples = extract_samples(md)
    assert len(samples) == 5, f"{pid} 题面样例不是 5 组：{len(samples)}"
    for i, (exp_in, exp_out) in enumerate(samples, 1):
        in_txt = (root / "tests" / f"{i}.in").read_text(encoding="utf-8")
        out_txt = (root / "tests" / f"{i}.out").read_text(encoding="utf-8")
        ok_in = in_txt.strip() == exp_in.strip()
        ok_out = out_txt.strip() == exp_out.strip()
        status = "OK " if (ok_in and ok_out) else "FAIL"
        if not (ok_in and ok_out):
            fail += 1
            print(f"[{status}] {pid} 样例{i}: in={ok_in} out={ok_out}")
            if not ok_out:
                print(f"    题面期望: {exp_out!r}\n    tests 实际: {out_txt!r}")
        else:
            print(f"[{status}] {pid} 样例{i} 与题面一致")

for (pid, stem), expected in HAND_CHECKED.items():
    out_txt = (ROOT / "problems" / pid / "tests" / f"{stem}.out").read_text(encoding="utf-8")
    ok = out_txt == expected
    print(f"[{'OK ' if ok else 'FAIL'}] {pid}/{stem}.out 手算核对")
    if not ok:
        fail += 1
        print(f"    期望: {expected!r}\n    实际: {out_txt!r}")

# 抽查压力用例输出形态
p3 = (ROOT / "problems" / "P3" / "tests" / "hidden-2.out").read_text(encoding="utf-8").strip()
assert p3.isdigit(), f"P3 hidden-2.out 应为整数，实际 {p3[:50]!r}"
p5 = (ROOT / "problems" / "P5" / "tests" / "hidden-2.out").read_text(encoding="utf-8").strip()
assert p5.lstrip("-").isdigit(), f"P5 hidden-2.out 应为整数，实际 {p5[:50]!r}"
p6 = (ROOT / "problems" / "P6" / "tests" / "hidden-3.out").read_text(encoding="utf-8")
assert p6.startswith("OK\n"), f"P6 hidden-3.out 应以 OK 开头，实际 {p6[:50]!r}"
order = p6.split("\n")[1].split()
assert order == sorted(order, key=int) and len(order) == 100000, "P6 hidden-3 拓扑序长度/形态异常"
print(f"[OK ] 压力用例形态抽查（P3={p3}, P5={p5}, P6 order len={len(order)}）")

print(("全部核对通过" if fail == 0 else f"失败 {fail} 项"))
sys.exit(1 if fail else 0)
