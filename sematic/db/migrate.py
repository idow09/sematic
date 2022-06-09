import os

import sqlite3

from sematic.config import get_config, SQLITE_FILE


def migrate():
    sqlite_file_path = os.path.join(get_config().config_dir, SQLITE_FILE)

    conn = sqlite3.connect(sqlite_file_path)

    with conn:
        conn.execute(
            (
                "CREATE TABLE IF NOT EXISTS "
                '"schema_migrations" (version varchar(255) primary key);'
            )
        )

    schema_migrations = conn.execute("SELECT version FROM schema_migrations;")

    versions = [row[0] for row in schema_migrations]

    migration_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "migrations"
    )

    migration_files = os.listdir(migration_dir)

    for migration_file in migration_files:
        version = migration_file.split("_")[0]
        if version in versions:
            continue

        with open(os.path.join(migration_dir, migration_file), "r") as file:
            sql = file.read()

        up_sql = sql.split("-- migrate:down")[0].split("-- migrate:up")[1].strip()

        statements = up_sql.split(";")

        with conn:
            for statement in statements:
                if len(statement) == 0:
                    continue

                conn.execute("{};".format(statement))

            conn.execute(
                "INSERT INTO schema_migrations(version) values (?)", (version,)
            )


if __name__ == "__main__":
    migrate()