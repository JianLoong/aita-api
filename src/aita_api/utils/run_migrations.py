import os
from pathlib import Path

from sqlalchemy import Engine, text


def run_migrations(engine: Engine) -> None:
    """Run SQL migrations from the migrations directory."""
    # Check for migrations directory in environment variable or default locations
    migrations_path = os.environ.get("MIGRATIONS_PATH", "/migrations")
    migration_file = Path(migrations_path) / "add_fts.sql"

    # Fallback to relative path if not in Docker
    if not migration_file.exists():
        migrations_dir = Path(__file__).parent.parent.parent.parent / "migrations"
        migration_file = migrations_dir / "add_fts.sql"

    if not migration_file.exists():
        print(f"Migration file not found: {migration_file}")
        return

    print(f"Running migration: {migration_file.name}")

    try:
        with open(migration_file, "r") as f:
            sql = f.read()

        # Execute the entire SQL file as a single transaction
        # PostgreSQL functions with $$ delimiters need to be executed together
        with engine.begin() as conn:
            conn.execute(text(sql))

        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {e}")
        # Don't raise - allow app to continue even if migration fails
