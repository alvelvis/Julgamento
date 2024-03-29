from config import UPLOAD_FOLDER, COMCORHD_FOLDER, JULGAMENTO_FOLDER, REPOSITORIES, VALIDATE_UD, VALIDATE_LANG, VALIDAR_UD
from flask import render_template, request
from sklearn.metrics import cohen_kappa_score
import pandas as pd
import os, estrutura_ud, estrutura_dados, confusao, re, time, datetime, validar_UD
import models, pickle
from app import db, app, allCorpora, modificacoesCorpora
from localtime import localtime
import sys, shutil
import subprocess

MAX_FILE_SIZE = 50

INTERROGATORIO = False
if os.path.isdir(os.path.abspath(os.path.join(JULGAMENTO_FOLDER, "..", "Interrogat-rio"))):
    globals()['INTERROGATORIO'] = True
else:
    globals()['INTERROGATORIO'] = False

def get_annotations(corpus1, corpus2):
    annotations1 = {}
    annotations2 = {}
    sentences = corpus1.sentences.keys()
    for sent_id in sentences:
        sentence1 = corpus1.sentences[sent_id]
        sentence2 = corpus2.sentences[sent_id]
        if len(sentence1.tokens) == len(sentence2.tokens):
            for t in range(len(sentence1.tokens)):
                token1 = sentence1.tokens[t]
                if '-' in token1.id:
                    continue
                token2 = sentence2.tokens[t]
                for col in token1.__dict__:
                    if not col in token2.__dict__:
                        continue
                    if col in estrutura_ud.col_to_idx or (col.startswith("col") and col != "color"):
                        if not col in annotations1:
                            annotations1[col] = []
                        if not col in annotations2:
                            annotations2[col] = []
                        annotations1[col].append((sent_id, t, token1.__dict__[col]))
                        annotations2[col].append((sent_id, t, token2.__dict__[col]))
    
    return annotations1, annotations2
            
def get_divergences(corpus1, corpus2, c):
    annotations1, annotations2 = get_annotations(corpus1, corpus2)

    cols = annotations1.keys()
    divergences = {col: [t for t, x in enumerate(annotations1[col]) if x != annotations2[col][t]] for col in cols}
    divergence_groups = {}

    for col in cols:
        if not col in divergence_groups:
            divergence_groups[col] = {}
        for t in divergences[col]:
            value1 = annotations1[col][t][2]
            value2 = annotations2[col][t][2]
            group = "%sxxx%s" % (value1, value2)
            if not group in divergence_groups[col]:
                divergence_groups[col][group] = []
            divergence_groups[col][group].append(annotations1[col][t])

    html = " | ".join(["<a style='color:blue; cursor:pointer;' class='toggle_columns' col='{0}'>{0} ({1})</a>".format(col, len(divergences[col])) for col in cols])
    for col in cols:
        html += "<div class='columnsDiv' style='display:none' col='%s'>" % col
        html += "<h1>Divergências de %s (%s)</h1>" % (col, len(divergences[col]))
        for group in sorted(divergence_groups[col]):
            html += "<a target='_blank' href='/corpus?c={c}&ud1={ud1}&ud2={ud2}&col={col}'>{ud1} - {ud2} ({n})</a><br>".format(
                c=c,
                ud1=group.split("xxx")[0], 
                ud2=group.split("xxx")[1], 
                col=col,
                n=len(divergence_groups[col][group])
                )

        html += "</div>"

    return html

def get_accuracy(corpus1, corpus2):
    annotations1, annotations2 = get_annotations(corpus1, corpus2)
    cols = annotations1.keys()
    html = " | ".join(["<a style='color:blue; cursor:pointer;' class='toggle_columns' col='{0}'>{0}</a>".format(col) for col in cols])
    for col in cols:
        same_annotation = len(set(annotations1[col]).intersection(set(annotations2[col])))
        n_tokens = len(annotations1[col])
        html += "<div class='columnsDiv' style='display:none' col='%s'>" % col
        html += "<h1>Acurácia de %s</h1>" % col
        html += "Número de tokens: %s" % n_tokens
        html += "<br>Anotações iguais: %s" % same_annotation
        html += "<br>Acurácia: %.4f" % (same_annotation / n_tokens)
        html += "<hr>"
        html += "<h1>Por etiqueta</h1>"
        html += "<table style='margin:auto'>"
        html += "<tr><th>Etiqueta</th><th>Quantidade</th><th>Acurácia</th></tr>"
        labels = {}
        for t, token in enumerate(annotations1[col]):
            label = token[2]
            if not label in labels:
                labels[label] = []
            labels[label].append(t)
        hits = {label: len([t for t in labels[label] if annotations2[col][t][2] == label]) for label in labels}
        for label in sorted(labels):
            html += "<tr><td>%s</td><td>%s</td><td>%.4f</td></tr>" % (label, len(labels[label]), hits[label]/len(labels[label]))
        html += "</table>"
        html += "</div>"
    return html

