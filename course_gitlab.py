#!/usr/bin/python3

import argparse
import gitlab
import requests
import sys
import logging
import pprint


GITLAB_GROUP="test-conc"
GITLAB_TOKEN_ENV="8k7sushNjNLT27sCcUW-"


logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description='Manage student repositories on gitlab.com')
    subparsers = parser.add_subparsers(dest='cmd')
    subparsers.required = True

    create = subparsers.add_parser("create", help="Create and configure repository for student")
    create.add_argument("--username", type=str, help="gitlab.com username of student", required=True)

    return parser.parse_args()


def get_gitlab():
    gl = gitlab.Gitlab("https://gitlab.com", GITLAB_TOKEN_ENV)
    return gl


def create_project(gl, username, name, team):
    users = gl.users.list(username=username)
    if len(users) == 0:
        raise ValueError("No user with username " + username)

    student = users[0]

    course_group = None
    for group in gl.groups.search(GITLAB_GROUP):
        if group.name == GITLAB_GROUP:
            course_group = group

    student_project_name = team + '-' + name
    student_project = None
    logger.info("Looking for project {}".format(student_project_name))
    for project in course_group.projects.list(search=student_project_name):
        if project.name == student_project_name:
            logger.info("Found existing project. id={}".format(project.id))
            student_project = gl.projects.get(project.id)

    if student_project is None:
        logger.info("Existing project not found, creating new.")
        student_project = gl.projects.create({
            "name": student_project_name,
            "namespace_id": course_group.id,
            "builds_enabled": True,
        })

    for member in student_project.members.list():
        if member.id == student.id:
            logger.info("User already project member")
            break
    else:
        logger.info("Adding user to project")
        student_project.members.create({
            "user_id": student.id,
            "access_level": gitlab.DEVELOPER_ACCESS,
        })


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',level=logging.INFO)

    gl = get_gitlab()

    args = parse_args()
    if args.cmd == "create":
        create_project(gl, args.username)