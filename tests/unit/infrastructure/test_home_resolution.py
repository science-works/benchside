"""The benchside home follows XDG, not a dotdir in ~."""

from pathlib import Path

from benchside.config import resolve_paths


class TestHomeResolution:
    def test_benchside_home_override_wins(self, monkeypatch, tmp_path):
        monkeypatch.setenv("BENCHSIDE_HOME", str(tmp_path / "custom"))
        assert resolve_paths().home == tmp_path / "custom"

    def test_default_is_xdg_data_home(self, monkeypatch):
        monkeypatch.delenv("BENCHSIDE_HOME", raising=False)
        monkeypatch.setenv("XDG_DATA_HOME", "/xdg/data")
        assert resolve_paths().home == Path("/xdg/data/benchside")

    def test_fallback_is_local_share(self, monkeypatch, tmp_path):
        monkeypatch.delenv("BENCHSIDE_HOME", raising=False)
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path))
        assert resolve_paths().home == tmp_path / ".local" / "share" / "benchside"
