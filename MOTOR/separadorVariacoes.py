import json
import re
from pathlib import Path
import logging
import unicodedata
from itertools import product

class SeparadorVariacoes:
    def __init__(self, pasta_json_mesclado=None, pasta_config=None, pasta_destino=None):
        script_dir = Path(__file__).parent.absolute()
        
        if pasta_json_mesclado is None:
            pasta_json_mesclado = script_dir / 'jsons_mesclados'
        if pasta_config is None:
            pasta_config = script_dir / 'configs'
        if pasta_destino is None:
            pasta_destino = script_dir / 'json_com_rgex'
        
        self.pasta_json_mesclado = Path(pasta_json_mesclado)
        self.pasta_config = Path(pasta_config)
        self.pasta_destino = Path(pasta_destino)
        self.pasta_destino.mkdir(exist_ok=True)

    def normalizar_nome(self, nome):
        """Normaliza nome de arquivo (mesma lógica dos outros módulos)"""
        return re.sub(r'[^a-zA-Z0-9]', '', str(nome).lower().strip())

    def normalizar_string_comparacao(self, texto):
        """Normaliza string removendo acentos para comparação (mesma lógica dos outros módulos)"""
        if not texto:
            return ""
        texto = str(texto).strip()
        # Remover acentos básicos
        texto = unicodedata.normalize('NFD', texto)
        texto = ''.join(char for char in texto if unicodedata.category(char) != 'Mn')
        return texto.lower()

    def encontrar_config(self, nome_arquivo_json):
        """Encontra a config correspondente ao arquivo JSON (mesma lógica dos outros módulos)"""
        if not self.pasta_config.exists():
            logging.error(f"Pasta de configs não encontrada: {self.pasta_config}")
            return None
        
        config_files = list(self.pasta_config.glob('*.json'))
        config_files = [f for f in config_files if f.name != '.gitkeep']
        
        if not config_files:
            logging.error(f"Nenhum arquivo de config encontrado em {self.pasta_config}")
            return None
        
        nome_arquivo_sem_ext = Path(nome_arquivo_json).stem
        nome_arquivo_sem_mesclado = nome_arquivo_sem_ext.replace('_mesclado', '')
        nome_arquivo_limpo = self.normalizar_nome(nome_arquivo_sem_mesclado)
        
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
            melhor_match = correspondencias[0]
            logging.debug(f"Arquivo {nome_arquivo_json} -> Config: {melhor_match[0].name} (score: {melhor_match[1]})")
            return melhor_match[0]
        
        logging.warning(f"Nenhuma config correspondente encontrada para {nome_arquivo_json}")
        return None

    def item_presente_no_valor(self, item, valor_original):
        """
        Verifica se o item está presente no valor original (match parcial)
        Segue a mesma lógica de normalização dos outros módulos
        """
        if not item or not valor_original:
            return False
        
        item_normalizado = self.normalizar_string_comparacao(item)
        valor_normalizado = self.normalizar_string_comparacao(valor_original)
        
        # Verificar se o item está contido no valor (case-insensitive, sem acentos)
        if item_normalizado in valor_normalizado:
            return True
        
        # Verificar também com remoção de sufixos numéricos para comparação
        # Ex: "MADEIRA (1)" deve corresponder a "MADEIRA"
        item_sem_sufixo = re.sub(r'\s*\(\s*\d+\s*\)\s*$', '', item_normalizado).strip()
        valor_sem_sufixo = re.sub(r'\s*\(\s*\d+\s*\)\s*$', '', valor_normalizado).strip()
        
        if item_sem_sufixo and item_sem_sufixo in valor_sem_sufixo:
            return True
        
        return False

    def deve_aplicar_separador(self, produto, separador):
        """
        Verifica se o separador deve ser aplicado ao produto
        Baseado na coluna e no valorOriginal
        """
        coluna = separador.get('coluna', '')
        valor_original = separador.get('valorOriginal', '')
        
        if not coluna:
            return False
        
        valor_coluna = produto.get(coluna, '')
        if not valor_coluna:
            return False
        
        # Se não há valorOriginal especificado, aplicar a todos os produtos que têm a coluna
        if not valor_original:
            return True
        
        # Verificar se o valorOriginal está presente no valor da coluna
        return self.item_presente_no_valor(valor_original, str(valor_coluna))

    def extrair_sufixo_numerico(self, texto):
        """
        Extrai sufixo numérico como "(1)", "(2)" etc da DESCRICAO
        Retorna (texto_sem_sufixo, sufixo)
        """
        if not texto:
            return texto, ""
        
        texto_str = str(texto)
        match = re.search(r'(.+?)\s*\(\s*(\d+)\s*\)\s*$', texto_str)
        
        if match:
            texto_base = match.group(1).strip()
            sufixo = f" ({match.group(2)})"
            return texto_base, sufixo
        
        return texto_str, ""

    def gerar_variacoes_por_coluna(self, produto, separador):
        """
        Gera todas as variações possíveis para uma coluna específica
        Retorna lista de produtos modificados (um por variação)
        """
        coluna = separador.get('coluna', '')
        valor_original = separador.get('valorOriginal', '')
        itens_separados = separador.get('itensSeparados', [])
        
        if not coluna or not itens_separados:
            return [produto]
        
        if not self.deve_aplicar_separador(produto, separador):
            return [produto]
        
        valor_coluna = produto.get(coluna, '')
        variacoes = []
        
        # Para DESCRICAO: preservar original, cada variação vai para OBS
        if coluna.upper() == "DESCRICAO":
            descricao_original = str(valor_coluna)
            texto_base, sufixo = self.extrair_sufixo_numerico(descricao_original)
            
            for item in itens_separados:
                item_limpo = str(item).strip()
                if not item_limpo:
                    continue
                
                # Verificar se o item está presente no valor original
                if not self.item_presente_no_valor(item_limpo, descricao_original):
                    continue
                
                novo_produto = produto.copy()
                # Preservar DESCRICAO original (com sufixo se houver)
                novo_produto['DESCRICAO'] = descricao_original.upper()
                # Cada variação vai para OBS
                novo_produto['OBS'] = item_limpo.upper()
                variacoes.append(novo_produto)
        
        # Para outras colunas: substituir o valor na coluna
        else:
            valor_original_str = str(valor_coluna)
            
            for item in itens_separados:
                item_limpo = str(item).strip()
                if not item_limpo:
                    continue
                
                # Verificar se o item está presente no valor original
                if not self.item_presente_no_valor(item_limpo, valor_original_str):
                    continue
                
                novo_produto = produto.copy()
                # Substituir valor na coluna específica
                novo_produto[coluna.upper()] = item_limpo.upper()
                variacoes.append(novo_produto)
        
        return variacoes if variacoes else [produto]

    def gerar_produto_cartesiano(self, produto, separadores_config):
        """
        Gera todas as combinações possíveis (produto cartesiano) entre as variações
        de todas as colunas que receberam separadores
        """
        if not separadores_config or 'separadores' not in separadores_config:
            return [produto]
        
        separadores = separadores_config['separadores']
        if not separadores:
            return [produto]
        
        # Agrupar separadores por coluna (priorizando o primeiro que aplicar)
        separadores_por_coluna = {}
        for separador in separadores:
            coluna = separador.get('coluna', '').upper()
            if coluna and self.deve_aplicar_separador(produto, separador):
                if coluna not in separadores_por_coluna:
                    separadores_por_coluna[coluna] = separador
        
        if not separadores_por_coluna:
            return [produto]
        
        # Preparar variações por coluna (como listas simples de valores)
        variacoes_por_coluna = {}
        descricao_original = None
        
        for coluna, separador in separadores_por_coluna.items():
            if coluna == "DESCRICAO":
                # Para DESCRICAO, preservar original e gerar lista de OBS
                descricao_original = str(produto.get('DESCRICAO', ''))
                itens_separados = separador.get('itensSeparados', [])
                obs_list = []
                
                for item in itens_separados:
                    item_limpo = str(item).strip()
                    if item_limpo and self.item_presente_no_valor(item_limpo, descricao_original):
                        obs_list.append(item_limpo.upper())
                
                if obs_list:
                    variacoes_por_coluna[coluna] = obs_list
            else:
                # Para outras colunas, gerar lista de valores
                valor_coluna = produto.get(coluna, '')
                itens_separados = separador.get('itensSeparados', [])
                valores_list = []
                
                for item in itens_separados:
                    item_limpo = str(item).strip()
                    if item_limpo and self.item_presente_no_valor(item_limpo, str(valor_coluna)):
                        valores_list.append(item_limpo.upper())
                
                if valores_list:
                    variacoes_por_coluna[coluna] = valores_list
        
        if not variacoes_por_coluna:
            return [produto]
        
        # Se apenas uma coluna tem variações
        if len(variacoes_por_coluna) == 1:
            coluna, valores = next(iter(variacoes_por_coluna.items()))
            produtos_finais = []
            
            if coluna == "DESCRICAO":
                # DESCRICAO: preservar original, cada valor vai para OBS
                for obs_valor in valores:
                    novo_produto = produto.copy()
                    novo_produto['DESCRICAO'] = descricao_original.upper()
                    novo_produto['OBS'] = obs_valor
                    produtos_finais.append(novo_produto)
            else:
                # Outra coluna: substituir valor
                for valor in valores:
                    novo_produto = produto.copy()
                    novo_produto[coluna] = valor
                    produtos_finais.append(novo_produto)
            
            return produtos_finais
        
        # Gerar produto cartesiano entre todas as colunas
        colunas_ordenadas = sorted(variacoes_por_coluna.keys())
        listas_valores = [variacoes_por_coluna[col] for col in colunas_ordenadas]
        
        produtos_finais = []
        
        # Para cada combinação do produto cartesiano
        for combinacao in product(*listas_valores):
            novo_produto = produto.copy()
            
            # Aplicar cada valor da combinação na coluna correspondente
            for idx, coluna in enumerate(colunas_ordenadas):
                valor = combinacao[idx]
                
                if coluna == "DESCRICAO":
                    # DESCRICAO: preservar original, valor vai para OBS
                    novo_produto['DESCRICAO'] = descricao_original.upper()
                    novo_produto['OBS'] = valor
                else:
                    # Outras colunas: substituir valor
                    novo_produto[coluna] = valor
            
            # Converter todas as strings para maiúsculas (garantir)
            for chave, valor in novo_produto.items():
                if isinstance(valor, str):
                    novo_produto[chave] = valor.upper()
            
            produtos_finais.append(novo_produto)
        
        return produtos_finais if produtos_finais else [produto]

    def processar_arquivo_com_config(self, arquivo_json, config_path):
        """Processa um arquivo JSON com uma config específica"""
        try:
            with open(arquivo_json, 'r', encoding='utf-8') as f:
                produtos = json.load(f)
        except Exception as e:
            logging.error(f"Erro ao ler {arquivo_json}: {e}")
            return False
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            logging.error(f"Erro ao ler config {config_path}: {e}")
            return False
        
        separadores_config = None
        if 'separadores' in config:
            separadores_config = {'separadores': config['separadores']}
        
        if not separadores_config or not separadores_config.get('separadores'):
            logging.debug(f"Nenhum separador configurado em {config_path.name}, pulando...")
            return False
        
        produtos_finais = []
        
        for produto in produtos:
            produtos_gerados = self.gerar_produto_cartesiano(produto, separadores_config)
            produtos_finais.extend(produtos_gerados)
        
        # Gerar nome do arquivo de saída
        nome_base = arquivo_json.stem
        nome_config = config_path.stem
        nome_saida = f"{nome_base}_{nome_config}.json"
        arquivo_destino = self.pasta_destino / nome_saida
        
        with open(arquivo_destino, 'w', encoding='utf-8') as f:
            json.dump(produtos_finais, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Processado {arquivo_json.name} com {config_path.name}: {len(produtos)} produtos -> {len(produtos_finais)} produtos")
        return True

    def processar_todos(self):
        """
        Processa TODOS os arquivos JSON mesclados com TODAS as configs
        Seguindo a regra: para cada config, processar todos os arquivos
        """
        if not self.pasta_json_mesclado.exists():
            logging.warning(f"Pasta de JSONs mesclados não encontrada: {self.pasta_json_mesclado}")
            return 0
        
        if not self.pasta_config.exists():
            logging.warning(f"Pasta de configs não encontrada: {self.pasta_config}")
            return 0
        
        arquivos_json = list(self.pasta_json_mesclado.glob('*_mesclado.json'))
        config_files = list(self.pasta_config.glob('*.json'))
        config_files = [f for f in config_files if f.name != '.gitkeep']
        
        if not arquivos_json:
            logging.warning(f"Nenhum arquivo JSON mesclado encontrado em {self.pasta_json_mesclado}")
            return 0
        
        if not config_files:
            logging.warning(f"Nenhum arquivo de config encontrado em {self.pasta_config}")
            return 0
        
        total_processados = 0
        
        # Para cada config, processar todos os arquivos
        for config_file in config_files:
            logging.info(f"Processando config: {config_file.name}")
            
            for arquivo_json in arquivos_json:
                if self.processar_arquivo_com_config(arquivo_json, config_file):
                    total_processados += 1
        
        return total_processados


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    separador = SeparadorVariacoes()
    total = separador.processar_todos()
    logging.info(f"Processamento concluído: {total} combinações arquivo/config processadas")


if __name__ == '__main__':
    main()

