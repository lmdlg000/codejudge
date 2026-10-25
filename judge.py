# judge.py —— CLI 入口（run / gen / import-samples / list / init）
# 返回码约定（requirements 五）：0 全 AC；1 非 AC；2 基础设施错误
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import builder, comparator, generator, importer, problem as problem_mod, reporter, runner, scorer
from core.problem import Problem, ProblemError, ProblemNotFound, is_safe_name
from core.verdict import Verdict, IS_WINDOWS, signal_name, translate_signal, windows_re_message

CE_MESSAGE = "编译失败，展开查看编译器输出"


def load_config() -> dict:
    path = ROOT / "config.toml"
    if path.is_file():
        try:
            with open(path, "rb") as fh:
                return tomllib.load(fh)
        except (OSError, tomllib.TOMLDecodeError):
            return {}
    return {}


CONFIG = load_config()
PROBLEMS_DIR = ROOT / "problems"
REPORTS_DIR = ROOT / os.environ.get("JUDGE_REPORTS_DIR", CONFIG.get("judge", {}).get("report_dir", "reports"))


# ---------------- run 流水线（编译 → 逐用例 → 计分 → 报告） ----------------

def _case_dict(case, verdict: str, message: str, time_ms: float = 0.0,
               exit_code: int | None = None, signal: str | None = None,
               timed_out: bool = False, stderr_tail: str | None = None) -> dict:
    return {
        "name": case.name,
        "verdict": verdict,
        "time_ms": round(time_ms, 1),
        "exit_code": exit_code,
        "weight": case.weight,
        "message": message,
        "signal": signal,
        "timed_out": timed_out,
        "stderr_tail": stderr_tail,
    }


def _run_single_case(problem: Problem, case, binary: Path) -> dict:
    """单用例：TLE → RE → 比对（AC/PE/WA），判定顺序冻结。"""
    input_data = case.input_path.read_bytes()
    expected = case.output_path.read_text(encoding="utf-8", errors="replace")
    time_ms = problem.case_time_ms(case)
    rr = runner.run(binary, input_data, time_ms, problem.default_memory_mb)

    if rr.timed_out:
        return _case_dict(case, Verdict.TLE.value, f"超时（限时 {time_ms}ms）",
                          rr.time_ms, rr.exit_code, timed_out=True,
                          stderr_tail=runner.stderr_tail(rr.stderr))

    if rr.signal is not None or (rr.exit_code not in (0, None)):
        if rr.signal is not None:
            sig_name = signal_name(rr.signal)
            msg = translate_signal(rr.signal)
        else:
            sig_name = None
            msg = windows_re_message(rr.exit_code)
        return _case_dict(case, Verdict.RE.value, msg, rr.time_ms, rr.exit_code,
                          signal=sig_name, timed_out=False,
                          stderr_tail=runner.stderr_tail(rr.stderr))

    actual = rr.stdout.decode("utf-8", errors="replace")
    verdict, message = comparator.compare(actual, expected, problem.compare_mode)
    return _case_dict(case, verdict.value, message, rr.time_ms, rr.exit_code,
                      timed_out=False, stderr_tail=runner.stderr_tail(rr.stderr) if rr.stderr else None)


def evaluate(problem: Problem, workdir: Path, src_names: list[str], mode: str,
             submission_label: str, files: list[dict], sid: str) -> dict:
    """完整流水线，返回报告 dict。CE 时全部用例 verdict=CE 且 build_log 非空。"""
    started_at = reporter.iso_now()
    try:
        br = builder.build(problem, workdir, src_names)
    except builder.BuildError as exc:
        br = builder.BuildResult(ok=False, binary=None, log=str(exc))

    cases: list[dict] = []
    build_log = None
    if not br.ok:
        build_log = br.log
        for case in problem.tests:
            cases.append(_case_dict(case, Verdict.CE.value, CE_MESSAGE))
    else:
        for case in problem.tests:
            cases.append(_run_single_case(problem, case, br.binary))

    summary = scorer.score(cases, mode, problem.score)
    verdict = scorer.synthesize_verdict([c["verdict"] for c in cases])
    return reporter.make_report(
        submission_id=sid,
        problem_id=problem.id,
        problem_title=problem.title,
        mode=mode,
        submission=submission_label,
        started_at=started_at,
        status="finished",
        verdict=verdict,
        summary=summary,
        cases=cases,
        build_log=build_log,
        files=files,
    )


