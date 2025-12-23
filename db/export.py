#!/usr/bin/env python3
"""
Export the PostgreSQL database to a SQL dump file.
Usage: python -m db.export [--cloud]
"""
import os
import subprocess
from dotenv import load_dotenv
import argparse

def export_database(is_local=True, output_file="data/database_dump.sql"):
    """
    Export database to SQL dump file using pg_dump.

    Args:
        is_local: If True, export local database. If False, export cloud database.
        output_file: Path to output SQL file.
    """
    load_dotenv()

    host = os.getenv("LOCAL_DB_HOST" if is_local else "DB_HOST")
    port = os.getenv("LOCAL_DB_PORT" if is_local else "DB_PORT")
    user = os.getenv("LOCAL_DB_USER" if is_local else "DB_USER")
    password = os.getenv("LOCAL_DB_PASSWORD" if is_local else "DB_PASSWORD")
    dbname = os.getenv("LOCAL_DB_NAME" if is_local else "DB_NAME")

    # Set PGPASSWORD environment variable for pg_dump
    env = os.environ.copy()
    env["PGPASSWORD"] = password

    # Construct pg_dump command
    cmd = [
        "pg_dump",
        "-h", host,
        "-p", str(port),
        "-U", user,
        "-d", dbname,
        "-f", output_file,
        "--clean",  # Include DROP commands
        "--if-exists",  # Use IF EXISTS
        "--no-owner",  # Don't output ownership commands
        "--no-privileges"  # Don't output privilege commands
    ]

    try:
        print(f"Exporting {'local' if is_local else 'cloud'} database to {output_file}...")
        subprocess.run(cmd, env=env, check=True)
        print(f"✓ Database exported successfully to {output_file}")

        # Get file size
        size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"  File size: {size_mb:.2f} MB")

    except subprocess.CalledProcessError as e:
        print(f"✗ Error exporting database: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    return True

def main():
    parser = argparse.ArgumentParser(description="Export PostgreSQL database to SQL dump")
    parser.add_argument(
        "--cloud",
        action="store_true",
        help="Export cloud database instead of local"
    )
    parser.add_argument(
        "-o", "--output",
        default="data/database_dump.sql",
        help="Output file path (default: data/database_dump.sql)"
    )

    args = parser.parse_args()

    is_local = not args.cloud
    export_database(is_local=is_local, output_file=args.output)

if __name__ == "__main__":
    main()
