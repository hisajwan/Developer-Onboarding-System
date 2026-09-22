"""Creates a login account, or resets an existing one's password. Interactive - passwords are

never accepted as a command-line argument, so they never land in shell history. Signing up is
normally done through the app itself; this script is for account recovery and for seeding one
outside the browser.

Run from server/, with the venv active:
    python scripts/create_user.py
"""

import asyncio
import getpass
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from app.domain.models import User  # noqa: E402
from app.infrastructure.auth.passwords import hash_password  # noqa: E402
from app.infrastructure.storage.sqlite_user_registry import SqliteUserRegistry  # noqa: E402


async def main() -> None:
    settings = get_settings()
    registry = SqliteUserRegistry(settings.database_path)

    username = input("Username: ").strip()
    if not username:
        print("Username cannot be blank.")
        return

    existing = await registry.get(username)
    if existing:
        prompt = f"'{username}' already exists - reset their password? [y/N] "
        if input(prompt).strip().lower() != "y":
            print("Cancelled.")
            return
        first_name, last_name, email = existing.first_name, existing.last_name, existing.email
    else:
        first_name = input("First name: ").strip()
        last_name = input("Last name: ").strip()
        email = input("Email: ").strip()
        if not (first_name and last_name and email):
            print("First name, last name and email cannot be blank.")
            return

    password = getpass.getpass("Password: ")
    if not password:
        print("Password cannot be blank.")
        return
    if password != getpass.getpass("Confirm password: "):
        print("Passwords did not match.")
        return

    user = User(
        username=username,
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        email=email,
        created_at=datetime.now(UTC),
    )
    await registry.record(user)
    print(f"{'Updated' if existing else 'Created'} '{username}' in {settings.database_path}")


if __name__ == "__main__":
    asyncio.run(main())
