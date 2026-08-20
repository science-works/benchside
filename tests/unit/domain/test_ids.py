"""Regression tests for id hygiene (bugs B5, B6)."""

import pytest

from benchside.domain.shared.model.ids import ProjectId


class TestB5ReservedProject:
    def test_consent_ledger_id_has_one_definition(self):
        from benchside.domain.export.service import consent
        from benchside.domain.shared.model import ids
        from benchside.infrastructure.journal import projection

        assert consent.CONSENT_LEDGER_PROJECT is ids.CONSENT_LEDGER_PROJECT
        assert projection.CONSENT_LEDGER_PROJECT is ids.CONSENT_LEDGER_PROJECT

    def test_user_cannot_name_a_project_after_the_ledger(self):
        from benchside.domain.shared.model.ids import CONSENT_LEDGER_PROJECT, user_project_id

        with pytest.raises(ValueError):
            user_project_id(CONSENT_LEDGER_PROJECT.root)
        assert user_project_id("chd7-neural-crest") == ProjectId("chd7-neural-crest")


class TestB6EventIds:
    def test_new_event_id_is_unique_per_call(self):
        from benchside.domain.shared.event import new_event_id

        ids = {new_event_id() for _ in range(200)}
        assert len(ids) == 200
