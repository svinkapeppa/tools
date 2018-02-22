#!/usr/bin/env python3

import logging

import gitlab
from retrying import retry

import config as cfg

logger = logging.getLogger(__name__)


def verify_login(gl, username):
    users = gl.users.list(username=username)
    if len(users) == 0:
        raise ValueError("No user with username " + username)


def verify_team(team):
    if (int(team) < 691) or (int(team) > 699) or (int(team) == 698):
        raise ValueError("Bad team " + team)


@retry
def get_gitlab():
    gl = gitlab.Gitlab("https://gitlab.com", cfg.GITLAB_TOKEN_ENV)
    return gl


@retry
def define_course_group(gl):
    course_group = None
    for group in gl.groups.list():
        if group.name == cfg.GITLAB_GROUP:
            course_group = group

    return course_group


@retry
def create_student_project(gl, course_group, student_project_name):
    logger.info("Looking for project {}".format(student_project_name))

    student_project = None
    projects = list(filter(lambda project: project.name == student_project_name,
                           course_group.projects.list(search=student_project_name)))
    if len(projects) > 0:
        logger.info("Found existing project")
        student_project = gl.projects.get(projects[0].id)

    if student_project is None:
        logger.info("Existing project not found, creating new.")
        student_project = gl.projects.create({
            "name": student_project_name,
            "namespace_id": course_group.id,
            "builds_enabled": True,
        })

    return student_project


@retry
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
    for file_info in cfg.file_info:
        content = open('./tmp/.gitignore').read()
        student_project.files.create({'file_path': file_info[0],
                                      'branch': 'master',
                                      'content': content,
                                      'commit_message': file_info[1]})


def create_project(gl, username, name, team):
    verify_login(gl, username)
    verify_team(team)

    users = gl.users.list(username=username)
    student = users[0]

    course_group = define_course_group(gl)

    student_project_name = team + '-' + name
    student_project = create_student_project(gl, course_group,
                                             student_project_name)

    add_user(student_project, student, gitlab.DEVELOPER_ACCESS)

    upload_files(student_project)

    branch = student_project.branches.get('master')
    branch.protect()

    teacher = cfg.teachers[team]
    verify_login(gl, teacher)
    admin = gl.users.list(username=teacher)[0]
    add_user(student_project, admin, gitlab.MASTER_ACCESS)


def delete_project(gl, student_project_name):
    course_group = define_course_group(gl)

    student_project = create_student_project(gl, course_group,
                                             student_project_name)

    student_project.delete()
