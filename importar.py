from config import UPLOAD_FOLDER, COMCORHD_FOLDER, JULGAMENTO_FOLDER, REPOSITORIES, VALIDATE_UD, VALIDATE_LANG, GOOGLE_LOGIN, VALIDAR_UD
from flask import render_template, request
import pandas as pd
import os, estrutura_ud, estrutura_dados, confusao, re, time, datetime, validar_UD
import models, pickle
from app import db, app, executor, allCorpora, modificacoesCorpora
from localtime import localtime
import sys, shutil

MAX_FILE_SIZE = 50

INTERROGATORIO = False
if os.path.isdir(JULGAMENTO_FOLDER.rsplit('/', 1)[0] + "/Interrogat-rio"):
    globals()['INTERROGATORIO'] = True
else:
    globals()['INTERROGATORIO'] = False

def checkRepo(repositorio="", branch=""):
    if not os.path.isdir(UPLOAD_FOLDER + "/" + 'repositories'):
        os.mkdir(UPLOAD_FOLDER + "/" + 'repositories')
    
    for repo in REPOSITORIES:
        if '/' in repo:
            if not os.path.isdir(UPLOAD_FOLDER + '/repositories/' + repo.rsplit("/", 1)[1].split(".git")[0]):
                if os.system(f'cd {UPLOAD_FOLDER}/repositories; git clone {repo}'):
                    pass

    listRepo = []
    for item in os.listdir(UPLOAD_FOLDER + "/" + 'repositories'):
        if os.path.isdir(UPLOAD_FOLDER + "/" + 'repositories' + "/" + item):
            listRepo.append(item)

    branches = []
    microBranches = []
    if repositorio:
        if os.system(f"cd {UPLOAD_FOLDER}/repositories/{repositorio}; git stash; git pull; git ls-remote > branches.txt"):
            pass
        with open(f"{UPLOAD_FOLDER}/repositories/{repositorio}/branches.txt", 'r') as f:
            texto = f.read().splitlines()
        for branchFor in texto:
            if branchFor and '/heads/' in branchFor:
                microBranches.append("<option>" + branchFor.split('/heads/')[1].strip() + "</option>")
        branches = ['<select name="branch" id="branch" class="form-control selectpicker branch" data-live-search="true" required>'] + ['<option class="translateHtml" disabled selected value> -- escolha um ramo -- </option>'] + sorted(microBranches) + ["</select>"]

    
    commits = []
    if repositorio and branch:
        if os.system(f"cd {UPLOAD_FOLDER}/repositories/{repositorio}; git stash; git pull; git checkout {branch}; git pull; git log > commits.txt"):
            pass
        with open(f"{UPLOAD_FOLDER}/repositories/{repositorio}/commits.txt", 'r') as f:
            texto = re.split(r"(^|\n\n)commit ", f.read())
        commits.append('<select name="repoCommit" id="repoCommit" class="form-control selectpicker repoCommit" data-live-search="true" required>')
        for commitFor in texto:
            if commitFor != "\n\n" and commitFor:
                commits.append("<option>" + commitFor.split("    ", 1)[1].split("\n")[0] + " | commit " + commitFor.split("\n")[0] + "</option>")
        commits.append("</select>")

    return {
        'repositories': listRepo,
        'commits': "\n".join(commits),
        'branches': "\n".join(branches),
    }


def renderErrors(c, texto="", exc=[], fromZero=False):
    if not os.path.isfile(conllu(c).findErrors() + "_html") or fromZero:
        if fromZero or not texto:
            #if not os.path.isfile(conllu(c).findErrors()):
            if os.system(JULGAMENTO_FOLDER + f'/.julgamento/bin/python3 {os.path.abspath(os.path.dirname(__file__))}/tools/validate.py {conllu(c).findGolden()} --max-err=0 --lang={VALIDATE_LANG} 2>&1 | tee {conllu(c).findErrors()}'):
                pass
            with open(conllu(c).findErrors()) as f:
                texto = f.read()
        if conllu(c).golden() in allCorpora.corpora and allCorpora.corpora.get(conllu(c).golden()):
            corpus = allCorpora.corpora.get(conllu(c).golden())
        else:
            corpus = estrutura_ud.Corpus(recursivo=True)
            corpus.load(conllu(c).findGolden())
        with open(conllu(c).findGolden(), 'r') as f:
            arquivo = f.read()
            arquivoSplit = arquivo.splitlines()
        sent_ids = {}
        exceptions = [
            'Exception caught',
            'for 9',
            'Non-tree',
            'HEAD == ID',
            'cycle',
            'Skipping'
        ]
        exceptions += exc
        for linha in texto.splitlines():
            if linha and any(x.lower().strip() in linha.lower() for x in exceptions) and ' Node ' in linha and 'Sent ' in linha and ("Line " in linha or ' line ' in linha):
                t = int(linha.split("Line ", 1)[1].split(" ")[0]) if "Line " in linha else int(linha.split(" line ", 1)[1].split(" ")[0])
                if "\t" in arquivoSplit[t-1]:
                    if not linha.split(":", 1)[1] in sent_ids:
                        sent_ids[linha.split(":", 1)[1]] = []
                    bold = {'word': arquivoSplit[t-1].split("\t")[1], 'color': 'black'}# if '\t' in arquivo.splitlines()[t-1] else ""
                    t = allCorpora.corpora[conllu(c).golden()].sentences[linha.split(" Node ")[0].split("Sent ", 1)[1]].map_token_id[arquivo.splitlines()[t-1].split("\t")[0]]
                    sent_ids[linha.split(":", 1)[1]].append({'id': linha.split(" Node ")[0].split("Sent ", 1)[1], 't': t, 'bold': bold})
        html = ""
        for k, problem in enumerate(sorted(sent_ids)):
            html += f"<div class='alert alert-warning' role='alert'>{k+1} / {len(sent_ids)} - {problem}</div>"
            for i, sent_id in enumerate(sent_ids[problem]):
                if sent_id['id'] in corpus.sentences:
                    if sent_id['bold']['word'] and sent_id['bold']['color'] and sent_id['t']:
                        html += f'<div class="panel panel-default"><div class="panel-body">{ i+1 } / { len(sent_ids[problem]) }</div>' + \
                            render_template(
                                'sentence.html',
                                golden=corpus.sentences[sent_id['id']],
                                c=c,
                                t=sent_id['t'],
                                bold=sent_id['bold'],
                                goldenAndSystem=True if conllu(c).system() in allCorpora.corpora else False,
                            ) + "</div></div>"
                    else:
                        html += f'<div class="panel panel-default"><div class="panel-body">{ i+1 } / { len(sent_ids[problem]) }: {sent_id["id"]}</div>'

        with open(conllu(c).findErrors() + "_html", "w") as f:
            f.write(html)
    else:
        with open(conllu(c).findErrors() + "_html") as f:
            html = f.read()
    
    return html

