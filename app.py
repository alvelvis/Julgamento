import config, sys, re, estrutura_ud, html, os, subprocess, time, shutil, pickle, psutil, threading
import pandas as pd
from flask import Flask, redirect, url_for, session, request, make_response, render_template, jsonify
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized, oauth_before_login
from flask_sqlalchemy import SQLAlchemy
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError
from flask_login import logout_user, LoginManager, current_user, login_required
from jinja2 import Template, escape, Markup, Environment
from interrogar_UD import getDistribution
import datetime
import validar_UD, functions
from functions import cleanEstruturaUD
from flask_executor import Executor
from subprocess import Popen
import json

app = Flask(__name__)
app.config.from_object('config')
executor = Executor(app)
db = SQLAlchemy(app)
blueprint = make_google_blueprint(
    client_id=app.config.get('GOOGLE_CLIENT_ID'),
    client_secret=app.config.get('GOOGLE_SECRET_KEY'),
	scope = [
	"openid",
	"https://www.googleapis.com/auth/userinfo.email",
	"https://www.googleapis.com/auth/userinfo.profile"
	]
)
app.register_blueprint(blueprint, url_prefix="/login")
login_manager = LoginManager(app)

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
	if GOOGLE_LOGIN and not google.authorized:
		return redirect(url_for("google.login") + "?next_url=" + request.full_path)

	dist = getDistribution(allCorpora.corpora[conllu(request.values.get("c")).golden()], parametros='word = ".*" and sent_id = "' + request.values.get("sent_id") + '"', coluna="children")

	return jsonify({
		'html': "- " + "<br>- ".join(dist["all_children"]),
		'success': True
	})

@app.route("/api/changeAbout", methods="POST".split("|"))
def changeAbout():
	if not google.authorized and GOOGLE_LOGIN:
		return redirect(url_for("google.login"))
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
	if not google.authorized and GOOGLE_LOGIN:
		return redirect(url_for("google.login"))
	#allCorpora.corpora.pop(conllu(request.values.get("c")).golden(), None)
	#allCorpora.corpora.pop(conllu(request.values.get("c")).system(), None)
	#loadCorpus.submit(request.values.get("c"))
	if request.values.get("c") in modificacoesCorpora.modificacoes:
		modificacoesCorpora.modificacoes.pop(request.values.get("c"))
	allCorpora.corpora.pop(conllu(request.values.get("c")).golden())
	#allCorpora.corpora[] = ""
	if conllu(request.values.get("c")).system() in allCorpora.corpora:
		allCorpora.corpora.pop(conllu(request.values.get("c")).system())
	checkCorpora()
	if os.path.isdir(UPLOAD_FOLDER + "/CM-" + request.values.get("c")):
		shutil.rmtree(UPLOAD_FOLDER + "/CM-" + request.values.get("c") + "/", ignore_errors=True)
	if os.path.isfile(conllu(request.values.get("c")).findErrorsValidarUD()):
		os.remove(conllu(request.values.get("c")).findErrorsValidarUD())
	if os.path.isfile(conllu(request.values.get("c")).findErrors()):
		os.remove(conllu(request.values.get("c")).findErrors())
	if os.path.isfile(conllu(request.values.get("c")).findErrors() + "_html"):
		os.remove(conllu(request.values.get("c")).findErrors() + "_html")
	return jsonify({'success': True})

@app.route("/api/getCommits", methods="POST".split("|"))
def getCommits():
	if not google.authorized and GOOGLE_LOGIN:
		return redirect(url_for("google.login"))

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