def get_kappa(corpus1, corpus2):
    annotations1, annotations2 = get_annotations(corpus1, corpus2)
    cols = annotations1.keys()
    html = " | ".join(["<a style='color:blue; cursor:pointer;' class='toggle_columns' col='{0}'>{0}</a>".format(col) for col in cols])
    for col in cols:
        html += "<div class='columnsDiv' style='display:none' col='%s'>" % col
        html += "<h1>Concordância interanotadores (Cohen's Kappa) de %s</h1>" % col
        html += "Concordância: %.4f" % cohen_kappa_score([x[2] for x in annotations1[col]], [x[2] for x in annotations2[col]])
        html += "</div>"
    return html

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


def renderErrorsUD(c, texto="", exc=[], fromZero=False):
    if not os.path.isfile(conllu(c).findErrorsUD() + "_html") or fromZero:
        if fromZero or not texto:
            #if not os.path.isfile(conllu(c).findErrorsUD()):
            if not 'win' in sys.platform:
                if os.system('"' + JULGAMENTO_FOLDER + f'/.julgamento/bin/python3" "{os.path.abspath(os.path.dirname(__file__))}/tools/validate.py" "{conllu(c).findFirst()}" --max-err=0 --lang={VALIDATE_LANG} 2>&1 | tee "{conllu(c).findErrorsUD()}"'):
                    pass
            else:
                subprocess.Popen('"{}\\python.exe\" "{}\\tools\\validate.py" "{}" --max-err=0 --lang={} > "{}" 2>&1'.format(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Python39"), os.path.abspath(os.path.dirname(__file__)), conllu(c).findFirst(), VALIDATE_LANG, conllu(c).findErrorsUD()), shell=True).wait()
            with open(conllu(c).findErrorsUD()) as f:
                texto = f.read()
        if conllu(c).first() in allCorpora.corpora and allCorpora.corpora.get(conllu(c).first()):
            corpus = allCorpora.corpora.get(conllu(c).first())
        else:
            corpus = estrutura_ud.Corpus(recursivo=True)
            corpus.load(conllu(c).findFirst())
        with open(conllu(c).findFirst(), 'r') as f:
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
                    bold = {'word': arquivoSplit[t-1].split("\t")[1], 'color': 'black', 'id': arquivo.splitlines()[t-1].split("\t")[0]}# if '\t' in arquivo.splitlines()[t-1] else ""
                    t = allCorpora.corpora[conllu(c).first()].sentences[linha.split(" Node ")[0].split("Sent ", 1)[1]].map_token_id[arquivo.splitlines()[t-1].split("\t")[0]]
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
                                first=corpus.sentences[sent_id['id']],
                                c=c,
                                t=sent_id['t'],
                                bold=sent_id['bold'],
                                firstAndsecond=True if conllu(c).second() in allCorpora.corpora else False,
                            ) + "</div></div>"
                    else:
                        html += f'<div class="panel panel-default"><div class="panel-body">{ i+1 } / { len(sent_ids[problem]) }: {sent_id["id"]}</div>'

        with open(conllu(c).findErrorsUD() + "_html", "w") as f:
            f.write(html)
    else:
        with open(conllu(c).findErrorsUD() + "_html") as f:
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
    elif tipo == 'onlyfirst':
        corpora = checkCorpora()['missingsecond']
    elif tipo == 'deleteFirst':
        corpora = checkCorpora()['missingsecond']
    elif tipo == 'features':
        corpora = checkCorpora()['withFeatures']
    filtro = filtro.split()
    for corpus in corpora:
        if tipo not in ["deleteFirst", "onlyfirst", 'features']:
            sobre = corpus['sobre'] if 'sobre' in corpus else ""
            corpusNom = corpus['nome']
            corpusDate = corpus['data'] 
        else:
            sobre = ""
            corpusNom = corpus
            corpusDate = ""
        if not filtro or all(x.lower() in (corpusNom+sobre+corpusDate).lower() for x in filtro):
            if tipo == 'available':
                lista.append(f'<a href="/corpus?c={ corpus["nome"] }" class="list-group-item"><strong>{ corpus["nome"] }</strong> <span class="badge">{ corpus["sentences"] if corpus["sentences"] else "" } <span class="translateHtml">{"sentenças" if corpus["sentences"] else "clique para carregar"}</span></span><br>{ corpus["sobre"] }<br><small>{ prettyDate(corpus["data"]).prettyDateDMAH() }</small></a>')
            elif tipo == 'training':
                terminated = ""
                if prettyDate(corpus["data"]).hora +3 < prettyDate(str(datetime.datetime.now())).hora:
                    terminated = "&terminated=True"
                lista.append(f'<a href="/log?c={ corpus["nome"] }{terminated}" class="list-group-item"><strong>{ corpus["nome"] }</strong><br><span class="translateHtml">Última modificação:</span> { prettyDate(corpus["data"]).prettyDateDMAH() }</a>')
            elif tipo == 'success':
                lista.append(f'<a href="/log?c={ corpus["nome"] }" class="list-group-item"><strong>{ corpus["nome"] }</strong><br><span class="translateHtml">Conclusão:</span> { prettyDate(corpus["data"]).prettyDateDMAH() }</a>')
            elif tipo == 'delete':
                lista.append(f'<a style="cursor:pointer" onclick="apagarCorpus(\'{corpus["nome"]}\')" class="list-group-item"><strong>{ corpus["nome"] }</strong> <span class="badge">{ corpus["sentences"] } <span class="translateHtml">sentenças</span></span><br>{ corpus["sobre"] }<br><small>{ prettyDate(corpus["data"]).prettyDateDMAH() }</small></a>')
            elif tipo == 'deleteFirst':
                lista.append(f'<a style="cursor:pointer" onclick="apagarcorpusFirst(\'{corpus}\')" class="list-group-item"><strong>{ corpus }</strong></a>')
            elif tipo == 'onlyfirst':
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
        <label for="about" class="col-sm-4 control-label"><span class="translateHtml">Sobre o corpus</span> <span class='glyphicon glyphicon-info-sign translateTitle' title='Descrição para ajudar a identificar os diferentes corpora disponíveis'></span></label>
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
        corpus = os.path.basename(corpus)
        self.naked = corpus.split("_inProgress")[0].split("_meta")[0].split('_second')[0].split(".conllu")[0].split('_success')[0].split('_original')[0].split('_features.html')[0]

    def first(self):
        return self.naked + ".conllu"

    def original(self):
        return self.naked + "_original.conllu"

    def second(self):
        return self.naked + "_second.conllu"

    def inProgress(self):
        return self.naked + "_inProgress"

    def success(self):
        return self.naked + "_success"

    def errorsUD(self):
        return self.naked + "_errors"

    def features(self):
        return self.naked + "_features.html"

    def findFirst(self):
        if INTERROGATORIO and os.path.isfile(os.path.join(COMCORHD_FOLDER, self.naked + '.conllu')):
            return os.path.join(COMCORHD_FOLDER, self.naked + '.conllu')
        elif os.path.isfile(os.path.join(UPLOAD_FOLDER, self.naked + ".conllu")):
            return os.path.join(UPLOAD_FOLDER, self.naked + ".conllu")
        elif INTERROGATORIO:
            return os.path.join(COMCORHD_FOLDER, self.naked + '.conllu')
        else:
            return os.path.join(UPLOAD_FOLDER, self.naked + ".conllu")
            
    def findOriginal(self):
        return os.path.join(UPLOAD_FOLDER, self.naked + "_original.conllu")

    def findFeatures(self):
        return os.path.join(UPLOAD_FOLDER, self.naked + "_features.html")

    def findSecond(self):
        return os.path.join(UPLOAD_FOLDER, self.naked + "_second.conllu")

    def findInProgress(self):
        return os.path.join(UPLOAD_FOLDER, self.naked + "_inProgress")

    def findSuccess(self):
        return os.path.join(UPLOAD_FOLDER, self.naked + "_success")

    def findErrorsUD(self):
        return os.path.join(UPLOAD_FOLDER, self.naked + "_errorsUD")

    def findErrorsET(self):
        return os.path.join(UPLOAD_FOLDER, self.naked + "_errorsET")


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

def getMatrixSentences(c, first, second, coluna):
    listaSentences = []
    ud1 = allCorpora.corpora.get(conllu(c).first())
    ud2 = allCorpora.corpora.get(conllu(c).second())
    
    for sent_id, sentence in ud1.sentences.items():
        if sent_id in ud2.sentences and len(sentence.tokens) == len(ud2.sentences[sent_id].tokens):
            for t, token in enumerate(sentence.tokens):
                if token.__dict__[coluna.lower()] == first and ud2.sentences[sent_id].tokens[t].__dict__[coluna.lower()] == second:
                    listaSentences.append({
                        'sent_id': sent_id, 
                        'first': sentence, 
                        'second': ud2.sentences[sent_id], 
                        'divergence': {
                            'second': {'category': second, 'head': {'id': ud2.sentences[sent_id].tokens[t].head_token.id, 'word': ud2.sentences[sent_id].tokens[t].head_token.word}},
                            'first': {'category': first, 'head': {'id': token.head_token.id, 'word': token.head_token.word}}
                            },
                        'col': coluna.lower(),
                        'bold': {'word': token.word, 'color': 'black', 'id': token.id},
                        'boldCol': f'{coluna.lower()}<coluna>{t}',
                        'secBold': {'word': token.head_token.word, 'color': 'green', 'id': token.head_token.id} if coluna.lower() in ["deprel"] else "",
                        'thirdBold': {'word': ud2.sentences[sent_id].tokens[t].head_token.word, 'color': 'red', 'id': ud2.sentences[sent_id].tokens[t].head_token.id} if coluna.lower() in ["deprel"] else "",
                        't': t
                    })
    
    return listaSentences

def sortLambda(dicionario, lambdaattr, reverse=True):
    return sorted(dicionario, key=lambda x: dicionario[x][lambdaattr], reverse=reverse)

def categoryAccuracy(ud1, ud2, c, coluna="DEPREL"):
    tables = ""
    
    first = allCorpora.corpora.get(conllu(ud1).first())
    second = allCorpora.corpora.get(conllu(ud2).second())

    dicionario = {}
    UAS = dict()
    for sentid, sentence in first.sentences.items():
        if sentid in second.sentences and len(first.sentences[sentid].tokens) == len(second.sentences[sentid].tokens):
            for t, token in enumerate(sentence.tokens):
                if not token.__dict__[coluna.lower()] in dicionario:
                    dicionario[token.__dict__[coluna.lower()]] = [0, 0, 0]
                    if not token.__dict__[coluna.lower()] in UAS:
                        UAS[token.__dict__[coluna.lower()]] = dict()
                dicionario[token.__dict__[coluna.lower()]][0] += 1
                if coluna == "DEPREL" and second.sentences[sentid].tokens[t].__dict__[coluna.lower()] == token.__dict__[coluna.lower()]:
                    dicionario[token.__dict__[coluna.lower()]][2] += 1
                if ((coluna == "DEPREL" and second.sentences[sentid].tokens[t].__dict__['dephead'] == token.__dict__['dephead']) or (coluna == "UPOS")) and second.sentences[sentid].tokens[t].__dict__[coluna.lower()] == token.__dict__[coluna.lower()]:
                    dicionario[token.__dict__[coluna.lower()]][1] += 1
                elif second.sentences[sentid].tokens[t].__dict__[coluna.lower()] == token.__dict__[coluna.lower()]:
                    tok_first = token.head_token.upos
                    tok_second = second.sentences[sentid].tokens[t].head_token.upos
                    tok_first += "_L" if int(token.head_token.id) < int(token.id) else "_R"
                    tok_second += "_L" if int(second.sentences[sentid].tokens[t].head_token.id) < int(second.sentences[sentid].tokens[t].id) else "_R"
                    if tok_first + "/" + tok_second in UAS[token.__dict__[coluna.lower()]]:
                        UAS[token.__dict__[coluna.lower()]][tok_first + "/" + tok_second][0] += 1
                    else:
                        UAS[token.__dict__[coluna.lower()]][tok_first + "/" + tok_second] = [1, []]
                    UAS[token.__dict__[coluna.lower()]][tok_first + "/" + tok_second][1].append([sentid, t])


    coluna1 = ""
    coluna2 = ""
    coluna3 = ""    
    if coluna == "DEPREL":
        conteudo = "".join([f"<tr><td>{x}</td><td>{dicionario[x][0]}</td><td>{round((dicionario[x][2] / dicionario[x][0])*100, 2)}%</td><td>{round((dicionario[x][1] / dicionario[x][0])*100, 2)}%</td><td class='matrixTd'><a href='/corpus?c={c}&{coluna}={x}'>{round((sum([len(UAS[x][y][1]) for y in UAS[x]]) / dicionario[x][0])*100, 2)}%</a></td></tr>" for x in sorted(dicionario, key=lambda x: x)])
        coluna2 = "<a style='text-decoration:underline; color:white; cursor:text;' class='translateTitle translateHtml' title='LAS é quando o deprel e o dephead estão corretos'>LAS</a>"
        coluna3 = "<a style='text-decoration:underline; color:white; cursor:text;' class='translateTitle translateHtml' title='Os erros de dephead são contabilizados apenas quando a etiqueta deprel está correta. Para ver divergências de deprel, verificar matriz de confusão'>Erros de dephead</a>"
        coluna1 = "<a style='text-decoration:underline; color:white; cursor:text;' class='translateTitle translateHtml' title='Acertos de deprel sem contabilizar dephead. Para ver divergências de deprel, verificar matriz de confusão'>Acertos</a>"
    elif coluna == "UPOS":
        conteudo = "".join([f"<tr><td>{x}</td><td>{dicionario[x][0]}</td><td>{round((dicionario[x][1] / dicionario[x][0])*100, 2)}%</td></tr>" for x in sorted(dicionario, key=lambda x: x)])
        coluna1 = "<span class='translateHtml'>Acertos</span>"

    tables += f"<table id='t01' style='margin:0 auto; max-height:70vh; overflow-x: auto; overflow-y:auto;'><thead><tr style='text-align:center;'><th>{coluna}</th><th>Total</th>{'<th>' + coluna1 + '</th>' if coluna1 else ''}{'<th>' + coluna2 + '</th>' if coluna2 else ''}{'<th>' + coluna3 + '</th>' if coluna3 else ''}</tr></thead>\
        {conteudo}\
        </table>"

    return {'tables': tables, 'UAS': UAS}

def caracteristicasCorpus(ud1, ud2=""):
    first = allCorpora.corpora.get(conllu(ud1).first())
    if not first:
        return None
    second = "" if not ud2 else allCorpora.corpora.get(conllu(ud2).second())

    n_Tokens = 0
    n_Sentences = len(first.sentences)
    dicionario_Lemas = {}
    documentos_first = {}
    documentos_second = {}
    for sentence in first.sentences.values():
        documento = sentence.sent_id.rsplit("-", 1)[0]
        if not documento in documentos_first:
            documentos_first[documento] = [0, 0]
        documentos_first[documento][0] += 1
        for token in sentence.tokens:
            if not '-' in token.id:
                if not token.lemma in dicionario_Lemas:
                    dicionario_Lemas[token.lemma] = 0
                dicionario_Lemas[token.lemma] += 1
                n_Tokens += 1
                documentos_first[documento][1] += 1

    if second:
        n_Tokens_s = 0
        n_Sentences_s = len(second.sentences)
        dicionario_Lemas_s = {}
        for sentence in second.sentences.values():
            documento = sentence.sent_id.rsplit("-", 1)[0]
            if not documento in documentos_second:
                documentos_second[documento] = [0, 0]
            documentos_second[documento][0] += 1
            for token in sentence.tokens:
                if not '-' in token.id:
                    if not token.lemma in dicionario_Lemas_s:
                        dicionario_Lemas_s[token.lemma] = 0
                    dicionario_Lemas_s[token.lemma] += 1
                    n_Tokens_s += 1
                    documentos_second[documento][1] += 1

    tabela_Geral = "<h3 class='translateHtml'>Características do corpus</h3><br>"
    if second:
        tabela_Geral += "<table style='max-height:70vh; margin:auto; display:block; overflow-x: auto; overflow-y: auto; overflow:scroll;'>"
        tabela_Geral += "<tr><td></td><th class='translateHtml'>Sentenças</th><th class='translateHtml'>Tokens</th><th class='translateHtml'>Lemas diferentes</th></tr>"
        tabela_Geral += f"<tr><th class='translateHtml'>Principal</th><td>{n_Sentences}</td><td>{n_Tokens}</td><td>{len(dicionario_Lemas)}</td></tr>"
        tabela_Geral += f"<tr><th class='translateHtml'>Secundário</th><td>{n_Sentences_s}</td><td>{n_Tokens_s}</td><td>{len(dicionario_Lemas_s)}</td></tr>"
    else:
        tabela_Geral += "<table style='max-height:70vh; margin:auto; display:block; overflow-x: auto; overflow-y: auto; overflow:scroll;'>"
        tabela_Geral += "<tr><td></td><th class='translateHtml'>Sentenças</th><th class='translateHtml'>Tokens</th><th class='translateHtml'>Lemas diferentes</th></tr>"
        tabela_Geral += f"<tr><th class='translateHtml'>Principal</th><td>{n_Sentences}</td><td>{n_Tokens}</td><td>{len(dicionario_Lemas)}</td></tr>"
    tabela_Geral += "</table>"

    if documentos_first:
        tabela_Geral += "<br><table style='max-height:70vh; margin:auto; display:block; overflow-x: auto; overflow-y: auto; overflow:scroll;'>"
        tabela_Geral += "<tr><th class='translateHtml'>PRINCIPAL</th><th class='translateHtml'>Sentenças</th><th class='translateHtml'>Tokens</th></tr>"
        for documento in sorted(documentos_first):
            tabela_Geral += f"<tr><td>{documento}</td><td>{documentos_first[documento][0]}</td><td>{documentos_first[documento][1]}</td></tr>"
        tabela_Geral += "</table>"
        if second:
            tabela_Geral += "<br><table style='max-height:70vh; margin:auto; display:block; overflow-x: auto; overflow-y: auto; overflow:scroll;'>"
            tabela_Geral += "<tr><th class='translateHtml'>SECUNDÁRIO</th><th class='translateHtml'>Sentenças</th><th class='translateHtml'>Tokens</th></tr>"
            for documento in sorted(documentos_second):
                tabela_Geral += f"<tr><td>{documento}</td><td>{documentos_second[documento][0]}</td><td>{documentos_second[documento][1]}</td></tr>"
            tabela_Geral += "</table>"
    

    c = conllu(ud1).naked
    depois = allCorpora.corpora[conllu(c).first()]
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
                    lemas_diferentes[token.lemma + "<depois>" + depois.sentences[sentid].tokens[t].lemma].append({'sent_id': sentid, 'first': sentence, 't': t, 'bold': {'word': token.word, 'color': 'red', 'id': token.id}})
                if token.upos != depois.sentences[sentid].tokens[t].upos:
                    if not token.upos + "<depois>" + depois.sentences[sentid].tokens[t].upos in upos_diferentes:
                        upos_diferentes[token.upos + "<depois>" + depois.sentences[sentid].tokens[t].upos] = []
                    upos_diferentes[token.upos + "<depois>" + depois.sentences[sentid].tokens[t].upos].append({'sent_id': sentid, 'first': sentence, 't': t, 'bold': {'word': token.word, 'color': 'red', 'id': token.id}})
                if token.deprel != depois.sentences[sentid].tokens[t].deprel:
                    if not token.deprel + "<depois>" + depois.sentences[sentid].tokens[t].deprel in deprel_diferentes:
                        deprel_diferentes[token.deprel + "<depois>" + depois.sentences[sentid].tokens[t].deprel] = []
                    deprel_diferentes[token.deprel + "<depois>" + depois.sentences[sentid].tokens[t].deprel].append({'sent_id': sentid, 'first': sentence, 't': t, 'bold': {'word': token.word, 'color': 'red', 'id': token.id}})
    
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
    tabela_Geral += "<tr><th class='translateHtml'>Lemas em Principal</th><th>#</th><th>%</th></tr>"
    tabela_Geral += "".join([f"<tr><td>{x}</td><td>{dicionario_Lemas[x]}</td><td>{str((dicionario_Lemas[x]/total_lemas)*100)[:5]}%</td></tr>" for x in sorted(dicionario_Lemas, reverse=False, key=lambda y: (-dicionario_Lemas[y], y))])
    tabela_Geral += "</table></div>"

    if second:
        total_lemas = sum([dicionario_Lemas_s[y] for y in dicionario_Lemas_s])
        tabela_Geral += "<div class='col-lg-6'><table>"
        tabela_Geral += "<tr><th class='translateHtml'>Lemas em Secundário</th><th>#</th><th>%</th></tr>"
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
            corpus=conllu(ud1).naked,)
            )
    return tabela_Geral

