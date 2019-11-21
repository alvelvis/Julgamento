if [ -d .git ]; then
  git update-index --assume-unchanged config.py
  git update-index --assume-unchanged localtime.py
fi

if [ ! -e prod.db ]; then
  python3 once.py
fi

export OAUTHLIB_INSECURE_TRANSPORT=1
export OAUTHLIB_RELAX_TOKEN_SCOPE=1
python3 app.py prod
