if [ ! -d .julgamento ]; then
    virtualenv .julgamento -p python3
fi

. .julgamento/bin/activate
pip3 install -r requirements.txt
if [ ! -e prod.db ]; then
    python3 once.py
    sudo chmod a+rwx -R *
fi