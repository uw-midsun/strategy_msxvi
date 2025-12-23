#!/usr/bin/env python3
"""
Import a PostgreSQL database dump file.
Usage: python -m db.import_dump [dump_file]
"""
import os
import subprocess
from dotenv import load_dotenv
import argparse
from db.connect import create_db

def import_database(dump_file="data/database_dump.sql", is_local=True):
    """
    Import database from SQL dump file using psql.

    Args:
        dump_file: Path to SQL dump file.
        is_local: If True, import to local database. If False, import to cloud database.
    """
    load_dotenv()

    if not os.path.exists(dump_file):
        print(f"✗ Error: Dump file not found: {dump_file}")
        return False

    host = os.getenv("LOCAL_DB_HOST" if is_local else "DB_HOST")
    port = os.getenv("LOCAL_DB_PORT" if is_local else "DB_PORT")
    user = os.getenv("LOCAL_DB_USER" if is_local else "DB_USER")
    password = os.getenv("LOCAL_DB_PASSWORD" if is_local else "DB_PASSWORD")
    dbname = os.getenv("LOCAL_DB_NAME" if is_local else "DB_NAME")

    # Set PGPASSWORD environment variable for psql
    env = os.environ.copy()
    env["PGPASSWORD"] = password

    # Try to create database if it doesn't exist
    print(f"Creating database '{dbname}' if it doesn't exist...")
    try:
        create_db(is_local=is_local)
    except Exception as e:
        print(f"  Note: {e} (database may already exist)")

    # Construct psql command
    cmd = [
        "psql",
        "-h", host,
        "-p", str(port),
        "-U", user,
        "-d", dbname,
        "-f", dump_file,
        "-q"  # Quiet mode
    ]

    try:
        print(f"Importing dump file to {'local' if is_local else 'cloud'} database...")
        subprocess.run(cmd, env=env, check=True)
        print(f"✓ Database imported successfully from {dump_file}")

    except subprocess.CalledProcessError as e:
        print(f"✗ Error importing database: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    return True

def main():
    parser = argparse.ArgumentParser(description="Import PostgreSQL database from SQL dump")
    parser.add_argument(
        "dump_file",
        nargs="?",
        default="data/database_dump.sql",
        help="Path to SQL dump file (default: data/database_dump.sql)"
    )
    parser.add_argument(
        "--cloud",
        action="store_true",
        help="Import to cloud database instead of local"
    )

    args = parser.parse_args()

    is_local = not args.cloud
    import_database(dump_file=args.dump_file, is_local=is_local)

if __name__ == "__main__":
    main()
