# Julgamento

Julgamento (Trial) is an enviroment for evaluating annotated corpora in the [CoNLL-U](https://universaldependencies.org/format.html) format. It is being developed and used by the research group [ComCorHd (Computational Linguistics, Corpus and Digital Humanities)](http://comcorhd.letras.puc-rio.br), from the Linguistics Department of PUC-Rio, in Brazil, for the project Linguistic resources for Portuguese Natural Language Processing.

Julgamento is part of [ET: a workstation for querying, revising and evaluating annotated corpora](http://comcorhd.letras.puc-rio.br/ET).

If you want to run your own version of Julgamento, a Linux computer and Python 3 are needed.

# 4-steps Tutorial

1) The recommended way to download the repository is by cloning it. In a terminal, execute the following command:

	$ git clone https://github.com/alvelvis/Julgamento.git


2) That way, whenever you want to update the repository, you can simply pull the updates inside the folder:

	$ git pull

3) After downloading the repository, install the requirements to your Python 3 libraries:

	$ pip3 install -r requirements.txt

4) And then, whenever you want to run Julgamento locally, run the command:

	$ sh run_julgamento.sh

All set, you'll be able to access Julgamento by the local page [http://127.0.0.1:5050/](http://127.0.0.1:5050/). End the server by pressing "Ctrl+C" in the terminal window.
