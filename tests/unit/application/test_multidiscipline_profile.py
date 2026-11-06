import json
from pathlib import Path

import pytest

from benchside.application.app import App
from benchside.domain.shared.error import BenchsideError
from benchside.reporting import summarise


def test_multiple_disciplines_survive_and_only_enter_opted_in_usage(paths):
    app = App(paths)
    fields = ["computer_information_sciences", "life_sciences"]
    profile = {"discipline": fields, "career_stage": "research_staff"}
    app.run({"action": "profile.set", "demographics": profile, "include_in_usage": False})
    assert App(paths).run({"action": "profile.status"})["demographics"] == profile
    app.run({"action": "sharing.consent", "channel": "usage", "enabled": True})
    private = app.run({"action": "sharing.preview", "channel": "usage"})[0]
    assert "demographics" not in json.loads(private["preview"]["payload"])
    app.run({"action": "profile.set", "demographics": profile, "include_in_usage": True})
    shared = app.run({"action": "sharing.preview", "channel": "usage"})[0]
    assert shared["id"] != private["id"]
    assert json.loads(shared["preview"]["payload"])["demographics"] == profile


@pytest.mark.parametrize("disciplines", [[], ["life_sciences", "life_sciences"],
    ["life_sciences", "prefer_not_to_say"], ["A private project"], [12], "A private project"])
def test_invalid_multiselect_is_not_saved(paths, disciplines):
    with pytest.raises(BenchsideError):
        App(paths).run({"action": "profile.set", "demographics": {"discipline": disciplines}, "include_in_usage": False})
    assert App(paths).run({"action": "profile.status"})["demographics"]["discipline"] is None


def test_legacy_and_multiple_disciplines_count_once_per_installation(tmp_path):
    fixture = json.loads((Path(__file__).parents[2] / "fixtures/reporting/benchside-usage.json").read_text())
    fixture["demographics"] = {"discipline": "life_sciences"}
    old = tmp_path / "old.json"
    old.write_text(json.dumps(fixture))
    fixture["revision"] += 1
    fixture["demographics"] = {"discipline": ["computer_information_sciences", "life_sciences"]}
    latest = tmp_path / "new.json"
    latest.write_text(json.dumps(fixture))
    result = summarise([old, latest, latest])
    assert result["demographic_installations"] == 1
    assert result["installations_by_discipline"] == {"computer_information_sciences": 1, "life_sciences": 1}


def test_opted_in_analysis_can_wait_for_sources_without_enabling_activity_sharing(paths):
    app = App(paths)
    app.run({"action": "metascience.consent", "choice": "analysis", "enabled": True})
    state = App(paths).run({"action": "metascience.status"})
    assert state["choices"]["analysis"]
    assert not state["choices"]["sharing"]
    assert state["scopes"] == []
    with pytest.raises(BenchsideError, match="Select accessible"):
        app.run({"action": "metascience.sample", "candidates": []})
