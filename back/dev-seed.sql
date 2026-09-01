-- 로컬 개발용 시드 데이터 (선택). 스키마는 alembic이 만들고, 이 파일은 데모용 행만 넣습니다.
-- 실행: mysql -u root -p forward < back/dev-seed.sql
-- (alembic upgrade head 를 먼저 실행해 테이블이 있어야 합니다)
--
-- SignupPage.tsx 데모값과 동일한 시연용 사원 1명. 실제 사원 명부로 교체하세요.

set names utf8mb4;

insert ignore into employees (emp_id, name, department)
values ('20230001', '김민준', '개발팀');
