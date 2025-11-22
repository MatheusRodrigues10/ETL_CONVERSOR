import { useState, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import * as XLSX from "xlsx";
import { PageConfig, UploadedFile, ColumnMapping } from "@/types/spreadsheet";
import {
  FileSpreadsheet,
  CheckCircle2,
  X,
  Plus,
  AlertCircle,
  Search,
} from "lucide-react";

interface PageManagerProps {
  workbook: XLSX.WorkBook | null;
  fileName: string;
  type: "custo" | "venda" | "gabarito";
  onPagesConfigChange: (pages: PageConfig[]) => void;
  onFileReady: (file: UploadedFile) => void;
}

export const PageManager = ({
  workbook,
  fileName,
  type,
  onPagesConfigChange,
  onFileReady,
}: PageManagerProps) => {
  const { toast } = useToast();
  const [selectedPages, setSelectedPages] = useState<number[]>([]);
  const [pageConfigs, setPageConfigs] = useState<PageConfig[]>([]);
  const [currentPageIndex, setCurrentPageIndex] = useState<number | null>(null);
  const [currentStartCell, setCurrentStartCell] = useState<string>("A1");
  const [currentColumns, setCurrentColumns] = useState<string[]>([]);
  const [currentColumnMappings, setCurrentColumnMappings] = useState<
    ColumnMapping[]
  >([]);
  const [currentStopRow, setCurrentStopRow] = useState<number | null>(null);
  const [isReviewing, setIsReviewing] = useState(false);

  const handlePageToggle = (pageIndex: number) => {
    setSelectedPages((prev) => {
      if (prev.includes(pageIndex)) {
        return prev.filter((p) => p !== pageIndex);
      } else {
        return [...prev, pageIndex];
      }
    });
  };

  const loadPageData = useCallback(
    (pageIndex: number, startCell: string) => {
      if (!workbook) return;

      try {
        const sheetName = workbook.SheetNames[pageIndex];
        const sheet = workbook.Sheets[sheetName];

        if (!sheet["!ref"]) {
          toast({
            title: "Erro",
            description: "A aba selecionada está vazia",
            variant: "destructive",
          });
          return null;
        }

        // Converter célula inicial
        const startCellAddress = XLSX.utils.decode_cell(startCell);
        const startRow = startCellAddress.r + 1;
        const startCol = startCellAddress.c;

        const range = sheet["!ref"];
        const decodedRange = XLSX.utils.decode_range(range);
        const maxRow = decodedRange.e.r;
        const maxCol = decodedRange.e.c;

        // Função para obter valor de célula considerando merges
        const getCellValue = (rowIdx: number, colIdx: number): any => {
          const merges = sheet["!merges"] || [];
          for (const merge of merges) {
            const { s, e } = merge;
            if (
              rowIdx >= s.r &&
              rowIdx <= e.r &&
              colIdx >= s.c &&
              colIdx <= e.c
            ) {
              const startAddr = XLSX.utils.encode_cell({ r: s.r, c: s.c });
              const startCell = sheet[startAddr];
              if (startCell) {
                if (startCell.w !== undefined) return startCell.w;
                if (startCell.v !== undefined && startCell.v !== null)
                  return String(startCell.v);
              }
              if (rowIdx !== s.r || colIdx !== s.c) return "";
            }
          }

          const cellAddress = XLSX.utils.encode_cell({ r: rowIdx, c: colIdx });
          const cell = sheet[cellAddress];

          if (cell) {
            if (cell.w !== undefined && cell.w !== null) return String(cell.w);
            if (cell.v !== undefined && cell.v !== null) return String(cell.v);
          }
          return "";
        };

        // Buscar cabeçalho
        let headerRow: any[] = [];
        let headerRowIndex = startRow - 1;

        for (
          let tryRow = startRow - 1;
          tryRow >= Math.max(0, startRow - 5);
          tryRow--
        ) {
          const candidateRow: any[] = [];
          let hasValues = false;

          for (let c = 0; c <= maxCol; c++) {
            const value = getCellValue(tryRow, c);
            candidateRow.push(value);
            if (String(value || "").trim() !== "") {
              hasValues = true;
            }
          }

          if (hasValues) {
            const textCount = candidateRow.filter((v) => {
              const str = String(v || "").trim();
              return str !== "" && (isNaN(Number(str)) || str.length > 10);
            }).length;

            if (
              textCount > candidateRow.length / 2 ||
              tryRow === startRow - 1
            ) {
              headerRow = candidateRow;
              headerRowIndex = tryRow;
              break;
            }
          }
        }

        if (!headerRow.length && startRow > 0) {
          for (let c = 0; c <= maxCol; c++) {
            headerRow.push(getCellValue(startRow - 1, c));
          }
        }

        // Criar nomes de colunas
        const columns = headerRow.map((col, idx) => {
          const colStr = String(col || "").trim();
          if (colStr === "" && headerRowIndex >= 0) {
            const cellAddr = XLSX.utils.encode_cell({
              r: headerRowIndex,
              c: idx,
            });
            const cell = sheet[cellAddr];
            if (cell) {
              const formatted =
                cell.w ||
                (cell.v !== undefined && cell.v !== null ? String(cell.v) : "");
              if (formatted.trim() !== "") {
                return formatted.trim();
              }
            }
          }
          return colStr !== "" ? colStr : `Coluna_${idx + 1}`;
        });

        return { columns, sheetName };
      } catch (error) {
        console.error("Error loading page data:", error);
        toast({
          title: "Erro",
          description: "Erro ao carregar dados da página",
          variant: "destructive",
        });
        return null;
      }
    },
    [workbook, toast]
  );

  const handleConfigurePage = (pageIndex: number) => {
    if (!workbook) return;

    // Buscar configuração existente ou usar padrão
    const existingConfig = pageConfigs.find((p) => p.pageIndex === pageIndex);
    if (existingConfig) {
      setCurrentStartCell(existingConfig.startCell);
      setCurrentColumns(existingConfig.columns);
      setCurrentColumnMappings(existingConfig.columnMappings);
      setCurrentStopRow(existingConfig.stopRow || null);
    } else {
      setCurrentStartCell("A1");
      setCurrentColumns([]);
      setCurrentColumnMappings([]);
      setCurrentStopRow(null);
    }

    setCurrentPageIndex(pageIndex);
    setIsReviewing(true);

    // Carregar dados da página
    const result = loadPageData(pageIndex, existingConfig?.startCell || "A1");
    if (result) {
      setCurrentColumns(result.columns);
    }
  };

  const handleApprovePage = () => {
    if (currentPageIndex === null || !workbook) return;

    const result = loadPageData(currentPageIndex, currentStartCell);
    if (!result) return;

    const newPageConfig: PageConfig = {
      pageIndex: currentPageIndex,
      pageName: result.sheetName || workbook.SheetNames[currentPageIndex],
      startCell: currentStartCell,
      columns: result.columns,
      columnMappings: currentColumnMappings,
      isApproved: true,
      stopRow: currentStopRow || undefined,
    };

    setPageConfigs((prev) => {
      const updated = prev.filter((p) => p.pageIndex !== currentPageIndex);
      return [...updated, newPageConfig];
    });

    setIsReviewing(false);
    setCurrentPageIndex(null);

    toast({
      title: "Página aprovada!",
      description: `Página ${currentPageIndex + 1} adicionada à configuração`,
    });

    // Atualizar configuração de páginas
    const updatedConfigs = [
      ...pageConfigs.filter((p) => p.pageIndex !== currentPageIndex),
      newPageConfig,
    ];
    onPagesConfigChange(updatedConfigs);
  };

  const handleReapplyPattern = () => {
    if (pageConfigs.length === 0 || currentPageIndex === null) {
      toast({
        title: "Aviso",
        description:
          "Configure pelo menos uma página primeiro para usar como padrão",
        variant: "destructive",
      });
      return;
    }

    // Usar a primeira página aprovada como padrão
    const patternPage = pageConfigs[0];

    if (patternPage) {
      setCurrentStartCell(patternPage.startCell);
      setCurrentColumnMappings(
        patternPage.columnMappings.map((m) => ({
          ...m,
          pageIndex: currentPageIndex,
        }))
      );

      // Recarregar dados com novo startCell
      const result = loadPageData(currentPageIndex, patternPage.startCell);
      if (result) {
        setCurrentColumns(result.columns);
      }

      toast({
        title: "Padrão aplicado",
        description:
          "Configuração da primeira página aplicada. Revise e ajuste se necessário.",
      });
    }
  };

  const processPageData = useCallback(
    (pageConfig: PageConfig) => {
      if (!workbook) return null;

      try {
        const sheet = workbook.Sheets[pageConfig.pageName];
        if (!sheet["!ref"]) return null;

        const startCellAddress = XLSX.utils.decode_cell(pageConfig.startCell);
        const startRow = startCellAddress.r + 1;
        const range = sheet["!ref"];
        const decodedRange = XLSX.utils.decode_range(range);
        const maxRow = decodedRange.e.r;
        const maxCol = decodedRange.e.c;

        const getCellValue = (rowIdx: number, colIdx: number): any => {
          const merges = sheet["!merges"] || [];
          for (const merge of merges) {
            const { s, e } = merge;
            if (
              rowIdx >= s.r &&
              rowIdx <= e.r &&
              colIdx >= s.c &&
              colIdx <= e.c
            ) {
              const startAddr = XLSX.utils.encode_cell({ r: s.r, c: s.c });
              const startCell = sheet[startAddr];
              if (startCell) {
                if (startCell.w !== undefined) return startCell.w;
                if (startCell.v !== undefined && startCell.v !== null)
                  return String(startCell.v);
              }
              if (rowIdx !== s.r || colIdx !== s.c) return "";
            }
          }

          const cellAddress = XLSX.utils.encode_cell({ r: rowIdx, c: colIdx });
          const cell = sheet[cellAddress];
          if (cell) {
            if (cell.w !== undefined && cell.w !== null) return String(cell.w);
            if (cell.v !== undefined && cell.v !== null) return String(cell.v);
          }
          return "";
        };

        const allData: any[][] = [];
        const headerRowIndex = startRow - 1;
        const headerValues: string[] = [];

        if (headerRowIndex >= 0) {
          for (let c = 0; c <= maxCol; c++) {
            headerValues.push(
              String(getCellValue(headerRowIndex, c) || "")
                .trim()
                .toLowerCase()
            );
          }
        }

        // Determinar a linha máxima a processar (respeitando stopRow se definido)
        // startRow é 1-based, maxRow é 0-based, stopRow é 1-based
        // Precisamos converter tudo para 0-based para o loop
        const startRow0Based = startRow - 1; // Converter para 0-based
        const effectiveMaxRow = pageConfig.stopRow 
          ? Math.min(maxRow, pageConfig.stopRow - 1) // stopRow é 1-based, então subtraímos 1 para 0-based
          : maxRow;

        for (let r = startRow0Based; r <= effectiveMaxRow; r++) {
          const row: any[] = [];
          let isEmptyRow = true;

          for (let c = 0; c <= maxCol; c++) {
            const value = getCellValue(r, c);
            const strValue = String(value || "").trim();
            if (strValue !== "") isEmptyRow = false;
            row.push(value);
          }

          if (isEmptyRow) continue;

          const isDuplicateHeader =
            row.every((cell, idx) => {
              const cellStr = String(cell || "")
                .trim()
                .toLowerCase();
              if (cellStr === "") return true;
              return idx < headerValues.length && headerValues[idx] === cellStr;
            }) && row.some((cell) => String(cell || "").trim() !== "");

          if (!isDuplicateHeader) {
            allData.push(row);
          }
        }

        return allData;
      } catch (error) {
        console.error("Error processing page data:", error);
        return null;
      }
    },
    [workbook]
  );

  const handleGenerateFile = () => {
    if (pageConfigs.length === 0) {
      toast({
        title: "Erro",
        description: "Configure pelo menos uma página antes de gerar o arquivo",
        variant: "destructive",
      });
      return;
    }

    // Combinar todas as colunas e dados de todas as páginas
    const allColumns = new Set<string>();
    const allData: any[][] = [];

    pageConfigs.forEach((pageConfig) => {
      pageConfig.columns.forEach((col) => allColumns.add(col));
    });

    // Processar dados de cada página
    pageConfigs.forEach((pageConfig) => {
      const pageData = processPageData(pageConfig);
      if (pageData) {
        // Normalizar dados para ter o mesmo número de colunas
        const normalizedData = pageData.map((row) => {
          const normalizedRow = [...row];
          const maxCols = Array.from(allColumns).length;
          while (normalizedRow.length < maxCols) {
            normalizedRow.push("");
          }
          return normalizedRow.slice(0, maxCols);
        });
        allData.push(...normalizedData);
      }
    });

    const combinedFile: UploadedFile = {
      name: fileName,
      columns: Array.from(allColumns),
      data: allData,
      type,
      sheets: pageConfigs.map((p) => p.pageName),
    };

    onFileReady(combinedFile);

    toast({
      title: "Sucesso!",
      description: `Arquivo gerado com ${pageConfigs.length} página(s) e ${allData.length} linhas de dados`,
    });
  };

  if (!workbook) return null;

  const sheetNames = workbook.SheetNames;

  return (
    <Card className="p-6">
      <div className="space-y-6">
        <div>
          <h3 className="font-semibold text-lg text-foreground mb-2">
            Gerenciador de Páginas
          </h3>
          <p className="text-sm text-muted-foreground">
            Selecione e configure as páginas que deseja incluir no JSON
          </p>
        </div>

        {/* Seleção de páginas */}
        <div className="space-y-3">
          <Label>Selecionar Páginas:</Label>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 auto-rows-fr">
            {sheetNames.map((sheetName, index) => {
              const checkboxId = `page-${type}-${index}`;
              return (
              <div
                key={index}
                className="flex items-start space-x-2 p-3 border rounded-lg hover:bg-muted/50 transition-colors h-full min-h-[80px]"
              >
                <Checkbox
                  id={checkboxId}
                  checked={selectedPages.includes(index)}
                  onCheckedChange={() => handlePageToggle(index)}
                  className="shrink-0 mt-0.5"
                />
                <Label
                  htmlFor={checkboxId}
                  className="flex-1 cursor-pointer text-sm leading-tight min-w-0"
                >
                  <div className="font-medium mb-1">Página {index + 1}</div>
                  <div className="text-xs text-muted-foreground break-words hyphens-auto">
                    {sheetName}
                  </div>
                </Label>
              </div>
            );})}
          </div>
        </div>

        {/* Configurar páginas selecionadas */}
        {selectedPages.length > 0 && (
          <div className="space-y-3">
            <Label>Configurar Páginas Selecionadas:</Label>
            <div className="flex flex-wrap gap-2">
              {selectedPages.map((pageIndex) => {
                const config = pageConfigs.find(
                  (p) => p.pageIndex === pageIndex
                );
                return (
                  <Button
                    key={pageIndex}
                    variant={config?.isApproved ? "default" : "outline"}
                    onClick={() => handleConfigurePage(pageIndex)}
                    className="gap-2 shrink-0"
                  >
                    {config?.isApproved && <CheckCircle2 className="h-4 w-4" />}
                    Página {pageIndex + 1}
                    {config?.isApproved && ` ✓`}
                  </Button>
                );
              })}
            </div>
          </div>
        )}

        {/* Modal de revisão */}
        {isReviewing && currentPageIndex !== null && (
          <Card className="p-6 border-2 border-primary bg-primary/5">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-foreground">
                    Configurando: Página {currentPageIndex + 1}
                  </h4>
                  <p className="text-sm text-muted-foreground">
                    {workbook.SheetNames[currentPageIndex]}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsReviewing(false)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              <div className="space-y-4">
                <div>
                  <Label htmlFor="review-start-cell">Célula Inicial:</Label>
                  <div className="flex gap-2 mt-2">
                    <Input
                      id="review-start-cell"
                      type="text"
                      value={currentStartCell}
                      onChange={(e) => {
                        setCurrentStartCell(e.target.value.toUpperCase());
                        const result = loadPageData(
                          currentPageIndex,
                          e.target.value.toUpperCase()
                        );
                        if (result) {
                          setCurrentColumns(result.columns);
                        }
                      }}
                      placeholder="A5"
                      className="flex-1"
                    />
                    {pageConfigs.some((p) => p.isApproved) && (
                      <Button
                        variant="outline"
                        onClick={handleReapplyPattern}
                        className="gap-2"
                      >
                        <Search className="h-4 w-4" />
                        Reaplicar Padrão
                      </Button>
                    )}
                  </div>
                </div>

                {currentColumns.length > 0 && (
                  <div>
                    <Label>Colunas Detectadas ({currentColumns.length}):</Label>
                    <div className="mt-2 p-3 bg-muted/30 rounded-lg max-h-40 overflow-y-auto">
                      <div className="flex flex-wrap gap-2">
                        {currentColumns.map((col, idx) => (
                          <Badge
                            key={idx}
                            variant="secondary"
                            className="text-xs"
                          >
                            {col}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                <div>
                  <Label htmlFor="review-stop-row">Linha de Parada (opcional):</Label>
                  <div className="flex gap-2 mt-2">
                    <Input
                      id="review-stop-row"
                      type="number"
                      min="1"
                      placeholder="Ex: 100"
                      value={currentStopRow || ""}
                      onChange={(e) => {
                        const value = e.target.value;
                        if (value === "") {
                          setCurrentStopRow(null);
                        } else {
                          const numValue = parseInt(value, 10);
                          if (!isNaN(numValue) && numValue > 0) {
                            setCurrentStopRow(numValue);
                          }
                        }
                      }}
                      onKeyDown={(e) => {
                        // Permitir apenas números, backspace, delete, tab, escape, enter
                        const allowedKeys = [
                          "Backspace",
                          "Delete",
                          "Tab",
                          "Escape",
                          "Enter",
                          "ArrowLeft",
                          "ArrowRight",
                          "ArrowUp",
                          "ArrowDown",
                        ];
                        const isNumber = /^[0-9]$/.test(e.key);
                        if (!isNumber && !allowedKeys.includes(e.key)) {
                          e.preventDefault();
                        }
                      }}
                      className="max-w-[200px]"
                    />
                    {currentStopRow !== null && (
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setCurrentStopRow(null)}
                      >
                        Limpar
                      </Button>
                    )}
                  </div>
                  {currentStopRow !== null && (
                    <div className="mt-2">
                      <Badge
                        variant="secondary"
                        className="flex items-center gap-1 pr-1 w-fit"
                      >
                        <span>Linha {currentStopRow}</span>
                        <button
                          type="button"
                          onClick={() => setCurrentStopRow(null)}
                          className="ml-1 rounded-full hover:bg-destructive/20 p-0.5 transition-colors"
                          title="Remover linha de parada"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    </div>
                  )}
                </div>

                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Revise a célula inicial, as colunas detectadas e a linha de parada (se necessário). Você pode
                    ajustar antes de aprovar esta página.
                  </AlertDescription>
                </Alert>

                <div className="flex gap-2">
                  <Button onClick={handleApprovePage} className="flex-1">
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    Aprovar Página
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setIsReviewing(false)}
                  >
                    Cancelar
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Lista de páginas aprovadas */}
        {pageConfigs.length > 0 && (
          <div className="space-y-2">
            <Label>Páginas Configuradas ({pageConfigs.length}):</Label>
            <div className="space-y-2">
              {pageConfigs.map((config) => (
                <div
                  key={config.pageIndex}
                  className="flex items-center justify-between p-3 border rounded-lg bg-muted/30"
                >
                  <div>
                    <div className="font-medium">
                      Página {config.pageIndex + 1}: {config.pageName}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Início: {config.startCell} • {config.columns.length}{" "}
                      colunas
                      {config.stopRow && ` • Parar na linha: ${config.stopRow}`}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleConfigurePage(config.pageIndex)}
                    >
                      Editar
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setPageConfigs((prev) =>
                          prev.filter((p) => p.pageIndex !== config.pageIndex)
                        );
                        onPagesConfigChange(
                          pageConfigs.filter(
                            (p) => p.pageIndex !== config.pageIndex
                          )
                        );
                      }}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Botão final */}
        {pageConfigs.length > 0 && (
          <Button onClick={handleGenerateFile} className="w-full" size="lg">
            <FileSpreadsheet className="h-4 w-4 mr-2" />
            Gerar Arquivo com {pageConfigs.length} Página(s)
          </Button>
        )}
      </div>
    </Card>
  );
};
