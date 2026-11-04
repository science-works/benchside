"""Reachability is independent of research storage, consent and submission."""

import io
from urllib.error import HTTPError

import pytest

from benchside.application.bridge import run
from benchside.domain.shared.error import InfrastructureError
from benchside.infrastructure.http_sink import COLLECTOR, USER_AGENT


@pytest.mark.parametrize("response", [b'{"studies":[]}', b'not a catalog', 403])
def test_connection_check_only_gets_catalog_without_opening_a_store(
    tmp_path, monkeypatch, response
):
    monkeypatch.setenv("BENCHSIDE_HOME", str(tmp_path / "private"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    # This diagnostic checks the official collector, not an overridden test sink.
    monkeypatch.setenv("BENCHSIDE_STUDIES_ENDPOINT", "https://elsewhere.example/catalog")
    calls = []

    class Opener:
        def open(self, request, timeout):
            calls.append(request)
            assert timeout == 10
            if response == 403:
                raise HTTPError(request.full_url, 403, "Forbidden", {}, io.BytesIO())
            result = io.BytesIO(response)
            result.status = 200
            return result

    monkeypatch.setattr("benchside.infrastructure.http_sink.build_opener", lambda *_: Opener())
    if response == b'{"studies":[]}':
        assert run({"action": "connection.check"}) == {
            "reachable": True,
            "endpoint": f"{COLLECTOR}/v1/studies",
            "method": "GET",
            "submitted": False,
        }
    else:
        with pytest.raises(InfrastructureError, match="no contribution was submitted"):
            run({"action": "connection.check"})
    assert len(calls) == 1
    assert calls[0].get_method() == "GET"
    assert calls[0].full_url == f"{COLLECTOR}/v1/studies"
    assert calls[0].data is None
    assert dict(calls[0].header_items()) == {
        "Accept": "application/json", "User-agent": USER_AGENT
    }
    assert list(tmp_path.iterdir()) == []
