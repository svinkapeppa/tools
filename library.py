#!/usr/bin/env python3

import argparse
import logging
import time

import gitlab

GITLAB_GROUP = "test-conc"
GITLAB_TOKEN_ENV = "8k7sushNjNLT27sCcUW-"

path = ['README.md', '1-mutex/.gitignore', '2-cond-var/.gitignore',
        '3-fine-grained/.gitignore', '4-cache/.gitignore', '5-memory-model/.gitignore',
        '6-lock-free/.gitignore', '7-linearizability/.gitignore', '8-consensus/.gitignore']

message = ['Create README.md', 'Create 1-mutex/.gitignore',
           'Create 2-cond-var/.gitignore', 'Create 3-fine-grained/.gitignore',
           'Create 4-cache/.gitignore', 'Create 5-memory-model/.gitignore',
           'Create 6-lock-free/.gitignore', 'Create 7-linearizability/.gitignore',
           'Create 8-consensus/.gitignore']

# Здесь должны быть реальные логины семенаристов и ассистентов
# 698 - чтобы не сбивался порядок
teachers = [['691'], ['692'], ['693'],
            ['694'], ['Lipovsky'], ['696'],
            ['697'], ['698'], ['699']]

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description='Manage student repositories on gitlab.com')
    subparsers = parser.add_subparsers(dest='cmd')
    subparsers.required = True

    create = subparsers.add_parser("create", help="Create and configure repository for student")
    create.add_argument("--username", type=str, help="gitlab.com username of student", required=True)

    verify = subparsers.add_parser("verify_login", help="Verify given gitlab login")
    verify.add_argument("--username", type=str, help="Login of the student", required=True)

    return parser.parse_args()


def verify_login(gl, username):
    users = gl.users.list(username=username)
    if len(users) == 0:
        raise ValueError("No user with username " + username)


def verify_name(name):
    if len(name) == 0:
        raise ValueError("Name not given")


def verify_team(team):
    if (int(team) < 691) and (int(team) > 699) and (int(team) != 698):
        raise ValueError("Bad team " + team)


def get_gitlab():
    gl = gitlab.Gitlab("https://gitlab.com", GITLAB_TOKEN_ENV)
    return gl


def define_course_group(gl):
    course_group = None
    for group in gl.groups.search(GITLAB_GROUP):
        if group.name == GITLAB_GROUP:
            course_group = group

    return course_group


def create_student_project(gl, course_group, team, name):
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

    return student_project


def add_user(student_project, student, access):
    for member in student_project.members.list():
        if member.id == student.id:
            logger.info("User already project member")
            break
    else:
        logger.info("Adding user to project")
        student_project.members.create({
            "user_id": student.id,
            "access_level": access,
        })


def upload_files(student_project):
    content = open('./tmp/README.md').read()
    student_project.files.create({'file_path': path[0],
                                  'branch_name': 'master',
                                  'content': content,
                                  'commit_message': message[0]})
    time.sleep(0.5)
    for i in range(1, 9):
        content = open('./tmp/.gitignore').read()
        student_project.files.create({'file_path': path[i],
                                      'branch_name': 'master',
                                      'content': content,
                                      'commit_message': message[i]})
        time.sleep(0.5)


def create_project(gl, username, name, team):
    verify_login(gl, username)
    verify_team(team)
    verify_name(name)

    users = gl.users.list(username=username)
    student = users[0]

    course_group = define_course_group(gl)

    student_project = create_student_project(gl, course_group,
                                             team, name)

    add_user(student_project, student, gitlab.DEVELOPER_ACCESS)

    upload_files(student_project)

    branch = student_project.branches.get('master')
    branch.protect()

    for teacher in teachers[int(team) - 691]:
        verify_login(gl, teacher)

        users = gl.users.list(username=teacher)
        admin = users[0]

        add_user(student_project, admin, gitlab.MASTER_ACCESS)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)

    gl = get_gitlab()

    args = parse_args()
    if args.cmd == "create":
        create_project(gl, args.username)
    elif args.cmd == "verify":
        verify_login(gl, args.username)
