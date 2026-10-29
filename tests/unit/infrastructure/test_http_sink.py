import hashlib
import io
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, build_opener

import pytest

from benchside import __version__
from benchside.domain.shared.error import BenchsideError
from benchside.infrastructure.http_sink import HttpExportSink, _NoRedirect

PAYLOAD = '{"schema":"benchside.gaps.v1","observations":[{"id":"o1","gap":{"kind":"missing_index","question":"🧬"}}]}'


class Response(io.BytesIO):
    status = 201


class Opener:
    def __init__(self, *, status=201, overrides=None):
        self.status = status
        self.overrides = overrides or {}
        self.requests = []

    def open(self, request, timeout):
        self.requests.append(request)
        assert timeout == 10
        data = {
            "status": "stored" if self.status == 201 else "duplicate",
            "sha256": hashlib.sha256(request.data).hexdigest(),
            "received_at": "2026-10-21T10:00:00Z",
            "observations": 1,
            **self.overrides,
        }
        response = Response(json.dumps(data).encode())
        response.status = self.status
        return response


@pytest.mark.parametrize("status", [200, 201])
def test_exact_bytes_and_verified_receipt(status):
    opener = Opener(status=status)
    sink = HttpExportSink("https://collector.example/v1/gaps", opener=opener)
    receipt = sink.send(PAYLOAD)
    assert opener.requests[0].data == PAYLOAD.encode("utf-8")
    assert receipt.sha256 == hashlib.sha256(PAYLOAD.encode("utf-8")).hexdigest()
    assert opener.requests[0].get_method() == "POST"
    assert opener.requests[0].get_header("User-agent") == f"Benchside/{__version__}"


@pytest.mark.parametrize(
    "overrides",
    [
        {"sha256": "wrong"},
        {"observations": 2},
        {"observations": True},
        {"received_at": "yesterday"},
        {"received_at": "2026-10-21T10:00:00"},
        {"status": "ok"},
        {"unexpected": "metadata"},
    ],
)
def test_unverifiable_receipt_is_a_failure(overrides):
    with pytest.raises(BenchsideError, match="receipt"):
        HttpExportSink(
            "https://collector.example/v1/gaps", opener=Opener(overrides=overrides)
        ).send(PAYLOAD)


@pytest.mark.parametrize("status", [302, 400, 413, 422, 429, 503])
def test_http_errors_do_not_get_treated_as_success(status):
    class Failing:
        def open(self, *args, **kwargs):
            raise HTTPError("https://collector.example", status, "failure", {}, None)

    with pytest.raises(BenchsideError):
        HttpExportSink("https://collector.example/v1/gaps", opener=Failing()).send(PAYLOAD)


@pytest.fixture
def denying_proxy():
    """A host egress proxy that refuses every CONNECT, as Claude's did on 29 October."""
    seen = []

    class Deny(BaseHTTPRequestHandler):
        def do_CONNECT(self):
            seen.append(self.path)
            self.send_response(403, "Forbidden")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Deny)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}", seen
    server.shutdown()
    server.server_close()


def test_egress_denial_keeps_code_and_explains_network_setting(denying_proxy):
    proxy, seen = denying_proxy
    opener = build_opener(ProxyHandler({"https": proxy}), _NoRedirect())
    sink = HttpExportSink("https://collector.example/v1/gaps", opener=opener)
    with pytest.raises(BenchsideError) as raised:
        sink.send(PAYLOAD)
    assert seen == ["collector.example:443"]  # The payload never left the tunnel request.
    assert raised.value.code == "submission_unavailable"
    message = str(raised.value)
    assert "network settings" in message and "collector.example" in message
    assert "Nothing was sent" in message and "still pending" in message


def test_http_403_does_not_claim_the_server_never_received_the_submission():
    class Refused:
        def open(self, *args, **kwargs):
            raise HTTPError("https://collector.example", 403, "Forbidden", {}, None)

    with pytest.raises(BenchsideError) as raised:
        HttpExportSink("https://collector.example/v1/gaps", opener=Refused()).send(PAYLOAD)
    assert raised.value.code == "submission_rejected"
    message = str(raised.value)
    assert "network settings" in message and "still pending" in message
    assert "before it reached" not in message
    assert "Nothing was sent" not in message
    assert "receipt" in message


def test_unreachable_collector_keeps_existing_guidance():
    class Offline:
        def open(self, *args, **kwargs):
            raise URLError(OSError("Name or service not known"))

    with pytest.raises(BenchsideError) as raised:
        HttpExportSink("https://collector.example/v1/gaps", opener=Offline()).send(PAYLOAD)
    assert raised.value.code == "submission_unavailable"
    assert (
        str(raised.value) == "Collector could not be reached; retry the same reviewed submission."
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://collector.example",
        "https://user:secret@collector.example",
        "https://collector.example/?key=secret",
        "file:///tmp/output",
    ],
)
def test_insecure_or_credentialled_destinations_rejected(url):
    with pytest.raises(BenchsideError):
        HttpExportSink(url)
