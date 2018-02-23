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
    return gitlab.Gitlab("https://gitlab.com", cfg.GITLAB_TOKEN_ENV)


@retry
def define_course_group(gl):
    groups = list(filter(lambda group: group.name == cfg.GITLAB_GROUP,
                         gl.groups.list(search=cfg.GITLAB_GROUP)))
    return groups[0] if len(groups) > 0 else None


@retry
def create_student_project(gl, course_group, student_project_name):
    logger.info("Looking for project {}".format(student_project_name))

    projects = list(filter(lambda project: project.name == student_project_name,
                           course_group.projects.list(search=student_project_name)))
    if len(projects) > 0:
        logger.info("Found existing project")
        return gl.projects.get(projects[0].id)

    logger.info("Existing project not found, creating new.")
    return gl.projects.create({
        "name": student_project_name,
        "namespace_id": course_group.id,
        "builds_enabled": True,
    })


@retry
def add_user(student_project, student, access):
    members = list(filter(lambda member: member.id == student.id, student_project.members.list()))
    if len(members) == 0:
        logger.info("Adding UserId={} to the project".format(student.id))
        student_project.members.create({
            "user_id": student.id,
            "access_level": access,
        })
    else:
        logger.info("UserId={} is already a project member".format(student.id))


def upload_files(student_project):
    content = open(cfg.README).read()
    student_project.files.create({'file_path': 'README.md',
                                  'branch': 'master',
                                  'content': content,
                                  'commit_message': 'Create README.md'})
    for file_info in cfg.file_info:
        content = open(cfg.GITIGNORE).read()
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
