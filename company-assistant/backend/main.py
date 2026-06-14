"""FastAPI entrypoint for the local permission-filtered RAG service."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api import admin, auth, chat, health
from backend.config import settings
from backend.logging_config import configure_logging

configure_logging()

app = FastAPI(
    title="Private Company Assistant API",
    version="0.13.0",
    description="Authenticated local RAG API with secured admin ingestion and local operations.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {"error": str(exc.detail)}
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": detail.get("error", "Request failed"),
            "code": detail.get("code", "HTTP_ERROR"),
        },
    )


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(admin.router)
