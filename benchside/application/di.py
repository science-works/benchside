"""The composition root.

The only place that knows every provider. Domain providers bind services and
handlers; infrastructure providers bind ports to implementations. Later
providers override earlier ones for the same type, which is how tests
substitute fakes:

    container = create_container(FakeJournalProvider())
"""

from dishka import Container, make_container
from dishka import Provider as DishkaProvider

from benchside.domain.authoring.util.di import AuthoringProvider
from benchside.domain.consultation.util.di import ConsultationProvider
from benchside.domain.export.util.di import ExportProvider
from benchside.infrastructure.journal.di import FileProvider
from benchside.util.di import Scope


def create_container(*extra_providers: DishkaProvider) -> Container:
    """Build the container.

    Args:
        extra_providers: Appended after the defaults. Use `override=True` on a
            provision to replace a default binding.
    """
    return make_container(
        FileProvider(),
        ConsultationProvider(),
        AuthoringProvider(),
        ExportProvider(),
        *extra_providers,
        scopes=Scope,  # type: ignore[arg-type]
    )
