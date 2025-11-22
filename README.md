# ETL_CONVERSOR

Sistema ETL para conversão de planilhas Excel em formato padronizado, com suporte a múltiplas configurações e processamento automatizado.

## Estrutura do Projeto

```
ETL_CONVERSOR/
├── MOTOR/              # Scripts de processamento ETL
│   ├── conversor_etl.py      # Converte Excel → TXT
│   ├── geradorJSON.py        # Converte TXT → JSON
│   ├── mescladorJSON.py      # Mescla JSONs de custo e venda
│   ├── configs/              # Arquivos de configuração JSON
│   ├── planilhas/            # Planilhas Excel de entrada
│   ├── txt_bruto/            # Arquivos TXT intermediários
│   ├── json_final/           # JSONs processados
│   └── jsons_mesclados/      # JSONs mesclados (custo + venda)
│
├── TRADUTOR/          # Conversão final para Excel
│   ├── tradutor_final.py     # Converte JSON → Excel final
│   ├── gabarito/             # Planilha gabarito padrão
│   ├── jsons/                # JSONs mesclados de entrada
│   └── saidas/               # Planilhas Excel finais
│
└── JSON/              # Interface web para criação de configurações
```

## Fluxo de Processamento

### 1. Conversão Excel → TXT
**Script:** `MOTOR/conversor_etl.py`

- Lê planilhas Excel da pasta `planilhas/`
- Identifica automaticamente o arquivo de configuração apropriado
- Converte cada aba em arquivo TXT no formato vertical
- Salva em `txt_bruto/`

**Execução:**
```bash
cd MOTOR
python conversor_etl.py
```

### 2. Conversão TXT → JSON
**Script:** `MOTOR/geradorJSON.py`

- Processa arquivos TXT de `txt_bruto/`
- Aplica mapeamento de colunas conforme configuração
- Identifica e remove registros de cabeçalho
- Gera JSONs estruturados em `json_final/`

**Execução:**
```bash
cd MOTOR
python geradorJSON.py
```

### 3. Mesclagem de JSONs
**Script:** `MOTOR/mescladorJSON.py`

- Agrupa JSONs por configuração
- Identifica arquivos de custo e venda
- Expande variações de cores
- Mescla dados baseado em `mergeConfig`
- Gera códigos sequenciais de produto
- Salva JSONs mesclados em `jsons_mesclados/`

**Execução:**
```bash
cd MOTOR
python mescladorJSON.py
```

### 4. Conversão Final JSON → Excel
**Script:** `TRADUTOR/tradutor_final.py`

- Processa JSONs mesclados de `jsons/`
- Aplica gabarito padrão
- Gera códigos de classificação fiscal (NCM) com cache
- Filtra produtos sem preços válidos
- Renumera códigos de produto e cor
- Formata valores numéricos no padrão brasileiro
- Exporta planilhas Excel finais em `saidas/`

**Execução:**
```bash
cd TRADUTOR
python tradutor_final.py
```

## Arquivos de Configuração

Os arquivos de configuração em `MOTOR/configs/` definem:

- **`files`**: Caminhos dos arquivos Excel de custo e venda
- **`columnMapping`**: Mapeamento de colunas origem → destino
- **`mergeConfig`**: Configuração de mesclagem (chaves, variações)
- **`colorColumn`**: Configuração de coluna de cores
- **`pages`**: Configuração de páginas/abas a processar

## Requisitos

- Python 3.7+
- pandas
- openpyxl
- pathlib (built-in)

**Instalação:**
```bash
pip install pandas openpyxl
```

## Funcionalidades Principais

- **Processamento Multi-config**: Suporta múltiplos arquivos de configuração
- **Detecção Automática**: Identifica configuração apropriada por nome de arquivo
- **Expansão de Variações**: Expande produtos com múltiplas cores/preços
- **Cache de NCM**: Reutiliza códigos de classificação fiscal entre execuções
- **Validação de Dados**: Filtra produtos sem preços válidos
- **Formatação Brasileira**: Aplica padrão brasileiro em valores numéricos

## Estrutura de Pastas

### Entrada
- `MOTOR/planilhas/` - Planilhas Excel originais
- `MOTOR/configs/` - Arquivos de configuração JSON

### Processamento
- `MOTOR/txt_bruto/` - Arquivos TXT intermediários
- `MOTOR/json_final/` - JSONs processados individualmente
- `MOTOR/jsons_mesclados/` - JSONs mesclados (custo + venda)

### Saída
- `TRADUTOR/saidas/` - Planilhas Excel finais padronizadas

## Logs

Logs de execução são salvos em:
- `MOTOR/logs/` - Logs do conversor ETL

## Observações

- Cada script pode ser executado independentemente
- A ordem de execução deve ser respeitada: conversor → gerador → mesclador → tradutor
- Arquivos de configuração são identificados automaticamente pelo nome do arquivo processado
- O cache de NCM é persistente entre execuções

