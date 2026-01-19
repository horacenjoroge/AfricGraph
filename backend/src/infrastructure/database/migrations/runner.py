"""
Migration execution engine for Neo4j schema.

Runs .cypher files in migrations/ in order. Tracks applied migrations in PostgreSQL
(schema_migrations). Idempotent when Cypher uses IF NOT EXISTS.
"""

from pathlib import Path

from sqlalchemy import text

from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent
MIGRATIONS_TABLE = "schema_migrations"


def _ensure_migrations_table() -> None:
    with postgres_client.get_session() as session:
        session.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(name VARCHAR(255) PRIMARY KEY, applied_at TIMESTAMPTZ DEFAULT now())"
            )
        )


def _applied_names() -> set:
    _ensure_migrations_table()
    with postgres_client.get_session() as session:
        result = session.execute(text("SELECT name FROM schema_migrations"))
        return {row[0] for row in result}


def _record_migration(name: str) -> None:
    with postgres_client.get_session() as session:
        session.execute(
            text("INSERT INTO schema_migrations (name) VALUES (:name) ON CONFLICT (name) DO NOTHING"),
            {"name": name},
        )


def _statements_from_file(path: Path) -> list:
    content = path.read_text()
    statements = []
    for raw in content.split(";"):
        s = raw.strip()
        if not s:
            continue
        lines = [ln for ln in s.splitlines() if ln.strip() and not ln.strip().startswith("//")]
        if lines:
            statements.append(s)
    return statements


def run_migrations() -> list:
    """
    Run all pending .cypher migrations in order. Returns list of applied migration names.
    Assumes neo4j_client and postgres_client are connected.
    """
    applied = _applied_names()
    migrated = []

    cypher_files = sorted(MIGRATIONS_DIR.glob("*.cypher"))
    for path in cypher_files:
        name = path.stem  # e.g. 001_create_constraints
        if name in applied:
            continue
        logger.info("Applying migration", migration=name)
        statements = _statements_from_file(path)
        for stmt in statements:
            neo4j_client.execute_cypher(stmt)
        _record_migration(name)
        migrated.append(name)

    return migrated


def _main() -> None:
    neo4j_client.connect()
    postgres_client.connect()
    try:
        applied = run_migrations()
        if applied:
            logger.info("Migrations applied", migrations=applied)
        else:
            logger.info("No pending migrations")
    finally:
        neo4j_client.close()
        postgres_client.close()


if __name__ == "__main__":
    _main()
