"""로컬 개발용 SMTP 싱크 서버.

이메일 발송 경로를 실제로 테스트할 때, 메일을 밖으로 보내지 않고 이 서버가 받아서
콘솔과 back/.dev-mail/ 폴더(.eml 파일)에 남긴다. notifier.py의 SMTP 발송 코드가
그대로 동작하는지 확인하는 용도.

사용법 (back/ 에서 실행):
    .venv\\Scripts\\python scripts\\dev_smtp_sink.py          # localhost:1025
    .venv\\Scripts\\python scripts\\dev_smtp_sink.py 1026     # 포트 변경

그리고 back/.env 에:
    SMTP_HOST=localhost
    SMTP_PORT=1025
    SMTP_USE_TLS=false
"""
import sys
import threading
from datetime import datetime
from email import message_from_bytes
from email.policy import default as default_policy
from pathlib import Path

from aiosmtpd.controller import Controller

_OUT_DIR = Path(__file__).resolve().parent.parent / ".dev-mail"


class _SinkHandler:
    async def handle_DATA(self, server, session, envelope):
        _OUT_DIR.mkdir(exist_ok=True)
        msg = message_from_bytes(envelope.content, policy=default_policy)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        path = _OUT_DIR / f"{stamp}.eml"
        path.write_bytes(envelope.content)

        print(f"\n{'=' * 60}")
        print(f"수신: {envelope.mail_from} -> {', '.join(envelope.rcpt_tos)}")
        print(f"제목: {msg.get('Subject')}")
        body = msg.get_body(preferencelist=("plain",))
        if body is not None:
            print(f"본문:\n{body.get_content().strip()}")
        print(f"저장: {path}")
        print(f"{'=' * 60}", flush=True)
        return "250 Message accepted for delivery"


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 1025
    controller = Controller(_SinkHandler(), hostname="localhost", port=port)
    controller.start()
    print(f"dev SMTP sink listening on localhost:{port} (Ctrl+C to stop)", flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        controller.stop()


if __name__ == "__main__":
    main()
