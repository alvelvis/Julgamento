import sys
import time, os

os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

sys.path.insert(0, "/home/elvis_desouza99/Dropbox/tronco/comcorhd.tronco.me/julgamento")
import site

site.addsitedir('/home/elvis_desouza99/Dropbox/tronco/comcorhd.tronco.me/julgamento/venv/lib/python3.6/site-packages')

from app import app as application
