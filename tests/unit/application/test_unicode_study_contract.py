"""Pin the same Unicode study canonical form exercised by the receiver tests."""

import json
from pathlib import Path

from benchside.domain.export.model.metascience import Study, SurveyPayload, canonical, digest


def test_unicode_study_matches_shared_canonical_bytes_and_digest():
    path = Path(__file__).parents[2] / "fixtures/metascience/unicode-study.json"
    fixture = json.loads(path.read_text())
    study = Study.model_validate(fixture["study"])
    assert canonical(study.model_dump()) == fixture["canonical"]
    assert digest(study.model_dump()) == fixture["sha256"]
    assert "—" in fixture["canonical"] and "🔬" in fixture["canonical"]
    SurveyPayload(
        benchside_version="0.1.1",
        response_id="a" * 32,
        study_id=study.id,
        study_version=study.version,
        study_sha256=fixture["sha256"],
        answers={"checked": "yes"},
    ).check_study(study)
