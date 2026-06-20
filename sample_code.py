"""A deliberately flawed sample file so you can see PIPE! find real issues.
Run `python main.py` (with no args) to have the agent review this file."""

import hashlib


def average(numbers):
    # Bug: ZeroDivisionError when the list is empty
    return sum(numbers) / len(numbers)


def hash_password(password):
    # Security: MD5 is not suitable for password hashing
    return hashlib.md5(password.encode()).hexdigest()


def find_user(users, name):
    # Readability/perf: builds a full list just to check membership
    matches = [u for u in users if u["name"] == name]
    if len(matches) > 0:
        return matches[0]
    return None


def run_query(db, user_input):
    # Security: SQL injection via string formatting
    query = "SELECT * FROM users WHERE name = '%s'" % user_input
    return db.execute(query)