@app.route("/api/cristianMarneffe", methods="POST".split("|"))
def cristianMarneffe():
	if not google.authorized and GOOGLE_LOGIN:
		return redirect(url_for("google.login"))

	if not os.path.isfile(UPLOAD_FOLDER + f"/CM-{request.values.get('c')}/results_{request.values.get('tipo')}.json"):
		os.system(JULGAMENTO_FOLDER + "/.julgamento/bin/python3 {}/Cristian-Marneffe.py {} {}".format(
			JULGAMENTO_FOLDER,
			conllu(request.values.get("c")).findGolden(), 
			request.values.get("tipo"),
			))

	with open(UPLOAD_FOLDER + f"/CM-{request.values.get('c')}/results_{request.values.get('tipo')}.json") as f:
		results = json.load(f)

	html = ""
	if not results:
		html += f"<div class='alert alert-warning translateHtml' role='alert'>Não foram encontradas inconsistências do tipo Cristian-Marneffe.</div>"
	else:
		for i, exemplo in enumerate(results):
			html += f"<div class='alert alert-warning' role='alert'>{i+1} / {len(results)} - {exemplo['exemplo']}</div>"
			for k, frase in enumerate(exemplo['frases']):
				html += f'<div class="panel panel-default"><div class="panel-body">{ k+1 } / { len(exemplo["frases"]) }</div>'
				html += render_template(
						'sentence.html',
						golden=allCorpora.corpora[conllu(request.values.get("c")).golden()].sentences[frase["sent_id"]],
						c=request.values.get("c"),
						t=allCorpora.corpora[conllu(request.values.get("c")).golden()].sentences[frase["sent_id"]].map_token_id[str(frase["id1"])],
						bold={'word': frase['WORD1'], 'color': 'red'},
						rel=frase["rel"],
						secBold={'word': frase['WORD2'], 'color': 'blue'},
						goldenAndSystem=True if conllu(request.values.get("c")).system() in allCorpora.corpora else False
						) + "</div>"
	
	return jsonify({
		'html': html,
		'success': True,
		'c': request.values.get('c'),
	}) 

@app.route('/api/getErrors', methods="POST".split("|"))
def getErrors():
	if not google.authorized and GOOGLE_LOGIN:
		return redirect(url_for("google.login"))
		
	html = renderErrors(c=request.values.get("c"), exc=request.values.get('exceptions').split("|") if request.values.get('exceptions') else "", fromZero=True)
	return jsonify({
		'html': html,
		'success': True,
		'c': request.values.get('c'),
	})

