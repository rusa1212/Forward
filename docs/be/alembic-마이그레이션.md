# DB 마이그레이션 (alembic)

> 대상: `back/` · 작성일 2026-09-01
> 스키마 정본은 이제 `back/alembic/versions/*.py` 입니다. `back/mysql/schema.sql`은 삭제됐습니다.

## 왜 도입했나

전에는 `schema.sql` 한 파일로 테이블을 만들었는데, `create table if not exists`라서
**이미 만들어진 테이블에는 컬럼 추가·변경이 안 먹었습니다.** 스키마를 바꾸면 팀원이 DB를 통째로
지우고 다시 만들거나 `ALTER TABLE`을 수동으로 쳐야 했고, 누가 어디까지 적용했는지 추적도 안 됐습니다.

alembic은 변경분을 버전이 매겨진 스크립트로 관리하고, `alembic_version` 테이블에
"이 DB가 몇 번까지 적용됐는지"를 기록합니다. 팀원은 `alembic upgrade head` 한 줄로 따라옵니다.

Supabase의 `supabase migration` / `supabase db push`에 해당합니다.

## 구조

```
back/
  alembic.ini            설정. 접속 URL은 여기 두지 않음(아래 참고)
  alembic/
    env.py               .env의 DATABASE_URL + app/db/models.py의 Base.metadata 연결
    script.py.mako       마이그레이션 파일 템플릿
    versions/
      0001_initial_schema.py   최초 5개 테이블 (구 schema.sql과 동일 결과)
```

- **접속 URL**: `alembic.ini`에 두지 않고 `env.py`가 `app.core.config.settings.DATABASE_URL`
  (= `back/.env`)을 읽어 주입합니다. 앱과 alembic이 항상 같은 DB를 봅니다.
- **autogenerate 기준**: `app/db/models.py`의 `Base.metadata`. 모델을 고치고 autogenerate하면
  차이를 감지해 마이그레이션 초안을 만들어 줍니다.

## 일상 작업

### 팀원이 pull 받았을 때

```bash
cd back
pip install -r requirements.txt      # alembic 포함
alembic upgrade head                 # 밀린 마이그레이션 전부 적용
```

### 스키마를 바꿀 때 (컬럼/테이블/인덱스 추가 등)

```bash
# 1) 먼저 app/db/models.py 를 수정한다  (ORM 모델이 기준)
# 2) 마이그레이션 초안 생성
alembic revision --autogenerate -m "add alert_settings table"
# 3) alembic/versions/ 에 새로 생긴 파일을 꼭 열어서 검토
#    - autogenerate가 놓치는 것: CHECK 제약, 서버 기본값 변경, 데이터 이관, 컬럼 rename(=drop+add로 나옴)
#    - MySQL이라 ENGINE/charset, 인덱스명도 확인
# 4) 내 DB에 적용
alembic upgrade head
# 5) 잘 되면 models.py + 새 버전 파일을 같이 커밋 → PR
```

### 자주 쓰는 명령

| 명령 | 설명 |
|---|---|
| `alembic current` | 이 DB가 지금 몇 번인지 |
| `alembic history` | 마이그레이션 목록 |
| `alembic upgrade head` | 최신까지 적용 |
| `alembic downgrade -1` | 한 단계 되돌리기 |
| `alembic downgrade base` | 전부 되돌리기 (테이블 다 삭제) |
| `alembic check` | 모델과 DB 사이에 미반영 변경이 있는지 (CI에 걸어두면 좋음) |
| `alembic stamp head` | DDL 없이 "최신으로 적용된 셈 치기" (아래) |

## 이미 MySQL을 쓰고 있던 팀원 (schema.sql로 만들었던 사람)

DB를 지울 필요 없습니다. `0001`은 구 `schema.sql`과 같은 결과라서, 적용된 셈만 표시하면 됩니다:

```bash
cd back
alembic stamp head        # alembic_version 테이블에 0001만 기록, 스키마는 안 건드림
alembic check             # "No new upgrade operations detected" 나오면 정상
```

이후부터는 새 마이그레이션을 `alembic upgrade head`로 정상적으로 받으면 됩니다.

## 권한 (로컬 vs 공용/운영)

alembic은 DDL(CREATE/ALTER/DROP)을 실행하므로 접속 계정에 해당 권한이 필요합니다.

- **로컬 개발**: 편의상 앱 계정(`forward`)에 `forward.*` ALL을 줘서 앱·마이그레이션 모두 이 계정으로 돌립니다.
- **공용/운영 DB**: 계정을 분리하세요.
  - 마이그레이션 계정: `forward` DB에 DDL 포함 전체 권한. 배포 파이프라인에서 `alembic upgrade head` 실행 시에만 사용.
  - 앱 런타임 계정: `SELECT, INSERT, UPDATE, DELETE`만. `back/.env`의 `DATABASE_URL`.
  - 이 경우 마이그레이션 실행 시에만 `DATABASE_URL`을 마이그레이션 계정으로 바꿔 주거나,
    별도 셸에서 그 URL로 `alembic`을 돌립니다.

## alembic이 하지 않는 것

- **데이터베이스 자체 생성**: `create database forward ...`는 사람이 먼저 해야 합니다 (README 4절).
- **시드 데이터**: 데모 사원은 `back/dev-seed.sql`로 분리했습니다. 마이그레이션에는 스키마만 둡니다.
