#!/usr/bin/env python3

import argparse
import datetime
import logging
import re

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
    create_hooks = subparsers.add_parser("create_hooks", help="Create webhooks for Jenkins")
    delete_hooks = subparsers.add_parser("delete_hooks", help="Delete webhooks for Jenkins")
    show_merge_requests = subparsers.add_parser("show_merge_requests", help="Show all merge requests for a certain group")
    show_merge_requests.add_argument("--group", type=int)
    mr = subparsers.add_parser("update_mr", help="Retry pipeline for every open merge request")
    mr.add_argument("task", help="Name of the task")

    return parser


def validate_team(team):
    is_valid = False
    try:
        is_valid = 691 <= int(team) <= 699 and int(team) != 698
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


def create_hooks(sheet):
    course_gitlab = cgl.CourseGitlab(config)
    for row in sheet.get_rows():
        logger.info("Processing table row {}".format(row.row_index))
        if not validate_team(row.team) or not validate_name(row.name):
            continue
        project_name = row.team + '-' + row.name
        if row.status == "PROCESSING":
            course_gitlab.delete_hook(project_name)
        if row.status != "OK":
            sheet.set_repo_status(row.row_index, "PROCESSING")
            try:
                course_gitlab.create_hook(project_name)
                sheet.set_repo_status(row.row_index, "OK")
            except cgl.UserException as exception:
                logger.exception(str(exception))


def delete_hooks(sheet):
    course_gitlab = cgl.CourseGitlab(config)
    for row in sheet.get_rows():
        logger.info("Processing table row {}".format(row.row_index))
        if not validate_team(row.team) or not validate_name(row.name):
            continue
        project_tame = row.team + '-' + row.name
        if row.status == "PROCESSING":
            course_gitlab.delete_hook(project_name)
        if row.status != "OK":
            sheet.set_repo_status(row.row_index, "PROCESSING")
            try:
                course_gitlab.delete_hook(project_name)
                sheet.set_repo_status(row.row_index, "OK")
            except cgl.UserException as exception:
                logger.exception(str(exception))


def show_merge_requests(group):
    course_gitlab = cgl.CourseGitlab(config)
    for project in course_gitlab.group.projects.list(search=group, with_merge_requests_enabled=True):
        project_obj = course_gitlab.get_or_create_project(project.name)
        # print("project: '{}'".format(project_obj
        for merge_request in project_obj.mergerequests.list(state='all', per_page=10000):
            if merge_request.state == "closed":
                continue
            task_deadline = None
            for regexp, deadline in config.deadlines:
                if re.match(regexp, merge_request.source_branch):
                    task_deadline = deadline
                    break
            if task_deadline is None:
                print("wrong merge request name '{}'".format(merge_request.source_branch))
                continue
            date_obj = datetime.datetime.strptime(merge_request.created_at, "%Y-%m-%dT%H:%M:%S.%fZ") \
                + datetime.timedelta(hours=3)
            date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            print("task: '{}', created_at: '{}', state: '{}', before_deadline: '{}'".format(merge_request.source_branch,
                  date, merge_request.state, date <= task_deadline))


def update_mr(sheet, task):
    course_gitlab = cgl.CourseGitlab(config)
    for row in sheet.get_rows():
        logger.info("Processing table row {}".format(row.row_index))
        if not validate_team(row.team) or not validate_name(row.name):
            continue
        project_name = row.team + '-' + row.name
        if row.status != "OK":
            sheet.set_repo_status(row.row_index, "PROCESSING")
            try:
                course_gitlab.update_mr(project_name, task)
                sheet.set_repo_status(row.row_index, "OK")
            except cgl.UserException as exception:
                logger.exception(str(exception))


def main():
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)

    parser = configure_argparser()
    flags = parser.parse_args()

    course = course_sheet.get_sheet_from_env()

    if flags.cmd == "create_repos":
        create_repos(course)
    elif flags.cmd == "verify_login":
        verify_users(course)
    elif flags.cmd == "delete_hooks":
        delete_hooks(course)
    elif flags.cmd == "create_hooks":
        create_hooks(course)
    elif flags.cmd == "update_mr":
        update_mr(course, flags.task)
    elif flags.cmd == "show_merge_requests":
        show_merge_requests(flags.group)


if __name__ == '__main__':
    main()
