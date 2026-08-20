"""Event registration.

`Event.__init_subclass__` populates the registry, so every event module must be
imported before a journal can be parsed. Importing them here keeps that
requirement in one place instead of scattered through the adapters.
"""

import importlib

_EVENT_MODULES = (
    "benchside.domain.consultation.event",
    "benchside.domain.export.event",
)

_registered = False


def ensure_events_registered() -> None:
    global _registered
    if _registered:
        return
    for module in _EVENT_MODULES:
        importlib.import_module(module)
    _registered = True
