import pandas as pd
from pathlib import Path
import logging
from datetime import datetime
import sys
import json
import re

class ConversorPlanilhasTXT:
    """Converte planilhas Excel para TXT vertical"""
    
    def __init__(self, config_path=None, pasta_origem='./planilhas', pasta_destino='./txt_bruto'):
        if config_path is None:
            config_path = self.encontrar_config()
        
        self.config = self.carregar_config(config_path)
        self.pasta_origem = Path(pasta_origem)
        self.pasta_destino = Path(pasta_destino)
        self.pasta_destino.mkdir(parents=True, exist_ok=True)
    
    def normalizar_nome(self, nome):
        """Normaliza nome para comparação (remove caracteres especiais e converte para minúsculas)"""
        return re.sub(r'[^a-zA-Z0-9]', '', str(nome).lower().strip())
    
    def encontrar_config(self):
        """Encontra automaticamente o primeiro arquivo JSON na pasta configs (fallback)"""
        config_dir = Path('./configs')
        if not config_dir.exists():
            logging.error("Pasta configs não encontrada")
            exit(1)
            
        config_files = list(config_dir.glob('*.json'))
        if not config_files:
            logging.error("Nenhum arquivo JSON encontrado em ./configs/")
            exit(1)
        
        config_path = config_files[0]
        logging.info(f"Usando configuração padrão: {config_path}")
        return config_path
    
    def encontrar_config_para_arquivo(self, nome_arquivo_excel):
        """Encontra o config apropriado baseado no arquivo Excel sendo processado"""
        config_dir = Path('./configs')
        if not config_dir.exists():
            logging.error("Pasta configs não encontrada")
            exit(1)
            
        config_files = list(config_dir.glob('*.json'))
        if not config_files:
            logging.error("Nenhum arquivo JSON encontrado em ./configs/")
            exit(1)
        
        # Remove extensão do arquivo Excel e normaliza
        nome_arquivo_sem_ext = Path(nome_arquivo_excel).stem
        nome_arquivo_limpo = self.normalizar_nome(nome_arquivo_sem_ext)
        
        # Lista para armazenar correspondências encontradas (config, score de correspondência, nome, tipo)
        correspondencias = []
        
        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_temp = json.load(f)
                
                # Verifica se algum arquivo definido no config corresponde ao arquivo Excel
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
                            # Nome do arquivo Excel começa com o nome do XLSX (correspondência muito forte)
                            elif nome_arquivo_limpo.startswith(nome_xlsx_limpo):
                                # Score baseado na proporção: quanto maior a parte correspondente, melhor
                                proporcao = len(nome_xlsx_limpo) / len(nome_arquivo_limpo) if nome_arquivo_limpo else 0
                                score = 90 + (proporcao * 10)  # Entre 90-100
                            # Nome do XLSX contém o nome do arquivo Excel (correspondência fraca, mas possível)
                            elif nome_xlsx_limpo.startswith(nome_arquivo_limpo):
                                proporcao = len(nome_arquivo_limpo) / len(nome_xlsx_limpo) if nome_xlsx_limpo else 0
                                score = 70 + (proporcao * 10)  # Entre 70-80
                            # Nome do config está contido no nome do arquivo (correspondência média)
                            elif nome_xlsx_limpo in nome_arquivo_limpo:
                                # Penaliza correspondências muito curtas (ex: "custo" em "custobutzkepagina1")
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
            
            logging.info(f"Arquivo '{nome_arquivo_excel}' corresponde ao config '{melhor_config.name}' "
                        f"(arquivo: '{melhor_nome}' tipo: {melhor_tipo}, score: {melhor_score:.1f})")
            
            # Se há múltiplas correspondências, avisa
            if len(correspondencias) > 1:
                logging.warning(f"Encontradas {len(correspondencias)} correspondências, usando a melhor: {melhor_config.name} (score: {melhor_score:.1f})")
                for cfg, sc, nm, tp in correspondencias[1:3]:  # Mostra as 2 próximas
                    logging.debug(f"  Alternativa: {cfg.name} - {nm} ({tp}) - score: {sc:.1f}")
            
            return melhor_config
        
        # Se não encontrou correspondência, usa o primeiro config (fallback)
        logging.warning(f"Não encontrou config específico para '{nome_arquivo_excel}', usando '{config_files[0].name}' como fallback")
        return config_files[0]
    
    def carregar_config(self, config_path):
        """Carrega o arquivo JSON de configuração"""
        config_path = Path(config_path)
        if not config_path.exists():
            logging.error(f"Arquivo de configuração não encontrado: {config_path}")
            logging.error("Verifique se o caminho está correto")
            exit(1)
            
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def parse_cell_to_row(self, cell_address):
        """Converte endereço de célula (ex: 'A5') para número de linha (1-based)"""
        match = re.match(r'([A-Z]+)(\d+)', cell_address.upper())
        if match:
            return int(match.group(2))
        return 1  # Default para primeira linha
    
    def processar_pagina_com_config(self, arquivo, nome_aba, pagina_config, tipo_arquivo, config=None):
        """Processa uma página específica usando configuração do config"""
        if config is None:
            config = self.config
        
        start_cell = pagina_config.get('startCell', 'A1')
        start_row = self.parse_cell_to_row(start_cell)  # Linha onde está o cabeçalho (1-based)
        
        # Obtém as colunas do config para este tipo de arquivo
        colunas_config = []
        if 'files' in config and tipo_arquivo in config['files']:
            colunas_config = config['files'][tipo_arquivo].get('columns', [])
        elif 'columns' in pagina_config:
            colunas_config = pagina_config['columns']
        
        # Se temos colunas do config, usa elas como referência para os cabeçalhos
        if colunas_config:
            # startCell indica onde está o cabeçalho (linha start_row do Excel)
            # Pula até antes do cabeçalho (start_row - 1 linhas)
            # Usa header=0 para que a primeira linha lida seja tratada como cabeçalho
            # Mas depois vamos substituir pelos nomes do config
            skip_rows = start_row - 1  # Pula linhas antes do cabeçalho
            df = pd.read_excel(arquivo, sheet_name=nome_aba, header=0, skiprows=skip_rows)
            
            # Substitui os cabeçalhos do Excel pelos do config
            num_colunas_config = len(colunas_config)
            num_colunas_df = len(df.columns)
            
            # Cria dicionário de mapeamento: coluna atual -> coluna do config
            novo_nomes = {}
            for i, col_config in enumerate(colunas_config):
                if i < num_colunas_df:
                    # Mapeia a coluna i do DataFrame para o nome do config
                    col_atual = df.columns[i]
                    novo_nomes[col_atual] = col_config
            
            # Renomeia as colunas
            df = df.rename(columns=novo_nomes)
            
            # Se o config tem mais colunas que o DataFrame, adiciona colunas vazias
            if num_colunas_config > num_colunas_df:
                for i in range(num_colunas_df, num_colunas_config):
                    df[colunas_config[i]] = None
            
            # Se o DataFrame tem mais colunas que o config, remove as extras
            elif num_colunas_config < num_colunas_df:
                colunas_para_manter = colunas_config
                colunas_para_remover = [col for col in df.columns if col not in colunas_para_manter]
                if colunas_para_remover:
                    df = df.drop(columns=colunas_para_remover)
        else:
            # Se não há colunas no config, lê normalmente
            skip_rows = start_row - 1 if start_row > 1 else 0
            df = pd.read_excel(arquivo, sheet_name=nome_aba, header=0, skiprows=skip_rows)
            df.columns = df.columns.str.replace('\n', ' ').str.strip()
        
        # Remove linhas completamente vazias
        df = df.dropna(how='all')
        # Remove colunas completamente vazias
        df = df.dropna(axis=1, how='all')
        
        return df
        
    def fase1_conversao_bruta(self):
        """Converte todos os arquivos Excel para TXT bruto em formato vertical usando config"""
        logging.info("INICIANDO CONVERSAO: Excel para TXT (formato vertical)")
        
        # Busca todos os arquivos Excel na pasta (agora encontra o config correto para cada um)
        arquivos_do_config = list(self.pasta_origem.glob('*.xlsx')) + list(self.pasta_origem.glob('*.xls'))
        
        if not arquivos_do_config:
            logging.warning(f"Nenhum arquivo Excel encontrado em {self.pasta_origem}")
            return 0
        
        total_txt = 0
        
        for arquivo in arquivos_do_config:
            try:
                logging.info(f"Processando: {arquivo.name}")
                
                # Encontra o config correto para este arquivo Excel
                config_path = self.encontrar_config_para_arquivo(arquivo.name)
                config_atual = self.carregar_config(config_path)
                
                xls = pd.ExcelFile(arquivo)
                
                # Identifica qual tipo de arquivo é este (custo ou venda) usando o config atual
                tipo_arquivo_atual = None
                if 'files' in config_atual:
                    for tipo, info in config_atual['files'].items():
                        if info.get('path', '').lower() == arquivo.name.lower():
                            tipo_arquivo_atual = tipo
                            break
                
                # Verifica se há configuração de páginas no config atual
                paginas_config = []
                if 'pages' in config_atual:
                    for pagina in config_atual['pages']:
                        if pagina.get('isApproved', False):
                            paginas_config.append(pagina)
                
                # Se houver páginas configuradas, processa apenas essas
                if paginas_config:
                    # Mapeia páginas para abas
                    paginas_por_aba = {}
                    for pagina in paginas_config:
                        page_name = pagina.get('pageName')
                        page_index = pagina.get('pageIndex', 0)
                        
                        # Tenta encontrar a aba pelo nome ou índice
                        nome_aba_encontrada = None
                        if page_name and page_name in xls.sheet_names:
                            nome_aba_encontrada = page_name
                        elif isinstance(page_index, int) and page_index < len(xls.sheet_names):
                            nome_aba_encontrada = xls.sheet_names[page_index]
                        
                        if nome_aba_encontrada:
                            if nome_aba_encontrada not in paginas_por_aba:
                                paginas_por_aba[nome_aba_encontrada] = []
                            paginas_por_aba[nome_aba_encontrada].append(pagina)
                    
                    # Se não conseguiu mapear nenhuma aba, processa todas (fallback)
                    if not paginas_por_aba:
                        logging.warning(f"Não foi possível mapear páginas do config para abas do arquivo {arquivo.name}, processando todas as abas")
                        for nome_aba in xls.sheet_names:
                            paginas_por_aba[nome_aba] = []
                else:
                    # Se não houver config de páginas, processa todas as abas
                    paginas_por_aba = {nome_aba: [] for nome_aba in xls.sheet_names}
                
                    # Processa cada aba
                for nome_aba, paginas_desta_aba in paginas_por_aba.items():
                    try:
                        # Se há páginas configuradas para esta aba, usa a primeira
                        if paginas_desta_aba and tipo_arquivo_atual:
                            pagina_config = paginas_desta_aba[0]  # Usa a primeira página configurada
                            # Usa o config atual para processar a página
                            df = self.processar_pagina_com_config(arquivo, nome_aba, pagina_config, tipo_arquivo_atual, config_atual)
                            logging.info(f"  Processando aba '{nome_aba}' com config (startCell: {pagina_config.get('startCell', 'A1')})")
                        else:
                            # Fallback: processa sem config
                            df = pd.read_excel(xls, sheet_name=nome_aba)
                            df.columns = df.columns.str.replace('\n', ' ').str.strip()
                            df = df.dropna(how='all')
                            df = df.dropna(axis=1, how='all')
                            logging.info(f"  Processando aba '{nome_aba}' sem config (fallback)")
                        
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
                        logging.info(f"  -> Gerado: {nome_txt} ({len(df)} registros x {len(df.columns)} campos)")
                    except Exception as e:
                        logging.error(f"Erro ao processar aba {nome_aba} do arquivo {arquivo.name}: {str(e)}")
                        import traceback
                        logging.error(traceback.format_exc())
                        continue
                    
            except Exception as e:
                logging.error(f"Erro ao processar {arquivo.name}: {str(e)}")
                continue
        
        logging.info(f"CONVERSAO CONCLUIDA: {len(arquivos_do_config)} arquivos Excel, {total_txt} arquivos TXT gerados")
        return total_txt


def configurar_logging(config=None):
    """Configura sistema de logs"""
    # Tenta obter pasta de logs do config, senão usa padrão
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
    # Carrega config temporariamente para configurar logging
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
    
    logging.info("=== CONVERSOR DE PLANILHAS PARA TXT VERTICAL ===")
    
    conversor = ConversorPlanilhasTXT()
    conversor.fase1_conversao_bruta()
    
    logging.info("\n=== PROXIMOS PASSOS ===")
    logging.info("Execute agora: python gerador_json.py")


if __name__ == '__main__':
    main()