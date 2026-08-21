"""The UI layer: plain/rich renderers with identical wording, stderr chrome.

Conventions under test (adopted from the OSA SDK pattern):
- chrome goes to the UI's file (stderr in production); data stays on stdout
- plain output is exact-string testable; rich differs only in ANSI
- NO_COLOR / CI / dumb terminals force plain
"""

import io

from benchside.cli.ui import UI


def make_plain() -> tuple[UI, io.StringIO]:
    buffer = io.StringIO()
    ui = UI.create(file=buffer, force_plain=True)
    return ui, buffer


class TestPlainRenderer:
    def test_success_line(self):
        ui, buffer = make_plain()
        ui.success("Sitting open with /pi on project 'plex'")
        assert buffer.getvalue() == "✓ Sitting open with /pi on project 'plex'\n"

    def test_error_with_cause_and_hint(self):
        ui, buffer = make_plain()
        ui.error("No open sitting for project 'plex'", hint="Run `bench sitting open --persona pi`")
        assert buffer.getvalue() == (
            "✗ No open sitting for project 'plex'\n"
            "→ Run `bench sitting open --persona pi`\n"
        )

    def test_warn_and_detail(self):
        ui, buffer = make_plain()
        ui.warn("2 critiques still open")
        ui.detail("k-123: method (confound): qPCR")
        assert buffer.getvalue() == (
            "⚠ 2 critiques still open\n"
            "  k-123: method (confound): qPCR\n"
        )

    def test_table_is_aligned(self):
        ui, buffer = make_plain()
        ui.table(["ID", "STATE"], [["c-1", "converged"], ["c-22", "abandoned"]])
        lines = buffer.getvalue().splitlines()
        assert lines[0].index("STATE") == lines[1].index("converged")
        assert lines[0].index("STATE") == lines[2].index("abandoned")


class TestRendererSelection:
    def test_no_color_env_forces_plain(self, monkeypatch):
        monkeypatch.setenv("NO_COLOR", "1")
        buffer = io.StringIO()
        ui = UI.create(file=buffer)
        ui.success("hello")
        assert "\x1b[" not in buffer.getvalue()

    def test_non_tty_is_plain(self):
        buffer = io.StringIO()  # StringIO has no tty
        ui = UI.create(file=buffer)
        ui.success("hello")
        assert "\x1b[" not in buffer.getvalue()


class TestRecordingRenderer:
    def test_events_are_recorded_in_order(self):
        from benchside.cli.ui import RecordingRenderer

        recorder = RecordingRenderer()
        ui = UI(renderer=recorder)
        ui.info("a")
        ui.error("b", hint="h")
        assert [event for event, _ in recorder.events] == ["info", "error"]
        assert recorder.events[1][1]["hint"] == "h"
