export interface SpreadsheetColumn {
  name: string;
  index: number;
  required: boolean;
  hasDefaultValue?: boolean;
}

export interface CellData {
  value: any;
  page: number;
  pageName: string;
  row: number;
  col: number;
  cellAddress: string;
}

export interface UploadedFile {
  name: string;
  columns: string[];
  data: any[][];
  type: 'custo' | 'venda' | 'gabarito';
  sheets?: string[]; // Nomes das abas/páginas
  cellData?: CellData[][]; // Dados com informações de localização
}

export interface ColumnMapping {
  gabaritoColumn: string;
  sourceColumn: string | string[]; // Permite múltiplas colunas para variações (ex: COR)
  sourceFile: 'custo' | 'venda';
  pageIndex?: number; // Índice da página (opcional para compatibilidade)
  name?: string; // Nome customizado usado como referência para todos (não é uma coluna da planilha)
  novas_variacoes?: string; // Novas variações separadas por vírgula (ex: "A6,A2,A1") - será combinada com sourceColumn
}

export interface PageConfig {
  pageIndex: number; // Índice da página no Excel (0-based)
  pageName: string; // Nome da aba
  startCell: string; // Célula inicial (ex: "A5")
  columns: string[]; // Colunas detectadas
  columnMappings: ColumnMapping[]; // Mapeamentos específicos desta página
  isApproved: boolean; // Se foi aprovada pelo usuário
  stopRow?: number; // Linha onde o sistema deve parar de ler esta página específica (opcional)
}

export interface MergeConfig {
  leftFile: 'custo' | 'venda';
  rightFile: 'custo' | 'venda';
  leftKey: string;
  rightKey: string;
  how: 'left' | 'right' | 'inner' | 'outer';
  includeVariationKey?: boolean; // Se verdadeiro, inclui a coluna de variação (ex: COR) como parte da chave de junção
}

export interface PandasConfig {
  gabarito: {
    requiredColumns: string[];
    optionalColumns?: string[];
    allColumns: string[];
  };
  files: {
    custo?: {
      columns: string[];
      path: string;
    };
    venda?: {
      columns: string[];
      path: string;
    };
  };
  columnMapping: ColumnMapping[];
  mergeConfig?: MergeConfig;
  colorColumn?: string;
  variationSplit?: {
    column: string; // Ex.: 'COR'
    pattern: string; // Regex em string (ex.: "\n|/|\\|\||,|;|\\b[Ee]\b")
    trim?: boolean; // Remover espaços ao redor
    ignoreEmpty?: boolean; // Ignorar partes vazias
    splitIntoRows?: boolean; // Se verdadeiro, explode em múltiplas linhas
  };
  pages?: PageConfig[]; // Configurações de múltiplas páginas
  stopRow?: number; // Linha onde o sistema deve parar de ler a tabela (opcional)
}
