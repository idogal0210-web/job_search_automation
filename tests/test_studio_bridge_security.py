"""Security regression tests for the loopback Career Studio bridge and the shared URL guard."""

import json
import os
import socket
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import MagicMock, patch

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.studio_bridge import (  # noqa: E402
    BridgeServices,
    is_allowed_host_header,
    make_handler,
    parse_content_length,
)
from src import url_guard  # noqa: E402
from src.url_guard import UnsafeUrlError, is_public_ip, safe_get, validate_public_http_url  # noqa: E402

TOKEN = "unit-test-token"
GOOD_ORIGIN = "http://127.0.0.1:8000"


class _NoAiServices(BridgeServices):
    """Services stub: every POST route returns a fixed marker without touching Gemini or disk."""

    def __init__(self):
        super().__init__(pool=MagicMock())
        self.calls = 0

    def ingest_job(self, payload):
        self.calls += 1
        return 200, {"ok": True, "marker": "ingest"}

    def profile(self):
        return {"ok": True, "profile": {"contact": {"email": "private@example.com"}}}


class BridgeSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.svc = _NoAiServices()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(cls.svc, session_token=TOKEN))
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _raw(self, method, path, headers, body=b""):
        lines = [f"{method} {path} HTTP/1.1"]
        lines += [f"{k}: {v}" for k, v in headers.items()]
        lines += ["Connection: close", "", ""]
        with socket.create_connection(("127.0.0.1", self.port), timeout=5) as sock:
            sock.sendall("\r\n".join(lines).encode("utf-8") + body)
            chunks = []
            while True:
                data = sock.recv(65536)
                if not data:
                    break
                chunks.append(data)
        raw = b"".join(chunks).decode("utf-8", errors="replace")
        head, _, payload = raw.partition("\r\n\r\n")
        status = int(head.split(" ", 2)[1])
        try:
            parsed = json.loads(payload) if payload else {}
        except json.JSONDecodeError:
            parsed = {}
        return status, head, parsed

    def _post_headers(self, body, **overrides):
        headers = {
            "Host": f"127.0.0.1:{self.port}",
            "Origin": GOOD_ORIGIN,
            "X-Studio-Token": TOKEN,
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        }
        headers.update(overrides)
        return {k: v for k, v in headers.items() if v is not None}

    def test_post_happy_path(self):
        body = b'{"text": "x"}'
        status, _, data = self._raw("POST", "/api/studio/ingest", self._post_headers(body), body)
        self.assertEqual(status, 200)
        self.assertEqual(data.get("marker"), "ingest")

    def test_post_rejects_foreign_origin_simple_request(self):
        body = b'{"text": "x"}'
        before = self.svc.calls
        headers = self._post_headers(body, Origin="https://evil.example.com", **{"Content-Type": "text/plain"})
        status, head, data = self._raw("POST", "/api/studio/ingest", headers, body)
        self.assertEqual(status, 403)
        self.assertEqual(data["error_code"], "origin_not_allowed")
        self.assertNotIn("Access-Control-Allow-Origin", head)
        self.assertEqual(self.svc.calls, before, "handler must not execute for a foreign origin")

    def test_post_rejects_missing_origin(self):
        body = b"{}"
        status, _, data = self._raw("POST", "/api/studio/ingest", self._post_headers(body, Origin=None), body)
        self.assertEqual(status, 403)

    def test_post_rejects_missing_or_wrong_token(self):
        body = b"{}"
        for tok in (None, "wrong-token"):
            status, _, data = self._raw("POST", "/api/studio/ingest", self._post_headers(body, **{"X-Studio-Token": tok}), body)
            self.assertEqual(status, 401)
            self.assertEqual(data["error_code"], "invalid_token")

    def test_dns_rebinding_host_header_rejected(self):
        body = b"{}"
        for host in ("attacker.example.com:%d" % self.port, "127.0.0.1:1", "127.0.0.1"):
            status, _, data = self._raw("POST", "/api/studio/ingest", self._post_headers(body, Host=host), body)
            self.assertEqual(status, 403, host)
            self.assertEqual(data["error_code"], "invalid_host")
            status, _, _ = self._raw("GET", "/api/health", {"Host": host})
            self.assertEqual(status, 403, host)

    def test_negative_content_length_rejected_without_blocking(self):
        status, _, data = self._raw("POST", "/api/studio/ingest", self._post_headers(b"", **{"Content-Length": "-1"}))
        self.assertEqual(status, 400)
        self.assertEqual(data["error_code"], "invalid_content_length")

    def test_non_json_content_type_rejected(self):
        body = b'{"text": "x"}'
        status, _, data = self._raw("POST", "/api/studio/ingest", self._post_headers(body, **{"Content-Type": "text/plain"}), body)
        self.assertEqual(status, 415)

    def test_session_token_only_for_allowed_origin_or_same_origin(self):
        host = {"Host": f"127.0.0.1:{self.port}"}
        status, head, data = self._raw("GET", "/api/session", {**host, "Origin": GOOD_ORIGIN})
        self.assertEqual(status, 200)
        self.assertEqual(data["token"], TOKEN)
        self.assertIn(f"Access-Control-Allow-Origin: {GOOD_ORIGIN}", head)

        status, head, data = self._raw("GET", "/api/session", {**host, "Origin": "https://evil.example.com"})
        self.assertEqual(status, 403)
        self.assertNotIn("token", data)

        status, _, data = self._raw("GET", "/api/session", {**host, "Sec-Fetch-Site": "cross-site"})
        self.assertEqual(status, 403)

        status, _, data = self._raw("GET", "/api/session", {**host, "Sec-Fetch-Site": "same-origin"})
        self.assertEqual(status, 200)

    def test_profile_requires_token(self):
        host = {"Host": f"127.0.0.1:{self.port}", "Origin": GOOD_ORIGIN}
        status, _, _ = self._raw("GET", "/api/profile", host)
        self.assertEqual(status, 401)
        status, _, data = self._raw("GET", "/api/profile", {**host, "X-Studio-Token": TOKEN})
        self.assertEqual(status, 200)

    def test_preflight_only_for_allowed_origin(self):
        host = {"Host": f"127.0.0.1:{self.port}", "Access-Control-Request-Method": "POST"}
        status, head, _ = self._raw("OPTIONS", "/api/studio/ingest", {**host, "Origin": GOOD_ORIGIN})
        self.assertEqual(status, 204)
        self.assertIn("X-Studio-Token", head)
        status, head, _ = self._raw("OPTIONS", "/api/studio/ingest", {**host, "Origin": "https://evil.example.com"})
        self.assertEqual(status, 403)
        self.assertNotIn("Access-Control-Allow-Origin", head)


