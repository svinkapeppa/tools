#!/usr/bin/env python3


import argparse
import logging
import os

import httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from retrying import retry

import library as lib

SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Test Conc Bot'
SPREADSHEET_ID = "1PuWau1Qo34PMSPUm9XHnOSeOlxGazSeoQgzZd3vS6rk"

logger = logging.getLogger(__name__)


def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


class CourseSheet:
    RANGE_REPO_FORM = "'Таблица логинов'!A:E"
    RANGE_UPDATE_FORM = "'Таблица логинов'!E{}"

    def __init__(self, service, spreadsheetId):
        self.service = service
        self.spreadsheetId = spreadsheetId

    @retry
    def get_repo_requests(self):
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheetId,
            range=CourseSheet.RANGE_REPO_FORM
        ).execute()

        values = result['values'][1:]
        return values

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=10000)
    def set_repo_status(self, index, status):
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheetId,
            range=CourseSheet.RANGE_UPDATE_FORM.format(index + 2),
            valueInputOption="USER_ENTERED",
            body={"values": [[status]]}).execute()


def configure_argparser():
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.required = True

    create = subparsers.add_parser("create_repos", help="Create repositories from google spreadsheet")
    verify = subparsers.add_parser("verify_login", help="Verify data from google spreadsheet")

    return parser


def create_repos(sheet):
    gitlab = lib.get_gitlab()
    requests = sheet.get_repo_requests()
    print(requests)
    for i, req in enumerate(requests):
        if len(req) < 4:
            logger.exception("Not all information is given")
        else:
            team = req[1]
            login = req[2]
            name = '-'.join(req[3].split()).lower()

            if len(req) == 4:
                sheet.set_repo_status(i, "PROCESSING")

                try:
                    sheet.set_repo_status(i, "OK")
                    lib.create_project(gitlab, login, name, team)
                except Exception:
                    logger.exception("Can't create project")
                    sheet.set_repo_status(i, "PROCESSING")

            elif (len(req) == 5) and (req[4] == 'PROCESSING'):
                try:
                    lib.delete_project(gitlab, name, team)
                except Exception:
                    logger.exception("Can't delete project")

                sheet.set_repo_status(i, "PROCESSING")

                try:
                    sheet.set_repo_status(i, "OK")
                    lib.create_project(gitlab, login, name, team)
                except Exception:
                    logger.exception("Can't create project")
                    sheet.set_repo_status(i, "PROCESSING")


def verify_users(sheet):
    gitlab = lib.get_gitlab()
    requests = sheet.get_repo_requests()
    print(requests)
    for i, req in enumerate(requests):
        login = req[2]

        try:
            lib.verify_login(gitlab, login)
        except Exception:
            logger.exception("Invalid login")

        sheet.set_repo_status(i, "OK")


def get_sheet_from_env():
    credentials = get_credentials()
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
    elif flags.cmd == "verify_login":
        verify_users(course)


if __name__ == '__main__':
    main()
