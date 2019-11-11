#não é pra ser executado
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

mv $1.conllu $1
cp *.py udpipe-* $1
cd $1
python3 tratar_conllu.py $1.conllu
python3 split_conllu.py $1_editado.conllu > /dev/null
python3 generate_release.py . > /dev/null
cat $2-train.conllu $2-dev.conllu > $2-train_e_dev.conllu

./udpipe-1.2.0 --train --tokenizer=none --tagger --parser $1.udpipe $2-train_e_dev.conllu

if [ ! -d MC_$1 ]; then
	mkdir MC_$1
fi
python3 tokenizar_conllu.py $2-test.conllu test_tokenizado.conllu
python3 udpipe_vertical.py $1.udpipe test_tokenizado.conllu MC_$1/$1_sistema.conllu
cp $2-test.conllu MC_$1/$1_golden.conllu
