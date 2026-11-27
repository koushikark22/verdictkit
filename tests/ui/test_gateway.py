"""The local gateway (scripts/gateway.mjs): loopback only, Host-checked, read-only static serving and a bounded API proxy.

Starts the real script with Node on a free port, with its API pointed at a throwaway fake backend. Skipped where Node
is not installed (for example in the Python container image). No credentials are passed to the child process.
"""
from __future__ import annotations

import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GATEWAY = ROOT / "scripts" / "gateway.mjs"
NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="Node.js is not installed")


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class FakeApi(BaseHTTPRequestHandler):
    seen: list[dict] = []

    def _reply(self):
        body = json.dumps({"contractVersion": "1.2.0", "path": self.path, "method": self.command}).encode()
        FakeApi.seen.append({"path": self.path, "method": self.command, "headers": {k.lower(): v for k, v in self.headers.items()}})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Set-Cookie", "must_not_reach_the_browser=1")
        self.end_headers()
        self.wfile.write(body)

    do_GET = do_POST = do_PATCH = _reply

    def log_message(self, *_args):
        pass


@pytest.fixture(scope="module")
def stack(tmp_path_factory):
    api_port, port = free_port(), free_port()
    api = HTTPServer(("127.0.0.1", api_port), FakeApi)
    threading.Thread(target=api.serve_forever, daemon=True).start()
    log = tmp_path_factory.mktemp("gw") / "gateway.log"
    env = {k: v for k, v in os.environ.items() if k in ("PATH", "Path", "SystemRoot", "SYSTEMROOT", "TEMP", "TMP", "HOME", "USERPROFILE")}
    proc = subprocess.Popen([NODE, str(GATEWAY), "--port", str(port), "--api-port", str(api_port), "--log", str(log)],
                            env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.3).close()
            break
        except OSError:
            time.sleep(0.1)
    else:
        proc.kill()
        pytest.fail("gateway did not start")
    yield port, api_port, log
    proc.terminate()
    proc.wait(timeout=10)
    api.shutdown()


def get(port: int, path: str, *, method: str = "GET", host: str | None = None, body: bytes | None = None, headers: dict | None = None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=8)
    h = {"Host": host or f"127.0.0.1:{port}", **(headers or {})}
    conn.request(method, path, body=body, headers=h)
    r = conn.getresponse()
    out = (r.status, {k.lower(): v for k, v in r.getheaders()}, r.read())
    conn.close()
    return out


def test_it_only_answers_on_its_own_loopback_name_which_blocks_dns_rebinding(stack):
    port, *_ = stack
    assert get(port, "/__gateway/health")[0] == 200
    assert get(port, "/__gateway/health", host=f"localhost:{port}")[0] == 200
    for evil in (f"evil.example:{port}", "127.0.0.1", f"127.0.0.1:{port + 1}", f"192.168.1.5:{port}"):
        assert get(port, "/api/v1/health", host=evil)[0] == 421, evil


def test_it_refuses_to_bind_anything_but_loopback():
    out = subprocess.run([NODE, str(GATEWAY), "--host", "0.0.0.0", "--port", str(free_port())], capture_output=True, text=True, timeout=15)
    assert out.returncode == 2 and "127.0.0.1 only" in (out.stderr + out.stdout)


def test_it_refuses_privileged_and_malformed_ports():
    for args in (["--port", "80"], ["--port", "70000"], ["--api-port", "abc"]):
        out = subprocess.run([NODE, str(GATEWAY), *args], capture_output=True, text=True, timeout=15)
        assert out.returncode == 2, args


