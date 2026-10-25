-- 0003_onecompiler.sql —— OneCompiler 真实运行数据 + 人工复核裁决状态（human_reviewed_*）
-- 流程升级：OneCompiler 确定性执行 → AI 基于运行数据语义评判
-- 人工介入条件：AI 低置信度 / 低分 / 编译失败

-- 1) submissions：OneCompiler 逐用例运行结果（AI 评判与人工复核的共同事实）
alter table public.submissions
  add column if not exists run_summary jsonb;

comment on column public.submissions.run_summary is
  'OneCompiler 运行结果（执行器 stdout/stderr/exception 推导）：{engine, skipped, all_accepted, cases:[{case,status,status_id,time_ms,memory_kb,expected,actual,stderr}]}';

-- 2) 复核裁决扩展：complete_review 增加 decision（pass|fail）
--    完成后 status = human_reviewed_pass / human_reviewed_fail（前端按 human_reviewed* 前缀识别）
create or replace function public.complete_review(
  p_submission_id text,
  p_score numeric,
  p_feedback text,
  p_decision text default 'pass'
) returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_decision text := case when p_decision = 'fail' then 'fail' else 'pass' end;
begin
  if not exists (select 1 from public.reviewers where id = auth.uid()) then
    raise exception 'not a reviewer';
  end if;

  update public.human_review_queue
     set status = 'done',
         reviewed_by = auth.uid(),
         reviewed_score = p_score,
         reviewed_feedback = p_feedback,
         reviewed_at = now()
   where submission_id = p_submission_id
     and status = 'pending';

  update public.submissions
     set status = 'human_reviewed_' || v_decision,
         score = p_score,
         reviewed_feedback = p_feedback,
         reviewed_at = now()
   where id = p_submission_id;
end $$;

revoke execute on function public.complete_review from public, anon;
grant execute on function public.complete_review to authenticated;

-- 3) 队列 reason 枚举扩展说明（无 DDL 变更，文档性注释）
comment on column public.human_review_queue.reason is
  'low_confidence | low_score | compile_failed | ai_failed';
