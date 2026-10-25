-- 0004_uapi.sql —— 执行引擎换 UAPI + 强制显式样例校验配套
-- 流程：judge 函数前置同步校验（UAPI 逐个跑显式样例，任一失败 400 不落库）
--      → 全部通过才插入 judging → 后台 AI 语义评判（conclusive/低分转人工）

-- 1) submissions：记录提交语言（UAPI language 参数）
alter table public.submissions
  add column if not exists language text not null default 'cpp';

-- 2) human_review_queue：优先级 + 裁决类型（bad_data=数据问题退回重审）
alter table public.human_review_queue
  add column if not exists priority text not null default 'medium',
  add column if not exists human_verdict text;

comment on column public.human_review_queue.priority is 'high | medium | low（AI 分数 <40 或 AI 失败 = high）';
comment on column public.human_review_queue.human_verdict is 'pass | fail | bad_data（bad_data：数据问题，提交退回 pending_review 并重新入队）';
comment on column public.human_review_queue.reason is
  'low_score | inconclusive | ai_failed | bad_data（回补入队）';

-- priority 取值约束（幂等）
do $$
begin
  alter table public.human_review_queue
    add constraint human_review_queue_priority_chk check (priority in ('high', 'medium', 'low'));
exception
  when duplicate_object then null;
  when others then null;
end $$;
