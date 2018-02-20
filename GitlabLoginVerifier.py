#!/usr/bin/env python3

import argparse
import gitlab
import logging

GITLAB_GROUP = "test-conc"
GITLAB_TOKEN_ENV = "8k7sushNjNLT27sCcUW-"

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description='Manage student\'s repositories on gitlab.com')
    subparsers = parser.add_subparsers(dest='cmd')
    subparsers.required = True

    create = subparsers.add_parser("verify_login", help="Verify given gitlab login")
    create.add_argument("--username", type=str, help="Login of the student", required=True)

    return parser.parse_args()


def get_gitlab():
    gl = gitlab.Gitlab("https://gitlab.com", GITLAB_TOKEN_ENV)
    return gl


def verify_login(gl, username):
    users = gl.users.list(username=username)
    if len(users) == 0:
        raise ValueError("No user with username " + username)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)

    gl = get_gitlab()

    args = parse_args()
    if args.cmd == "verify_login":
        verify_login(gl, args.username)
