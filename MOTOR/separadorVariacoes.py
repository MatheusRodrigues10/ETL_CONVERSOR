import json
import re
from pathlib import Path
import logging
import os

class SeparadorVariacoes:
    def __init__(self, pasta_json_mesclado=None, pasta_config=None, pasta_destino=None):
        script_dir = Path(__file__).parent.absolute()
        
        if pasta_json_mesclado is None:
            pasta_json_mesclado = script_dir / 'jsons_mesclados'
        if pasta_config is None:
            pasta_config = script_dir / 'configs'
        if pasta_destino is None:
            pasta_destino = script_dir / 'jsons_mesclados'
        
        self.pasta_json_mesclado = Path(pasta_json_mesclado)
        self.pasta_config = Path(pasta_config)
        self.pasta_destino = Path(pasta_destino)
        self.pasta_destino.mkdir(exist_ok=True)

    def normalizar_nome(self, nome):
        return re.sub(r'[^a-zA-Z0-9]', '', str(nome).lower().strip())

    def encontrar_config(self, nome_arquivo_json):
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
            logging.info(f"Arquivo {nome_arquivo_json} -> Config: {melhor_match[0].name} (score: {melhor_match[1]})")
            return melhor_match[0]
        
        logging.warning(f"Nenhuma config correspondente encontrada para {nome_arquivo_json}")
        return None

    def verificar_varacao(self, valor, item_palavras):
        if not valor or not item_palavras:
            return False
        
        valor_str = str(valor).upper()
        item_str = str(item_palavras).upper().strip()
        
        padroes = [
            rf'\b{re.escape(item_str)}\s*\(\s*\d+\s*\)',
            rf'\b{re.escape(item_str)}\s+\d+',
            rf'\b{re.escape(item_str)}\s*-\s*\d+',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, valor_str)
            if match:
                inicio_match = match.start()
                trecho_antes = valor_str[:inicio_match].strip()
                
                if inicio_match == 0:
                    return True
                
                if not trecho_antes or not trecho_antes[-1].isalnum():
                    return True
        
        return False

    def deve_aplicar_separador(self, produto, separador):
        coluna = separador.get('coluna', '')
        valor_original = separador.get('valorOriginal', '')
        
        if not coluna:
            return False
        
        valor_coluna = produto.get(coluna, '')
        if not valor_coluna:
            return False
        
        if not valor_original:
            return True
        
        valor_coluna_str = str(valor_coluna).upper()
        valor_original_str = str(valor_original).upper()
        
        if valor_original_str in valor_coluna_str:
            return True
        
        return False

    def processar_separadores(self, produto, separadores_config):
        if not separadores_config or 'separadores' not in separadores_config:
            return [produto]
        
        separadores = separadores_config['separadores']
        if not separadores:
            return [produto]
        
        produtos_finais = []
        
        for separador in separadores:
            coluna = separador.get('coluna', '')
            valor_original = separador.get('valorOriginal', '')
            itens_separados = separador.get('itensSeparados', [])
            
            if not coluna or not itens_separados:
                continue
            
            if not self.deve_aplicar_separador(produto, separador):
                continue
            
            valor_coluna = produto.get(coluna, '')
            
            if coluna == "DESCRICAO":
                for item in itens_separados:
                    item_limpo = str(item).strip()
                    if not item_limpo:
                        continue
                    
                    item_match = False
                    
                    if valor_original and valor_original.lower() in str(valor_coluna).lower():
                        item_match = True
                    elif self.verificar_varacao(valor_coluna, item_limpo):
                        item_match = True
                    else:
                        valor_coluna_str = str(valor_coluna).upper()
                        item_limpo_str = item_limpo.upper()
                        if item_limpo_str in valor_coluna_str:
                            item_match = True
                    
                    if item_match:
                        novo_produto = produto.copy()
                        novo_produto['OBS'] = [item_limpo]
                        if 'itensSeparados' in novo_produto:
                            del novo_produto['itensSeparados']
                        produtos_finais.append(novo_produto)
            else:
                for item in itens_separados:
                    item_limpo = str(item).strip()
                    if not item_limpo:
                        continue
                    
                    item_match = False
                    
                    if valor_original and valor_original.lower() in str(valor_coluna).lower():
                        item_match = True
                    elif self.verificar_varacao(valor_coluna, item_limpo):
                        item_match = True
                    else:
                        valor_coluna_str = str(valor_coluna).upper()
                        item_limpo_str = item_limpo.upper()
                        if item_limpo_str in valor_coluna_str or valor_coluna_str == item_limpo_str:
                            item_match = True
                    
                    if item_match:
                        novo_produto = produto.copy()
                        novo_produto['itensSeparados'] = [item_limpo]
                        if 'OBS' in novo_produto and isinstance(novo_produto['OBS'], list) and len(novo_produto['OBS']) == 0:
                            del novo_produto['OBS']
                        produtos_finais.append(novo_produto)
        
        return produtos_finais if produtos_finais else [produto]

    def processar_arquivo(self, arquivo_json):
        try:
            with open(arquivo_json, 'r', encoding='utf-8') as f:
                produtos = json.load(f)
        except Exception as e:
            logging.error(f"Erro ao ler {arquivo_json}: {e}")
            return False
        
        config_path = self.encontrar_config(arquivo_json.name)
        if not config_path:
            logging.warning(f"Config não encontrado para {arquivo_json.name}, pulando...")
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
            return False
        
        produtos_finais = []
        
        for produto in produtos:
            produtos_gerados = self.processar_separadores(produto, separadores_config)
            produtos_finais.extend(produtos_gerados)
        
        arquivo_destino = self.pasta_destino / arquivo_json.name
        
        with open(arquivo_destino, 'w', encoding='utf-8') as f:
            json.dump(produtos_finais, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Processado {arquivo_json.name}: {len(produtos)} produtos -> {len(produtos_finais)} produtos")
        return True

    def processar_todos(self):
        arquivos_json = list(self.pasta_json_mesclado.glob('*_mesclado.json'))
        
        if not arquivos_json:
            logging.warning(f"Nenhum arquivo JSON mesclado encontrado em {self.pasta_json_mesclado}")
            return 0
        
        total_processados = 0
        for arquivo_json in arquivos_json:
            if self.processar_arquivo(arquivo_json):
                total_processados += 1
        
        return total_processados


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    separador = SeparadorVariacoes()
    total = separador.processar_todos()
    logging.info(f"Processamento concluído: {total} arquivo(s) processado(s)")


if __name__ == '__main__':
    main()
