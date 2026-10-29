"""Conservative identifier scrubbing; human review is still required for free text."""

import json
import re

from benchside.domain.export.port.redactor import Finding

_PATTERNS = (
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
    ("local-path", re.compile(r"(?:/(?:Users|home)/[^\s\"<>]+|[A-Z]:\\Users\\[^\s\"<>]+)")),
    ("credential", re.compile(r"\b(?:sk-|ghp_|github_pat_)[A-Za-z0-9_-]{12,}\b")),
    ("url", re.compile(r"https?://[^\s\"<>]+")),
)


class TextRedactor:
    def apply(self, payload: str) -> str:
        data = json.loads(payload)

        def scrub(value):
            if isinstance(value, str):
                for label, pattern in _PATTERNS:
                    value = pattern.sub(f"[removed {label}]", value)
            elif isinstance(value, list):
                value = [scrub(item) for item in value]
            elif isinstance(value, dict):
                value = {key: scrub(item) for key, item in value.items()}
            return value

        # Only research-workflow text and feedback text are scrubbed. IDs,
        # schema names and controlled metadata must remain byte-for-byte values.
        for observation in data.get("observations", []):
            observation["gap"] = scrub(observation["gap"])
        if "feedback" in data:
            data["feedback"]["comment"] = scrub(data["feedback"]["comment"])
        return json.dumps(data, ensure_ascii=False, indent=2)

    def scan(self, payload: str) -> list[Finding]:
        # Patterns cannot detect names, unpublished results, or indirect identity.
        return [
            Finding(tier="HIGH", category=label, field="shared text")
            for label, pattern in _PATTERNS
            if pattern.search(payload)
        ]
