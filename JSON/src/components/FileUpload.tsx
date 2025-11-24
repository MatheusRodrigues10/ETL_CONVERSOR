import { useCallback, useState } from 'react';
import { Upload, FileSpreadsheet, X, Loader2, Pencil } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import * as XLSX from 'xlsx';
import { UploadedFile, PageConfig } from '@/types/spreadsheet';
import { PageManager } from './PageManager';

interface FileUploadProps {
  type: 'custo' | 'venda' | 'gabarito';
  file: UploadedFile | null;
  onFileUpload: (file: UploadedFile) => void;
  onFileRemove: () => void;
  onPagesConfigChange?: (pages: any[]) => void; // Configurações de páginas
  initialPagesConfig?: PageConfig[]; // Configurações iniciais de páginas
}

export const FileUpload = ({ type, file, onFileUpload, onFileRemove, onPagesConfigChange, initialPagesConfig = [] }: FileUploadProps) => {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [workbook, setWorkbook] = useState<XLSX.WorkBook | null>(null);
  const [isConfiguring, setIsConfiguring] = useState(false);
  const [fileName, setFileName] = useState<string>('');
  
  // Manter workbook mesmo após gerar arquivo para permitir edição posterior
  const handleFileReady = (uploadedFile: UploadedFile) => {
    onFileUpload(uploadedFile);
    setIsConfiguring(false);
    // Não limpar workbook aqui para permitir edição posterior
  };
  
  const handleEditConfig = () => {
    setIsConfiguring(true);
  };

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
          setIsConfiguring(true);
          setIsLoading(false);
          
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
              onClick={() => {
                onFileRemove();
                setWorkbook(null);
                setIsConfiguring(false);
              }}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {isConfiguring && workbook ? (
          <PageManager
            workbook={workbook}
            fileName={fileName}
            type={type}
            initialPagesConfig={initialPagesConfig}
            onPagesConfigChange={(pages: PageConfig[]) => {
              if (onPagesConfigChange) {
                onPagesConfigChange(pages);
              }
            }}
            onFileReady={handleFileReady}
          />
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
          <div className="space-y-3 p-4 bg-muted/30 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="h-4 w-4 text-success" />
                <span className="text-sm font-medium text-foreground truncate">{file.name}</span>
              </div>
              {workbook && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleEditConfig}
                  className="gap-2"
                >
                  <Pencil className="h-4 w-4" />
                  Editar Configurações
                </Button>
              )}
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
