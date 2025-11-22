import json
import logging
from pathlib import Path
import re

class GeradorJSONMesclado:
    def __init__(self, config_path=None, pasta_json='./json_final', pasta_destino='./jsons_mesclados'):
        # Não carrega config aqui, será carregado por grupo de arquivos
        self.config = None
        self.config_path = config_path
        self.pasta_json = Path(pasta_json)
        self.pasta_destino = Path(pasta_destino)
        self.pasta_destino.mkdir(exist_ok=True)
        
    def normalizar_nome(self, nome):
        """Normaliza nome para comparação (remove caracteres especiais e converte para minúsculas)"""
        return re.sub(r'[^a-zA-Z0-9]', '', str(nome).lower().strip())
    
    def encontrar_config(self, nome_arquivo_json=None):
        """Encontra o config apropriado baseado no arquivo JSON sendo processado"""
        config_dir = Path('./configs')
        if not config_dir.exists():
            logging.error("Pasta configs não encontrada")
            exit(1)
            
        config_files = list(config_dir.glob('*.json'))
        if not config_files:
            logging.error("Nenhum arquivo JSON encontrado em ./configs/")
            exit(1)
        
        # Se não foi passado nome de arquivo, retorna o primeiro (comportamento antigo)
        if nome_arquivo_json is None:
            config_path = config_files[0]
            logging.info(f"Usando configuração padrão: {config_path}")
            return config_path
        
        # Remove extensão do arquivo JSON e normaliza
        nome_arquivo_sem_ext = Path(nome_arquivo_json).stem
        nome_arquivo_limpo = self.normalizar_nome(nome_arquivo_sem_ext)
        
        # Lista para armazenar correspondências encontradas (config, score de correspondência, nome)
        correspondencias = []
        
        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_temp = json.load(f)
                
                # Verifica se algum arquivo definido no config corresponde ao arquivo JSON
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
                            # Nome do arquivo JSON começa com o nome do XLSX (correspondência muito forte)
                            elif nome_arquivo_limpo.startswith(nome_xlsx_limpo):
                                proporcao = len(nome_xlsx_limpo) / len(nome_arquivo_limpo) if nome_arquivo_limpo else 0
                                score = 90 + (proporcao * 10)  # Entre 90-100
                            # Nome do XLSX contém o nome do arquivo JSON (correspondência fraca, mas possível)
                            elif nome_xlsx_limpo.startswith(nome_arquivo_limpo):
                                proporcao = len(nome_arquivo_limpo) / len(nome_xlsx_limpo) if nome_xlsx_limpo else 0
                                score = 70 + (proporcao * 10)  # Entre 70-80
                            # Nome do config está contido no nome do arquivo (correspondência média)
                            elif nome_xlsx_limpo in nome_arquivo_limpo:
                                proporcao = len(nome_xlsx_limpo) / len(nome_arquivo_limpo) if nome_arquivo_limpo else 0
                                if proporcao < 0.3:  # Menos de 30% do nome
                                    score = 30
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
            
            logging.info(f"Arquivo '{nome_arquivo_json}' corresponde ao config '{melhor_config.name}' "
                        f"(arquivo: '{melhor_nome}' tipo: {melhor_tipo}, score: {melhor_score:.1f})")
            
            # Se há múltiplas correspondências, avisa
            if len(correspondencias) > 1:
                logging.warning(f"Encontradas {len(correspondencias)} correspondências, usando a melhor: {melhor_config.name} (score: {melhor_score:.1f})")
            
            return melhor_config
        
        # Se não encontrou correspondência, usa o primeiro config (fallback)
        logging.warning(f"Não encontrou config específico para '{nome_arquivo_json}', usando '{config_files[0].name}' como fallback")
        return config_files[0]
        
    def carregar_config(self, config_path):
        config_path = Path(config_path)
        if not config_path.exists():
            logging.error(f"Arquivo de configuração não encontrado: {config_path}")
            logging.error("Verifique se o caminho está correto")
            exit(1)
            
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def normalizar_nome_arquivo(self, nome):
        """Normaliza nome do arquivo para comparação"""
        # Remove extensão, espaços extras, e caracteres especiais
        nome_sem_ext = Path(nome).stem
        nome_limpo = re.sub(r'[^a-zA-Z0-9]', '', nome_sem_ext.lower())
        return nome_limpo
    
    def identificar_tipo_arquivo(self, nome_arquivo, config=None):
        """Identifica se o arquivo é de custo ou venda baseado no config"""
        if config is None:
            config = self.config
        
        if config is None:
            return None
            
        files_config = config.get('files', {})
        
        nome_arquivo_limpo = self.normalizar_nome_arquivo(nome_arquivo)
        
        for tipo, config_file in files_config.items():
            if 'path' in config_file:
                # Pega o nome do arquivo XLSX do config e normaliza
                nome_xlsx = Path(config_file['path']).stem  # Remove .xlsx
                nome_xlsx_limpo = self.normalizar_nome_arquivo(nome_xlsx)
                
                # Verifica se o arquivo atual corresponde ao esperado (comparação flexível)
                if nome_xlsx_limpo in nome_arquivo_limpo or nome_arquivo_limpo in nome_xlsx_limpo:
                    logging.info(f"Arquivo {nome_arquivo} identificado como {tipo}")
                    return tipo
        
        logging.warning(f"Arquivo {nome_arquivo} não corresponde a nenhum config")
        return None
    
    def normalizar_nome_produto(self, nome):
        """Normaliza nome para comparação de produtos"""
        if isinstance(nome, (list, dict)):
            return ""
        return re.sub(r'\s+', ' ', str(nome).lower().strip())
    
    def formatar_valor(self, valor):
        """Formata valores para 2 casas decimais"""
        if not valor or valor == "" or valor is None:
            return ""
        
        # Remove caracteres não numéricos exceto vírgula e ponto
        valor_limpo = re.sub(r'[^\d,\.]', '', str(valor))
        
        # Substitui vírgula por ponto para conversão
        valor_limpo = valor_limpo.replace(',', '.')
        
        try:
            # Converte para float e formata com 2 casas decimais
            valor_float = float(valor_limpo)
            return f"{valor_float:.2f}"
        except (ValueError, TypeError):
            return valor
    
    def expandir_variacoes_cores(self, dados, tipo_arquivo):
        """Expande os registros que têm COR como lista em registros individuais"""
        dados_expandidos = []
        
        for produto in dados:
            cor = produto.get('COR', '')
            
            # Se COR for uma lista de objetos, expande em registros individuais
            if isinstance(cor, list) and cor and isinstance(cor[0], dict):
                for variacao in cor:
                    novo_produto = produto.copy()
                    novo_produto['COR'] = variacao.get('nome_cor', '')
                    
                    # Define CUSTO ou PRECO1 baseado no tipo de arquivo
                    if tipo_arquivo == 'custo':
                        novo_produto['CUSTO'] = self.formatar_valor(variacao.get('preco', ''))
                    elif tipo_arquivo == 'venda':
                        novo_produto['PRECO1'] = self.formatar_valor(variacao.get('preco', ''))
                    
                    dados_expandidos.append(novo_produto)
            else:
                # Se não tiver variações, mantém o registro original
                dados_expandidos.append(produto)
        
        return dados_expandidos
    
    def agrupar_arquivos_por_config(self):
        """Agrupa arquivos JSON por config correspondente"""
        arquivos_json = list(self.pasta_json.glob('*.json'))
        
        if not arquivos_json:
            logging.error(f"Nenhum arquivo JSON encontrado em {self.pasta_json}")
            return {}
        
        # Log dos arquivos encontrados
        logging.info(f"Arquivos JSON encontrados: {[f.name for f in arquivos_json]}")
        
        # Agrupa arquivos por config
        grupos_por_config = {}
        
        for arquivo in arquivos_json:
            # Encontra o config apropriado para este arquivo
            config_path = self.encontrar_config(arquivo.name)
            config_key = str(config_path)
            
            if config_key not in grupos_por_config:
                grupos_por_config[config_key] = {
                    'config_path': config_path,
                    'arquivos': []
                }
            
            grupos_por_config[config_key]['arquivos'].append(arquivo)
        
        return grupos_por_config
    
    def carregar_jsons_do_grupo(self, arquivos, config):
        """Carrega JSONs de um grupo específico (mesma config)"""
        dados_custo = []
        dados_venda = []
        
        for arquivo in arquivos:
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                
                # Identifica o tipo do arquivo baseado no config
                tipo = self.identificar_tipo_arquivo(arquivo.name, config)
                
                if tipo == 'custo':
                    # Expande as variações de cores
                    dados_expandidos = self.expandir_variacoes_cores(dados, 'custo')
                    logging.info(f"Carregando CUSTO: {arquivo.name} ({len(dados)} -> {len(dados_expandidos)} registros)")
                    dados_custo.extend(dados_expandidos)
                elif tipo == 'venda':
                    # Expande as variações de cores
                    dados_expandidos = self.expandir_variacoes_cores(dados, 'venda')
                    logging.info(f"Carregando VENDA: {arquivo.name} ({len(dados)} -> {len(dados_expandidos)} registros)")
                    dados_venda.extend(dados_expandidos)
                else:
                    logging.warning(f"Arquivo não identificado: {arquivo.name}")
                    
            except Exception as e:
                logging.error(f"Erro ao carregar {arquivo.name}: {e}")
                continue
        
        return dados_custo, dados_venda
    
    def obter_nome_arquivo_venda(self, config):
        """Obtém o nome do arquivo de venda do config para usar como nome do arquivo final"""
        if 'files' in config and 'venda' in config['files']:
            nome_venda = Path(config['files']['venda'].get('path', 'venda')).stem
            return nome_venda
        return 'produtos_mesclados'
    
    def mesclar_dados(self, dados_custo, dados_venda):
        """Mescla dados de custo e venda baseado no mergeConfig com suporte real a additionalKeys"""

        merge_config = self.config.get('mergeConfig', {})
        include_variation = merge_config.get('includeVariationKey', True)
        additional_keys = merge_config.get('additionalKeys', [])

        produtos_mesclados = []

        def gerar_chave(produto):
            partes = []

            # DESCRICAO (sempre)
            partes.append(self.normalizar_nome_produto(produto.get('DESCRICAO', '')))

            # COR (opcional)
            if include_variation:
                partes.append(self.normalizar_nome_produto(produto.get('COR', '')))

            # additionalKeys (dinâmico)
            for key in additional_keys:
                partes.append(self.normalizar_nome_produto(produto.get(key, '')))

            return "|".join(partes)

        # Cria índice da venda
        indice_venda = {}
        for produto_venda in dados_venda:
            chave = gerar_chave(produto_venda)
            indice_venda[chave] = produto_venda

        # Processa custo e mescla
        for produto_custo in dados_custo:

            chave = gerar_chave(produto_custo)
            produto_mesclado = produto_custo.copy()

            # Se achou na venda → mescla valores
            if chave in indice_venda:
                produto_venda = indice_venda[chave]

                if 'PRECO1' in produto_venda and produto_venda['PRECO1']:
                    produto_mesclado['PRECO1'] = self.formatar_valor(produto_venda['PRECO1'])

            # Formata custo
            if 'CUSTO' in produto_mesclado:
                produto_mesclado['CUSTO'] = self.formatar_valor(produto_mesclado['CUSTO'])

            produtos_mesclados.append(produto_mesclado)

        return produtos_mesclados

    
    def gerar_codigos_produto(self, produtos):
        """Gera COD_PRODUTO sequencial baseado na DESCRICAO (mesmo COD_PRODUTO para mesma descrição)"""
        codigos_gerados = {}
        codigo_sequencial = 1
        produtos_com_codigo = []
        
        for produto in produtos:
            descricao = produto.get('DESCRICAO', '')
            descricao_normalizada = self.normalizar_nome_produto(descricao)
            
            if descricao_normalizada not in codigos_gerados:
                codigos_gerados[descricao_normalizada] = f"{codigo_sequencial:06d}"
                codigo_sequencial += 1
            
            produto_com_codigo = produto.copy()
            produto_com_codigo['COD_PRODUTO'] = codigos_gerados[descricao_normalizada]
            produtos_com_codigo.append(produto_com_codigo)
        
        return produtos_com_codigo
    
    def converter_para_maiusculas(self, dados):
        """Converte todos os valores string para maiúsculas"""
        for produto in dados:
            for chave, valor in produto.items():
                if isinstance(valor, str):
                    produto[chave] = valor.upper()
        return dados
    
    def limpar_dados(self, dados):
        """Remove campos vazios e trata valores nulos"""
        dados_limpos = []
        for produto in dados:
            produto_limpo = {}
            for chave, valor in produto.items():
                if valor not in ["", None, "null", "NULL"]:
                    produto_limpo[chave] = valor
            dados_limpos.append(produto_limpo)
        return dados_limpos
    
    def processar_grupo(self, grupo):
        """Processa um grupo de arquivos com a mesma config"""
        config_path = grupo['config_path']
        arquivos = grupo['arquivos']
        
        # Carrega o config para este grupo
        config = self.carregar_config(config_path)
        self.config = config  # Atualiza o config da instância
        
        logging.info(f"\n=== Processando grupo com config: {config_path.name} ===")
        logging.info(f"Arquivos neste grupo: {[f.name for f in arquivos]}")
        
        # Carrega os JSONs deste grupo
        dados_custo, dados_venda = self.carregar_jsons_do_grupo(arquivos, config)
        
        if not dados_custo and not dados_venda:
            logging.warning(f"Nenhum dado encontrado para processar no grupo {config_path.name}")
            return 0
        
        logging.info(f"Dados carregados - Custo: {len(dados_custo)} registros, Venda: {len(dados_venda)} registros")
        
        # Mescla os dados usando mergeConfig
        logging.info("Mesclando dados de custo e venda...")
        produtos_mesclados = self.mesclar_dados(dados_custo, dados_venda)
        
        # Gera COD_PRODUTO sequencial
        logging.info("Gerando códigos de produto...")
        produtos_com_codigo = self.gerar_codigos_produto(produtos_mesclados)
        
        # Converte para maiúsculas
        produtos_finais = self.converter_para_maiusculas(produtos_com_codigo)
        
        # Limpa dados
        produtos_finais = self.limpar_dados(produtos_finais)
        
        # Obtém nome do arquivo baseado no arquivo de venda do config
        nome_arquivo_venda = self.obter_nome_arquivo_venda(config)
        nome_arquivo_final = f"{nome_arquivo_venda}_mesclado.json"
        
        # Salva JSON final
        caminho_json = self.pasta_destino / nome_arquivo_final
        with open(caminho_json, 'w', encoding='utf-8') as f:
            json.dump(produtos_finais, f, ensure_ascii=False, indent=2)
        
        logging.info(f"JSON MESCLADO GERADO: {caminho_json} ({len(produtos_finais)} produtos)")
        
        # Log de resumo
        codigos_unicos = len(set(p['COD_PRODUTO'] for p in produtos_finais))
        logging.info(f"RESUMO: {codigos_unicos} produtos únicos com {len(produtos_finais)} variações totais")
        
        return len(produtos_finais)
    
    def gerar_json_final(self):
        logging.info("INICIANDO GERACAO JSON MESCLADO")
        
        # Agrupa arquivos por config
        grupos_por_config = self.agrupar_arquivos_por_config()
        
        if not grupos_por_config:
            logging.error("Nenhum arquivo encontrado para processar")
            return 0
        
        logging.info(f"Encontrados {len(grupos_por_config)} grupo(s) de arquivos por config")
        
        total_processados = 0
        total_produtos = 0
        
        # Processa cada grupo separadamente
        for config_key, grupo in grupos_por_config.items():
            produtos = self.processar_grupo(grupo)
            total_produtos += produtos
            total_processados += 1
        
        logging.info(f"\n=== CONCLUIDO ===")
        logging.info(f"Total de grupos processados: {total_processados}")
        logging.info(f"Total de produtos gerados: {total_produtos}")
        
        return total_produtos

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    
    gerador = GeradorJSONMesclado()
    total = gerador.gerar_json_final()
    
    logging.info(f"Arquivo final salvo em: {gerador.pasta_destino}")

if __name__ == '__main__':
    main()