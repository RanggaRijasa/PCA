"""Environment-backed configuration shared by local project components."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _path_from_env(name: str, default: str) -> Path:
    configured = Path(os.getenv(name, default)).expanduser()
    if configured.is_absolute():
        return configured
    return (PROJECT_ROOT / configured).resolve()


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    app_host: str = os.getenv("APP_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    llm_model: str = os.getenv("LLM_MODEL", "")
    embed_model: str = os.getenv("EMBED_MODEL", "")
    ollama_timeout_seconds: float = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))
    sqlite_path: Path = _path_from_env("SQLITE_PATH", "./data/app.db")
    chroma_path: Path = _path_from_env("CHROMA_PATH", "./data/chroma")
    raw_docs_path: Path = _path_from_env("RAW_DOCS_PATH", "./data/raw")
    metadata_csv_path: Path = _path_from_env(
        "METADATA_CSV_PATH", "./data/metadata/document_metadata.csv"
    )
    processed_docs_path: Path = _path_from_env("PROCESSED_DOCS_PATH", "./data/processed")
    backups_path: Path = _path_from_env("BACKUP_PATH", "./data/backups")
    chroma_collection: str = os.getenv("CHROMA_COLLECTION", "company_documents")
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))
    chunk_target_tokens: int = int(os.getenv("CHUNK_TARGET_TOKENS", "600"))
    chunk_overlap_tokens: int = int(os.getenv("CHUNK_OVERLAP_TOKENS", "80"))
    chunk_max_tokens: int = int(os.getenv("CHUNK_MAX_TOKENS", "1000"))
    default_top_k: int = int(os.getenv("DEFAULT_TOP_K", "20"))
    rerank_top_k: int = int(os.getenv("RERANK_TOP_K", "5"))
    max_context_chunks: int = int(os.getenv("MAX_CONTEXT_CHUNKS", "6"))
    retrieval_min_score: float = float(os.getenv("RETRIEVAL_MIN_SCORE", "0.30"))
    retrieval_min_lexical_overlap: float = float(
        os.getenv("RETRIEVAL_MIN_LEXICAL_OVERLAP", "0.08")
    )
    retrieval_min_vector_score: float = float(
        os.getenv("RETRIEVAL_MIN_VECTOR_SCORE", "0.60")
    )
    context_score_margin: float = float(os.getenv("CONTEXT_SCORE_MARGIN", "0.12"))
    audit_store_answer_text: bool = os.getenv(
        "AUDIT_STORE_ANSWER_TEXT", "false"
    ).lower() in {"1", "true", "yes"}
    session_cookie_name: str = os.getenv("SESSION_COOKIE_NAME", "pca_session")
    session_ttl_hours: int = int(os.getenv("SESSION_TTL_HOURS", "12"))
    session_cookie_secure: bool = os.getenv(
        "SESSION_COOKIE_SECURE", "false"
    ).lower() in {"1", "true", "yes"}
    seed_user_password: str = os.getenv("SEED_USER_PASSWORD", "")
    eval_reports_path: Path = _path_from_env("EVAL_REPORTS_PATH", "./eval/reports")


settings = Settings()
