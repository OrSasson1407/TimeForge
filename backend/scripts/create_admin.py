"""Bootstrap the very first ADMIN account for a TimeForge deployment.

Every self-registered account starts life as PENDING and needs an existing
Administrator to approve it (docs/02-PRD.md #28a) — which is a chicken-and-
egg problem the very first time a school comes online, since no admin
exists yet to do the approving. This script is the one sanctioned way
around that: it creates one real School and one real ADMIN account
directly, via the Firebase Admin SDK, bypassing the normal
register -> verify -> approve flow entirely.

Every value is supplied explicitly on the command line, or typed
interactively for the password — there is no demo/sample data and no
default credentials baked in here, unlike the old scripts/seed.py this
replaces. It runs equally well against a local Firebase emulator (for
development) or a real Firebase project (for an actual production
bootstrap); it is the caller's job to make sure `.env`/the environment
points at the right one before running it.

Usage (from backend/):
    uv run python -m scripts.create_admin \
        --school-name "Example High School" \
        --school-timezone "America/New_York" \
        --admin-email you@example.com \
        --admin-display-name "Your Name"

The password is never a command-line argument (shell history, process
lists) — it's prompted for interactively and checked against the same
strength policy self-registration uses.
"""

import argparse
import getpass
import sys
import uuid

from firebase_admin import auth as firebase_auth

from app.core.errors import ValidationError
from app.core.security import validate_password_strength
from app.domain.models import School, User, UserRole
from app.infrastructure.firebase.client import get_auth_client, get_firestore_client
from app.infrastructure.repositories import FirestoreSchoolRepository, FirestoreUserRepository


def _prompt_password() -> str:
    while True:
        password = getpass.getpass("Admin password: ")
        try:
            validate_password_strength(password)
        except ValidationError as exc:
            print(f"  {exc.message}", file=sys.stderr)
            continue
        if getpass.getpass("Confirm password: ") != password:
            print("  Passwords did not match — try again.", file=sys.stderr)
            continue
        return password


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--school-name", required=True)
    parser.add_argument(
        "--school-timezone", required=True, help="An IANA timezone, e.g. America/New_York"
    )
    parser.add_argument("--admin-email", required=True)
    parser.add_argument("--admin-display-name", required=True)
    args = parser.parse_args()

    try:
        school = School(
            id=f"school_{uuid.uuid4().hex[:12]}",
            name=args.school_name,
            timezone=args.school_timezone,
        )
    except ValueError as exc:
        print(f"Invalid school details: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    password = _prompt_password()

    firestore_client = get_firestore_client()
    FirestoreSchoolRepository(firestore_client).save(school)

    auth_client = get_auth_client()
    try:
        record = auth_client.get_user_by_email(args.admin_email)
        print(f"Reusing existing Firebase Auth account for {args.admin_email!r}.")
    except firebase_auth.UserNotFoundError:
        record = auth_client.create_user(
            email=args.admin_email, password=password, display_name=args.admin_display_name
        )

    FirestoreUserRepository(firestore_client).save(
        User(
            id=record.uid,
            role=UserRole.ADMIN,
            school_id=school.id,
            display_name=args.admin_display_name,
            email_verified=True,
        )
    )

    print(
        f"Created school {school.id!r} ({args.school_name!r}) and admin account "
        f"{args.admin_email!r} (uid {record.uid}).\n"
        "Sign in with this email/password, then use Management to add your "
        "real teachers, classes, rooms, subjects, and lesson requirements — "
        "nothing else is pre-populated."
    )


if __name__ == "__main__":
    main()
