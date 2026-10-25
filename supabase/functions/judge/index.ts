// supabase/functions/judge/index.ts —— 提交接收 + 显式样例强制校验 Edge Function
// 关键设计（双层校验的后端安全层）：
//   ① 前置同步校验：插入 submissions 前用 UAPI 逐个跑显式样例，任一失败 400 不落库；
//   ② 全部通过才插入 judging 并立即返回 202；AI 评分走 EdgeRuntime.waitUntil 后台异步；
//   ③ dry_run=true：只跑样例返回逐样例结果（前端体验层用），不落库。
// 状态变更由 Supabase Realtime 推送（前端零轮询）。
//
// 部署：supabase functions deploy judge
// 密钥：supabase secrets set SUPABASE_SECRET_KEY=sb_secret_… UAPI_ACCESS_TOKEN=… AI_API_KEY=…
import { createClient } from "npm:@supabase/supabase-js@2";
import {
  apiError,
  corsHeaders,
  json,
  newSid,
  normalizeSubmission,
  PayloadError,
  readJson,
} from "../_shared/util.ts";
import { runSamples, caseToSampleResult, type RunnerRun } from "../_shared/uapi.ts";
import { gradeInBackground } from "../_shared/scoring.ts";

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }
  if (req.method !== "POST") {
    return apiError("VALIDATION_ERROR", "提交内容不合法，请检查后重试：仅支持 POST", 405);
  }

  try {
    // ---- 1. 鉴权（用户 JWT；匿名提交不在本流程） ----
    const authHeader = req.headers.get("Authorization") ?? "";
    const jwt = authHeader.replace(/^Bearer\s+/i, "");
    const supabaseUrl = Deno.env.get("SUPABASE_URL") ?? "";
    const publishable =
      Deno.env.get("SUPABASE_PUBLISHABLE_KEY") ?? Deno.env.get("SUPABASE_ANON_KEY") ?? "";
    if (!jwt || !supabaseUrl || !publishable) {
      return apiError("UNAUTHORIZED", "请先登录（登录状态可能已过期）", 401);
    }
    const { data: userData, error: userErr } = await createClient(supabaseUrl, publishable, {
      global: { headers: { Authorization: authHeader } },
      auth: { persistSession: false },
    }).auth.getUser();
    if (userErr || !userData?.user) {
      return apiError("UNAUTHORIZED", "请先登录（登录状态可能已过期）", 401);
    }
    const user = userData.user;

    // ---- 2. 校验提交体 ----
    const body = await readJson(req);
    const sub = normalizeSubmission(body);
    const problemId = String(body.problem_id ?? "").slice(0, 64);
    const dryRun = body.dry_run === true;
    // 备用通道：样例未全过强制提交（前端测试 ≥10 次解锁；结果强制转人工复核）
    const forceSubmit = body.force_submit === true;
    if (!problemId) {
      return apiError("VALIDATION_ERROR", "提交内容不合法，请检查后重试：problem_id 必填");
    }
    if (!Array.isArray(body?.problem?.samples) || body.problem.samples.length === 0) {
      return apiError("VALIDATION_ERROR", "必须提供显式测试样例");
    }

    // ---- 3. 前置强制校验：UAPI 逐个跑显式样例（双层校验的后端安全层） ----
    const run: RunnerRun = await runSamples(sub);
    if (run.skipped === "not_configured") {
      return apiError("ENGINE_UNAVAILABLE", "判题引擎不可用，请检查服务端 UAPI 配置", 503);
    }

    // dry_run：只回逐样例结果（前端体验层），不落库
    if (dryRun) {
      return json({
        dry_run: true,
        passed: run.all_accepted,
        samples: run.cases.map((c, i) => caseToSampleResult(i, c)),
      });
    }

    // 任一样例失败 → 400，不写入数据库（force_submit 备用通道除外：走 AI + 强制人工复核）
    const failed = run.cases.find((c) => c.status_id !== 1);
    if (!run.all_accepted && !forceSubmit && failed) {
      return json(
        {
          error: {
            code: "VALIDATION_ERROR",
            message: `存在未通过的显式测试样例，不能提交（${failed.status}）`,
          },
          failed_sample: `样例 ${failed.case}`,
          expected: failed.expected,
          actual: failed.actual,
          execution_status: failed.status,
        },
        400,
      );
    }

    // ---- 4. 全部通过：落库即回执（status=judging） ----
    const secret = Deno.env.get("SUPABASE_SECRET_KEY") ?? "";
    if (!secret) {
      return apiError("ENGINE_UNAVAILABLE", "判题引擎不可用，请检查服务端配置", 503);
    }
    const admin = createClient(supabaseUrl, secret, { auth: { persistSession: false } });
    const sid = newSid(problemId);
    const { error: insErr } = await admin.from("submissions").insert({
      id: sid,
      user_id: user.id,
      problem_id: problemId,
      verdict: null,
      score: null,
      summary: null,
      cases: [],
      files: sub.files,
      mode: sub.mode ?? sub.problem.contest_type,
      language: sub.language,
      file_label: sub.file_label,
      build_log: null,
      status: "judging",
      // 显式样例真跑结果随单落库（AI 评判与人工复核的共同事实）
      run_summary: {
        engine: run.engine,
        skipped: run.skipped,
        all_accepted: run.all_accepted,
        cases: run.cases,
      },
    });
    if (insErr) {
      return apiError("INTERNAL_ERROR", `服务异常，请重试：${insErr.message}`, 500);
    }

    // ---- 5. 后台异步 AI 评分（复用校验运行结果，不重复执行省积分）
    //      force_submit 备用通道 → 无论 AI 结论一律转人工复核
    EdgeRuntime.waitUntil(
      gradeInBackground({ sid, problemId, sub, run, forceReview: forceSubmit }).catch((e) =>
        console.error("gradeInBackground failed", sid, e),
      ),
    );

    // ---- 6. 回执 ----
    return json({ submissionId: sid, status: "judging" }, 202);
  } catch (e) {
    if (e instanceof PayloadError) {
      return apiError(e.code, e.message, e.status);
    }
    return apiError("INTERNAL_ERROR", `服务异常，请重试：${e?.message ?? e}`, 500);
  }
});
