import os
import json
import pandas as pd
from datetime import datetime
import logging
import numpy as np
import re

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

class TradutorFinal:
    def __init__(self, pasta_gabarito='gabarito', pasta_json='jsons', pasta_saida='saidas', pasta_cache='cache', arquivo_cod='start_cod_produto.txt'):
        self.pasta_gabarito = pasta_gabarito
        self.pasta_json = pasta_json
        self.pasta_saida = pasta_saida
        self.pasta_cache = pasta_cache
        self.arquivo_cod = arquivo_cod

        os.makedirs(self.pasta_saida, exist_ok=True)
        os.makedirs(self.pasta_cache, exist_ok=True)

        # Aqui carregamos o código inicial do TXT
        self.start_cod_produto = self._carregar_codigo_inicial()

        self.cache_ncm_path = os.path.join(self.pasta_cache, 'ncm_codes.json')
        self.ncm_cache = self._carregar_cache_ncm()

    # =========================
    # LEITURA E GRAVAÇÃO DO TXT
    # =========================
    def _carregar_codigo_inicial(self):
        if not os.path.exists(self.arquivo_cod):
            with open(self.arquivo_cod, 'w') as f:
                f.write("1")
            return 1
        
        try:
            with open(self.arquivo_cod, 'r') as f:
                valor = f.read().strip()
                return int(valor)
        except:
            return 1

    def _salvar_codigo_final(self, novo_codigo):
        try:
            with open(self.arquivo_cod, 'w') as f:
                f.write(str(novo_codigo))
        except:
            pass

    # =========================

    def _limpar_texto(self, texto):
        if isinstance(texto, str):
            texto_limpo = texto.replace('\n', ' ').replace('\r', ' ')
            return texto_limpo
        return texto

    def _limpar_dataframe(self, df):
        for coluna in df.columns:
            if df[coluna].dtype == 'object':
                df[coluna] = df[coluna].apply(self._limpar_texto)
        return df

    def _extrair_nome_arquivo(self, nome_arquivo):
        padrao = r'^saida_(.+)\.json$'
        match = re.match(padrao, nome_arquivo)
        if match:
            return match.group(1)
        return None

    def _obter_nome_saida(self, nome_arquivo_json):
        nome_base = os.path.splitext(nome_arquivo_json)[0]
        nome_extraido = self._extrair_nome_arquivo(nome_arquivo_json)
        return nome_extraido if nome_extraido else nome_base

    def _carregar_cache_ncm(self):
        if os.path.exists(self.cache_ncm_path):
            try:
                with open(self.cache_ncm_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _salvar_cache_ncm(self):
        try:
            with open(self.cache_ncm_path, 'w', encoding='utf-8') as f:
                json.dump(self.ncm_cache, f, ensure_ascii=False, indent=2)
        except:
            pass

    def _carregar_gabarito(self):
        arquivos = [f for f in os.listdir(self.pasta_gabarito) if f.endswith('.xlsx')]
        if not arquivos:
            raise FileNotFoundError("Nenhum arquivo .xlsx encontrado em 'gabarito/'")

        path_gabarito = os.path.join(self.pasta_gabarito, arquivos[0])
        
        gabarito_df = pd.read_excel(path_gabarito, dtype=str)
        gabarito_df = gabarito_df.fillna('')
        colunas = list(gabarito_df.columns)
        valores_padrao = gabarito_df.iloc[0].to_dict()
        
        return colunas, valores_padrao

    def _ler_json_arquivo(self, nome_arquivo):
        try:
            with open(os.path.join(self.pasta_json, nome_arquivo), 'r', encoding='utf-8') as f:
                dados = json.load(f)
                return dados if isinstance(dados, list) else [dados]
        except:
            return []

    def _listar_arquivos_json(self):
        arquivos = [f for f in os.listdir(self.pasta_json) if f.endswith('.json')]
        if not arquivos:
            raise FileNotFoundError("Nenhum arquivo .json encontrado em 'jsons/'")
        return arquivos

    def _gerar_cod_classificacao_fis(self, df):
        if 'CLASSIFICACAO_FIS' not in df.columns:
            return df
        
        df['CLASSIFICACAO_FIS'] = df['CLASSIFICACAO_FIS'].astype(str).str.strip().str.upper()
        valores_invalidos = ['', 'NAN', 'NONE', 'NULL', 'NA']
        
        codigos_existentes = []
        if self.ncm_cache:
            codigos_existentes = [int(v) for v in self.ncm_cache.values() if v.isdigit()]

        proximo_codigo = max(codigos_existentes) + 1 if codigos_existentes else 1
        ncms_unicos = [ncm for ncm in df['CLASSIFICACAO_FIS'].unique() if ncm not in valores_invalidos]

        novos_ncms = []
        for ncm in ncms_unicos:
            if ncm not in self.ncm_cache:
                novo_codigo = f"{proximo_codigo:04d}"
                self.ncm_cache[ncm] = novo_codigo
                novos_ncms.append((ncm, novo_codigo))
                proximo_codigo += 1

        df['COD_CLASSIFICACAO_FIS'] = df['CLASSIFICACAO_FIS'].apply(
            lambda ncm: self.ncm_cache.get(ncm, '') if ncm not in valores_invalidos else ''
        )

        if novos_ncms:
            self._salvar_cache_ncm()

        return df

    def _converter_preco_para_numero(self, valor):
        if valor is None:
            return None

        valor_str = str(valor)
        valor_str = valor_str.replace('\xa0', '').replace('\u200b', '').replace('\u200e', '').replace('\u200f', '')
        valor_str = re.sub(r'[^\d.,]', '', valor_str)

        if valor_str.startswith(','):
            valor_str = '0' + valor_str

        if valor_str.count(',') == 1:
            valor_str = valor_str.replace('.', '')

        valor_str = valor_str.replace(',', '.')

        try:
            return float(valor_str)
        except:
            return None

    def _filtrar_produtos_invalidos(self, df):
        df['_custo'] = df['CUSTO'].apply(self._converter_preco_para_numero)
        df['_preco'] = df['PRECO1'].apply(self._converter_preco_para_numero)

        df_validos = df[
            ((df['_custo'].notna()) & (df['_custo'] > 0)) |
            ((df['_preco'].notna()) & (df['_preco'] > 0))
        ].copy()

        df_validos = df_validos.drop(columns=['_custo', '_preco'], errors='ignore')

        return df_validos

    def _renumerar_cod_produto(self, df, start_cod):
        if 'DESCRICAO' not in df.columns:
            return df

        descricoes_unicas = df['DESCRICAO'].drop_duplicates().tolist()

        mapeamento = {}
        codigo_atual = start_cod

        for descricao in descricoes_unicas:
            mapeamento[descricao] = codigo_atual
            codigo_atual += 1

        df['COD_PRODUTO'] = df['DESCRICAO'].map(mapeamento)

        return df, codigo_atual

    def _gerar_cod_cor(self, df):
        if 'COR' not in df.columns:
            return df
        
        df['COR'] = df['COR'].astype(str).str.strip().str.upper()
        cores_validas = df['COR'].replace(['', 'NAN', 'NONE', 'NULL'], pd.NA)
        cores_unicas = sorted([c for c in cores_validas.dropna().unique() if c])

        cor_to_code = {cor: f"{i:03d}" for i, cor in enumerate(cores_unicas, start=1)}
        
        df['COD_COR'] = df['COR'].map(cor_to_code).fillna('')

        return df

    def _formatar_numero_brasileiro(self, valor):
        try:
            num = float(valor)
            inteira = int(num)
            decimal = f"{num:.2f}".split('.')[1]
            return f"{inteira:,}".replace(',', '.') + "," + decimal
        except:
            return valor

    def _corrigir_valores(self, df, colunas, valores_padrao):
        for col in colunas:
            if col not in df.columns:
                df[col] = valores_padrao.get(col, '')

        invalidos = {'', None, np.nan, 'NaN', 'nan', 'undefined', 'null', 'NULL', 'None'}

        colunas_formatar = ['CUSTO', 'PRECO1']
        for col in colunas_formatar:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda v: self._formatar_numero_brasileiro(self._converter_preco_para_numero(v))
                    if not (pd.isna(v) or str(v).strip() in invalidos)
                    else valores_padrao.get(col, '')
                )

        df = df[colunas]

        for col in colunas:
            df[col] = df[col].apply(
                lambda v: valores_padrao.get(col, '') if (pd.isna(v) or str(v).strip() in invalidos) else v
            )

        if 'TAMANHO' in df.columns:
            df['TAMANHO'] = df['TAMANHO'].astype(str).replace(
                ['nan', 'NaN', 'None', 'NONE', 'NULL', 'null'], ''
            )

        return df

    def _processar_arquivo_json(self, nome_arquivo_json, start_cod_produto):
        nome_saida = self._obter_nome_saida(nome_arquivo_json)
        colunas, valores_padrao = self._carregar_gabarito()
        dados_json = self._ler_json_arquivo(nome_arquivo_json)
        
        if not dados_json:
            return 0, start_cod_produto
        
        df_json = pd.DataFrame(dados_json)
        df_json = self._limpar_dataframe(df_json)
        df_json = self._gerar_cod_classificacao_fis(df_json)
        df_json = self._filtrar_produtos_invalidos(df_json)

        if len(df_json) == 0:
            return 0, start_cod_produto

        df_json, novo_cod_produto = self._renumerar_cod_produto(df_json, start_cod_produto)
        df_json = self._gerar_cod_cor(df_json)
        df_final = self._corrigir_valores(df_json, colunas, valores_padrao)

        path_saida = os.path.join(self.pasta_saida, f"{nome_saida}.xlsx")
        
        with pd.ExcelWriter(path_saida, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Dados')
            
            workbook = writer.book
            worksheet = writer.sheets['Dados']
            
            if hasattr(worksheet, 'merged_cells'):
                for merged_cell in list(worksheet.merged_cells):
                    worksheet.unmerge_cells(str(merged_cell))
            
            for column in worksheet.columns:
                max_length = 0
                col_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                worksheet.column_dimensions[col_letter].width = min(max_length + 2, 50)
        
        logger.info(f"Gerado: {nome_saida}.xlsx ({len(df_final)} registros)")
        return len(df_final), novo_cod_produto

    def processar(self):
        arquivos_json = self._listar_arquivos_json()
        total = 0
        codigo_atual = self.start_cod_produto

        for nome_arquivo in arquivos_json:
            qtd, codigo_atual = self._processar_arquivo_json(nome_arquivo, codigo_atual)
            total += qtd

        # Aqui salvamos o novo código no TXT
        self._salvar_codigo_final(codigo_atual)

        logger.info(f"Total gerado: {total} registros")
        logger.info(f"Novo código salvo no TXT: {codigo_atual}")


if __name__ == "__main__":
    tradutor = TradutorFinal()
    tradutor.processar()
