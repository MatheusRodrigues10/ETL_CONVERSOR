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
    def __init__(self, pasta_gabarito='gabarito', pasta_json='jsons', pasta_saida='saidas', pasta_cache='cache'):
        self.pasta_gabarito = pasta_gabarito
        self.pasta_json = pasta_json
        self.pasta_saida = pasta_saida
        self.pasta_cache = pasta_cache
        os.makedirs(self.pasta_saida, exist_ok=True)
        os.makedirs(self.pasta_cache, exist_ok=True)
        
        self.cache_ncm_path = os.path.join(self.pasta_cache, 'ncm_codes.json')
        self.ncm_cache = self._carregar_cache_ncm()

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
        
        if nome_extraido:
            return nome_extraido
        else:
            return nome_base

    def _carregar_cache_ncm(self):
        if os.path.exists(self.cache_ncm_path):
            try:
                with open(self.cache_ncm_path, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                return cache
            except Exception as e:
                logger.warning(f"Erro ao carregar cache de NCMs: {e}")
                return {}
        else:
            return {}
    
    def _salvar_cache_ncm(self):
        try:
            with open(self.cache_ncm_path, 'w', encoding='utf-8') as f:
                json.dump(self.ncm_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar cache de NCMs: {e}")
    
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
        path = os.path.join(self.pasta_json, nome_arquivo)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                if isinstance(dados, list):
                    return dados
                elif isinstance(dados, dict):
                    return [dados]
                return []
        except Exception as e:
            logger.error(f"Erro ao ler {nome_arquivo}: {e}")
            return []
    
    def _listar_arquivos_json(self):
        arquivos = [f for f in os.listdir(self.pasta_json) if f.endswith('.json')]
        if not arquivos:
            raise FileNotFoundError("Nenhum arquivo .json encontrado em 'jsons/'")
        return arquivos

    def _gerar_cod_classificacao_fis(self, df):
        if 'CLASSIFICACAO_FIS' not in df.columns:
            logger.warning("Coluna CLASSIFICACAO_FIS nao encontrada. COD_CLASSIFICACAO_FIS nao sera gerado.")
            return df
        
        df['CLASSIFICACAO_FIS'] = df['CLASSIFICACAO_FIS'].astype(str).str.strip().str.upper()
        valores_invalidos = ['', 'NAN', 'NONE', 'NULL', 'NA']
        
        codigos_existentes = []
        if self.ncm_cache:
            codigos_existentes = [int(v) for v in self.ncm_cache.values() if v.isdigit()]
        
        proximo_codigo = max(codigos_existentes) + 1 if codigos_existentes else 1
        
        ncms_unicos = [ncm for ncm in df['CLASSIFICACAO_FIS'].unique() 
                       if ncm not in valores_invalidos]
        
        novos_ncms = []
        
        for ncm in ncms_unicos:
            if ncm not in self.ncm_cache:
                novo_codigo = f"{proximo_codigo:04d}"
                self.ncm_cache[ncm] = novo_codigo
                novos_ncms.append((ncm, novo_codigo))
                proximo_codigo += 1
        
        if 'COD_CLASSIFICACAO_FIS' not in df.columns:
            df['COD_CLASSIFICACAO_FIS'] = ''
        
        df['COD_CLASSIFICACAO_FIS'] = df['CLASSIFICACAO_FIS'].apply(
            lambda ncm: self.ncm_cache.get(ncm, '') if ncm not in valores_invalidos else ''
        )

        df['COD_CLASSIFICACAO_FIS'] = df['COD_CLASSIFICACAO_FIS'].astype(str)
        df['COD_CLASSIFICACAO_FIS'] = df['COD_CLASSIFICACAO_FIS'].replace(['nan', 'NaN', 'None', 'NONE'], '')

        for coluna in ['CLASSIFICACAO_FIS', 'COD_CLASSIFICACAO_FIS']:
            df[coluna] = df[coluna].astype(str)
            df[coluna] = df[coluna].replace(
            ['nan', 'NaN', 'None', 'NONE', 'NULL', 'null'],
            ''
        )

        if novos_ncms:
            self._salvar_cache_ncm()
        
        return df
    
    def _converter_preco_para_numero(self, valor):
        if valor is None:
            return None

        valor_str = str(valor)

        # limpa unicode invisível (NBSP, zero-width, etc)
        valor_str = valor_str.replace('\xa0', '').replace('\u200b', '').replace('\u200e', '').replace('\u200f', '')

        # remove textos tipo "R$", "USD", " ", TAB, quebras etc
        valor_str = re.sub(r'[^\d.,]', '', valor_str)

        # casos como ",00" viram "0,00"
        if valor_str.startswith(','):
            valor_str = '0' + valor_str

        # se tiver múltiplos '.' mas a vírgula for decimal, remove só separadores
        if valor_str.count(',') == 1:
            valor_str = valor_str.replace('.', '')

        # converte vírgula para ponto
        valor_str = valor_str.replace(',', '.')

        try:
            return float(valor_str)
        except:
            return None

    def _linha_tem_preco_valido(self, row):
        custo = self._converter_preco_para_numero(row.get('CUSTO'))
        preco1 = self._converter_preco_para_numero(row.get('PRECO1'))
        
        custo_valido = custo is not None and custo != 0
        preco1_valido = preco1 is not None and preco1 != 0
        
        return custo_valido or preco1_valido

    def _filtrar_produtos_invalidos(self, df):
        if 'DESCRICAO' not in df.columns:
            logger.warning("Coluna DESCRICAO nao encontrada. Pulando filtragem.")
            return df

        df['_custo_num'] = df['CUSTO'].apply(self._converter_preco_para_numero)
        df['_preco1_num'] = df['PRECO1'].apply(self._converter_preco_para_numero)

        df_validos = df[
            ((df['_custo_num'].notna()) & (df['_custo_num'] > 0)) |
            ((df['_preco1_num'].notna()) & (df['_preco1_num'] > 0))
        ].copy()

        df_validos = df_validos.drop(columns=['_custo_num', '_preco1_num'], errors='ignore')

        return df_validos

    def _renumerar_cod_produto(self, df):
        if 'DESCRICAO' not in df.columns:
            logger.warning("Coluna DESCRICAO nao encontrada. Pulando renumeracao.")
            return df
        
        descricoes_unicas = df['DESCRICAO'].drop_duplicates().tolist()
        
        mapeamento = {}
        for idx, descricao in enumerate(descricoes_unicas, start=1):
            mapeamento[descricao] = f"{idx:06d}"
        
        df['COD_PRODUTO'] = df['DESCRICAO'].map(mapeamento)
        
        return df

    def _gerar_cod_cor(self, df):
        if 'COR' not in df.columns:
            logger.warning("Coluna COR nao encontrada. COD_COR nao sera gerado.")
            return df
        
        df['COR'] = df['COR'].astype(str).str.strip().str.upper()
        cores_validas = df['COR'].replace(['', 'NAN', 'NONE', 'NULL'], pd.NA)
        cores_unicas = sorted([c for c in cores_validas.dropna().unique() if c])
        
        cor_to_code = {}
        for idx, cor in enumerate(cores_unicas, start=1):
            cor_to_code[cor] = f"{idx:03d}"
        
        if 'COD_COR' not in df.columns:
            df['COD_COR'] = ''
        
        df['COD_COR'] = df['COR'].map(cor_to_code)
        df['COD_COR'] = df['COD_COR'].fillna('')
        
        return df

    def _formatar_numero_brasileiro(self, valor):
        try:
            num = float(valor)
            parte_inteira = int(num)
            parte_decimal = num - parte_inteira
            inteira_formatada = f"{parte_inteira:,}".replace(',', '.')
            
            if parte_decimal > 0:
                decimal_str = f"{parte_decimal:.2f}".split('.')[1]
                return f"{inteira_formatada},{decimal_str}"
            else:
                return f"{inteira_formatada},00"
        except (ValueError, TypeError):
            return valor

    def _corrigir_valores(self, df, colunas, valores_padrao):
        # adiciona colunas faltantes
        for col in colunas:
            if col not in df.columns:
                df[col] = valores_padrao.get(col, '')

        invalidos = {'', None, np.nan, 'NaN', 'nan', 'undefined', 'null', 'NULL', 'None'}

        def formatar_seguro(v, col):
            num = self._converter_preco_para_numero(v)
            if num is None:
                return valores_padrao.get(col, '')
            return self._formatar_numero_brasileiro(num)

        # formata SOMENTE colunas numéricas
        colunas_formatar = ['CUSTO', 'PRECO1']

        for col in colunas_formatar:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda v: formatar_seguro(v, col)
                    if not (pd.isna(v) or str(v).strip() in invalidos)
                    else valores_padrao.get(col, '')
                )

        # garante que todas as colunas existam e respeitem a ordem do gabarito
        df = df[colunas]

        return df

    def _processar_arquivo_json(self, nome_arquivo_json):
        nome_saida = self._obter_nome_saida(nome_arquivo_json)
        colunas, valores_padrao = self._carregar_gabarito()
        dados_json = self._ler_json_arquivo(nome_arquivo_json)
        
        if not dados_json:
            logger.warning(f"Nenhum dado encontrado em {nome_arquivo_json}. Pulando...")
            return 0
        
        df_json = pd.DataFrame(dados_json)
        df_json = self._limpar_dataframe(df_json)
        df_json = self._gerar_cod_classificacao_fis(df_json)
        df_json = self._filtrar_produtos_invalidos(df_json)

        if len(df_json) == 0:
            logger.warning(f"Nenhum registro valido apos filtragem em {nome_arquivo_json}. Pulando...")
            return 0

        df_json = self._renumerar_cod_produto(df_json)
        df_json = self._gerar_cod_cor(df_json)
        df_final = self._corrigir_valores(df_json, colunas, valores_padrao)

        path_saida = os.path.join(self.pasta_saida, f"{nome_saida}.xlsx")
        
        with pd.ExcelWriter(path_saida, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Dados')
            
            workbook = writer.book
            worksheet = writer.sheets['Dados']
            
            if hasattr(worksheet, 'merged_cells'):
                merged_cells_copy = list(worksheet.merged_cells)
                for merged_cell in merged_cells_copy:
                    worksheet.unmerge_cells(str(merged_cell))
            
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        logger.info(f"Gerado: {nome_saida}.xlsx ({len(df_final)} registros)")
        
        return len(df_final)

    def processar(self):
        arquivos_json = self._listar_arquivos_json()
        total_processados = 0
        total_registros = 0

        for nome_arquivo in arquivos_json:
            try:
                registros = self._processar_arquivo_json(nome_arquivo)
                if registros > 0:
                    total_processados += 1
                    total_registros += registros
            except Exception as e:
                logger.error(f"Erro ao processar {nome_arquivo}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue

if __name__ == "__main__":
    tradutor = TradutorFinal()
    tradutor.processar()