from __future__ import annotations

import csv
import datetime as dt
import html
import json
import os
import socket
import ssl
import threading
import time
import urllib.parse
import urllib.request
import zipfile
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"
DATA_DIR = ROOT / "stroop_data"
PAYLOAD_DIR = DATA_DIR / "payloads"
TRIALS_CSV = DATA_DIR / "trials.csv"
SUMMARY_CSV = DATA_DIR / "summary.csv"
EXPORT_ZIP = DATA_DIR / "stroop_data.zip"

HOST = os.environ.get("STROOP_HOST", "0.0.0.0")
PORT = int(os.environ.get("STROOP_PORT", "8766"))
ADMIN_PASSWORD = os.environ.get("STROOP_ADMIN_PASSWORD", "stroop-admin")
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
FEISHU_APP_TOKEN = os.environ.get("STROOP_FEISHU_APP_TOKEN", "")
FEISHU_SUMMARY_TABLE_ID = os.environ.get("STROOP_FEISHU_SUMMARY_TABLE_ID", "")
FEISHU_TRIALS_TABLE_ID = os.environ.get("STROOP_FEISHU_TRIALS_TABLE_ID", "")
FEISHU_API_BASE = os.environ.get("FEISHU_API_BASE", "https://open.feishu.cn/open-apis")

SUMMARY_COLUMNS = [
    "participant_name",
    "participant_id",
    "session_id",
    "started_at",
    "finished_at",
    "practice_trial_count",
    "formal_trial_count",
    "total_correct",
    "total_errors",
    "accuracy_percent",
    "mean_rt_correct_ms",
    "mean_rt_congruent_ms",
    "mean_rt_incongruent_ms",
    "mean_rt_neutral_ms",
    "stroop_interference_ms",
    "duration_sec",
    "trial_count",
]

TRIAL_COLUMNS = [
    "timestamp",
    "participant_name",
    "participant_id",
    "session_id",
    "trial_index",
    "block_type",
    "block_index",
    "trial_in_block",
    "formal_trial_index",
    "condition",
    "word",
    "ink_color",
    "ink_color_en",
    "correct_key",
    "response_key",
    "response_color",
    "accuracy",
    "rt_ms",
    "fixation_ms",
]

FEISHU_DATE_COLUMNS = {"started_at", "finished_at", "timestamp"}
FEISHU_BOOLEAN_COLUMNS = {"accuracy"}

write_lock = threading.Lock()
feishu_token_cache: dict[str, Any] = {"token": "", "expires_at": 0.0}


def ssl_context() -> ssl.SSLContext | None:
    cert_file = os.environ.get("SSL_CERT_FILE", "")
    if not cert_file and Path("/etc/ssl/cert.pem").exists():
        cert_file = "/etc/ssl/cert.pem"
    if not cert_file:
        return None
    return ssl.create_default_context(cafile=cert_file)


SSL_CONTEXT = ssl_context()


def local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    PAYLOAD_DIR.mkdir(exist_ok=True)


def format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def append_csv(path: Path, columns: list[str], row: dict[str, Any]) -> None:
    is_new = not path.exists()
    with path.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        if is_new:
            writer.writeheader()
        writer.writerow({column: format_value(row.get(column, "")) for column in columns})


def append_many_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    is_new = not path.exists()
    with path.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        if is_new:
            writer.writeheader()
        for row in rows:
            writer.writerow({column: format_value(row.get(column, "")) for column in columns})


def feishu_enabled() -> bool:
    return bool(FEISHU_APP_ID and FEISHU_APP_SECRET and FEISHU_APP_TOKEN and FEISHU_SUMMARY_TABLE_ID)


def request_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            **(headers or {}),
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20, context=SSL_CONTEXT) as response:
        response_body = response.read().decode("utf-8")
    data = json.loads(response_body)
    if data.get("code", 0) != 0:
        raise RuntimeError(f"Feishu API error: {data}")
    return data


def get_feishu_tenant_access_token() -> str:
    now = time.time()
    cached_token = str(feishu_token_cache.get("token") or "")
    if cached_token and float(feishu_token_cache.get("expires_at") or 0) > now + 60:
        return cached_token

    data = request_json(
        f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal",
        {
            "app_id": FEISHU_APP_ID,
            "app_secret": FEISHU_APP_SECRET,
        },
    )
    token = data.get("tenant_access_token")
    if not token:
        raise RuntimeError(f"Feishu token missing: {data}")
    expire = int(data.get("expire", 7200))
    feishu_token_cache["token"] = token
    feishu_token_cache["expires_at"] = now + expire
    return str(token)


