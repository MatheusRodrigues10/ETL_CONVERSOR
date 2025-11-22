# Documentação: Novas Variações e Linha de Parada

## 📋 Resumo das Mudanças

Este documento descreve todas as alterações implementadas relacionadas a:
1. **Campo de Novas Variações** (`novas_variacoes`)
2. **Linha de Parada** (`stopRow`)

---

## 1. Campo de Novas Variações (`novas_variacoes`)

### 1.1 O que foi implementado

Foi criado um campo opcional que permite ao usuário adicionar variações adicionais para a coluna de variação (COR) sem precisar que essas variações existam nas colunas das planilhas.

### 1.2 Mudanças nos Tipos TypeScript

**Arquivo:** `src/types/spreadsheet.ts`

```typescript
export interface ColumnMapping {
  gabaritoColumn: string;
  sourceColumn: string | string[]; // Permite múltiplas colunas para variações (ex: COR)
  sourceFile: 'custo' | 'venda';
  pageIndex?: number;
  name?: string;
  novas_variacoes?: string; // ✨ NOVO: Novas variações separadas por vírgula (ex: "A6,A2,A1")
}
```

### 1.3 Interface do Usuário

**Arquivo:** `src/pages/Index.tsx`

Foi adicionado um campo opcional entre "Mapeamento de Colunas Obrigatórias" e "Colunas Adicionais":

- **Localização:** Entre o `ColumnMapper` e a seção de colunas opcionais
- **Funcionalidades:**
  - Input para digitar variações separadas por vírgula
  - Botão "Adicionar" para processar as variações
  - Botão "Limpar Todas" (aparece quando há variações adicionadas)
  - Exibição das variações adicionadas como badges com botão de remoção individual

### 1.4 Lógica de Funcionamento

**Arquivo:** `src/pages/Index.tsx`

#### Função `handleNovasVariacoes`:
- Recebe uma string com variações separadas por vírgula (ex: "A6,A2,A1")
- Converte todas para UPPERCASE
- Remove espaços e valores vazios
- Combina com variações já existentes (evita duplicatas)
- Aplica para ambas as planilhas (custo e venda) se existirem
- **IMPORTANTE:** Não modifica o `sourceColumn`, apenas adiciona ao campo `novas_variacoes`

#### Função `handleRemoverVariacaoIndividual`:
- Remove uma variação específica da lista de `novas_variacoes`
- Mantém outras variações intactas

#### Função `handleLimparNovasVariacoes`:
- Remove todas as variações adicionadas via `novas_variacoes`
- Não afeta as variações selecionadas via checkbox

### 1.5 Comportamento Especial

**Arquivo:** `src/components/ColumnMapper.tsx`

- As variações de `novas_variacoes` **NÃO** contam para o progresso de mapeamento obrigatório
- A coluna COR só é considerada "mapeada" (verde) se houver variações selecionadas via checkbox ou adicionadas individualmente
- As variações de `novas_variacoes` aparecem apenas no JSON final, mas não afetam os contadores visuais

### 1.6 Como aparece no JSON

**Estrutura no JSON:**

```json
{
  "columnMapping": [
    {
      "gabaritoColumn": "COR",
      "sourceColumn": ["A1", "A2"],  // Variações selecionadas via checkbox
      "sourceFile": "custo",
      "novas_variacoes": "A6,A2,A1"  // ✨ Novas variações adicionadas
    },
    {
      "gabaritoColumn": "COR",
      "sourceColumn": ["A3", "A4"],
      "sourceFile": "venda",
      "novas_variacoes": "A6,A5"     // ✨ Novas variações adicionadas
    }
  ]
}
```

**Explicação:**
- `sourceColumn`: Contém as variações que existem nas colunas das planilhas (selecionadas via checkbox)
- `novas_variacoes`: Contém variações adicionais que o usuário digitou manualmente
- **Ambos são combinados** na engine de processamento para formar a lista completa de variações

**Exemplo prático:**
- Se `sourceColumn = ["A1", "A2"]` e `novas_variacoes = "A6,A2,A1"`
- A lista final de variações será: `["A1", "A2", "A6"]` (duplicatas são ignoradas)