def _materialize(submission: Path, workdir: Path) -> tuple[list[str], list[dict]]:
    """把提交（单文件/目录）落盘到 workdir，返回 (源码文件名列表, files 回显)。"""
    if submission.is_file():
        name = submission.name
        if not is_safe_name(name):
            raise ProblemError(f"文件名不合法：{name!r}（仅限字母、数字、_ . -，最长 64 字符）")
        shutil.copy2(submission, workdir / name)
        content = (workdir / name).read_text(encoding="utf-8", errors="replace")
        return [name], [{"name": name, "content": content}]

    if submission.is_dir():
        names: list[str] = []
        files: list[dict] = []
        for p in sorted(submission.iterdir()):
            if not p.is_file():
                continue
            if not is_safe_name(p.name):
                raise ProblemError(f"文件名不合法：{p.name!r}（仅限字母、数字、_ . -，最长 64 字符）")
            shutil.copy2(p, workdir / p.name)
            names.append(p.name)
            files.append({"name": p.name, "content": p.read_text(encoding="utf-8", errors="replace")})
        if not names:
            raise ProblemError(f"提交目录为空：{submission}")
        return names, files

    raise ProblemError(f"找不到提交文件：{submission}")


def cmd_run(args) -> int:
    try:
        problem = Problem.load(args.pid, args.problems_dir)
    except ProblemNotFound as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except ProblemError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    submission = Path(args.submission)
    if not submission.is_absolute():
        submission = (Path.cwd() / submission).resolve()
    mode = args.mode or problem.contest_type

    workdir = Path(tempfile.mkdtemp(prefix="judge-"))
    try:
        src_names, files = _materialize(submission, workdir)
        sid = reporter.make_sid(problem.id)
        report = evaluate(problem, workdir, src_names, mode, str(submission), files, sid)
        path = reporter.write_report(report, args.reports_dir)
    except ProblemError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # 基础设施异常 → SE / 返回码 2
        print(f"评测器自身异常：{exc}", file=sys.stderr)
        return 2
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    reporter.print_table(report)
    print(f"\n报告已写入 {path}")
    return 0 if report["verdict"] == Verdict.AC.value else 1