def feishu_field_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float, str)):
        return value
    return json.dumps(value, ensure_ascii=False)


def feishu_date_value(value: Any) -> Any:
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    parsed: dt.datetime | None = None
    for fmt in ("%Y%m%d_%H%M%S", "%Y-%m-%d %H:%M:%S"):
        try:
            parsed = dt.datetime.strptime(text, fmt)
            parsed = parsed.replace(tzinfo=dt.datetime.now().astimezone().tzinfo)
            break
        except ValueError:
            pass
    if parsed is None:
        try:
            parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return text
    return int(parsed.timestamp() * 1000)


def feishu_boolean_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "正确"}


def feishu_fields(row: dict[str, Any], columns: list[str]) -> dict[str, Any]:
    return {
        column: feishu_date_value(row.get(column, ""))
        if column in FEISHU_DATE_COLUMNS
        else feishu_boolean_value(row.get(column, ""))
        if column in FEISHU_BOOLEAN_COLUMNS
        else feishu_field_value(row.get(column, ""))
        for column in columns
    }


def feishu_batch_create(table_id: str, rows: list[dict[str, Any]], columns: list[str]) -> int:
    if not rows:
        return 0
    token = get_feishu_tenant_access_token()
    url = f"{FEISHU_API_BASE}/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{table_id}/records/batch_create"
    total = 0
    for start in range(0, len(rows), 500):
        chunk = rows[start : start + 500]
        request_json(
            url,
            {"records": [{"fields": feishu_fields(row, columns)} for row in chunk]},
            {"Authorization": f"Bearer {token}"},
        )
        total += len(chunk)
    return total


def feishu_push_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not feishu_enabled():
        return {"enabled": False}

    summary = payload.get("summary") or {}
    events = [row for row in payload.get("events") or [] if isinstance(row, dict)]
    if not isinstance(summary, dict):
        raise ValueError("summary must be an object")

    result = {
        "enabled": True,
        "summary_rows": feishu_batch_create(FEISHU_SUMMARY_TABLE_ID, [summary], SUMMARY_COLUMNS),
        "trial_rows": 0,
    }
    if FEISHU_TRIALS_TABLE_ID:
        result["trial_rows"] = feishu_batch_create(FEISHU_TRIALS_TABLE_ID, events, TRIAL_COLUMNS)
    return result


def save_payload(payload: dict[str, Any]) -> dict[str, Any]:
    ensure_data_dir()
    summary = payload.get("summary") or {}
    events = payload.get("events") or []
    if not isinstance(summary, dict):
        raise ValueError("summary must be an object")
    if not isinstance(events, list):
        raise ValueError("events must be a list")

    participant_id = str(summary.get("participant_id") or "unknown").strip() or "unknown"
    started_at = str(summary.get("started_at") or int(time.time()))
    safe_id = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in participant_id)[:80]
    safe_started = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in started_at)[:80]
    payload_path = PAYLOAD_DIR / f"{safe_id}_{safe_started}_{int(time.time())}.json"

    with write_lock:
        payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        append_csv(SUMMARY_CSV, SUMMARY_COLUMNS, summary)
        append_many_csv(TRIALS_CSV, TRIAL_COLUMNS, [row for row in events if isinstance(row, dict)])

    result = {"summary_rows": 1, "trial_rows": len(events)}
    feishu_result = feishu_push_payload(payload)
    return {**result, "feishu": feishu_result}


