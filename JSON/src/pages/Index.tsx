import { useState, useEffect, useCallback, useMemo } from "react";
import { FileUpload } from "@/components/FileUpload";
import { ColumnMapper } from "@/components/ColumnMapper";
import { MergeConfig } from "@/components/MergeConfig";
import { JsonOutput } from "@/components/JsonOutput";
import { SeparadoresBuilder } from "@/components/SeparadoresBuilder";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AlertCircle } from "lucide-react";
import {
  UploadedFile,
  ColumnMapping,
  MergeConfig as MergeConfigType,
  PandasConfig,
  PageConfig,
} from "@/types/spreadsheet";
import {
  FileSpreadsheet,
  ArrowRight,
  CheckCircle2,
  Download,
  Info,
  X,
} from "lucide-react";
import {
  REQUIRED_COLUMNS,
  ALL_COLUMNS,
  OPTIONAL_COLUMNS,
  VARIATION_COLUMN,
  IMMUTABLE_OPTIONAL_COLUMNS,
  MERGE_COLUMNS,
} from "@/config/requiredColumns";

const addImmutableOptionalDefaults = (
  mappings: ColumnMapping[],
  hasCusto: boolean,
  hasVenda: boolean
): ColumnMapping[] => {
  if (!hasCusto && !hasVenda) {
    return mappings;
  }

  const existingColumns = new Set(
    mappings.map((mapping) => mapping.gabaritoColumn)
  );
  const defaultSourceFile: "custo" | "venda" = hasCusto ? "custo" : "venda";

  const additionalMappings: ColumnMapping[] = IMMUTABLE_OPTIONAL_COLUMNS.filter(
    (column) => !existingColumns.has(column)
  ).map((column) => ({
    gabaritoColumn: column,
    sourceColumn: "__EMPTY__",
    sourceFile: defaultSourceFile,
    name: "VAZIO",
  }));

  if (additionalMappings.length === 0) {
    return mappings;
  }

  return [...mappings, ...additionalMappings];
};

