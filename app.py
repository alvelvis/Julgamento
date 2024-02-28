import config, sys, re, estrutura_ud, html, os, subprocess, time, shutil, pickle, threading
from estrutura_ud import idx_to_col, col_to_idx
import pandas as pd
from flask import Flask, redirect, url_for, session, request, make_response, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from jinja2 import Template, escape, Markup, Environment
from interrogar_UD import getDistribution
import datetime
import validar_UD, utils
from utils import cleanEstruturaUD
from subprocess import Popen
import json

def tracefunc(frame, event, arg, indent=[0]):
      if event == "call":
          indent[0] += 2
          print("-" * indent[0] + "> call function", frame.f_code.co_name)
      elif event == "return":
          print("<" + "-" * indent[0], "exit function", frame.f_code.co_name)
          indent[0] -= 2
      return tracefunc

#sys.setprofile(tracefunc)
#sys.settrace()

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

class Corpora:

    def __init__(self):
        self.corpora = {}

class Modificacoes:

	def __init__(self):
		self.modificacoes = {}

allCorpora = Corpora()
modificacoesCorpora = Modificacoes()

@app.route("/api/getPhrases", methods=["POST"])
def getPhrases():
	dist = getDistribution(allCorpora.corpora[conllu(request.values.get("c")).first()], parametros='word = ".*" and sent_id = "' + request.values.get("sent_id") + '"', coluna="children")

	return jsonify({
		'html': "- " + "<br>- ".join(dist["all_children"]),
		'success': True
	})

@app.route("/api/changeAbout", methods="POST".split("|"))
def changeAbout():
	corpus = db.session.query(models.Corpus).get(request.values.get("c"))
	corpus.about = re.sub(r'<.*?>', "", request.values.get("about"))
	db.session.merge(corpus)
	db.session.commit()

	return jsonify({
		'html': db.session.query(models.Corpus).get(request.values.get("c")).about,
		'success': True
	})

@app.route("/api/refreshTables", methods="POST".split("|"))
def refreshTables():
	if request.values.get("c") in modificacoesCorpora.modificacoes:
		modificacoesCorpora.modificacoes.pop(request.values.get("c"))
	allCorpora.corpora.pop(conllu(request.values.get("c")).first())
	#allCorpora.corpora[] = ""
	if conllu(request.values.get("c")).second() in allCorpora.corpora:
		allCorpora.corpora.pop(conllu(request.values.get("c")).second())
	if os.path.isdir(os.path.abspath(os.path.join(UPLOAD_FOLDER, "CM-" + request.values.get("c")))):
		shutil.rmtree(os.path.abspath(os.path.join(UPLOAD_FOLDER, "CM-" + request.values.get("c"))), ignore_errors=True)
	if os.path.isfile(conllu(request.values.get("c")).findErrorsET()):
		os.remove(conllu(request.values.get("c")).findErrorsET())
	if os.path.isfile(conllu(request.values.get("c")).findErrorsUD()):
		os.remove(conllu(request.values.get("c")).findErrorsUD())
	if os.path.isfile(conllu(request.values.get("c")).findErrorsUD() + "_html"):
		os.remove(conllu(request.values.get("c")).findErrorsUD() + "_html")
	return jsonify({'success': True})

@app.route("/api/getCommits", methods="POST".split("|"))
def getCommits():
	if 'branch' in request.values:
		return jsonify({
			'html': checkRepo(repositorio=request.values.get('repoName'), branch=request.values.get('branch'))['commits'],
			'success': True,
		})

	elif 'repoName' in request.values:
		return jsonify({
			'html': checkRepo(repositorio=request.values.get('repoName'))['branches'],
			'success': True,
		})