def admin_page(message: str = "") -> bytes:
    summary_count = max(0, sum(1 for _ in SUMMARY_CSV.open("r", encoding="utf-8-sig")) - 1) if SUMMARY_CSV.exists() else 0
    trial_count = max(0, sum(1 for _ in TRIALS_CSV.open("r", encoding="utf-8-sig")) - 1) if TRIALS_CSV.exists() else 0
    payload_count = len(list(PAYLOAD_DIR.glob("*.json"))) if PAYLOAD_DIR.exists() else 0
    safe_message = html.escape(message)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Stroop 管理页</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif; color: #202431; background: #f5f6f8; }}
    main {{ width: min(760px, calc(100vw - 32px)); margin: 48px auto; background: #fff; border: 1px solid #d8dde6; border-radius: 8px; padding: 28px; }}
    h1 {{ margin: 0 0 18px; }}
    input {{ min-height: 40px; padding: 6px 10px; border: 1px solid #c9ced8; border-radius: 8px; min-width: 220px; }}
    button, a.button {{ min-height: 42px; padding: 0 16px; border-radius: 8px; border: 1px solid #1769e0; background: #1769e0; color: white; font-weight: 700; text-decoration: none; display: inline-flex; align-items: center; margin: 6px 8px 6px 0; }}
    .muted {{ color: #5c6677; }}
    .message {{ color: #b42318; }}
  </style>
</head>
<body>
  <main>
    <h1>Stroop 管理页</h1>
    <p class="muted">summary: {summary_count} 行；trials: {trial_count} 行；payload: {payload_count} 个。</p>
    <p class="message">{safe_message}</p>
    <form method="post" action="/admin">
      <input type="password" name="password" placeholder="老师密码">
      <button type="submit">进入下载</button>
    </form>
  </main>
</body>
</html>""".encode("utf-8")


def admin_download_page(token: str) -> bytes:
    return f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Stroop 下载</title></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC',sans-serif;margin:40px;">
  <h1>Stroop 数据下载</h1>
  <p><a href="/admin/download?file=summary&token={token}">下载 summary.csv</a></p>
  <p><a href="/admin/download?file=trials&token={token}">下载 trials.csv</a></p>
  <p><a href="/admin/download?file=zip&token={token}">下载全部 zip</a></p>
</body>
</html>""".encode("utf-8")


def make_zip() -> None:
    ensure_data_dir()
    with zipfile.ZipFile(EXPORT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if SUMMARY_CSV.exists():
            zf.write(SUMMARY_CSV, SUMMARY_CSV.name)
        if TRIALS_CSV.exists():
            zf.write(TRIALS_CSV, TRIALS_CSV.name)
        if PAYLOAD_DIR.exists():
            for payload in PAYLOAD_DIR.glob("*.json"):
                zf.write(payload, f"payloads/{payload.name}")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(DOCS_DIR), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_POST(self) -> None:
        if self.path == "/submit":
            self.handle_submit()
            return
        if self.path == "/admin":
            self.handle_admin_login()
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_GET(self) -> None:
        if self.path.startswith("/admin/download"):
            self.handle_admin_download()
            return
        if self.path == "/admin":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(admin_page())
            return
        super().do_GET()

    def read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        return self.rfile.read(length)

    def handle_submit(self) -> None:
        try:
            payload = json.loads(self.read_body().decode("utf-8"))
            result = save_payload(payload)
            response = {"ok": True, **result}
            status = HTTPStatus.OK
        except Exception as exc:
            response = {"ok": False, "error": str(exc)}
            status = HTTPStatus.BAD_REQUEST
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))

    def handle_admin_login(self) -> None:
        body = self.read_body().decode("utf-8")
        params = dict(item.split("=", 1) for item in body.split("&") if "=" in item)
        password = urllib.parse.unquote_plus(params.get("password", ""))
        if password != ADMIN_PASSWORD:
            self.send_response(HTTPStatus.UNAUTHORIZED)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(admin_page("密码不正确。"))
            return
        token = str(int(time.time()))
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(admin_download_page(token))

    def handle_admin_download(self) -> None:
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        file_kind = params.get("file", [""])[0]
        if file_kind == "summary":
            path = SUMMARY_CSV
            filename = "stroop_summary.csv"
        elif file_kind == "trials":
            path = TRIALS_CSV
            filename = "stroop_trials.csv"
        elif file_kind == "zip":
            make_zip()
            path = EXPORT_ZIP
            filename = "stroop_data.zip"
        else:
            self.send_error(HTTPStatus.BAD_REQUEST)
            return
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(path.read_bytes())


def main() -> None:
    ensure_data_dir()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    ip = local_ip()
    print(f"Stroop server: http://127.0.0.1:{PORT}")
    print(f"Classroom URL: http://{ip}:{PORT}")
    print(f"Admin URL: http://127.0.0.1:{PORT}/admin")
    server.serve_forever()


if __name__ == "__main__":
    main()