const Index = () => {
  const [gabaritoFile, setGabaritoFile] = useState<UploadedFile | null>(null);
  const [custoFile, setCustoFile] = useState<UploadedFile | null>(null);
  const [vendaFile, setVendaFile] = useState<UploadedFile | null>(null);
  const [columnMappings, setColumnMappings] = useState<ColumnMapping[]>([]);
  const [mergeConfig, setMergeConfig] = useState<MergeConfigType | null>(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [generatedConfig, setGeneratedConfig] = useState<PandasConfig | null>(
    null
  );
  const [custoPagesConfig, setCustoPagesConfig] = useState<PageConfig[]>([]);
  const [vendaPagesConfig, setVendaPagesConfig] = useState<PageConfig[]>([]);
  const [separadoresConfig, setSeparadoresConfig] = useState<any>(null);

  // Usar as colunas obrigatórias predefinidas, excluindo as colunas de merge (CUSTO e PRECO1)
  const requiredColumns = Array.from(REQUIRED_COLUMNS).filter(
    (col) => !MERGE_COLUMNS.includes(col as any)
  );
  const allColumns = Array.from(ALL_COLUMNS);
  const optionalColumns = Array.from(OPTIONAL_COLUMNS);

  // Verificar quantas colunas obrigatórias foram mapeadas (contar apenas colunas únicas válidas)
  const mappedRequiredColumns = (() => {
    const mappedColumns = new Set<string>();

    // Agrupar mapeamentos por coluna
    const mappingsByColumn = new Map<string, ColumnMapping[]>();
    columnMappings.forEach((m) => {
      if (!mappingsByColumn.has(m.gabaritoColumn)) {
        mappingsByColumn.set(m.gabaritoColumn, []);
      }
      mappingsByColumn.get(m.gabaritoColumn)!.push(m);
    });

    mappingsByColumn.forEach((mappings, gabaritoColumn) => {
      // Verificar se é uma coluna obrigatória (excluindo colunas de merge)
      if (
        !REQUIRED_COLUMNS.includes(gabaritoColumn as any) ||
        MERGE_COLUMNS.includes(gabaritoColumn as any)
      )
        return;

      // Para a coluna COR, verificar se há variações selecionadas via checkbox ou adicionadas individualmente
      if (gabaritoColumn === VARIATION_COLUMN) {
        const custoMapping = mappings.find((m) => m.sourceFile === "custo");
        const vendaMapping = mappings.find((m) => m.sourceFile === "venda");

        // Obter variações que foram adicionadas via novas_variacoes
        const novasVariacoesCusto = custoMapping?.novas_variacoes
          ? custoMapping.novas_variacoes
              .split(",")
              .map((v) => v.trim().toUpperCase())
              .filter((v) => v.length > 0)
          : [];
        const novasVariacoesVenda = vendaMapping?.novas_variacoes
          ? vendaMapping.novas_variacoes
              .split(",")
              .map((v) => v.trim().toUpperCase())
              .filter((v) => v.length > 0)
          : [];
        const todasNovasVariacoes = new Set([
          ...novasVariacoesCusto,
          ...novasVariacoesVenda,
        ]);

        // Verificar se há variações selecionadas via checkbox ou adicionadas individualmente
        let hasValidVariations = false;

        [custoMapping, vendaMapping].forEach((mapping, index) => {
          if (!mapping) return;
          const file = index === 0 ? custoFile : vendaFile;
          if (!file) return;

          const variations = Array.isArray(mapping.sourceColumn)
            ? mapping.sourceColumn
            : mapping.sourceColumn && mapping.sourceColumn !== "__EMPTY__"
            ? [mapping.sourceColumn]
            : [];

          // Verificar se há variações que estão nas colunas da planilha (checkbox) ou foram adicionadas individualmente
          const hasCheckboxVariations = variations.some((v) =>
            file.columns.includes(v)
          );
          const hasCustomVariations = variations.some(
            (v) => !file.columns.includes(v) && !todasNovasVariacoes.has(v)
          );

          if (hasCheckboxVariations || hasCustomVariations) {
            hasValidVariations = true;
          }
        });

        if (hasValidVariations) {
          mappedColumns.add(gabaritoColumn);
        }
      } else {
        // Para outras colunas, usar lógica normal
        const isValid = mappings.some(
          (m) =>
            m.name ||
            (m.sourceColumn !== "__EMPTY__" &&
              (Array.isArray(m.sourceColumn)
                ? m.sourceColumn.length > 0
                : true))
        );
        if (isValid) {
          mappedColumns.add(gabaritoColumn);
        }
      }
    });

    return Array.from(mappedColumns);
  })();
  const requiredMappingProgress =
    (mappedRequiredColumns.length / requiredColumns.length) * 100;

  const canProceedToStep2 = true; // Sempre pode prosseguir pois temos o gabarito padrão
  const canProceedToStep3 = custoFile !== null || vendaFile !== null;
  const canProceedToStep4 =
    canProceedToStep3 &&
    mappedRequiredColumns.length === requiredColumns.length;
  const canGenerate =
    canProceedToStep4 &&
    custoFile &&
    vendaFile &&
    mergeConfig?.leftKey &&
    mergeConfig?.rightKey;

  useEffect(() => {
    if (canGenerate && columnMappings.length > 0) {
      // Combinar todas as páginas configuradas
      const allPages: PageConfig[] = [];

      const finalColumnMappings = addImmutableOptionalDefaults(
        columnMappings,
        !!custoFile,
        !!vendaFile
      );

      // Adicionar automaticamente as colunas CUSTO e PRECO1 no formato MERGE
      // Remover essas colunas se já existirem no mapeamento (para garantir o formato correto)
      const mergedMappings = finalColumnMappings.filter(
        (m) => !MERGE_COLUMNS.includes(m.gabaritoColumn as any)
      );

      // Adicionar CUSTO e PRECO1 no formato especificado
      const mergeColumnsMappings: ColumnMapping[] = MERGE_COLUMNS.map(
        (col) => ({
          gabaritoColumn: col,
          sourceColumn: "__EMPTY__",
          sourceFile: "custo" as const,
          name: "MERGE",
        })
      );

      const finalMappingsWithMerge = [
        ...mergedMappings,
        ...mergeColumnsMappings,
      ];

      // Adicionar páginas de custo (se houver)
      if (custoPagesConfig.length > 0) {
        allPages.push(
          ...custoPagesConfig.map((page) => ({
            ...page,
            columnMappings: page.columnMappings.map((m) => ({
              ...m,
              sourceFile: "custo" as const,
            })),
          }))
        );
      }

      // Adicionar páginas de venda (se houver)
      if (vendaPagesConfig.length > 0) {
        allPages.push(
          ...vendaPagesConfig.map((page) => ({
            ...page,
            columnMappings: page.columnMappings.map((m) => ({
              ...m,
              sourceFile: "venda" as const,
            })),
          }))
        );
      }

      const config: PandasConfig = {
        gabarito: {
          requiredColumns: Array.from(REQUIRED_COLUMNS),
          optionalColumns: Array.from(OPTIONAL_COLUMNS),
          allColumns: Array.from(ALL_COLUMNS),
        },
        files: {
          ...(custoFile && {
            custo: {
              columns: custoFile.columns,
              path: custoFile.name,
            },
          }),
          ...(vendaFile && {
            venda: {
              columns: vendaFile.columns,
              path: vendaFile.name,
            },
          }),
        },
        columnMapping: finalMappingsWithMerge,
        mergeConfig: mergeConfig
          ? { ...mergeConfig, how: "inner", includeVariationKey: true }
          : undefined,
        colorColumn: VARIATION_COLUMN,
        pages: allPages.length > 0 ? allPages : undefined, // Incluir páginas se houver
      };
      setGeneratedConfig(config);
    }
  }, [
    columnMappings,
    mergeConfig,
    custoFile,
    vendaFile,
    canGenerate,
    custoPagesConfig,
    vendaPagesConfig,
  ]);

  const steps = [
    {
      number: 1,
      title: "Upload das Planilhas",
      completed: custoFile !== null || vendaFile !== null,
    },
    {
      number: 2,
      title: "Mapeamento de Colunas",
      completed: mappedRequiredColumns.length === requiredColumns.length,
    },
    { number: 3, title: "Configuração de Merge", completed: canGenerate },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center gap-3">
            <FileSpreadsheet className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-2xl font-bold text-foreground">LUI HOME</h1>
              <p className="text-sm text-muted-foreground">
                Automatize a padronização de planilhas Excel
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Progress Steps */}
      <div className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between max-w-4xl mx-auto">
            {steps.map((step, index) => (
              <div key={step.number} className="flex items-center flex-1">
                <div className="flex items-center gap-2 flex-1">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold transition-all ${
                      step.completed
                        ? "bg-success text-success-foreground"
                        : currentStep === step.number
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {step.completed ? (
                      <CheckCircle2 className="h-5 w-5" />
                    ) : (
                      step.number
                    )}
                  </div>
                  <span
                    className={`text-sm font-medium hidden md:block ${
                      step.completed || currentStep === step.number
                        ? "text-foreground"
                        : "text-muted-foreground"
                    }`}
                  >
                    {step.title}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <ArrowRight className="h-4 w-4 text-muted-foreground mx-2 flex-shrink-0" />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-7xl mx-auto space-y-8">
          {/* Info sobre Gabarito */}
          <Alert className="border-info bg-info/5">
            <Info className="h-4 w-4 text-info" />
            <AlertDescription className="flex items-center justify-between">
              <div>
                <strong className="text-foreground">Gabarito Padrão:</strong>
                <span className="text-muted-foreground ml-2">
                  6 colunas obrigatórias | {OPTIONAL_COLUMNS.length} colunas
                  opcionais | {ALL_COLUMNS.length} colunas totais | Coluna de
                  variação: {VARIATION_COLUMN}
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open("/gabarito-padrao.xlsx", "_blank")}
                className="gap-2"
              >
                <Download className="h-4 w-4" />
                Baixar Gabarito
              </Button>
            </AlertDescription>
          </Alert>

          {/* Step 1: Files Upload */}
          <section className="space-y-4">
            <div className="flex items-center gap-2">
              <Badge variant={currentStep === 1 ? "default" : "secondary"}>
                Passo 1
              </Badge>
              <h2 className="text-xl font-semibold text-foreground">
                Upload das Planilhas
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <FileUpload
                type="custo"
                file={custoFile}
                onFileUpload={setCustoFile}
                onFileRemove={() => {
                  setCustoFile(null);
                  setCustoPagesConfig([]);
                }}
                onPagesConfigChange={setCustoPagesConfig}
                initialPagesConfig={custoPagesConfig}
              />
              <FileUpload
                type="venda"
                file={vendaFile}
                onFileUpload={setVendaFile}
                onFileRemove={() => {
                  setVendaFile(null);
                  setVendaPagesConfig([]);
                }}
                onPagesConfigChange={setVendaPagesConfig}
                initialPagesConfig={vendaPagesConfig}
              />
            </div>
          </section>

          {/* Step 2: Column Mapping */}
          {canProceedToStep3 && (
            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge variant={currentStep === 2 ? "default" : "secondary"}>
                    Passo 2
                  </Badge>
                  <h2 className="text-xl font-semibold text-foreground">
                    Mapeamento de Colunas Obrigatórias
                  </h2>
                </div>
                <Badge
                  variant={
                    requiredMappingProgress === 100 ? "default" : "secondary"
                  }
                  className="bg-success"
                >
                  {mappedRequiredColumns.length} / {requiredColumns.length}{" "}
                  obrigatórias
                </Badge>
              </div>
              {mappedRequiredColumns.length < requiredColumns.length && (
                <Alert className="border-warning bg-warning/5">
                  <AlertCircle className="h-4 w-4 text-warning" />
                  <AlertDescription className="text-foreground">
                    <strong>Atenção:</strong> Você precisa mapear todas as{" "}
                    {requiredColumns.length} colunas obrigatórias antes de
                    prosseguir.
                  </AlertDescription>
                </Alert>
              )}
              <ColumnMapper
                gabaritoColumns={requiredColumns}
                custoFile={custoFile}
                vendaFile={vendaFile}
                mappings={columnMappings}
                onMappingChange={setColumnMappings}
              />

              {/* Separadores Builder - Aparece apenas após anexar planilhas */}
              {(custoFile || vendaFile) && (
                <div className="pt-6 border-t border-dashed border-border space-y-4">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">Separadores</Badge>
                    <h3 className="text-lg font-semibold text-foreground">
                      Configuração de Separadores
                    </h3>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Configure separadores para dividir valores em múltiplos itens.
                  </p>
                  <SeparadoresBuilder
                    columnMappings={columnMappings}
                    onChange={(config) => {
                      console.log("Configuração de separadores atualizada:", config);
                    }}
                    onExport={(json) => {
                      console.log("JSON Separadores exportado:", json);
                      // Armazenar o separadores config como objeto parseado
                      const separadoresObj = JSON.parse(json);
                      setSeparadoresConfig(separadoresObj);
                    }}
                  />
                </div>
              )}

              {optionalColumns.length > 0 && (
                <div className="pt-6 border-t border-dashed border-border space-y-3">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">Opcional</Badge>
                    <h3 className="text-lg font-semibold text-foreground">
                      Colunas Adicionais
                    </h3>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Mapeie colunas opcionais para enriquecer o gabarito final.
                    Elas não são obrigatórias, mas ajudam a manter informações
                    de altura, profundidade e comprimento quando disponíveis.
                  </p>
                  <ColumnMapper
                    title="Mapeamento de Colunas Opcionais"
                    gabaritoColumns={optionalColumns}
                    custoFile={custoFile}
                    vendaFile={vendaFile}
                    mappings={columnMappings}
                    onMappingChange={setColumnMappings}
                  />
                </div>
              )}
            </section>
          )}

          {/* Step 3: Merge Configuration */}
          {canProceedToStep4 && custoFile && vendaFile && (
            <section className="space-y-4">
              <div className="flex items-center gap-2">
                <Badge variant={currentStep === 3 ? "default" : "secondary"}>
                  Passo 3
                </Badge>
                <h2 className="text-xl font-semibold text-foreground">
                  Configuração de Merge
                </h2>
              </div>
              <MergeConfig
                custoFile={custoFile}
                vendaFile={vendaFile}
                config={mergeConfig}
                onConfigChange={setMergeConfig}
                columnMappings={columnMappings}
              />
            </section>
          )}

          {/* JSON Output */}
          {generatedConfig && (
            <section className="space-y-4">
              <div className="flex items-center gap-2">
                <Badge variant="default" className="bg-success">
                  Concluído
                </Badge>
                <h2 className="text-xl font-semibold text-foreground">
                  JSON Gerado
                </h2>
              </div>
              <JsonOutput config={generatedConfig} separadoresConfig={separadoresConfig} />
            </section>
          )}
        </div>
      </main>
    </div>
  );
};

export default Index;
