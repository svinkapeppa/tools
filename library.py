#!/usr/bin/env python3

import argparse
import logging
import time

import gitlab

import config as cfg

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


def verify_team(team):
    if (int(team) < 691) or (int(team) > 699) or (int(team) == 698):
        raise ValueError("Bad team " + team)


def get_gitlab():
    gl = gitlab.Gitlab("https://gitlab.com", cfg.GITLAB_TOKEN_ENV)
    return gl


def define_course_group(gl):
    course_group = None
    for group in gl.groups.list():
        if group.name == cfg.GITLAB_GROUP:
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
    student_project.files.create({'file_path': 'README.md',
                                  'branch': 'master',
                                  'content': content,
                                  'commit_message': 'Create README.md'})
    time.sleep(0.5)
    for file_info in cfg.file_info:
        content = open('./tmp/.gitignore').read()
        student_project.files.create({'file_path': file_info[0],
                                      'branch': 'master',
                                      'content': content,
                                      'commit_message': file_info[1]})
        time.sleep(0.5)


def create_project(gl, username, name, team):
    verify_login(gl, username)
    verify_team(team)

    users = gl.users.list(username=username)
    student = users[0]

    course_group = define_course_group(gl)

    student_project = create_student_project(gl, course_group,
                                             team, name)

    add_user(student_project, student, gitlab.DEVELOPER_ACCESS)

    upload_files(student_project)

    branch = student_project.branches.get('master')
    branch.protect()

    teacher = cfg.teachers[team]
    verify_login(gl, teacher)
    admin = gl.users.list(username=teacher)[0]
    add_user(student_project, admin, gitlab.MASTER_ACCESS)


def delete_project(gl, name, team):
    course_group = define_course_group(gl)

    student_project = create_student_project(gl, course_group,
                                             team, name)

    student_project.delete()


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)

    git = get_gitlab()

    args = parse_args()
    if args.cmd == "create":
        create_project(git, args.username)
    elif args.cmd == "verify":
        verify_login(git, args.username)
