#!/usr/bin/python3


import httplib2
import os
import re
import argparse
import logging
import time
import pprint
import datetime


from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage


import course_gitlab


SPREADSHEET_ID = "1PuWau1Qo34PMSPUm9XHnOSeOlxGazSeoQgzZd3vS6rk"
ENV_CREDENTIALS = "TEST-CONC-TABLE"


logger = logging.getLogger(__name__)


SHEET_RESULTS='Оценки'
SHEET_REJUDGE='Rejudge'
SHEET_LEADERBOARD='Leaderboard'


class CourseSheet:
    RANGE_SUBMIT_LOG = "Лог Посылок"
    RANGE_REPO_FORM = "'Заявки на Репозиторий'!A:D"
    RANGE_UPDATE_FORM = "'Заявки на Репозиторий'!D{}"
    RANGE_TASK_HEADER = "'{sheet}'!2:2"
    RANGE_STUDENTS = "'{sheet}'!A3:C1000"
    RANGE_UPDATE_SCORE = "'{sheet}'!{x}{y}"

    def __init__(self, service, spreadsheetId):
        self.service = service
        self.spreadsheetId = spreadsheetId

    def get_repo_requests(self):
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheetId,
            range=CourseSheet.RANGE_REPO_FORM
        ).execute()

        values = result['values'][1:]
        return values

    def set_repo_status(self, index, status):
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheetId,
            range=CourseSheet.RANGE_UPDATE_FORM.format(index + 2),
            valueInputOption="USER_ENTERED",
            body={"values": [[status]]}).execute()

    def add_student(self, name, login, repo_url):
        if len(name) == 0 or re.match("\W", name[0], flags=re.UNICODE):
            raise ValueError("Name looks fishy")

        if len(login) == 0 or re.match("\W", login[0], flags=re.UNICODE):
            raise ValueError("Login looks fishy")

        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheetId,
            range=CourseSheet.RANGE_STUDENTS.format(sheet=SHEET_RESULTS),
            valueInputOption="USER_ENTERED",
            body={"values": [[
                '=HYPERLINK("{}";"git")'.format(repo_url),
                name,
                login, # Spreadsheet injection, Oh My!
            ]]}).execute()
    

def configure_argparser():
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.required = True

    repos_parser = subparsers.add_parser("create_repos", help="Create repositories from google form")
    return parser


def create_repos(sheet):
    gitlab = course_gitlab.get_gitlab()
    requests = sheet.get_repo_requests()
    for i, req in enumerate(requests):
        if len(req) > 3:
            continue

        name = req[1]
        login = req[2]
        try:
            course_gitlab.create_project(gitlab, login)
            sheet.add_student(name, login, "https://gitlab.com/test-conc/student-" + login)
            sheet.set_repo_status(i, "OK")
        except Exception:
            logger.exception("Can't create project")

        time.sleep(1.0) # More time to press ^C


def get_sheet_from_env():
    if ENV_CREDENTIALS not in os.environ:
        raise ValueError(ENV_CREDENTIALS + " not set")
    credentials = client.Credentials.new_from_json(os.environ[ENV_CREDENTIALS])
    http = credentials.authorize(httplib2.Http())

    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
    logger.info("API Discovery Finished")

    course = CourseSheet(service, SPREADSHEET_ID)
    return course


def main():
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.ERROR)
    logger.setLevel(logging.INFO)

    parser = configure_argparser()
    flags = parser.parse_args()

    course = get_sheet_from_env()

    if flags.cmd == "create_repos":
        create_repos(course)


if __name__ == '__main__':
    main()