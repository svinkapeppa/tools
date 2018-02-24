#!/usr/bin/env python3

import argparse
import logging

from oauth2client import tools

import config
import course_gitlab as cgl
import course_sheet

logger = logging.getLogger(__name__)


def configure_argparser():
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.required = True

    create = subparsers.add_parser("create_repos", help="Create repositories from google spreadsheet")
    verify = subparsers.add_parser("verify_login", help="Verify data from google spreadsheet")

    return parser


def validate_team(team):
    is_valid = False
    try:
        is_valid = 691 <= int(team) and int(team) <= 699 and int(team) != 698
    except Exception:
        pass
    if not is_valid:
        logger.warning("team '{}' is not valid".format(team))
    return is_valid


def validate_name(name):
    is_valid = name is not None and name != "" and name[-1] != "-"
    if not is_valid:
        logger.warning("name '{}' is not valid".format(name))
    return is_valid


def create_repos(sheet):
    course_gitlab = cgl.CourseGitlab(config)
    for row in sheet.get_rows():
        logger.info("Processing table row {}".format(row.row_index))
        if not validate_team(row.team) or not validate_name(row.name):
            continue
        project_name = row.team + '-' + row.name
        if row.status == "PROCESSING":
            course_gitlab.delete_project(project_name)
        if row.status != "OK":
            sheet.set_repo_status(row.row_index, "PROCESSING")
            master_login = config.teachers[row.team]
            try:
                course_gitlab.create_project_full(project_name, row.login, master_login)
                sheet.set_repo_status(row.row_index, "OK")
            except cgl.UserException as exception:
                logger.exception(str(exception))


def verify_users(sheet):
    course_gitlab = cgl.CourseGitlab(config)
    for row in sheet.get_rows():
        course_gitlab.get_user(row.login)
        sheet.set_repo_status(row.row_index, "OK")


def main():
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)

    parser = configure_argparser()
    flags = parser.parse_args()

    course = course_sheet.get_sheet_from_env()

    if flags.cmd == "create_repos":
        create_repos(course)
    elif flags.cmd == "verify_login":
        verify_users(course)


if __name__ == '__main__':
    main()
