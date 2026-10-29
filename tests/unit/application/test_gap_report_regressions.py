import json
from itertools import permutations

from benchside.reporting import summarise


def batch(path, observations):
    path.write_text(json.dumps({"schema": "benchside.gaps.v1", "observations": observations}))
    return path


def observation(identifier, question="Synthetic workflow need"):
    return {"id": identifier, "gap": {"kind": "missing_index", "question": question}}


def test_retries_and_rebatching_count_observation_ids_once(tmp_path):
    first, second = observation("o-first"), observation("o-second")
    files = [
        batch(tmp_path / "first.json", [first]),
        batch(tmp_path / "retry.json", [first]),
        batch(tmp_path / "rebatched.json", [first, second]),
    ]
    report = summarise(files)
    # Equal descriptions with different independently generated IDs remain distinct.
    assert report["workflow_observations"] == 2
    assert report["workflow_kinds"] == {"missing_index": 2}
    assert report["conflicting_snapshots"] == 0


def test_edited_retry_of_same_observation_is_excluded_as_conflicting(tmp_path):
    first = observation("o-first")
    edited = observation("o-first", "Synthetic clarification after a lost response")
    second = observation("o-second")
    files = [
        batch(tmp_path / "original.json", [first]),
        batch(tmp_path / "edited.json", [edited, second]),
        batch(tmp_path / "retry.json", [edited]),
    ]
    for ordering in permutations(files):
        report = summarise(ordering)
        assert report["workflow_observations"] == 1
        assert report["workflow_kinds"] == {"missing_index": 1}
        assert report["conflicting_snapshots"] == 1
        assert report["invalid_files"] == 0
