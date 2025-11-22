import json
import logging
from pathlib import Path
import re

class GeradorJSONMesclado:
    def __init__(self, config_path=None, pasta_json='./json_final', pasta_destino='./jsons_mesclados'):
        self.config = None
        self.config_path = config_path
        self.pasta_json = Path(pasta_json)
        self.pasta_destino = Path(pasta_destino)
        self.pasta_destino.mkdir(exist_ok=True)
        
    def normalizar_nome(self, nome):
        return re.sub(r'[^a-zA-Z0-9]', '', str(nome).lower().strip())
    
    def encontrar_config(self, nome_arquivo_json=None):
        config_dir = Path('./configs')
        if not config_dir.exists():
            logging.error("Pasta configs não encontrada")
            exit(1)
            
        config_files = list(config_dir.glob('*.json'))
        if not config_files:
            logging.error("Nenhum arquivo JSON encontrado em ./configs/")
            exit(1)
        
        if nome_arquivo_json is None:
            return config_files[0]
        
        nome_arquivo_sem_ext = Path(nome_arquivo_json).stem
        nome_arquivo_limpo = self.normalizar_nome(nome_arquivo_sem_ext)
        correspondencias = []
        
        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_temp = json.load(f)
                
                if 'files' in config_temp:
                    for tipo, info in config_temp['files'].items():
                        if 'path' in info:
                            nome_xlsx = Path(info['path']).stem
                            nome_xlsx_limpo = self.normalizar_nome(nome_xlsx)
                            score = 0
                            
                            if nome_xlsx_limpo == nome_arquivo_limpo:
                                score = 100
                            elif nome_arquivo_limpo.startswith(nome_xlsx_limpo):
                                proporcao = len(nome_xlsx_limpo) / len(nome_arquivo_limpo) if nome_arquivo_limpo else 0
                                score = 90 + (proporcao * 10)
                            elif nome_xlsx_limpo.startswith(nome_arquivo_limpo):
                                proporcao = len(nome_arquivo_limpo) / len(nome_xlsx_limpo) if nome_xlsx_limpo else 0
                                score = 70 + (proporcao * 10)
                            elif nome_xlsx_limpo in nome_arquivo_limpo:
                                proporcao = len(nome_xlsx_limpo) / len(nome_arquivo_limpo) if nome_arquivo_limpo else 0
                                if proporcao < 0.3:
                                    score = 30
                                else:
                                    score = 50 + (proporcao * 20)
                            
                            if score > 0:
                                correspondencias.append((config_file, score, nome_xlsx, tipo))
            except Exception as e:
                logging.warning(f"Erro ao ler config {config_file}: {e}")
                continue
        
        if correspondencias:
            correspondencias.sort(key=lambda x: (x[1], len(x[2])), reverse=True)
            return correspondencias[0][0]
        
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
        nome_sem_ext = Path(nome).stem
        nome_limpo = re.sub(r'[^a-zA-Z0-9]', '', nome_sem_ext.lower())
        return nome_limpo
    
    def identificar_tipo_arquivo(self, nome_arquivo, config=None):
        if config is None:
            config = self.config
        
        if config is None:
            return None
            
        files_config = config.get('files', {})
        nome_arquivo_limpo = self.normalizar_nome_arquivo(nome_arquivo)
        
        for tipo, config_file in files_config.items():
            if 'path' in config_file:
                nome_xlsx = Path(config_file['path']).stem
                nome_xlsx_limpo = self.normalizar_nome_arquivo(nome_xlsx)
                
                if nome_xlsx_limpo in nome_arquivo_limpo or nome_arquivo_limpo in nome_xlsx_limpo:
                    return tipo
        
        return None
    
    def normalizar_nome_produto(self, nome):
        if isinstance(nome, (list, dict)):
            return ""
        return re.sub(r'\s+', ' ', str(nome).lower().strip())
    
    def formatar_valor(self, valor):
        if not valor or valor == "" or valor is None:
            return ""
        
        valor_limpo = re.sub(r'[^\d,\.]', '', str(valor))
        valor_limpo = valor_limpo.replace(',', '.')
        
        try:
            valor_float = float(valor_limpo)
            return f"{valor_float:.2f}"
        except (ValueError, TypeError):
            return valor
    
    def expandir_variacoes_cores(self, dados, tipo_arquivo):
        dados_expandidos = []
        
        for produto in dados:
            cor = produto.get('COR', '')
            
            if isinstance(cor, list) and cor and isinstance(cor[0], dict):
                for variacao in cor:
                    novo_produto = produto.copy()
                    novo_produto['COR'] = variacao.get('nome_cor', '')
                    
                    if tipo_arquivo == 'custo':
                        novo_produto['CUSTO'] = self.formatar_valor(variacao.get('preco', ''))
                    elif tipo_arquivo == 'venda':
                        novo_produto['PRECO1'] = self.formatar_valor(variacao.get('preco', ''))
                    
                    dados_expandidos.append(novo_produto)
            else:
                dados_expandidos.append(produto)
        
        return dados_expandidos
    
    def agrupar_arquivos_por_config(self):
        arquivos_json = list(self.pasta_json.glob('*.json'))
        
        if not arquivos_json:
            logging.error(f"Nenhum arquivo JSON encontrado em {self.pasta_json}")
            return {}
        
        grupos_por_config = {}
        
        for arquivo in arquivos_json:
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
        dados_custo = []
        dados_venda = []
        
        for arquivo in arquivos:
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                
                tipo = self.identificar_tipo_arquivo(arquivo.name, config)
                
                if tipo == 'custo':
                    dados_expandidos = self.expandir_variacoes_cores(dados, 'custo')
                    dados_custo.extend(dados_expandidos)
                elif tipo == 'venda':
                    dados_expandidos = self.expandir_variacoes_cores(dados, 'venda')
                    dados_venda.extend(dados_expandidos)
                    
            except Exception as e:
                logging.error(f"Erro ao carregar {arquivo.name}: {e}")
                continue
        
        return dados_custo, dados_venda
    
    def obter_nome_arquivo_venda(self, config):
        if 'files' in config and 'venda' in config['files']:
            nome_venda = Path(config['files']['venda'].get('path', 'venda')).stem
            return nome_venda
        return 'produtos_mesclados'
    
    def mesclar_dados(self, dados_custo, dados_venda):
        merge_config = self.config.get('mergeConfig', {})
        include_variation = merge_config.get('includeVariationKey', True)
        additional_keys = merge_config.get('additionalKeys', [])

        produtos_mesclados = []

        def gerar_chave(produto):
            partes = []
            partes.append(self.normalizar_nome_produto(produto.get('DESCRICAO', '')))

            if include_variation:
                partes.append(self.normalizar_nome_produto(produto.get('COR', '')))

            for key in additional_keys:
                partes.append(self.normalizar_nome_produto(produto.get(key, '')))

            return "|".join(partes)

        indice_venda = {}
        for produto_venda in dados_venda:
            chave = gerar_chave(produto_venda)
            indice_venda[chave] = produto_venda

        for produto_custo in dados_custo:
            chave = gerar_chave(produto_custo)
            produto_mesclado = produto_custo.copy()

            if chave in indice_venda:
                produto_venda = indice_venda[chave]

                if 'PRECO1' in produto_venda and produto_venda['PRECO1']:
                    produto_mesclado['PRECO1'] = self.formatar_valor(produto_venda['PRECO1'])

            if 'CUSTO' in produto_mesclado:
                produto_mesclado['CUSTO'] = self.formatar_valor(produto_mesclado['CUSTO'])

            produtos_mesclados.append(produto_mesclado)

        return produtos_mesclados

    
    def gerar_codigos_produto(self, produtos):
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
        for produto in dados:
            for chave, valor in produto.items():
                if isinstance(valor, str):
                    produto[chave] = valor.upper()
        return dados
    
    def limpar_dados(self, dados):
        dados_limpos = []
        for produto in dados:
            produto_limpo = {}
            for chave, valor in produto.items():
                if valor not in ["", None, "null", "NULL"]:
                    produto_limpo[chave] = valor
            dados_limpos.append(produto_limpo)
        return dados_limpos
    
    def processar_grupo(self, grupo):
        config_path = grupo['config_path']
        arquivos = grupo['arquivos']
        
        config = self.carregar_config(config_path)
        self.config = config
        
        dados_custo, dados_venda = self.carregar_jsons_do_grupo(arquivos, config)
        
        if not dados_custo and not dados_venda:
            return 0
        
        produtos_mesclados = self.mesclar_dados(dados_custo, dados_venda)
        produtos_com_codigo = self.gerar_codigos_produto(produtos_mesclados)
        produtos_finais = self.converter_para_maiusculas(produtos_com_codigo)
        produtos_finais = self.limpar_dados(produtos_finais)
        
        nome_arquivo_venda = self.obter_nome_arquivo_venda(config)
        nome_arquivo_final = f"{nome_arquivo_venda}_mesclado.json"
        
        caminho_json = self.pasta_destino / nome_arquivo_final
        with open(caminho_json, 'w', encoding='utf-8') as f:
            json.dump(produtos_finais, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Gerado: {nome_arquivo_final} ({len(produtos_finais)} produtos)")
        
        return len(produtos_finais)
    
    def gerar_json_final(self):
        grupos_por_config = self.agrupar_arquivos_por_config()
        
        if not grupos_por_config:
            logging.error("Nenhum arquivo encontrado para processar")
            return 0
        
        total_produtos = 0
        
        for config_key, grupo in grupos_por_config.items():
            produtos = self.processar_grupo(grupo)
            total_produtos += produtos
        
        return total_produtos

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    
    gerador = GeradorJSONMesclado()
    gerador.gerar_json_final()

if __name__ == '__main__':
    main()