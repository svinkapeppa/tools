import logging
import os

import httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from retrying import retry

import config as cfg

logger = logging.getLogger(__name__)


def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, cfg.CREDENTIALS_DIR)
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   cfg.CREDENTIALS_FILE)

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(cfg.CLIENT_SECRET_FILE, cfg.SCOPES)
        flow.user_agent = cfg.APPLICATION_NAME
        credentials = tools.run_flow(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


class CourseSheet(object):
    RANGE_REPO_FORM = "'Таблица логинов'!A:E"
    RANGE_UPDATE_FORM = "'Таблица логинов'!E{}"

    class Row(object):
        def __init__(self, team, login, name, status, row_index):
            self.team = team
            self.login = login
            self.name = name
            self.status = status
            self.row_index = row_index

    def __init__(self, service, spreadsheetId):
        self.service = service
        self.spreadsheetId = spreadsheetId

    def read_sheet_rows(self):
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheetId,
            range=CourseSheet.RANGE_REPO_FORM
        ).execute()

        return result['values']

    def get_requests(self):
        rows = self.read_sheet_rows()

        for row_index in range(1, len(rows)):
            row = rows[row_index]

            if len(row) < 4:
                logger.warning("invalid {}-th row: {}".format(row_index, row))
                continue

            team = row[1]
            login = row[2]
            name = '-'.join(row[3].split()).lower()

            status = row[4] if len(row) >= 5 else None

            yield self.Row(team, login, name, status, row_index)

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=10000)
    def set_repo_status(self, index, status):
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheetId,
            range=CourseSheet.RANGE_UPDATE_FORM.format(index + 1),
            valueInputOption="USER_ENTERED",
            body={"values": [[status]]}).execute()


def get_sheet_from_env():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())

    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
    logger.info("API Discovery Finished")

    course = CourseSheet(service, cfg.SPREADSHEET_ID)
    return course
