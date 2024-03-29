# -*- coding: utf-8 -*-

import sys
from estrutura_dados import LerUD
import re
import os
from subprocess import call
import estrutura_ud
import pandas as pd
import html as wb
import cgi
import datetime

feats = {
				1: "ID",
				2: "FORM",
				3: "LEMMA",
				4: "UPOS",
				5: "XPOS",
				6: "FEATS",
				7: "DEPHEAD",
				8: "DEPREL",
				9: "DEPS",
				10: "MISC",
}

def get_list(conllu1, conllu2, coluna):
		lista_coluna1 = list()
		lista_coluna2 = list()
		solitarios = list()

		for sentid, sentence in conllu1.sentences.items():
			if sentid in conllu2.sentences:
				if len(sentence.tokens) == len(conllu2.sentences[sentid].tokens):
					sentenceLength = len(sentence.tokens)
					if not sentid in conllu2.sentences or sentence.text != conllu2.sentences[sentid].text or len(sentence.tokens) != len(conllu2.sentences[sentid].tokens):
						solitarios.append(sentid + ': ' + sentence.text)
					else:
						for t, token in enumerate(sentence.tokens):
							if not '-' in token.id:
								lista_coluna1.append(token.__dict__[coluna])
								lista_coluna2.append(conllu2.sentences[sentid].tokens[t].__dict__[coluna])

		return {'matriz_1': lista_coluna1, 'matriz_2': lista_coluna2, 'solitários_1': solitarios}