@app.route('/api/getErrorsValidarUD', methods="POST".split("|"))
def getErrorsValidarUD():
	if not google.authorized and GOOGLE_LOGIN:
		return redirect(url_for("google.login"))
	
	html = ""
	if os.path.isfile(conllu(request.values.get("c")).findErrorsValidarUD()):
		with open(conllu(request.values.get("c")).findErrorsValidarUD(), "rb") as f:
			errors = pickle.loads(f.read())
	else:
		errors = validar_UD.validate(allCorpora.corpora[conllu(request.values.get("c")).golden()], errorList=VALIDAR_UD, noMissingToken=True)
		with open(conllu(request.values.get("c")).findErrorsValidarUD(), "wb") as f:
			f.write(pickle.dumps(errors))

	if not errors:
		html = "<div class='alert alert-warning translateHtml' role='alert'>Não foram encontrados erros de validação.</div>"
	for k, error in enumerate(errors):
		html += f"<div class='alert alert-warning' role='alert'>{k+1} / {len(errors)} - {error}</div>"
		for i, value in enumerate(errors[error]):
			if value['sentence']:
				html += f'<div class="panel panel-default"><div class="panel-body">{ i+1 } / { len(errors[error]) }</div>' + \
					render_template(
						'sentence.html',
						golden=value['sentence'],
						c=request.values.get("c"),
						t=value['t'],
						bold={'word': value['sentence'].tokens[value['t']].word, 'color': 'black'},
						rel=value['sentence'].tokens[value['t']].col[value['attribute']],
						goldenAndSystem=True if conllu(request.values.get("c")).system() in allCorpora.corpora else False,
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
	if not google.authorized and GOOGLE_LOGIN:
		return redirect(url_for("google.login"))
	return jsonify({
		'html': findCorpora(filtro=request.values.get('filtro'), tipo=request.values.get('tipo')),
		'success': True,
	})

@app.route('/api/deleteGolden', methods="POST|GET".split("|"))
def deleteGolden():
	if not google.authorized and GOOGLE_LOGIN:
		return redirect(url_for("google.login"))
	caracteristicasCorpus(request.values.get("c"))
	os.remove(conllu(request.values.get("c")).findGolden())
	if os.path.isfile(conllu(request.values.get("c")).findOriginal()):
		os.remove(conllu(request.values.get("c")).findOriginal())
	return render_template(
		'upload.html',
		success="Corpus golden \"" + request.values.get("c") + "\" deletado com sucesso!",
		user=google.get('/oauth2/v2/userinfo').json(),
	)


@app.route('/cancelTrain', methods="GET".split("|"))
def cancelTrain():
	if not google.authorized and GOOGLE_LOGIN:
		return redirect(url_for("google.login"))
	if not request.args.get('delete'):
		os.system('killall udpipe-1.2.0')
		return redirect("/log?c=" + request.args.get('c'))
	else:
		caracteristicasCorpus(request.values.get("c"))
		if request.args.get('golden') == 'true':
			if os.path.isfile(conllu(request.args.get("c")).findGolden()):
				os.remove(conllu(request.args.get("c")).findGolden())
			if os.path.isfile(conllu(request.args.get("c")).findOriginal()):
				os.remove(conllu(request.args.get("c")).findOriginal())
			if conllu(request.values.get("c")).original in allCorpora.corpora:
				allCorpora.corpora.pop(conllu(request.values.get("c")).original)
		if os.path.isfile(conllu(request.args.get("c")).findInProgress()):
			os.remove(conllu(request.args.get("c")).findInProgress())
		if os.path.isfile(conllu(request.args.get("c")).findSystem()):
			os.remove(conllu(request.args.get("c")).findSystem())
		corpus = db.session.query(models.Corpus).get(conllu(request.args.get('c')).naked)
		if conllu(request.values.get("c")).golden() in allCorpora.corpora:
			allCorpora.corpora.pop(conllu(request.values.get("c")).golden())
		if conllu(request.values.get("c")).system() in allCorpora.corpora:
			allCorpora.corpora.pop(conllu(request.values.get("c")).system())
		if corpus:
			db.session.delete(corpus)
			db.session.commit()
		if not request.args.get('callback'):
			return redirect("/")
		else:
			return redirect("/" + request.args.get('callback'))

@app.route('/api/getTables', methods="POST".split("|"))
def getTables():
	if not google.authorized and GOOGLE_LOGIN:
		return redirect(url_for('google.login'))
	table = request.values.get('table')

	if table == "caracteristicas":
		return jsonify({
			'html': caracteristicasCorpus(request.values.get('ud1'), request.values.get('ud2') if request.values.get('ud2') else ""),
			'success': True
		})

	elif table == 'metrics':
		return jsonify({
			'html': '<h3 class="translateHtml">Métricas do conll18_ud_eval.py</h3>' + metrics(request.values.get('ud1'), request.values.get('ud2')),
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
			<div id="POSAccuracy" class="col-lg-4">
				<div class=" panel panel-default panel-body">
					<h3 class="translateHtml">Acurácia por UPOS</h3>
					{categoryAccuracy(request.values.get('ud1'), request.values.get('ud2'), request.values.get('c'), 'UPOS')['tables']}
				</div>
			</div>
			<div id="DEPRELAccuracy" class="col-lg-8">
				<div class=" panel panel-default panel-body">
					<h3 class="translateHtml">Acurácia por DEPREL</h3>
					{categoryAccuracy(request.values.get('ud1'), request.values.get('ud2'), request.values.get('c'), 'DEPREL')['tables']}
				</div>
			</div>
			''',
			'success': True
		})

	elif table == 'POSMatrix':
		ud1Estruturado = allCorpora.corpora.get(conllu(request.values.get('ud1')).golden())
		ud2Estruturado = allCorpora.corpora.get(conllu(request.values.get('ud2')).system())
		listaPOS = confusao.get_list(ud1Estruturado, ud2Estruturado, 4)
		listaPOS1 = listaPOS['matriz_1']
		listaPOS2 = listaPOS['matriz_2']
		pd.options.display.max_rows = None
		pd.options.display.max_columns = None
		pd.set_option('display.expand_frame_repr', False)
		return jsonify({
			'html': '<h3 class="translateHtml">Matriz de confusão de UPOS</h3>' + matrix(str(pd.crosstab(pd.Series(listaPOS1), pd.Series(listaPOS2), rownames=['golden'], colnames=['sistema'], margins=True)), request.values.get('c'), kind="UPOS"),
			'success': True,
		})

	elif table == 'DEPRELMatrix':
		ud1Estruturado = allCorpora.corpora.get(conllu(request.values.get('ud1')).golden())
		ud2Estruturado = allCorpora.corpora.get(conllu(request.values.get('ud2')).system())
		listaDep = confusao.get_list(ud1Estruturado, ud2Estruturado, 8)
		listaDep1 = listaDep['matriz_1']
		listaDep2 = listaDep['matriz_2']
		pd.options.display.max_rows = None
		pd.options.display.max_columns = None
		pd.set_option('display.expand_frame_repr', False)
		return jsonify({
			'html': '<h3 class="translateHtml">Matriz de confusão de DEPREL</h3>' + matrix(str(pd.crosstab(pd.Series(listaDep1), pd.Series(listaDep2), rownames=['golden'], colnames=['sistema'], margins=True)), request.values.get('c'), kind="DEPREL"),
			'success': True,
		})

	elif table == 'errorLog':
		return ""

	elif table == 'errorValidarUD':
		return ""

	elif table == 'cristianMarneffe':
		return ""

@app.route('/upload', methods="GET|POST".split("|"))
def upload(alert="", success=""):
	if not google.authorized and GOOGLE_LOGIN:
		return redirect(url_for('google.login'))
	if request.method == "GET":
		return render_template(
			'upload.html',
			user=google.get('/oauth2/v2/userinfo').json(),
			formDB=formDB()
		)

	elif request.method == "POST" and 'goldenFile' in request.files:
		goldenFile = request.files.get('goldenFile')
		if goldenFile.filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS:			
			goldenFileName = removerAcento(conllu(request.values.get('goldenName')).golden())
			if (INTERROGATORIO and not os.path.isfile(COMCORHD_FOLDER + '/' + goldenFileName)) or (not INTERROGATORIO and not os.path.isfile(UPLOAD_FOLDER + '/' + goldenFileName)):
				goldenFile.save(COMCORHD_FOLDER + '/' + goldenFileName) if INTERROGATORIO else goldenFile.save(UPLOAD_FOLDER + '/' + goldenFileName)
				shutil.copyfile(conllu(goldenFileName).findGolden(), conllu(goldenFileName).findOriginal())
				textInterrogatorio = "(1) Realize buscas e edições no corpus pelo <a href='http://github.com/alvelvis/Interrogat-rio'>Interrogatório</a>, ou, (2) "
				success = f'"{goldenFileName}" enviado com sucesso! {textInterrogatorio if INTERROGATORIO else ""}Julgue-o na <a href="/corpus">página inicial</a>.'
			else:
				alert = "Arquivo golden já existe na pasta."
		else:
			alert = 'Extensão deve estar entre "' + ",".join(ALLOWED_EXTENSIONS) + '"'

	elif request.method == "POST" and 'systemFile' in request.files:
		goldenFile = request.values.get('sysGoldenFile')
		systemFile = request.files.get('systemFile')
		if systemFile.filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS:			
			systemFileName = conllu(goldenFile).system()
			systemFile.save(UPLOAD_FOLDER + '/' + systemFileName)
			if not os.path.isfile(conllu(systemFileName).findOriginal()):
				shutil.copyfile(conllu(systemFileName).findGolden(), conllu(systemFileName).findOriginal())
			corpusGolden = estrutura_ud.Corpus(recursivo=False)
			corpusSystem = estrutura_ud.Corpus(recursivo=False)
			corpusGolden.load(conllu(goldenFile).findGolden())
			corpusSystem.load(conllu(goldenFile).findSystem())
			if len(corpusGolden.sentences) != len(corpusSystem.sentences):
				alert = "Arquivo sistema não tem o mesmo número de sentenças do arquivo golden."
				os.remove(conllu(goldenFile).findSystem())
			else:
				success = f'"{systemFileName}" enviado com sucesso! Julgue o corpus na <a href="/corpus">página inicial</a>.'
				corpusdb = db.session.query(models.Corpus).get(conllu(goldenFile).naked)
				if corpusdb:
					db.session.remove(corpusdb)
					db.session.commit()
				novoCorpus = models.Corpus(
					name=conllu(goldenFile).naked,
					date=str(datetime.datetime.now()),
					sentences=0,
					about=request.values.get('sysAbout') if request.values.get('sysAbout') else ">",
					partitions="",
					author=google.get('/oauth2/v2/userinfo').json()['email'] if GOOGLE_LOGIN else "",
					goldenAlias='Golden',
					systemAlias='Sistema'
				)
				db.session.add(novoCorpus)
				db.session.commit()
			#loadCorpus.submit(goldenFile)

		else:
			alert = 'Extensão deve estar entre "' + ",".join(ALLOWED_EXTENSIONS) + '"'

	elif request.method == 'POST' and 'trainFile' in request.values:
		corpusTemporario = False
		if os.path.isfile(COMCORHD_FOLDER + "/" + conllu(request.values.get('trainFile')).golden()):
			os.system(f'cp {COMCORHD_FOLDER + "/" + conllu(request.values.get("trainFile")).golden()} {UPLOAD_FOLDER}')
			corpusTemporario = f"; rm {UPLOAD_FOLDER}/{conllu(request.values.get('trainFile')).golden()} &"
		if not request.values.get('crossvalidation'):
			Popen(f"cd {UPLOAD_FOLDER}; cp {conllu(request.values.get('trainFile')).golden()} {conllu(request.values.get('trainFile')).naked + '_test'}.conllu; sh udpipe.sh {conllu(request.values.get('trainFile')).naked + '_test'} {request.values.get('partitions')} 2>&1 | tee -a {conllu(request.values.get('trainFile')).naked + '_test'}_inProgress {corpusTemporario if corpusTemporario else '&'}", shell=True)
			nomeConllu = conllu(request.values.get('trainFile')).naked + "_test"
		else:
			Popen(f"cd {UPLOAD_FOLDER}; sh crossvalidation.sh {request.values.get('trainFile')} {request.values.get('partitions')} 2>&1 | tee -a {request.values.get('trainFile')}_inProgress {corpusTemporario if corpusTemporario else '&'}", shell=True)
			nomeConllu = conllu(request.values.get('trainFile')).naked
		novoCorpus = models.Corpus(
			name=nomeConllu,
			date=str(datetime.datetime.now()),
			sentences=0,
			about=request.values.get('about') if request.values.get('about') else ">",
			partitions=request.values.get('partitions'),
			author=google.get('/oauth2/v2/userinfo').json()['email'] if GOOGLE_LOGIN else "",
			goldenAlias='Golden',
			systemAlias='Sistema'
		)
		db.session.add(novoCorpus)
		db.session.commit()
		success = "Um modelo está sendo treinado a partir do corpus \"" + nomeConllu + "\". Acompanhe o status do treinamento na <a href='/'>página inicial do Julgamento.</a>"

	elif request.method == 'POST' and 'repoName' in request.values:
		sh = f"cd {UPLOAD_FOLDER}/repositories/{request.values.get('repoName')}; \
				git pull; \
					git checkout {request.values.get('repoCommit').split(' | commit ')[1]}; \
						cat documents/*.conllu > {conllu(removerAcento(request.values.get('repoCorpusName'))).findGolden()}; \
							cat documents/*.conllu > {conllu(removerAcento(request.values.get('repoCorpusName'))).findOriginal()}"
		if request.values.get('criarRamo'):
			sh += f"; git checkout -b {removerAcento(request.values.get('repoCorpusName'))}; \
						git push --set-upstream origin {removerAcento(request.values.get('repoCorpusName'))}"

		if not os.path.isfile(f"{conllu(removerAcento(request.values.get('repoCorpusName'))).findGolden()}"):
			os.system(sh)
			textInterrogatorio = "(1) Realize buscas e edições no corpus pelo <a href='http://github.com/alvelvis/interrogat-rio'>Interrogatório</a>, ou, (2) "
			success = f"Corpus {'e ramo ' if request.values.get('criarRamo') else ''}\"{removerAcento(request.values.get('repoCorpusName'))}\" criado{'s' if request.values.get('criarRamo') else ''} com sucesso! {textInterrogatorio if INTERROGATORIO else ''}Para prosseguir com o julgamento, treine um modelo a partir desse corpus clicando no menu lateral \"Treinar um modelo\" ou envie um arquivo sistema equivalente ao corpus."
		else:
			alert = f"Corpus com o nome '{removerAcento(request.values.get('repoCorpusName'))}' já existe."

	return render_template(
		'upload.html',
		alert=alert,
		success=success,
		user=google.get('/oauth2/v2/userinfo').json(),
		formDB=formDB()
	)


@app.route('/api/getCatSents', methods="POST".split("|"))
def getCatSents():
	if not google.authorized and GOOGLE_LOGIN:
		return redirect(url_for("google.login"))

	html = f'<h3>{request.values.get("tipo")}</h3>'
	sentences = categoryAccuracy(conllu(request.values.get('c')).findGolden(), conllu(request.values.get('c')).findSystem(), request.values.get('c'), request.values.get('coluna'))['UAS'][request.values.get('deprel')][request.values.get('tipo')][1]
	corpusGolden = allCorpora.corpora[conllu(request.values.get('c')).golden()]
	corpusSystem = allCorpora.corpora[conllu(request.values.get('c')).system()]
	for i, sentence in enumerate(sentences):
		html += f'<div class="panel panel-default"><div class="panel-body">{i+1} / {len(sentences)}</div>' + render_template(
			'sentence.html',
			golden=corpusGolden.sentences[sentence[0]],
			system=corpusSystem.sentences[sentence[0]],
			c=request.values.get('c'),
			bold={'word': corpusGolden.sentences[sentence[0]].tokens[sentence[1]].word, 'color': 'black'},
			secBold={'word': corpusGolden.sentences[sentence[0]].tokens[sentence[1]].head_token.word, 'color': 'green'},
			thirdBold={'word': corpusSystem.sentences[sentence[0]].tokens[sentence[1]].head_token.word, 'color': 'red'},
			col=request.values.get('coluna').lower(),
			boldCol=f'{request.values.get("coluna").lower()}<coluna>{sentence[1]}',
			t=sentence[1],
			divergence={
				'system': {'category': corpusSystem.sentences[sentence[0]].tokens[sentence[1]].col[request.values.get('coluna').lower()], 'head': {'id': corpusSystem.sentences[sentence[0]].tokens[sentence[1]].head_token.id, 'word': corpusSystem.sentences[sentence[0]].tokens[sentence[1]].head_token.word}},
				'golden': {'category': corpusGolden.sentences[sentence[0]].tokens[sentence[1]].col[request.values.get('coluna').lower()], 'head': {'id': corpusGolden.sentences[sentence[0]].tokens[sentence[1]].head_token.id, 'word': corpusGolden.sentences[sentence[0]].tokens[sentence[1]].head_token.word}},
			},
		) + '</div>'

	return jsonify({
		'html': html,
		'success': True,
	})

@app.route('/api/sendAnnotation', methods="POST".split("|"))
def sendAnnotation():
	if not google.authorized and GOOGLE_LOGIN:
		return redirect(url_for('google.login'))

	goldenAndSystem = int(request.values.get('goldenAndSystem'))
	globals()["change"] = False
	attention = ""
	if any('<coluna>' in data and request.values.get(data) for data in request.values):
		sent_id = request.values.get('sent_id')
		arquivo = conllu(request.values.get('c')).findGolden() if request.values.get('ud') == 'ud1' else conllu(request.values.get('c')).findSystem()
		if goldenAndSystem:
			arquivoSystem = conllu(request.values.get('c')).findSystem()
		
		corpus = estrutura_ud.Corpus(recursivo=False, sent_id=request.values.get('sent_id'))
		corpus.load(arquivo)

		if goldenAndSystem:
			corpusSystem = estrutura_ud.Corpus(recursivo=False, sent_id=request.values.get('sent_id'))
			corpusSystem.load(arquivoSystem)

		for data in request.values:
			if '<coluna>' in data and request.values.get(data):
				token = int(data.split('<coluna>')[1])
				coluna = data.split('<coluna>')[0] if not re.search(r'^\d+$', data.split('<coluna>')[0], flags=re.MULTILINE) else dicionarioColunas[data.split('<coluna>')[0]]
				valor = html.unescape(request.values.get(data).replace("<br>", "").strip()).replace("<br>", "").strip()
				if request.values.get("headToken"):
					headTokenNum = request.values.get("headToken") if request.values.get("headToken") != "_" else "0"
				headToken = f'\ncorpus.sentences["{sent_id}"].tokens[{token}].dephead = "{headTokenNum}"\n' if request.values.get('headToken') else "\n"
				exec(f'if corpus.sentences["{sent_id}"].tokens[{token}].{coluna} != "{valor}":\n\tcorpus.sentences["{sent_id}"].tokens[{token}].{coluna} = "{valor}"{headToken}globals()["change"] = True\nglobals()["allCorpora"].corpora["{conllu(request.values.get("c")).golden()}"].sentences["{sent_id}"].tokens[{token}].{coluna} = "{valor}"')
				
				if goldenAndSystem:
					exec(f'if corpusSystem.sentences["{sent_id}"].tokens[{token}].{coluna} != "{valor}":\n\tcorpusSystem.sentences["{sent_id}"].tokens[{token}].{coluna} = "{valor}"{headToken}globals()["change"] = True\nglobals()["allCorpora"].corpora["{conllu(request.values.get("c")).system()}"].sentences["{sent_id}"].tokens[{token}].{coluna} = "{valor}"')

		attention = []
		if globals()["change"]:
			corpus.save(arquivo)
			if goldenAndSystem:
				corpusSystem.save(arquivoSystem)
			errors = validar_UD.validate(corpus, errorList=VALIDAR_UD, noMissingToken=True, sent_id=request.values.get('sent_id'))
			if errors:
				for error in errors:
					if error.strip():
						attention += [f'<div class="alert alert-warning translateHtml" role="alert">Atenção: {error}</div><ul>']
						for value in errors[error]:
							if value['sentence']:
								attention += ["<li>" + functions.cleanEstruturaUD(value['sentence'].tokens[value['t']].id) + " / " + functions.cleanEstruturaUD(value['sentence'].tokens[value['t']].word) + " / " + functions.cleanEstruturaUD(value['sentence'].tokens[value['t']].col[value['attribute']]) + "</li>"]
						attention += ["</ul>"]
			
		attention = "\n".join(attention)

	return jsonify({
		'change': globals()["change"],
		'data': prettyDate(datetime.datetime.now()).prettyDateDMAH(),
		'attention': attention,
		'success': True,
	})


@app.route("/log")
def log(success=False):
	if not google.authorized and GOOGLE_LOGIN:
		return redirect(url_for("google.login") + "?next_url=" + request.full_path)
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
		user=google.get('/oauth2/v2/userinfo').json(), 
		corpus=request.args.get('c'), 
		success=success,
		terminated=request.args.get('terminated') or ''
	)


@app.route("/api/getAnnotation", methods="POST".split("|"))
def getAnnotation():
	if not google.authorized and GOOGLE_LOGIN:
		return redirect(url_for('google.login'))

	html1, html2 = "", ""

	if request.values.get('ud') == 'ud1':
		ud1 = estrutura_ud.Corpus(recursivo=False, sent_id=request.values.get('sent_id'))
		ud1.load(conllu(request.values.get('c')).findGolden())
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
		ud2.load(conllu(request.values.get('c')).findSystem())
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

	return jsonify({
		'annotationUd1': html1,
		'annotationUd2': html2,
		'success': True,
	})


@app.route("/corpus")
def corpus():
	if GOOGLE_LOGIN and not google.authorized:
		return redirect(url_for("google.login") + "?next_url=" + request.full_path)

	resp = google.get('/oauth2/v2/userinfo')

	if not request.args.get('c'):
		return render_template(
			'corpus.html',
			user = resp.json(),
			corpora = checkCorpora()
		)

	elif request.args.get('mod'):
		return render_template(
			'mod.html',
			user=resp.json(),
			antes=request.args.get('antes'),
			depois=request.args.get('depois'),
			mod=request.args.get('mod'),
			c=request.args.get("c"),
			sentences=modificacoesCorpora.modificacoes[request.args.get("c")][request.args.get('mod')][request.args.get('antes') + "<depois>" + request.args.get('depois')],
		)
	
	elif request.args.get('ud1') and request.args.get('ud2') and request.args.get('col'):
		return render_template(
			'matriz.html',
			user=resp.json(),
			ud1=request.args.get('ud1'),
			ud2=request.args.get('ud2'),
			c=request.args.get('c'),
			col=request.args.get('col'),
			sentences=getMatrixSentences(request.args.get('c'), request.args.get('ud1'), request.args.get('ud2'), request.args.get('col'))
		)

	elif request.args.get('DEPREL'):
		return render_template(
			'catAccuracy.html',
			user=resp.json(),
			c=request.values.get('c'),
			conteudo=categoryAccuracy(conllu(request.values.get('c')).findGolden(), conllu(request.values.get('c')).findSystem(), request.values.get('c'), 'DEPREL')['UAS'][request.args.get('DEPREL')],
			deprel=request.args.get('DEPREL'),
			coluna='DEPREL',
		)

	elif request.args.get('UPOS'):
		return render_template(
			'catAccuracy.html',
			user=resp.json(),
			c=request.values.get('c'),
			conteudo=categoryAccuracy(conllu(request.values.get('c')).findGolden(), conllu(request.values.get('c')).findSystem(), request.values.get('c'), 'UPOS')['UAS'][request.args.get('UPOS')],
			deprel=request.args.get('UPOS'),
			coluna='UPOS',
		)
	
	else:
		return render_template(
			'tables.html',
			user = resp.json(),
			c = request.args.get('c'),
			sobre = db.session.query(models.Corpus).get(request.args.get('c')).about if db.session.query(models.Corpus).get(request.args.get('c')) else "Sem informação",
			pagina = "tables",
		)

@app.errorhandler(TokenExpiredError)
@app.errorhandler(KeyError)
def handle_error(e):
    session.clear()
    return redirect(url_for("google.login") + "?next_url=" + request.full_path)

@app.route("/logout")
def logout():
	if not google.authorized and GOOGLE_LOGIN:
		return redirect(url_for("google.login"))
	
	token = blueprint.token['access_token']
	logout_user()
	session.clear()
	google.post(
		"https://accounts.google.com/o/oauth2/revoke",
		params={"token": token},
		headers={"Content-Type": "application/x-www-form-urlencoded"}
	)
	del blueprint.token
	return redirect(url_for('google.login'))


@oauth_before_login.connect
def before_login(blueprint, url):
	session["next_url"] = request.full_path.split("next_url=")[1] if 'next_url=' in request.full_path else ''


@oauth_authorized.connect
def logged_in(blueprint, token):
	blueprint.token = token
	next_url = session["next_url"]
	resp = google.get("/oauth2/v2/userinfo")
	email = resp.json().get('email')
	if not email in ALLOWED_GOOGLE_EMAILS:
		next_link = "/corpus" if not next_url else next_url
		return redirect('/logout?next_url=' + next_link)
	else:
		return redirect(next_url or '/corpus')


@app.route("/")
def index():
	if not google.authorized and GOOGLE_LOGIN:
		return redirect(url_for('google.login'))
	else:
		return redirect('/corpus')

import models
from importar import *
from config import *

app.before_first_request(checkCorpora)

app.jinja_env.filters['resub'] = resub
app.jinja_env.filters['sortLambda'] = sortLambda
app.jinja_env.globals.update(re=re)
app.jinja_env.globals.update(conllu=conllu)
app.jinja_env.globals.update(comcorhd=globals()['INTERROGATORIO'])
app.jinja_env.globals.update(upload_folder=UPLOAD_FOLDER)
app.jinja_env.globals.update(checkCorpora=checkCorpora)
app.jinja_env.globals.update(checkRepo=checkRepo)
app.jinja_env.globals.update(prettyDate=prettyDate)
app.jinja_env.globals.update(listProcess=[x.name() for x in psutil.process_iter()])
app.jinja_env.globals.update(findCorpora=findCorpora)
app.jinja_env.globals.update(allCorpora=allCorpora)
app.jinja_env.globals.update(isinstance=isinstance)

if __name__ == "__main__":
	app.run(threaded=True, port="5050")
