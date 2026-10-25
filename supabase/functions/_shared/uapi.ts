// supabase/functions/_shared/uapi.ts —— UAPI 确定性执行层（在线运行代码）
// 契约：POST https://uapis.cn/api/v1/execution/run（4 积分/次）
//   headers: Authorization: Bearer {UAPI_ACCESS_TOKEN}
//   body:    { language, code, stdin, timeout_ms, network: { mode: 'offline' } }
//   resp:    { status: 'success'|'compile_error'|'runtime_error'|'timeout', stdout, stderr, ... }
//   注意：HTTP 200 仅代表接收；判定必须看响应体 status 字段。
// 多文件：UAPI 为单 code 模型 —— 本地头文件内联合并（去 #include "local.h"）后整串执行。
// 配置（Edge Function secrets）：
//   UAPI_ACCESS_TOKEN  必填（uapis.cn 控制台）
//   UAPI_LANGUAGE      可选（默认 cpp）
//   UAPI_TIMEOUT_MS    可选（默认 5000，单样例执行时限）
import type { NormalizedSubmission } from "./util.ts";

export interface RunCase {
  case: number;
  status: string;
  /** 语义化 id：1=Accepted 2=Wrong Answer 3=Time Limit 4=Compilation Error 5=Runtime Error -1=执行器失败 */
  status_id: number;
  time_ms: number | null;
  memory_kb: number | null;
  expected: string;
  actual: string;
  stderr: string;
}

export interface RunnerRun {
  engine: "uapi" | "none";
  /** null=已执行；'not_configured' | 'api_failed' | 'no_samples'（未跑原因） */
  skipped: string | null;
  compile_output: string | null;
  all_accepted: boolean;
  cases: RunCase[];
}

const SID = {
  AC: 1,
  WA: 2,
  TLE: 3,
  CE: 4,
  RE: 5,
  FAIL: -1,
} as const;

export function env(name: string, fallback = ""): string {
  return Deno.env.get(name) ?? fallback;
}

/** 多文件合并：本地头文件内联（去 #include "local.h"），过滤 Makefile。 */
export function mergeFiles(files: { name: string; content: string }[]): string {
  if (files.length === 1) return files[0].content;
  const names = new Set(files.map((f) => f.name));
  const isHeader = (n: string) => /\.(h|hpp|hh)$/i.test(n);
  const isMake = (n: string) => /^makefile$/i.test(n) || n === "GNUmakefile";
  const stripLocalIncludes = (content: string) =>
    content
      .split("\n")
      .filter((line) => {
        const m = line.match(/^\s*#\s*include\s+"(.+?)"/);
        return !(m && names.has(m[1]));
      })
      .join("\n");
  const ordered = [
    ...files.filter((f) => isHeader(f.name) && !isMake(f.name)),
    ...files.filter((f) => !isHeader(f.name) && !isMake(f.name)),
  ];
  return ordered
    .map((f) => `// ===== ${f.name} =====\n${stripLocalIncludes(f.content)}`)
    .join("\n\n");
}

/** trim 比对：行尾空白与末尾空行视为无害（与本地 comparator 语义一致）。 */
function norm(s: string): string {
  return String(s ?? "").replace(/\r\n/g, "\n").replace(/[ \t]+$/gm, "").trim();
}

/** 由 UAPI status + stdout 比对推导代码结论。 */
export function classify(
  execStatus: string,
  actual: string,
  expected: string,
): { id: number; label: string } {
  if (execStatus === "compile_error") return { id: SID.CE, label: "Compilation Error" };
  if (execStatus === "timeout") return { id: SID.TLE, label: "Time Limit Exceeded" };
  if (execStatus === "runtime_error") return { id: SID.RE, label: "Runtime Error" };
  if (execStatus !== "success") return { id: SID.FAIL, label: "执行器调用失败" };
  if (norm(actual) === norm(expected)) return { id: SID.AC, label: "Accepted" };
  return { id: SID.WA, label: "Wrong Answer" };
}

/** 单组样例跑一次 UAPI（同步返回响应体；null=网络/接口失败）。 */
export async function runOne(
  language: string,
  code: string,
  stdin: string,
  timeoutMs: number,
): Promise<any | null> {
  const token = env("UAPI_ACCESS_TOKEN");
  if (!token) return null;
  try {
    const resp = await fetch("https://uapis.cn/api/v1/execution/run", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      signal: AbortSignal.timeout(15000),
      body: JSON.stringify({
        language,
        code,
        stdin,
        timeout_ms: timeoutMs,
        network: { mode: "offline" },
      }),
    });
    if (!resp.ok) return null;
    return await resp.json();
  } catch {
    return null;
  }
}

/**
 * 逐组样例执行（显式样例校验与运行数据收集共用）。
 * 返回 RunnerRun：cases 逐用例含状态/期望/实际/stderr。
 */
export async function runSamples(
  sub: NormalizedSubmission,
  samples?: { input: string; output: string }[],
): Promise<RunnerRun> {
  const empty = (skipped: string): RunnerRun => ({
    engine: "none",
    skipped,
    compile_output: null,
    all_accepted: false,
    cases: [],
  });
  if (!env("UAPI_ACCESS_TOKEN")) return empty("not_configured");
  const list = (samples ?? sub.problem.samples ?? []).slice(0, 10);
  if (list.length === 0) return empty("no_samples");

  const language = sub.language || env("UAPI_LANGUAGE", "cpp");
  const code = mergeFiles(sub.files);
  const timeoutMs = Math.min(10000, Math.max(1000, sub.problem.limits.time_ms || 5000));
  const cases: RunCase[] = [];
  let compileOutput: string | null = null;
  let anyFail = false;

  for (let i = 0; i < list.length; i++) {
    const s = list[i];
    const raw = await runOne(language, code, s.input, timeoutMs);
    if (!raw || typeof raw.status !== "string") {
      anyFail = true;
      cases.push({
        case: i + 1,
        status: "执行器调用失败",
        status_id: SID.FAIL,
        time_ms: null,
        memory_kb: null,
        expected: s.output,
        actual: "",
        stderr: "",
      });
      continue;
    }
    const actual = raw.stdout != null ? String(raw.stdout) : "";
    const stderr = raw.stderr != null ? String(raw.stderr) : "";
    const { id, label } = classify(raw.status, actual, s.output);
    if (id === SID.CE && !compileOutput) compileOutput = (stderr || label).slice(-4000) || null;
    if (id !== SID.AC) anyFail = true;
    cases.push({
      case: i + 1,
      status: label,
      status_id: id,
      time_ms: raw.execution_time != null ? Number(raw.execution_time) : null,
      memory_kb: raw.memory_used != null ? Number(raw.memory_used) : null,
      expected: s.output,
      actual,
      stderr: stderr.slice(-2048),
    });
    if (id === SID.CE) break; // 编译失败后续样例无意义
  }

  return {
    engine: "uapi",
    skipped: null,
    compile_output: compileOutput,
    all_accepted: !anyFail && cases.length > 0,
    cases,
  };
}

/** 是否编译失败。 */
export function hasCompileFailure(run: RunnerRun): boolean {
  return run.cases.some((c) => c.status_id === SID.CE);
}

/** 单组样例结论（前端 dry_run 逐样例回显用）。 */
export function caseToSampleResult(idx: number, c: RunCase) {
  return {
    name: `样例 ${idx + 1}`,
    passed: c.status_id === SID.AC,
    status: c.status,
    expected: c.expected,
    actual: c.actual,
    stderr: c.stderr,
  };
}