def cmd_gen(args) -> int:
    try:
        # gen 要能为缺 .out 的新 .in 生成期望输出 → require_output=False
        problem = Problem.load(args.pid, args.problems_dir, require_output=False)
        results = generator.generate(problem, args.ref, keep_going=args.keep_going)
    except (ProblemNotFound, ProblemError, generator.GenError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    for item in results:
        print(f"{item.name:<16} {item.verdict:<4} {item.time_ms:.0f}ms  {item.message}")
    print(f"已刷新 {len(results)} 个 .out（{problem.root / 'tests'}）")
    return 0


def cmd_import_samples(args) -> int:
    md_path = Path(args.md)
    if args.target:
        target = Path(args.target)
    else:
        target = importer.infer_target(md_path, args.problems_dir)
        if target is None:
            print(f"错误：无法从文件名推导题目（需 Pn-* 前缀），请显式 --target", file=sys.stderr)
            return 2
    try:
        written = importer.import_samples(md_path, target)
    except ProblemError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    for name in written:
        print(f"写入 {target / 'tests' / name}")
    print(f"共 {len(written)} 组样例 → {target / 'tests'}")
    return 0


def cmd_list(args) -> int:
    problems_dir = Path(args.problems_dir)
    pids = [args.pid] if args.pid else sorted(
        p.name for p in problems_dir.iterdir() if p.is_dir() and (p / "problem.json").is_file()
    )
    for pid in pids:
        try:
            problem = Problem.load(pid, problems_dir)
        except (ProblemNotFound, ProblemError) as exc:
            print(f"{pid}: 不可用（{exc}）")
            continue
        print(f"{problem.id}  {problem.title}  [{problem.contest_type}]  "
              f"满分 {problem.score:g}  时限 {problem.default_time_ms}ms  "
              f"用例 {len(problem.tests)}  构建 {problem.build_mode}")
        if args.pid:  # 明确指定 pid 时展开用例
            for case in problem.tests:
                tl = case.time_limit_ms or problem.default_time_ms
                print(f"    {case.name:<18} weight={case.weight:g} time={tl}ms {case.note}")
    return 0


def cmd_init(args) -> int:
    root = Path(args.problems_dir) / args.pid
    if root.exists():
        print(f"错误：目录已存在 {root}", file=sys.stderr)
        return 2
    (root / "tests").mkdir(parents=True)
    (root / "reference").mkdir()
    defaults = CONFIG.get("judge", {})
    import json

    meta = {
        "id": args.pid,
        "title": args.title or f"题目 {args.pid}",
        "topic": None,
        "difficulty": None,
        "contest_type": args.type,
        "build": {"command": "g++ -O2 -std=c++17 -o {bin} {src}", "src": "main.cpp"},
        "limits": {
            "time_ms": int(defaults.get("default_time_ms", 1000)),
            "memory_mb": int(defaults.get("default_memory_mb", 256)),
        },
        "score": 100,
        "compare_mode": "trim",
    }
    (root / "problem.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (root / "statement.md").write_text(
        f"# {args.pid} {meta['title']}\n\n## 题目背景\n\n（在此填写题面）\n\n"
        "## 输入格式\n\n（在此填写输入格式）\n\n## 输出格式\n\n（在此填写输出格式）\n\n"
        "## 样例输入\n\n```\n0 0\n```\n\n## 样例输出\n\n```\n0\n```\n\n## 数据范围\n\n- （在此填写数据范围）\n",
        encoding="utf-8",
    )
    (root / "tests" / "1.in").write_text("0 0\n", encoding="utf-8")
    (root / "tests" / "1.out").write_text("0\n", encoding="utf-8")
    (root / "reference" / f"{args.pid}.cpp").write_text(
        "#include <bits/stdc++.h>\nusing namespace std;\nint main() {\n    long long a, b;\n    cin >> a >> b;\n    cout << a + b << \"\\n\";\n    return 0;\n}\n",
        encoding="utf-8",
    )
    print(f"已创建题目骨架 {root}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="judge.py", description="CodeJudge 判题引擎 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="评测单个提交")
    p_run.add_argument("pid")
    p_run.add_argument("submission", help="提交文件或目录（多文件 make 工程）")
    p_run.add_argument("--mode", choices=["acm", "oi"], default=None, help="覆盖比赛类型")
    p_run.set_defaults(func=cmd_run)

    p_gen = sub.add_parser("gen", help="用参考实现刷新 .out")
    p_gen.add_argument("pid")
    p_gen.add_argument("--ref", required=True, help="参考实现路径")
    p_gen.add_argument("--keep-going", action="store_true", help="参考实现出错时跳过而非中止")
    p_gen.set_defaults(func=cmd_gen)

    p_imp = sub.add_parser("import-samples", help="从题面抽取样例")
    p_imp.add_argument("md")
    p_imp.add_argument("--target", default=None, help="题目目录，缺省按 Pn-* 前缀推导")
    p_imp.set_defaults(func=cmd_import_samples)

    p_list = sub.add_parser("list", help="列出题目与用例")
    p_list.add_argument("pid", nargs="?", default=None)
    p_list.set_defaults(func=cmd_list)

    p_init = sub.add_parser("init", help="创建题目骨架")
    p_init.add_argument("pid")
    p_init.add_argument("--type", choices=["acm", "oi"], default="oi")
    p_init.add_argument("--title", default=None)
    p_init.set_defaults(func=cmd_init)

    for p in (p_run, p_gen, p_imp, p_list, p_init):
        p.add_argument("--problems-dir", default=str(PROBLEMS_DIR), help=argparse.SUPPRESS)
    p_run.add_argument("--reports-dir", default=str(REPORTS_DIR), help=argparse.SUPPRESS)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