def sentAccuracy(ud1, ud2):
    first = allCorpora.corpora.get(conllu(ud1).first())
    second = allCorpora.corpora.get(conllu(ud2).second())

    sent_accuracy = [0, 0]
    for sentid, sentence in first.sentences.items():
        if sentid in second.sentences and len(sentence.tokens) == len(second.sentences[sentid].tokens):
            sent_accuracy[0] += 1
            acertos = 0
            for t, token in enumerate(sentence.tokens):
                if second.sentences[sentid].tokens[t].upos == token.upos and second.sentences[sentid].tokens[t].dephead == token.dephead and second.sentences[sentid].tokens[t].deprel == token.deprel:
                    acertos += 1
            if acertos == len(sentence.tokens):
                sent_accuracy[1] += 1

    return "<table style='max-height:70vh; margin:auto; display:block; overflow-x: auto; overflow-y: auto; overflow:scroll;'><tr><th></th><th>#</th><th>%</th></tr><tr><th class='translateHtml'>Sentenças comparáveis</th><td>{comparableSentences}</td><td>{percentSentences}</td></tr>\
        <tr><th class='translateHtml'>Sentenças corretas</th><td>{correctSentences}</td><td>{percentCorrect}</td></tr>\
        </table>".format(
            comparableSentences=sent_accuracy[0],
            percentSentences=f"{(sent_accuracy[0] / len(first.sentences)) * 100}%",
            correctSentences=sent_accuracy[1],
            percentCorrect=f"{(sent_accuracy[1] / sent_accuracy[0]) * 100}%",
    )