def test_static_serving_is_read_only_and_cannot_leave_its_folders(stack):
    port, *_ = stack
    for hostile in ("/../package.json", "/%2e%2e/package.json", "/quote/../../package.json", "/quote/%2e%2e/%2e%2e/.git/config",
                    "/..%5c..%5cpackage.json", "/%00", "/quote/\\..\\..\\package.json", "/.git/config", "/.env", "/quote/.env", "/reel/.hidden/x"):
        status, _h, body = get(port, hostile)
        assert status in (400, 404, 503) and b"verdictkit-web" not in body and b"[core]" not in body and b"<!doctype" not in body.lower(), hostile
    for method in ("POST", "PUT", "DELETE", "PATCH"):
        assert get(port, "/", method=method)[0] == 405
    assert get(port, "/missing.js")[0] == 404
    assert get(port, "/quote")[0] == 308 and get(port, "/quote")[1]["location"] == "/quote/"


def test_the_responses_carry_security_headers_and_no_caching_of_html(stack):
    port, *_ = stack
    _status, headers, _body = get(port, "/__gateway/config.json")
    assert headers["x-content-type-options"] == "nosniff" and headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "no-referrer" and headers["cache-control"] == "no-store"


def test_the_api_proxy_forwards_an_allowlist_of_headers_and_drops_cookies_both_ways(stack):
    port, *_ = stack
    FakeApi.seen.clear()
    status, headers, body = get(port, "/api/v1/cases/case_x/outcome?x=1", headers={
        "Cookie": "session=secret", "Authorization": "Bearer secret", "X-Forwarded-For": "6.6.6.6", "Accept": "application/json"})
    assert status == 200 and json.loads(body)["path"] == "/api/v1/cases/case_x/outcome?x=1"
    seen = FakeApi.seen[-1]["headers"]
    assert "cookie" not in seen and "authorization" not in seen and "x-forwarded-for" not in seen
    assert seen["accept"] == "application/json"
    assert "set-cookie" not in headers, "an upstream cookie is not passed on to the browser"
    status, _h, body = get(port, "/api/v1/replays", method="POST", body=b"PK\x03\x04bundle", headers={"Content-Type": "application/zip"})
    assert status == 200 and FakeApi.seen[-1]["method"] == "POST" and FakeApi.seen[-1]["headers"]["content-type"] == "application/zip"
    assert get(port, "/api/v1/cases/x", method="PATCH", body=b"{}", headers={"Content-Type": "application/json"})[0] == 200


def test_unsupported_api_methods_are_refused_before_reaching_the_backend(stack):
    port, *_ = stack
    FakeApi.seen.clear()
    for method in ("DELETE", "PUT", "OPTIONS", "TRACE"):
        status, _h, body = get(port, "/api/v1/cases/x", method=method)
        assert status == 405 and json.loads(body)["error"]["code"] == "METHOD_NOT_ALLOWED"
    assert FakeApi.seen == []


def test_a_dead_backend_is_reported_as_backend_unavailable_not_as_a_hang(stack, tmp_path):
    _port, _api, _log = stack
    dead_api, port = free_port(), free_port()
    env = {k: v for k, v in os.environ.items() if k in ("PATH", "Path", "SystemRoot", "SYSTEMROOT", "TEMP", "TMP")}
    proc = subprocess.Popen([NODE, str(GATEWAY), "--port", str(port), "--api-port", str(dead_api), "--log", str(tmp_path / "g.log")],
                            env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.3).close()
                break
            except OSError:
                time.sleep(0.1)
        started = time.monotonic()
        status, _h, body = get(port, "/api/v1/health")
        assert status == 502 and json.loads(body)["error"]["code"] == "BACKEND_UNAVAILABLE"
        assert time.monotonic() - started < 6, "an unreachable backend must be reported promptly"
        assert b"contractVersion" not in body, "the gateway never invents a contract-versioned body"
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def test_the_gateway_logs_nothing_per_request(stack):
    port, _api, log = stack
    get(port, "/api/v1/cases/case_secret_identifier/outcome")
    text = log.read_text() if log.exists() else ""
    assert "case_secret_identifier" not in text and text.count("\n") <= 1


def test_python_can_import_this_module_without_node():
    assert sys.version_info >= (3, 12)
