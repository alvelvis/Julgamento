import sys
import os
import estrutura_ud
from pprint import pprint

partitions = sys.argv[2]

def main():
	adicionarAoLog(f"carregando {sys.argv[1]}.conllu")
	conlluVirgem = estrutura_ud.Corpus(recursivo=False)
	conlluVirgem.load(f"{sys.argv[1]}.conllu")

	listaDeIdsEmOrdem = [x.sent_id for x in conlluVirgem.sentences.values()]

	crossvalidation = Crossvalidation(listaDeIdsEmOrdem)
	crossvalidation.montarParticoes()

	listaPartitions = [x.rsplit("_", 1)[1] for x in os.listdir(".") if os.path.isdir(x) and "partition_" in x]
	checarPartitions(crossvalidation, listaPartitions, listaDeIdsEmOrdem)
	

def juntarPartitions(crossvalidation, listaPartitions, listaDeIdsEmOrdem):
	arquivoConlluCompletoAnotado = []
	for partition in sorted([int(x) for x in listaPartitions if x != "sobra"]):
		with open(f"partition_{partition}/MC_partition_{partition}/partition_{partition}_sistema.conllu", "r") as f:
			arquivoConlluCompletoAnotado.append([x for x in f.read().splitlines()])
			adicionarAoLog(f"partição {partition} acrescida ao corpus anotado")
	with open(f"partition_sobra/MC_partition_sobra/partition_sobra_sistema.conllu", "r") as f:
			arquivoConlluCompletoAnotado.append([x for x in f.read().splitlines()])
			adicionarAoLog(f"partição sobra acrescida ao corpus anotado")
	for a in range(len(arquivoConlluCompletoAnotado)):
		arquivoConlluCompletoAnotado[a] = "\n".join(arquivoConlluCompletoAnotado[a])
	arquivoConlluCompletoAnotado = "\n\n".join(arquivoConlluCompletoAnotado)
	corpusSemOrdem = estrutura_ud.Corpus(recursivo=False)
	corpusSemOrdem.build(arquivoConlluCompletoAnotado)
	corpusOrdem = []
	for sentOrdem in listaDeIdsEmOrdem:
		corpusOrdem.append(corpusSemOrdem.sentences[sentOrdem].to_str())
	corpus = estrutura_ud.Corpus(recursivo=False)
	corpus.build("\n\n".join(corpusOrdem))
	if not os.path.isdir(f"MC_{sys.argv[1]}"): os.mkdir(f"MC_{sys.argv[1]}")
	adicionarAoLog(f"salvando corpus anotado em MC_{sys.argv[1]}/{sys.argv[1]}_sistema.conllu")
	corpus.save(f"MC_{sys.argv[1]}/{sys.argv[1]}_sistema.conllu")
	os.system(f"cd MC_{sys.argv[1]}; mv {sys.argv[1]}_sistema.conllu ../../; cd ../../; mv {sys.argv[1]}_inProgress {sys.argv[1]}_success 2>&1 | tee -a ../log.txt")
	os._exit(1)
	adicionarAoLog(f"finalizado. Resultado em MC_{sys.argv[1]}/{sys.argv[1]}.html")

def checarPartitions(crossvalidation, listaPartitions, listaDeIdsEmOrdem):
	while True:
		ok = 0
		faltaTreinar = None
		for partition in listaPartitions:
			if not os.path.isfile(f"partition_{partition}/MC_partition_{partition}/partition_{partition}_sistema.conllu"):
				adicionarAoLog(f"partição {partition} não foi treinada ainda")
				faltaTreinar = partition
			else:
				ok += 1
				adicionarAoLog(f"[{ok}/{len(listaPartitions)}] partição {partition} já foi treinada!")
		if ok == len(listaPartitions):
			break
		else:
			treinarPartition(faltaTreinar, crossvalidation)
	adicionarAoLog(f'{ok} partições (todas) treinadas. Juntando arquivo conllu anotado :)')
	juntarPartitions(crossvalidation, listaPartitions, listaDeIdsEmOrdem)

def treinarPartition(partition, crossvalidation):
	adicionarAoLog(f'preparando partição {partition}')
	os.system(f"sh crossvalidation_udpipe.sh partition_{partition} {sys.argv[2]} 2>&1 | tee -a log.txt")
	adicionarAoLog(f'partição {partition} treinada com sucesso!')

def adicionarAoLog(texto):
	with open("log.txt", "a") as f:
		f.write(texto + '\n')
	with open(f"../{sys.argv[1]}_inProgress", "a") as f:
		f.write(texto + '\n')
	print(texto)


