import json
import logging
from pathlib import Path
import re

class GeradorJSON:
    def __init__(self, config_path=None, pasta_txt='./txt_bruto', pasta_destino='./json_final'):
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
        
        if nome_arquivo_txt is None:
            return config_files[0]
        
        nome_arquivo_sem_ext = Path(nome_arquivo_txt).stem
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
    
    def normalizar_nome(self, nome):
        return re.sub(r'[^a-zA-Z0-9]', '', nome.lower().strip())
    
    def comparar_nomes(self, nome1, nome2):
        return self.normalizar_nome(nome1) == self.normalizar_nome(nome2)
    
    def identificar_tipo_arquivo(self, nome_arquivo_txt, config=None):
        if config is None:
            config = self.config
        
        if config is None:
            nome_arquivo_limpo = self.normalizar_nome(nome_arquivo_txt)
            if 'custo' in nome_arquivo_limpo:
                return 'custo'
            elif 'venda' in nome_arquivo_limpo:
                return 'venda'
            return None
        
        nome_arquivo_limpo = self.normalizar_nome(nome_arquivo_txt)
        
        if 'files' in config:
            for tipo, info in config['files'].items():
                if 'path' in info:
                    nome_xlsx = Path(info['path']).stem
                    nome_xlsx_limpo = self.normalizar_nome(nome_xlsx)
                    if nome_xlsx_limpo in nome_arquivo_limpo or nome_arquivo_limpo in nome_xlsx_limpo:
                        return tipo
        
        nome_arquivo_limpo = self.normalizar_nome(nome_arquivo_txt)
        if 'custo' in nome_arquivo_limpo:
            return 'custo'
        elif 'venda' in nome_arquivo_limpo:
            return 'venda'
        return None
    
    def encontrar_valor_registro(self, linhas, coluna_procurada):
        for linha in linhas:
            if ':' in linha:
                coluna, valor = linha.split(':', 1)
                if self.comparar_nomes(coluna.strip(), coluna_procurada):
                    return valor.strip()
        return ""
    
    def obter_colunas_cores_do_config(self, tipo_arquivo, log_fallback=True):
        colunas_cores = []
        if 'columnMapping' in self.config:
            for mapeamento in self.config['columnMapping']:
                if (mapeamento.get('sourceFile') == tipo_arquivo and
                    mapeamento.get('gabaritoColumn') == 'COR' and 
                    isinstance(mapeamento.get('sourceColumn'), list)):
                    colunas_cores = mapeamento['sourceColumn']
                    break
            
            if not colunas_cores:
                tipo_fallback = 'venda' if tipo_arquivo == 'custo' else 'custo'
                for mapeamento in self.config['columnMapping']:
                    if (mapeamento.get('sourceFile') == tipo_fallback and
                        mapeamento.get('gabaritoColumn') == 'COR' and 
                        isinstance(mapeamento.get('sourceColumn'), list)):
                        colunas_cores = mapeamento['sourceColumn']
                        break
            
            if not colunas_cores:
                for mapeamento in self.config['columnMapping']:
                    if (mapeamento.get('gabaritoColumn') == 'COR' and 
                        isinstance(mapeamento.get('sourceColumn'), list)):
                        colunas_cores = mapeamento['sourceColumn']
                        break
        return colunas_cores
    
    def extrair_variacoes_cores(self, linhas, tipo_arquivo):
        variacoes = []
        colunas_cores = self.obter_colunas_cores_do_config(tipo_arquivo, log_fallback=False)
        
        if not colunas_cores:
            return variacoes
        
        for coluna_cor in colunas_cores:
            valor = self.encontrar_valor_registro(linhas, coluna_cor)
            if valor and valor != "0" and valor != "":
                cor_limpa = coluna_cor.replace('\n', ' ').strip()
                variacoes.append({
                    "nome_cor": cor_limpa,
                    "preco": valor
                })
        
        return variacoes
        
    def obter_colunas_source_mapping(self, tipo_arquivo=None):
        colunas_source = set()
        
        if 'columnMapping' not in self.config:
            return colunas_source
        
        for mapeamento in self.config['columnMapping']:
            if tipo_arquivo and mapeamento.get('sourceFile') != tipo_arquivo:
                continue
            
            source_column = mapeamento.get('sourceColumn')
            
            if isinstance(source_column, list):
                for col in source_column:
                    colunas_source.add(col)
            elif isinstance(source_column, str) and source_column != "__EMPTY__":
                colunas_source.add(source_column)
        
        return colunas_source
    
    def registro_eh_header(self, linhas, colunas_source):
        if not colunas_source:
            return False
        
        colunas_source_encontradas = set()
        colunas_source_vazias = set()
        outras_colunas = set()
        
        for linha in linhas:
            if ':' in linha:
                coluna, valor = linha.split(':', 1)
                coluna_limpa = coluna.strip()
                valor_limpo = valor.strip()
                coluna_normalizada = self.normalizar_nome(coluna_limpa)
                
                eh_coluna_source = False
                for source_col in colunas_source:
                    source_col_normalizada = self.normalizar_nome(source_col)
                    if coluna_normalizada == source_col_normalizada:
                        eh_coluna_source = True
                        colunas_source_encontradas.add(coluna_normalizada)
                        if not valor_limpo or valor_limpo == "0" or valor_limpo == "0.0":
                            colunas_source_vazias.add(coluna_normalizada)
                        break
                
                if not eh_coluna_source and valor_limpo and valor_limpo != "0" and valor_limpo != "0.0":
                    outras_colunas.add(coluna_normalizada)
        
        if colunas_source_encontradas:
            if len(colunas_source_vazias) == len(colunas_source_encontradas) and not outras_colunas:
                return True
            if not outras_colunas:
                return True
        
        return False
    
    def processar_arquivo_txt(self, arquivo_txt, tipo_arquivo=None, config=None):
        registros = []
        nomes_usados = {}
        
        if config is None:
            config_path = self.encontrar_config(arquivo_txt.name)
            config = self.carregar_config(config_path)
        
        self.config = config
        
        if tipo_arquivo is None:
            tipo_arquivo = self.identificar_tipo_arquivo(arquivo_txt.name, config)
        
        colunas_source = self.obter_colunas_source_mapping(tipo_arquivo)
        
        mapeamentos_filtrados = []
        if tipo_arquivo and 'columnMapping' in self.config:
            for mapeamento in self.config['columnMapping']:
                if mapeamento.get('sourceFile') == tipo_arquivo:
                    mapeamentos_filtrados.append(mapeamento)
            
            if not mapeamentos_filtrados:
                tipo_fallback = 'venda' if tipo_arquivo == 'custo' else 'custo'
                for mapeamento in self.config['columnMapping']:
                    if mapeamento.get('sourceFile') == tipo_fallback:
                        mapeamentos_filtrados.append(mapeamento)
            
            if not mapeamentos_filtrados:
                mapeamentos_filtrados = self.config.get('columnMapping', [])
        else:
            mapeamentos_filtrados = self.config.get('columnMapping', [])

        with open(arquivo_txt, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        blocos = conteudo.split('========== REGISTRO ')[1:]
        
        for bloco in blocos:
            linhas = bloco.split('\n')
            
            if self.registro_eh_header(linhas, colunas_source):
                continue
            
            registro = {}
            variacoes_cores = self.extrair_variacoes_cores(linhas, tipo_arquivo) if tipo_arquivo else self.extrair_variacoes_cores(linhas, None)
            
            for mapeamento in mapeamentos_filtrados:
                coluna_gabarito = mapeamento['gabaritoColumn']
                coluna_origem = mapeamento['sourceColumn']

                if coluna_origem == "__EMPTY__":
                    if 'name' in mapeamento:
                        if mapeamento['name'] in ["VAZIO", "MERGE"]:
                            continue
                        registro[coluna_gabarito] = mapeamento['name']
                    continue

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

                valor = self.encontrar_valor_registro(linhas, coluna_origem)
                if valor and valor not in ["", "MERGE"]:
                    registro[coluna_gabarito] = valor
            
            if "DESCRICAO" not in registro:
                registro["DESCRICAO"] = "SEM NOME"

            nome_original = registro["DESCRICAO"].strip()
            nome_base = re.sub(r'\s+', ' ', nome_original)

            if nome_base not in nomes_usados:
                nomes_usados[nome_base] = 0
            else:
                nomes_usados[nome_base] += 1
                registro["DESCRICAO"] = f"{nome_base} ({nomes_usados[nome_base]})"

            registros.append(registro)

        return registros

    
    def gerar_json_final(self):
        arquivos_txt = list(self.pasta_txt.glob('*.txt'))
        total_gerados = 0
        
        for arquivo in arquivos_txt:
            config_path = self.encontrar_config(arquivo.name)
            config = self.carregar_config(config_path)
            dados = self.processar_arquivo_txt(arquivo, config=config)
            
            nome_json = arquivo.stem + '.json'
            caminho_json = self.pasta_destino / nome_json
            
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            
            total_gerados += 1
            logging.info(f"Gerado: {nome_json} ({len(dados)} registros)")
        
        return total_gerados

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    
    gerador = GeradorJSON()
    gerador.gerar_json_final()

if __name__ == '__main__':
    main()