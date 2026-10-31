// supabase/functions/_shared/scoring.ts —— AI 语义评判（基于 UAPI 真实运行数据）+ 分流
// 流程：显式样例已在 judge 前置校验全过（UAPI 真跑结果随任务传入，不重复执行省积分）→
//   把「代码 + 题目 + 实际运行结果」交给 AI → 高置信（conclusive）且分数达标 → status='ai_scored'；
//   否则（conclusive=false / 低分 / AI 失败）→ human_review_queue + status='pending_review'
import { createClient } from "npm:@supabase/supabase-js@2";
import type { NormalizedSubmission } from "./util.ts";
import { supabaseSecretKey } from "./util.ts";
import type { RunnerRun } from "./uapi.ts";

const DEFAULT_AI_URL = "https://api.openai.com/v1/chat/completions";

export interface AiResult {
  score: number;
  feedback: string;
  /** false = AI 无法可靠判断 → 转人工（参考设计的 conclusive 语义） */
  conclusive: boolean;
}

function env(name: string, fallback = ""): string {
  return Deno.env.get(name) ?? fallback;
}

function adminClient() {
  // 新密钥体系：SUPABASE_SECRET_KEYS（JSON 字典）自动解析（见 util.supabaseSecretKey）
  return createClient(env("SUPABASE_URL"), supabaseSecretKey());
}

function describeRun(run: RunnerRun): string {
  if (run.skipped === "not_configured") return "（本次未接入执行器实跑，请仅凭代码与题面评判）";
  if (run.skipped === "no_samples") return "（本题无样例可实跑，请仅凭代码与题面评判）";
  const lines: string[] = [];
  for (const c of run.cases) {
    lines.push(
      `用例 ${c.case}：状态=${c.status}` +
        (c.time_ms != null ? ` 耗时=${c.time_ms}ms` : "") +
        `\n  期望输出：${JSON.stringify(c.expected)}` +
        `\n  实际输出：${JSON.stringify(c.actual)}` +
        (c.stderr ? `\n  stderr：${JSON.stringify(c.stderr.slice(-500))}` : ""),
    );
  }
  if (run.compile_output) {
    lines.push(`编译输出（Compilation Error）：\n${run.compile_output.slice(-1500)}`);
  }
  return lines.join("\n\n") || "（无运行数据）";
}

function buildPrompt(
  n: NormalizedSubmission,
  problemId: string,
  run: RunnerRun,
): { system: string; user: string } {
  const p = n.problem;
  const filesText = n.files
    .map((f) => `===== ${f.name} =====\n${f.content}`)
    .join("\n\n");
  const system =
    "你是代码评分助手。已给出题面、提交代码，以及执行器（UAPI）的真实运行数据（stdout/stderr/状态）。" +
    "以真实运行数据为主要事实依据，结合代码语义给出 0-100 分和简要中文反馈。" +
    "若无法可靠判断，将 conclusive 设为 false。只返回 JSON：" +
    '{"score": number, "feedback": string, "conclusive": boolean}';
  const user =
    `题目编号：${problemId}\n题目标题：${p.title}\n计分模式：${p.contest_type}\n` +
    `限制：${p.limits.time_ms}ms / ${p.limits.memory_mb}MB\n\n` +
    `【题面】\n${p.statement_md}\n\n【提交代码】\n${filesText}\n\n` +
    `【真实运行数据（UAPI，显式样例已全部通过）】\n${describeRun(run)}`;
  return { system, user };
}

