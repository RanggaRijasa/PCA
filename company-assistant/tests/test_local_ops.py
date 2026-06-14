"""Backup and reset safety checks using harmless temporary data."""

from pathlib import Path
import sqlite3
from types import SimpleNamespace

import scripts.backup as backup_script
from scripts.reset_local_data import reset_local_data


def test_backup_copies_runtime_data_with_sqlite_snapshot_and_manifest(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project = tmp_path / "project"
    data = project / "data"
    raw = data / "raw"
    processed = data / "processed"
    chroma = data / "chroma"
    eval_path = project / "eval"
    for path in (raw, processed, chroma, eval_path):
        path.mkdir(parents=True)
    (raw / "sample.md").write_text("dummy", encoding="utf-8")
    (processed / "chunk.json").write_text("{}", encoding="utf-8")
    (chroma / "index.bin").write_bytes(b"dummy-index")
    (eval_path / "test_questions.csv").write_text("id\nQ1\n", encoding="utf-8")
    (project / ".env.example").write_text("SAFE=value\n", encoding="utf-8")
    (project / ".env").write_text("SECRET=do-not-copy\n", encoding="utf-8")
    (project / "README.md").write_text("# Dummy\n", encoding="utf-8")
    (project / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    database = data / "app.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE sample (value TEXT)")
        connection.execute("INSERT INTO sample VALUES ('preserved')")

    monkeypatch.setattr(backup_script, "PROJECT_ROOT", project)
    monkeypatch.setattr(
        backup_script,
        "settings",
        SimpleNamespace(
            raw_docs_path=raw,
            processed_docs_path=processed,
            chroma_path=chroma,
            sqlite_path=database,
            backups_path=data / "backups",
        ),
    )
    destination = backup_script.create_backup(tmp_path / "backups")

    assert (destination / "manifest.json").exists()
    assert (destination / "data" / "raw" / "sample.md").exists()
    assert (destination / "project" / ".env.example").exists()
    assert not (destination / "project" / ".env").exists()
    with sqlite3.connect(destination / "data" / "app.db") as connection:
        assert connection.execute("SELECT value FROM sample").fetchone()[0] == "preserved"


def test_reset_preserves_samples_and_backups_by_default(tmp_path: Path) -> None:
    data = tmp_path / "data"
    for name in ("raw", "processed", "archived", "chroma", "backups"):
        (data / name).mkdir(parents=True)
    (data / "app.db").write_bytes(b"db")
    (data / "raw" / "sample_policy.md").write_text("dummy", encoding="utf-8")
    (data / "raw" / "private_policy.md").write_text("private", encoding="utf-8")
    (data / "raw" / "uploads").mkdir()
    (data / "raw" / "uploads" / "staged.md").write_text("staged", encoding="utf-8")
    (data / "processed" / "chunk.json").write_text("{}", encoding="utf-8")
    (data / "chroma" / "index.bin").write_bytes(b"index")
    (data / "backups" / "keep.txt").write_text("backup", encoding="utf-8")

    reset_local_data(data)

    assert not (data / "app.db").exists()
    assert (data / "raw" / "sample_policy.md").exists()
    assert not (data / "raw" / "private_policy.md").exists()
    assert not (data / "raw" / "uploads").exists()
    assert not (data / "processed" / "chunk.json").exists()
    assert not (data / "chroma" / "index.bin").exists()
    assert (data / "backups" / "keep.txt").exists()
