"""Set one account's sign-in password (stored hashed in the accounts database, app/core/auth.py).

    .venv\\Scripts\\python -m scripts.set_password crown.de      # asks for the new password twice
"""
import getpass
import sys

from sqlalchemy.orm import Session

from app.core import auth


def main(username: str) -> None:
    auth.init()
    with Session(auth.engine) as s, s.begin():
        account = s.get(auth.Account, username.strip().lower())
        if not account:
            sys.exit(f"No account '{username}'. Accounts: {', '.join(sorted(auth.accounts()))}")
        password = getpass.getpass(f"New password for {account.username}: ")
        if not password or password != getpass.getpass("Again: "):
            sys.exit("The passwords are empty or differ: nothing changed.")
        account.password_hash = auth.hash_password(password)
    print(f"Password set for {username}.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
