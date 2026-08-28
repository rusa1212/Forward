-- ============================================================
-- 저장공고(saved_announcements) 테이블
-- Supabase 대시보드 -> SQL Editor 에서 실행하세요.
-- (employees_users.sql이 먼저 있어야 합니다 — users 테이블 참조,
--  announcements 테이블도 이미 있어야 합니다)
-- ============================================================

create extension if not exists pgcrypto;

create table if not exists public.saved_announcements (
    id                uuid primary key default gen_random_uuid(),
    user_id           uuid not null references public.users(id) on delete cascade,
    announcement_id   uuid not null references public.announcements(id) on delete cascade,
    saved_at          timestamptz not null default now(),
    constraint saved_announcements_user_id_announcement_id_key unique (user_id, announcement_id)
);

-- RLS: BE(서버)가 DATABASE_URL로 직접 접속해 처리하고, 요청마다 JWT의 user_id로 소유권을 검증합니다.
-- 클라이언트(anon/authenticated)의 직접 접근은 차단 — BE(서버)만 이 테이블을 다룸.
alter table public.saved_announcements enable row level security;
