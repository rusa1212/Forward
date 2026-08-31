-- ============================================================
-- Forward BE — MySQL/MariaDB 스키마 (Supabase Postgres에서 전환)
-- 요구: MySQL 5.7+ / MariaDB 10.3+ (utf8mb4, InnoDB)
-- 실행: mysql -u root -p < back/mysql/schema.sql
-- 주의: back/supabase/*.sql (Postgres용)은 더 이상 사용하지 않습니다.
--
-- Postgres 대비 달라진 점
--  - uuid 타입 → CHAR(36). PK 기본값은 DB가 아니라 앱(SQLAlchemy default)에서 생성.
--    (이 파일에서 직접 INSERT할 때는 UUID() 함수를 명시적으로 호출)
--  - timestamptz → DATETIME. 세션 time_zone을 UTC로 고정해 사용 (app/db/session.py).
--  - RLS 없음 → 접근 제어는 API 코드의 user_id 필터(WHERE user_id = 로그인사용자)에 전적으로 의존.
-- ============================================================

-- 클라이언트 연결 charset을 강제 (이게 없으면 클라이언트 기본값이 latin1일 때 아래 한글 시드가 깨짐)
set names utf8mb4;

create database if not exists forward
  default character set utf8mb4
  default collate utf8mb4_unicode_ci;

use forward;

-- ------------------------------------------------------------
-- 사원 명부 (회원가입 시 사번+이름 인증용)
-- ------------------------------------------------------------
create table if not exists employees (
    emp_id      varchar(20)  not null,
    name        varchar(50)  not null,
    department  varchar(100) null,
    created_at  datetime     not null default current_timestamp,
    primary key (emp_id)
) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 가입 계정 (emp_id는 사번 1개당 계정 1개)
-- ------------------------------------------------------------
create table if not exists users (
    id             char(36)     not null,
    emp_id         varchar(20)  not null,
    email          varchar(255) not null,
    password_hash  varchar(255) not null,
    created_at     datetime     not null default current_timestamp,
    primary key (id),
    unique key users_emp_id_key (emp_id),
    unique key users_email_key (email),
    constraint fk_users_emp_id foreign key (emp_id) references employees (emp_id)
) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 공고 (수집기 upsert 대상 — (source, external_id) UNIQUE가 중복 방지 기준)
-- ------------------------------------------------------------
create table if not exists announcements (
    id               char(36)     not null,
    source           varchar(50)  not null,
    external_id      varchar(100) not null,
    title            text         not null,
    department       varchar(255) null,
    reception_start  date         null,
    reception_end    date         null,
    status           varchar(50)  null,
    detail_url       text         null,
    summary          text         null,
    collected_at     datetime     not null default current_timestamp,
    primary key (id),
    unique key announcements_source_external_id_key (source, external_id),
    key idx_announcements_department (department),
    key idx_announcements_status (status),
    key idx_announcements_reception (reception_start, reception_end),
    key idx_announcements_collected_at (collected_at)
) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 사용자별 키워드
-- ------------------------------------------------------------
create table if not exists keywords (
    id          char(36)    not null,
    user_id     char(36)    not null,
    keyword     varchar(50) not null,
    created_at  datetime    not null default current_timestamp,
    primary key (id),
    unique key keywords_user_id_keyword_key (user_id, keyword),
    constraint fk_keywords_user_id foreign key (user_id) references users (id) on delete cascade,
    constraint keywords_keyword_length_check check (char_length(keyword) between 1 and 50)
) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 저장공고 (즐겨찾기)
-- ------------------------------------------------------------
create table if not exists saved_announcements (
    id               char(36) not null,
    user_id          char(36) not null,
    announcement_id  char(36) not null,
    saved_at         datetime not null default current_timestamp,
    primary key (id),
    unique key saved_announcements_user_id_announcement_id_key (user_id, announcement_id),
    key idx_saved_announcements_announcement_id (announcement_id),
    constraint fk_saved_user_id foreign key (user_id) references users (id) on delete cascade,
    constraint fk_saved_announcement_id foreign key (announcement_id) references announcements (id) on delete cascade
) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 시연/테스트용 사원 1명 (SignupPage.tsx 데모값과 동일 — 실제 사원 명부로 교체)
-- ------------------------------------------------------------
insert ignore into employees (emp_id, name, department)
values ('20230001', '김민준', '개발팀');
