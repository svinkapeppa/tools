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


import check_gitlab
import course_gitlab


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
    RANGE_REPO_FORM = "'Таблица логинов'!A:C"
    RANGE_UPDATE_FORM = "'Таблица логинов'!C{}"
    
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


def configure_argparser():
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.required = True

    repos_parser = subparsers.add_parser("check", help="Check logins from google form")
    return parser


def check(sheet):
    gitlab = course_gitlab.get_gitlab()
    requests = sheet.get_repo_requests()
    print(requests)
    for i, req in enumerate(requests):
        login = req[1]

        try:
            check_gitlab.check_user(gitlab, login)
        except Exception:
            logger.exception("Invalid login")
        
        flag = 1
        sleep_time = 10
        while flag == 1:
            try:
                sheet.set_repo_status(i, "OK")
                flag = 0
            except Exception:
                time.sleep(sleep_time)
                sleep_time *= 10
                logger.exception("Timing problem")


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

    if flags.cmd == "check":
        check(course)


if __name__ == '__main__':
    main()