#!/usr/bin/env python3
"""Database migration management script."""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from easymcp.core.migration import (
    check_migration_status,
    create_migration,
    downgrade_migration,
    get_migration_history,
    run_migrations,
)


async def main():
    """Main migration script."""
    parser = argparse.ArgumentParser(description="EasyMCP Database Migration Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    subparsers.add_parser("status", help="Check migration status")

    # Up command
    subparsers.add_parser("up", help="Run migrations to latest version")

    # Down command
    down_parser = subparsers.add_parser("down", help="Downgrade to specific revision")
    down_parser.add_argument("revision", help="Target revision (use 'base' for clean database)")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create new migration")
    create_parser.add_argument("message", help="Migration message")

    # History command
    subparsers.add_parser("history", help="Show migration history")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "status":
            status = check_migration_status()
            print("Migration Status:")
            print(f"  Current: {status['current']}")
            print(f"  Latest:  {status['latest']}")
            print(f"  Status:  {'Needs upgrade' if status['needs_upgrade'] else 'Up to date'}")
            if "error" in status:
                print(f"  Error:   {status['error']}")

        elif args.command == "up":
            print("Running migrations...")
            run_migrations()
            print("Migrations completed successfully!")

        elif args.command == "down":
            print(f"Downgrading to revision: {args.revision}")
            downgrade_migration(args.revision)
            print("Downgrade completed successfully!")

        elif args.command == "create":
            print(f"Creating migration: {args.message}")
            revision = create_migration(args.message)
            print(f"Migration created: {revision}")

        elif args.command == "history":
            history = get_migration_history()
            if not history:
                print("No migrations found.")
            else:
                print("Migration History:")
                for i, migration in enumerate(history, 1):
                    print(f"  {i}. {migration['revision']} - {migration['doc']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