---

## 2. Linha de Parada (`stopRow`)

### 2.1 O que foi implementado

Foi criado um campo que permite definir em qual linha o sistema deve parar de ler cada página específica da planilha. Isso é útil quando você quer processar apenas uma parte de cada aba.

### 2.2 Mudanças nos Tipos TypeScript

**Arquivo:** `src/types/spreadsheet.ts`

```typescript
export interface PageConfig {
  pageIndex: number;
  pageName: string;
  startCell: string;
  columns: string[];
  columnMappings: ColumnMapping[];
  isApproved: boolean;
  stopRow?: number; // ✨ NOVO: Linha onde o sistema deve parar de ler esta página específica
}

export interface PandasConfig {
  // ... outros campos ...
  pages?: PageConfig[]; // Cada página pode ter seu próprio stopRow
  stopRow?: number; // ⚠️ Este campo foi removido (não é mais usado)
}
```

**Nota:** O campo `stopRow` no nível de `PandasConfig` foi removido, pois agora cada página tem seu próprio `stopRow`.

### 2.3 Interface do Usuário

**Arquivo:** `src/components/PageManager.tsx`

Foi adicionado um campo no modal de configuração de cada página:

- **Localização:** No modal de revisão/aprovação de página, após o campo "Célula Inicial"
- **Funcionalidades:**
  - Input numérico que aceita apenas números positivos
  - Validação para impedir caracteres não numéricos
  - Botão "Limpar" (aparece quando há valor definido)
  - Badge mostrando a linha escolhida com botão de remoção
  - Campo totalmente opcional

### 2.4 Lógica de Funcionamento

**Arquivo:** `src/components/PageManager.tsx`

#### Estado `currentStopRow`:
- Armazena temporariamente a linha de parada enquanto o usuário configura a página
- É salvo no `PageConfig` quando a página é aprovada

#### Função `processPageData`:
```typescript
// Determinar a linha máxima a processar (respeitando stopRow se definido)
const startRow0Based = startRow - 1; // Converter para 0-based
const effectiveMaxRow = pageConfig.stopRow 
  ? Math.min(maxRow, pageConfig.stopRow - 1) // stopRow é 1-based, então subtraímos 1 para 0-based
  : maxRow;

for (let r = startRow0Based; r <= effectiveMaxRow; r++) {
  // Processar apenas até a linha stopRow
}
```

**Explicação:**
- `stopRow` é 1-based (o usuário digita linha 100, por exemplo)
- Internamente, o código usa índices 0-based
- O sistema processa linhas desde `startCell` até `stopRow - 1` (convertido para 0-based)
- Se `stopRow` não estiver definido, processa até o final da planilha

### 2.5 Exibição na Lista de Páginas

**Arquivo:** `src/components/PageManager.tsx`

Quando uma página tem `stopRow` definido, aparece na lista de páginas configuradas:

```
Página 1: Sheet1
Início: A5 • 10 colunas • Parar na linha: 100
```

### 2.6 Como aparece no JSON

**Estrutura no JSON:**

```json
{
  "pages": [
    {
      "pageIndex": 0,
      "pageName": "Sheet1",
      "startCell": "A5",
      "columns": ["PRODUTO", "COR", "PREÇO"],
      "columnMappings": [...],
      "isApproved": true,
      "stopRow": 100  // ✨ Linha onde parar de ler esta página
    },
    {
      "pageIndex": 1,
      "pageName": "Sheet2",
      "startCell": "A3",
      "columns": ["PRODUTO", "COR", "PREÇO"],
      "columnMappings": [...],
      "isApproved": true
      // ✨ Sem stopRow = processa até o final
    }
  ]
}
```

**Explicação:**
- Cada página pode ter seu próprio `stopRow`
- Se `stopRow` não estiver presente, o sistema processa até o final da planilha
- O valor é 1-based (linha 100 = linha 100 do Excel)
- O sistema para de processar **antes** da linha especificada (processa até `stopRow - 1`)

**Exemplo prático:**
- `startCell = "A5"` (linha 5)
- `stopRow = 100`
- O sistema processa linhas de 5 até 99 (inclusive)

---

