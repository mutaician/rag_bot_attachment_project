"""CLI utilities — create users, preflight checks, setup helpers."""

import argparse
import sys

from app import db
from app.auth.passwords import hash_password
from app.config import settings
from app.ingestion.embed import embed_text_sync


def cmd_create_user(args: argparse.Namespace) -> int:
    existing = db.get_user_by_username(args.username)
    if existing is not None:
        print(f"User {args.username!r} already exists", file=sys.stderr)
        return 1

    user_id = db.create_user(
        username=args.username,
        display_name=args.display_name,
        password_hash=hash_password(args.password),
    )
    print(f"Created user {args.username} ({user_id})")
    return 0


def cmd_preflight(_args: argparse.Namespace) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    except Exception as exc:
        errors.append(f"Database: {exc}")

    try:
        embed_text_sync("preflight")
    except Exception as exc:
        errors.append(f"Ollama embeddings: {exc}")

    if settings.session_secret == "dev-insecure-change-me":
        warnings.append("SESSION_SECRET is still the dev default")

    try:
        user_count = db.count_users()
        if user_count == 0:
            warnings.append("No users — run: uv run python -m app.cli create-user ...")
    except Exception as exc:
        errors.append(f"Users table: {exc}")

    for warning in warnings:
        print(f"WARN: {warning}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print("OK: preflight passed")
    return 0


def cmd_setup(args: argparse.Namespace) -> int:
    if args.username and args.password and args.display_name:
        code = cmd_create_user(
            argparse.Namespace(
                username=args.username,
                display_name=args.display_name,
                password=args.password,
            )
        )
        if code != 0:
            return code
    return cmd_preflight(argparse.Namespace())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    create_user = sub.add_parser("create-user", help="Create a login user")
    create_user.add_argument("--username", required=True)
    create_user.add_argument("--display-name", required=True)
    create_user.add_argument("--password", required=True)
    create_user.set_defaults(func=cmd_create_user)

    preflight = sub.add_parser("preflight", help="Check DB and Ollama connectivity")
    preflight.set_defaults(func=cmd_preflight)

    setup = sub.add_parser("setup", help="Create initial user (optional) and preflight")
    setup.add_argument("--username")
    setup.add_argument("--display-name")
    setup.add_argument("--password")
    setup.set_defaults(func=cmd_setup)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
