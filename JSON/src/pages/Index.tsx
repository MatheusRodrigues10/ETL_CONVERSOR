import { useState, useEffect, useCallback, useMemo } from "react";
import { FileUpload } from "@/components/FileUpload";
import { ColumnMapper } from "@/components/ColumnMapper";
import { MergeConfig } from "@/components/MergeConfig";
import { JsonOutput } from "@/components/JsonOutput";
import { ConfigRegexBuilder } from "@/components/ConfigRegexBuilder";
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
  const [regexConfig, setRegexConfig] = useState<any>(null);

  // Usar as colunas obrigatórias predefinidas
  const requiredColumns = Array.from(REQUIRED_COLUMNS);
  const allColumns = Array.from(ALL_COLUMNS);
  const optionalColumns = Array.from(OPTIONAL_COLUMNS);

  // Função para processar novas variações
  const handleNovasVariacoes = useCallback(
    (novasVariacoesString: string) => {
      // Separar por vírgula e limpar espaços
      const novasVariacoes = novasVariacoesString
        .split(",")
        .map((v) => v.trim().toUpperCase())
        .filter((v) => v.length > 0);

      if (novasVariacoes.length === 0) {
        return;
      }

      // Aplicar para ambas as planilhas se existirem
      const updatedMappings = [...columnMappings];

      (["custo", "venda"] as const).forEach((sourceFile) => {
        const file = sourceFile === "custo" ? custoFile : vendaFile;
        if (!file) return;

        const existingIndex = updatedMappings.findIndex(
          (m) =>
            m.gabaritoColumn === VARIATION_COLUMN && m.sourceFile === sourceFile
        );

        // Manter o sourceColumn existente (não modificar)
        let existingSourceColumn: string | string[] | "__EMPTY__" = "__EMPTY__";
        if (existingIndex >= 0) {
          const existingMapping = updatedMappings[existingIndex];
          existingSourceColumn = existingMapping.sourceColumn || "__EMPTY__";
        }

        // Combinar novas_variacoes existentes com as novas
        let combinedNovasVariacoes: string[] = [];
        if (
          existingIndex >= 0 &&
          updatedMappings[existingIndex].novas_variacoes
        ) {
          const existingNovas = updatedMappings[existingIndex]
            .novas_variacoes!.split(",")
            .map((v) => v.trim().toUpperCase())
            .filter((v) => v.length > 0);
          combinedNovasVariacoes = [...existingNovas];
        }

        // Adicionar apenas as novas variações que não existem
        novasVariacoes.forEach((nova) => {
          if (!combinedNovasVariacoes.includes(nova)) {
            combinedNovasVariacoes.push(nova);
          }
        });

        // Criar ou atualizar mapeamento
        // IMPORTANTE: sourceColumn não é modificado, apenas novas_variacoes
        const newMapping: ColumnMapping = {
          gabaritoColumn: VARIATION_COLUMN,
          sourceColumn: existingSourceColumn, // Mantém o que já existe
          sourceFile,
          novas_variacoes: combinedNovasVariacoes.join(","),
        };

        if (existingIndex >= 0) {
          updatedMappings[existingIndex] = newMapping;
        } else {
          updatedMappings.push(newMapping);
        }
      });

      setColumnMappings(updatedMappings);
    },
    [columnMappings, custoFile, vendaFile]
  );

  // Função para remover uma variação individual
  const handleRemoverVariacaoIndividual = useCallback(
    (variacaoParaRemover: string) => {
      const updatedMappings = columnMappings.map((mapping) => {
        // Se é a coluna COR e tem novas_variacoes
        if (
          mapping.gabaritoColumn === VARIATION_COLUMN &&
          mapping.novas_variacoes
        ) {
          const novasVariacoes = mapping.novas_variacoes
            .split(",")
            .map((v) => v.trim().toUpperCase())
            .filter((v) => v.length > 0);

          // Remover a variação específica da lista de novas_variacoes
          const novasVariacoesAtualizadas = novasVariacoes.filter(
            (v) => v !== variacaoParaRemover.toUpperCase()
          );

          // IMPORTANTE: Não modificar sourceColumn, apenas novas_variacoes
          // Se ainda há novas variações, manter o campo, senão remover
          if (novasVariacoesAtualizadas.length > 0) {
            return {
              ...mapping,
              novas_variacoes: novasVariacoesAtualizadas.join(","),
            };
          } else {
            return {
              ...mapping,
              novas_variacoes: undefined,
            };
          }
        }
        return mapping;
      });

      setColumnMappings(updatedMappings);
    },
    [columnMappings]
  );

  // Função para limpar todas as variações adicionadas via novas_variacoes
  const handleLimparNovasVariacoes = useCallback(() => {
    const updatedMappings = columnMappings.map((mapping) => {
      // Se é a coluna COR e tem novas_variacoes, remover apenas o campo novas_variacoes
      if (
        mapping.gabaritoColumn === VARIATION_COLUMN &&
        mapping.novas_variacoes
      ) {
        // IMPORTANTE: Não modificar sourceColumn, apenas remover novas_variacoes
        return {
          ...mapping,
          novas_variacoes: undefined,
        };
      }
      return mapping;
    });

    setColumnMappings(updatedMappings);
  }, [columnMappings]);

  // Obter todas as variações adicionadas via novas_variacoes (únicas)
  const novasVariacoesAdicionadas = useMemo(() => {
    const todasVariacoes = new Set<string>();
    columnMappings.forEach((mapping) => {
      if (
        mapping.gabaritoColumn === VARIATION_COLUMN &&
        mapping.novas_variacoes
      ) {
        const variacoes = mapping.novas_variacoes
          .split(",")
          .map((v) => v.trim().toUpperCase())
          .filter((v) => v.length > 0);
        variacoes.forEach((v) => todasVariacoes.add(v));
      }
    });
    return Array.from(todasVariacoes);
  }, [columnMappings]);

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
      // Verificar se é uma coluna obrigatória
      if (!REQUIRED_COLUMNS.includes(gabaritoColumn as any)) return;

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
    (mappedRequiredColumns.length / REQUIRED_COLUMNS.length) * 100;

  const canProceedToStep2 = true; // Sempre pode prosseguir pois temos o gabarito padrão
  const canProceedToStep3 = custoFile !== null || vendaFile !== null;
  const canProceedToStep4 =
    canProceedToStep3 &&
    mappedRequiredColumns.length === REQUIRED_COLUMNS.length;
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
        columnMapping: finalColumnMappings,
        mergeConfig: mergeConfig || undefined,
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
      completed: mappedRequiredColumns.length === REQUIRED_COLUMNS.length,
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
                  {REQUIRED_COLUMNS.length} colunas obrigatórias |{" "}
                  {OPTIONAL_COLUMNS.length} colunas opcionais |{" "}
                  {ALL_COLUMNS.length} colunas totais | Coluna de variação:{" "}
                  {VARIATION_COLUMN}
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
                  {mappedRequiredColumns.length} / {REQUIRED_COLUMNS.length}{" "}
                  obrigatórias
                </Badge>
              </div>
              {mappedRequiredColumns.length < REQUIRED_COLUMNS.length && (
                <Alert className="border-warning bg-warning/5">
                  <AlertCircle className="h-4 w-4 text-warning" />
                  <AlertDescription className="text-foreground">
                    <strong>Atenção:</strong> Você precisa mapear todas as{" "}
                    {REQUIRED_COLUMNS.length} colunas obrigatórias antes de
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

              {/* Campo opcional para novas variações */}
              {(custoFile || vendaFile) && (
                <Card className="p-4 border-dashed">
                  <div className="space-y-3">
                    <div>
                      <Label className="text-sm font-medium text-foreground">
                        Novas variações opcionais (separadas por vírgula)
                      </Label>
                      <p className="text-xs text-muted-foreground mt-1">
                        Adicione novas variações que serão combinadas com as
                        selecionadas na coluna COR acima.
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Ex: A6,A2,A1 (opcional)"
                        onKeyDown={(e) => {
                          const target = e.target as HTMLInputElement;
                          if (e.key === "Enter" && target.value.trim()) {
                            handleNovasVariacoes(target.value.trim());
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
                          const novasVariacoes = input?.value.trim() || "";
                          if (novasVariacoes) {
                            handleNovasVariacoes(novasVariacoes);
                            input.value = "";
                          }
                        }}
                      >
                        Adicionar
                      </Button>
                      {novasVariacoesAdicionadas.length > 0 && (
                        <Button
                          type="button"
                          variant="outline"
                          onClick={handleLimparNovasVariacoes}
                        >
                          Limpar Todas
                        </Button>
                      )}
                    </div>
                    {novasVariacoesAdicionadas.length > 0 && (
                      <div className="mt-3 pt-3 border-t">
                        <Label className="text-xs text-muted-foreground mb-2 block">
                          Variações adicionadas (
                          {novasVariacoesAdicionadas.length}):
                        </Label>
                        <div className="flex flex-wrap gap-2">
                          {novasVariacoesAdicionadas.map((variacao) => (
                            <Badge
                              key={variacao}
                              variant="secondary"
                              className="flex items-center gap-1 pr-1"
                            >
                              <span>{variacao}</span>
                              <button
                                type="button"
                                onClick={() =>
                                  handleRemoverVariacaoIndividual(variacao)
                                }
                                className="ml-1 rounded-full hover:bg-destructive/20 p-0.5 transition-colors"
                                title={`Remover ${variacao}`}
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </Card>
              )}

              {/* Config Regex Builder - Aparece apenas após anexar planilhas */}
              {(custoFile || vendaFile) && (
                <div className="pt-6 border-t border-dashed border-border space-y-4">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">Regex Builder</Badge>
                    <h3 className="text-lg font-semibold text-foreground">
                      Construtor de Configuração Regex
                    </h3>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Configure regras avançadas de regex para processamento dinâmico das linhas.
                  </p>
                  <ConfigRegexBuilder
                    onChange={(configs) => {
                      console.log("Configurações regex atualizadas:", configs);
                    }}
                    onExport={(json) => {
                      console.log("JSON Regex exportado:", json);
                      // Armazenar o regex config como um array parseado
                      const regexArray = JSON.parse(json);
                      setRegexConfig(regexArray);
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
              <JsonOutput config={generatedConfig} regexConfig={regexConfig} />
            </section>
          )}
        </div>
      </main>
    </div>
  );
};

export default Index;
