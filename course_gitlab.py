#!/usr/bin/python3

import argparse
import gitlab
import requests
import sys
import logging
import pprint
import time


GITLAB_GROUP="test-conc"
GITLAB_TOKEN_ENV="8k7sushNjNLT27sCcUW-"


file = ['./tmp/0README.md', './tmp/1README.md', './tmp/2README.md',
        './tmp/3README.md', './tmp/4README.md', './tmp/5README.md',
        './tmp/6README.md', './tmp/7README.md', './tmp/8README.md']

path = ['README.md', '1-mutex/README.md', '2-cond-var/README.md',
        '3-fine-grained/README.md', '4-cache/README.md', '5-memory-model/README.md',
        '6-lock-free/README.md', '7-linearizability/README.md', '8-consensus/README.md']

message = ['Create README.md', 'Create 1-mutex/README.md',
           'Create 2-cond-var/README.md', 'Create 3-fine-grained/README.md',
           'Create 4-cache/README.md', 'Create 5-memory-model/README.md',
           'Create 6-lock-free/README.md', 'Create 7-linearizability/README.md',
           'Create 8-consensus/README.md']

# Здесь должны быть реальные логины семенаристов и ассистентов
# 698 - чтобы не сбивался порядок
teachers = [['691'], ['692'], ['693'],
            ['complicated'], ['695'], ['696'],
            ['697'], ['698'], ['699']]


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

    for i in range(9):
        content = open(file[i]).read()
        student_project.files.create({'file_path': path[i],
                                      'branch_name': 'master',
                                      'content': content,
                                      'commit_message': message[i]})
        time.sleep(0.5) # иначе файлы не успевают загрузиться

    branch = student_project.branches.get('master')
    branch.protect()

    for i in teachers[int(team)-691]:
        users = gl.users.list(username=i)
        if len(users) == 0:
            raise ValueError("No user with username " + i)

        admin = users[0]

        for member in student_project.members.list():
            if member.id == admin.id:
                logger.info("User already project member")
                break
        else:
            logger.info("Adding user to project")
            student_project.members.create({
                "user_id": admin.id,
                "access_level": gitlab.MASTER_ACCESS,
            })

    
if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',level=logging.INFO)

    gl = get_gitlab()

    args = parse_args()
    if args.cmd == "create":
        create_project(gl, args.username)