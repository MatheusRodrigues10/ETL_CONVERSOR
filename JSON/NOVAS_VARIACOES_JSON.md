# Campo "novas_variacoes" no JSON

## Onde as novas variações aparecem no JSON

O campo `novas_variacoes` aparece dentro de cada objeto `ColumnMapping` no array `columnMapping` do JSON gerado.

### Estrutura no JSON

```json
{
  "columnMapping": [
    {
      "gabaritoColumn": "COR",
      "sourceColumn": ["COLUNA1", "COLUNA2", "A6", "A2", "A1"],
      "sourceFile": "custo",
      "novas_variacoes": "A6,A2,A1"
    },
    {
      "gabaritoColumn": "COR",
      "sourceColumn": ["COLUNA3", "A6"],
      "sourceFile": "venda",
      "novas_variacoes": "A6"
    }
  ]
}
```

## Como funciona

### 1. Campo `novas_variacoes`
- **Tipo**: `string` (opcional)
- **Formato**: Variações separadas por vírgula (ex: `"A6,A2,A1"`)
- **Localização**: Dentro de cada objeto `ColumnMapping` no array `columnMapping`

### 2. Campo `sourceColumn`
- **Tipo**: `string | string[]`
- **Conteúdo**: Lista final de variações após combinação
- **Comportamento**: 
  - Contém as variações originais (selecionadas via checkbox)
  - **MAIS** as novas variações informadas em `novas_variacoes`
  - Duplicatas são automaticamente removidas

## Exemplo Completo

### Entrada do Usuário:
1. Seleciona via checkbox: `COLUNA1`, `COLUNA2`
2. Digita em "Novas variações": `A6,A2,A1`

### Processamento:
1. Sistema lê: `"A6,A2,A1"`
2. Separa por vírgula: `["A6", "A2", "A1"]`
3. Combina com existentes: `["COLUNA1", "COLUNA2"] + ["A6", "A2", "A1"]`
4. Remove duplicatas (se houver)
5. Resultado final: `["COLUNA1", "COLUNA2", "A6", "A2", "A1"]`

### JSON Gerado:

```json
{
  "columnMapping": [
    {
      "gabaritoColumn": "COR",
      "sourceColumn": ["COLUNA1", "COLUNA2", "A6", "A2", "A1"],
      "sourceFile": "custo",
      "novas_variacoes": "A6,A2,A1"
    }
  ]
}
```

## Regras de Processamento

1. **Separação**: O sistema separa a string `novas_variacoes` pelo caractere `,` (vírgula)
2. **Limpeza**: Remove espaços em branco e converte para UPPERCASE
3. **Combinação**: Adiciona apenas variações que não existem em `sourceColumn`
4. **Preservação**: As variações originais (selecionadas via checkbox) são mantidas
5. **Atualização**: O campo `sourceColumn` é atualizado com a lista combinada

## Casos Especiais

### Caso 1: Variação já existe
**Entrada**: 
- `sourceColumn`: `["COLUNA1", "A6"]`
- `novas_variacoes`: `"A6,A2"`

**Resultado**: 
- `sourceColumn`: `["COLUNA1", "A6", "A2"]` (A6 não é duplicado)
- `novas_variacoes`: `"A6,A2"`

### Caso 2: Campo vazio
**Entrada**: 
- `sourceColumn`: `["COLUNA1"]`
- `novas_variacoes`: `""` (vazio)

**Resultado**: 
- `sourceColumn`: `["COLUNA1"]` (não muda)
- `novas_variacoes`: `""` ou campo não aparece no JSON

### Caso 3: Apenas novas variações (sem seleção via checkbox)
**Entrada**: 
- `sourceColumn`: `[]` ou `"__EMPTY__"`
- `novas_variacoes`: `"A6,A2,A1"`

**Resultado**: 
- `sourceColumn`: `["A6", "A2", "A1"]`
- `novas_variacoes`: `"A6,A2,A1"`

## Como usar na Engine

### Python (Pandas)

```python
import json

# Carregar JSON
with open('config_exemplo.json', 'r') as f:
    config = json.load(f)

# Processar cada mapeamento
for mapping in config['columnMapping']:
    gabarito_column = mapping['gabaritoColumn']
    source_column = mapping['sourceColumn']
    novas_variacoes = mapping.get('novas_variacoes', '')
    
    # Se houver novas_variacoes, elas já foram combinadas em sourceColumn
    # Mas você pode acessar o campo original se necessário
    if novas_variacoes:
        print(f"Novas variações adicionadas: {novas_variacoes}")
        # Separar se necessário
        novas_list = [v.strip().upper() for v in novas_variacoes.split(',')]
        print(f"Lista de novas variações: {novas_list}")
    
    # sourceColumn já contém todas as variações combinadas
    print(f"Todas as variações: {source_column}")
```

## Resumo

- **Campo `novas_variacoes`**: String com variações separadas por vírgula (ex: `"A6,A2,A1"`)
- **Campo `sourceColumn`**: Array com todas as variações combinadas (originais + novas)
- **Localização**: Dentro de cada objeto no array `columnMapping`
- **Comportamento**: Adiciona novas variações sem substituir as existentes
- **Duplicatas**: Automaticamente removidas

