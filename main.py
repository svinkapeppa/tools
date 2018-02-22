#!/usr/bin/env python3


import argparse
import logging

from oauth2client import tools

import course_gitlab as cgl
import course_sheet as csh

logger = logging.getLogger(__name__)


def configure_argparser():
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.required = True

    create = subparsers.add_parser("create_repos", help="Create repositories from google spreadsheet")
    verify = subparsers.add_parser("verify_login", help="Verify data from google spreadsheet")

    return parser


def create_repos(sheet):
    gitlab = cgl.get_gitlab()
    for row in sheet.get_requests():
        if row.status == "PROCESSING":
            try:
                cgl.delete_project(gitlab, row.name, row.team)
            except Exception:
                logger.exception("Can't delete project")
        if row.status != "OK":
            try:
                cgl.create_project(gitlab, row.login, row.name, row.team)
                sheet.set_repo_status(row.row_index, "OK")
            except Exception:
                logger.exception("Can't create project")
                sheet.set_repo_status(row.row_index, "PROCESSING")


def verify_users(sheet):
    gitlab = cgl.get_gitlab()
    for row in sheet.get_requests():
        try:
            cgl.verify_login(gitlab, row.login)
            sheet.set_repo_status(row.row_index, "OK")
        except Exception:
            logger.exception("Invalid login")


def main():
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.ERROR)
    logger.setLevel(logging.INFO)

    parser = configure_argparser()
    flags = parser.parse_args()

    course = csh.get_sheet_from_env()

    if flags.cmd == "create_repos":
        create_repos(course)
    elif flags.cmd == "verify_login":
        verify_users(course)


if __name__ == '__main__':
    main()
