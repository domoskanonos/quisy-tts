"""Search and term endpoints for voices using FTS5."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from services.voice_service import VoiceService

router: APIRouter = APIRouter(tags=["Voice Search"])


def _get_service() -> VoiceService:
    # reuse the same lazy init pattern as other routes
    return VoiceService()


@router.get("/terms")
def get_terms() -> dict[str, Any]:
    """Return top 50 instruct terms (from FTS or derived table)."""
    service = _get_service()
    try:
        terms = service.get_top_instruct_terms()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve terms")
    return {"terms": terms}


@router.get("/search")
def search_voices(
    q: str | None = Query(None, max_length=200),
    terms: str | None = Query(None),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Search voices by free text `q` and comma-separated `terms` (chips)."""
    service = _get_service()
    term_list = [t.strip() for t in terms.split(",")] if terms else []
    results = service.search(term_list, q, limit=limit, offset=offset)
    return {"total": len(results), "voices": results}
