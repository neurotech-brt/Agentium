"""
Genesis API routes.

Handles:
- POST /api/v1/genesis/country-name  — receive country name during genesis
- GET  /api/v1/genesis/status        — check whether genesis has run and an API key exists
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.core.auth import get_current_user
from backend.services.initialization_service import InitializationService
from backend.services.api_key_manager import api_key_manager

router = APIRouter(prefix="/api/v1/genesis", tags=["genesis"])


@router.post("/country-name")
async def submit_country_name(
    name: str,
    db: Session = Depends(get_db),
):
    """
    Receive the sovereign's chosen country name during the genesis naming step.
    Called by the frontend when the user submits a name in response to the
    Head-of-Council broadcast prompt.
    """
    service = InitializationService(db)
    service.set_country_name(name)
    return {"status": "received", "name": name}


@router.get("/status")
async def genesis_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Check whether genesis has completed and whether at least one API key exists.

    Returns one of three states:
    - {"status": "no_api_key",  "initialized": bool}  — no healthy provider key
    - {"status": "pending",     "initialized": False}  — key exists but genesis not run
    - {"status": "ready",       "initialized": True}   — fully operational
    """
    service = InitializationService(db)
    is_initialized = service.is_system_initialized()

    availability = api_key_manager.get_provider_availability(db)
    has_key = any(availability.values())

    if not has_key:
        return {"status": "no_api_key", "initialized": is_initialized}
    if not is_initialized:
        return {"status": "pending", "initialized": False}
    return {"status": "ready", "initialized": True}