# $1 = arquivo a ser treinado, sem .conllu

set -e

if [ $# -eq 0 ]
  then
    echo "No arguments supplied"
    exit
fi

if [ ! -d $1 ]; then
	mkdir $1
else
	mv $1/$1.conllu .
fi

echo "\n" 2>&1 | tee -a $1/log.txt
date 2>&1 | tee -a $1/log.txt
echo "============== INICIANDO crossvalidation de $1.conllu ==============" 2>&1 | tee -a $1/log.txt

echo "movendo arquivos para $1" 2>&1 | tee -a $1/log.txt
mv $1.conllu $1
cp *.py *.txt crossvalidation_udpipe.sh udpipe-* $1
cd $1
echo "executando crossvalidation.py na pasta $1" 2>&1 | tee -a log.txt
python3 crossvalidation.py $1 $2