def findCorpora(filtro, tipo):
    lista = []
    if tipo == 'available':
        corpora = checkCorpora()['available']
    elif tipo == 'training':
        corpora = checkCorpora()['inProgress']
    elif tipo == 'success':
        corpora = checkCorpora()['success']
    elif tipo == 'delete':
        corpora = checkCorpora()['available']
    elif tipo == 'onlyGolden':
        corpora = checkCorpora()['missingSystem']
    elif tipo == 'deleteGolden':
        corpora = checkCorpora()['missingSystem']
    elif tipo == 'features':
        corpora = checkCorpora()['withFeatures']
    filtro = filtro.split()
    for corpus in corpora:
        if tipo not in ["deleteGolden", "onlyGolden", 'features']:
            sobre = corpus['sobre'] if 'sobre' in corpus else ""
            corpusNom = corpus['nome']
            corpusDate = corpus['data'] 
        else:
            sobre = ""
            corpusNom = corpus
            corpusDate = ""
        if not filtro or all(x.lower() in (corpusNom+sobre+corpusDate).lower() for x in filtro):
            if tipo == 'available':
                lista.append(f'<a href="/corpus?c={ corpus["nome"] }" class="list-group-item"><strong>{ corpus["nome"] }</strong> <span class="badge">{ corpus["sentences"] } <span class="translateHtml">sentenças</span></span><br>{ corpus["sobre"] }<br><small>{ prettyDate(corpus["data"]).prettyDateDMAH() }</small></a>')
            elif tipo == 'training':
                terminated = ""
                if prettyDate(corpus["data"]).hora +3 < prettyDate(str(datetime.datetime.now())).hora:
                    terminated = "&terminated=True"
                lista.append(f'<a href="/log?c={ corpus["nome"] }{terminated}" class="list-group-item"><strong>{ corpus["nome"] }</strong><br><span class="translateHtml">Última modificação:</span> { prettyDate(corpus["data"]).prettyDateDMAH() }</a>')
            elif tipo == 'success':
                lista.append(f'<a href="/log?c={ corpus["nome"] }" class="list-group-item"><strong>{ corpus["nome"] }</strong><br><span class="translateHtml">Conclusão:</span> { prettyDate(corpus["data"]).prettyDateDMAH() }</a>')
            elif tipo == 'delete':
                lista.append(f'<a style="cursor:pointer" onclick="apagarCorpus(\'{corpus["nome"]}\')" class="list-group-item"><strong>{ corpus["nome"] }</strong> <span class="badge">{ corpus["sentences"] } <span class="translateHtml">sentenças</span></span><br>{ corpus["sobre"] }<br><small>{ prettyDate(corpus["data"]).prettyDateDMAH() }</small></a>')
            elif tipo == 'deleteGolden':
                lista.append(f'<a style="cursor:pointer" onclick="apagarCorpusGolden(\'{corpus}\')" class="list-group-item"><strong>{ corpus }</strong></a>')
            elif tipo == 'onlyGolden':
                if os.path.isfile(conllu(corpus).findOriginal()):
                    lista.append(f'<a href="/corpus?c={ corpus }" class="list-group-item"><strong>{ corpus }</strong></a>')
            elif tipo == 'features':
                lista.append(f'<a style="cursor:pointer" href="/static/uploads/{conllu(corpus).features()}" class="list-group-item"><strong>{ corpus }</strong></a>')


    return "\n".join(lista)

def removerAcento(s):
    return re.sub(r'[^A-Za-z0-9_\.\-]', '', s)

def formDB():
    return '''
<div class="form-horizontal">
    <div class="form-group">
        <label for="about" class="col-sm-4 control-label"><span class="translateHtml">Sobre o corpus</span> <span class='glyphicon glyphicon-info-sign translateTitle' title='Informação extra para ajudar a identificar os diferentes corpora disponíveis'></span></label>
        <div class="col-sm-8">
            <input class="form-control" id="about" name="about" >
        </div>
    </div>
    <div class="form-group">
        <label for="partitions" class="col-sm-4 control-label"><span class="translateHtml">Partições</span> <span class='glyphicon glyphicon-info-sign translateTitle' title='A separação entre as partições train/test/dev deve ser feita por meio de arquivos .txt, contendo um ID de sentença por linha, na pasta /static/uploads'></span></label>
        <div class="col-sm-8">
            <select class="form-control selectpicker" data-live-search="true" id="partitions" name="partitions" required>
                ''' + "\n".join(\
                    ["<option>" + x.rsplit("-", 1)[0] + "</option>" \
                        for x in os.listdir(UPLOAD_FOLDER) \
                            if '.txt' in x \
                                and "-train" in x \
                                    and all(os.path.isfile(UPLOAD_FOLDER + "/" + x.rsplit("-", 1)[0] + "-" + y + ".txt") \
                                        for y in ['test', 'train', 'dev'])]) + '''
            </select>
        </div>
    </div>
    <div class="form-group">
        <div class="col-sm-offset-4 col-sm-8">
            <div class="checkbox">
                <label>
                    <input name="crossvalidation" type="checkbox"> <span class="translateHtml">Treinar todo o corpus (crossvalidation)</span> 
                    <span class='glyphicon glyphicon-info-sign translateTitle' title='Treinar um corpus inteiro (crossvalidation) significa que vários modelos serão treinados, um para cada pedaço do corpus, de modo a garantir que o treino será realizado em todo o corpus e não haverá enviesamento. Pode demorar alguns dias para concluir o processo.'></span>
                </label>
            </div>
        </div>
    </div>
</div>
'''

