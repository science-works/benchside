"""Write-only collector client: exact UTF-8 bytes, verified receipts, no redirects."""

import hashlib
import json
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from benchside import __version__
from benchside.domain.export.model.value import DeliveryReceipt
from benchside.domain.export.model.wire import MAX_BYTES
from benchside.domain.shared.error import ConfigurationError, InfrastructureError

COLLECTOR = "https://ingest.benchside.science.works"
USER_AGENT = f"Benchside/{__version__}"


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HttpExportSink:
    def __init__(self, destination: str, *, allow_local: bool = False, opener=None):
        url = urlsplit(destination)
        local = (
            allow_local
            and url.scheme == "http"
            and url.hostname in {"localhost", "127.0.0.1", "::1"}
        )
        if (
            (url.scheme != "https" and not local)
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
        ):
            raise ConfigurationError("The collector requires an HTTPS endpoint without credentials")
        self.destination = destination
        self._opener = opener or build_opener(_NoRedirect())

    def _network_denied(self, outcome: str, what: str) -> str:
        # Host-neutral: an app sandbox with network access off, or an institutional
        # proxy. Host-specific steps belong in that host's instructions.
        host = urlsplit(self.destination).hostname
        return (
            f"{outcome}: a network proxy {what} {host} before it reached Science Works. "
            "The reviewed submission is still pending. Once network access to "
            f"{host} is allowed in the app or network settings, retry the same reviewed "
            "submission. Do not change settings for the researcher."
        )

    def send(self, payload: str) -> DeliveryReceipt:
        body = payload.encode("utf-8")
        if len(body) > MAX_BYTES:
            raise InfrastructureError(
                "Submission exceeds the collector limit", code="submission_invalid"
            )
        request = Request(
            self.destination,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
        )
        try:
            with self._opener.open(request, timeout=10) as response:
                status = response.status
                raw = response.read(8193)
            if status not in {200, 201} or len(raw) > 8192:
                raise ValueError("Unexpected response")
            data = json.loads(raw)
            if set(data) != {"status", "sha256", "received_at", "observations"}:
                raise ValueError("Unexpected receipt fields")
            parsed = json.loads(payload)
            count = len(parsed["observations"]) if "observations" in parsed else 1
            expected_status = "stored" if status == 201 else "duplicate"
            if (
                data["status"] != expected_status
                or data["sha256"] != hashlib.sha256(body).hexdigest()
                or type(data["observations"]) is not int
                or data["observations"] != count
                or not isinstance(data["received_at"], str)
                or datetime.fromisoformat(data["received_at"]).tzinfo is None
            ):
                raise ValueError("Receipt does not match submission")
            return DeliveryReceipt.model_validate(data)
        except HTTPError as err:
            err.close()
            code = (
                "submission_rate_limited"
                if err.code == 429
                else ("submission_unavailable" if err.code >= 500 else "submission_rejected")
            )
            # An HTTP response can arrive after the destination received the POST.
            # Only a refused CONNECT tunnel below proves the payload was not sent.
            message = f"Collector returned HTTP {err.code}; nothing was marked as shared. Retry the same reviewed submission."
            if err.code == 403:
                host = urlsplit(self.destination).hostname
                message = (
                    "HTTP 403: no valid collector receipt was received; nothing was marked "
                    "as shared. The reviewed submission is still pending. A proxy or server "
                    f"policy may be refusing access to {host}. Check the app or network "
                    "settings before retrying the same reviewed submission. Do not change "
                    "settings for the researcher."
                )
            raise InfrastructureError(message, code=code) from err
        except (URLError, TimeoutError, OSError) as err:
            # Host egress proxies refuse the HTTPS tunnel before any payload is sent.
            if str(getattr(err, "reason", err)).startswith("Tunnel connection failed: 403"):
                raise InfrastructureError(
                    self._network_denied("Nothing was sent", "blocked the connection to"),
                    code="submission_unavailable",
                ) from err
            raise InfrastructureError(
                "Collector could not be reached; retry the same reviewed submission.",
                code="submission_unavailable",
            ) from err
        except (ValueError, TypeError, KeyError) as err:
            raise InfrastructureError(
                "Collector receipt could not be verified; retry the same reviewed submission.",
                code="submission_receipt_invalid",
            ) from err