def metrics(ud1, ud2):
    html = ""
    if not 'win' in sys.platform:
        if os.system(f"python3 '{JULGAMENTO_FOLDER}/conll18_ud_eval.py' '{ud1}' '{ud2}' -v > '{UPLOAD_FOLDER}/{conllu(ud1).naked}_metrics'"):
            pass
    else:
        subprocess.Popen('"{}\\python.exe\" "{}\\conll18_ud_eval.py" "{}" "{}" -v > {}'.format(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "Python39"), 
            JULGAMENTO_FOLDER,
            ud1,
            ud2,
            os.path.join(UPLOAD_FOLDER, conllu(ud1).naked + "_metrics")
            ), shell=True).wait()

    with open(f"{UPLOAD_FOLDER}/{conllu(ud1).naked}_metrics", 'r') as f:
        result = f.read()
    if not result.strip():
        result = "Houve um erro na geração das métricas de avaliação, verifique o terminal."
    html += f"<pre>{result}</pre>"
    
    return html


def matrix(table, c, kind):
    html = ""
    colunas = [x for x in table.splitlines()[0].split()]

    for i, linha in enumerate(table.splitlines()):
        ud1 = linha.split()[0]
        if i == 0:
            html += "<thead>"
        html += "<tr>"
        for k, coluna in enumerate(linha.split()):
            ud2 = colunas[k] if len(colunas) > k else ""
            html += "<t{dorh}>{0}{2}{1}</t{dorh}>".format(f"<a href='/corpus?c={c}&ud1={ud1}&ud2={ud2}&col={kind}' target='_blank'>" if k != 0 and i != 0 and k + 1 < len(linha.split()) and i + 1 < len(table.splitlines()) else "", "</a>" if k != 0 and i != 0 and k + 1 < len(linha.split()) and i + 1 < len(table.splitlines()) else "", coluna, dorh="h" if k == 0 or i == 0 else "d class='matrixTd'")
        html += '</tr>'
        if i == 0:
            html += "</thead>"
    return "<table id='t01' style='margin:auto; max-height:85vh; display:block; overflow-x: auto; overflow-y:auto;'>" + html + "</table>"

