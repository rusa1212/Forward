"""
공통 오류 응답 구조 (5-1plan.md의 "권장 오류 응답 예시"와 동일한 형태로 통일)

{"success": false, "error": {"code": "DUPLICATE_EMAIL", "message": "이미 등록된 이메일입니다."}}
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException  # fastapi.HTTPException의 부모 클래스 — 라우팅 404 등도 여기서 잡힘


def error_body(code: str, message: str) -> dict:
    return {"success": False, "error": {"code": code, "message": message}}


class AppError(Exception):
    """라우터에서 의도적으로 던지는 에러. 예: raise AppError(409, "DUPLICATE_EMAIL", "이미 등록된 이메일입니다.")"""

    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content=error_body(exc.code, exc.message))

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content=error_body("HTTP_ERROR", str(exc.detail)))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content=error_body("VALIDATION_ERROR", "요청 값이 올바르지 않습니다."))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content=error_body("INTERNAL_ERROR", "서버 내부 오류가 발생했습니다."))
