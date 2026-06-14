#!/usr/bin/env python3
"""Run the grounded local RAG pipeline from the terminal."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.auth.models import UserRole
from backend.auth.session import simulated_user_for_role
from backend.db.connection import transaction
from backend.db.schema import initialize_database
from backend.db.users import seed_default_roles_and_users
from backend.llm.ollama_client import OllamaError
from backend.rag.service import get_rag_service


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ask the local company RAG service.")
    parser.add_argument("question", nargs="+", help="Company question")
    parser.add_argument(
        "--role",
        choices=["viewer", "staff", "manager", "admin"],
        default="staff",
    )
    parser.add_argument("--department", default="all")
    parser.add_argument(
        "--source", choices=["all", "policies", "handbooks"], default="all"
    )
    parser.add_argument("--allow-document-id", action="append", default=[])
    return parser


def main() -> int:
    args = _parser().parse_args()
    initialize_database()
    with transaction() as connection:
        seed_default_roles_and_users(connection)

    role: UserRole = args.role
    user = simulated_user_for_role(role)
    if args.allow_document_id:
        user = replace(
            user,
            allowed_restricted_document_ids=frozenset(args.allow_document_id),
        )
    question = " ".join(args.question).strip()

    try:
        result = get_rag_service().query(
            question,
            user,
            department_filter=args.department,
            source_filter=args.source,
        )
    except OllamaError as exc:
        print(f"RAG query failed: {exc}", file=sys.stderr)
        return 1

    print(result.answer)
    print(
        f"\nPerformance: total={result.latency_ms}ms, "
        f"retrieval={result.retrieval_ms}ms, generation={result.generation_ms}ms, "
        f"audit={result.audit_id or 'unavailable'}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
