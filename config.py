GITLAB_GROUP = "tpcc-course-2018"
GITLAB_TOKEN_ENV = "8k7sushNjNLT27sCcUW-"

SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Test Conc Bot'
SPREADSHEET_ID = "1PuWau1Qo34PMSPUm9XHnOSeOlxGazSeoQgzZd3vS6rk"

CREDENTIALS_DIR = '.credentials'
CREDENTIALS_FILE = 'sheets.googleapis.com-python-quickstart.json'

README = './tmp/README.md'
GITIGNORE = './tmp/.gitignore'

HOOKURL = 'http://tpcc.btty.su:8080/project/test'
HOOKTOKEN = '9d944bdd33b48e51c604803c54944a5c'

file_paths = [
    '1-mutex/.gitignore',
    '2-cond-var/.gitignore',
    '3-fine-grained/.gitignore',
    '4-cache/.gitignore',
    '5-memory-model/.gitignore',
    '6-lock-free/.gitignore',
    '7-linearizability/.gitignore',
    '8-consensus/.gitignore',
]

teachers = {
    '691': 'kamiltalipov',
    '692': 'ksamelyuk',
    '693': 'misty-fungus',
    '694': 'tau0',
    '695': 'Lipovsky',
    '696': 'akazz',
    '697': 'tau0',
    '699': 'velavokr',
}

deadlines = [
    (r"^1-mutex/.*$", "2018-03-06 09:00:00"),
    (r"^2-cond-var/.*$", "2018-03-20 09:00:00"),
    (r"^3-fine-grained/cuckoo-hash-table$", "2018-05-02 23:59:59"),
    (r"^3-fine-grained/.*$", "2018-04-03 09:00:00"),
    (r"^4-cache/.*$", "2018-04-10 09:00:00"),
    (r"^5-memory-model/.*$", "2018-04-18 09:00:00"),
    (r"^6-lock-free/stack$", "2018-05-10 09:00:00"),
    (r"^6-lock-free/queue$", "2018-05-10 09:00:00"),
    (r"^6-lock-free/list$", "2018-05-16 23:59:59"),
    (r"^6-lock-free/hash-table$", "2018-05-16 23:59:59"),
    (r"^7-linearizability/.*$", "2018-05-10 09:00:00"),
    (r"^8-consensus/.*$", "2018-05-16 23:59:59"),
]
