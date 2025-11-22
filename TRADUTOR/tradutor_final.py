import os
import json
import pandas as pd
from datetime import datetime
import logging
import numpy as np
import re

# Configuracao basica de log
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)

class TradutorFinal:
    def __init__(self, pasta_gabarito='gabarito', pasta_json='jsons', pasta_saida='saidas', pasta_cache='cache'):
        self.pasta_gabarito = pasta_gabarito
        self.pasta_json = pasta_json
        self.pasta_saida = pasta_saida
        self.pasta_cache = pasta_cache
        os.makedirs(self.pasta_saida, exist_ok=True)
        os.makedirs(self.pasta_cache, exist_ok=True)
        
        # Arquivo de cache para NCMs
        self.cache_ncm_path = os.path.join(self.pasta_cache, 'ncm_codes.json')
        self.ncm_cache = self._carregar_cache_ncm()

    def _limpar_texto(self, texto):
        """
        Versão ultra-conservativa: remove apenas quebras de linha e conteúdo após _
        PRESERVA COMPLETAMENTE a formatação original de espaços
        """
        if isinstance(texto, str):
            # Remove quebras de linha - substitui por espaço normal
            texto_limpo = texto.replace('\n', ' ').replace('\r', ' ')
            
            return texto_limpo
        return texto

    def _limpar_dataframe(self, df):
        """
        Aplica limpeza de texto em todas as colunas do DataFrame
        """
        logger.info("Limpando quebras de linha e conteúdo após '_' dos textos...")
        
        # Aplica a limpeza em todas as colunas que são strings
        for coluna in df.columns:
            if df[coluna].dtype == 'object':  # Colunas do tipo string/object
                df[coluna] = df[coluna].apply(self._limpar_texto)
        
        return df

    def _extrair_nome_arquivo(self, nome_arquivo):
        """
        Extrai o nome do arquivo JSON no padrao saida_{NOME}.json
        Retorna o {NOME} ou None se nao encontrar o padrao
        """
        # Padrao para saida_{NOME}.json
        padrao = r'^saida_(.+)\.json$'
        match = re.match(padrao, nome_arquivo)
        if match:
            return match.group(1)
        return None

    def _obter_nome_saida(self):
        """
        Obtem o nome para o arquivo de saida baseado nos JSONs disponiveis
        Se houver multiplos arquivos, usa o primeiro encontrado
        """
        arquivos_json = [f for f in os.listdir(self.pasta_json) if f.endswith('.json')]
        
        if not arquivos_json:
            raise FileNotFoundError("Nenhum arquivo .json encontrado em 'jsons/'")
        
        # Tenta extrair nome do primeiro arquivo JSON
        primeiro_arquivo = arquivos_json[0]
        nome_extraido = self._extrair_nome_arquivo(primeiro_arquivo)
        
        if nome_extraido:
            logger.info(f"Nome extraido do JSON: {nome_extraido}")
            return nome_extraido
        else:
            # Se nao encontrar o padrao, usa o nome do arquivo sem extensao
            nome_base = os.path.splitext(primeiro_arquivo)[0]
            logger.info(f"Usando nome base do arquivo: {nome_base}")
            return nome_base

    def _carregar_cache_ncm(self):
        """
        Carrega o cache de NCMs (CLASSIFICACAO_FIS -> COD_CLASSIFICACAO_FIS)
        Se nao existir, cria um novo
        """
        if os.path.exists(self.cache_ncm_path):
            try:
                with open(self.cache_ncm_path, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                logger.info(f"Cache de NCMs carregado: {len(cache)} registros")
                return cache
            except Exception as e:
                logger.warning(f"Erro ao carregar cache de NCMs: {e}")
                return {}
        else:
            logger.info("Criando novo cache de NCMs")
            return {}
    
    def _salvar_cache_ncm(self):
        """Salva o cache de NCMs no arquivo JSON"""
        try:
            with open(self.cache_ncm_path, 'w', encoding='utf-8') as f:
                json.dump(self.ncm_cache, f, ensure_ascii=False, indent=2)
            logger.info(f"Cache de NCMs salvo: {self.cache_ncm_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar cache de NCMs: {e}")
    
    def _carregar_gabarito(self):
        """Le o gabarito e obtem colunas + valores padrao"""
        arquivos = [f for f in os.listdir(self.pasta_gabarito) if f.endswith('.xlsx')]
        if not arquivos:
            raise FileNotFoundError("Nenhum arquivo .xlsx encontrado em 'gabarito/'")

        path_gabarito = os.path.join(self.pasta_gabarito, arquivos[0])
        logger.info(f"Lendo gabarito: {path_gabarito}")
        
        # Le preservando os tipos de dados originais
        gabarito_df = pd.read_excel(path_gabarito, dtype=str)  # Le tudo como string para preservar zeros
        gabarito_df = gabarito_df.fillna('')
        colunas = list(gabarito_df.columns)
        
        # Converte para dict mantendo os valores exatos (com zeros)
        valores_padrao = gabarito_df.iloc[0].to_dict()
        
        # Log para debug - mostra alguns valores padrao
        logger.info("Valores padrao carregados (exemplos):")
        for col, val in list(valores_padrao.items())[:5]:
            logger.info(f"  {col}: '{val}' (tipo: {type(val).__name__})")
        
        return colunas, valores_padrao

    def _ler_jsons(self):
        """Le todos os JSONs da pasta jsons"""
        jsons = []
        arquivos = [f for f in os.listdir(self.pasta_json) if f.endswith('.json')]
        if not arquivos:
            raise FileNotFoundError("Nenhum arquivo .json encontrado em 'jsons/'")

        for arq in arquivos:
            path = os.path.join(self.pasta_json, arq)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    if isinstance(dados, list):
                        jsons.extend(dados)
                    elif isinstance(dados, dict):
                        jsons.append(dados)
                    logger.info(f"Lido com sucesso: {arq}")
            except Exception as e:
                logger.error(f"Erro ao ler {arq}: {e}")
        
        df = pd.DataFrame(jsons)
        
        # Aplica limpeza de texto nos dados lidos
        df = self._limpar_dataframe(df)
        
        return df

    def _gerar_cod_classificacao_fis(self, df):
        """
        Gera COD_CLASSIFICACAO_FIS automaticamente baseado em CLASSIFICACAO_FIS (NCM)
        - Reutiliza codigos existentes do cache
        - Gera novos codigos sequenciais para NCMs novos
        - Salva tudo no cache para reutilizacao futura
        """
        if 'CLASSIFICACAO_FIS' not in df.columns:
            logger.warning("Coluna CLASSIFICACAO_FIS nao encontrada. COD_CLASSIFICACAO_FIS nao sera gerado.")
            return df
        
        logger.info("\nGerando codigos de classificacao fiscal (NCM)...")
        
        # Normaliza valores da coluna CLASSIFICACAO_FIS
        df['CLASSIFICACAO_FIS'] = df['CLASSIFICACAO_FIS'].astype(str).str.strip().str.upper()
        
        # Valores considerados invalidos/vazios
        valores_invalidos = ['', 'NAN', 'NONE', 'NULL', 'NA']
        
        # Encontra o maior codigo ja usado no cache
        codigos_existentes = []
        if self.ncm_cache:
            codigos_existentes = [int(v) for v in self.ncm_cache.values() if v.isdigit()]
        
        proximo_codigo = max(codigos_existentes) + 1 if codigos_existentes else 1
        
        # Obtem NCMs unicos do DataFrame atual
        ncms_unicos = [ncm for ncm in df['CLASSIFICACAO_FIS'].unique() 
                       if ncm not in valores_invalidos]
        
        novos_ncms = []
        ncms_reutilizados = []
        
        # Processa cada NCM unico
        for ncm in ncms_unicos:
            if ncm in self.ncm_cache:
                # NCM ja existe no cache, reutiliza o codigo
                ncms_reutilizados.append((ncm, self.ncm_cache[ncm]))
            else:
                # NCM novo, gera codigo sequencial
                novo_codigo = f"{proximo_codigo:04d}"
                self.ncm_cache[ncm] = novo_codigo
                novos_ncms.append((ncm, novo_codigo))
                proximo_codigo += 1
        
        # Log de estatisticas
        logger.info(f"NCMs processados:")
        logger.info(f"   - Reutilizados do cache: {len(ncms_reutilizados)}")
        logger.info(f"   - Novos codigos gerados: {len(novos_ncms)}")
        logger.info(f"   - Total no cache agora: {len(self.ncm_cache)}")
        
        # Mostra exemplos de NCMs reutilizados
        if ncms_reutilizados:
            logger.info(f"\nCodigos reutilizados:")
            for ncm, cod in ncms_reutilizados[:5]:
                logger.info(f"   {cod} -> {ncm}")
            if len(ncms_reutilizados) > 5:
                logger.info(f"   ... e mais {len(ncms_reutilizados) - 5}")
        
        # Mostra exemplos de NCMs novos
        if novos_ncms:
            logger.info(f"\nNovos codigos gerados:")
            for ncm, cod in novos_ncms[:5]:
                logger.info(f"   {cod} -> {ncm}")
            if len(novos_ncms) > 5:
                logger.info(f"   ... e mais {len(novos_ncms) - 5}")
        
        # Cria coluna COD_CLASSIFICACAO_FIS se nao existir
        if 'COD_CLASSIFICACAO_FIS' not in df.columns:
            df['COD_CLASSIFICACAO_FIS'] = ''
        
        # Aplica mapeamento do cache
        df['COD_CLASSIFICACAO_FIS'] = df['CLASSIFICACAO_FIS'].apply(
            lambda ncm: self.ncm_cache.get(ncm, '') if ncm not in valores_invalidos else ''
        )

        # Garante que nada vira NaN
        df['COD_CLASSIFICACAO_FIS'] = df['COD_CLASSIFICACAO_FIS'].astype(str)
        df['COD_CLASSIFICACAO_FIS'] = df['COD_CLASSIFICACAO_FIS'].replace(['nan', 'NaN', 'None', 'NONE'], '')

        for coluna in ['CLASSIFICACAO_FIS', 'COD_CLASSIFICACAO_FIS']:
            df[coluna] = df[coluna].astype(str)
            df[coluna] = df[coluna].replace(
            ['nan', 'NaN', 'None', 'NONE', 'NULL', 'null'],
            ''
        )

        # Salva cache atualizado
        if novos_ncms:
            self._salvar_cache_ncm()
            logger.info(f"Cache atualizado e salvo em: {self.cache_ncm_path}")
        
        return df
    
    def _converter_preco_para_numero(self, valor):
        """
        Converte valores de preco (string ou numero) para float
        Exemplos: "900,10" -> 900.10 | "1.234,56" -> 1234.56 | 0 -> 0.0 | null -> None
        """
        if valor is None or pd.isna(valor):
            return None
        
        if isinstance(valor, (int, float)):
            return float(valor)
        
        # Se for string, tenta converter do formato brasileiro
        valor_str = str(valor).strip()
        
        # Valores considerados invalidos
        if valor_str.upper() in ['', 'NAN', 'NONE', 'NULL', 'NA']:
            return None
        
        try:
            # Remove pontos (separador de milhares) e substitui virgula por ponto
            valor_limpo = valor_str.replace('.', '').replace(',', '.')
            return float(valor_limpo)
        except (ValueError, AttributeError):
            return None

    def _linha_tem_preco_valido(self, row):
        """
        Verifica se a linha tem pelo menos CUSTO OU PRECO1 validos (nao null, nao zero)
        """
        custo = self._converter_preco_para_numero(row.get('CUSTO'))
        preco1 = self._converter_preco_para_numero(row.get('PRECO1'))
        
        # Considera valido se pelo menos um dos dois for != 0 e != None
        custo_valido = custo is not None and custo != 0
        preco1_valido = preco1 is not None and preco1 != 0
        
        return custo_valido or preco1_valido

    def _filtrar_produtos_invalidos(self, df):
        """
        Remove TODAS as linhas onde CUSTO OU PRECO1 for inválido (null, 0, NaN)
        Mas mantém o produto se pelo menos UMA variação tiver AMBOS válidos
        """
        if 'DESCRICAO' not in df.columns:
            logger.warning("Coluna DESCRICAO nao encontrada. Pulando filtragem.")
            return df
        
        logger.info("\nFiltrando produtos invalidos...")
        total_antes = len(df)
        
        # Funcao auxiliar para verificar se AMBOS os precos sao validos
        def _ambos_precos_validos(custo, preco1):
            # Verifica CUSTO
            if custo is None or pd.isna(custo):
                return False
            
            # Se for string
            if isinstance(custo, str):
                custo_limpo = custo.strip().replace('.', '').replace(',', '.')
                if not custo_limpo or custo_limpo.upper() in ['NAN', 'NONE', 'NULL', 'NA']:
                    return False
                try:
                    custo_float = float(custo_limpo)
                    if custo_float == 0:
                        return False
                except (ValueError, AttributeError):
                    return False
            elif isinstance(custo, (int, float)):
                if custo == 0:
                    return False
            else:
                return False
            
            # Verifica PRECO1
            if preco1 is None or pd.isna(preco1):
                return False
            
            if isinstance(preco1, str):
                preco1_limpo = preco1.strip().replace('.', '').replace(',', '.')
                if not preco1_limpo or preco1_limpo.upper() in ['NAN', 'NONE', 'NULL', 'NA']:
                    return False
                try:
                    preco1_float = float(preco1_limpo)
                    if preco1_float == 0:
                        return False
                except (ValueError, AttributeError):
                    return False
            elif isinstance(preco1, (int, float)):
                if preco1 == 0:
                    return False
            else:
                return False
            
            # Se chegou aqui, AMBOS sao validos
            return True
        
        # DEBUG: Mostra alguns valores antes da filtragem
        logger.info("DEBUG - Amostra de valores antes da filtragem:")
        for idx, row in df.head(10).iterrows():
            custo = row.get('CUSTO')
            preco1 = row.get('PRECO1')
            ambos_validos = _ambos_precos_validos(custo, preco1)
            logger.info(f"  {row['DESCRICAO'][:30]}... CUSTO='{custo}' PRECO1='{preco1}' -> AMBOS_VALIDOS={ambos_validos}")
        
        # Marca linhas onde AMBOS os precos sao validos
        df['_ambos_validos'] = df.apply(
            lambda row: _ambos_precos_validos(row.get('CUSTO'), row.get('PRECO1')), 
            axis=1
        )
        
        # DEBUG: Mostra estatisticas
        linhas_ambos_validos = df['_ambos_validos'].sum()
        logger.info(f"DEBUG - Linhas com AMBOS precos validos: {linhas_ambos_validos}/{len(df)}")
        
        # Identifica produtos que tem pelo menos UMA variacao com ambos validos
        produtos_com_variacao_valida = df[df['_ambos_validos']]['DESCRICAO'].unique()
        logger.info(f"DEBUG - Produtos com pelo menos 1 variacao valida: {len(produtos_com_variacao_valida)}")
        
        # Filtra: mantem apenas produtos que tem pelo menos 1 variacao valida
        # E desses produtos, mantem apenas as linhas onde AMBOS sao validos
        df_filtrado = df[
            (df['DESCRICAO'].isin(produtos_com_variacao_valida)) & 
            (df['_ambos_validos'])
        ].copy()
        
        # Remove coluna temporaria
        df_filtrado = df_filtrado.drop(columns=['_ambos_validos'])
        
        total_depois = len(df_filtrado)
        removidos = total_antes - total_depois
        
        if removidos > 0:
            logger.info(f"Removidos {removidos} registros invalidos")
            logger.info(f"Registros restantes: {total_depois}")
            
            # Mostra estatisticas
            descricoes_antes = set(df['DESCRICAO'].unique())
            descricoes_depois = set(df_filtrado['DESCRICAO'].unique())
            descricoes_removidas = descricoes_antes - descricoes_depois
            
            if descricoes_removidas:
                logger.info(f"\nProdutos completamente removidos ({len(descricoes_removidas)}):")
                for desc in sorted(list(descricoes_removidas))[:10]:
                    variacoes = len(df[df['DESCRICAO'] == desc])
                    logger.info(f"   - {desc} ({variacoes} variacoes - NENHUMA com ambos precos validos)")
            
            # Mostra produtos mantidos
            logger.info(f"\nProdutos mantidos: {len(descricoes_depois)}")
            for desc in sorted(list(descricoes_depois))[:5]:
                produto_df = df_filtrado[df_filtrado['DESCRICAO'] == desc]
                variacoes_validas = len(produto_df)
                logger.info(f"   - {desc}: {variacoes_validas} variacoes com AMBOS precos validos")
                
        else:
            logger.info("Nenhum registro removido - todos tem AMBOS precos validos")
        
        return df_filtrado




    def _renumerar_cod_produto(self, df):
        """
        Renumera COD_PRODUTO de forma sequencial baseado em DESCRICAO
        Mantém o mesmo código para todas as variações do mesmo produto
        """
        if 'DESCRICAO' not in df.columns:
            logger.warning("Coluna DESCRICAO nao encontrada. Pulando renumeracao.")
            return df
        
        logger.info("\nRenumerando codigos de produto...")
        
        # Obtem descricoes unicas na ordem que aparecem
        descricoes_unicas = df['DESCRICAO'].drop_duplicates().tolist()
        
        # Cria mapeamento DESCRICAO -> COD_PRODUTO sequencial
        mapeamento = {}
        for idx, descricao in enumerate(descricoes_unicas, start=1):
            mapeamento[descricao] = f"{idx:06d}"
        
        # Aplica mapeamento
        df['COD_PRODUTO'] = df['DESCRICAO'].map(mapeamento)
        
        logger.info(f"Gerados {len(mapeamento)} codigos unicos de produto")
        logger.info(f"Exemplos:")
        for desc, cod in list(mapeamento.items())[:5]:
            contagem = len(df[df['DESCRICAO'] == desc])
            logger.info(f"   {cod} -> {desc} ({contagem} variacoes)")
        
        return df

    def _gerar_cod_cor(self, df):
        """
        Gera COD_COR automaticamente baseado na coluna COR
        - Cada COR unica recebe um codigo sequencial (001, 002, 003...)
        - Se a mesma COR aparecer em outros produtos, mantem o mesmo codigo
        """
        if 'COR' not in df.columns:
            logger.warning("Coluna COR nao encontrada. COD_COR nao sera gerado.")
            return df
        
        logger.info("\nGerando codigos de cor (COD_COR)...")
        
        # Normaliza valores da coluna COR (remove espacos, converte para string)
        df['COR'] = df['COR'].astype(str).str.strip().str.upper()
        
        # Remove valores vazios ou invalidos
        cores_validas = df['COR'].replace(['', 'NAN', 'NONE', 'NULL'], pd.NA)
        
        # Obtem cores unicas e ordena (G0, G1, G2... ou alfabeticamente)
        cores_unicas = sorted([c for c in cores_validas.dropna().unique() if c])
        
        # Cria mapeamento COR -> COD_COR
        cor_to_code = {}
        for idx, cor in enumerate(cores_unicas, start=1):
            cor_to_code[cor] = f"{idx:03d}"
        
        logger.info(f"{len(cor_to_code)} codigos de cor gerados:")
        for cor, code in list(cor_to_code.items())[:10]:  # Mostra ate 10 exemplos
            logger.info(f"   {code} -> {cor}")
        
        if len(cor_to_code) > 10:
            logger.info(f"   ... e mais {len(cor_to_code) - 10} cores")
        
        # Aplica o mapeamento
        if 'COD_COR' not in df.columns:
            df['COD_COR'] = ''
        
        df['COD_COR'] = df['COR'].map(cor_to_code)
        
        # Preenche valores nao mapeados com vazio
        df['COD_COR'] = df['COD_COR'].fillna('')
        
        # Contagem de uso
        cores_count = df['COR'].value_counts()
        logger.info(f"\nEstatisticas de uso das cores:")
        logger.info(f"   Total de registros: {len(df)}")
        logger.info(f"   Cores unicas: {len(cor_to_code)}")
        if len(cores_count) > 0:
            logger.info(f"   Cor mais usada: {cores_count.index[0]} ({cores_count.iloc[0]} vezes)")
        
        return df

    def _formatar_numero_brasileiro(self, valor):
        """
        Converte numero para formato brasileiro
        Exemplos: 5300.00 -> 5.300,00 | 12.50 -> 12,50 | 1234567.89 -> 1.234.567,89
        """
        try:
            # Tenta converter para float
            num = float(valor)
            
            # Separa parte inteira e decimal
            parte_inteira = int(num)
            parte_decimal = num - parte_inteira
            
            # Formata parte inteira com separador de milhares
            inteira_formatada = f"{parte_inteira:,}".replace(',', '.')
            
            # Formata parte decimal (sempre 2 casas)
            if parte_decimal > 0:
                decimal_str = f"{parte_decimal:.2f}".split('.')[1]
                return f"{inteira_formatada},{decimal_str}"
            else:
                return f"{inteira_formatada},00"
        except (ValueError, TypeError):
            # Se nao for numero, retorna o valor original
            return valor

    def _corrigir_valores(self, df, colunas, valores_padrao):
        """Corrige valores invalidos e preenche colunas ausentes PRESERVANDO ZEROS"""
        # Preenche colunas que nao existirem
        for col in colunas:
            if col not in df.columns:
                # Usa o valor padrao exato (preserva zeros)
                df[col] = valores_padrao.get(col, '')
            else:
                # Para colunas existentes, preserva valores validos e aplica padrao apenas para invalidos
                pass

        # Define valores considerados invalidos
        invalidos = {'', None, np.nan, 'NaN', 'nan', 'undefined', 'null', 'NULL', 'None'}

        # Colunas que devem ter formatacao numerica brasileira
        colunas_numericas = ['CUSTO', 'PRECO1', 'PRECO2', 'PRECO3', 'PRECO4', 'PRECO5',
                            'PESO', 'ALTURA', 'LARGURA', 'PROFUNDIDADE', 'COMPRIMENTO',
                            'QTDE_MAX_VENDA', 'FATOR_CA', 'FATOR_AU']

        # Corrige celula por celula PRESERVANDO ZEROS
        for col in colunas:
            if col in colunas_numericas:
                # Para colunas numericas, aplica formatacao brasileira
                df[col] = df[col].apply(
                    lambda v: self._formatar_numero_brasileiro(v) if not (pd.isna(v) or str(v).strip() in invalidos) else valores_padrao.get(col, '')
                )
            else:
                # Para outras colunas, mantem comportamento original
                df[col] = df[col].apply(
                    lambda v: valores_padrao.get(col, '') if (pd.isna(v) or str(v).strip() in invalidos) else str(v)
                )

        # Garante ordem de colunas
        df = df[colunas]
        return df

    def processar(self):
        """Executa o pipeline completo"""
        logger.info("\nIniciando traducao final dos JSONs...")

        # 1. Obtem nome para o arquivo de saida
        nome_saida = self._obter_nome_saida()

        # 2. Le gabarito
        colunas, valores_padrao = self._carregar_gabarito()

        # 3. Le JSONs
        df_json = self._ler_jsons()
        logger.info(f"Total de registros lidos: {len(df_json)}")

        # 4. Gera COD_CLASSIFICACAO_FIS automaticamente (com cache persistente)
        df_json = self._gerar_cod_classificacao_fis(df_json)

        # 5. Filtra produtos invalidos (sem precos validos)
        df_json = self._filtrar_produtos_invalidos(df_json)
        logger.info(f"Apos filtragem: {len(df_json)} registros")

        # 6. Renumera COD_PRODUTO sequencialmente
        df_json = self._renumerar_cod_produto(df_json)

        # 7. Gera COD_COR automaticamente
        df_json = self._gerar_cod_cor(df_json)

        # 8. Corrige e preenche
        df_final = self._corrigir_valores(df_json, colunas, valores_padrao)

        # 9. Salva resultado SEM mesclar celulas - APENAS COM O NOME EXTRAIDO
        path_saida = os.path.join(self.pasta_saida, f"{nome_saida}.xlsx")
        
        # Usa ExcelWriter com opcoes especificas para evitar mesclagem
        with pd.ExcelWriter(path_saida, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Dados')
            
            # Acessa a planilha e desabilita mesclagem
            workbook = writer.book
            worksheet = writer.sheets['Dados']
            
            # Remove qualquer mesclagem existente
            if hasattr(worksheet, 'merged_cells'):
                # Cria uma copia da lista para evitar modificacao durante iteracao
                merged_cells_copy = list(worksheet.merged_cells)
                for merged_cell in merged_cells_copy:
                    worksheet.unmerge_cells(str(merged_cell))
            
            # Ajusta largura das colunas para melhor visualizacao
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Limita a 50
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        logger.info(f"\nPlanilha final gerada com sucesso em: {path_saida}")
        logger.info(f"{len(df_final)} registros exportados")
        logger.info(f"Celulas NAO mescladas - cada linha independente")
        
        # Log final mostrando que zeros foram preservados
        logger.info(f"Valores padrao com zeros preservados (ex: '001', '0001')")

if __name__ == "__main__":
    tradutor = TradutorFinal()
    tradutor.processar()