class conllu:

    def __init__(self, corpus):
        if '/' in corpus: corpus = corpus.rsplit('/', 1)[1]
        self.naked = corpus.split("_inProgress")[0].split("_meta")[0].split('_sistema')[0].split(".conllu")[0].split('_success')[0].split('_original')[0].split('_features.html')[0]

    def golden(self):
        return self.naked + ".conllu"

    def original(self):
        return self.naked + "_original.conllu"

    def system(self):
        return self.naked + "_sistema.conllu"

    def inProgress(self):
        return self.naked + "_inProgress"

    def success(self):
        return self.naked + "_success"

    def errors(self):
        return self.naked + "_errors"

    def features(self):
        return self.naked + "_features.html"

    def findGolden(self):
        if INTERROGATORIO and os.path.isfile(f'{COMCORHD_FOLDER}/{self.naked}.conllu'):
            return f'{COMCORHD_FOLDER}/{self.naked}.conllu'
        elif os.path.isfile(UPLOAD_FOLDER + "/" + self.naked + ".conllu"):
            return UPLOAD_FOLDER + "/" + self.naked + ".conllu"
        elif INTERROGATORIO:
            return f'{COMCORHD_FOLDER}/{self.naked}.conllu'
        else:
            return UPLOAD_FOLDER + "/" + self.naked + ".conllu"
            
    def findOriginal(self):
        return UPLOAD_FOLDER + "/" + self.naked + "_original.conllu"

    def findFeatures(self):
        return UPLOAD_FOLDER + "/" + self.naked + "_features.html"

    def findSystem(self):
        return UPLOAD_FOLDER + "/" + self.naked + "_sistema.conllu"

    def findInProgress(self):
        return UPLOAD_FOLDER + "/" + self.naked + "_inProgress"

    def findSuccess(self):
        return UPLOAD_FOLDER + "/" + self.naked + "_success"

    def findErrors(self):
        return UPLOAD_FOLDER + "/" + self.naked + "_errors"

    def findErrorsValidarUD(self):
        return UPLOAD_FOLDER + "/" + self.naked + "_errorsValidarUD"


class prettyDate:

    def __init__(self, date):

        date = str(date)
        calendario_raw = "janeiro,fevereiro,março,abril,maio,junho,julho,agosto,setembro,outubro,novembro,dezembro"
        calendario = {i+1: mes for i, mes in enumerate(calendario_raw.split(","))}
        data = date.split(" ")[0].split("-")

        self.dia = int(data[2])
        self.mes = int(data[1])
        self.mesExtenso = calendario[self.mes]
        self.mesExtenso_3 = "".join(calendario[self.mes][:3])
        self.ano = int(data[0])		
        horabruta = date.split(" ")[1].rsplit(":", 1)[0]
        self.hora = int(horabruta.split(":")[0]) - localtime
        if self.hora < 0: self.hora = 24 + self.hora
        self.tempo = str(self.hora) + ":" + horabruta.split(":")[1]

    def prettyDateDMAH(self):
        
        return f"{self.dia} de {self.mesExtenso_3}. {self.ano} {self.tempo}"

    def prettyDateDMH(self):

        return f"{self.dia} de {self.mesExtenso_3}. às {self.tempo}"

    def prettyDateDMA(self):

        return f"{self.dia} de {self.mesExtenso} de {self.ano}"

dicionarioColunas = {
		'0': 'id',
		'1': 'word',
		'2': 'lemma',
		'3': 'upos',
		'4': 'xpos',
		'5': 'feats',
		'6': 'dephead',
		'7': 'deprel',
		'8': 'deps',
		'9': 'misc',
	}

def getMatrixSentences(c, golden, system, coluna):
    listaSentences = []
    ud1 = allCorpora.corpora.get(conllu(c).golden())
    ud2 = allCorpora.corpora.get(conllu(c).system())
    
    for sent_id, sentence in ud1.sentences.items():
        if sent_id in ud2.sentences and len(sentence.tokens) == len(ud2.sentences[sent_id].tokens):
            for t, token in enumerate(sentence.tokens):
                if token.__dict__[coluna.lower()] == golden and ud2.sentences[sent_id].tokens[t].__dict__[coluna.lower()] == system:
                    listaSentences.append({
                        'sent_id': sent_id, 
                        'golden': sentence, 
                        'system': ud2.sentences[sent_id], 
                        'divergence': {
                            'system': {'category': system, 'head': {'id': ud2.sentences[sent_id].tokens[t].head_token.id, 'word': ud2.sentences[sent_id].tokens[t].head_token.word}},
                            'golden': {'category': golden, 'head': {'id': token.head_token.id, 'word': token.head_token.word}}
                            },
                        'col': coluna.lower(),
                        'bold': {'word': token.word, 'color': 'black'},
                        'boldCol': f'{coluna.lower()}<coluna>{t}',
                        'secBold': {'word': token.head_token.word, 'color': 'green'} if coluna.lower() in ["deprel"] else "",
                        'thirdBold': {'word': ud2.sentences[sent_id].tokens[t].head_token.word, 'color': 'red'} if coluna.lower() in ["deprel"] else "",
                        't': t
                    })
    
    return listaSentences

def sortLambda(dicionario, lambdaattr, reverse=True):
    return sorted(dicionario, key=lambda x: dicionario[x][lambdaattr], reverse=reverse)