## 3. Resumo das Mudanças nos Arquivos

### 3.1 Arquivos Modificados

1. **`src/types/spreadsheet.ts`**
   - Adicionado `novas_variacoes?: string` em `ColumnMapping`
   - Adicionado `stopRow?: number` em `PageConfig`
   - Campo `stopRow` em `PandasConfig` mantido (mas não usado mais)

2. **`src/pages/Index.tsx`**
   - Adicionado campo de input para novas variações
   - Funções: `handleNovasVariacoes`, `handleRemoverVariacaoIndividual`, `handleLimparNovasVariacoes`
   - Hook `useMemo` para `novasVariacoesAdicionadas`
   - Lógica especial em `mappedRequiredColumns` para não contar `novas_variacoes` no progresso

3. **`src/components/ColumnMapper.tsx`**
   - Lógica especial para não considerar `novas_variacoes` no cálculo de colunas mapeadas
   - Ajustes em `isMapped` e `uniqueVariationsCount` para excluir `novas_variacoes`

4. **`src/components/PageManager.tsx`**
   - Adicionado estado `currentStopRow`
   - Campo de input para linha de parada no modal de configuração
   - Lógica em `processPageData` para respeitar `stopRow`
   - Exibição de `stopRow` na lista de páginas configuradas

---

## 4. Exemplo Completo de JSON Gerado

```json
{
  "gabarito": {
    "requiredColumns": ["PRODUTO", "COR", "PREÇO"],
    "optionalColumns": ["ALTURA", "LARGURA"],
    "allColumns": ["PRODUTO", "COR", "PREÇO", "ALTURA", "LARGURA"]
  },
  "files": {
    "custo": {
      "columns": ["PRODUTO", "COR", "PREÇO"],
      "path": "custo.xlsx"
    },
    "venda": {
      "columns": ["PRODUTO", "COR", "PREÇO"],
      "path": "venda.xlsx"
    }
  },
  "columnMapping": [
    {
      "gabaritoColumn": "PRODUTO",
      "sourceColumn": "PRODUTO",
      "sourceFile": "custo"
    },
    {
      "gabaritoColumn": "COR",
      "sourceColumn": ["A1", "A2", "A3"],  // Variações das colunas da planilha
      "sourceFile": "custo",
      "novas_variacoes": "A6,A2,A1"  // ✨ Variações adicionais
    },
    {
      "gabaritoColumn": "COR",
      "sourceColumn": ["A4", "A5"],
      "sourceFile": "venda",
      "novas_variacoes": "A6,A7"  // ✨ Variações adicionais
    },
    {
      "gabaritoColumn": "PREÇO",
      "sourceColumn": "PREÇO",
      "sourceFile": "custo"
    }
  ],
  "mergeConfig": {
    "leftFile": "custo",
    "rightFile": "venda",
    "leftKey": "PRODUTO",
    "rightKey": "PRODUTO",
    "how": "inner"
  },
  "colorColumn": "COR",
  "pages": [
    {
      "pageIndex": 0,
      "pageName": "Sheet1",
      "startCell": "A5",
      "columns": ["PRODUTO", "COR", "PREÇO"],
      "columnMappings": [],
      "isApproved": true,
      "stopRow": 100  // ✨ Para de ler na linha 100
    },
    {
      "pageIndex": 1,
      "pageName": "Sheet2",
      "startCell": "A3",
      "columns": ["PRODUTO", "COR", "PREÇO"],
      "columnMappings": [],
      "isApproved": true
      // ✨ Sem stopRow = processa até o final
    }
  ]
}
```

---

## 5. Notas Importantes

### 5.1 Novas Variações (`novas_variacoes`)

- ✅ Não afeta o progresso de mapeamento obrigatório
- ✅ Não faz a coluna COR ficar "verde" (mapeada) sozinha
- ✅ É combinada com `sourceColumn` na engine de processamento
- ✅ Duplicatas são automaticamente ignoradas
- ✅ Valores são sempre convertidos para UPPERCASE

### 5.2 Linha de Parada (`stopRow`)

- ✅ É específica para cada página
- ✅ Valor é 1-based (como no Excel)
- ✅ O sistema processa até `stopRow - 1` (inclusive)
- ✅ Se não definido, processa até o final da planilha
- ✅ Campo totalmente opcional

