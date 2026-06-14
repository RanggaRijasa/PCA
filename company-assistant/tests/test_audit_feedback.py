from pathlib import Path

from backend.db.audit import create_audit_log, list_audit_logs
from backend.db.chat import append_chat_message, create_chat_session
from backend.db.connection import transaction
from backend.db.feedback import create_feedback
from backend.db.schema import initialize_database
from backend.db.users import seed_default_roles_and_users


def test_audit_redacts_secrets_and_feedback_updates_event(tmp_path: Path) -> None:
    database = tmp_path / "app.db"
    initialize_database(database)
    with transaction(database) as connection:
        seed_default_roles_and_users(connection)
        session = create_chat_session(connection, "user_staff", "Audit test")
        audit_id = create_audit_log(
            connection,
            event_type="rag_chat",
            user_id="user_staff",
            session_id=session["id"],
            question="Check password=super-secret and Bearer abcdefghijklmnop",
            answer_hash="abc123",
            refusal_flag=True,
            status="refused",
        )
        append_chat_message(
            connection,
            "msg_answer",
            session["id"],
            "assistant",
            "Refused",
            status="refused",
            audit_id=audit_id,
        )
        feedback_id = create_feedback(
            connection,
            rating="down",
            message_id="msg_answer",
            user_id="user_staff",
            comment="token=do-not-store-this",
            audit_id=audit_id,
        )
        logs = list_audit_logs(connection)
        feedback = connection.execute(
            "SELECT comment FROM feedback WHERE id = ?", (feedback_id,)
        ).fetchone()

    assert "super-secret" not in logs[0]["question"]
    assert "abcdefghijklmnop" not in logs[0]["question"]
    assert logs[0]["feedbackRating"] == "down"
    assert feedback["comment"] == "token=[REDACTED]"


def test_feedback_cannot_target_another_users_message(tmp_path: Path) -> None:
    database = tmp_path / "app.db"
    initialize_database(database)
    with transaction(database) as connection:
        seed_default_roles_and_users(connection)
        session = create_chat_session(connection, "user_staff", "Ownership")
        append_chat_message(
            connection, "msg_answer", session["id"], "assistant", "Answer"
        )
        try:
            create_feedback(
                connection,
                rating="up",
                message_id="msg_answer",
                user_id="user_viewer",
            )
        except KeyError:
            pass
        else:
            raise AssertionError("Feedback ownership must be enforced")
