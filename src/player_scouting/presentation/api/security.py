from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException

from player_scouting.presentation.api.settings import ApiSettings, get_api_settings


def verify_ingestion_api_key(
    settings: Annotated[ApiSettings, Depends(get_api_settings)],
    x_ingestion_key: Annotated[str | None, Header()] = None,
) -> None:
    if not settings.ingestion_api_key:
        return
    if x_ingestion_key != settings.ingestion_api_key:
        raise HTTPException(
            status_code=401, detail="Invalid or missing ingestion API key"
        )
