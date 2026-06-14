"""Health endpoint."""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok", "version": "0.13.0", "mode": "local-rag"}