function parseAiJson(text: string): AiResult | null {
  if (!text) return null;
  const cleaned = text.replace(/```(?:json)?/gi, "");
  const start = cleaned.indexOf("{");
  const end = cleaned.lastIndexOf("}");
  if (start < 0 || end <= start) return null;
  try {
    const obj = JSON.parse(cleaned.slice(start, end + 1));
    const score = Number(obj.score);
    if (!Number.isFinite(score) || score < 0 || score > 100) return null;
    return {
      score: Math.round(score),
      feedback: String(obj.feedback ?? "").slice(0, 2000),
      conclusive: obj.conclusive !== false,
    };
  } catch {
    return null;
  }
}

/** 调 OpenAI 兼容接口评分（入参含 UAPI 运行数据）；失败返回 null。 */
export async function callAi(
  n: NormalizedSubmission,
  problemId: string,
  run: RunnerRun,
): Promise<AiResult | null> {
  const url = env("AI_API_URL", DEFAULT_AI_URL);
  const key = env("AI_API_KEY");
  const model = env("AI_MODEL", "gpt-4o-mini");
  if (!key) return null;
  const { system, user } = buildPrompt(n, problemId, run);
  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${key}`,
      },
      body: JSON.stringify({
        model,
        temperature: 0.2,
        response_format: { type: "json_object" },
        messages: [
          { role: "system", content: system },
          { role: "user", content: user },
        ],
      }),
    });
    if (!resp.ok) return null;
    const data = await resp.json();
    const text = data?.choices?.[0]?.message?.content ?? "";
    return parseAiJson(String(text));
  } catch {
    return null;
  }
}

/**
 * 后台评分主流程（judge Edge Function 的 EdgeRuntime.waitUntil 调用）。
 * run=显式样例真跑结果（前置校验产物，不重复执行省积分）。
 * forceReview=true（备用通道：样例未全过强制提交）→ 无论 AI 结论一律转人工复核。
 * 绝不抛出：任何异常都把提交转人工队列，避免卡在 judging。
 */
export async function gradeInBackground(opts: {
  sid: string;
  problemId: string;
  sub: NormalizedSubmission;
  run: RunnerRun;
  forceReview?: boolean;
}): Promise<void> {
  const { sid, problemId, sub, run, forceReview = false } = opts;
  const admin = adminClient();
  const scoreFloor = Number(env("AI_SCORE_THRESHOLD", "60")) || 60;

  async function toHumanReview(ai: AiResult | null, reason: string) {
    const priority = reason === "ai_failed" || reason === "force_submit" || (ai != null && ai.score < 40)
      ? "high"
      : "medium";
    const { error: insErr } = await admin.from("human_review_queue").insert({
      submission_id: sid,
      reason,
      priority,
      ai_score: ai ? ai.score : null,
      ai_feedback: ai ? ai.feedback : null,
    });
    if (insErr) {
      console.error("[gradeInBackground] human_review_queue insert failed:", sid, insErr.message, insErr);
      throw new Error(`hrq insert: ${insErr.message}`);
    }
    const { error: updErr } = await admin.from("submissions").update({
      status: "pending_review",
      score: ai ? ai.score : null,
      ai_feedback: ai ? ai.feedback : null,
      scored_at: new Date().toISOString(),
    }).eq("id", sid);
    if (updErr) {
      console.error("[gradeInBackground] submissions update failed:", sid, updErr.message, updErr);
      throw new Error(`sub update: ${updErr.message}`);
    }
    console.log("[gradeInBackground] toHumanReview OK:", sid, reason);
  }

  try {
    const ai = await callAi(sub, problemId, run);
    console.log("[gradeInBackground] callAi result:", sid, ai ? `score=${ai.score} conclusive=${ai.conclusive}` : "null");
    // 备用通道（样例未全过强制提交）：AI 只出参考分，最终以人工裁决为准
    if (forceReview) {
      await toHumanReview(ai, "force_submit");
      return;
    }
    const lowScore = ai != null && ai.score < scoreFloor;
    const inconclusive = ai == null || !ai.conclusive;

    if (ai != null && !inconclusive && !lowScore) {
      const { error: updErr } = await admin.from("submissions").update({
        status: "ai_scored",
        score: ai.score,
        ai_feedback: ai.feedback,
        scored_at: new Date().toISOString(),
      }).eq("id", sid);
      if (updErr) {
        console.error("[gradeInBackground] ai_scored update failed:", sid, updErr.message, updErr);
        throw new Error(`ai_scored update: ${updErr.message}`);
      }
      console.log("[gradeInBackground] ai_scored OK:", sid, ai.score);
      return;
    }
    const reason = ai == null ? "ai_failed" : lowScore ? "low_score" : "inconclusive";
    await toHumanReview(ai, reason);
  } catch (e) {
    console.error("[gradeInBackground] primary path failed:", sid, e);
    try {
      await toHumanReview(null, "ai_failed");
    } catch (e2) {
      console.error("[gradeInBackground] fallback toHumanReview also failed:", sid, e2);
    }
  }
}
