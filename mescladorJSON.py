import json
import logging
from pathlib import Path
import re

class GeradorJSONMesclado:
    def __init__(self, config_path=None, pasta_json='./json_final', pasta_destino='./jsons_mesclados'):
        if config_path is None:
            config_path = self.encontrar_config()
        
        self.config = self.carregar_config(config_path)
        self.pasta_json = Path(pasta_json)
        self.pasta_destino = Path(pasta_destino)
        self.pasta_destino.mkdir(exist_ok=True)
        
    def encontrar_config(self):
        """Encontra automaticamente o primeiro arquivo JSON na pasta configs"""
        config_dir = Path('./configs')
        if not config_dir.exists():
            logging.error("Pasta configs não encontrada")
            exit(1)
            
        config_files = list(config_dir.glob('*.json'))
        if not config_files:
            logging.error("Nenhum arquivo JSON encontrado em ./configs/")
            exit(1)
        
        config_path = config_files[0]
        logging.info(f"Usando configuração: {config_path}")
        return config_path
        
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
    
    def identificar_tipo_arquivo(self, nome_arquivo):
        """Identifica se o arquivo é de custo ou venda baseado no config"""
        files_config = self.config.get('files', {})
        
        nome_arquivo_limpo = self.normalizar_nome_arquivo(nome_arquivo)
        
        for tipo, config in files_config.items():
            if 'path' in config:
                # Pega o nome do arquivo XLSX do config e normaliza
                nome_xlsx = Path(config['path']).stem  # Remove .xlsx
                nome_xlsx_limpo = self.normalizar_nome_arquivo(nome_xlsx)
                
                # Verifica se o arquivo atual corresponde ao esperado (comparação flexível)
                if nome_xlsx_limpo in nome_arquivo_limpo or nome_arquivo_limpo in nome_xlsx_limpo:
                    logging.info(f"Arquivo {nome_arquivo} identificado como {tipo}")
                    return tipo
        
        logging.warning(f"Arquivo {nome_arquivo} não corresponde a nenhum config")
        return None
    
    def normalizar_nome(self, nome):
        """Normaliza nome para comparação"""
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
    
    def carregar_jsons(self):
        """Carrega todos os JSONs da pasta json_final"""
        dados_custo = []
        dados_venda = []
        
        arquivos_json = list(self.pasta_json.glob('*.json'))
        
        if not arquivos_json:
            logging.error(f"Nenhum arquivo JSON encontrado em {self.pasta_json}")
            return dados_custo, dados_venda
        
        # Log dos arquivos encontrados
        logging.info(f"Arquivos JSON encontrados: {[f.name for f in arquivos_json]}")
        
        for arquivo in arquivos_json:
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                
                # Identifica o tipo do arquivo baseado no config
                tipo = self.identificar_tipo_arquivo(arquivo.name)
                
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
    
    def mesclar_dados(self, dados_custo, dados_venda):
        """Mescla dados de custo e venda baseado no mergeConfig com suporte real a additionalKeys"""

        merge_config = self.config.get('mergeConfig', {})
        include_variation = merge_config.get('includeVariationKey', True)
        additional_keys = merge_config.get('additionalKeys', [])

        produtos_mesclados = []

        def gerar_chave(produto):
            partes = []

            # DESCRICAO (sempre)
            partes.append(self.normalizar_nome(produto.get('DESCRICAO', '')))

            # COR (opcional)
            if include_variation:
                partes.append(self.normalizar_nome(produto.get('COR', '')))

            # additionalKeys (dinâmico)
            for key in additional_keys:
                partes.append(self.normalizar_nome(produto.get(key, '')))

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
            descricao_normalizada = self.normalizar_nome(descricao)
            
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
    
    def gerar_json_final(self):
        logging.info("INICIANDO GERACAO JSON MESCLADO")
        
        # Carrega os JSONs
        dados_custo, dados_venda = self.carregar_jsons()
        
        if not dados_custo and not dados_venda:
            logging.error("Nenhum dado encontrado para processar")
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
        
        # Salva JSON final
        caminho_json = self.pasta_destino / 'produtos_mesclados.json'
        with open(caminho_json, 'w', encoding='utf-8') as f:
            json.dump(produtos_finais, f, ensure_ascii=False, indent=2)
        
        logging.info(f"JSON MESCLADO GERADO: {caminho_json} ({len(produtos_finais)} produtos)")
        
        # Log de resumo
        codigos_unicos = len(set(p['COD_PRODUTO'] for p in produtos_finais))
        logging.info(f"RESUMO: {codigos_unicos} produtos únicos com {len(produtos_finais)} variações totais")
        
        return len(produtos_finais)

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    
    gerador = GeradorJSONMesclado()
    total = gerador.gerar_json_final()
    
    logging.info(f"Arquivo final salvo em: {gerador.pasta_destino}")

if __name__ == '__main__':
    main()