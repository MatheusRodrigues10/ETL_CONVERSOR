import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { Card } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ColumnMapping, UploadedFile } from "@/types/spreadsheet";
import { ArrowRight, CheckCircle2, AlertCircle } from "lucide-react";
import { REQUIRED_COLUMNS, VARIATION_COLUMN } from "@/config/requiredColumns";

interface ColumnMapperProps {
  gabaritoColumns: string[];
  custoFile: UploadedFile | null;
  vendaFile: UploadedFile | null;
  mappings: ColumnMapping[];
  onMappingChange: (mappings: ColumnMapping[]) => void;
  title?: string;
}

export const ColumnMapper = ({
  gabaritoColumns,
  custoFile,
  vendaFile,
  mappings,
  onMappingChange,
  title = "Mapeamento de Colunas",
}: ColumnMapperProps) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const gabaritoColumnsSet = useMemo(
    () => new Set(gabaritoColumns),
    [gabaritoColumns]
  );

  const handleMapping = useCallback((
    gabaritoColumn: string,
    sourceColumn: string,
    sourceFile: "custo" | "venda"
  ) => {
    // Se selecionou vazio, criar mapeamento especial que indica valor vazio
    if (sourceColumn === "__EMPTY__") {
      const existingIndex = mappings.findIndex(
        (m) =>
          m.gabaritoColumn === gabaritoColumn && m.sourceFile === sourceFile
      );
      const newMapping: ColumnMapping = {
        gabaritoColumn,
        sourceColumn: "__EMPTY__",
        sourceFile,
      };

      if (existingIndex >= 0) {
        const updated = [...mappings];
        updated[existingIndex] = newMapping;
        onMappingChange(updated);
      } else {
        onMappingChange([...mappings, newMapping]);
      }
      return;
    }

    // Para campos que não são COR e há ambas as planilhas
    if (gabaritoColumn !== VARIATION_COLUMN && custoFile && vendaFile) {
      const updated = [...mappings];

      // Verificar se o valor é customizado (não está nas colunas das planilhas)
      const isCustom = (file: "custo" | "venda") => {
        const fileObj = file === "custo" ? custoFile : vendaFile;
        return fileObj ? !fileObj.columns.includes(sourceColumn) : false;
      };

      const isCustomValue = isCustom(sourceFile);

      // Se é um valor customizado, permitir que ambos os campos fiquem disponíveis
      // Caso contrário, garantir que apenas uma tenha valor ativo (comportamento original)
      if (!isCustomValue) {
        // Remover mapeamento da outra planilha (se existir) apenas para valores não-customizados
        const otherFile = sourceFile === "custo" ? "venda" : "custo";
        const otherIndex = updated.findIndex(
          (m) =>
            m.gabaritoColumn === gabaritoColumn && m.sourceFile === otherFile
        );
        if (otherIndex >= 0) {
          updated.splice(otherIndex, 1);
        }
      }

      // Adicionar ou atualizar o mapeamento da planilha atual
      const existingIndex = updated.findIndex(
        (m) =>
          m.gabaritoColumn === gabaritoColumn && m.sourceFile === sourceFile
      );
      const newMapping: ColumnMapping = {
        gabaritoColumn,
        sourceColumn,
        sourceFile,
      };

      if (existingIndex >= 0) {
        updated[existingIndex] = newMapping;
      } else {
        updated.push(newMapping);
      }

      onMappingChange(updated);
      return;
    }

    // Comportamento normal para COR ou quando há apenas uma planilha
    const existingIndex = mappings.findIndex(
      (m) => m.gabaritoColumn === gabaritoColumn && m.sourceFile === sourceFile
    );
    const newMapping: ColumnMapping = {
      gabaritoColumn,
      sourceColumn,
      sourceFile,
    };

    if (existingIndex >= 0) {
      const updated = [...mappings];
      updated[existingIndex] = newMapping;
      onMappingChange(updated);
    } else {
      onMappingChange([...mappings, newMapping]);
    }
  }, [mappings, custoFile, vendaFile, onMappingChange]);

  const handleNameMapping = useCallback((gabaritoColumn: string, name: string) => {
    // Criar ou atualizar mapeamento com a propriedade "name" para valores customizados compartilhados
    // Criar apenas UM mapeamento (não dois) para evitar duplicação na contagem
    const updated = [...mappings];

    // Remover mapeamentos existentes para esta coluna (tanto custo quanto venda)
    const filtered = updated.filter((m) => m.gabaritoColumn !== gabaritoColumn);

    // Criar apenas um mapeamento com a propriedade "name"
    // Usar a primeira planilha disponível (custo tem prioridade)
    const sourceFile = custoFile ? "custo" : vendaFile ? "venda" : "custo";

    const newMapping: ColumnMapping = {
      gabaritoColumn,
      sourceColumn: "__EMPTY__", // Não usar como sourceColumn
      sourceFile,
      name, // Usar como name
    };

    onMappingChange([...filtered, newMapping]);
  }, [mappings, custoFile, vendaFile, onMappingChange]);

  const handleMultipleMapping = useCallback((
    gabaritoColumn: string,
    sourceColumn: string,
    sourceFile: "custo" | "venda",
    checked: boolean
  ) => {
    const existingIndex = mappings.findIndex(
      (m) => m.gabaritoColumn === gabaritoColumn && m.sourceFile === sourceFile
    );

    let selectedColumns: string[] = [];

    if (existingIndex >= 0) {
      const existingMapping = mappings[existingIndex];
      if (Array.isArray(existingMapping.sourceColumn)) {
        selectedColumns = [...existingMapping.sourceColumn];
      } else if (
        existingMapping.sourceColumn &&
        existingMapping.sourceColumn !== "__EMPTY__"
      ) {
        selectedColumns = [existingMapping.sourceColumn];
      }
    }

    if (checked) {
      // Adicionar coluna se não estiver já selecionada
      if (!selectedColumns.includes(sourceColumn)) {
        selectedColumns.push(sourceColumn);
      }
    } else {
      // Remover coluna
      selectedColumns = selectedColumns.filter((col) => col !== sourceColumn);
    }

    const newMapping: ColumnMapping = {
      gabaritoColumn,
      sourceColumn: selectedColumns.length > 0 ? selectedColumns : "__EMPTY__",
      sourceFile,
    };

    if (existingIndex >= 0) {
      const updated = [...mappings];
      updated[existingIndex] = newMapping;
      onMappingChange(updated);
    } else {
      onMappingChange([...mappings, newMapping]);
    }
  }, [mappings, onMappingChange]);

  // Criar índice de mappings por coluna para otimizar buscas
  const mappingsByColumn = useMemo(() => {
    const index = new Map<string, { custo?: ColumnMapping; venda?: ColumnMapping }>();
    mappings.forEach((m) => {
      const existing = index.get(m.gabaritoColumn) || {};
      if (m.sourceFile === "custo") {
        existing.custo = m;
      } else {
        existing.venda = m;
      }
      index.set(m.gabaritoColumn, existing);
    });
    return index;
  }, [mappings]);

  const getCurrentValue = useCallback((column: string, sourceFile: "custo" | "venda") => {
    const columnMappings = mappingsByColumn.get(column);
    const mapping = sourceFile === "custo" ? columnMappings?.custo : columnMappings?.venda;
    if (!mapping) return "";

    if (Array.isArray(mapping.sourceColumn)) {
      // Para múltiplas seleções, retornar o primeiro valor (ou string vazia) para compatibilidade com Select
      return mapping.sourceColumn.length > 0 ? mapping.sourceColumn[0] : "";
    }

    return mapping.sourceColumn || "";
  }, [mappingsByColumn]);

  // Função para obter valor do select - retorna vazio se for valor customizado
  const getSelectValue = useCallback((column: string, sourceFile: "custo" | "venda") => {
    if (column === VARIATION_COLUMN) {
      // Para COR, usar getCurrentValue normal
      return getCurrentValue(column, sourceFile);
    }

    const value = getCurrentValue(column, sourceFile);
    if (!value || value === "__EMPTY__") {
      return "";
    }

    // Verificar se o valor é customizado (não está nas colunas da planilha)
    const file = sourceFile === "custo" ? custoFile : vendaFile;
    if (file && !file.columns.includes(value)) {
      // Se for valor customizado, retornar vazio para mostrar "Selecione..."
      return "";
    }

    return value;
  }, [getCurrentValue, custoFile, vendaFile]);

  // Função para verificar se há uma seleção válida no dropdown (não customizada, não vazia)
  const hasValidSelection = useCallback((
    column: string,
    sourceFile: "custo" | "venda"
  ): boolean => {
    const columnMappings = mappingsByColumn.get(column);
    const mapping = sourceFile === "custo" ? columnMappings?.custo : columnMappings?.venda;
    if (!mapping) return false;

    // Se tem propriedade "name", não é uma seleção do dropdown
    if (mapping.name) return false;

    const sourceColumn = Array.isArray(mapping.sourceColumn)
      ? mapping.sourceColumn[0]
      : mapping.sourceColumn;

    if (!sourceColumn || sourceColumn === "__EMPTY__") {
      return false;
    }

    // Verificar se o valor está nas colunas da planilha (não é customizado)
    const file = sourceFile === "custo" ? custoFile : vendaFile;
    if (file && file.columns.includes(sourceColumn)) {
      return true;
    }

    return false;
  }, [mappingsByColumn, custoFile, vendaFile]);

  const getSelectedColumns = useCallback((
    column: string,
    sourceFile: "custo" | "venda"
  ): string[] => {
    const columnMappings = mappingsByColumn.get(column);
    const mapping = sourceFile === "custo" ? columnMappings?.custo : columnMappings?.venda;
    if (!mapping) return [];

    if (Array.isArray(mapping.sourceColumn)) {
      return mapping.sourceColumn;
    }

    if (mapping.sourceColumn && mapping.sourceColumn !== "__EMPTY__") {
      return [mapping.sourceColumn];
    }

    return [];
  }, [mappingsByColumn]);

  const isColumnSelected = useCallback((
    column: string,
    sourceColumn: string,
    sourceFile: "custo" | "venda"
  ): boolean => {
    const selected = getSelectedColumns(column, sourceFile);
    return selected.includes(sourceColumn);
  }, [getSelectedColumns]);

  const isCustomValue = useCallback((
    column: string,
    sourceFile: "custo" | "venda"
  ): boolean => {
    if (column === VARIATION_COLUMN) return false; // Não se aplica a COR

    const columnMappings = mappingsByColumn.get(column);
    const mapping = sourceFile === "custo" ? columnMappings?.custo : columnMappings?.venda;
    if (
      !mapping ||
      !mapping.sourceColumn ||
      mapping.sourceColumn === "__EMPTY__"
    )
      return false;

    const value = Array.isArray(mapping.sourceColumn)
      ? mapping.sourceColumn[0]
      : mapping.sourceColumn;
    const file = sourceFile === "custo" ? custoFile : vendaFile;

    // Se o valor não está na lista de colunas do arquivo, é um valor customizado
    return file ? !file.columns.includes(value) : false;
  }, [mappingsByColumn, custoFile, vendaFile]);

  const isEitherEmpty = useCallback((column: string): boolean => {
    if (column === VARIATION_COLUMN || !custoFile || !vendaFile) return false;

    const columnMappings = mappingsByColumn.get(column);
    const custoMapping = columnMappings?.custo;
    const vendaMapping = columnMappings?.venda;

    return (
      custoMapping?.sourceColumn === "__EMPTY__" ||
      vendaMapping?.sourceColumn === "__EMPTY__"
    );
  }, [mappingsByColumn, custoFile, vendaFile]);

  const getCustomDefaultValue = useCallback((column: string): string => {
    // Primeiro verificar se há uma propriedade "name" (valor compartilhado)
    const columnMappings = mappingsByColumn.get(column);
    const custoMapping = columnMappings?.custo;
    const vendaMapping = columnMappings?.venda;

    // Se há uma propriedade "name", retornar ela
    if (custoMapping?.name) {
      return custoMapping.name;
    }
    if (vendaMapping?.name) {
      return vendaMapping.name;
    }

    // Caso contrário, retornar o valor customizado salvo (que não está nas colunas das planilhas)
    const custoValue = custoMapping?.sourceColumn;
    const vendaValue = vendaMapping?.sourceColumn;

    // Verificar se há um valor customizado (não está nas colunas das planilhas)
    if (
      custoValue &&
      custoValue !== "__EMPTY__" &&
      !Array.isArray(custoValue)
    ) {
      if (custoFile && !custoFile.columns.includes(custoValue)) {
        return custoValue;
      }
    }

    if (
      vendaValue &&
      vendaValue !== "__EMPTY__" &&
      !Array.isArray(vendaValue)
    ) {
      if (vendaFile && !vendaFile.columns.includes(vendaValue)) {
        return vendaValue;
      }
    }

    return "";
  }, [mappingsByColumn, custoFile, vendaFile]);

  // Sincronizar valores customizados com os inputs (apenas quando mappings mudam)
  useEffect(() => {
    if (!custoFile || !vendaFile) return;

    gabaritoColumns.forEach((column) => {
      if (column === VARIATION_COLUMN) return;

      const input = customInputRefs.current[column];
      if (!input) return;

      // Não atualizar inputs que estão sendo editados
      if (document.activeElement === input) return;

      const columnMappings = mappingsByColumn.get(column);
      const custoMapping = columnMappings?.custo;
      const vendaMapping = columnMappings?.venda;

      const customValue = getCustomDefaultValue(column);

      // Se há um valor customizado salvo
      if (customValue) {
        // Verificar se há propriedade "name" (valor compartilhado)
        const hasNameInMapping = custoMapping?.name || vendaMapping?.name;

        const custoValue = custoMapping?.sourceColumn;
        const vendaValue = vendaMapping?.sourceColumn;
        const hasCustomInMapping =
          hasNameInMapping ||
          (custoValue &&
            custoValue !== "__EMPTY__" &&
            !Array.isArray(custoValue) &&
            !custoFile.columns.includes(custoValue)) ||
          (vendaValue &&
            vendaValue !== "__EMPTY__" &&
            !Array.isArray(vendaValue) &&
            !vendaFile.columns.includes(vendaValue));

        if (hasCustomInMapping && input.value !== customValue) {
          input.value = customValue;
        }
      } else {
        // Se não há mais valor customizado, limpar apenas se não houver mapeamento válido
        const custoValue = custoMapping?.sourceColumn;
        const vendaValue = vendaMapping?.sourceColumn;

        // Verificar se há propriedade "name"
        const hasName = custoMapping?.name || vendaMapping?.name;

        // Limpar apenas se não há mapeamento ou se o mapeamento não é customizado
        const shouldClear =
          (!custoMapping && !vendaMapping) ||
          (!hasName &&
            (custoValue === "__EMPTY__" ||
              vendaValue === "__EMPTY__" ||
              (custoValue &&
                !Array.isArray(custoValue) &&
                custoFile.columns.includes(custoValue)) ||
              (vendaValue &&
                !Array.isArray(vendaValue) &&
                vendaFile.columns.includes(vendaValue))));

        if (shouldClear && input.value) {
          input.value = "";
        }
      }
    });
  }, [mappingsByColumn, custoFile, vendaFile, gabaritoColumns, getCustomDefaultValue]);

  // Refs para inputs customizados (para evitar re-renderizações)
  const customInputRefs = useRef<Record<string, HTMLInputElement | null>>({});

  // Contar colunas únicas mapeadas (não mapeamentos individuais)
  const totalMapped = useMemo(() => {
    const mappedColumns = new Set<string>();
    mappings.forEach((m) => {
      if (!gabaritoColumnsSet.has(m.gabaritoColumn)) return;

      // Verificar se é um mapeamento válido (não apenas __EMPTY__)
      const isValid =
        m.name ||
        (m.sourceColumn !== "__EMPTY__" &&
          (Array.isArray(m.sourceColumn) ? m.sourceColumn.length > 0 : true));
      if (isValid) {
        mappedColumns.add(m.gabaritoColumn);
      }
    });
    return mappedColumns.size;
  }, [mappings, gabaritoColumnsSet]);

  const progress = useMemo(() => {
    if (gabaritoColumns.length === 0) return 0;
    return (totalMapped / gabaritoColumns.length) * 100;
  }, [totalMapped, gabaritoColumns.length]);

  return (
    <Card className="p-6">
      <div className="space-y-6">
        <div>
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-lg text-foreground">
              {title}
            </h3>
            <Badge variant="secondary">
              {totalMapped} / {gabaritoColumns.length} mapeadas
            </Badge>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {gabaritoColumns.map((column, index) => {
            const custoMapping = mappings.find(
              (m) => m.gabaritoColumn === column && m.sourceFile === "custo"
            );
            const vendaMapping = mappings.find(
              (m) => m.gabaritoColumn === column && m.sourceFile === "venda"
            );

            // Verificar se realmente está mapeado (não apenas com __EMPTY__)
            // Para COR, não considerar mapeado se só tiver novas_variacoes (sem seleções via checkbox)
            const isMapped = (() => {
              // Para COR, verificar se há variações selecionadas via checkbox (não apenas novas_variacoes)
              if (column === VARIATION_COLUMN) {
                const custoVariations = custoMapping && Array.isArray(custoMapping.sourceColumn)
                  ? custoMapping.sourceColumn
                  : custoMapping?.sourceColumn && custoMapping.sourceColumn !== "__EMPTY__"
                  ? [custoMapping.sourceColumn]
                  : [];
                
                const vendaVariations = vendaMapping && Array.isArray(vendaMapping.sourceColumn)
                  ? vendaMapping.sourceColumn
                  : vendaMapping?.sourceColumn && vendaMapping.sourceColumn !== "__EMPTY__"
                  ? [vendaMapping.sourceColumn]
                  : [];

                // Obter variações que foram adicionadas via novas_variacoes
                const novasVariacoesCusto = custoMapping?.novas_variacoes
                  ? custoMapping.novas_variacoes.split(',').map((v) => v.trim().toUpperCase()).filter((v) => v.length > 0)
                  : [];
                const novasVariacoesVenda = vendaMapping?.novas_variacoes
                  ? vendaMapping.novas_variacoes.split(',').map((v) => v.trim().toUpperCase()).filter((v) => v.length > 0)
                  : [];
                const todasNovasVariacoes = [...new Set([...novasVariacoesCusto, ...novasVariacoesVenda])];

                // Filtrar variações que estão nas colunas das planilhas (selecionadas via checkbox)
                const custoVariationsCheckbox = custoVariations.filter((v) => {
                  if (custoFile && custoFile.columns.includes(v)) return true;
                  return false;
                });
                const vendaVariationsCheckbox = vendaVariations.filter((v) => {
                  if (vendaFile && vendaFile.columns.includes(v)) return true;
                  return false;
                });

                // Também incluir variações que foram adicionadas individualmente (não estão nas colunas)
                // mas que não vieram de novas_variacoes
                const custoVariationsCustom = custoVariations.filter((v) => {
                  if (custoFile && custoFile.columns.includes(v)) return false; // Já contou acima
                  if (todasNovasVariacoes.includes(v)) return false; // Veio de novas_variacoes
                  return true; // Foi adicionada individualmente
                });
                const vendaVariationsCustom = vendaVariations.filter((v) => {
                  if (vendaFile && vendaFile.columns.includes(v)) return false; // Já contou acima
                  if (todasNovasVariacoes.includes(v)) return false; // Veio de novas_variacoes
                  return true; // Foi adicionada individualmente
                });

                // Considerar mapeado apenas se houver variações selecionadas via checkbox ou adicionadas individualmente
                return (custoVariationsCheckbox.length > 0 || vendaVariationsCheckbox.length > 0 ||
                        custoVariationsCustom.length > 0 || vendaVariationsCustom.length > 0);
              }

              // Para outras colunas, usar lógica normal
              const custoIsValid =
                custoMapping &&
                (custoMapping.name ||
                  (custoMapping.sourceColumn !== "__EMPTY__" &&
                    (Array.isArray(custoMapping.sourceColumn)
                      ? custoMapping.sourceColumn.length > 0
                      : true)));
              const vendaIsValid =
                vendaMapping &&
                (vendaMapping.name ||
                  (vendaMapping.sourceColumn !== "__EMPTY__" &&
                    (Array.isArray(vendaMapping.sourceColumn)
                      ? vendaMapping.sourceColumn.length > 0
                      : true)));
              return !!(custoIsValid || vendaIsValid);
            })();

            const isRequired = REQUIRED_COLUMNS.includes(column as any);

            // Contar variações únicas para COR (excluindo as que vieram apenas de novas_variacoes)
            const uniqueVariationsCount = (() => {
              if (column !== VARIATION_COLUMN) return 0;
              
              // Obter variações que foram adicionadas via novas_variacoes
              const novasVariacoesCusto = custoMapping?.novas_variacoes
                ? custoMapping.novas_variacoes.split(',').map((v) => v.trim().toUpperCase()).filter((v) => v.length > 0)
                : [];
              const novasVariacoesVenda = vendaMapping?.novas_variacoes
                ? vendaMapping.novas_variacoes.split(',').map((v) => v.trim().toUpperCase()).filter((v) => v.length > 0)
                : [];
              const todasNovasVariacoes = new Set([...novasVariacoesCusto, ...novasVariacoesVenda]);
              
              const allVariations = new Set<string>();
              
              if (custoMapping) {
                const variations = Array.isArray(custoMapping.sourceColumn)
                  ? custoMapping.sourceColumn
                  : custoMapping.sourceColumn && custoMapping.sourceColumn !== "__EMPTY__"
                  ? [custoMapping.sourceColumn]
                  : [];
                
                variations.forEach((v) => {
                  if (v && v !== "__EMPTY__") {
                    // Incluir apenas se não veio apenas de novas_variacoes
                    // Ou seja, incluir se está nas colunas da planilha (checkbox) ou foi adicionada individualmente
                    if (custoFile && custoFile.columns.includes(v)) {
                      allVariations.add(v); // Selecionada via checkbox
                    } else if (!todasNovasVariacoes.has(v)) {
                      allVariations.add(v); // Adicionada individualmente (não veio de novas_variacoes)
                    }
                  }
                });
              }
              
              if (vendaMapping) {
                const variations = Array.isArray(vendaMapping.sourceColumn)
                  ? vendaMapping.sourceColumn
                  : vendaMapping.sourceColumn && vendaMapping.sourceColumn !== "__EMPTY__"
                  ? [vendaMapping.sourceColumn]
                  : [];
                
                variations.forEach((v) => {
                  if (v && v !== "__EMPTY__") {
                    // Incluir apenas se não veio apenas de novas_variacoes
                    if (vendaFile && vendaFile.columns.includes(v)) {
                      allVariations.add(v); // Selecionada via checkbox
                    } else if (!todasNovasVariacoes.has(v)) {
                      allVariations.add(v); // Adicionada individualmente (não veio de novas_variacoes)
                    }
                  }
                });
              }
              
              return allVariations.size;
            })();

            return (
              <div
                key={column}
                className={`p-4 border rounded-lg transition-all ${
                  isMapped
                    ? "border-success bg-success/5"
                    : isRequired
                    ? "border-warning bg-warning/5"
                    : "border-border"
                }`}
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Label className="text-sm font-semibold text-foreground">
                        {column}
                      </Label>
                      {isRequired && !isMapped && (
                        <Badge variant="destructive" className="h-5 text-xs">
                          Obrigatória
                        </Badge>
                      )}
                      {column === VARIATION_COLUMN && isMapped && (
                        <Badge variant="outline" className="h-5 text-xs">
                          {uniqueVariationsCount} selecionada
                          {uniqueVariationsCount !== 1 ? "s" : ""}
                        </Badge>
                      )}
                    </div>
                    {isMapped ? (
                      <CheckCircle2 className="h-4 w-4 text-success" />
                    ) : isRequired ? (
                      <AlertCircle className="h-4 w-4 text-warning" />
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    {custoFile && (
                      <div>
                        <Label className="text-xs text-muted-foreground mb-1">
                          Planilha de Custo
                          {column === VARIATION_COLUMN && (
                            <span className="text-muted-foreground ml-1 text-xs">
                              (Selecione múltiplas)
                            </span>
                          )}
                        </Label>
                        {column === VARIATION_COLUMN ? (
                          <div className="space-y-2 max-h-48 overflow-y-auto border rounded-md p-2">
                            {custoFile.columns.map((col) => (
                              <div
                                key={col}
                                className="flex items-center space-x-2"
                              >
                                <Checkbox
                                  id={`custo-${column}-${col}`}
                                  checked={isColumnSelected(
                                    column,
                                    col,
                                    "custo"
                                  )}
                                  onCheckedChange={(checked) =>
                                    handleMultipleMapping(
                                      column,
                                      col,
                                      "custo",
                                      checked === true
                                    )
                                  }
                                />
                                <Label
                                  htmlFor={`custo-${column}-${col}`}
                                  className="text-sm font-normal cursor-pointer flex-1"
                                >
                                  {col}
                                </Label>
                              </div>
                            ))}
                            <div className="flex gap-2 pt-2 border-t mt-2">
                              <Input
                                placeholder="Adicionar variação..."
                                onKeyDown={(e) => {
                                  const target = e.target as HTMLInputElement;
                                  const val = target.value.trim();
                                  if (e.key === "Enter" && val) {
                                    handleMultipleMapping(
                                      column,
                                      val,
                                      "custo",
                                      true
                                    );
                                    target.value = "";
                                  }
                                }}
                              />
                              <Button
                                type="button"
                                variant="outline"
                                onClick={(e) => {
                                  const input = e.currentTarget
                                    .previousElementSibling as HTMLInputElement;
                                  const val = input?.value.trim();
                                  if (val) {
                                    handleMultipleMapping(
                                      column,
                                      val,
                                      "custo",
                                      true
                                    );
                                    input.value = "";
                                  }
                                }}
                              >
                                Adicionar
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <>
                            <div className="flex gap-2">
                              <Select
                                value={getSelectValue(column, "custo")}
                                onValueChange={(value) =>
                                  handleMapping(column, value, "custo")
                                }
                              >
                                <SelectTrigger className="h-9 flex-1">
                                  <SelectValue placeholder="Selecione..." />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="__EMPTY__">
                                    <span className="text-muted-foreground italic">
                                      — Vazio —
                                    </span>
                                  </SelectItem>
                                  {custoFile.columns.map((col) => (
                                    <SelectItem key={col} value={col}>
                                      {col}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                              {hasValidSelection(column, "custo") && (
                                <Button
                                  type="button"
                                  variant="outline"
                                  size="icon"
                                  className="h-9 w-9"
                                  onClick={() => {
                                    // Remover completamente o mapeamento em vez de criar com __EMPTY__
                                    const updated = mappings.filter(
                                      (m) =>
                                        !(
                                          m.gabaritoColumn === column &&
                                          m.sourceFile === "custo"
                                        )
                                    );
                                    onMappingChange(updated);
                                  }}
                                  title="Limpar seleção"
                                >
                                  ×
                                </Button>
                              )}
                            </div>
                            {/* Mostrar input individual apenas se não houver ambas as planilhas */}
                            {!vendaFile && (
                              <div className="mt-2 flex gap-2">
                                <Input
                                  placeholder="Digite o nome"
                                  defaultValue={
                                    isCustomValue(column, "custo")
                                      ? getCurrentValue(column, "custo")
                                      : ""
                                  }
                                  onKeyDown={(e) => {
                                    const target = e.target as HTMLInputElement;
                                    if (
                                      e.key === "Enter" &&
                                      target.value.trim()
                                    ) {
                                      handleMapping(
                                        column,
                                        target.value.trim(),
                                        "custo"
                                      );
                                    }
                                  }}
                                />
                                <Button
                                  type="button"
                                  variant="outline"
                                  onClick={(e) => {
                                    const input = e.currentTarget
                                      .previousElementSibling as HTMLInputElement;
                                    if (input && input.value.trim()) {
                                      handleMapping(
                                        column,
                                        input.value.trim(),
                                        "custo"
                                      );
                                    }
                                  }}
                                >
                                  Usar
                                </Button>
                                {isCustomValue(column, "custo") && (
                                  <Button
                                    type="button"
                                    variant="outline"
                                    onClick={(e) => {
                                      // Limpar o mapeamento
                                      handleMapping(
                                        column,
                                        "__EMPTY__",
                                        "custo"
                                      );
                                      // Limpar o valor do input
                                      const input =
                                        e.currentTarget.parentElement?.querySelector(
                                          "input"
                                        ) as HTMLInputElement;
                                      if (input) {
                                        input.value = "";
                                      }
                                    }}
                                  >
                                    Limpar
                                  </Button>
                                )}
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    )}

                    {vendaFile && (
                      <div>
                        <Label className="text-xs text-muted-foreground mb-1">
                          Planilha de Venda
                          {column === VARIATION_COLUMN && (
                            <span className="text-muted-foreground ml-1 text-xs">
                              (Selecione múltiplas)
                            </span>
                          )}
                        </Label>
                        {column === VARIATION_COLUMN ? (
                          <div className="space-y-2 max-h-48 overflow-y-auto border rounded-md p-2">
                            {vendaFile.columns.map((col) => (
                              <div
                                key={col}
                                className="flex items-center space-x-2"
                              >
                                <Checkbox
                                  id={`venda-${column}-${col}`}
                                  checked={isColumnSelected(
                                    column,
                                    col,
                                    "venda"
                                  )}
                                  onCheckedChange={(checked) =>
                                    handleMultipleMapping(
                                      column,
                                      col,
                                      "venda",
                                      checked === true
                                    )
                                  }
                                />
                                <Label
                                  htmlFor={`venda-${column}-${col}`}
                                  className="text-sm font-normal cursor-pointer flex-1"
                                >
                                  {col}
                                </Label>
                              </div>
                            ))}
                            <div className="flex gap-2 pt-2 border-t mt-2">
                              <Input
                                placeholder="Adicionar variação..."
                                onKeyDown={(e) => {
                                  const target = e.target as HTMLInputElement;
                                  const val = target.value.trim();
                                  if (e.key === "Enter" && val) {
                                    handleMultipleMapping(
                                      column,
                                      val,
                                      "venda",
                                      true
                                    );
                                    target.value = "";
                                  }
                                }}
                              />
                              <Button
                                type="button"
                                variant="outline"
                                onClick={(e) => {
                                  const input = e.currentTarget
                                    .previousElementSibling as HTMLInputElement;
                                  const val = input?.value.trim();
                                  if (val) {
                                    handleMultipleMapping(
                                      column,
                                      val,
                                      "venda",
                                      true
                                    );
                                    input.value = "";
                                  }
                                }}
                              >
                                Adicionar
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <>
                            <div className="flex gap-2">
                              <Select
                                value={getSelectValue(column, "venda")}
                                onValueChange={(value) =>
                                  handleMapping(column, value, "venda")
                                }
                              >
                                <SelectTrigger className="h-9 flex-1">
                                  <SelectValue placeholder="Selecione..." />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="__EMPTY__">
                                    <span className="text-muted-foreground italic">
                                      — Vazio —
                                    </span>
                                  </SelectItem>
                                  {vendaFile.columns.map((col) => (
                                    <SelectItem key={col} value={col}>
                                      {col}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                              {hasValidSelection(column, "venda") && (
                                <Button
                                  type="button"
                                  variant="outline"
                                  size="icon"
                                  className="h-9 w-9"
                                  onClick={() => {
                                    // Remover completamente o mapeamento em vez de criar com __EMPTY__
                                    const updated = mappings.filter(
                                      (m) =>
                                        !(
                                          m.gabaritoColumn === column &&
                                          m.sourceFile === "venda"
                                        )
                                    );
                                    onMappingChange(updated);
                                  }}
                                  title="Limpar seleção"
                                >
                                  ×
                                </Button>
                              )}
                            </div>
                            {/* Mostrar input individual apenas se não houver ambas as planilhas */}
                            {!custoFile && (
                              <div className="mt-2 flex gap-2">
                                <Input
                                  placeholder="Digite o nome"
                                  defaultValue={
                                    isCustomValue(column, "venda")
                                      ? getCurrentValue(column, "venda")
                                      : ""
                                  }
                                  onKeyDown={(e) => {
                                    const target = e.target as HTMLInputElement;
                                    if (
                                      e.key === "Enter" &&
                                      target.value.trim()
                                    ) {
                                      handleMapping(
                                        column,
                                        target.value.trim(),
                                        "venda"
                                      );
                                    }
                                  }}
                                />
                                <Button
                                  type="button"
                                  variant="outline"
                                  onClick={(e) => {
                                    const input = e.currentTarget
                                      .previousElementSibling as HTMLInputElement;
                                    if (input && input.value.trim()) {
                                      handleMapping(
                                        column,
                                        input.value.trim(),
                                        "venda"
                                      );
                                    }
                                  }}
                                >
                                  Usar
                                </Button>
                                {isCustomValue(column, "venda") && (
                                  <Button
                                    type="button"
                                    variant="outline"
                                    onClick={(e) => {
                                      // Limpar o mapeamento
                                      handleMapping(
                                        column,
                                        "__EMPTY__",
                                        "venda"
                                      );
                                      // Limpar o valor do input
                                      const input =
                                        e.currentTarget.parentElement?.querySelector(
                                          "input"
                                        ) as HTMLInputElement;
                                      if (input) {
                                        input.value = "";
                                      }
                                    }}
                                  >
                                    Limpar
                                  </Button>
                                )}
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    )}

                    {/* Quando há ambas as planilhas e não é COR, mostrar um input compartilhado */}
                    {custoFile && vendaFile && column !== VARIATION_COLUMN && (
                      <div className="mt-2 pt-2 border-t">
                        <Label className="text-xs text-muted-foreground mb-1">
                          Digite um valor padrão (caso não haja dados, use esta
                          opção)
                        </Label>
                        <div className="flex gap-2">
                          <Input
                            ref={(el) => {
                              if (el) {
                                customInputRefs.current[column] = el;
                                // Inicializar valor apenas na primeira vez
                                if (!el.value) {
                                  const initialValue = getCustomDefaultValue(column);
                                  if (initialValue) {
                                    el.value = initialValue;
                                  }
                                }
                              } else {
                                delete customInputRefs.current[column];
                              }
                            }}
                            placeholder="Digite o nome"
                            onKeyDown={(e) => {
                              const target = e.target as HTMLInputElement;
                              if (e.key === "Enter" && target.value.trim()) {
                                const value = target.value.trim();
                                handleNameMapping(column, value);
                              }
                            }}
                          />
                          <Button
                            type="button"
                            variant="outline"
                            onClick={() => {
                              const input = customInputRefs.current[column];
                              const value = input?.value.trim() || "";
                              if (value) {
                                handleNameMapping(column, value);
                              }
                            }}
                          >
                            Usar
                          </Button>
                          {(getCustomDefaultValue(column) ||
                            (getCurrentValue(column, "custo") &&
                              getCurrentValue(column, "custo") !==
                                "__EMPTY__") ||
                            (getCurrentValue(column, "venda") &&
                              getCurrentValue(column, "venda") !==
                                "__EMPTY__")) && (
                            <Button
                              type="button"
                              variant="outline"
                              onClick={() => {
                                // Remover mapeamentos com "name" e valores customizados
                                const updated = mappings.filter(
                                  (m) => m.gabaritoColumn !== column
                                );
                                onMappingChange(updated);
                                // Limpar o valor do input
                                const input = customInputRefs.current[column];
                                if (input) {
                                  input.value = "";
                                }
                              }}
                            >
                              Limpar
                            </Button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
};