class HelperTests(unittest.TestCase):
    def test_host_header_parser(self):
        self.assertTrue(is_allowed_host_header("127.0.0.1:8765", 8765))
        self.assertTrue(is_allowed_host_header("LOCALHOST:8765", 8765))
        self.assertTrue(is_allowed_host_header("[::1]:8765", 8765))
        self.assertFalse(is_allowed_host_header("127.0.0.1", 8765))
        self.assertFalse(is_allowed_host_header("evil.com:8765", 8765))
        self.assertFalse(is_allowed_host_header("127.0.0.1.evil.com:8765", 8765))
        self.assertFalse(is_allowed_host_header("", 8765))

    def test_content_length_parser(self):
        self.assertEqual(parse_content_length("0", 10), (0, None))
        self.assertEqual(parse_content_length(None, 10), (0, None))
        self.assertEqual(parse_content_length("10", 10), (10, None))
        self.assertEqual(parse_content_length("11", 10)[1], "payload_too_large")
        for bad in ("-1", "abc", "1e3", " -5 ", "+3"):
            self.assertEqual(parse_content_length(bad, 10)[1], "invalid_content_length", bad)


class UrlGuardTests(unittest.TestCase):
    def test_is_public_ip(self):
        for ip in ("8.8.8.8", "1.1.1.1", "2606:4700:4700::1111"):
            self.assertTrue(is_public_ip(ip), ip)
        for ip in ("10.0.0.1", "192.168.1.1", "127.0.0.1", "169.254.169.254", "100.64.0.1",
                   "100.127.255.254", "0.0.0.0", "::1", "fe80::1", "::ffff:127.0.0.1", "224.0.0.1", "not-an-ip"):
            self.assertFalse(is_public_ip(ip), ip)

    def test_cgnat_rejected_on_dns_path(self):
        fake = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("100.64.1.2", 0))]
        with patch("src.url_guard.socket.getaddrinfo", return_value=fake):
            ok, _ = validate_public_http_url("https://cgnat.example.com/job")
        self.assertFalse(ok)

    def test_literal_and_scheme_rejections(self):
        for bad in ("http://100.64.0.1/", "http://[::1]/", "file:///etc/passwd", "http://user:pw@example.com/",
                    "http://foo.localhost/", "ftp://example.com/", ""):
            self.assertFalse(validate_public_http_url(bad)[0], bad)

    def _resp(self, status, location=None, body=b"ok", peer="93.184.216.34"):
        resp = MagicMock()
        resp.is_redirect = status in (301, 302, 303, 307, 308)
        resp.is_permanent_redirect = status in (301, 308)
        resp.headers = {"Location": location} if location else {}
        resp.iter_content.return_value = [body]
        resp.raw.connection.sock.getpeername.return_value = (peer, 443)
        return resp

    def test_redirect_to_private_address_blocked(self):
        public = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
        with patch("src.url_guard.socket.getaddrinfo", return_value=public), \
             patch.object(url_guard.requests.Session, "get", return_value=self._resp(302, "http://169.254.169.254/latest")):
            with self.assertRaises(UnsafeUrlError):
                safe_get("https://jobs.example.com/apply")

    def test_rebinding_peer_check_blocks_private_peer(self):
        public = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
        with patch("src.url_guard.socket.getaddrinfo", return_value=public), \
             patch.object(url_guard.requests.Session, "get", return_value=self._resp(200, peer="10.0.0.5")):
            with self.assertRaises(UnsafeUrlError):
                safe_get("https://jobs.example.com/apply")

    def test_public_fetch_succeeds_and_follows_safe_redirect(self):
        public = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
        responses = [self._resp(301, "/final"), self._resp(200, body=b"<html>job</html>")]
        with patch("src.url_guard.socket.getaddrinfo", return_value=public), \
             patch.object(url_guard.requests.Session, "get", side_effect=responses) as mocked:
            resp = safe_get("https://jobs.example.com/apply")
        self.assertEqual(resp._content, b"<html>job</html>")
        self.assertEqual(mocked.call_args_list[1].args[0], "https://jobs.example.com/final")

    def test_redirect_limit(self):
        public = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
        with patch("src.url_guard.socket.getaddrinfo", return_value=public), \
             patch.object(url_guard.requests.Session, "get", side_effect=lambda *a, **k: self._resp(302, "/loop")):
            with self.assertRaises(UnsafeUrlError):
                safe_get("https://jobs.example.com/apply", max_redirects=3)


if __name__ == "__main__":
    unittest.main()
