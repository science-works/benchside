"""Private, content-free context for the app that produced a journal event."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints


class AppProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    host: Literal["chatgpt", "claude", "unknown"] = "unknown"
    app_version: (
        Annotated[str, StringConstraints(pattern=r"^[0-9][A-Za-z0-9.-]{0,39}$")]
        | Literal["unknown"]
    ) = "unknown"
    surface: Literal["web", "desktop", "cli", "unknown"] = "unknown"
