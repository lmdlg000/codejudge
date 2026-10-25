# core/scorer.py —— 汇总与计分（requirements.md 三-6）
# OI：score = Σ通过权重/Σ总权重×满分；ACM：全 AC 满分否则 0（partial_score 供参考）
# 总判定两种模式统一用 ACM 合成规则（site-spec 5.4：便于列表徽章统一）
from __future__ import annotations

from .verdict import Verdict

# 每用例判定所需的最小字段视图（dict 或对象均可）
_CASE_FIELDS = ("verdict", "weight")


def _case_verdict(case) -> str:
    v = case["verdict"] if isinstance(case, dict) else case.verdict
    return str(v.value if isinstance(v, Verdict) else v)


def _case_weight(case) -> float:
    w = case["weight"] if isinstance(case, dict) else case.weight
    return float(w)


def synthesize_verdict(case_verdicts: list[str]) -> str:
    """ACM 合成规则：全 AC → AC；否则首个非 AC 用例判定；无用例 → SE。"""
    if not case_verdicts:
        return Verdict.SE.value
    for v in case_verdicts:
        if v != Verdict.AC.value:
            return v
    return Verdict.AC.value


def score(cases: list, mode: str, max_score: float) -> dict:
    """汇总 Summary（site-spec 5.3）：total/passed/pass_rate/score/max_score/partial_score。"""
    total = len(cases)
    verdicts = [_case_verdict(c) for c in cases]
    passed = sum(1 for v in verdicts if v == Verdict.AC.value)

    total_weight = sum(_case_weight(c) for c in cases)
    passed_weight = sum(_case_weight(c) for c in cases if _case_verdict(c) == Verdict.AC.value)
    partial = (passed_weight / total_weight * max_score) if total_weight > 0 else 0.0

    pass_rate = round(passed / total, 4) if total else 0.0
    partial_score = round(partial, 4)

    if mode == "acm":
        final = max_score if (total > 0 and passed == total) else 0.0
    else:  # oi
        final = partial_score

    return {
        "total": total,
        "passed": passed,
        "pass_rate": pass_rate,
        "score": round(final, 4),
        "max_score": float(max_score),
        "partial_score": partial_score,
    }
