// supabase/functions/_shared/util.ts —— Edge Function 公共件（CORS / 校验 / 响应）
// 校验规则与 FastAPI judge_service.validate_submission 保持同源语义

export const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

export function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json; charset=utf-8" },
  });
}

export function apiError(code: string, message: string, status: number): Response {
  return json({ error: { code, message } }, status);
}

export class PayloadError extends Error {
  code: string;
  status: number;
  constructor(code: string, message: string, status = 400) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

export interface FileItem {
  name: string;
  content: string;
}

export interface NormalizedSubmission {
  files: FileItem[];
  file_label: string;
  mode: string | null;
  /** UAPI language 参数（默认 cpp） */
  language: string;
  problem: {
    title: string;
    statement_md: string;
    contest_type: string;
    limits: { time_ms: number; memory_mb: number };
    build_mode: string;
    /** 样例（UAPI 真实运行入参；显式样例校验与 AI 语义评判的对照数据） */
    samples: { input: string; output: string }[];
  };
}

const NAME_RE = /^[A-Za-z0-9_.-]{1,64}$/;
const MAX_FILES = 20;
const MAX_FILE_CHARS = 65536;
const MAX_TOTAL_CHARS = 262144;

function safeName(name: string): boolean {
  return NAME_RE.test(name) && name !== "." && name !== "..";
}

/** 提交体校验：source_code|files 二选一、文件名白名单、体积上限。 */
export function normalizeSubmission(body: any): NormalizedSubmission {
  const sourceCode = body?.source_code;
  const rawFiles = body?.files;
  const filename = body?.filename;
  const problem = body?.problem || {};

  if ((sourceCode == null) === (rawFiles == null)) {
    throw new PayloadError("VALIDATION_ERROR", "提交内容不合法，请检查后重试：source_code 与 files 必须恰好给其一");
  }

  let files: FileItem[];
  if (sourceCode != null) {
    if (typeof sourceCode !== "string" || sourceCode.trim() === "") {
      throw new PayloadError("VALIDATION_ERROR", "提交内容不合法，请检查后重试：源码为空");
    }
    if (sourceCode.length > MAX_FILE_CHARS) {
      throw new PayloadError("PAYLOAD_TOO_LARGE", `代码太长，请精简后重试：单文件上限 ${MAX_FILE_CHARS} 字符`, 413);
    }
    const name = typeof filename === "string" && filename ? filename : "main.cpp";
    if (!safeName(name)) {
      throw new PayloadError("VALIDATION_ERROR", "提交内容不合法，请检查后重试：文件名仅限字母、数字、_ . -，最长 64 字符");
    }
    files = [{ name, content: sourceCode }];
  } else {
    if (!Array.isArray(rawFiles) || rawFiles.length === 0) {
      throw new PayloadError("VALIDATION_ERROR", "提交内容不合法，请检查后重试：files 不能为空");
    }
    if (rawFiles.length > MAX_FILES) {
      throw new PayloadError("PAYLOAD_TOO_LARGE", `代码太长，请精简后重试：最多 ${MAX_FILES} 个文件`, 413);
    }
    let total = 0;
    const seen = new Set<string>();
    files = [];
    for (const item of rawFiles) {
      const name = String(item?.name ?? "");
      const content = item?.content;
      if (!safeName(name)) {
        throw new PayloadError("VALIDATION_ERROR", "提交内容不合法，请检查后重试：文件名仅限字母、数字、_ . -，最长 64 字符");
      }
      if (seen.has(name)) {
        throw new PayloadError("VALIDATION_ERROR", `提交内容不合法，请检查后重试：文件名重复：${name}`);
      }
      seen.add(name);
      if (typeof content !== "string" || content.trim() === "") {
        throw new PayloadError("VALIDATION_ERROR", `提交内容不合法，请检查后重试：源码为空：${name}`);
      }
      if (content.length > MAX_FILE_CHARS) {
        throw new PayloadError("PAYLOAD_TOO_LARGE", `代码太长，请精简后重试：单文件上限 ${MAX_FILE_CHARS} 字符`, 413);
      }
      total += content.length;
      files.push({ name, content });
    }
    if (total > MAX_TOTAL_CHARS) {
      throw new PayloadError("PAYLOAD_TOO_LARGE", `代码太长，请精简后重试：files 合计上限 ${MAX_TOTAL_CHARS} 字符`, 413);
    }
  }

  const buildMode = String(problem.build_mode || "g++");
  if (buildMode === "make") {
    if (sourceCode != null) {
      throw new PayloadError("VALIDATION_ERROR", "提交内容不合法，请检查后重试：该题为多文件 make 构建，请用多文件提交（需包含 Makefile 与源文件）");
    }
    const names = new Set(files.map((f) => f.name));
    if (!["Makefile", "makefile", "GNUmakefile"].some((n) => names.has(n))) {
      throw new PayloadError("VALIDATION_ERROR", "提交内容不合法，请检查后重试：多文件 make 构建缺少 Makefile，请在提交文件中包含 Makefile");
    }
  }

  const mode = body?.mode ?? null;
  if (mode != null && mode !== "acm" && mode !== "oi") {
    throw new PayloadError("VALIDATION_ERROR", "提交内容不合法，请检查后重试：mode 只能是 acm 或 oi");
  }

  const fileLabel = files.length === 1
    ? files[0].name
    : `${files[0].name} 等 ${files.length} 个文件`;

  return {
    files,
    file_label: fileLabel,
    mode,
    language: (() => {
      const lang = String(body?.language ?? "").trim();
      return /^[a-z0-9+#.-]{1,24}$/i.test(lang) ? lang.toLowerCase() : "cpp";
    })(),
    problem: {
      title: String(problem.title || ""),
      statement_md: String(problem.statement_md || ""),
      contest_type: String(problem.contest_type || "oi"),
      limits: {
        time_ms: Number(problem.limits?.time_ms || 1000),
        memory_mb: Number(problem.limits?.memory_mb || 256),
      },
      build_mode: buildMode,
      samples: Array.isArray(problem.samples)
        ? problem.samples.slice(0, 10).map((s: any) => ({
            input: String(s?.input ?? ""),
            output: String(s?.output ?? ""),
          }))
        : [],
    },
  };
}

/** 提交 id：与 reports/<sid>.json 命名空间同构的可读 id。 */
export function newSid(problemId: string): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  const ts =
    `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-` +
    `${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
  const rand = crypto.randomUUID().replace(/-/g, "").slice(0, 4);
  const pid = String(problemId || "P0").replace(/[^A-Za-z0-9_-]/g, "").slice(0, 12) || "P0";
  return `${ts}-${pid}-${rand}`;
}

export async function readJson(req: Request): Promise<any> {
  try {
    return await req.json();
  } catch {
    throw new PayloadError("VALIDATION_ERROR", "提交内容不合法，请检查后重试：请求体不是合法 JSON");
  }
}
