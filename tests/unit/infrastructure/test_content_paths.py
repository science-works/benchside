"""Regression test for content resolution off-repo (bug B4).

An installed user has no repo checkout: benchside/config.py's repo_root
defaulted into site-packages, where content/ does not exist. Content must
fall back to packaged data.
"""

from benchside.config import resolve_content_root


class TestB4ContentOffRepo:
    def test_env_override_wins(self, tmp_path, monkeypatch):
        (tmp_path / "content").mkdir()
        monkeypatch.setenv("BENCHSIDE_REPO", str(tmp_path))
        assert resolve_content_root() == tmp_path / "content"

    def test_packaged_content_is_found_without_a_repo(self, monkeypatch, tmp_path):
        """Simulate the installed case: no env var, cwd far from any checkout."""
        monkeypatch.delenv("BENCHSIDE_REPO", raising=False)
        monkeypatch.chdir(tmp_path)
        root = resolve_content_root()
        assert root.is_dir(), f"content root does not exist: {root}"
        assert (root / "personas").is_dir(), "packaged content must include personas/"
