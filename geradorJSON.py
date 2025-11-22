import json
import logging
from pathlib import Path
import re

class GeradorJSON:
    def __init__(self, config_path=None, pasta_txt='./txt_bruto', pasta_destino='./json_final'):
        if config_path is None:
            config_path = self.encontrar_config()
        
        self.config = self.carregar_config(config_path)
        self.pasta_txt = Path(pasta_txt)
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
    
    def normalizar_nome(self, nome):
        return re.sub(r'[^a-zA-Z0-9]', '', nome.lower().strip())
    
    def comparar_nomes(self, nome1, nome2):
        return self.normalizar_nome(nome1) == self.normalizar_nome(nome2)
    
    def encontrar_valor_registro(self, linhas, coluna_procurada):
        for linha in linhas:
            if ':' in linha:
                coluna, valor = linha.split(':', 1)
                if self.comparar_nomes(coluna.strip(), coluna_procurada):
                    return valor.strip()
        return ""
    
    def extrair_variacoes_cores(self, linhas):
        """Extrai as variações de cores e preços do registro"""
        variacoes = []
        colunas_cores = [
            "Indoor IV", "Indoor I", "Outdoor V Sunbrella", 
            "Outdoor IV Docril/Boucle", "Outdoor II Olefin/Courvin", 
            "Outdoor I Acquablock", "Sem Almofada/ Kit"
        ]
        
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
        
    def processar_arquivo_txt(self, arquivo_txt):
        registros = []
        nomes_usados = {}

        with open(arquivo_txt, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        blocos = conteudo.split('========== REGISTRO ')[1:]
        
        for bloco in blocos:
            linhas = bloco.split('\n')
            registro = {}
            
            # variações de cores
            variacoes_cores = self.extrair_variacoes_cores(linhas)
            
            for mapeamento in self.config['columnMapping']:
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

        return registros

    
    def gerar_json_final(self):
        logging.info("INICIANDO GERACAO JSON")
        
        arquivos_txt = list(self.pasta_txt.glob('*.txt'))
        total_gerados = 0
        
        for arquivo in arquivos_txt:
            logging.info(f"Processando: {arquivo.name}")
            dados = self.processar_arquivo_txt(arquivo)
            
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