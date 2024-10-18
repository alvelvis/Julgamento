# Julgamento

Julgamento is an enviroment for evaluating annotated corpora in the [CoNLL-U](https://universaldependencies.org/format.html) format. It's been used in several research projects at PUC-Rio, including **Linguistic resources for Portuguese Natural Language Processing** from the Linguistics Department of PUC-Rio, in Brazil, under the supervision of Prof. Cláudia Freitas, and project [**Petrolês**](https://petroles.puc-rio.ai), at the Applied Computational Intelligence Laboratory from PUC-Rio.

Julgamento is part of ET: a workstation for querying, revising and evaluating annotated corpora. Consider also installing [Interrogatório](https://github.com/alvelvis/Interrogat-rio), an enviroment for querying and revising annotated corpora, in the same folder as Julgamento to integrate both.

If you wish to deploy Julgamento to a web server, using Ubuntu/Apache2, check [Deploying with Ubuntu/Apache2](https://github.com/alvelvis/Julgamento/wiki/Deploying-with-Ubuntu-Apache2).

Check the [Wiki](https://github.com/alvelvis/Julgamento/wiki) for a broader understanding of Julgamento tools.

# How to run on a Windows machine

1) Go to [releases](https://github.com/alvelvis/Julgamento/releases)

2) Download the latest version `Julgamento.zip`

3) Extract the folder `Julgamento` from the zip file

4) Double click `julgamento_for_windows.bat`

# How to install in a local server: 4-steps Tutorial

If you wish to run Julgamento in a local server, a Linux computer (or Windows with [Windows Subsystem for Linux](https://docs.microsoft.com/pt-br/windows/wsl/install-win10)), `python3` and `virtualenv` are needed.

1) The recommended way to download the repository is by cloning it. In a terminal, execute the following command:

	$ git clone https://github.com/alvelvis/Julgamento.git --recursive

2) Change to the directory:

	$ cd Julgamento

3) After downloading the repository, run the command below, and it will then create a Python 3 virtual environment and install the requirements in order to run Julgamento.

	$ sh install_julgamento.sh
	
4) Then, whenever you intend to run Julgamento locally, run the command below and it will also auto-update when necessary if you cloned the repo using Git:

	$ sh run_julgamento.sh

All set, you'll be able to access Julgamento by the local page [http://127.0.0.1:5050/](http://127.0.0.1:5050/). End the server by pressing "Ctrl+C" in the terminal window.

# How to cite

```
@inproceedings{de-souza-freitas-2021-et,
    title = "{ET}: A Workstation for Querying, Editing and Evaluating Annotated Corpora",
    author = "de Souza, Elvis  and
      Freitas, Cl{\'a}udia",
    booktitle = "Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing: System Demonstrations",
    month = nov,
    year = "2021",
    address = "Online and Punta Cana, Dominican Republic",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2021.emnlp-demo.5",
    pages = "35--41",
    abstract = "In this paper we explore the functionalities of ET, a suite designed to support linguistic research and natural language processing tasks using corpora annotated in the CoNLL-U format. These goals are achieved by two integrated environments {--} Interrogat{\'o}rio, an environment for querying and editing annotated corpora, and Julgamento, an environment for assessing their quality. ET is open-source, built on different Python Web technologies and has Web demonstrations available on-line. ET has been intensively used in our research group for over two years, being the chosen framework for several linguistic and NLP-related studies conducted by its researchers.",
}
