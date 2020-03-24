import sys
import time, os

os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

sys.path.insert(0, "/var/www/Julgamento")
import site

site.addsitedir('/var/www/Julgamento/.julgamento/lib/python3.6/site-packages')

from app import app as application
