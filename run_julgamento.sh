if [ -d .git ]; then
  git update-index --assume-unchanged config.py
  git update-index --assume-unchanged localtime.py
  git pull
fi

if ! python3 -c "import tqdm"; then
  if ! pip3 install -r requirements.txt; then
    sudo apt install python3-pip
    pip3 install -r requirements.txt
  fi
fi

if [ ! -e prod.db ]; then
  python3 once.py
  sudo chmod a+rwx -R *
fi

export OAUTHLIB_INSECURE_TRANSPORT=1
export OAUTHLIB_RELAX_TOKEN_SCOPE=1
python3 app.py prod