def gerar_HTML(matriz, ud1, ud2, col, output, codificação):
		script = 'yes "\n" | python3 conll18_ud_eval.py -v "' + matriz.split('\n\n')[0].splitlines()[1].split(': ' ,1)[1] + '" "' + matriz.split('\n\n')[0].splitlines()[2].split(': ' ,1)[1] + '" > metrica.txt'
		call(script, shell=True)
		metrics = open("metrica.txt", 'r').read()
		with open(output + "_results.txt", "r") as f:
			resultados_cru = f.read()
		with open(output + "_sentence.txt", "r") as f:
			sentence_accuracy = f.read()

		resultados = "<table><tr><th colspan='4'>Acurácia por categoria gramatical</th></tr>"
		for linha in resultados_cru.splitlines():
			resultados += "<tr>"
			for n, item in enumerate(linha.split()):
				if n == 0:
					deprel = item
				if n + 1 == len(linha.split()) and deprel != "DEPREL":
					item = "<a href='UAS/" + deprel + ".html'>" + item + "</a>"
				resultados += "<td>" + item + "</td>"
			resultados += "</tr>"
		resultados += "</table>"

		html = ['<html><head><meta charset="'+codificação+'" name="viewport" content="width=device-width, initial-scale=1.0" ><link href="style.css" rel="stylesheet" type="text/css"><link href="http://fonts.googleapis.com/css?family=Lato" rel="stylesheet" type="text/css"></head><body><div class="header">']
		html.append('<h1>'+output+'</h1><br><span id="topo"><h3>' + "\n".join(matriz.split('\n\n')[0].splitlines()[1:]) + '''</h3></span></div><div class="content"><center><table><th>Métricas oficiais</th><tr><td><pre>'''+metrics+'''</pre></td></tr></table><br>''' + sentence_accuracy + '''<br>''' + resultados + '''</center></div><!--div class="tab"><button class="tablinks" onclick="openCity(event, 'Dados')">Métricas oficiais</button><button class="tablinks" onclick="openCity(event, 'Matriz')">Matriz de confusão</button></div><div class="tabcontent" id="Matriz"--><pre><table id="t01">''')

		tiposy = dict()
		tiposx = dict()
		for i, linha in enumerate("\n".join(matriz.split('\n\n')[1:]).split('#!$$')[0].split('\n')[2:-1]):
				tiposy[i+2] = linha.split(' ')[0]
		for i, coluna in enumerate("\n".join(matriz.split('\n\n')[1:]).split('#!$$')[0].split('\n')[0].split()[1:-1]):
				tiposx[i+1] = coluna
		y = 0

		linha_html = ""
		for linha in "\n".join(matriz.split('\n\n')[1:]).split('#!$$')[0].split('\n'):
				if linha.strip() != '':
						linha_html += '<tr><td>' + linha.split(' ')[0] + '</td>'
						if y == 0 or y == 1:
								for x, coluna in enumerate(linha.split()[1:]):
										#linha_html += '&#09;' + coluna
										linha_html += '<td>' + coluna + '</td>'
								y += 1
						elif y < len(tiposy):
								for x, coluna in enumerate(linha.split()[1:-1]):
										#linha_html += '&#09;' + '<a href="' + output + '_html/' + tiposy[y] + '-' + tiposx[x+1] + '.html">' + coluna + '</a>'
										linha_html += '<td>' + '<a href="' + output + '_html/' + tiposy[y] + '-' + tiposx[x+1] + '.html">' + coluna + '</a>' + '</td>'
								y += 1
								#linha_html += '&#09;' + linha.split()[-1]
								linha_html += '<td>' + linha.split()[-1] + '</td>'
						elif y == len(tiposy):
								for x, coluna in enumerate(linha.split()[1:]):
										#linha_html += '&#09;' + coluna
										linha_html += '<td>' + coluna + '</td>'
						linha_html += '</tr>'

		html.append(linha_html + '</table></pre>')

		solitários = dict()
		for i, grupo in enumerate(matriz.split('#!$$')[1:]):
				grupo = [x for x in grupo.splitlines() if x]
				html.append('<div class="container"><b>' + grupo[0] + ' (' + str(len(grupo[1:])) + ''')</b> <input type="button" id="botao''' + str(i) + '''" value="Mostrar" onClick="ativa('solitary''' + str(i) + '''', 'botao''' + str(i) + '''')" class="btn-gradient blue mini"><br>''')
				html.append("<div id='solitary" + str(i) + "' style='display:none'>")
				for linha in grupo[1:]:
						if linha.strip() != '':
								html.append(linha)
				html.append("</div></div>")

		sentenças = dict()
		for sentença in ud1:
				sentença_id = ''
				tamanho_sentença = 0
				for linha in sentença:
						if '# text = ' in linha:
								sentença_header = linha
						if '# sent_id = ' in linha:
								sentença_id = linha
						if isinstance(linha, list):
								tamanho_sentença += 1
				for subsentença in ud2:
						subsentença_correta = False
						tamanho_subsentença = 0
						for sublinha in subsentença:
								if '# text = ' in sublinha and sublinha == sentença_header:
										subsentença_correta = True
								if sentença_id == '' and '# sent_id = ' in sublinha:
										sentença_id = sublinha
								if isinstance(sublinha, list):
										tamanho_subsentença += 1
						if subsentença_correta and tamanho_sentença == tamanho_subsentença:
								sentença_limpo = [x for x in sentença if isinstance(x, list)]
								subsentença_limpo = [x for x in subsentença if isinstance(x, list)]
								sentença_limpo_string = [x for x in sentença if isinstance(x, list)]
								subsentença_limpo_string = [x for x in subsentença if isinstance(x, list)]
								for l, linha in enumerate(sentença_limpo_string):
										if isinstance(linha, list):
												sentença_limpo_string[l] = "&#09;".join(sentença_limpo_string[l])
								sentença_limpo_string = "\n".join(sentença_limpo_string)
								for l, linha in enumerate(subsentença_limpo_string):
										if isinstance(linha, list):
												subsentença_limpo_string[l] = "&#09;".join(subsentença_limpo_string[l])
								subsentença_limpo_string = "\n".join(subsentença_limpo_string)
								for k in range(len(sentença_limpo)):
										coluna1 = sentença_limpo[k][col-1]
										coluna2 = subsentença_limpo[k][col-1]
										palavra = sentença_limpo[k][1]
										if not coluna1 + '-' + coluna2 in sentenças:
												sentenças[coluna1 + '-' + coluna2] = [(sentença_id, re.sub(r'\b(' + re.escape(palavra) + r')\b', '<b>' + palavra +'</b>', sentença_header), sentença_limpo_string.replace("&#09;".join(sentença_limpo[k]), '<b>' + "&#09;".join(sentença_limpo[k]) + '</b>'), subsentença_limpo_string.replace("&#09;".join(subsentença_limpo[k]), '<b>' + "&#09;".join(subsentença_limpo[k]) + '</b>'))]
										else: sentenças[coluna1+'-'+coluna2].append((sentença_id, re.sub(r'\b(' + re.escape(palavra) + r')\b', '<b>' + palavra + '</b>', sentença_header), sentença_limpo_string.replace("&#09;".join(sentença_limpo[k]), '<b>' + "&#09;".join(sentença_limpo[k]) + '</b>'), subsentença_limpo_string.replace("&#09;".join(subsentença_limpo[k]), '<b>' + "&#09;".join(subsentença_limpo[k]) + '</b>')))

		open(output + '.html', 'w', encoding=codificação).write("<br>".join(html).replace('\n','<br>') + '''</div></div></body></html>

<script>
function ativa(nome, botao){
var div = document.getElementById(nome)
if (div.style.display == 'none') {
document.getElementById(botao).value='Esconder'
div.style.display = 'block'
} else {
div.style.display = 'none'
document.getElementById(botao).value='Mostrar'
}
}
function carregar_version(){
var link_combination = document.getElementById("carregar_edit").value.split("/")
window.location = window.location.href.split(".html")[0] + "_html/" + link_combination[link_combination.length-1].split("?")[0] + "?" + document.getElementById("carregar_edit").value.split("?")[1]
}
function openCity(evt, cityName) {
	// Declare all variables
	var i, tabcontent, tablinks;

	// Get all elements with class="tabcontent" and hide them
	tabcontent = document.getElementsByClassName("tabcontent");
	for (i = 0; i < tabcontent.length; i++) {
		tabcontent[i].style.display = "none";
	}

	// Get all elements with class="tablinks" and remove the class "active"
	tablinks = document.getElementsByClassName("tablinks");
	for (i = 0; i < tablinks.length; i++) {
		tablinks[i].className = tablinks[i].className.replace(" active", "");
	}

	// Show the current tab, and add an "active" class to the button that opened the tab
	document.getElementById(cityName).style.display = "block";
	evt.currentTarget.className += " active";
}
</script>''')

		#Páginas independentes
		for combinação in sentenças:
				html = ['<html><form><head><meta charset="'+codificação+'" name="viewport" content="width=device-width, initial-scale=1.0" /><style>input[name=maior] { width: 400; }</style><link href="../style.css" rel="stylesheet" type="text/css"><link href="http://fonts.googleapis.com/css?family=Lato" rel="stylesheet" type="text/css"></head><body onLoad="carregar()"><div class="header">'] #<form action="../matriz_cgi.py?output='+output+'&combination='+combinação+'&encoding='+codificação+'" method="post">
				html.append('<h1>'+output+'</h1><br><span id="topo"><h3>' + matriz.split('\n\n')[0] + '</span></h3></div><div class="content"><h3><a href="../' + output + '.html">Voltar</a></h3>')
				if not os.path.isdir(output + '_html'):
						os.mkdir(output + '_html')
				html.append('<h1><span id="combination">' + combinação + '</span> (' + str(len(sentenças[combinação])) + ')</h1><!--hr--><br>' + ''' <!--input type="button" onclick="enviar('2')" id="salvar_btn" class="btn-gradient orange mini" style="margin-left:0px" value="Gerar link para a versão atual"--> <input type="button" class="btn-gradient green mini" onclick="copiar_frases()" id="copiar_btn" value="Copiar sent_id das frases" style="margin-left:0px"> <input id="link_edit2" type="text" style="display:none"> <div id="gerado2" style="display:none"><b>Link gerado!</b></div><br><br>''')

				carregamento_comment = list()
				carregamento_check = list()
				for i, sentença in enumerate(sentenças[combinação]):
						for word in sentença[1].split():
							if "<b>" in sentença[1]:
								negrito = sentença[1].split("<b>")[1].split("</b>")[0]
							else:
								negrito = ".*"
								#print(negrito)
								#exit()

						#checar pai
						pais = ""
						#if combinação.split("-")[0] == combinação.split("-")[1]:
						pre_1 = estrutura_ud.Sentence()
						pre_1.build(wb.unescape(sentença[2]))
						pre_2 = estrutura_ud.Sentence()
						pre_2.build(wb.unescape(sentença[3]))
						caixa = sentença[1]
						for t, token in enumerate(pre_1.tokens):
							if "<b>" in token.to_str():
								if token.dephead != pre_2.tokens[t].dephead:
									caixa = re.sub(r"\b" + re.escape(token.head_token.word) + r"\b", "<font color=green>" + token.head_token.word + "</font>", caixa)
									caixa = re.sub(r"\b" + re.escape(pre_2.tokens[t].head_token.word) + r"\b", "<font color=red>" + pre_2.tokens[t].head_token.word + "</font>", caixa)
									pais = '<h3><font color="red">PAIS DIFERENTES</font></h3>'
								break

						carregamento_check.append('check1_'+str(i))
						carregamento_check.append('check2_'+str(i))
						carregamento_comment.append('comment'+str(i))
						html.append('<div class="container"><input type="hidden" name="negrito" value="' + negrito + '">' + str(i+1) + ' / ' + str(len(sentenças[combinação])) + '<br><br>' + sentença[0] + '<br><br>' + '''<input type="hidden" name="copiar_id" id="''' + str(i) + '''" value="''' + sentença[0].replace('/BOLD','').replace('@BOLD','').replace('@YELLOW/', '').replace('@PURPLE/', '').replace('@BLUE/', '').replace('@RED/', '').replace('@CYAN/', '').replace('/FONT', '') + '''">''' + caixa + '<!--br><br><input type="checkbox" style="margin-left:0px" id="check1_'+str(i)+'" >' + combinação.split('-')[0] + ' <input type="checkbox" id="check2_'+str(i)+'" >' + combinação.split('-')[1] + ' - Comentários: <input type="text" id="comment'+str(i)+'" name="maior" -->')
						html.append('''<br><input type="button" id="botao1''' + combinação + str(i) + '''" style="margin-left:0px" value="Mostrar PRINCIPAL" onClick="ativa1('sentence1''' + combinação + str(i) + '''', 'botao1''' + combinação + str(i) + '''')" > <input type="button" id="botao2''' + combinação + str(i) + '''" value="Mostrar PREVISTO" onClick="ativa2('sentence2''' + combinação + str(i) + '''', 'botao2''' + combinação + str(i) + '''')">''' + pais)
						html.append("<div id='sentence1" + combinação + str(i) + "' style='display:none'><b><br>PRINCIPAL:</b>")
						html.append("<pre>" + sentença[2].replace('<','&lt;').replace('>','&gt;').replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>") + "</pre></div><div id='sentence2" + combinação + str(i) + "' style='display:none'><br><b>PREVISTO:</b>")
						html.append("<pre>" + sentença[3].replace('<','&lt;').replace('>','&gt;').replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>") + '</pre></div></div>')

				html = "<br>".join(html).replace('\n','<br>') + '''<br><!--input type="button" class="btn-gradient orange" onclick="enviar('1')" id="salvar_btn" value="Gerar link para a versão atual" style="margin-left:0px"--> <input id="link_edit1" type="text" style="display:none"> <div id="gerado1" style="display:none"><b>Link gerado!</b></div><br><h3><a href="../''' + output + '''.html">Voltar</a></h3></div></body></form></html>

<script>
function escapeRegExp(string) {
	return string.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&').replace('&amp;', '.'); // $& means the whole matched string
}
String.prototype.rsplit = function(sep, maxsplit) {
	var split = this.split(sep);
	return maxsplit ? [ split.slice(0, -maxsplit).join(sep) ].concat(split.slice(-maxsplit)) : split;
}
function copiar_frases(){
	document.getElementById("link_edit2").value = "";
	document.getElementById("link_edit2").style.display = "inline";
	
	var sentids, i, negritos;
	sentids = document.getElementsByName("copiar_id");
	negritos = document.getElementsByName("negrito");
	for (i = 0; i < sentids.length; i++) {
		document.getElementById("link_edit2").value = document.getElementById("link_edit2").value + "^" + sentids[i].value + "$(.*\\\\n)*.*\\\\t" + negritos[i].value + "\\\\t|";
	}
	document.getElementById("link_edit2").value = document.getElementById("link_edit2").value.rsplit('|',1)[0];
}
function carregar_version(){
window.location = window.location.href.split("?")[0] + "?" + document.getElementById("carregar_edit").value.split("?")[1]
}
function ativa1(nome, botao){
var div = document.getElementById(nome)
if (div.style.display == 'none') {
document.getElementById(botao).value='Esconder PRINCIPAL'
div.style.display = 'block'
} else {
div.style.display = 'none'
document.getElementById(botao).value='Mostrar PRINCIPAL'
}
}
function ativa2(nome, botao){
var div = document.getElementById(nome)
if (div.style.display == 'none') {
document.getElementById(botao).value='Esconder PREVISTO'
div.style.display = 'block'
} else {
div.style.display = 'none'
document.getElementById(botao).value='Mostrar PREVISTO'
}
}
function gerado_false(id) {
document.getElementById("gerado"+id).style.display = "none"
}
'''
				script_onload = ['function carregar() {','let url_href = window.location.href','let url = new URL(url_href)']
				for item in carregamento_comment:
						script_onload.append('document.getElementById("'+item+'").value = url.searchParams.get("'+item+'")')
				for item in carregamento_check:
						script_onload.append('if (url.searchParams.get("'+item+'") == "true") { document.getElementById("'+item+'").checked = url.searchParams.get("'+item+'") }')
				script_onload.append('}')

				link = '?'
				script_enviar = ['''
function enviar(id) {
document.getElementById("gerado"+id).style.display = "inline"
setTimeout("gerado_false("+id+")", 1000)
document.getElementById("link_edit"+id).style.display = "inline"''']

				link = '?'
				for item in carregamento_comment:
						link += item + '=" + document.getElementById("' + item + '").value.replace(/\?/g, "~").replace(/\&/g, "~").replace(/\//g,"~") + "&'
				for item in carregamento_check:
						link += item + '=" + document.getElementById("' + item + '").checked + "&'

				script_enviar.append('document.getElementById("link_edit"+id).value = window.location.href.split("?")[0] + "' + link + '"')
				script_enviar.append('}')


				html += "\n".join(script_onload) + "\n".join(script_enviar) + '\n</script>'

				open(output + '_html/' + combinação + '.html', 'w', encoding=codificação).write(html)

#falta criar os htmls
def get_percentages(ud1, ud2, output, coluna):
	if not os.path.isdir("UAS"):
		os.mkdir("UAS")
	UAS = dict()

	with open(ud1, "r") as f:
		first = estrutura_ud.Corpus()
		first.build(f.read())	

	with open(ud2, "r") as f:
		second = estrutura_ud.Corpus()
		second.build(f.read())

	dicionario = {}
	for sentid, sentence in first.sentences.items():
		for t, token in enumerate(sentence.tokens):
			if not token.__dict__[feats[coluna].lower()] in dicionario:
				if coluna == 8:
					dicionario[token.__dict__[feats[coluna].lower()]] = [0, 0, 0, 0, 0]
					UAS[token.deprel] = dict()
				else:
					dicionario[token.__dict__[feats[coluna].lower()]] = [0, 0, 0]
			dicionario[token.__dict__[feats[coluna].lower()]][0] += 1
			if second.sentences[sentid].tokens[t].__dict__[feats[coluna].lower()] == token.__dict__[feats[coluna].lower()]:
				dicionario[token.__dict__[feats[coluna].lower()]][1] += 1
				if coluna == 8:
					if second.sentences[sentid].tokens[t].dephead == token.dephead:
						dicionario[token.deprel][2] += 1
					else:
						tok_first = token.head_token.upos
						tok_second = second.sentences[sentid].tokens[t].head_token.upos
						tok_first += "_L" if int(token.head_token.id) < int(token.id) else "_R"
						tok_second += "_L" if int(second.sentences[sentid].tokens[t].head_token.id) < int(second.sentences[sentid].tokens[t].id) else "_R"
						if tok_first + "/" + tok_second in UAS[token.deprel]:
							UAS[token.deprel][tok_first + "/" + tok_second]["qtd"] += 1
						else:
							UAS[token.deprel][tok_first + "/" + tok_second] = {"qtd": 1, "sentences": []}
						UAS[token.deprel][tok_first + "/" + tok_second]["sentences"].append([sentence, second.sentences[sentid], token, token.head_token, second.sentences[sentid].tokens[t].head_token, second.sentences[sentid].tokens[t]])

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
				#print(sentid)
	sentence_accuracy = "<table><tr><th>Acurácia por sentença</th></tr><tr><th>Sentenças comparáveis</th><th>Sentenças corretas</th><th>Número relativo</th></tr><tr><td>{0}</td><td>{1}</td><td>{2}</td></tr></table>".format(sent_accuracy[0], sent_accuracy[1], str((sent_accuracy[1]/sent_accuracy[0])*100) + "%")
	with open(output + "_sentence.txt", "w") as f:
		f.write(sentence_accuracy)

	if coluna == 8:
		csv = ["{0:20} {1:10} {2:10} {3:10} {4:10} {5:10}".format("DEPREL", "PRINCIPAL", "ACERTOS_DEPREL", "ACERTOS_DEPREL_DEPHEAD", "PORCENTAGEM_DEPREL", "PORCENTAGEM_DEPREL_DEPHEAD")]
		for classe in sorted(dicionario):
			dicionario[classe][3] = (dicionario[classe][1] / dicionario[classe][0]) * 100
			dicionario[classe][4] = (dicionario[classe][2] / dicionario[classe][0]) * 100
			csv.append("{0:20} {1:10} {2:10} {3:10} {4:10} {5:10}".format(classe, str(dicionario[classe][0]), str(dicionario[classe][1]), str(dicionario[classe][2]), str(dicionario[classe][3]) + "%", str(dicionario[classe][4]) + "%"))
	else:
		csv = ["{0:20} {1:10} {2:10} {3:10}".format(feats[coluna], "PRINCIPAL", "ACERTOS", "PORCENTAGEM")]
		for classe in sorted(dicionario):
			dicionario[classe][2] = (dicionario[classe][1] / dicionario[classe][0]) * 100
			csv.append("{0:20} {1:10} {2:10} {3:10}".format(classe, str(dicionario[classe][0]), str(dicionario[classe][1]), str(dicionario[classe][2]) + "%"))

	with open(output + "_results.txt", "w") as f:
		f.write("\n".join(csv))

	for deprel in UAS:
		total = 0
		for x in UAS[deprel].values(): total += x["qtd"]
		escrever = ["<tr><td>{0}</td><td>{1}</td><td>{2}</td><td><a href='./{4}_{0}_{1}.html'>{3}%</a></td></tr>".format(padrao.split("/")[0], padrao.split("/")[1], quantidade["qtd"], (quantidade["qtd"]/total)*100, deprel) for padrao, quantidade in sorted(UAS[deprel].items(), key=lambda x: x[1]["qtd"], reverse=True)]
		with open("UAS/" + deprel + ".html", "w") as f:
			f.write("<body style='margin:20px'>" + str(dicionario[deprel][3] - dicionario[deprel][4]) + '% "' + deprel + '" com dephead divergentes<br><br><head><link href="../style.css" rel="stylesheet" type="text/css"></head>' + "<table><tr><td colspan='4'>Distribuição dos erros</td></tr><tr><th>PRINCIPAL</th><th>SECUNDÁRIO</th><th>N</th><th>%</th></tr>" + "\n".join(escrever) + "<tr><td colspan='2'>Total</td><td>" + str(total) + "</td></tr></table>")

		for padrao in UAS[deprel]:
			escrever = "<body style='margin:20px;'>DEPREL: " + deprel + "\n<br>PRINCIPAL HEAD: " + padrao.split("/")[0] + "\n<br>SECUNDÁRIO HEAD: " + padrao.split("/")[1] + '''\n<br><input type=button value='Copiar sent_id das frases' onclick='copiar_frases()'> <input id='input' style='display:none'><br><br>'''
			for n, sentence in enumerate(UAS[deprel][padrao]["sentences"]):
				escrever += str(n+1) + " / " + str(len(UAS[deprel][padrao]["sentences"]))
				escrever += "\n<br><input type=hidden name=copiar_id value='"+sentence[0].sent_id.replace("'", "\\'")+"'># sent_id = " + sentence[0].sent_id
				text = sentence[0].text
				text = re.sub(r"\b" + re.escape(sentence[2].word) + r"\b", "<b>" + sentence[2].word + "</b>", text)
				escrever += "\n<input type=hidden name=negrito value='"+sentence[2].word.replace("'", "\\'")+"'>"
				text = re.sub(r"\b" + re.escape(sentence[3].word) + r"\b", "<font color=green>" + sentence[3].word + "</font>", text)
				text = re.sub(r"\b" + re.escape(sentence[4].word) + r"\b", "<font color=red>" + sentence[4].word + "</font>", text)
				escrever += "\n<br># text = " + text
				escrever += '''\n<br><input type='button' id="but_'''+str(n)+'''" value='Mostrar PRINCIPAL' onclick='if(document.getElementById("pre_'''+str(n)+'''").style.display == "none") { document.getElementById("pre_''' + str(n) + '''").style.display = "block"; document.getElementById("but_'''+str(n)+'''").value = "Esconder PRINCIPAL"; } else { document.getElementById("pre_''' + str(n) + '''").style.display = "none"; document.getElementById("but_'''+str(n)+'''").value = "Mostrar PRINCIPAL"; }\'>'''
				escrever += '''\n<input type='button' id="but2_'''+str(n)+'''" value='Mostrar SECUNDÁRIO' onclick='if(document.getElementById("pre2_'''+str(n)+'''").style.display == "none") { document.getElementById("pre2_''' + str(n) + '''").style.display = "block"; document.getElementById("but2_'''+str(n)+'''").value = "Esconder SECUNDÁRIO"; } else { document.getElementById("pre2_''' + str(n) + '''").style.display = "none"; document.getElementById("but2_'''+str(n)+'''").value = "Mostrar SECUNDÁRIO"; }\'>'''
				escrever += '\n<pre id=pre_' + str(n) + ' style="display:none">PRINCIPAL<br>' + sentence[0].to_str().replace(sentence[2].to_str(), "<b>" + sentence[2].to_str() + "</b>").replace(sentence[3].to_str(), "<font color=green>" + sentence[3].to_str() + "</font>") + '</pre>'
				escrever += '\n<pre id=pre2_' + str(n) + ' style="display:none">SECUNDÁRIO<br>' + sentence[1].to_str().replace(sentence[5].to_str(), "<b>" + sentence[5].to_str() + "</b>").replace(sentence[4].to_str(), "<font color=red>" + sentence[4].to_str() + "</font>") + '</pre>'
				escrever += "\n<hr>"
			escrever += '''
	<script>
	String.prototype.rsplit = function(sep, maxsplit) {
	var split = this.split(sep);
	return maxsplit ? [ split.slice(0, -maxsplit).join(sep) ].concat(split.slice(-maxsplit)) : split;
	}

	function copiar_frases(){
	document.getElementById("input").value = "";
	document.getElementById("input").style.display = "inline";
	
	var sentids, i, negritos;
	sentids = document.getElementsByName("copiar_id");
	negritos = document.getElementsByName("negrito");
	for (i = 0; i < sentids.length; i++) {
		document.getElementById("input").value = document.getElementById("input").value + "^# sent_id = " + sentids[i].value + "$(.*\\\\n)*.*" + negritos[i].value + "|";
	}
	document.getElementById("input").value = document.getElementById("input").value.rsplit('|',1)[0];
	}
	</script>'''
			with open("UAS/" + deprel + "_" + padrao.replace("/", "_") + ".html", "w") as f:
				f.write(escrever)


def main(ud1, ud2, output, coluna = 4):
	conllu1 = LerUD(ud1)
	conllu2 = LerUD(ud2)
	conllu1Estruturado, conllu2Estruturado = estrutura_ud.Corpus(), estrutura_ud.Corpus()
	conllu1Estruturado.load(ud1)
	conllu2Estruturado.load(ud2)
	lista_conllu = get_list(conllu1Estruturado, conllu2Estruturado, coluna)
	lista_conllu1 = lista_conllu['matriz_1']
	lista_conllu2 = lista_conllu['matriz_2']
	pd.options.display.max_rows = None
	pd.options.display.max_columns = None
	pd.set_option('display.expand_frame_repr', False)
	saída = list()
	saída.append('Col ' + str(coluna)+': ' + feats[coluna])
	saída.append('PRINCIPAL: ' + ud1)
	saída.append('SECUNDÁRIO: ' + ud2 + '\n')
	saída.append(str(pd.crosstab(pd.Series(lista_conllu1), pd.Series(lista_conllu2), rownames=['UD[1]'], colnames=['UD[2]'], margins=True)))
	saída.append('\n')
	saída.append('#!$$ Sentenças de PRINCIPAL que não foram encontradas em SECUNDÁRIO:\n')
	for item in lista_conllu['solitários_1']:
			saída.append(item)

		#Output
	if ':' in output: codificação_saída = output.split(':')[1]
	else: codificação_saída = 'utf8'
	output = output.split(':')[0]

	get_percentages(ud1, ud2, output, coluna)

	#Gera os arquivos HTML
	gerar_HTML("\n".join(saída), conllu1, conllu2, coluna, output, codificação_saída)
	#Gera o arquivo "txt" (apenas a matriz)
	open(output, 'w', encoding=codificação_saída).write("\n".join(saída))

if __name__ == '__main__':
	número_de_argumentos_mínimo = 4

	if len(sys.argv) < número_de_argumentos_mínimo +1:
		print('uso: confusão.py PRINCIPAL.conllu:utf8 SECUNDARIO.conllu:utf8 saída.txt:utf8 coluna')
		print('Colunas:')
		for i in range(len(feats)):
				print(str(i+1) + ': ' + feats[i+1])
	elif len(sys.argv) >= número_de_argumentos_mínimo +1:
		main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]))
	else:
		print('Argumentos demais')