---

## 6. Como Usar na Engine de Processamento

### 6.1 Processar Novas Variações

**⚠️ IMPORTANTE: Lógica de Processamento de Variações**

A engine deve processar as variações da seguinte forma:

1. **Combinar todas as variações disponíveis:**
   - Variações de `sourceColumn` (colunas da planilha)
   - Variações de `novas_variacoes` (adicionadas manualmente)
   - Remover duplicatas

2. **Durante o processamento das linhas:**
   - Ao encontrar uma variação **antiga** (que já existe na lista), **usar ela**
   - Ao encontrar uma variação **nova** (que não existe na lista), **adicionar à lista e usar**
   - **Ficar trocando** entre variações conforme encontra novas ou velhas nas linhas processadas
   - A lista de variações é **dinâmica** e pode crescer durante o processamento

**Exemplo de código:**

```python
# Exemplo em Python
for mapping in config['columnMapping']:
    if mapping['gabaritoColumn'] == 'COR':
        # Obter variações das colunas (variações antigas)
        source_variations = mapping['sourceColumn']
        if isinstance(source_variations, str):
            source_variations = [source_variations]
        
        # Obter novas variações adicionadas manualmente
        novas_variacoes = []
        if 'novas_variacoes' in mapping and mapping['novas_variacoes']:
            novas_variacoes = [
                v.strip().upper() 
                for v in mapping['novas_variacoes'].split(',')
                if v.strip()
            ]
        
        # Combinar variações iniciais (remover duplicatas)
        todas_variacoes = list(set(source_variations + novas_variacoes))
        
        # Processar linhas da planilha
        for row in planilha:
            valor_cor = row['COR']  # Valor encontrado na linha
            
            # Verificar se é uma variação conhecida (antiga)
            if valor_cor in todas_variacoes:
                # Usar a variação antiga
                usar_variacao(valor_cor)
            else:
                # É uma variação nova - adicionar à lista e usar
                todas_variacoes.append(valor_cor)
                usar_variacao(valor_cor)
                print(f"Nova variação encontrada e adicionada: {valor_cor}")
        
        print(f"Lista final de variações: {todas_variacoes}")
```

**Comportamento esperado:**
- Se encontrar "A1" (variação antiga) → usar "A1"
- Se encontrar "A6" (variação nova) → adicionar "A6" à lista e usar "A6"
- Se encontrar "A1" novamente → usar "A1" (já está na lista)
- Se encontrar "A7" (outra nova) → adicionar "A7" à lista e usar "A7"
- A lista vai **crescendo dinamicamente** conforme novas variações são encontradas

### 6.2 Processar com Linha de Parada

**⚠️ IMPORTANTE: Especificação de Página para Linha de Parada**

A engine **DEVE** verificar o campo `stopRow` **especificamente para cada página** quando há múltiplas páginas configuradas. O `stopRow` é **específico por página**, não global.

**Pergunta para a Engine:**
> A engine especifica para qual página deve parar de ler as linhas quando há essa configuração?

**Resposta:** Sim! Cada página no array `pages` pode ter seu próprio `stopRow`. A engine deve:
1. Processar cada página individualmente
2. Verificar se a página tem `stopRow` definido
3. Aplicar o `stopRow` **apenas para aquela página específica**
4. Outras páginas podem ter `stopRow` diferentes ou não ter `stopRow` (processa até o final)

**Exemplo de código:**

