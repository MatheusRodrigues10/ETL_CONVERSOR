import pandas as pd
from pathlib import Path
import logging
from datetime import datetime
import sys

class ConversorPlanilhasTXT:
    """Converte planilhas Excel para TXT vertical"""
    
    def __init__(self, pasta_origem='./planilhas', pasta_destino='./txt_bruto'):
        self.pasta_origem = Path(pasta_origem)
        self.pasta_destino = Path(pasta_destino)
        self.pasta_destino.mkdir(parents=True, exist_ok=True)
        
    def fase1_conversao_bruta(self):
        """Converte todos os arquivos Excel para TXT bruto em formato vertical"""
        logging.info("INICIANDO CONVERSAO: Excel para TXT (formato vertical)")
        
        arquivos_excel = list(self.pasta_origem.glob('*.xlsx')) + list(self.pasta_origem.glob('*.xls'))
        
        if not arquivos_excel:
            logging.warning(f"Nenhum arquivo Excel encontrado em {self.pasta_origem}")
            return 0
        
        total_txt = 0
        
        for arquivo in arquivos_excel:
            try:
                logging.info(f"Processando: {arquivo.name}")
                xls = pd.ExcelFile(arquivo)
                
                for nome_aba in xls.sheet_names:
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
                    logging.info(f"  -> Gerado: {nome_txt} ({len(df)} registros x {len(df.columns)} campos)")
                    
            except Exception as e:
                logging.error(f"Erro ao processar {arquivo.name}: {str(e)}")
                continue
        
        logging.info(f"CONVERSAO CONCLUIDA: {len(arquivos_excel)} arquivos Excel, {total_txt} arquivos TXT gerados")
        return total_txt


def configurar_logging():
    """Configura sistema de logs"""
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
    configurar_logging()
    
    logging.info("=== CONVERSOR DE PLANILHAS PARA TXT VERTICAL ===")
    
    conversor = ConversorPlanilhasTXT()
    conversor.fase1_conversao_bruta()
    
    logging.info("\n=== PROXIMOS PASSOS ===")
    logging.info("Execute agora: python gerador_json.py")


if __name__ == '__main__':
    main()