def categoryAccuracy(ud1, ud2, c, coluna="DEPREL"):
    tables = ""
    
    golden = allCorpora.corpora.get(conllu(ud1).golden())
    system = allCorpora.corpora.get(conllu(ud2).system())
    dicionario = {}
    UAS = dict()
    for sentid, sentence in golden.sentences.items():
        if sentid in system.sentences and len(golden.sentences[sentid].tokens) == len(system.sentences[sentid].tokens):
            for t, token in enumerate(sentence.tokens):
                if not token.__dict__[coluna.lower()] in dicionario:
                    dicionario[token.__dict__[coluna.lower()]] = [0, 0, 0]
                    if not token.__dict__[coluna.lower()] in UAS:
                        UAS[token.__dict__[coluna.lower()]] = dict()
                dicionario[token.__dict__[coluna.lower()]][0] += 1
                if coluna == "DEPREL" and system.sentences[sentid].tokens[t].__dict__[coluna.lower()] == token.__dict__[coluna.lower()]:
                    dicionario[token.__dict__[coluna.lower()]][2] += 1
                if ((coluna == "DEPREL" and system.sentences[sentid].tokens[t].__dict__['dephead'] == token.__dict__['dephead']) or (coluna == "UPOS")) and system.sentences[sentid].tokens[t].__dict__[coluna.lower()] == token.__dict__[coluna.lower()]:
                    dicionario[token.__dict__[coluna.lower()]][1] += 1
                elif system.sentences[sentid].tokens[t].__dict__[coluna.lower()] == token.__dict__[coluna.lower()]:
                    tok_golden = token.head_token.upos
                    tok_system = system.sentences[sentid].tokens[t].head_token.upos
                    tok_golden += "_L" if int(token.head_token.id) < int(token.id) else "_R"
                    tok_system += "_L" if int(system.sentences[sentid].tokens[t].head_token.id) < int(system.sentences[sentid].tokens[t].id) else "_R"
                    if tok_golden + "/" + tok_system in UAS[token.__dict__[coluna.lower()]]:
                        UAS[token.__dict__[coluna.lower()]][tok_golden + "/" + tok_system][0] += 1
                    else:
                        UAS[token.__dict__[coluna.lower()]][tok_golden + "/" + tok_system] = [1, []]
                    UAS[token.__dict__[coluna.lower()]][tok_golden + "/" + tok_system][1].append([sentid, t])


    coluna1 = ""
    coluna2 = ""
    coluna3 = ""    
    if coluna == "DEPREL":
        conteudo = "".join([f"<tr><td>{x}</td><td>{dicionario[x][0]}</td><td>{(dicionario[x][2] / dicionario[x][0])*100}%</td><td>{(dicionario[x][1] / dicionario[x][0])*100}%</td><td class='matrixTd'><a href='/corpus?c={c}&{coluna}={x}'>{(sum([len(UAS[x][y][1]) for y in UAS[x]]) / dicionario[x][0])*100}%</a></td></tr>" for x in sorted(dicionario, key=lambda x: x)])
        coluna2 = "<a style='text-decoration:underline; color:white; cursor:text;' class='translateTitle translateHtml' title='LAS é quando o deprel e o dephead estão corretos'>LAS</a>"
        coluna3 = "<a style='text-decoration:underline; color:white; cursor:text;' class='translateTitle translateHtml' title='Os erros de dephead são contabilizados apenas quando a etiqueta deprel está correta. Para ver divergências de deprel, verificar matriz de confusão'>Erros de dephead</a>"
        coluna1 = "<a style='text-decoration:underline; color:white; cursor:text;' class='translateTitle translateHtml' title='Acertos de deprel sem contabilizar dephead. Para ver divergências de deprel, verificar matriz de confusão'>Acertos</a>"
    elif coluna == "UPOS":
        conteudo = "".join([f"<tr><td>{x}</td><td>{dicionario[x][0]}</td><td>{(dicionario[x][1] / dicionario[x][0])*100}%</td></tr>" for x in sorted(dicionario, key=lambda x: x)])
        coluna1 = "<span class='translateHtml'>Acertos</span>"

    tables += f"<table id='t01' style='margin:auto; max-height:70vh; display:block; overflow-x: auto; overflow-y:auto;'><thead><tr style='text-align:center;'><th>{coluna}</th><th>Total</th>{'<th>' + coluna1 + '</th>' if coluna1 else ''}{'<th>' + coluna2 + '</th>' if coluna2 else ''}{'<th>' + coluna3 + '</th>' if coluna3 else ''}</tr></thead>\
        {conteudo}\
        </table>"

    return {'tables': tables, 'UAS': UAS}

