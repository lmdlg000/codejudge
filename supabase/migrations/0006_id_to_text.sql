-- 0006_id_to_text.sql —— submissions.id 从 uuid 改为 text
-- 根因：judge 函数的 newSid() 生成可读文本 ID（如 20261031-084607-P7-f444），
--       但 id 列是 uuid 类型，导致 "invalid input syntax for type uuid"
-- 执行入口：Supabase Dashboard → SQL Editor → 整段一次性执行

-- 1) 先解除 human_review_queue → submissions 的外键（列类型不同无法直接改）
alter table public.human_review_queue
  drop constraint if exists human_review_queue_submission_id_fkey;

-- 2) submissions.id: uuid → text（保留已有数据）
alter table public.submissions
  alter column id drop default,
  alter column id type text using id::text;

-- 3) human_review_queue.submission_id 保持 text（已是 text），重建外键
alter table public.human_review_queue
  add constraint human_review_queue_submission_id_fkey
  foreign key (submission_id) references public.submissions (id) on delete cascade;
