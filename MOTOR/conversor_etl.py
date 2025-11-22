import pandas as pd
from pathlib import Path
import logging
from datetime import datetime
import sys
import json
import re

class ConversorPlanilhasTXT:
    def __init__(self, config_path=None, pasta_origem='./planilhas', pasta_destino='./txt_bruto'):
        if config_path is None:
            config_path = self.encontrar_config()
        
        self.config = self.carregar_config(config_path)
        self.pasta_origem = Path(pasta_origem)
        self.pasta_destino = Path(pasta_destino)
        self.pasta_destino.mkdir(parents=True, exist_ok=True)
    
    def normalizar_nome(self, nome):
        return re.sub(r'[^a-zA-Z0-9]', '', str(nome).lower().strip())
    
    def encontrar_config(self):
        config_dir = Path('./configs')
        if not config_dir.exists():
            logging.error("Pasta configs não encontrada")
            exit(1)
            
        config_files = list(config_dir.glob('*.json'))
        if not config_files:
            logging.error("Nenhum arquivo JSON encontrado em ./configs/")
            exit(1)
        
        return config_files[0]
    
    def encontrar_config_para_arquivo(self, nome_arquivo_excel):
        config_dir = Path('./configs')
        if not config_dir.exists():
            logging.error("Pasta configs não encontrada")
            exit(1)
            
        config_files = list(config_dir.glob('*.json'))
        if not config_files:
            logging.error("Nenhum arquivo JSON encontrado em ./configs/")
            exit(1)
        
        nome_arquivo_sem_ext = Path(nome_arquivo_excel).stem
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
            exit(1)
            
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def parse_cell_to_row(self, cell_address):
        match = re.match(r'([A-Z]+)(\d+)', cell_address.upper())
        if match:
            return int(match.group(2))
        return 1
    
    def processar_pagina_com_config(self, arquivo, nome_aba, pagina_config, tipo_arquivo, config=None):
        if config is None:
            config = self.config
        
        start_cell = pagina_config.get('startCell', 'A1')
        start_row = self.parse_cell_to_row(start_cell)
        
        colunas_config = []
        if 'files' in config and tipo_arquivo in config['files']:
            colunas_config = config['files'][tipo_arquivo].get('columns', [])
        elif 'columns' in pagina_config:
            colunas_config = pagina_config['columns']
        
        if colunas_config:
            skip_rows = start_row - 1
            df = pd.read_excel(arquivo, sheet_name=nome_aba, header=0, skiprows=skip_rows)
            
            num_colunas_config = len(colunas_config)
            num_colunas_df = len(df.columns)
            
            novo_nomes = {}
            for i, col_config in enumerate(colunas_config):
                if i < num_colunas_df:
                    col_atual = df.columns[i]
                    novo_nomes[col_atual] = col_config
            
            df = df.rename(columns=novo_nomes)
            
            if num_colunas_config > num_colunas_df:
                for i in range(num_colunas_df, num_colunas_config):
                    df[colunas_config[i]] = None
            elif num_colunas_config < num_colunas_df:
                colunas_para_manter = colunas_config
                colunas_para_remover = [col for col in df.columns if col not in colunas_para_manter]
                if colunas_para_remover:
                    df = df.drop(columns=colunas_para_remover)
        else:
            skip_rows = start_row - 1 if start_row > 1 else 0
            df = pd.read_excel(arquivo, sheet_name=nome_aba, header=0, skiprows=skip_rows)
            df.columns = df.columns.str.replace('\n', ' ').str.strip()
        
        df = df.dropna(how='all')
        df = df.dropna(axis=1, how='all')
        
        return df
        
    def fase1_conversao_bruta(self):
        arquivos_do_config = list(self.pasta_origem.glob('*.xlsx')) + list(self.pasta_origem.glob('*.xls'))
        
        if not arquivos_do_config:
            logging.warning(f"Nenhum arquivo Excel encontrado em {self.pasta_origem}")
            return 0
        
        total_txt = 0
        
        for arquivo in arquivos_do_config:
            try:
                config_path = self.encontrar_config_para_arquivo(arquivo.name)
                config_atual = self.carregar_config(config_path)
                
                xls = pd.ExcelFile(arquivo)
                
                tipo_arquivo_atual = None
                if 'files' in config_atual:
                    for tipo, info in config_atual['files'].items():
                        if info.get('path', '').lower() == arquivo.name.lower():
                            tipo_arquivo_atual = tipo
                            break
                
                paginas_config = []
                if 'pages' in config_atual:
                    for pagina in config_atual['pages']:
                        if pagina.get('isApproved', False):
                            paginas_config.append(pagina)
                
                if paginas_config:
                    paginas_por_aba = {}
                    for pagina in paginas_config:
                        page_name = pagina.get('pageName')
                        page_index = pagina.get('pageIndex', 0)
                        
                        nome_aba_encontrada = None
                        if page_name and page_name in xls.sheet_names:
                            nome_aba_encontrada = page_name
                        elif isinstance(page_index, int) and page_index < len(xls.sheet_names):
                            nome_aba_encontrada = xls.sheet_names[page_index]
                        
                        if nome_aba_encontrada:
                            if nome_aba_encontrada not in paginas_por_aba:
                                paginas_por_aba[nome_aba_encontrada] = []
                            paginas_por_aba[nome_aba_encontrada].append(pagina)
                    
                    if not paginas_por_aba:
                        for nome_aba in xls.sheet_names:
                            paginas_por_aba[nome_aba] = []
                else:
                    paginas_por_aba = {nome_aba: [] for nome_aba in xls.sheet_names}
                
                for nome_aba, paginas_desta_aba in paginas_por_aba.items():
                    try:
                        if paginas_desta_aba and tipo_arquivo_atual:
                            pagina_config = paginas_desta_aba[0]
                            df = self.processar_pagina_com_config(arquivo, nome_aba, pagina_config, tipo_arquivo_atual, config_atual)
                        else:
                            df = pd.read_excel(xls, sheet_name=nome_aba)
                            df.columns = df.columns.str.replace('\n', ' ').str.strip()
                            df = df.dropna(how='all')
                            df = df.dropna(axis=1, how='all')
                        
                        nome_base = arquivo.stem
                        nome_txt = f"{nome_base}_{nome_aba}.txt"
                        caminho_txt = self.pasta_destino / nome_txt
                        
                        with open(caminho_txt, 'w', encoding='utf-8') as f:
                            for idx, row in df.iterrows():
                                f.write(f"========== REGISTRO {idx + 1} ==========\n")
                                for col in df.columns:
                                    valor = row[col]
                                    valor_str = "" if pd.isna(valor) else str(valor)
                                    f.write(f"{col}: {valor_str}\n")
                                f.write("\n")
                        
                        total_txt += 1
                        logging.info(f"Gerado: {nome_txt} ({len(df)} registros)")
                    except Exception as e:
                        logging.error(f"Erro ao processar aba {nome_aba} do arquivo {arquivo.name}: {str(e)}")
                        continue
                    
            except Exception as e:
                logging.error(f"Erro ao processar {arquivo.name}: {str(e)}")
                continue
        
        return total_txt


def configurar_logging(config=None):
    if config and 'paths' in config and 'logs' in config['paths']:
        log_dir = Path(config['paths']['logs'])
    else:
        log_dir = Path('./logs')
    
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'conversao_{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    config_dir = Path('./configs')
    config_temp = None
    if config_dir.exists():
        config_files = list(config_dir.glob('*.json'))
        if config_files:
            try:
                with open(config_files[0], 'r', encoding='utf-8') as f:
                    config_temp = json.load(f)
            except:
                pass
    
    configurar_logging(config_temp)
    
    conversor = ConversorPlanilhasTXT()
    conversor.fase1_conversao_bruta()


if __name__ == '__main__':
    main()