def caracteristicasCorpus(ud1, ud2=""):
    golden = allCorpora.corpora.get(conllu(ud1).golden())
    if not golden:
        return None
    system = "" if not ud2 else allCorpora.corpora.get(conllu(ud2).system())

    n_Tokens = 0
    n_Sentences = len(golden.sentences)
    dicionario_Lemas = {}
    documentos_golden = {}
    documentos_sistema = {}
    for sentence in golden.sentences.values():
        documento = sentence.sent_id.rsplit("-", 1)[0]
        if not documento in documentos_golden:
            documentos_golden[documento] = [0, 0]
        documentos_golden[documento][0] += 1
        for token in sentence.tokens:
            if not '-' in token.id:
                if not token.lemma in dicionario_Lemas:
                    dicionario_Lemas[token.lemma] = 0
                dicionario_Lemas[token.lemma] += 1
                n_Tokens += 1
                documentos_golden[documento][1] += 1

    if system:
        n_Tokens_s = 0
        n_Sentences_s = len(system.sentences)
        dicionario_Lemas_s = {}
        for sentence in system.sentences.values():
            documento = sentence.sent_id.rsplit("-", 1)[0]
            if not documento in documentos_sistema:
                documentos_sistema[documento] = [0, 0]
            documentos_sistema[documento][0] += 1
            for token in sentence.tokens:
                if not '-' in token.id:
                    if not token.lemma in dicionario_Lemas_s:
                        dicionario_Lemas_s[token.lemma] = 0
                    dicionario_Lemas_s[token.lemma] += 1
                    n_Tokens_s += 1
                    documentos_sistema[documento][1] += 1

    tabela_Geral = "<h3 class='translateHtml'>Características do corpus</h3><br>"
    if system:
        tabela_Geral += "<table style='max-height:70vh; margin:auto; display:block; overflow-x: auto; overflow-y: auto; overflow:scroll;'>"
        tabela_Geral += "<tr><td></td><th class='translateHtml'>Sentenças</th><th class='translateHtml'>Tokens</th><th class='translateHtml'>Lemas diferentes</th></tr>"
        tabela_Geral += f"<tr><th class='translateHtml'>Golden</th><td>{n_Sentences}</td><td>{n_Tokens}</td><td>{len(dicionario_Lemas)}</td></tr>"
        tabela_Geral += f"<tr><th class='translateHtml'>Sistema</th><td>{n_Sentences_s}</td><td>{n_Tokens_s}</td><td>{len(dicionario_Lemas_s)}</td></tr>"
    else:
        tabela_Geral += "<table style='max-height:70vh; margin:auto; display:block; overflow-x: auto; overflow-y: auto; overflow:scroll;'>"
        tabela_Geral += "<tr><td></td><th class='translateHtml'>Sentenças</th><th class='translateHtml'>Tokens</th><th class='translateHtml'>Lemas diferentes</th></tr>"
        tabela_Geral += f"<tr><th class='translateHtml'>Golden</th><td>{n_Sentences}</td><td>{n_Tokens}</td><td>{len(dicionario_Lemas)}</td></tr>"
    tabela_Geral += "</table>"

    if documentos_golden:
        tabela_Geral += "<br><table style='max-height:70vh; margin:auto; display:block; overflow-x: auto; overflow-y: auto; overflow:scroll;'>"
        tabela_Geral += "<tr><th class='translateHtml'>GOLDEN</th><th class='translateHtml'>Sentenças</th><th class='translateHtml'>Tokens</th></tr>"
        for documento in sorted(documentos_golden):
            tabela_Geral += f"<tr><td>{documento}</td><td>{documentos_golden[documento][0]}</td><td>{documentos_golden[documento][1]}</td></tr>"
        tabela_Geral += "</table>"
        if system:
            tabela_Geral += "<br><table style='max-height:70vh; margin:auto; display:block; overflow-x: auto; overflow-y: auto; overflow:scroll;'>"
            tabela_Geral += "<tr><th class='translateHtml'>SISTEMA</th><th class='translateHtml'>Sentenças</th><th class='translateHtml'>Tokens</th></tr>"
            for documento in sorted(documentos_sistema):
                tabela_Geral += f"<tr><td>{documento}</td><td>{documentos_sistema[documento][0]}</td><td>{documentos_sistema[documento][1]}</td></tr>"
            tabela_Geral += "</table>"
    

    c = conllu(ud1).naked
    depois = allCorpora.corpora[conllu(c).golden()]
    antes = allCorpora.corpora[conllu(c).original()]

    lemas_diferentes = {}
    upos_diferentes = {}
    deprel_diferentes = {}
    sentences_diferentes = []
    text_diferentes = []
    comparable_sentences = []
    not_comparable_sentences = []
    removed_sentences = []
    modified_tokens = []
    for sentid, sentence in antes.sentences.items():
        if not sentid in depois.sentences:
            removed_sentences.append(sentid)
            continue
        if sentence.tokens_to_str() != depois.sentences[sentid].tokens_to_str():
            sentences_diferentes.append(sentid)
            if sentence.text != depois.sentences[sentid].text:
                text_diferentes.append(sentid + "<br>" + sentence.text + "<depois>" + depois.sentences[sentid].text)
        if len(sentence.tokens) != len(depois.sentences[sentid].tokens):
            not_comparable_sentences.append(sentid)
        else:
            comparable_sentences.append(sentid)
            for t, token in enumerate(sentence.tokens):
                if token.to_str() != depois.sentences[sentid].tokens[t].to_str():
                    modified_tokens.append(1)
                if token.lemma != depois.sentences[sentid].tokens[t].lemma:
                    if not token.lemma + "<depois>" + depois.sentences[sentid].tokens[t].lemma in lemas_diferentes:
                        lemas_diferentes[token.lemma + "<depois>" + depois.sentences[sentid].tokens[t].lemma] = []
                    lemas_diferentes[token.lemma + "<depois>" + depois.sentences[sentid].tokens[t].lemma].append({'sent_id': sentid, 'golden': sentence, 't': t, 'bold': {'word': token.word, 'color': 'red'}})
                if token.upos != depois.sentences[sentid].tokens[t].upos:
                    if not token.upos + "<depois>" + depois.sentences[sentid].tokens[t].upos in upos_diferentes:
                        upos_diferentes[token.upos + "<depois>" + depois.sentences[sentid].tokens[t].upos] = []
                    upos_diferentes[token.upos + "<depois>" + depois.sentences[sentid].tokens[t].upos].append({'sent_id': sentid, 'golden': sentence, 't': t, 'bold': {'word': token.word, 'color': 'red'}})
                if token.deprel != depois.sentences[sentid].tokens[t].deprel:
                    if not token.deprel + "<depois>" + depois.sentences[sentid].tokens[t].deprel in deprel_diferentes:
                        deprel_diferentes[token.deprel + "<depois>" + depois.sentences[sentid].tokens[t].deprel] = []
                    deprel_diferentes[token.deprel + "<depois>" + depois.sentences[sentid].tokens[t].deprel].append({'sent_id': sentid, 'golden': sentence, 't': t, 'bold': {'word': token.word, 'color': 'red'}})
    
    modificacoesCorpora.modificacoes[c] = {'lemma': lemas_diferentes, 'upos': upos_diferentes, 'deprel': deprel_diferentes}

    sentences_iguais = [x for x in depois.sentences if x not in sentences_diferentes]
    tabela_Geral += f"<br><h4><span class='translateHtml' style='cursor:pointer;' onclick='$(\".modified_sentences\").slideToggle();'>Sentenças modificadas</span>: {len(sentences_diferentes)} / {round((len(sentences_diferentes)/n_Sentences)*100, 2)}%</h4><pre class='modified_sentences' style='display:none;'>{'; '.join(sentences_diferentes)}</pre>"
    tabela_Geral += f"<br><h4><span class='translateHtml' style='cursor:pointer;' onclick='$(\".unmodified_sentences\").slideToggle();'>Sentenças não modificadas</span>: {len(sentences_iguais)} / {round((len(sentences_iguais)/n_Sentences)*100, 2)}%</h4><pre class='unmodified_sentences' style='display:none'>{'; '.join(sentences_iguais)}</pre>"
    tabela_Geral += f"<br><h4><span class='translateHtml' style='cursor:pointer;' onclick='$(\".removed_sentences\").slideToggle();'>Sentenças removidas</span>: {len(removed_sentences)}</h4><pre class='removed_sentences' style='display:none'>{'; '.join(removed_sentences)}</pre>"
    tabela_Geral += f"<br><h4><span class='translateHtml' style='cursor:pointer;' onclick='$(\".different_tokenization\").slideToggle();'>Sentenças com tokenização diferente</span>: {len(not_comparable_sentences)}</h4><pre class='different_tokenization' style='display:none'>{'; '.join(not_comparable_sentences)}</pre>"

    tabela_Geral += f"<br><h4 style='cursor:pointer;' onclick='$(\".different_text\").slideToggle();'><span class='translateHtml'>\"# text\" modificados</span>: {len(text_diferentes)}</h4>"
    tabela_Geral += "<table class='different_text' style='display:none;'>"
    for entrada in text_diferentes:
        tabela_Geral += "<tr><th></th><th>{}</th></tr>".format(entrada.split("<br>")[0])
        tabela_Geral += "<tr><th class='translateHtml'>ANTES</th><td>{}</td></tr>".format(entrada.split("<depois>")[0].split("<br>")[1])
        tabela_Geral += "<tr><th class='translateHtml'>DEPOIS</th><td>{}</td></tr>".format(entrada.split("<depois>")[1])    
    tabela_Geral += "</table>"

    tabela_Geral += f"<br><h4><span class='translateHtml'>Tokens modificados</span>: {len(modified_tokens)} / {round((len(modified_tokens)/n_Tokens)*100, 2)}%</h4>"
    tabela_Geral += f"<br><h4><span class='translateHtml'>Tokens modificados por sentença modificada</span>: {len(modified_tokens)/len(sentences_diferentes) if len(sentences_diferentes) else '0'}</h4>"

    tabela_Geral += f"<br><h4 style='cursor:pointer;' onclick='$(\".dist_lemas\").slideToggle();'><span class='translateHtml'>Distribuição de lemas</span>: {len(dicionario_Lemas)}</h4>"
    total_lemas = sum([dicionario_Lemas[y] for y in dicionario_Lemas])
    tabela_Geral += "<div style='margin-top:10px; display:none' class='dist_lemas'>"
    tabela_Geral += "<div class='col-lg-6'><table>"
    tabela_Geral += "<tr><th class='translateHtml'>Lemas em Golden</th><th>#</th><th>%</th></tr>"
    tabela_Geral += "".join([f"<tr><td>{x}</td><td>{dicionario_Lemas[x]}</td><td>{str((dicionario_Lemas[x]/total_lemas)*100)[:5]}%</td></tr>" for x in sorted(dicionario_Lemas, reverse=False, key=lambda y: (-dicionario_Lemas[y], y))])
    tabela_Geral += "</table></div>"

    if system:
        total_lemas = sum([dicionario_Lemas_s[y] for y in dicionario_Lemas_s])
        tabela_Geral += "<div class='col-lg-6'><table>"
        tabela_Geral += "<tr><th class='translateHtml'>Lemas em Sistema</th><th>#</th><th>%</th></tr>"
        tabela_Geral += "".join([f"<tr><td>{x}</td><td>{dicionario_Lemas_s[x]}</td><td>{str((dicionario_Lemas_s[x]/total_lemas)*100)[:5]}%</td></tr>" for x in sorted(dicionario_Lemas_s, reverse=False, key=lambda y: (-dicionario_Lemas_s[y], y))])
        tabela_Geral += "</table></div>"

    tabela_Geral += "</div>"

    tabela_Geral += f"<br><h4 style='cursor:pointer;' onclick='$(\".different_lemma\").slideToggle();'><span class='translateHtml'>Lemas modificados</span>: {sum([len(lemas_diferentes[x]) for x in lemas_diferentes])}</h4>"
    tabela_Geral += "<table class='different_lemma' style='display:none'>"
    tabela_Geral += "<tr><th class='translateHtml'>ANTES</th><th class='translateHtml'>DEPOIS</th><th>#</th></tr>"
    tabela_Geral += "".join(["<tr><td>" + x.split("<depois>")[0] + "</td><td>" + x.split("<depois>")[1] + f"</td><td class='matrixTd'><a href='/corpus?c={c}&antes={x.split('<depois>')[0]}&depois={x.split('<depois>')[1]}&mod=lemma'>" + str(len(lemas_diferentes[x])) + "</a></td></tr>" for x in sorted(lemas_diferentes, reverse=False, key=lambda y: (-len(lemas_diferentes[y]), y))])
    tabela_Geral += "</table>"

    tabela_Geral += f"<br><h4 style='cursor:pointer;' onclick='$(\".different_upos\").slideToggle();'><span class='translateHtml'>UPOS modificados</span>: {sum([len(upos_diferentes[x]) for x in upos_diferentes])}</h4>"
    tabela_Geral += "<table style='display:none;' class='different_upos'>"
    tabela_Geral += "<tr><th class='translateHtml'>ANTES</th><th class='translateHtml'>DEPOIS</th><th>#</th></tr>"
    tabela_Geral += "".join(["<tr><td>" + x.split("<depois>")[0] + "</td><td>" + x.split("<depois>")[1] + f"</td><td class='matrixTd'><a href='/corpus?c={c}&antes={x.split('<depois>')[0]}&depois={x.split('<depois>')[1]}&mod=upos'>" + str(len(upos_diferentes[x])) + "</a></td></tr>" for x in sorted(upos_diferentes, reverse=False, key=lambda y: (-len(upos_diferentes[y]), y))])
    tabela_Geral += "</table>"

    tabela_Geral += f"<br><h4 style='cursor:pointer;' onclick='$(\".different_deprel\").slideToggle();'><span class='translateHtml'>DEPREL modificados</span>: {sum([len(deprel_diferentes[x]) for x in deprel_diferentes])}</h4>"
    tabela_Geral += "<table class='different_deprel' style='display:none'>"
    tabela_Geral += "<tr><th class='translateHtml'>ANTES</th><th class='translateHtml'>DEPOIS</th><th>#</th></tr>"
    tabela_Geral += "".join(["<tr><td>" + x.split("<depois>")[0] + "</td><td>" + x.split("<depois>")[1] + f"</td><td class='matrixTd'><a href='/corpus?c={c}&antes={x.split('<depois>')[0]}&depois={x.split('<depois>')[1]}&mod=deprel'>" + str(len(deprel_diferentes[x])) + "</a></td></tr>" for x in sorted(deprel_diferentes, reverse=False, key=lambda y: (-len(deprel_diferentes[y]), y))])
    tabela_Geral += "</table>"

    with open(conllu(ud1).findFeatures(), "w") as f:
        f.write(render_template('caracteristicas.html',
            tabela_Geral=tabela_Geral,
            corpus=conllu(ud1).naked,
            user="")
            )
    return tabela_Geral

