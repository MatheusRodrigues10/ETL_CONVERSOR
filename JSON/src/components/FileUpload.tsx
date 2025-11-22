import { useCallback, useState } from 'react';
import { Upload, FileSpreadsheet, X, Loader2, Search, Layers } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/hooks/use-toast';
import * as XLSX from 'xlsx';
import { UploadedFile, CellData, PageConfig } from '@/types/spreadsheet';
import { PageManager } from './PageManager';

interface FileUploadProps {
  type: 'custo' | 'venda' | 'gabarito';
  file: UploadedFile | null;
  onFileUpload: (file: UploadedFile) => void;
  onFileRemove: () => void;
  onPagesConfigChange?: (pages: any[]) => void; // Configurações de páginas
}

export const FileUpload = ({ type, file, onFileUpload, onFileRemove, onPagesConfigChange }: FileUploadProps) => {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [workbook, setWorkbook] = useState<XLSX.WorkBook | null>(null);
  const [selectedSheetIndex, setSelectedSheetIndex] = useState<number | null>(null);
  const [startCell, setStartCell] = useState<string>('A1');
  const [isConfiguring, setIsConfiguring] = useState(false);
  const [fileName, setFileName] = useState<string>('');
  const [useMultiPageMode, setUseMultiPageMode] = useState(false);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0];
      if (!selectedFile) return;

      const fileExtension = selectedFile.name.toLowerCase().split('.').pop();
      const supportedFormats = ['xlsx', 'xls', 'xlsm', 'csv'];
      
      if (!fileExtension || !supportedFormats.includes(fileExtension)) {
        toast({
          title: 'Erro',
          description: 'Por favor, selecione um arquivo Excel (.xlsx, .xls, .xlsm) ou CSV (.csv)',
          variant: 'destructive',
        });
        return;
      }

      setIsLoading(true);
      
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          let loadedWorkbook: XLSX.WorkBook;
          
          if (fileExtension === 'csv') {
            // Processar arquivo CSV como texto
            const text = event.target?.result as string;
            
            if (!text || text.trim() === '') {
              setIsLoading(false);
              toast({
                title: 'Erro',
                description: 'O arquivo CSV está vazio',
                variant: 'destructive',
              });
              return;
            }
            
            // Função para parse CSV robusto considerando aspas e diferentes delimitadores
            const parseCSV = (csvText: string): string[][] => {
              const lines = csvText.split(/\r?\n/).filter(line => line.trim() !== '');
              if (lines.length === 0) return [];
              
              // Detectar delimitador na primeira linha
              const firstLine = lines[0];
              const commaCount = (firstLine.match(/,/g) || []).length;
              const semicolonCount = (firstLine.match(/;/g) || []).length;
              const tabCount = (firstLine.match(/\t/g) || []).length;
              
              let delimiter = ',';
              if (tabCount > Math.max(commaCount, semicolonCount)) {
                delimiter = '\t';
              } else if (semicolonCount > commaCount) {
                delimiter = ';';
              }
              
              // Parse cada linha considerando aspas
              return lines.map(line => {
                const row: string[] = [];
                let currentCell = '';
                let inQuotes = false;
                
                for (let i = 0; i < line.length; i++) {
                  const char = line[i];
                  const nextChar = line[i + 1];
                  
                  if (char === '"') {
                    if (inQuotes && nextChar === '"') {
                      // Aspas duplas dentro de aspas = caractere literal
                      currentCell += '"';
                      i++; // Pular próximo caractere
                    } else {
                      // Alternar estado de aspas
                      inQuotes = !inQuotes;
                    }
                  } else if (char === delimiter && !inQuotes) {
                    // Fim da célula
                    row.push(currentCell);
                    currentCell = '';
                  } else {
                    currentCell += char;
                  }
                }
                
                // Adicionar última célula
                row.push(currentCell);
                
                return row;
              });
            };
            
            // Converter CSV para array de arrays
            const csvData = parseCSV(text);
            
            if (csvData.length === 0) {
              setIsLoading(false);
              toast({
                title: 'Erro',
                description: 'Não foi possível ler dados do arquivo CSV',
                variant: 'destructive',
              });
              return;
            }
            
            // Criar workbook a partir dos dados CSV
            loadedWorkbook = XLSX.utils.book_new();
            const sheet = XLSX.utils.aoa_to_sheet(csvData);
            XLSX.utils.book_append_sheet(loadedWorkbook, sheet, 'Sheet1');
          } else {
            // Processar arquivo Excel (.xlsx, .xls, .xlsm)
            const data = new Uint8Array(event.target?.result as ArrayBuffer);
            
            // Opções otimizadas para arquivos grandes
            loadedWorkbook = XLSX.read(data, {
              type: 'array',
              cellFormula: false,
              cellStyles: false,
              cellDates: false,
              dense: false,
              sheetStubs: false,
            });
          }
          
          const sheetNames = loadedWorkbook.SheetNames;
          
          if (sheetNames.length === 0) {
            setIsLoading(false);
            toast({
              title: 'Erro',
              description: 'A planilha não possui abas',
              variant: 'destructive',
            });
            return;
          }

          // Salvar workbook e mostrar interface de configuração
          setWorkbook(loadedWorkbook);
          setFileName(selectedFile.name);
          setSelectedSheetIndex(0);
          setStartCell('A1');
          setIsConfiguring(true);
          setIsLoading(false);
          setUseMultiPageMode(false); // Resetar modo multi-página
          
          toast({
            title: 'Arquivo carregado',
            description: `${sheetNames.length} aba(s) encontrada(s). Configure a leitura abaixo.`,
          });
        } catch (error) {
          setIsLoading(false);
          console.error('Error reading file:', error);
          
          // Mensagens de erro mais específicas
          let errorMessage = 'Erro ao ler o arquivo. Verifique se é um arquivo Excel válido.';
          if (error instanceof Error) {
            if (error.message.includes('memory') || error.message.includes('out of memory')) {
              errorMessage = 'Arquivo muito grande. Tente dividir em arquivos menores ou usar uma versão mais recente do navegador.';
            } else if (error.message.includes('corrupt') || error.message.includes('invalid')) {
              errorMessage = 'Arquivo corrompido ou inválido. Verifique se o arquivo não está danificado.';
            }
          }
          
          toast({
            title: 'Erro',
            description: errorMessage,
            variant: 'destructive',
          });
        }
      };
      
      reader.onerror = () => {
        setIsLoading(false);
        toast({
          title: 'Erro',
          description: 'Erro ao ler o arquivo. Tente novamente.',
          variant: 'destructive',
        });
      };
      
      // Ler arquivo CSV como texto, Excel como ArrayBuffer
      if (fileExtension === 'csv') {
        reader.readAsText(selectedFile, 'UTF-8');
      } else {
        reader.readAsArrayBuffer(selectedFile);
      }
    },
    [type, toast]
  );

  // Função para processar dados a partir da célula inicial
  const processDataFromCell = useCallback(() => {
    if (!workbook || selectedSheetIndex === null) {
      toast({
        title: 'Erro',
        description: 'Selecione uma aba primeiro',
        variant: 'destructive',
      });
      return;
    }

    try {
      const sheetName = workbook.SheetNames[selectedSheetIndex];
      const sheet = workbook.Sheets[sheetName];
      
      if (!sheet['!ref']) {
        toast({
          title: 'Erro',
          description: 'A aba selecionada está vazia',
          variant: 'destructive',
        });
        return;
      }

      // Converter célula inicial (ex: "A5") para índices
      // O usuário digita em formato Excel (1-based), mas decode_cell retorna (0-based)
      // Adicionamos +1 para compensar: se digitar A5, queremos ler linha 5 (índice 4), mas ajustamos para índice 5
      let startCellAddress;
      try {
        startCellAddress = XLSX.utils.decode_cell(startCell);
      } catch (error) {
        toast({
          title: 'Erro',
          description: 'Célula inicial inválida. Use formato como A5, B10, etc.',
          variant: 'destructive',
        });
        return;
      }
      
      // Adicionar +1 para compensar: A5 (linha 5 no Excel) = índice 4, mas queremos ler do índice 4
      // Na verdade, se o usuário digita A5, ele espera que leia A5, então precisamos manter o índice correto
      // Mas como o usuário disse que precisa digitar A6 para ler A5, vamos adicionar +1
      const startRow = startCellAddress.r + 1; // Adicionar 1 para compensar
      const startCol = startCellAddress.c;

      const range = sheet['!ref'];
      const decodedRange = XLSX.utils.decode_range(range);
      const maxRow = decodedRange.e.r;
      const maxCol = decodedRange.e.c;

      // Função para obter valor de célula considerando merges
      const getCellValue = (rowIdx: number, colIdx: number): any => {
        // Verificar merges primeiro
        const merges = sheet['!merges'] || [];
        for (const merge of merges) {
          const { s, e } = merge;
          if (rowIdx >= s.r && rowIdx <= e.r && colIdx >= s.c && colIdx <= e.c) {
            // Se está dentro do merge, pegar valor da célula inicial
            const startAddr = XLSX.utils.encode_cell({ r: s.r, c: s.c });
            const startCell = sheet[startAddr];
            if (startCell) {
              // Priorizar valor formatado, depois valor bruto
              if (startCell.w !== undefined) {
                return startCell.w;
              }
              if (startCell.v !== undefined && startCell.v !== null) {
                return String(startCell.v);
              }
            }
            // Se merge não tem valor, retornar vazio apenas se não for célula inicial
            if (rowIdx !== s.r || colIdx !== s.c) {
              return '';
            }
          }
        }
        
        // Célula normal (não está em merge)
        const cellAddress = XLSX.utils.encode_cell({ r: rowIdx, c: colIdx });
        const cell = sheet[cellAddress];
        
        if (cell) {
          // Priorizar valor formatado
          if (cell.w !== undefined && cell.w !== null) {
            return String(cell.w);
          }
          // Depois valor bruto
          if (cell.v !== undefined && cell.v !== null) {
            return String(cell.v);
          }
        }
        return '';
      };

      // Ler cabeçalho - buscar na linha antes da célula inicial
      // Se não encontrar valores, buscar algumas linhas acima
      let headerRow: any[] = [];
      let headerRowIndex = startRow - 1;
      let foundHeader = false;
      
      // Tentar encontrar cabeçalho (até 5 linhas acima)
      for (let tryRow = startRow - 1; tryRow >= Math.max(0, startRow - 5); tryRow--) {
        const candidateRow: any[] = [];
        let hasValues = false;
        
        for (let c = 0; c <= maxCol; c++) {
          const value = getCellValue(tryRow, c);
          candidateRow.push(value);
          if (String(value || '').trim() !== '') {
            hasValues = true;
          }
        }
        
        // Se encontrou valores nesta linha e parece com cabeçalho (mais texto que números)
        if (hasValues) {
          const textCount = candidateRow.filter(v => {
            const str = String(v || '').trim();
            return str !== '' && (isNaN(Number(str)) || str.length > 10);
          }).length;
          
          // Se mais da metade é texto, provavelmente é o cabeçalho
          if (textCount > candidateRow.length / 2 || tryRow === startRow - 1) {
            headerRow = candidateRow;
            headerRowIndex = tryRow;
            foundHeader = true;
            break;
          }
        }
      }
      
      // Se não encontrou cabeçalho, usar a linha imediatamente anterior
      if (!foundHeader && startRow > 0) {
        for (let c = 0; c <= maxCol; c++) {
          headerRow.push(getCellValue(startRow - 1, c));
        }
        headerRowIndex = startRow - 1;
      }

      // Processar dados a partir da célula inicial
      const allData: any[][] = [];
      const cellDataArray: CellData[][] = [];
      const headerValues = headerRow.map(v => String(v || '').trim().toLowerCase());
      
      console.log('Cabeçalho encontrado:', headerRow);
      console.log('Linha do cabeçalho:', headerRowIndex + 1);

      for (let r = startRow; r <= maxRow; r++) {
        const row: any[] = [];
        const cellRow: CellData[] = [];
        let isEmptyRow = true;

        for (let c = 0; c <= maxCol; c++) {
          const value = getCellValue(r, c);
          const strValue = String(value || '').trim();
          
          if (strValue !== '') {
            isEmptyRow = false;
          }

          row.push(value);
          cellRow.push({
            value,
            page: selectedSheetIndex + 1,
            pageName: sheetName,
            row: r + 1, // Excel usa 1-based
            col: c + 1,
            cellAddress: XLSX.utils.encode_cell({ r, c }),
          });
        }

        // Ignorar linha se estiver vazia
        if (isEmptyRow) {
          continue;
        }

        // Ignorar se for cabeçalho duplicado (todos os valores coincidem com o cabeçalho)
        const isDuplicateHeader = row.every((cell, idx) => {
          const cellStr = String(cell || '').trim().toLowerCase();
          if (cellStr === '') return true; // Células vazias não contam
          return idx < headerValues.length && headerValues[idx] === cellStr;
        }) && row.some(cell => String(cell || '').trim() !== '');

        if (!isDuplicateHeader) {
          allData.push(row);
          cellDataArray.push(cellRow);
        }
      }

      // Criar nomes de colunas - garantir que tenham nomes válidos
      const columns = headerRow.map((col, idx) => {
        const colStr = String(col || '').trim();
        // Se estiver vazio, tentar buscar valor formatado da célula
        if (colStr === '' && headerRowIndex >= 0) {
          const cellAddr = XLSX.utils.encode_cell({ r: headerRowIndex, c: idx });
          const cell = sheet[cellAddr];
          if (cell) {
            const formatted = cell.w || (cell.v !== undefined && cell.v !== null ? String(cell.v) : '');
            if (formatted.trim() !== '') {
              return formatted.trim();
            }
          }
        }
        return colStr !== '' ? colStr : `Coluna_${idx + 1}`;
      });
      
      console.log('Colunas finais:', columns);

      if (allData.length === 0) {
        toast({
          title: 'Aviso',
          description: 'Nenhum dado encontrado a partir da célula especificada',
          variant: 'destructive',
        });
        return;
      }

      const uploadedFile: UploadedFile = {
        name: fileName || 'arquivo.xlsx',
        columns,
        data: allData,
        type,
        sheets: workbook.SheetNames,
        cellData: cellDataArray,
      };

      onFileUpload(uploadedFile);
      setIsConfiguring(false);
      setWorkbook(null);

      toast({
        title: 'Sucesso!',
        description: `Dados processados: ${allData.length} linhas de dados a partir de ${startCell} na página ${selectedSheetIndex + 1}`,
      });
    } catch (error) {
      console.error('Error processing data:', error);
      toast({
        title: 'Erro',
        description: 'Erro ao processar dados. Verifique se a célula inicial está correta (ex: A5)',
        variant: 'destructive',
      });
    }
  }, [workbook, selectedSheetIndex, startCell, fileName, type, onFileUpload, toast]);

  const handleCancel = () => {
    setWorkbook(null);
    setIsConfiguring(false);
    setSelectedSheetIndex(null);
    setStartCell('A1');
    setFileName('');
  };

  const getTypeLabel = () => {
    switch (type) {
      case 'gabarito':
        return 'Gabarito';
      case 'custo':
        return 'Planilha de Custo';
      case 'venda':
        return 'Planilha de Venda';
    }
  };

  const getTypeColor = () => {
    switch (type) {
      case 'gabarito':
        return 'border-accent';
      case 'custo':
        return 'border-destructive';
      case 'venda':
        return 'border-primary';
    }
  };

  return (
    <Card className={`p-6 border-2 ${getTypeColor()} transition-all hover:shadow-lg`}>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5 text-primary" />
            <h3 className="font-semibold text-foreground">{getTypeLabel()}</h3>
          </div>
          {file && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onFileRemove}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {isConfiguring && workbook ? (
          <>
            {/* Modo multi-página */}
            <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg border border-border">
              <div className="flex items-center gap-3">
                <Layers className="h-5 w-5 text-primary" />
                <div>
                  <Label htmlFor="multi-page-mode" className="cursor-pointer">
                    Modo Multi-Página
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    Configure múltiplas páginas dinamicamente
                  </p>
                </div>
              </div>
              <Switch
                id="multi-page-mode"
                checked={useMultiPageMode}
                onCheckedChange={setUseMultiPageMode}
              />
            </div>

            {useMultiPageMode ? (
              <PageManager
                workbook={workbook}
                fileName={fileName}
                type={type}
                onPagesConfigChange={(pages: PageConfig[]) => {
                  if (onPagesConfigChange) {
                    onPagesConfigChange(pages);
                  }
                }}
                onFileReady={(uploadedFile) => {
                  onFileUpload(uploadedFile);
                  setIsConfiguring(false);
                  setWorkbook(null);
                }}
              />
            ) : (
              <div className="space-y-4 p-4 bg-muted/30 rounded-lg border border-border">
                <div className="space-y-2">
                  <Label htmlFor="sheet-select">Selecionar Página/Aba:</Label>
                  <Select
                    value={selectedSheetIndex?.toString() ?? ''}
                    onValueChange={(value) => setSelectedSheetIndex(parseInt(value))}
                  >
                    <SelectTrigger id="sheet-select">
                      <SelectValue placeholder="Selecione uma aba" />
                    </SelectTrigger>
                    <SelectContent>
                      {workbook.SheetNames.map((sheetName, index) => (
                        <SelectItem key={index} value={index.toString()}>
                          Página {index + 1}: {sheetName}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="start-cell">Célula Inicial (ex: A5):</Label>
                  <Input
                    id="start-cell"
                    type="text"
                    value={startCell}
                    onChange={(e) => setStartCell(e.target.value.toUpperCase())}
                    placeholder="A1"
                    pattern="[A-Z]+[0-9]+"
                  />
                  <p className="text-xs text-muted-foreground">
                    Digite a célula onde começam os dados. O cabeçalho será a linha anterior.
                  </p>
                </div>

                <div className="flex gap-2">
                  <Button onClick={processDataFromCell} className="flex-1">
                    <Search className="h-4 w-4 mr-2" />
                    Processar Dados
                  </Button>
                  <Button onClick={handleCancel} variant="outline">
                    Cancelar
                  </Button>
                </div>
              </div>
            )}
          </>
        ) : !file ? (
          <label className="flex flex-col items-center justify-center gap-2 p-8 border-2 border-dashed border-border rounded-lg cursor-pointer hover:bg-muted/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
            {isLoading ? (
              <>
                <Loader2 className="h-8 w-8 text-primary animate-spin" />
                <span className="text-sm text-muted-foreground">Processando arquivo...</span>
                <span className="text-xs text-muted-foreground">Aguarde, isso pode levar alguns segundos</span>
              </>
            ) : (
              <>
                <Upload className="h-8 w-8 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Clique para selecionar</span>
                <span className="text-xs text-muted-foreground">.xlsx, .xls, .xlsm ou .csv</span>
              </>
            )}
            <input
              type="file"
              accept=".xlsx,.xls,.xlsm,.csv"
              onChange={handleFileChange}
              className="hidden"
              disabled={isLoading}
            />
          </label>
        ) : (
          <div className="space-y-2 p-4 bg-muted/30 rounded-lg">
            <div className="flex items-center gap-2">
              <FileSpreadsheet className="h-4 w-4 text-success" />
              <span className="text-sm font-medium text-foreground truncate">{file.name}</span>
            </div>
            <div className="text-xs text-muted-foreground space-y-1">
              <div>{file.data.length} linhas de dados</div>
              <div>{file.columns.length} colunas encontradas</div>
              {file.sheets && (
                <div>Páginas: {file.sheets.join(', ')}</div>
              )}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};
