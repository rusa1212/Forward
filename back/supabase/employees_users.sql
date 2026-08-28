-- ============================================================
-- 사원 명부(employees) + 계정(users) 테이블
-- Supabase 대시보드 -> SQL Editor 에서 실행하세요.
-- (announcements 테이블은 이미 있다고 가정 — collector.py/storage.py가 쓰는 그 테이블)
-- ============================================================

create extension if not exists pgcrypto;

create table if not exists public.employees (
    emp_id      text primary key,
    name        text not null,
    department  text,
    created_at  timestamptz not null default now()
);

create table if not exists public.users (
    id             uuid primary key default gen_random_uuid(),
    emp_id         text not null unique references public.employees(emp_id),
    email          text not null unique,
    password_hash  text not null,
    created_at     timestamptz not null default now()
);

-- 시연/테스트용 사원 1명 (SignupPage.tsx 데모값과 동일 — 필요하면 실제 사원 명부로 교체)
insert into public.employees (emp_id, name, department)
values ('20230001', '김민준', '개발팀')
on conflict (emp_id) do nothing;

-- RLS: 로그인 전(anon)에도 사번 인증은 가능해야 하므로 employees는 조회만 열어둠.
-- users는 서버(BE)가 DATABASE_URL로 직접 접속해 처리하므로 RLS로 막아도 서버 동작에는 지장 없음.
alter table public.employees enable row level security;
create policy "사번 인증용 조회 허용" on public.employees for select using (true);

alter table public.users enable row level security;
-- 클라이언트(anon/authenticated)의 직접 접근은 차단 — BE(서버)만 이 테이블을 다룸
