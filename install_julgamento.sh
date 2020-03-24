if [ ! -d .julgamento ]; then
    if ! virtualenv .julgamento -p python3.6; then
        sudo apt install virtualenv
        virtualenv .julgamento -p python3.6
    fi
fi

. .julgamento/bin/activate
pip3 install -r requirements.txt
if [ ! -e prod.db ]; then
    python3 once.py
    sudo chmod a+rwx -R *
fi
