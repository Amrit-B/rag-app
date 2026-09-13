import argparse
import sys
import getpass
from dotenv import load_dotenv

load_dotenv()

from backend.database import init_db, SessionLocal, User
from passlib.hash import pbkdf2_sha256


def list_users(db):
    users = db.query(User).all()
    print(f"\n--- Registered Users ({len(users)}) ---")
    for u in users:
        role = "ADMIN" if u.is_admin else "USER"
        print(f"ID: {u.id:<4} | Role: {role:<6} | Username: {u.username}")
    print("-----------------------------------\n")


def demote_user(username: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username.strip()).first()
        if user:
            user.is_admin = False
            db.commit()
            print(f"[SUCCESS] User '{username}' has been demoted to regular USER!")
        else:
            print(f"Error: User '{username}' not found.")
    except Exception as e:
        db.rollback()
        print(f"Error demoting user: {e}")
    finally:
        db.close()


def make_admin(username: str, password: str | None = None):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username.strip()).first()
        if user:
            user.is_admin = True
            if password:
                if len(password) < 6:
                    print("Error: Password must be at least 6 characters long.")
                    return
                user.password_hash = pbkdf2_sha256.hash(password)
            db.commit()
            print(f"[SUCCESS] User '{username}' has been promoted to ADMIN{' (password updated)' if password else ''}!")
        else:
            if not password:
                print(f"Error: User '{username}' does not exist. A password is required to create a new admin.")
                return
            if len(username.strip()) < 3:
                print("Error: Username must be at least 3 characters long.")
                return
            if len(password) < 6:
                print("Error: Password must be at least 6 characters long.")
                return
            new_user = User(
                username=username.strip(),
                password_hash=pbkdf2_sha256.hash(password),
                is_admin=True,
            )
            db.add(new_user)
            db.commit()
            print(f"[SUCCESS] Admin account '{username}' created successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error creating admin: {e}")
    finally:
        db.close()


def main():
    init_db()
    parser = argparse.ArgumentParser(description="Create or manage admin accounts for the RAG platform.")
    parser.add_argument("--username", "-u", type=str, help="Admin username")
    parser.add_argument("--password", "-p", type=str, help="Admin password")
    parser.add_argument("--promote", type=str, help="Promote an existing username to admin")
    parser.add_argument("--demote", type=str, help="Demote an admin back to regular user")
    parser.add_argument("--list", "-l", action="store_true", help="List all registered users and roles")

    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.list:
            list_users(db)
            return

        if args.promote:
            make_admin(args.promote)
            list_users(db)
            return

        if args.demote:
            demote_user(args.demote)
            list_users(db)
            return

        if args.username and args.password:
            make_admin(args.username, args.password)
            list_users(db)
            return

        if args.username and not args.password:
            password = getpass.getpass(f"Enter password for admin '{args.username}': ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("Error: Passwords do not match.")
                sys.exit(1)
            make_admin(args.username, password)
            list_users(db)
            return

        # Interactive mode
        print("\n=== Agentic RAG Admin Account Manager ===")
        list_users(db)
        username = input("Enter admin username: ").strip()
        if not username:
            print("Operation canceled.")
            return
        password = getpass.getpass(f"Enter password for '{username}': ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Error: Passwords do not match.")
            sys.exit(1)
        make_admin(username, password)
        list_users(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