@app.route("/api/inconsistent_ngrams", methods="POST".split("|"))
def inconsistent_ngrams():
	if not os.path.isfile(os.path.abspath(os.path.join(UPLOAD_FOLDER, "CM-" + request.values.get('c'), "results_" + request.values.get('tipo') + ".json"))):
		if not 'win' in sys.platform:
			os.system("'" + JULGAMENTO_FOLDER + "/.julgamento/bin/python3' \"{}/inconsistent_ngrams.py\" \"{}\" {}".format(
				JULGAMENTO_FOLDER,
				conllu(request.values.get("c")).findFirst(), 
				request.values.get("tipo"),
				))
		else:
			subprocess.Popen('"{}\\python.exe\" "{}\\inconsistent_ngrams.py" "{}" {}'.format(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Python39"), os.path.abspath(os.path.dirname(__file__)), conllu(request.values.get("c")).findFirst(), request.values.get("tipo")), shell=False).wait()

	with open(UPLOAD_FOLDER + f"/CM-{request.values.get('c')}/results_{request.values.get('tipo')}.json") as f:
		results = json.load(f) 

	html = ""
	if not results:
		html += f"<div class='alert alert-warning translateHtml' role='alert'>Não foram encontrados n-grams inconsistentes.</div>"
	else:
		for i, exemplo in enumerate(results):
			html += f"<div class='alert alert-warning' role='alert'>{i+1} / {len(results)} - {exemplo['exemplo']}</div>"
			for k, frase in enumerate(exemplo['frases']):
				html += f'<div class="panel panel-default"><div class="panel-body">{ k+1 } / { len(exemplo["frases"]) }</div>'
				html += render_template(
						'sentence.html',
						first=allCorpora.corpora[conllu(request.values.get("c")).first()].sentences[frase["sent_id"]],
						c=request.values.get("c"),
						t=allCorpora.corpora[conllu(request.values.get("c")).first()].sentences[frase["sent_id"]].map_token_id[str(frase["id1"])],
						bold={'word': frase['WORD1'], 'color': 'red', 'id': str(frase["id1"])},
						rel=frase["rel"],
						secBold={'word': frase['WORD2'], 'color': 'blue', 'id': str(frase["id2"])},
						firstAndSecond=True if conllu(request.values.get("c")).second() in allCorpora.corpora else False
						) + "</div>"
	
	return jsonify({
		'html': html,
		'success': True,
		'c': request.values.get('c'),
	}) 

@app.route('/api/getErrorsUD', methods="POST".split("|"))
def getErrorsUD():
	html = renderErrorsUD(c=request.values.get("c"), exc=request.values.get('exceptions').split("|") if request.values.get('exceptions') else "", fromZero=True)
	return jsonify({
		'html': html,
		'success': True,
		'c': request.values.get('c'),
	})

@app.route('/api/getErrorsET', methods="POST".split("|"))
def getErrorsValidarUD():
	html = ""

	errors = validar_UD.validate(allCorpora.corpora[conllu(request.values.get("c")).first()], errorList=VALIDAR_UD, noMissingToken=True)

	if not errors:
		html = "<div class='alert alert-warning translateHtml' role='alert'>Não foram encontrados erros de validação.</div>"
	for k, error in enumerate(errors):
		html += f"<div class='alert alert-warning' role='alert'>{k+1} / {len(errors)} - {error}</div>"
		for i, value in enumerate(errors[error]):
			if value['sentence']:
				html += f'<div class="panel panel-default"><div class="panel-body">{ i+1 } / { len(errors[error]) }</div>' + \
					render_template(
						'sentence.html',
						first=value['sentence'],
						c=request.values.get("c"),
						t=value['t'],
						bold={'word': value['sentence'].tokens[value['t']].word, 'color': 'black', 'id': value['sentence'].tokens[value['t']].id},
						rel=value['sentence'].tokens[value['t']].__dict__[value['attribute']],
						firstAndSecond=True if conllu(request.values.get("c")).second() in allCorpora.corpora else False,
					) + "</div>"
			elif value['sent_id']:
				html += f'<div class="panel panel-default"><div class="panel-body">{ i+1 } / { len(errors[error]) }: {value["sent_id"]}</div></div>'

	return jsonify({
		'html': html,
		'success': True,
		'c': request.values.get('c'),
	})

@app.route('/api/filterCorpora', methods="POST".split("|"))
def filterCorpora():
	return jsonify({
		'html': findCorpora(filtro=request.values.get('filtro'), tipo=request.values.get('tipo')),
		'success': True,
	})

@app.route('/api/deleteFirst', methods="POST|GET".split("|"))
def deleteFirst():
	if os.path.isfile(conllu(request.values.get("c")).findFirst()):
		caracteristicasCorpus(request.values.get("c"))
		os.remove(conllu(request.values.get("c")).findFirst())
	if os.path.isfile(conllu(request.values.get("c")).findOriginal()):
		os.remove(conllu(request.values.get("c")).findOriginal())
	return render_template(
		'upload.html',
		success="Corpus \"" + request.values.get("c") + "\" deletado com sucesso!",
	)


@app.route('/cancelTrain', methods="GET".split("|"))
def cancelTrain():
	if not request.args.get('delete'):
		os.system('killall udpipe-1.2.0')
		return redirect("/log?c=" + request.args.get('c'))
	else:
		if request.args.get('first') == 'true':
			if os.path.isfile(conllu(request.args.get("c")).findFirst()):
				caracteristicasCorpus(request.values.get("c"))
				os.remove(conllu(request.args.get("c")).findFirst())
			if os.path.isfile(conllu(request.args.get("c")).findOriginal()):
				os.remove(conllu(request.args.get("c")).findOriginal())
			if conllu(request.values.get("c")).original in allCorpora.corpora:
				allCorpora.corpora.pop(conllu(request.values.get("c")).original)
		if os.path.isfile(conllu(request.args.get("c")).findInProgress()):
			os.remove(conllu(request.args.get("c")).findInProgress())
		if os.path.isfile(conllu(request.args.get("c")).findSecond()):
			os.remove(conllu(request.args.get("c")).findSecond())
		corpus = db.session.query(models.Corpus).get(conllu(request.args.get('c')).naked)
		if conllu(request.values.get("c")).first() in allCorpora.corpora:
			allCorpora.corpora.pop(conllu(request.values.get("c")).first())
		if conllu(request.values.get("c")).second() in allCorpora.corpora:
			allCorpora.corpora.pop(conllu(request.values.get("c")).second())
		if corpus:
			db.session.delete(corpus)
			db.session.commit()
		if not request.args.get('callback'):
			return redirect("/")
		else:
			return redirect("/" + request.args.get('callback'))

@app.route('/api/getTables', methods="POST".split("|"))
def getTables():
	table = request.values.get('table')
	matrix_col = request.values.get('matrix_col', None)

	if table == "caracteristicas":
		return jsonify({
			'html': caracteristicasCorpus(request.values.get('ud1'), request.values.get('ud2') if request.values.get('ud2') else ""),
			'success': True
		})

	elif table == 'metrics':
		return jsonify({
			'html': '<h3 class="translateHtml">Métricas de avaliação do CoNLL 2018</h3>' + metrics(request.values.get('ud1'), request.values.get('ud2')),
			'success': True
			})

	elif table == 'sentAccuracy':
		return jsonify({
			'html': '<h3 class="translateHtml">Sentenças com UPOS e DEPREL corretas</h3>' + sentAccuracy(request.values.get('ud1'), request.values.get('ud2')),
			'success': True,
		})

	elif table == 'accuracy':
		return jsonify({
			'html': f'''
			<!--div id="POSAccuracy" class="col-lg-4">
				<div class=" panel panel-default panel-body">
					<h3 class="translateHtml" style="text-align:center; ">Acurácia por UPOS</h3>
					{categoryAccuracy(request.values.get('ud1'), request.values.get('ud2'), request.values.get('c'), 'UPOS')['tables']}
				</div>
			</div-->
			<div id="DEPRELAccuracy" class="col-lg-12">
				<div class=" panel panel-default panel-body">
					<h3 class="translateHtml" style="text-align:center; ">Acurácia por DEPREL</h3>
					{categoryAccuracy(request.values.get('ud1'), request.values.get('ud2'), request.values.get('c'), 'DEPREL')['tables']}
				</div>
			</div>
			''',
			'success': True
		})

	elif table == 'matrix':
		matrix_col = matrix_col.lower()
		ud1Estruturado = allCorpora.corpora.get(conllu(request.values.get('ud1')).first())
		ud2Estruturado = allCorpora.corpora.get(conllu(request.values.get('ud2')).second())
		listaPOS = confusao.get_list(ud1Estruturado, ud2Estruturado, matrix_col)
		listaPOS1 = listaPOS['matriz_1']
		listaPOS2 = listaPOS['matriz_2']
		pd.options.display.max_rows = None
		pd.options.display.max_columns = None
		pd.set_option('display.expand_frame_repr', False)
		return jsonify({
			'html': '<h3 class="translateHtml">Matriz de confusão de {}</h3>'.format(matrix_col.upper()) + matrix(str(pd.crosstab(pd.Series(listaPOS1), pd.Series(listaPOS2), rownames=['principal'], colnames=['secundário'], margins=True)), request.values.get('c'), kind=matrix_col),
			'success': True,
		})

	elif table == 'errorUD':
		return ""

	elif table == 'errorET':
		return ""

	elif table == 'inconsistent_ngrams':
		return ""

	elif table == "accuracy_columns":
		return jsonify({
			'html': get_accuracy(
				corpus1=allCorpora.corpora.get(conllu(request.values.get('ud1')).first()),
				corpus2=allCorpora.corpora.get(conllu(request.values.get('ud2')).second())
				),
			'success': True,
		})
	
	elif table == "iaa":
		return jsonify({
			'html': get_kappa(
				corpus1=allCorpora.corpora.get(conllu(request.values.get('ud1')).first()),
				corpus2=allCorpora.corpora.get(conllu(request.values.get('ud2')).second())
				),
			'success': True,
		})
	
	elif table == "divergences":
		return jsonify({
			'html': get_divergences(
				corpus1=allCorpora.corpora.get(conllu(request.values.get('ud1')).first()),
				corpus2=allCorpora.corpora.get(conllu(request.values.get('ud2')).second()),
				c=request.values.get('c')
				),
			'success': True,
		})
	

@app.route('/upload', methods="GET|POST".split("|"))
def upload(alert="", success=""):
	if request.method == "GET":
		return render_template(
			'upload.html',
			formDB=formDB()
		)

	elif request.method == "POST" and 'firstFile' in request.files:
		firstFile = request.files.get('firstFile')
		if firstFile.filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS:			
			firstFileName = removerAcento(conllu(request.values.get('firstName')).first())
			if (INTERROGATORIO and not os.path.isfile(os.path.abspath(os.path.join(COMCORHD_FOLDER, firstFileName)))) or (not INTERROGATORIO and not os.path.isfile(os.path.abspath(os.path.join(UPLOAD_FOLDER, firstFileName)))):
				firstFile.save(os.path.abspath(os.path.join(COMCORHD_FOLDER, firstFileName))) if INTERROGATORIO else firstFile.save(os.path.abspath(os.path.join(UPLOAD_FOLDER, firstFileName)))
				shutil.copyfile(conllu(firstFileName).findFirst(), conllu(firstFileName).findOriginal())
				textInterrogatorio = "(1) Realize buscas e edições no corpus pelo <a href='http://github.com/alvelvis/Interrogat-rio'>Interrogatório</a>, ou, (2) "
				success = f'"{firstFileName}" enviado com sucesso! {textInterrogatorio if INTERROGATORIO else ""}Avalie-o na <a href="/corpus">página inicial</a>.'
			else:
				alert = "Arquivo já existe na pasta."
		else:
			alert = 'Extensão deve estar entre "' + ",".join(ALLOWED_EXTENSIONS) + '"'

	elif request.method == "POST" and 'secondFile' in request.files:
		firstFile = request.values.get('sysfirstFile')
		secondFile = request.files.get('secondFile')
		if secondFile.filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS:			
			secondFileName = conllu(firstFile).second()
			secondFile.save(os.path.abspath(os.path.join(UPLOAD_FOLDER, secondFileName)))
			if not os.path.isfile(conllu(secondFileName).findOriginal()):
				shutil.copyfile(conllu(secondFileName).findFirst(), conllu(secondFileName).findOriginal())
			corpusFirst = estrutura_ud.Corpus(recursivo=False)
			corpusSecond = estrutura_ud.Corpus(recursivo=False)
			corpusFirst.load(conllu(firstFile).findFirst())
			corpusSecond.load(conllu(firstFile).findSecond())
			if len(corpusFirst.sentences) != len(corpusSecond.sentences):
				alert = "Segunda versão não tem o mesmo número de sentenças do arquivo principal."
				os.remove(conllu(firstFile).findSecond())
			else:
				success = f'"{secondFileName}" enviado com sucesso! Avalie o corpus na <a href="/corpus">página inicial</a>.'
				addDatabase(firstFile)
			#loadCorpus.submit(firstFile)
			del corpusFirst
			del corpusSecond
		else:
			alert = 'Extensão deve estar entre "' + ",".join(ALLOWED_EXTENSIONS) + '"'

	elif request.method == 'POST' and 'trainFile' in request.values:
		if not 'win' in sys.platform:
			corpusTemporario = False
			if os.path.isfile(COMCORHD_FOLDER + "/" + conllu(request.values.get('trainFile')).first()):
				os.system(f'cp {COMCORHD_FOLDER + "/" + conllu(request.values.get("trainFile")).first()} {UPLOAD_FOLDER}')
				corpusTemporario = f"; rm {UPLOAD_FOLDER}/{conllu(request.values.get('trainFile')).first()} &"
			if not request.values.get('crossvalidation'):
				Popen(f"cd {UPLOAD_FOLDER}; cp {conllu(request.values.get('trainFile')).first()} {conllu(request.values.get('trainFile')).naked + '_test'}.conllu; sh udpipe.sh {conllu(request.values.get('trainFile')).naked + '_test'} {request.values.get('partitions')} 2>&1 | tee -a {conllu(request.values.get('trainFile')).naked + '_test'}_inProgress {corpusTemporario if corpusTemporario else '&'}", shell=True)
				nomeConllu = conllu(request.values.get('trainFile')).naked + "_test"
			else:
				Popen(f"cd {UPLOAD_FOLDER}; sh crossvalidation.sh {request.values.get('trainFile')} {request.values.get('partitions')} 2>&1 | tee -a {request.values.get('trainFile')}_inProgress {corpusTemporario if corpusTemporario else '&'}", shell=True)
				nomeConllu = conllu(request.values.get('trainFile')).naked
			try:
				novoCorpus = models.Corpus(
					name=nomeConllu,
					date=str(datetime.datetime.now()),
					sentences=0,
					about=request.values.get('about') if request.values.get('about') else "Editar descrição",
					partitions=request.values.get('partitions'),
				)
				db.session.add(novoCorpus)
				db.session.commit()
			except TypeError as e:
				raise Exception("Apague o arquivo prod.db e tente novamente. (%s)" % e)
			success = "Um modelo está sendo treinado a partir do corpus \"" + nomeConllu + "\". Acompanhe o status do treinamento na <a href='/'>página inicial do Julgamento.</a>"
		else:
			raise Exception("Only available on Linux.")

	elif request.method == 'POST' and 'repoName' in request.values:
		if not 'win' in sys.platform:
			sh = f"cd {UPLOAD_FOLDER}/repositories/{request.values.get('repoName')}; \
					git pull; \
						git checkout {request.values.get('repoCommit').split(' | commit ')[1]}; \
							cat documents/*.conllu > {conllu(removerAcento(request.values.get('repoCorpusName'))).findFirst()}; \
								cat documents/*.conllu > {conllu(removerAcento(request.values.get('repoCorpusName'))).findOriginal()}"
			if request.values.get('criarRamo'):
				sh += f"; git checkout -b {removerAcento(request.values.get('repoCorpusName'))}; \
							git push --set-upstream origin {removerAcento(request.values.get('repoCorpusName'))}"

			if not os.path.isfile(f"{conllu(removerAcento(request.values.get('repoCorpusName'))).findFirst()}"):
				os.system(sh)
				textInterrogatorio = "(1) Realize buscas e edições no corpus pelo <a href='http://github.com/alvelvis/interrogat-rio'>Interrogatório</a>, ou, (2) "
				success = f"Corpus {'e ramo ' if request.values.get('criarRamo') else ''}\"{removerAcento(request.values.get('repoCorpusName'))}\" criado{'s' if request.values.get('criarRamo') else ''} com sucesso! {textInterrogatorio if INTERROGATORIO else ''}Para prosseguir com o julgamento, treine um modelo a partir desse corpus clicando no menu lateral \"Treinar um modelo\" ou envie uma segunda versão desse corpus."
			else:
				alert = f"Corpus com o nome '{removerAcento(request.values.get('repoCorpusName'))}' já existe."
		else:
			raise Exception("Only available on Linux.")

	return render_template(
		'upload.html',
		alert=alert,
		success=success,
		formDB=formDB()
	)


@app.route('/api/getCatSents', methods="POST".split("|"))
def getCatSents():
	html = f'<h3>{request.values.get("tipo")}</h3>'
	sentences = categoryAccuracy(conllu(request.values.get('c')).findFirst(), conllu(request.values.get('c')).findSecond(), request.values.get('c'), request.values.get('coluna'))['UAS'][request.values.get('deprel')][request.values.get('tipo')][1]
	corpusFirst = allCorpora.corpora[conllu(request.values.get('c')).first()]
	corpusSecond = allCorpora.corpora[conllu(request.values.get('c')).second()]
	for i, sentence in enumerate(sentences):
		html += f'<div class="panel panel-default"><div class="panel-body">{i+1} / {len(sentences)}</div>' + render_template(
			'sentence.html',
			first=corpusFirst.sentences[sentence[0]],
			second=corpusSecond.sentences[sentence[0]],
			c=request.values.get('c'),
			bold={'word': corpusFirst.sentences[sentence[0]].tokens[sentence[1]].word, 'color': 'black', 'id': corpusFirst.sentences[sentence[0]].tokens[sentence[1]].id},
			secBold={'word': corpusFirst.sentences[sentence[0]].tokens[sentence[1]].head_token.word, 'color': 'green', 'id': corpusFirst.sentences[sentence[0]].tokens[sentence[1]].head_token.id},
			thirdBold={'word': corpusSecond.sentences[sentence[0]].tokens[sentence[1]].head_token.word, 'color': 'red', 'id': corpusSecond.sentences[sentence[0]].tokens[sentence[1]].head_token.id},
			col=request.values.get('coluna').lower(),
			boldCol=f'{request.values.get("coluna").lower()}<coluna>{sentence[1]}',
			t=sentence[1],
			divergence={
				'second': {'category': corpusSecond.sentences[sentence[0]].tokens[sentence[1]].__dict__[request.values.get('coluna').lower()], 'head': {'id': corpusSecond.sentences[sentence[0]].tokens[sentence[1]].head_token.id, 'word': corpusSecond.sentences[sentence[0]].tokens[sentence[1]].head_token.word}},
				'first': {'category': corpusFirst.sentences[sentence[0]].tokens[sentence[1]].__dict__[request.values.get('coluna').lower()], 'head': {'id': corpusFirst.sentences[sentence[0]].tokens[sentence[1]].head_token.id, 'word': corpusFirst.sentences[sentence[0]].tokens[sentence[1]].head_token.word}},
			},
		) + '</div>'

	return jsonify({
		'html': html,
		'success': True,
	})

@app.route('/api/sendAnnotation', methods="POST".split("|"))
def sendAnnotation():
	firstAndsecond = int(request.values.get('firstAndsecond'))
	change = False
	attention = ""
	if any('<coluna>' in data and request.values.get(data) for data in request.values):
		sent_id = request.values.get('sent_id')
		arquivo = conllu(request.values.get('c')).findFirst() if request.values.get('ud') == 'ud1' else conllu(request.values.get('c')).findSecond()
		if firstAndsecond:
			arquivosecond = conllu(request.values.get('c')).findSecond()
		
		corpus = estrutura_ud.Corpus(recursivo=False, sent_id=request.values.get('sent_id'))
		corpus.load(arquivo)

		if firstAndsecond:
			corpusSecond = estrutura_ud.Corpus(recursivo=False, sent_id=request.values.get('sent_id'))
			corpusSecond.load(arquivosecond)

		for data in request.values:
			# Comentei as referências a headToken, pois dizem respeito à função "quickSendAnnotation", que copia a anotação do corpus 2 para o 1, mas só quero modificar o valor da coluna, não o dephead
			if '<coluna>' in data and request.values.get(data):
				token = int(data.split('<coluna>')[1])
				coluna = data.split('<coluna>')[0] if not re.search(r'^\d+$', data.split('<coluna>')[0], flags=re.MULTILINE) else idx_to_col.get(int(data.split('<coluna>')[0]), "col%s" % (int(data.split("<coluna>")[0])+1))
				valor = html.unescape(request.values.get(data).replace("<br>", "").strip()).replace("<br>", "").strip()
				#if request.values.get("headToken"):
					#headTokenNum = request.values.get("headToken") if request.values.get("headToken") != "_" else "0"
				if corpus.sentences[sent_id].tokens[token].__dict__[coluna] != valor:
					corpus.sentences[sent_id].tokens[token].__dict__[coluna] = valor
					#if request.values.get('headToken'):
						#corpus.sentences[sent_id].tokens[token].dephead = headTokenNum
					change = True
					allCorpora.corpora[conllu(request.values.get("c")).first()].sentences[sent_id].tokens[token].__dict__[coluna] = valor
				
				if firstAndsecond:
					if corpusSecond.sentences[sent_id].tokens[token].__dict__[coluna] != valor:
						corpusSecond.sentences[sent_id].tokens[token].__dict__[coluna] = valor
						#if request.values.get('headToken'):
							#corpus.sentences[sent_id].tokens[token].dephead = headTokenNum
						change = True
						allCorpora.corpora[conllu(request.values.get("c")).second()].sentences[sent_id].tokens[token].__dict__[coluna] = valor

		attention = []
		if change:
			corpus.save(arquivo)
			if firstAndsecond:
				corpusSecond.save(arquivosecond)
			errors = validar_UD.validate(corpus, errorList=VALIDAR_UD, noMissingToken=True, sent_id=request.values.get('sent_id'))
			if errors:
				for error in errors:
					if error.strip():
						attention += [f'<div class="alert alert-warning translateHtml" role="alert">Atenção: {error}</div><ul>']
						for value in errors[error]:
							if value['sentence']:
								attention += ["<li>" + utils.cleanEstruturaUD(value['sentence'].tokens[value['t']].id) + " / " + utils.cleanEstruturaUD(value['sentence'].tokens[value['t']].word) + " / " + utils.cleanEstruturaUD(value['sentence'].tokens[value['t']].__dict__[value['attribute']]) + "</li>"]
						attention += ["</ul>"]

		del corpus
		if "corpusSecond" in globals(): del corpusSecond
		attention = "\n".join(attention)

	return jsonify({
		'change': change,
		'data': prettyDate(datetime.datetime.now()).prettyDateDMAH(),
		'attention': attention,
		'success': True,
	})


@app.route("/log")
def log(success=False):
	if not os.path.isfile(conllu(request.args.get('c')).findInProgress()) and os.path.isfile(f"{UPLOAD_FOLDER}/{conllu(request.args.get('c')).naked}_success"):
		inProgress = f"{UPLOAD_FOLDER}/{conllu(request.args.get('c')).naked}_success"
		success = True
	else:
		inProgress = conllu(request.args.get('c')).findInProgress()
	with open(inProgress, 'r') as f:
		log = f.read()
		
	return render_template(
		'log.html',
		log=log, 
		corpus=request.args.get('c'), 
		success=success,
		terminated=request.args.get('terminated') or ''
	)


@app.route("/api/getAnnotation", methods="POST".split("|"))
def getAnnotation():
	html1, html2 = "", ""

	if request.values.get('ud') == 'ud1':
		ud1 = estrutura_ud.Corpus(recursivo=False, sent_id=request.values.get('sent_id'))
		ud1.load(conllu(request.values.get('c')).findFirst())
		bold = request.values.get('bold') or ""
		annotationUd1 = escape(ud1.sentences.get(request.values.get('sent_id')).tokens_to_str())

		html1 = "<table id='t01' style='margin:auto; cursor:pointer; margin-bottom:30px'>"
		for t, linha in enumerate(annotationUd1.splitlines()):
			html1 += "<tr class='bold'>" if bold and t == int(bold) else "<tr>"
			for col, coluna in enumerate(linha.split("\t")):
				if col == 0: drag = 'id notPipe '
				elif col == 6: drag = 'drag notPipe '
				elif col in [3, 7] or coluna == "_": drag = "notPipe "
				else: drag = ""
				html1 += '<td contenteditable=true class="{drag}valor"><input type=hidden name="{col}<coluna>{t}">{coluna}</td>'.format(col=col, t=t, coluna=coluna, drag=drag)
			html1 += "</tr>"
		html1 += "</table>"

	elif request.values.get('ud') == 'ud2':
		ud2 = estrutura_ud.Corpus(recursivo=False, sent_id=request.values.get('sent_id'))
		ud2.load(conllu(request.values.get('c')).findSecond())
		bold = request.values.get('bold') or ""
		annotationUd2 = escape(ud2.sentences.get(request.values.get('sent_id')).tokens_to_str())

		html2 = "<table id='t01' style='margin:auto; cursor:pointer; margin-bottom:30px;'>"
		for t, linha in enumerate(annotationUd2.splitlines()):
			html2 += "<tr class='bold'>" if bold and t == int(bold) else "<tr>"
			for col, coluna in enumerate(linha.split("\t")):
				if col == 0: drag = 'id'
				elif col == 6: drag = 'drag'
				else: drag = ""
				html2 += '<td contenteditable=true class="{drag} valor"><input type=hidden name="{col}<coluna>{t}">{coluna}</td>'.format(col=col, t=t, coluna=coluna, drag=drag)
			html2 += "</tr>"
		html2 += "</table>"
	
	if 'ud1' in globals():
		del ud1

	if 'ud2' in globals():
		del ud2
		
	return jsonify({
		'annotationUd1': html1,
		'annotationUd2': html2,
		'success': True,
	})

@app.route("/git-update")
def gitUpdate():
	os.system(f"cd {JULGAMENTO_FOLDER}; git pull")
	print("ok")

@app.route("/corpus")
def corpus():
	if request.args.get('c'):
		loadCorpus(conllu(request.args.get('c')).naked)

	if not request.args.get('c'):
		return render_template(
			'corpus.html',
			corpora = checkCorpora()
		)

	elif request.args.get('mod'):
		return render_template(
			'mod.html',
			antes=request.args.get('antes'),
			depois=request.args.get('depois'),
			mod=request.args.get('mod'),
			c=request.args.get("c"),
			sentences=modificacoesCorpora.modificacoes[request.args.get("c")][request.args.get('mod')][request.args.get('antes') + "<depois>" + request.args.get('depois')],
		)
	
	elif request.args.get('ud1') and request.args.get('ud2') and request.args.get('col'):
		return render_template(
			'matriz.html',
			ud1=request.args.get('ud1'),
			ud2=request.args.get('ud2'),
			c=request.args.get('c'),
			col=request.args.get('col'),
			sentences=getMatrixSentences(request.args.get('c'), request.args.get('ud1'), request.args.get('ud2'), request.args.get('col'))
		)

	elif request.args.get('DEPREL'):
		return render_template(
			'catAccuracy.html',
			c=request.values.get('c'),
			conteudo=categoryAccuracy(conllu(request.values.get('c')).findFirst(), conllu(request.values.get('c')).findSecond(), request.values.get('c'), 'DEPREL')['UAS'][request.args.get('DEPREL')],
			deprel=request.args.get('DEPREL'),
			coluna='DEPREL',
		)

	elif request.args.get('UPOS'):
		return render_template(
			'catAccuracy.html',
			c=request.values.get('c'),
			conteudo=categoryAccuracy(conllu(request.values.get('c')).findFirst(), conllu(request.values.get('c')).findSecond(), request.values.get('c'), 'UPOS')['UAS'][request.args.get('UPOS')],
			deprel=request.args.get('UPOS'),
			coluna='UPOS',
		)

	elif request.args.get("action") and request.args.get("action") == "destroy":
		if conllu(request.args.get("c")).first() in allCorpora.corpora:
			del allCorpora.corpora[conllu(request.args.get("c")).first()]
		if conllu(request.args.get("c")).second() in allCorpora.corpora:
			del allCorpora.corpora[conllu(request.args.get("c")).second()]
		if conllu(request.args.get("c")).original() in allCorpora.corpora:
			del allCorpora.corpora[conllu(request.args.get("c")).original()]
		return redirect('/corpus')
	
	else:
		return render_template(
			'tables.html',
			c = request.args.get('c'),
			sobre = db.session.query(models.Corpus).get(request.args.get('c')).about if db.session.query(models.Corpus).get(request.args.get('c')) else "Sem informação",
			pagina = "tables",
			interrogatorio = INTERROGATORIO,
		)

@app.route("/")
def index():
	return redirect('/corpus')

import models
from importar import *
from config import *

app.before_first_request(checkCorpora)

filter_sentences = '''
<button type="button" title="Remover sentenças dessa página" class="filterSentences translateTitle btn btn-default"><i class="fa fa-filter"></i> <span class="translateHtml">Filtrar sentenças</span></button>
<br><br>
<div class="form-group panel panel-default panel-body col-lg-4 filterSentencesDiv" style="display:none;">
    <label for="filterSentencesInput" class="translateTitle translateHtml" title="Utilize expressão regular">Identificador das sentenças</label>
    <input type="text" class="form-control" id="filterSentencesInput" >
    <br>
    <button type="submit" class="filterSentencesButton translateHtml btn btn-primary mb-2">Filtrar</button>
</div>'''

app.jinja_env.filters['resub'] = resub
app.jinja_env.filters['paint_text'] = paint_text
app.jinja_env.filters['sortLambda'] = sortLambda
app.jinja_env.globals.update(re=re)
app.jinja_env.globals.update(conllu=conllu)
app.jinja_env.globals.update(comcorhd=globals()['COMCORHD'])
app.jinja_env.globals.update(upload_folder=UPLOAD_FOLDER)
app.jinja_env.globals.update(checkCorpora=checkCorpora)
app.jinja_env.globals.update(checkRepo=checkRepo)
app.jinja_env.globals.update(prettyDate=prettyDate)
app.jinja_env.globals.update(findCorpora=findCorpora)
app.jinja_env.globals.update(allCorpora=allCorpora)
app.jinja_env.globals.update(isinstance=isinstance)
app.jinja_env.globals.update(filter_sentences=filter_sentences)

if __name__ == "__main__":
	app.run(threaded=False, port="5050", processes=1)
