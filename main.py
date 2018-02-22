#!/usr/bin/env python3


import argparse
import logging

from oauth2client import tools

import course_sheet as csh

logger = logging.getLogger(__name__)


def configure_argparser():
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.required = True

    create = subparsers.add_parser("create_repos", help="Create repositories from google spreadsheet")
    verify = subparsers.add_parser("verify_login", help="Verify data from google spreadsheet")

    return parser


def main():
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.ERROR)
    logger.setLevel(logging.INFO)

    parser = configure_argparser()
    flags = parser.parse_args()

    course = csh.get_sheet_from_env()

    if flags.cmd == "create_repos":
        csh.create_repos(course)
    elif flags.cmd == "verify_login":
        csh.verify_users(course)


if __name__ == '__main__':
    main()
