import json
import logging
from pathlib import Path
import re

class GeradorJSON:
    def __init__(self, config_path=None, pasta_txt='./txt_bruto', pasta_destino='./json_final'):
        # Não carrega config aqui, será carregado por arquivo
        self.config = None
        self.config_path = config_path
        self.pasta_txt = Path(pasta_txt)
        self.pasta_destino = Path(pasta_destino)
        self.pasta_destino.mkdir(exist_ok=True)
        
    def encontrar_config(self, nome_arquivo_txt=None):
        """Encontra o config apropriado baseado no arquivo TXT sendo processado"""
        config_dir = Path('./configs')
        if not config_dir.exists():
            logging.error("Pasta configs não encontrada")
            exit(1)
            
        config_files = list(config_dir.glob('*.json'))
        if not config_files:
            logging.error("Nenhum arquivo JSON encontrado em ./configs/")
            exit(1)
        
        # Se não foi passado nome de arquivo, retorna o primeiro (comportamento antigo)
        if nome_arquivo_txt is None:
            config_path = config_files[0]
            logging.info(f"Usando configuração padrão: {config_path}")
            return config_path
        
        # Remove extensão do arquivo TXT e normaliza
        nome_arquivo_sem_ext = Path(nome_arquivo_txt).stem
        nome_arquivo_limpo = self.normalizar_nome(nome_arquivo_sem_ext)
        
        # Lista para armazenar correspondências encontradas (config, score de correspondência, nome)
        correspondencias = []
        
        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_temp = json.load(f)
                
                # Verifica se algum arquivo definido no config corresponde ao arquivo TXT
                if 'files' in config_temp:
                    for tipo, info in config_temp['files'].items():
                        if 'path' in info:
                            nome_xlsx = Path(info['path']).stem
                            nome_xlsx_limpo = self.normalizar_nome(nome_xlsx)
                            
                            # Calcula score de correspondência (quanto maior, melhor)
                            score = 0
                            
                            # Correspondência exata = score máximo
                            if nome_xlsx_limpo == nome_arquivo_limpo:
                                score = 100
                            # Nome do arquivo TXT começa com o nome do XLSX (correspondência muito forte)
                            # Ex: "custopagina1" começa com "custo"
                            elif nome_arquivo_limpo.startswith(nome_xlsx_limpo):
                                # Score baseado na proporção: quanto maior a parte correspondente, melhor
                                # Prioriza correspondências mais longas e específicas
                                proporcao = len(nome_xlsx_limpo) / len(nome_arquivo_limpo) if nome_arquivo_limpo else 0
                                score = 90 + (proporcao * 10)  # Entre 90-100
                            # Nome do XLSX contém o nome do arquivo TXT (correspondência fraca, mas possível)
                            elif nome_xlsx_limpo.startswith(nome_arquivo_limpo):
                                proporcao = len(nome_arquivo_limpo) / len(nome_xlsx_limpo) if nome_xlsx_limpo else 0
                                score = 70 + (proporcao * 10)  # Entre 70-80
                            # Nome do config está contido no nome do arquivo (correspondência média)
                            elif nome_xlsx_limpo in nome_arquivo_limpo:
                                # Penaliza correspondências muito curtas (ex: "custo" em "custobutzkepagina1")
                                # Prioriza correspondências mais longas e específicas
                                proporcao = len(nome_xlsx_limpo) / len(nome_arquivo_limpo) if nome_arquivo_limpo else 0
                                # Se a correspondência é muito curta comparada ao total, reduz o score
                                if proporcao < 0.3:  # Menos de 30% do nome
                                    score = 30  # Score baixo para correspondências genéricas
                                else:
                                    score = 50 + (proporcao * 20)  # Entre 50-70
                            
                            if score > 0:
                                correspondencias.append((config_file, score, nome_xlsx, tipo))
            except Exception as e:
                logging.warning(f"Erro ao ler config {config_file}: {e}")
                continue
        
        # Se encontrou correspondências, retorna a de maior score
        if correspondencias:
            # Ordena por score (maior primeiro), depois por tamanho do nome (mais específico primeiro)
            correspondencias.sort(key=lambda x: (x[1], len(x[2])), reverse=True)
            melhor_config, melhor_score, melhor_nome, melhor_tipo = correspondencias[0]
            
            logging.info(f"Arquivo '{nome_arquivo_txt}' corresponde ao config '{melhor_config.name}' "
                        f"(arquivo: '{melhor_nome}' tipo: {melhor_tipo}, score: {melhor_score:.1f})")
            
            # Se há múltiplas correspondências, avisa
            if len(correspondencias) > 1:
                logging.warning(f"Encontradas {len(correspondencias)} correspondências, usando a melhor: {melhor_config.name} (score: {melhor_score:.1f})")
                for cfg, sc, nm, tp in correspondencias[1:3]:  # Mostra as 2 próximas
                    logging.debug(f"  Alternativa: {cfg.name} - {nm} ({tp}) - score: {sc:.1f}")
            
            return melhor_config
        
        # Se não encontrou correspondência, usa o primeiro config (fallback)
        logging.warning(f"Não encontrou config específico para '{nome_arquivo_txt}', usando '{config_files[0].name}' como fallback")
        return config_files[0]
        
    def carregar_config(self, config_path):
        config_path = Path(config_path)
        if not config_path.exists():
            logging.error(f"Arquivo de configuração não encontrado: {config_path}")
            logging.error("Verifique se o caminho está correto")
            exit(1)
            
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def normalizar_nome(self, nome):
        return re.sub(r'[^a-zA-Z0-9]', '', nome.lower().strip())
    
    def comparar_nomes(self, nome1, nome2):
        return self.normalizar_nome(nome1) == self.normalizar_nome(nome2)
    
    def identificar_tipo_arquivo(self, nome_arquivo_txt, config=None):
        """Identifica se o arquivo TXT é de custo ou venda baseado no nome e no config"""
        if config is None:
            config = self.config
        
        if config is None:
            # Fallback: tenta identificar pelo nome
            nome_arquivo_limpo = self.normalizar_nome(nome_arquivo_txt)
            if 'custo' in nome_arquivo_limpo:
                return 'custo'
            elif 'venda' in nome_arquivo_limpo:
                return 'venda'
            return None
        
        nome_arquivo_limpo = self.normalizar_nome(nome_arquivo_txt)
        
        # Verifica no config quais arquivos existem
        if 'files' in config:
            for tipo, info in config['files'].items():
                if 'path' in info:
                    # Pega o nome do arquivo XLSX do config e normaliza
                    nome_xlsx = Path(info['path']).stem  # Remove .xlsx
                    nome_xlsx_limpo = self.normalizar_nome(nome_xlsx)
                    
                    # Verifica se o nome do arquivo TXT contém o nome do arquivo do config
                    # Ex: "Custo_Página 1.txt" deve corresponder a "Custo.xlsx"
                    if nome_xlsx_limpo in nome_arquivo_limpo or nome_arquivo_limpo in nome_xlsx_limpo:
                        logging.info(f"Arquivo {nome_arquivo_txt} identificado como {tipo}")
                        return tipo
        
        # Fallback: tenta identificar pelo nome
        if 'custo' in nome_arquivo_limpo:
            return 'custo'
        elif 'venda' in nome_arquivo_limpo:
            return 'venda'
        
        logging.warning(f"Arquivo {nome_arquivo_txt} não corresponde a nenhum tipo no config")
        return None
    
    def encontrar_valor_registro(self, linhas, coluna_procurada):
        for linha in linhas:
            if ':' in linha:
                coluna, valor = linha.split(':', 1)
                if self.comparar_nomes(coluna.strip(), coluna_procurada):
                    return valor.strip()
        return ""
    
    def obter_colunas_cores_do_config(self, tipo_arquivo, log_fallback=True):
        """Obtém as colunas de cores do config (coluna COR com sourceColumn como lista) para o tipo específico ou fallback"""
        colunas_cores = []
        if 'columnMapping' in self.config:
            # Primeiro tenta encontrar para o tipo específico
            for mapeamento in self.config['columnMapping']:
                if (mapeamento.get('sourceFile') == tipo_arquivo and
                    mapeamento.get('gabaritoColumn') == 'COR' and 
                    isinstance(mapeamento.get('sourceColumn'), list)):
                    colunas_cores = mapeamento['sourceColumn']
                    break
            
            # Se não encontrou para o tipo específico, tenta o outro tipo como fallback
            if not colunas_cores:
                tipo_fallback = 'venda' if tipo_arquivo == 'custo' else 'custo'
                for mapeamento in self.config['columnMapping']:
                    if (mapeamento.get('sourceFile') == tipo_fallback and
                        mapeamento.get('gabaritoColumn') == 'COR' and 
                        isinstance(mapeamento.get('sourceColumn'), list)):
                        colunas_cores = mapeamento['sourceColumn']
                        if log_fallback:
                            logging.info(f"Usando colunas de cores do tipo {tipo_fallback} como fallback para {tipo_arquivo}")
                        break
            
            # Se ainda não encontrou, tenta qualquer tipo
            if not colunas_cores:
                for mapeamento in self.config['columnMapping']:
                    if (mapeamento.get('gabaritoColumn') == 'COR' and 
                        isinstance(mapeamento.get('sourceColumn'), list)):
                        colunas_cores = mapeamento['sourceColumn']
                        if log_fallback:
                            logging.info(f"Usando colunas de cores de qualquer tipo como fallback")
                        break
        return colunas_cores
    
    def extrair_variacoes_cores(self, linhas, tipo_arquivo):
        """Extrai as variações de cores e preços do registro usando config para o tipo específico ou fallback"""
        variacoes = []
        # Obtém as colunas de cores do config para este tipo de arquivo (sem log repetido)
        colunas_cores = self.obter_colunas_cores_do_config(tipo_arquivo, log_fallback=False)
        
        # Se não encontrou no config, retorna vazio (não usa hardcode)
        if not colunas_cores:
            if tipo_arquivo:
                logging.debug(f"Colunas de cores não encontradas no config para a coluna COR do tipo {tipo_arquivo}")
            return variacoes
        
        for coluna_cor in colunas_cores:
            valor = self.encontrar_valor_registro(linhas, coluna_cor)
            if valor and valor != "0" and valor != "":
                # Limpa o nome da cor (remove quebras de linha)
                cor_limpa = coluna_cor.replace('\n', ' ').strip()
                variacoes.append({
                    "nome_cor": cor_limpa,
                    "preco": valor
                })
        
        return variacoes
        
    def obter_colunas_source_mapping(self, tipo_arquivo=None):
        """Obtém todas as colunas sourceColumn usadas no columnMapping"""
        colunas_source = set()
        
        if 'columnMapping' not in self.config:
            return colunas_source
        
        # Filtra por tipo de arquivo se especificado
        for mapeamento in self.config['columnMapping']:
            # Se tipo_arquivo foi especificado, filtra apenas mapeamentos desse tipo
            if tipo_arquivo and mapeamento.get('sourceFile') != tipo_arquivo:
                continue
            
            source_column = mapeamento.get('sourceColumn')
            
            # Se sourceColumn for uma lista (como no caso de COR)
            if isinstance(source_column, list):
                for col in source_column:
                    colunas_source.add(col)
            # Se sourceColumn for uma string e não for __EMPTY__
            elif isinstance(source_column, str) and source_column != "__EMPTY__":
                colunas_source.add(source_column)
        
        return colunas_source
    
    def registro_eh_header(self, linhas, colunas_source):
        """Verifica se um registro é um header (contém APENAS colunas source do mapeamento, sem dados reais)"""
        if not colunas_source:
            return False
        
        # Conta quantas colunas source foram encontradas e quantas têm valores vazios
        colunas_source_encontradas = set()
        colunas_source_vazias = set()
        outras_colunas = set()
        
        # Analisa cada linha do registro
        for linha in linhas:
            if ':' in linha:
                coluna, valor = linha.split(':', 1)
                coluna_limpa = coluna.strip()
                valor_limpo = valor.strip()
                
                # Normaliza para comparação
                coluna_normalizada = self.normalizar_nome(coluna_limpa)
                
                # Verifica se é uma coluna source
                eh_coluna_source = False
                for source_col in colunas_source:
                    source_col_normalizada = self.normalizar_nome(source_col)
                    if coluna_normalizada == source_col_normalizada:
                        eh_coluna_source = True
                        colunas_source_encontradas.add(coluna_normalizada)
                        # Se o valor estiver vazio, marca como vazia
                        if not valor_limpo or valor_limpo == "0" or valor_limpo == "0.0":
                            colunas_source_vazias.add(coluna_normalizada)
                        break
                
                # Se não é coluna source, é outra coluna (dados reais)
                if not eh_coluna_source and valor_limpo and valor_limpo != "0" and valor_limpo != "0.0":
                    outras_colunas.add(coluna_normalizada)
        
        # É header se:
        # 1. Tem colunas source E todas estão vazias E não tem outras colunas com dados
        # 2. OU tem APENAS colunas source (sem outras colunas de dados)
        if colunas_source_encontradas:
            # Se todas as colunas source estão vazias e não há outras colunas com dados
            if len(colunas_source_vazias) == len(colunas_source_encontradas) and not outras_colunas:
                return True
            # Se tem colunas source mas não tem outras colunas (só tem headers)
            if not outras_colunas:
                return True
        
        return False
    
    def processar_arquivo_txt(self, arquivo_txt, tipo_arquivo=None, config=None):
        registros = []
        nomes_usados = {}
        headers_ignorados = 0
        
        # Carrega o config apropriado para este arquivo se não foi passado
        if config is None:
            config_path = self.encontrar_config(arquivo_txt.name)
            config = self.carregar_config(config_path)
        
        # Atualiza o config da instância para uso em outros métodos
        self.config = config
        
        # Se não foi passado o tipo, tenta identificar pelo nome do arquivo
        if tipo_arquivo is None:
            tipo_arquivo = self.identificar_tipo_arquivo(arquivo_txt.name, config)
        
        # Obtém colunas source do mapeamento para detectar headers
        colunas_source = self.obter_colunas_source_mapping(tipo_arquivo)
        if colunas_source:
            logging.info(f"Colunas source detectadas para detecção de headers: {sorted(colunas_source)}")
        
        # Filtra os mapeamentos: primeiro tenta o tipo específico, depois usa fallback
        mapeamentos_filtrados = []
        if tipo_arquivo and 'columnMapping' in self.config:
            # Primeiro tenta encontrar mapeamentos para o tipo específico
            for mapeamento in self.config['columnMapping']:
                if mapeamento.get('sourceFile') == tipo_arquivo:
                    mapeamentos_filtrados.append(mapeamento)
            
            # Se não encontrou mapeamentos para o tipo específico, usa o outro tipo como fallback
            if not mapeamentos_filtrados:
                tipo_fallback = 'venda' if tipo_arquivo == 'custo' else 'custo'
                logging.info(f"Não encontrou mapeamentos para {tipo_arquivo}, usando mapeamentos de {tipo_fallback} como fallback")
                for mapeamento in self.config['columnMapping']:
                    if mapeamento.get('sourceFile') == tipo_fallback:
                        mapeamentos_filtrados.append(mapeamento)
            
            # Se ainda não encontrou, usa todos os mapeamentos disponíveis
            if not mapeamentos_filtrados:
                logging.warning(f"Não encontrou mapeamentos específicos, usando todos os mapeamentos disponíveis")
                mapeamentos_filtrados = self.config.get('columnMapping', [])
        else:
            # Se não conseguiu identificar o tipo, usa todos os mapeamentos (fallback)
            logging.warning(f"Não foi possível identificar o tipo do arquivo {arquivo_txt.name}, usando todos os mapeamentos")
            mapeamentos_filtrados = self.config.get('columnMapping', [])

        # Pré-carrega as colunas de cores uma vez (com log de fallback apenas na primeira vez)
        if tipo_arquivo:
            self.obter_colunas_cores_do_config(tipo_arquivo, log_fallback=True)

        with open(arquivo_txt, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        blocos = conteudo.split('========== REGISTRO ')[1:]
        
        for bloco in blocos:
            linhas = bloco.split('\n')
            
            # Verifica se é um header (contém colunas source do mapeamento)
            if self.registro_eh_header(linhas, colunas_source):
                headers_ignorados += 1
                continue  # Ignora este registro (é um header)
            
            registro = {}
            
            # variações de cores (passa o tipo de arquivo, com fallback automático, sem log repetido)
            variacoes_cores = self.extrair_variacoes_cores(linhas, tipo_arquivo) if tipo_arquivo else self.extrair_variacoes_cores(linhas, None)
            
            # Usa apenas os mapeamentos filtrados para este tipo de arquivo
            for mapeamento in mapeamentos_filtrados:
                coluna_gabarito = mapeamento['gabaritoColumn']
                coluna_origem = mapeamento['sourceColumn']

                # campos manuais
                if coluna_origem == "__EMPTY__":
                    if 'name' in mapeamento:
                        if mapeamento['name'] in ["VAZIO", "MERGE"]:
                            continue
                        registro[coluna_gabarito] = mapeamento['name']
                    continue

                # coluna COR (lista)
                if isinstance(coluna_origem, list):
                    if coluna_gabarito == "COR":
                        if variacoes_cores:
                            registro[coluna_gabarito] = variacoes_cores
                    else:
                        for coluna in coluna_origem:
                            valor = self.encontrar_valor_registro(linhas, coluna)
                            if valor and valor not in ["0", "", "MERGE"]:
                                registro[coluna_gabarito] = valor
                                break
                    continue

                # coluna única
                valor = self.encontrar_valor_registro(linhas, coluna_origem)
                if valor and valor not in ["", "MERGE"]:
                    registro[coluna_gabarito] = valor
            
            # GARANTIR QUE SEMPRE HAJA UM REGISTRO
            if "DESCRICAO" not in registro:
                registro["DESCRICAO"] = "SEM NOME"

            # REMOVER ESPAÇOS INDESEJADOS
            nome_original = registro["DESCRICAO"].strip()
            nome_base = re.sub(r'\s+', ' ', nome_original)

            # NUMERAR DUPLICADOS
            if nome_base not in nomes_usados:
                nomes_usados[nome_base] = 0
            else:
                nomes_usados[nome_base] += 1
                registro["DESCRICAO"] = f"{nome_base} ({nomes_usados[nome_base]})"

            registros.append(registro)
        
        if headers_ignorados > 0:
            logging.info(f"Headers ignorados: {headers_ignorados} registros")

        return registros

    
    def gerar_json_final(self):
        logging.info("INICIANDO GERACAO JSON")
        
        arquivos_txt = list(self.pasta_txt.glob('*.txt'))
        total_gerados = 0
        
        for arquivo in arquivos_txt:
            logging.info(f"Processando: {arquivo.name}")
            
            # Encontra e carrega o config apropriado para este arquivo
            config_path = self.encontrar_config(arquivo.name)
            config = self.carregar_config(config_path)
            
            # Processa o arquivo com o config correto
            dados = self.processar_arquivo_txt(arquivo, config=config)
            
            nome_json = arquivo.stem + '.json'
            caminho_json = self.pasta_destino / nome_json
            
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            
            total_gerados += 1
            logging.info(f"  -> Gerado: {nome_json} ({len(dados)} registros)")
        
        logging.info(f"CONCLUIDO: {total_gerados} arquivos JSON gerados")
        return total_gerados

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    
    gerador = GeradorJSON()
    total = gerador.gerar_json_final()
    
    logging.info(f"Arquivos salvos em: {gerador.pasta_destino}")

if __name__ == '__main__':
    main()