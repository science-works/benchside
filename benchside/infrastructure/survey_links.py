"""Survey-only link confirmation; no requests are made to supplied URLs."""

import ipaddress
import re
from urllib.parse import unquote, urlsplit

from benchside.domain.shared.error import ValidationError
from benchside.infrastructure.redaction import TextRedactor

URL = re.compile(r"https?://[^\s\"<>]+", re.IGNORECASE)


def survey_urls(text: str) -> set[str]:
    """Read links inside ordinary prose/Markdown without changing the answer."""
    urls = set()
    for match in URL.finditer(text):
        url = match.group()
        while url:
            previous = url
            url = url.rstrip(".,;:!\u2019\u201d'")
            for opening, closing in (("(", ")"), ("[", "]"), ("{", "}")):
                if url.endswith(closing) and url.count(closing) > url.count(opening):
                    url = url[:-1]
            if url == previous:
                break
        urls.add(url)
    return urls


def public_link_candidate(url: str) -> bool:
    """Reject mechanically risky links; public status still requires the researcher."""
    try:
        parts = urlsplit(url)
        host = parts.hostname or ""
        if (
            parts.scheme not in {"http", "https"}
            or parts.username is not None or parts.password is not None
            or parts.port is not None or "?" in url or "#" in url
            or not re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,63}", host)
            or host.endswith((".localhost", ".local", ".internal", ".lan", ".home", ".test", ".invalid"))
        ):
            return False
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            return False
        decoded = url
        for _ in range(4):
            changed = unquote(decoded)
            if changed == decoded:
                break
            decoded = changed
        if "%" in decoded or any(ord(char) < 33 for char in decoded) or any(
            char in decoded for char in "\\?#"
        ):
            return False
        return not any(f.category != "url" for f in TextRedactor().scan(decoded))
    except ValueError:
        return False


def confirmed_links(texts: list[str], confirmation) -> set[str]:
    urls = set().union(*(survey_urls(text) for text in texts))
    confirmation = [] if confirmation is None else confirmation
    if (
        not isinstance(confirmation, list) or len(confirmation) > 20
        or any(not isinstance(url, str) for url in confirmation)
        or len(set(confirmation)) != len(confirmation)
        or not set(confirmation) <= urls
    ):
        raise ValidationError(
            "Confirm only the exact public URLs present in these survey answers. Nothing was sent.",
            code="survey_public_link_confirmation_invalid",
        )
    return set(confirmation)
