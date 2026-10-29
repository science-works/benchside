import json
from pathlib import Path

from benchside.reporting import summarise


def test_retries_and_revisions_do_not_inflate_usage(tmp_path):
    fixture = json.loads(
        (Path(__file__).parents[2] / "fixtures/reporting/benchside-usage.json").read_text()
    )
    old = tmp_path / "old.json"
    old.write_text(json.dumps(fixture))
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text(old.read_text())
    fixture["revision"] = 2
    fixture["sessions"][0]["started"] = 2
    newest = tmp_path / "new.json"
    newest.write_text(json.dumps(fixture))
    fixture["week"] = "2026-10-26"
    fixture["report_id"] = "d" * 32
    fixture["revision"] = 1
    fixture["sessions"][0]["started"] = 1
    next_week = tmp_path / "next.json"
    next_week.write_text(json.dumps(fixture))
    report = summarise([newest, old, duplicate, next_week])
    assert report["active_installations"] == 1
    assert report["returning_installations_across_weeks"] == 1
    assert report["consultations_by_role"]["methods-clinic"] == 3
    assert report["weekly"]["2026-10-19"]["started"] == 2
    assert "b" * 32 not in json.dumps(report)


def test_conflicting_same_revision_is_not_arbitrarily_counted(tmp_path):
    fixture = json.loads(
        (Path(__file__).parents[2] / "fixtures/reporting/benchside-usage.json").read_text()
    )
    first, other = tmp_path / "one.json", tmp_path / "two.json"
    first.write_text(json.dumps(fixture))
    fixture["sessions"][0]["started"] = 100
    other.write_text(json.dumps(fixture))
    report = summarise([first, other])
    assert report["conflicting_snapshots"] == 1
    assert report["active_installations"] == 0


def test_demographic_buckets_count_latest_report_per_installation(tmp_path):
    fixture = json.loads(
        (Path(__file__).parents[2] / "fixtures/reporting/benchside-usage.json").read_text()
    )
    fixture["demographics"] = {"discipline": "life_sciences", "career_stage": "doctoral_researcher"}
    first = tmp_path / "first.json"
    first.write_text(json.dumps(fixture))
    fixture["week"] = "2026-10-26"
    fixture["report_id"] = "d" * 32
    fixture["demographics"]["career_stage"] = "postdoctoral_researcher"
    latest = tmp_path / "latest.json"
    latest.write_text(json.dumps(fixture))
    report = summarise([first, latest, first])
    assert report["demographic_installations"] == 1
    assert report["installations_by_discipline"] == {"life_sciences": 1}
    assert report["installations_by_career_stage"] == {"postdoctoral_researcher": 1}
    fixture.pop("demographics")
    fixture["revision"] = 2
    cleared = tmp_path / "cleared.json"
    cleared.write_text(json.dumps(fixture))
    report = summarise([first, latest, cleared])
    assert report["demographic_installations"] == 0
    assert report["installations_by_discipline"] == {}