```python
# Exemplo em Python
import pandas as pd

# Verificar se há configuração de páginas
if 'pages' in config and config['pages']:
    # Processar cada página individualmente
    for page in config['pages']:
        page_name = page['pageName']  # Ex: "Sheet1"
        start_cell = page['startCell']  # Ex: "A5"
        stop_row = page.get('stopRow')  # Ex: 100 ou None
        
        print(f"Processando página: {page_name}")
        
        # Carregar a página específica
        df = pd.read_excel(arquivo, sheet_name=page_name)
        
        # Converter startCell para linha inicial (1-based)
        start_row = parse_cell_to_row(start_cell)  # Ex: 5
        
        # Determinar linha final para ESTA página específica
        if stop_row:
            # Esta página tem stopRow definido
            end_row = stop_row - 1  # Processa até stopRow - 1 (inclusive)
            print(f"  Página {page_name}: Processando linhas {start_row} até {end_row} (stopRow={stop_row})")
        else:
            # Esta página não tem stopRow - processa até o final
            end_row = len(df)  # Processa até o final da planilha
            print(f"  Página {page_name}: Processando linhas {start_row} até {end_row} (sem stopRow)")
        
        # Processar apenas as linhas especificadas para ESTA página
        for row_index in range(start_row - 1, end_row):  # -1 porque pandas é 0-based
            if row_index < len(df):
                row_data = df.iloc[row_index]
                process_row(row_data, page_name)
else:
    # Sem configuração de páginas - processar normalmente
    df = pd.read_excel(arquivo)
    for row_index, row_data in df.iterrows():
        process_row(row_data)
```

**Exemplo prático com múltiplas páginas:**

```json
{
  "pages": [
    {
      "pageIndex": 0,
      "pageName": "Sheet1",
      "startCell": "A5",
      "stopRow": 100  // ✨ Esta página para na linha 100
    },
    {
      "pageIndex": 1,
      "pageName": "Sheet2",
      "startCell": "A3"
      // ✨ Esta página NÃO tem stopRow - processa até o final
    },
    {
      "pageIndex": 2,
      "pageName": "Sheet3",
      "startCell": "A10",
      "stopRow": 50  // ✨ Esta página para na linha 50
    }
  ]
}
```

**Processamento:**
- **Sheet1**: Processa linhas 5 até 99 (stopRow=100)
- **Sheet2**: Processa linhas 3 até o final (sem stopRow)
- **Sheet3**: Processa linhas 10 até 49 (stopRow=50)

**Cada página é processada independentemente com seu próprio `stopRow`!**

---

## 7. Checklist de Implementação

- [x] Adicionado campo `novas_variacoes` em `ColumnMapping`
- [x] Adicionado campo `stopRow` em `PageConfig`
- [x] Criada interface de usuário para novas variações
- [x] Criada interface de usuário para linha de parada
- [x] Implementada lógica de combinação de variações
- [x] Implementada lógica de processamento com linha de parada
- [x] Ajustada lógica de progresso para não contar `novas_variacoes`
- [x] Testado comportamento de remoção individual
- [x] Testado comportamento de limpeza total
- [x] Verificado JSON gerado

---

---

## 8. Perguntas e Respostas para a Engine

### 8.1 Como processar variações antigas vs novas?

**Pergunta:** Ao encontrar uma variação antiga, devo usar ela e ficar trocando se encontrar nova ou velha?

**Resposta:** Sim! A engine deve:
- Manter uma lista dinâmica de todas as variações (antigas + novas)
- Ao encontrar uma variação **antiga** (já na lista) → usar ela
- Ao encontrar uma variação **nova** (não está na lista) → adicionar à lista e usar
- A lista cresce dinamicamente durante o processamento
- Sempre usar a variação encontrada, seja antiga ou nova

### 8.2 A engine especifica para qual página parar de ler?

**Pergunta:** A engine especifica para qual página deve parar de ler as linhas quando há essa configuração?

**Resposta:** Sim! O `stopRow` é **específico para cada página**:
- Cada página no array `pages` pode ter seu próprio `stopRow`
- A engine deve verificar o `stopRow` de cada página individualmente
- Se uma página tem `stopRow`, aplica apenas para aquela página
- Outras páginas podem ter `stopRow` diferentes ou não ter (processa até o final)
- O `stopRow` **não é global**, é por página

**Exemplo:**
- Página 1 (`Sheet1`) tem `stopRow: 100` → processa até linha 99
- Página 2 (`Sheet2`) não tem `stopRow` → processa até o final
- Página 3 (`Sheet3`) tem `stopRow: 50` → processa até linha 49

---

**Última atualização:** Implementação completa das funcionalidades de novas variações e linha de parada, incluindo explicações detalhadas sobre processamento dinâmico de variações e especificação de linha de parada por página.