def sentAccuracy(ud1, ud2):
    golden = allCorpora.corpora.get(conllu(ud1).golden())
    system = allCorpora.corpora.get(conllu(ud2).system())

    sent_accuracy = [0, 0]
    for sentid, sentence in golden.sentences.items():
        if sentid in system.sentences and len(sentence.tokens) == len(system.sentences[sentid].tokens):
            sent_accuracy[0] += 1
            acertos = 0
            for t, token in enumerate(sentence.tokens):
                if system.sentences[sentid].tokens[t].upos == token.upos and system.sentences[sentid].tokens[t].dephead == token.dephead and system.sentences[sentid].tokens[t].deprel == token.deprel:
                    acertos += 1
            if acertos == len(sentence.tokens):
                sent_accuracy[1] += 1

    return "<table style='max-height:70vh; margin:auto; display:block; overflow-x: auto; overflow-y: auto; overflow:scroll;'><tr><th></th><th>#</th><th>%</th></tr><tr><th class='translateHtml'>Sentenças comparáveis</th><td>{comparableSentences}</td><td>{percentSentences}</td></tr>\
        <tr><th class='translateHtml'>Sentenças corretas</th><td>{correctSentences}</td><td>{percentCorrect}</td></tr>\
        </table>".format(
            comparableSentences=sent_accuracy[0],
            percentSentences=f"{(sent_accuracy[0] / len(golden.sentences)) * 100}%",
            correctSentences=sent_accuracy[1],
            percentCorrect=f"{(sent_accuracy[1] / sent_accuracy[0]) * 100}%",
    )

