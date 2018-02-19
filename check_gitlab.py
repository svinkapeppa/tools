#!/usr/bin/env python3

import argparse
import gitlab
import logging

GITLAB_GROUP = "test-conc"
GITLAB_TOKEN_ENV = "8k7sushNjNLT27sCcUW-"

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description='Manage student repositories on gitlab.com')
    subparsers = parser.add_subparsers(dest='cmd')
    subparsers.required = True

    create = subparsers.add_parser("check_user", help="Check gitlab login")
    create.add_argument("--username", type=str, help="gitlab.com username of student", required=True)

    return parser.parse_args()


def get_gitlab():
    gl = gitlab.Gitlab("https://gitlab.com", GITLAB_TOKEN_ENV)
    return gl


def check_user(gl, username):
    users = gl.users.list(username=username)
    if len(users) == 0:
        raise ValueError("No user with username " + username)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)

    gl = get_gitlab()

    args = parse_args()
    if args.cmd == "check_user":
        check_user(gl, args.username)
