# Julgamento

Julgamento (Trial) is an enviroment for evaluating annotated corpora in the [CoNLL-U](https://universaldependencies.org/format.html) format. It is being developed and used by the research group [ComCorHd (Computational Linguistics, Corpus and Digital Humanities)](http://comcorhd.letras.puc-rio.br), from the Linguistics Department of PUC-Rio, in Brazil, for the project Linguistic resources for Portuguese Natural Language Processing.

Julgamento is part of [ET: a workstation for querying, revising and evaluating annotated corpora](http://comcorhd.letras.puc-rio.br/ET). Consider also installing [Interrogatório](https://github.com/alvelvis/Interrogat-rio), an enviroment for querying and revising annotated corpora, in the same folder as Julgamento to integrate both.

If you wish to run your own version of Julgamento, a Linux computer (or Windows with [Windows Subsystem for Linux](https://docs.microsoft.com/pt-br/windows/wsl/install-win10)), `python3` and `virtualenv` are needed.

If you wish to deploy Julgamento to a web server, using Ubuntu/Apache2, check [Deploying with Ubuntu/Apache2](https://github.com/alvelvis/Interrogat-rio/wiki/Deploying-with-Ubuntu-Apache2).

Check the [Wiki](https://github.com/alvelvis/Julgamento/wiki) for a broader understanding of Julgamento tools.

# How to install: 4-steps Tutorial

1) The recommended way to download the repository is by cloning it. In a terminal, execute the following command:

	$ git clone https://github.com/alvelvis/Julgamento.git

2) Change to the directory:

	$ cd Julgamento

3) After downloading the repository, run the command below, and it will then create a Python 3 virtual environment and install the requirements in order to run Julgamento.

	$ sh install_julgamento.sh
	
4) Then, whenever you intend to run Julgamento locally, run the command below and it will also auto-update when necessary if you cloned the repo using Git:

	$ sh run_julgamento.sh

All set, you'll be able to access Julgamento by the local page [http://127.0.0.1:5050/](http://127.0.0.1:5050/). End the server by pressing "Ctrl+C" in the terminal window.

# How to cite

```
@inproceedings{ETtilic,
  title={ET: uma Estação de Trabalho para revisão, edição e avaliação de corpora anotados morfossintaticamente},
  author={de Souza, Elvis and Freitas, Cl{\'a}udia},
  booktitle={VI Workshop de Iniciação Científica em Tecnologia da Informação e da Linguagem Humana (TILic 2019)},
  place={Salvador, BA, Brazil, Outubro, 15-18, 2019},
  year={2019}
}
```