def metrics(ud1, ud2):
    html = ""
    if os.system(f"python3 {JULGAMENTO_FOLDER}/conll18_ud_eval.py {ud1} {ud2} -v > {UPLOAD_FOLDER}/{conllu(ud1).naked}_metrics"):
        pass
    with open(f"{UPLOAD_FOLDER}/{conllu(ud1).naked}_metrics", 'r') as f:
        html += f"<pre>{f.read()}</pre>"
    
    return html


def matrix(table, c, kind="UPOS"):
    html = ""
    colunas = [x for x in table.splitlines()[0].split()]

    for i, linha in enumerate(table.splitlines()):
        ud1 = linha.split()[0]
        if i == 0:
            html += "<thead>"
        html += "<tr>"
        for k, coluna in enumerate(linha.split()):
            ud2 = colunas[k] if len(colunas) > k else ""
            html += "<t{dorh}>{0}{2}{1}</t{dorh}>".format(f"<a href='/corpus?c={c}&ud1={ud1}&ud2={ud2}&col={kind}'>" if k != 0 and i != 0 and k + 1 < len(linha.split()) and i + 1 < len(table.splitlines()) else "", "</a>" if k != 0 and i != 0 and k + 1 < len(linha.split()) and i + 1 < len(table.splitlines()) else "", coluna, dorh="h" if k == 0 or i == 0 else "d class='matrixTd'")
        html += '</tr>'
        if i == 0:
            html += "</thead>"
    return "<table id='t01' style='margin:auto; max-height:85vh; display:block; overflow-x: auto; overflow-y:auto;'>" + html + "</table>"

def resub(s, a, b):
    return re.sub(r'\b' + a + r'\b', b, s)

@executor.job
def loadCorpus(x):
    if not os.path.isfile(conllu(x).findOriginal()):
        shutil.copyfile(conllu(x).findGolden(), conllu(x).findOriginal())
    if not conllu(x).golden() in allCorpora.corpora or not conllu(x).system() in allCorpora.corpora or (conllu(x).golden() in allCorpora.corpora and isinstance(allCorpora.corpora[conllu(x).golden()], str)) or (conllu(x).system() in allCorpora.corpora and isinstance(allCorpora.corpora[conllu(x).system()], str)):    
        corpusGolden, corpusSystem, corpusOriginal = estrutura_ud.Corpus(recursivo=True), estrutura_ud.Corpus(recursivo=True), estrutura_ud.Corpus(recursivo=True)
        #if not conllu(x).golden() in allCorpora.corpora:
            #if GOOGLE_LOGIN:
                #renderErrors(c=x, texto="", fromZero=True)
                #with open(conllu(x).findErrorsValidarUD(), "wb") as f:
                    #f.write(pickle.dumps(validar_UD.validate(
                        #conllu=corpusGolden,
                        #errorList=VALIDAR_UD,
                        #))
                    #)
        if not conllu(x).golden() in allCorpora.corpora:
            sys.stderr.write("\n>>>>>>>>>>>>>> loading {}...".format(x))
            corpusGolden.load(conllu(x).findGolden())
            corpusOriginal.load(conllu(x).findOriginal())
            allCorpora.corpora[conllu(x).golden()] = corpusGolden
            allCorpora.corpora[conllu(x).original()] = corpusOriginal
        if not conllu(x).system() in allCorpora.corpora and os.path.isfile(conllu(x).findSystem()):
            sys.stderr.write("\n>>>>>>>>>>>>>> loading system {}...".format(x))
            corpusSystem.load(conllu(x).findSystem())
            allCorpora.corpora[conllu(x).system()] = corpusSystem

