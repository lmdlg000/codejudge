// supabase/functions/admin-review/index.ts —— 人工复核裁决（admin-review）
// 复核人（reviewers 白名单）提交最终裁决 → status = human_reviewed_pass | human_reviewed_fail
// 安全模型：用户 JWT 鉴权 + 服务端查 reviewers 白名单；写库走 SUPABASE_SECRET_KEY（绕过 RLS）。
//
// 部署：supabase functions deploy admin-review
import { createClient } from "npm:@supabase/supabase-js@2";
import { apiError, corsHeaders, json, readJson, supabasePublishableKey, supabaseSecretKey } from "../_shared/util.ts";

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }
  if (req.method !== "POST") {
    return apiError("VALIDATION_ERROR", "提交内容不合法，请检查后重试：仅支持 POST", 405);
  }

  try {
    const authHeader = req.headers.get("Authorization") ?? "";
    const jwt = authHeader.replace(/^Bearer\s+/i, "");
    const supabaseUrl = Deno.env.get("SUPABASE_URL") ?? "";
    const publishable = supabasePublishableKey();
    const secret = supabaseSecretKey();
    if (!jwt) {
      return apiError("UNAUTHORIZED", "请先登录（登录状态可能已过期）", 401);
    }
    if (!supabaseUrl || !publishable || !secret) {
      return apiError(
        "ENGINE_UNAVAILABLE",
        "服务端未正确配置 Supabase 密钥（SUPABASE_PUBLISHABLE_KEYS / SUPABASE_SECRET_KEYS），请检查 Edge Secrets 后重新部署",
        503,
      );
    }

    // 1. 鉴权
    const { data: userData, error: userErr } = await createClient(supabaseUrl, publishable, {
      global: { headers: { Authorization: authHeader } },
      auth: { persistSession: false },
    }).auth.getUser();
    if (userErr || !userData?.user) {
      return apiError("UNAUTHORIZED", "请先登录（登录状态可能已过期）", 401);
    }
    const uid = userData.user.id;
    const admin = createClient(supabaseUrl, secret, { auth: { persistSession: false } });

    // 2. 复核人白名单
    const { data: rev, error: revErr } = await admin
      .from("reviewers")
      .select("id")
      .eq("id", uid)
      .maybeSingle();
    if (revErr || !rev) {
      return apiError("UNAUTHORIZED", "当前账号无复核权限，请联系管理员加入 reviewers 名单", 403);
    }

    // 3. 校验裁决入参（pass|fail|bad_data：bad_data=数据问题，退回重审）
    const body = await readJson(req);
    const submissionId = String(body?.submission_id ?? "");
    const score = Number(body?.score);
    const feedback = String(body?.feedback ?? "").slice(0, 2000);
    const decision =
      body?.decision === "fail" ? "fail" : body?.decision === "bad_data" ? "bad_data" : "pass";
    if (!submissionId) {
      return apiError("VALIDATION_ERROR", "提交内容不合法，请检查后重试：submission_id 必填");
    }
    if (!Number.isFinite(score) || score < 0 || score > 100) {
      return apiError("VALIDATION_ERROR", "提交内容不合法，请检查后重试：分数须为 0–100 的数字");
    }

    // 4. 收队列 + 改状态
    //    pass → human_reviewed_pass；fail → human_reviewed_fail；
    //    bad_data → 提交退回 pending_review 并以高优先级重新入队（reason=bad_data）
    const newStatus =
      decision === "bad_data" ? "pending_review" : `human_reviewed_${decision}`;
    const { data: qrow, error: qerr } = await admin
      .from("human_review_queue")
      .update({
        status: "done",
        human_verdict: decision,
        reviewed_by: uid,
        reviewed_score: score,
        reviewed_feedback: feedback,
        reviewed_at: new Date().toISOString(),
      })
      .eq("submission_id", submissionId)
      .eq("status", "pending")
      .select("id")
      .maybeSingle();
    if (qerr) {
      return apiError("INTERNAL_ERROR", `服务异常，请重试：${qerr.message}`, 500);
    }
    if (!qrow) {
      return apiError("VALIDATION_ERROR", "提交内容不合法，请检查后重试：该复核任务不存在或已被裁决");
    }
    const { error: uerr } = await admin
      .from("submissions")
      .update(
        decision === "bad_data"
          ? { status: newStatus } // 数据问题：分数等保持原样，等重新裁决
          : {
              status: newStatus,
              score,
              reviewed_feedback: feedback,
              reviewed_at: new Date().toISOString(),
            },
      )
      .eq("id", submissionId);
    if (uerr) {
      return apiError("INTERNAL_ERROR", `服务异常，请重试：${uerr.message}`, 500);
    }

    // bad_data：以高优先级重新入队，交由（另一位）管理员重新裁决
    if (decision === "bad_data") {
      const { data: subRow } = await admin
        .from("submissions")
        .select("score, ai_feedback")
        .eq("id", submissionId)
        .maybeSingle();
      await admin.from("human_review_queue").insert({
        submission_id: submissionId,
        reason: "bad_data",
        priority: "high",
        ai_score: subRow?.score ?? null,
        ai_feedback: subRow?.ai_feedback ?? feedback,
      });
    }

    return json({ submission_id: submissionId, status: newStatus });
  } catch (e) {
    return apiError("INTERNAL_ERROR", `服务异常，请重试：${e?.message ?? e}`, 500);
  }
});