def resub(s, a, b):
    return re.sub(r'\b' + a + r'\b', b, s)

def paint_text(sentence, id1, color1, id2="", color2="", id3="", color3=""):
    text = []
    for token in sentence.tokens:
        if not '-' in token.id and not '.' in token.id:
            word = token.word
            if id3 and token.id == id3:
                word = "<span style='color:{}'>{}</span>".format(color3 if id2 != id3 else "purple", word)
            elif id2 and token.id == id2:
                word = "<span style='color:{}'>{}</span>".format(color2, word)
            elif id1 and token.id == id1:
                word = "<b><span style='color:{}'>{}</span></b>".format(color1, word)
            text.append(word)
    return " ".join(text)

def loadCorpus(x):
    if os.path.isfile(conllu(x).findFirst()) and not os.path.isfile(conllu(x).findOriginal()):
        shutil.copyfile(conllu(x).findFirst(), conllu(x).findOriginal())
    if os.path.isfile(conllu(x).findSecond()) and not conllu(x).second() in allCorpora.corpora:
        allCorpora.corpora[conllu(x).second()] = estrutura_ud.Corpus(recursivo=True)
    if not conllu(x).first() in allCorpora.corpora:
        allCorpora.corpora[conllu(x).first()] = estrutura_ud.Corpus(recursivo=True)
    if not conllu(x).original() in allCorpora.corpora:
        allCorpora.corpora[conllu(x).original()] = estrutura_ud.Corpus(recursivo=True)
    if conllu(x).second() in allCorpora.corpora and not allCorpora.corpora[conllu(x).second()].sentences:
        sys.stderr.write("\n>>>>>>>>>>>>>> loading second {}...".format(x))
        corpus = estrutura_ud.Corpus(recursivo=True)
        corpus.load(conllu(x).findSecond())
        allCorpora.corpora[conllu(x).second()].sentences = dict(corpus.sentences.items())
        sys.stderr.write(" second ok <<<<<<<<")
    if conllu(x).original() in allCorpora.corpora and not allCorpora.corpora[conllu(x).original()].sentences:
        corpus = estrutura_ud.Corpus(recursivo=True)
        corpus.load(conllu(x).findOriginal())
        allCorpora.corpora[conllu(x).original()].sentences = dict(corpus.sentences.items())
    if conllu(x).first() in allCorpora.corpora and not allCorpora.corpora[conllu(x).first()].sentences:
        sys.stderr.write("\n>>>>>>>>>>>>>> loading first {}...".format(x))
        corpus = estrutura_ud.Corpus(recursivo=True)
        corpus.load(conllu(x).findFirst())
        allCorpora.corpora[conllu(x).first()].sentences = dict(corpus.sentences.items())
        sys.stderr.write(" ok <<<<<<<<")
    corpus = ""