def addDatabase(golden):
    corpusdb = db.session.query(models.Corpus).get(conllu(golden).naked)
    if corpusdb:
        db.session.remove(corpusdb)
        db.session.commit()
    novoCorpus = models.Corpus(
        name=conllu(golden).naked,
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

def checkCorpora():
    availableCorpora = []
    missingSystem = []

    for corpus in list(allCorpora.corpora.keys()):
        if not os.path.isfile(conllu(corpus).findGolden()) and conllu(corpus).golden() in allCorpora.corpora:
            allCorpora.corpora.pop(conllu(corpus).golden())
            if conllu(corpus).system() in allCorpora.corpora:
                allCorpora.corpora.pop(conllu(corpus).system())
            corpusdb = db.session.query(models.Corpus).get(conllu(corpus).naked)
            if corpusdb:
                db.session.delete(corpusdb)
                db.session.commit()
            if os.path.isfile(conllu(corpus).findSystem()):
                os.remove(conllu(corpus).findSystem())
            if os.path.isfile(conllu(corpus).findOriginal()):
                os.remove(conllu(corpus).findOriginal())
        if not os.path.isfile(conllu(corpus).findOriginal()) and conllu(corpus).original() in allCorpora.corpora:
            allCorpora.corpora.pop(conllu(corpus).original())

    if INTERROGATORIO:
        for x in os.listdir(COMCORHD_FOLDER):
            if os.path.getsize("{}/{}".format(COMCORHD_FOLDER, x))/1024/1000 < MAX_FILE_SIZE:
                if x.endswith('.conllu') and os.path.isfile(f'{UPLOAD_FOLDER}/{conllu(x).system()}'):
                    if not db.session.query(models.Corpus).get(conllu(x).naked):
                        addDatabase(x)
                    loadCorpus.submit(conllu(x).naked)
                    availableCorpora += [{'nome': conllu(x).naked, 'data': db.session.query(models.Corpus).get(conllu(x).naked).date, 'sobre': db.session.query(models.Corpus).get(conllu(x).naked).about, 'sentences': len(allCorpora.corpora[conllu(x).golden()].sentences) if conllu(x).golden() in allCorpora.corpora and not isinstance(allCorpora.corpora[conllu(x).golden()], str) else 0}]

    for x in os.listdir(UPLOAD_FOLDER):
        if os.path.getsize("{}/{}".format(UPLOAD_FOLDER, x))/1024/1000 < MAX_FILE_SIZE:
            if x.endswith('.conllu') and not x.endswith("_sistema.conllu") and not x.endswith("_original.conllu") and os.path.isfile(f"{UPLOAD_FOLDER}/{conllu(x).system()}") and not any(conllu(x).naked == k['nome'] for k in availableCorpora):
                if not db.session.query(models.Corpus).get(conllu(x).naked):
                    addDatabase(x)
                loadCorpus.submit(conllu(x).naked)
                availableCorpora += [{'nome': conllu(x).naked, 'data': db.session.query(models.Corpus).get(conllu(x).naked).date, 'sobre': db.session.query(models.Corpus).get(conllu(x).naked).about, 'sentences': len(allCorpora.corpora[conllu(x).golden()].sentences) if conllu(x).system() in allCorpora.corpora and not isinstance(allCorpora.corpora[conllu(x).system()], str) else 0}]

    if INTERROGATORIO:
        for x in os.listdir(COMCORHD_FOLDER):
            if os.path.getsize("{}/{}".format(COMCORHD_FOLDER, x))/1024/1000 < MAX_FILE_SIZE:
                if x.endswith('.conllu') and not any(x.endswith(y) for y in ['_sistema.conllu', '_original.conllu']) and not os.path.isfile(f"{UPLOAD_FOLDER}/{conllu(x).system()}") and not os.path.isfile(f"{UPLOAD_FOLDER}/{conllu(x).inProgress()}"):
                    loadCorpus.submit(conllu(x).naked)
                    missingSystem += [conllu(x).naked]

    for x in os.listdir(UPLOAD_FOLDER):
        if os.path.getsize("{}/{}".format(UPLOAD_FOLDER, x))/1024/1000 < MAX_FILE_SIZE:
            if x.endswith('.conllu') and not os.path.isfile(f"{UPLOAD_FOLDER}/{conllu(x).system()}") and not any(x.endswith(y) for y in ['_sistema.conllu', '_original.conllu']) and not os.path.isfile(f"{UPLOAD_FOLDER}/{conllu(x).inProgress()}") and not conllu(x).naked in missingSystem:
                loadCorpus.submit(conllu(x).naked)
                missingSystem += [conllu(x).naked]
    
    inProgress = [{'nome': conllu(x).naked, 'data': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(conllu(x).findInProgress())))} for x in os.listdir(UPLOAD_FOLDER) if x.endswith('_inProgress')]
    success = [{'nome': conllu(x).naked, 'data': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(conllu(x).findSuccess())))} for x in os.listdir(UPLOAD_FOLDER) if x.endswith('_success')]
    features = []

    for arquivo in os.listdir(UPLOAD_FOLDER):
        if arquivo == conllu(arquivo).features():
            if conllu(arquivo).naked not in features and conllu(arquivo).naked not in [conllu(x).naked for x in allCorpora.corpora]:
                features.append(arquivo.split("_features.html")[0])

    return {
        'available': sorted(availableCorpora, key=lambda x: x['data'], reverse=True),
        'missingSystem': sorted(missingSystem),
        'onlyGolden': sorted(missingSystem),
        'inProgress': sorted(inProgress, key=lambda x: x['data'], reverse=True),
        'success': sorted(success, key=lambda x: x['data'], reverse=True),
        'withFeatures': sorted(features),
        }