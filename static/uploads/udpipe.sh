# $1 = arquivo a ser treinado, sem .conllu

set -e

if [ $# -eq 0 ]
  then
    echo "No arguments supplied"
    exit
fi

if [ ! -d $1 ]; then
	mkdir $1
fi

mv $1.conllu $1
cp *.py $2*.txt $1
cd $1
python3 tratar_conllu.py $1.conllu
python3 split_conllu.py $1_editado.conllu
python3 generate_release.py .
cat *-train.conllu *-dev.conllu > $1_train_e_dev.conllu

cd ..
cp udpipe* $1
cd $1
./udpipe-1.2.0 --train --tokenizer=none --tagger --parser $1.udpipe $1_train_e_dev.conllu

cd ..
cd $1
if [ ! -d MC_$1 ]; then
	mkdir MC_$1
fi
python3 tokenizar_conllu.py $2-test.conllu test_tokenizado.conllu
python3 udpipe_vertical.py $1.udpipe test_tokenizado.conllu MC_$1/$1_sistema.conllu
cp $2-test.conllu MC_$1/$1_golden.conllu
#cp estrutura_dados.py estrutura_ud.py conll18_ud_eval.py MC_$1/
cd MC_$1
cp $1_sistema.conllu ../../$1_sistema.conllu
cp $1_golden.conllu ../../$1.conllu
mv ../../$1_inProgress ../../$1_success
cd ../../
rm -r $1
exit
#python3 confusao.py $1_golden.conllu $1_sistema.conllu $1 8