def addDatabase(first):
    corpusdb = db.session.query(models.Corpus).get(conllu(first).naked)
    if corpusdb:
        db.session.remove(corpusdb)
        db.session.commit()
    novoCorpus = models.Corpus(
        name=conllu(first).naked,
        date=str(datetime.datetime.now()),
        sentences=0,
        about=request.values.get('sysAbout') if request.values.get('sysAbout') else "Editar descrição",
        partitions="",
    )
    db.session.add(novoCorpus)
    db.session.commit()

def checkCorpora():
    availableCorpora = []
    missingsecond = []

    for corpus in list(allCorpora.corpora.keys()):
        if not os.path.isfile(conllu(corpus).findFirst()) and conllu(corpus).first() in allCorpora.corpora:
            allCorpora.corpora.pop(conllu(corpus).first())
            if conllu(corpus).second() in allCorpora.corpora:
                allCorpora.corpora.pop(conllu(corpus).second())
            corpusdb = db.session.query(models.Corpus).get(conllu(corpus).naked)
            if corpusdb:
                db.session.delete(corpusdb)
                db.session.commit()
            if os.path.isfile(conllu(corpus).findSecond()):
                os.remove(conllu(corpus).findSecond())
            if os.path.isfile(conllu(corpus).findOriginal()):
                os.remove(conllu(corpus).findOriginal())
        if not os.path.isfile(conllu(corpus).findOriginal()) and conllu(corpus).original() in allCorpora.corpora:
            allCorpora.corpora.pop(conllu(corpus).original())

    if INTERROGATORIO:
        for x in os.listdir(COMCORHD_FOLDER):
            if os.path.getsize("{}/{}".format(COMCORHD_FOLDER, x))/1024/1000 < MAX_FILE_SIZE:
                if x.endswith('.conllu') and os.path.isfile(f'{UPLOAD_FOLDER}/{conllu(x).second()}'):
                    if not db.session.query(models.Corpus).get(conllu(x).naked):
                        addDatabase(x)
                    availableCorpora += [{'nome': conllu(x).naked, 'data': db.session.query(models.Corpus).get(conllu(x).naked).date, 'sobre': db.session.query(models.Corpus).get(conllu(x).naked).about, 'sentences': len(allCorpora.corpora[conllu(x).first()].sentences) if conllu(x).first() in allCorpora.corpora and not isinstance(allCorpora.corpora[conllu(x).first()], str) else 0}]

    for x in os.listdir(UPLOAD_FOLDER):
        if os.path.getsize("{}/{}".format(UPLOAD_FOLDER, x))/1024/1000 < MAX_FILE_SIZE:
            if x.endswith('.conllu') and not x.endswith("_second.conllu") and not x.endswith("_original.conllu") and os.path.isfile(f"{UPLOAD_FOLDER}/{conllu(x).second()}") and not any(conllu(x).naked == k['nome'] for k in availableCorpora):
                if not db.session.query(models.Corpus).get(conllu(x).naked):
                    addDatabase(x)
                availableCorpora += [{'nome': conllu(x).naked, 'data': db.session.query(models.Corpus).get(conllu(x).naked).date, 'sobre': db.session.query(models.Corpus).get(conllu(x).naked).about, 'sentences': len(allCorpora.corpora[conllu(x).first()].sentences) if conllu(x).second() in allCorpora.corpora and not isinstance(allCorpora.corpora[conllu(x).second()], str) else 0}]

    if INTERROGATORIO:
        for x in os.listdir(COMCORHD_FOLDER):
            if os.path.getsize("{}/{}".format(COMCORHD_FOLDER, x))/1024/1000 < MAX_FILE_SIZE:
                if x.endswith('.conllu') and not any(x.endswith(y) for y in ['_second.conllu', '_original.conllu']) and not os.path.isfile(f"{UPLOAD_FOLDER}/{conllu(x).second()}") and not os.path.isfile(f"{UPLOAD_FOLDER}/{conllu(x).inProgress()}"):
                    missingsecond += [conllu(x).naked]

    for x in os.listdir(UPLOAD_FOLDER):
        if os.path.getsize("{}/{}".format(UPLOAD_FOLDER, x))/1024/1000 < MAX_FILE_SIZE:
            if x.endswith('.conllu') and not os.path.isfile(f"{UPLOAD_FOLDER}/{conllu(x).second()}") and not any(x.endswith(y) for y in ['_second.conllu', '_original.conllu']) and not os.path.isfile(f"{UPLOAD_FOLDER}/{conllu(x).inProgress()}") and not conllu(x).naked in missingsecond:
                missingsecond += [conllu(x).naked]
    
    inProgress = [{'nome': conllu(x).naked, 'data': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(conllu(x).findInProgress())))} for x in os.listdir(UPLOAD_FOLDER) if x.endswith('_inProgress')]
    success = [{'nome': conllu(x).naked, 'data': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(conllu(x).findSuccess())))} for x in os.listdir(UPLOAD_FOLDER) if x.endswith('_success')]
    features = []

    for arquivo in os.listdir(UPLOAD_FOLDER):
        if arquivo == conllu(arquivo).features():
            if conllu(arquivo).naked not in features and conllu(arquivo).naked not in [conllu(x).naked for x in allCorpora.corpora]:
                features.append(arquivo.split("_features.html")[0])

    return {
        'available': sorted(availableCorpora, key=lambda x: x['data'], reverse=True),
        'missingsecond': sorted(missingsecond),
        'onlyfirst': sorted(missingsecond),
        'inProgress': sorted(inProgress, key=lambda x: x['data'], reverse=True),
        'success': sorted(success, key=lambda x: x['data'], reverse=True),
        'withFeatures': sorted(features),
        }
