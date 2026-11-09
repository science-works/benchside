"""Survey-only public-link review never overrides other sensitive-text checks."""

import json

import pytest

from benchside.domain.shared.error import BenchsideError
from benchside.infrastructure.redaction import TextRedactor
from tests.unit.application.test_linked_contributions import join_text_study
from tests.unit.application.test_metascience import flow as flow  # noqa: PLC0414

URL = "https://imagej.net/software/fiji/"


@pytest.mark.parametrize("text", [f"See [Fiji]({URL})", f"See ({URL}).", f"See {URL}, please."])
def test_public_links_in_prose_preserve_answer_and_confirm_actual_url(flow, text):
    key = join_text_study(flow)
    draft = flow.survey(key, {"comment": {"text": text}}, confirmed_public_urls=[URL])
    flow.send(draft["id"], draft["sha256"], confirmed_public_urls=[URL])
    assert json.loads(flow.sinks["surveys"].sent[0])["answers"]["comment"]["text"] == text


def test_public_link_needs_confirmation_on_preview_and_send(flow):
    key = join_text_study(flow)
    answers = {"comment": {"text": f"The documentation is at {URL}"}}
    with pytest.raises(BenchsideError) as missing:
        flow.survey(key, answers)
    assert missing.value.code == "survey_public_link_confirmation_required"
    draft = flow.survey(key, answers, confirmed_public_urls=[URL])
    assert json.loads(draft["payload"])["answers"] == answers
    assert "confirmed_public_urls" not in draft["payload"]
    with pytest.raises(BenchsideError) as pending:
        flow.send(draft["id"], draft["sha256"])
    assert pending.value.code == "survey_public_link_confirmation_required"
    assert not flow.sinks["surveys"].sent
    flow.send(draft["id"], draft["sha256"], confirmed_public_urls=[URL])
    assert flow.sinks["surveys"].sent == [draft["payload"]]
    # Receipt replay does not send again or ask for the same link confirmation.
    flow.send(draft["id"], draft["sha256"])
    assert len(flow.sinks["surveys"].sent) == 1


@pytest.mark.parametrize("url", [
    "https://example.org/?token=secret", "https://example.org/#private-token",
    "https://user:password@example.org/resource", "https://127.0.0.1/resource",
    "https://[::1]/resource", "https://localhost/resource", "https://lab.internal/resource",
    "https://example.org:8443/resource", "https://example.org/Users/will/private",
    "https://example.org/%73%6b-" + "x" * 30,
])
def test_confirmation_cannot_override_unsafe_links(flow, url):
    key = join_text_study(flow)
    with pytest.raises(BenchsideError) as refused:
        flow.survey(key, {"comment": {"text": url}}, confirmed_public_urls=[url])
    assert refused.value.code == "survey_answer_sensitive"
    assert not flow.state.drafts
    assert not flow.sinks["surveys"].sent


@pytest.mark.parametrize("extra", ["synthetic@example.org", "sk-" + "x" * 30, "/Users/will/private"])
def test_public_url_confirmation_keeps_other_text_checks(flow, extra):
    key = join_text_study(flow)
    with pytest.raises(BenchsideError) as refused:
        flow.survey(key, {"comment": {"text": URL + " " + extra}}, confirmed_public_urls=[URL])
    assert refused.value.code == "survey_answer_sensitive"
    assert not flow.sinks["surveys"].sent


@pytest.mark.parametrize("confirmation", [True, URL, ["https://other.org/"], [1], [URL, URL]])
def test_confirmation_requires_exact_unique_urls_in_the_answer(flow, confirmation):
    key = join_text_study(flow)
    with pytest.raises(BenchsideError):
        flow.survey(key, {"comment": {"text": URL}}, confirmed_public_urls=confirmation)
    assert not flow.state.drafts


def test_all_urls_need_confirmation_and_consent_still_applies(flow):
    key = join_text_study(flow)
    second = "https://www.python.org/"
    answers = {"comment": {"text": URL + "\n" + second}}
    with pytest.raises(BenchsideError):
        flow.survey(key, answers, confirmed_public_urls=[URL])
    draft = flow.dispatch({"action": "metascience.survey", "study_key": key,
                           "answers": answers, "confirmed_public_urls": [URL, second]})
    flow.consent("invitations", False)
    with pytest.raises(BenchsideError):
        flow.dispatch({"action": "metascience.send", "draft_id": draft["id"],
                       "approved_sha256": draft["sha256"], "confirmed_public_urls": [URL, second]})
    assert not flow.sinks["surveys"].sent


@pytest.mark.parametrize("answers", [{"comment": {"text": " \n\t"}},
                                     {"comment": {"text": "\ufeff \t"}},
                                     {"checked": "not-an-option"}, {}])
def test_invalid_answers_have_actionable_code_without_creating_a_draft(flow, answers):
    key = join_text_study(flow)
    with pytest.raises(BenchsideError) as error:
        flow.survey(key, answers)
    assert error.value.code == "survey_answer_invalid"
    assert "Nothing was sent" in str(error.value)
    assert not flow.state.drafts


def test_general_redaction_still_blocks_public_urls():
    assert any(f.category == "url" for f in TextRedactor().scan(URL))
