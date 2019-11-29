import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))
APP_NAME = "julgamento"
VALIDATE_UD = f'{os.path.abspath(os.path.dirname(__file__))}/validate.py'
VALIDAR_UD = f'{os.path.abspath(os.path.dirname(__file__))}/validar_UD.txt'
VALIDATE_LANG = 'PT'
DEBUG = True
SQLALCHEMY_TRACK_MODIFICATIONS = False
EXECUTOR_PROPAGATE_EXCEPTIONS = True
EXECUTOR_MAX_WORKERS = 1
SECRET_KEY = 'ALSKDJHALSKDJHALK'
SQLALCHEMY_ECHO = True
SQLALCHEMY_COMMIT_ON_TEARDOWN = True
OAUTHLIB_RELAX_TOKEN_SCOPE = 1
SEND_FILE_MAX_AGE_DEFAULT = 0
COMCORHD = False
GOOGLE_LOGIN = False
REPOSITORIES = [
	'',
]
GOOGLE_CLIENT_ID = ''
GOOGLE_SECRET_KEY = ''
ALLOWED_GOOGLE_EMAILS = '''

	'''.strip().replace(" ", "").replace('\t', '').replace('\n', '').split("|")

UPLOAD_FOLDER = f"{os.path.abspath(os.path.dirname(__file__))}/static/uploads"
JULGAMENTO_FOLDER = os.path.abspath(os.path.dirname(__file__))
COMCORHD_FOLDER = f"{os.path.abspath(os.path.dirname(__file__)).rsplit('/', 1)[0]}/Interrogat-rio/www/interrogar-ud/conllu"
ALLOWED_EXTENSIONS = "conllu".split("|")
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASEDIR, "prod.db")
