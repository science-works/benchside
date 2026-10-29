import json
from itertools import permutations
from pathlib import Path

from benchside.reporting import markdown, summarise

LEGACY = "weekly-random-10pct-max5-v1"
RANDOM = "weekly-random-max20-v1"
MANUAL = "weekly-user-selected-max20-v1"


def activity(identifier, **changes):
    payload = json.loads(
        (Path(__file__).parents[2] / "fixtures/metascience/activity.json").read_text()
    )
    return {**payload, "batch_id": identifier * 32, **changes}


def save(tmp_path, *payloads):
    files = []
    for index, payload in enumerate(payloads):
        path = tmp_path / f"{index}.json"
        path.write_text(json.dumps(payload))
        files.append(path)
    return files


def test_report_separates_manual_capped_random_and_legacy_frames(tmp_path):
    legacy = activity("a")
    legacy.pop("sampling")  # Older payloads using the original default remain accepted.
    random = activity("b", sampling=RANDOM, eligible=100, selected=20)
    manual = activity("c", sampling=MANUAL, eligible=8, selected=8)
    report = summarise(save(tmp_path, legacy, random, manual, manual))
    assert report["activity_batches"] == 3
    assert report["invalid_files"] == report["conflicting_snapshots"] == 0
    grouped = report["activity_by_sampling"]
    assert set(grouped) == {LEGACY, RANDOM, MANUAL}
    for method, supplied, selected in [(LEGACY, 21, 3), (RANDOM, 100, 20), (MANUAL, 8, 8)]:
        assert grouped[method]["batches"] == 1
        assert grouped[method]["coverage"] == {
            "eligible_in_submitted_batches": supplied,
            "selected_in_submitted_batches": selected,
            "reviewed_and_shared": 1,
        }
        assert grouped[method]["findings"]["activity/analysis/model_inferred"] == 1
    assert "manual" in report["interpretation"].lower()
    assert "population" in report["interpretation"]
    rendered = markdown(report)
    assert "Researcher-chosen conversations" in rendered
    assert RANDOM in rendered and LEGACY in rendered


def test_report_rejects_method_switch_within_batch_even_at_newer_revision(tmp_path):
    first = activity("d", sampling=RANDOM, eligible=20, selected=20)
    changed = {**first, "revision": 2, "sampling": MANUAL}
    for ordering in permutations(save(tmp_path, first, changed)):
        report = summarise(ordering)
        assert report["activity_batches"] == 0
        assert report["conflicting_snapshots"] == 1
        assert report["activity_by_sampling"] == {}
