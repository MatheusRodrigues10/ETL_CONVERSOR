# ConfigRegexBuilder - Documentação

## O que foi entendido

O componente `ConfigRegexBuilder` foi criado para permitir que usuários construam regras avançadas e dinâmicas de regex de forma visual e intuitiva. O componente suporta:

### 1. **Configuração Inicial**
- **Nome da linha inicial**: Campo obrigatório que identifica a linha de início
- **Variações iniciais**: Lista de variações separadas por vírgula (ex: "A6, A2, A1")
- **Ativar regex**: Switch para habilitar/desabilitar regex nesta configuração
- **Como aplicar o regex**: Duas opções:
  - "Aplicar regex apenas nesta linha inicial" (`aplicarRegex: "inicial"`)
  - "Aplicar regex em todas as linhas abaixo (até o evento de parada)" (`aplicarRegex: "abaixo"`)

### 2. **Linha de Parada**
Aparece apenas quando `aplicarRegex === "abaixo"`. Permite definir:
- **Nome da linha de parada**: Campo obrigatório
- **O que fazer ao encontrar a linha de parada**: Três opções:
  - **OPÇÃO A - Parar totalmente** (`tipo: "parar_total"`): Para completamente, nenhuma linha recebe regex
  - **OPÇÃO B - Aplicar regex nesta linha e parar** (`tipo: "aplicar_e_parar"`): A linha de parada recebe regex próprio, mas para abaixo
  - **OPÇÃO C - Ignorar e continuar** (`tipo: "ignorar_e_continuar"`): Para a lógica principal, aplica regex na linha de parada, e inicia nova configuração recursiva abaixo

### 3. **Recursividade Infinita**
A opção C permite criar configurações aninhadas infinitamente. Cada nova configuração abaixo pode ter sua própria linha de parada, que por sua vez pode ter outra configuração abaixo, e assim por diante.

### 4. **Controles de Interface**
Cada card possui:
- **Recolher/Expandir**: Botão para mostrar/ocultar conteúdo
- **Remover**: Remove a configuração (exceto configurações raiz)
- **Duplicar**: Cria uma cópia da configuração
- **Adicionar nova configuração**: Adiciona uma nova configuração no mesmo nível

## Estrutura do JSON Gerado

O componente gera um array de objetos `ConfiguracaoRegex`, onde cada objeto pode ter uma estrutura recursiva. Abaixo está um exemplo completo baseado no JSON fornecido:

### Exemplo 1: Configuração Simples

```json
[
  {
    "inicio": "CARVALHO SEM VIDRO COM",
    "variacoes": ["LACA FOSCA", "LACA BRILHO", "SUPREMA NOG"],
    "regexAtivado": true,
    "aplicarRegex": "inicial"
  }
]
```

### Exemplo 2: Com Linha de Parada (Parar Totalmente)

```json
[
  {
    "inicio": "CARVALHO SEM VIDRO COM",
    "variacoes": ["LACA FOSCA", "LACA BRILHO"],
    "regexAtivado": true,
    "aplicarRegex": "abaixo",
    "linhaParada": {
      "nome": "FIM",
      "tipo": "parar_total"
    }
  }
]
```

### Exemplo 3: Com Linha de Parada (Aplicar e Parar)

```json
[
  {
    "inicio": "CARVALHO SEM VIDRO COM",
    "variacoes": ["LACA FOSCA", "LACA BRILHO"],
    "regexAtivado": true,
    "aplicarRegex": "abaixo",
    "linhaParada": {
      "nome": "CARV. NOG/CAST/PTO/NAT COM OU SEM TS",
      "tipo": "aplicar_e_parar",
      "regexLinhaParada": "REGEX_DA_PARADA"
    }
  }
]
```

### Exemplo 4: Configuração Recursiva Completa (Como no Exemplo Fornecido)

```json
[
  {
    "inicio": "CARVALHO SEM VIDRO COM",
    "variacoes": ["LACA FOSCA", "LACA BRILHO", "SUPREMA NOG"],
    "regexAtivado": true,
    "aplicarRegex": "abaixo",
    "linhaParada": {
      "nome": "CARV. NOG/CAST/PTO/NAT COM OU SEM TS",
      "tipo": "ignorar_e_continuar",
      "regexLinhaParada": "REGEX_DA_PARADA",
      "novaConfiguracaoAbaixo": {
        "inicio": "LACA FOSCA",
        "variacoes": ["BRANCO", "PRETO", "CINZA"],
        "regexAtivado": true,
        "aplicarRegex": "abaixo",
        "linhaParada": {
          "nome": "FIM",
          "tipo": "parar_total"
        }
      }
    }
  }
]
```

## Campos do JSON

### ConfiguracaoRegex
- `inicio` (string, obrigatório): Nome da linha inicial
- `variacoes` (string[], obrigatório): Array de variações
- `regexAtivado` (boolean): Se o regex está ativado
- `aplicarRegex` ("inicial" | "abaixo"): Como aplicar o regex
- `linhaParada` (opcional): Objeto LinhaParada

### LinhaParada
- `nome` (string, obrigatório): Nome da linha de parada
- `tipo` ("parar_total" | "aplicar_e_parar" | "ignorar_e_continuar"): Tipo de ação
- `regexLinhaParada` (string, opcional): Regex específico (apenas para tipos "aplicar_e_parar" e "ignorar_e_continuar")
- `novaConfiguracaoAbaixo` (ConfiguracaoRegex, opcional): Nova configuração recursiva (apenas para tipo "ignorar_e_continuar")

## Validações

O componente valida:
1. **Nome da linha inicial**: Deve estar preenchido
2. **Variações**: Deve ter pelo menos uma variação válida
3. **Linha de parada**: Se existir, deve ter nome preenchido
4. **Regex da linha de parada**: Obrigatório para tipos "aplicar_e_parar" e "ignorar_e_continuar"
5. **Nova configuração abaixo**: Se existir (tipo "ignorar_e_continuar"), deve ser válida recursivamente

## Funcionalidades

- ✅ Interface visual intuitiva com cards colapsáveis
- ✅ Suporte a múltiplas configurações no mesmo nível
- ✅ Recursividade infinita para configurações aninhadas
- ✅ Validação em tempo real
- ✅ Exportação para JSON formatado
- ✅ Cópia automática para clipboard ao exportar
- ✅ Duplicação de configurações
- ✅ Remoção de configurações
- ✅ Indicadores visuais de nível (bordas laterais para configurações aninhadas)

## Como Usar

```tsx
import { ConfigRegexBuilder } from "@/components/ConfigRegexBuilder";
import { ConfiguracaoRegex } from "@/types/regexConfig";

function MinhaPagina() {
  const handleExport = (json: string) => {
    console.log("JSON:", json);
    // Enviar para backend, salvar em arquivo, etc.
  };

  const handleChange = (configs: ConfiguracaoRegex[]) => {
    // Atualizar estado local se necessário
  };

  return (
    <ConfigRegexBuilder
      onChange={handleChange}
      onExport={handleExport}
    />
  );
}
```

## Observações Importantes

1. **Explosão de variações**: O frontend apenas captura e organiza os dados. A lógica de gerar múltiplas variações quando uma linha possui diferentes campos com regras (ex: descrição e preço) é responsabilidade do backend.

2. **Recursividade**: Não há limite de profundidade para configurações aninhadas, mas é recomendado manter a estrutura razoável para melhor usabilidade.

3. **Exportação**: O JSON gerado remove automaticamente campos vazios e valores inválidos, mantendo apenas a estrutura necessária.

