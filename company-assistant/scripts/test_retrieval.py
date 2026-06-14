#!/usr/bin/env python3
"""Inspect permission-filtered retrieval without generating an LLM answer."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
import sys
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.auth.models import UserRole
from backend.auth.session import simulated_user_for_role
from backend.config import settings
from backend.db.schema import initialize_database
from backend.db.connection import transaction
from backend.db.users import seed_default_roles_and_users
from backend.llm.ollama_client import OllamaError
from backend.rag.service import get_rag_service


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run vector retrieval with role filters and no answer generation."
    )
    parser.add_argument("question", nargs="+", help="Question to retrieve for")
    parser.add_argument(
        "--role",
        choices=["viewer", "staff", "manager", "admin"],
        default="staff",
    )
    parser.add_argument("--department", default="all")
    parser.add_argument(
        "--source", choices=["all", "policies", "handbooks"], default="all"
    )
    parser.add_argument("--top-k", type=int, default=settings.default_top_k)
    parser.add_argument(
        "--allow-document-id",
        action="append",
        default=[],
        help="Explicitly grant one restricted document ID for this test.",
    )
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

    service = get_rag_service()
    try:
        retrieval = service.retriever.search(
            question,
            user,
            top_k=args.top_k,
            department_filter=args.department,
            source_filter=args.source,
        )
    except OllamaError as exc:
        print(f"Retrieval failed: {exc}", file=sys.stderr)
        return 1
    reranked = service.reranker.rerank(
        question, retrieval.chunks, top_k=settings.rerank_top_k
    )

    print(f"Query: {question}")
    print(f"User: {user.id} ({user.role}, {user.department})")
    print(f"Permission filter: {retrieval.permission_filter.to_audit_dict()}")
    print(f"Retrieved candidates: {len(retrieval.chunks)}")
    print(f"Top reranked chunks: {len(reranked)}")
    for rank, chunk in enumerate(reranked, start=1):
        location: List[str] = []
        if chunk.page is not None:
            location.append(f"page={chunk.page}")
        if chunk.section:
            location.append(f"section={chunk.section}")
        print("\n" + "-" * 72)
        print(f"Rank: {rank}")
        print(f"Document: {chunk.title}")
        print(f"Source file: {chunk.source_file}")
        print("Location: " + (", ".join(location) if location else "not available"))
        print(f"Access level: {chunk.access_level}")
        print(f"Department: {chunk.department}")
        print(f"Relevance score: {chunk.relevance_score:.4f}")
        print(f"Vector score: {chunk.vector_score:.4f}")
        print(f"Lexical overlap: {chunk.lexical_overlap:.4f}")
        print(f"Chunk ID: {chunk.id}")
        print(f"Text: {chunk.content[:500]}")
    if not reranked:
        print("\nNo authorized chunks matched this query.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
