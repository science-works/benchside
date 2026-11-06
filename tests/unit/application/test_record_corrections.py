"""Exercise the documented correction recipe without changing the event schema."""

import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import pytest

from benchside.application.app import App
from benchside.config import Paths, resolve_content_root
from benchside.infrastructure.journal.projection import JournalObservationReader
from tests.unit.application.test_native import Notebook


@pytest.mark.parametrize("native", [False, True], ids=["local", "native"])
def test_documented_correction_survives_restore_and_preserves_original(paths, native):
    paths = Paths(home=paths.home, repo_root=paths.repo_root, store_root=paths.home)
    book = Notebook() if native else None
    app = App(paths)

    def run(request):
        if book:
            result = book.run(request)
            assert result["ok"], result
            return result["result"]
        return app.run(request)

    setup = book.setup() if book else run({"action": "setup", "project_key": "correction"})
    ctx = {k: setup[k] for k in ("project_id", "session_id")}
    ctx["sitting_id"] = run({"action": "start", "role": "journal-club", **ctx})["sitting"]["id"]
    source = "synthetic-excerpt.md, Methods: allocation details omitted"
    original = {
        "kind": "literature", "summary": "Allocation was nonrandomized",
        "details": ["Earlier mistaken inference from convenience sampling."], "sources": [source],
    }
    earlier = run({"action": "record", **ctx, "record": original})["recorded"]
    # The actual documented payload must work with returned IDs in both adapters.
    guide = (resolve_content_root() / "app/references/app-api.md").read_text()
    recipe = guide.split("### Corrections and faithful recall", 1)[1]
    example = re.search(r"```json\n(.*?)\n```", recipe, re.DOTALL).group(1)
    for placeholder, value in {
        "<returned project ID>": ctx["project_id"],
        "<returned session ID>": ctx["session_id"],
        "<returned sitting ID>": ctx["sitting_id"],
        "<earlier record ID>": earlier,
        "<actual inspected source locator>": source,
    }.items():
        example = example.replace(placeholder, value)
    correction = json.loads(example)
    corrected = run(correction)["recorded"]
    assert corrected != earlier
    # Put both entries outside the default recent window.
    for i in range(5):
        run({"action": "record", **ctx, "record": {
            "kind": "literature", "summary": f"Later note {i}",
            "details": ["No further allocation information."], "sources": [source],
        }})
    if native:
        fresh = Notebook()
        fresh.document, fresh.workspace_id = book.document, book.workspace_id
        saved_document = fresh.document
        recalled = fresh.run({"action": "recall", **ctx, "history": "all"})
        assert not recalled["changed"] and fresh.document == saved_document
        result = recalled["result"]
        reading_copies = [recalled["project_journal"]["markdown"]]
    else:
        app = App(paths)
        journal_before = paths.journal_file(ctx["project_id"]).read_bytes()
        result = app.run({"action": "recall", **ctx, "history": "all"})
        assert paths.journal_file(ctx["project_id"]).read_bytes() == journal_before
        app.run({"action": "records.configure", "format": "both"})
        exported = app.run({"action": "records.export", "project_id": ctx["project_id"]})
        with zipfile.ZipFile(exported["odt"]) as archive:
            odt = ElementTree.fromstring(archive.read("content.xml"))
        reading_copies = [Path(exported["markdown"]).read_text(), "".join(odt.itertext())]
        assert JournalObservationReader(app.journal).list_all() == []
    records = result["recent_records"]
    assert len(records) == 7
    assert records[0] == {"id": earlier, **original}
    assert records[1] == {"id": corrected, **correction["record"]}
    for text in reading_copies:
        assert original["summary"] in text
        assert correction["record"]["summary"] in text
        assert f"Corrects record {earlier}" in text
    assert not run({"action": "sharing.status"})["gaps"]["enabled"]


def test_onboarding_skip_profile_example_is_valid_and_private(paths):
    guide = (resolve_content_root() / "app/references/onboarding.md").read_text()
    example = re.search(r'`(\{"action":"profile.set"[^`]+\})`', guide).group(1)
    app = App(paths)
    app.run(json.loads(example))
    saved = App(paths).run({"action": "profile.status"})
    assert saved["revision"] > 0
    assert saved["demographics"] == {"discipline": None, "career_stage": None}
    assert not saved["include_in_usage"]
    assert not app.run({"action": "sharing.status"})["usage"]["enabled"]