class Crossvalidation:

	def __init__(self, listaDeIdsEmOrdem):
		self.listaDeIdsEmOrdem = listaDeIdsEmOrdem
		self.dicionarioDeParticoesOriginal = {}
		self.dicionarioDeNovasParticoes = {
			'sobra': {
				partitions + '-train.txt': [],
				partitions + '-test.txt': [],
				partitions + '-dev.txt': [],
			}
		}
		self.quantidadeDeTests = 0
		self.idJaTemPartition = []
		self.quantidadeSentTest = 0


	def montarParticoes(self):
		adicionarAoLog("distribuição das partições originais:")
		self.dicionarioDeParticoesOriginal = {x: [] for x in os.listdir(".") if ".txt" in x and x != "log.txt"}
		for partition in self.dicionarioDeParticoesOriginal:
			with open(partition, "r") as f:
				self.dicionarioDeParticoesOriginal[partition] = f.read().strip().splitlines()

			adicionarAoLog(f" {partition}: {len(self.dicionarioDeParticoesOriginal[partition])}")

		for partition in [partitions + '-dev.txt', partitions + '-train.txt', partitions + '-test.txt']:
			if not partition in self.dicionarioDeParticoesOriginal:
				adicionarAoLog(f"partições incorretas: {partition} não encontrada")
				exit()

		self.dicionarioDeParticoesOriginal[partitions + '-train.txt'] += self.dicionarioDeParticoesOriginal[partitions + '-dev.txt']
		self.dicionarioDeParticoesOriginal[partitions + '-dev.txt'] = []
		self.quantidadeDeTests = int(str((len(self.dicionarioDeParticoesOriginal[partitions + '-train.txt']) + len(self.dicionarioDeParticoesOriginal[partitions + '-test.txt'])) / len(self.dicionarioDeParticoesOriginal[partitions + '-test.txt'])).split(".")[0])
		self.quantidadeSentTest = len(self.dicionarioDeParticoesOriginal[partitions + '-test.txt']) if len(self.dicionarioDeParticoesOriginal[partitions + '-test.txt']) % 2 == 0 else len(self.dicionarioDeParticoesOriginal[partitions + '-test.txt']) + 1

		adicionarAoLog(f"quantidade de tests sendo feitos: {self.quantidadeDeTests} ({len(self.dicionarioDeParticoesOriginal[partitions + '-test.txt'])} sentenças cada) + sobra ({len(self.listaDeIdsEmOrdem) - self.quantidadeDeTests * len(self.dicionarioDeParticoesOriginal[partitions + '-test.txt'])} sentenças)")

		for i in range(self.quantidadeDeTests):
			qtdCP = 0
			qtdCF = 0
			
			if not i in self.dicionarioDeNovasParticoes: self.dicionarioDeNovasParticoes[i] = {
				partitions + '-test.txt': [],
				partitions + '-train.txt': [],
				partitions + '-dev.txt': [],
				}

			for sent_id in self.listaDeIdsEmOrdem:
				if len(self.dicionarioDeNovasParticoes[i][partitions + '-test.txt']) < self.quantidadeSentTest:
					if not sent_id in self.idJaTemPartition and (('CP' in sent_id and qtdCP < self.quantidadeSentTest/2) or ('CF' in sent_id and qtdCF < self.quantidadeSentTest/2)):
						self.dicionarioDeNovasParticoes[i][partitions + '-test.txt'] += [sent_id]
						self.idJaTemPartition += [sent_id]
						if 'CP' in sent_id: qtdCP += 1
						if 'CF' in sent_id: qtdCF += 1
					else:
						self.dicionarioDeNovasParticoes[i][partitions + '-train.txt'] += [sent_id]
				else:
					self.dicionarioDeNovasParticoes[i][partitions + '-train.txt'] += [sent_id]

		for sent_id in self.listaDeIdsEmOrdem:
			if not sent_id in self.idJaTemPartition:
				self.dicionarioDeNovasParticoes['sobra'][partitions + '-test.txt'] += [sent_id]
			else:
				self.dicionarioDeNovasParticoes['sobra'][partitions + '-train.txt'] += [sent_id]

		for partition, tipo in self.dicionarioDeNovasParticoes.items():
			adicionarAoLog(f"preparando pasta: partition_{partition}, {len(tipo[partitions + '-test.txt'])} {partitions}-test, {len(tipo[partitions+'-train.txt'])} {partitions}-train")
			if not os.path.isdir(f"partition_{partition}"): os.mkdir(f"partition_{partition}")
			for nome in tipo:
				with open(f"partition_{partition}/{nome}", "w") as f:
					f.write("\n".join(tipo[nome]))
			os.system(f"cp {sys.argv[1]}.conllu partition_{partition}/partition_{partition}.conllu")

main()