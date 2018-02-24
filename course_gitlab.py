#!/usr/bin/env python3

import logging

import gitlab
from retrying import retry

logger = logging.getLogger(__name__)


class CourseGitlabException(Exception):
    pass


class GroupException(CourseGitlabException):
    pass


class UserException(CourseGitlabException):
    pass


class CourseGitlab(object):
    GITLAB_URL = "https://gitlab.com"

    def __init__(self, config):
        self.config = config
        self.gitlab = gitlab.Gitlab(CourseGitlab.GITLAB_URL, config.GITLAB_TOKEN_ENV)
        self.group = CourseGitlab._get_group(self.gitlab, config.GITLAB_GROUP)

    def _get_group(gitlab, group_name):
        groups = list(filter(lambda group: group.name == group_name,
                             gitlab.groups.list(search=group_name)))
        if len(groups) == 0:
            raise GroupException("Group '{}' not found".format(group_name))
        return groups[0]

    def get_user(self, login):
        users = list(filter(lambda user: user.username == login,
                            self.gitlab.users.list(username=login)))
        if len(users) == 0:
            raise UserException("User '{}' not found".format(login))
        return users[0]

    @retry(stop_max_attempt_number=5)
    def get_or_create_project(self, project_name):
        logger.info("Looking up for a project '{}'".format(project_name))

        projects = list(filter(lambda project: project.name == project_name,
                               self.group.projects.list(search=project_name)))
        if len(projects) > 0:
            logger.info("Found existing project '{}'".format(project_name))
            return self.gitlab.projects.get(projects[0].id)

        logger.info("Project '{}' not found, creating a new one".format(project_name))
        return self.gitlab.projects.create({
            "name": project_name,
            "namespace_id": self.group.id,
            "builds_enabled": True,
        })

    def delete_project(self, project_name):
        self.get_or_create_project(project_name).delete()

    def add_user(project, user, access_level):
        members = list(filter(lambda member: member.id == user.id, project.members.list()))
        if len(members) == 0:
            logger.info("Adding User '{}' to the project '{}'".format(user.username, project.name))
            project.members.create({
                "user_id": user.id,
                "access_level": access_level,
            })
        else:
            logger.info("User '{}' is already a member of project '{}'".format(user.username, project.name))

    @retry(stop_max_attempt_number=5)
    def upload_file(project, **kwargs):
        logger.info("Uploading '{}' to the project '{}'".format(kwargs['file_path'], project.name))
        project.files.create(kwargs)

    def upload_files(self, project):
        CourseGitlab.upload_file(
            project, file_path='README.md', branch='master',
            content=open(self.config.README).read(), commit_message='Create README.md'
        )
        for file_path in self.config.file_paths:
            CourseGitlab.upload_file(
                project, file_path=file_path, branch='master',
                content=open(self.config.GITIGNORE).read(),
                commit_message="Create {}".format(file_path)
            )

    def create_project_full(self, project_name, user_login, master_login):
        project = self.get_or_create_project(project_name)
        user = self.get_user(user_login)
        CourseGitlab.add_user(project, user, gitlab.DEVELOPER_ACCESS)
        self.upload_files(project)
        project.branches.get('master').protect()
        master = self.get_user(master_login)
        CourseGitlab.add_user(project,  master, gitlab.MASTER_ACCESS)
