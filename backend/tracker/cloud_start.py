"""Migrate, optionally bootstrap an admin, and start exactly one worker."""

import os
import subprocess
import sys

from tracker.config import settings


def main():
    settings.check_production()
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    username = os.environ.get("ADMIN_USERNAME", "admin").strip().lower()
    password = os.environ.get("ADMIN_PASSWORD", "")
    if password:
        from sqlalchemy import select

        from tracker.db import SessionLocal
        from tracker.models import User
        from tracker.security import MIN_PASSWORD_LEN, hash_password

        if not username or len(password) < MIN_PASSWORD_LEN:
            raise RuntimeError("ADMIN_USERNAME is required; ADMIN_PASSWORD needs 10+ characters")
        with SessionLocal() as db:
            if db.scalar(select(User).where(User.username == username)) is None:
                db.add(
                    User(
                        username=username,
                        role="admin",
                        active=True,
                        password_hash=hash_password(password),
                    )
                )
                db.commit()
                print("Administrator created. Its password was not logged.", flush=True)
    os.execv(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "tracker.web:app",
            "--host",
            "0.0.0.0",
            "--port",
            os.environ.get("PORT", "8000"),
            "--workers",
            "1",
            "--proxy-headers",
        ],
    )


if __name__ == "__main__":
    main()
