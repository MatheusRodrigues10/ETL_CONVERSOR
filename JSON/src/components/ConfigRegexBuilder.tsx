import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { AplicarRegexTipo, ConfiguracaoRegex, LinhaParadaTipo } from "@/types/regexConfig";
import {
  ChevronDown,
  ChevronRight,
  Copy,
  Plus,
  Trash2
} from "lucide-react";
import { useCallback, useState } from "react";

interface ConfigRegexBuilderProps {
  value?: ConfiguracaoRegex[];
  onChange?: (config: ConfiguracaoRegex[]) => void;
  onExport?: (json: string) => void;
}

interface ConfiguracaoCardProps {
  config: ConfiguracaoRegex;
  onUpdate: (config: ConfiguracaoRegex) => void;
  onRemove: () => void;
  onDuplicate: () => void;
  level?: number;
  isRoot?: boolean;
}

interface LinhaParadaCardProps {
  linhaParada: ConfiguracaoRegex["linhaParada"];
  onUpdate: (linhaParada: ConfiguracaoRegex["linhaParada"]) => void;
  level?: number;
}

/**
 * Componente para construir uma linha de parada
 */
const LinhaParadaCard = ({ linhaParada, onUpdate, level = 0 }: LinhaParadaCardProps) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [regexInputValue, setRegexInputValue] = useState(linhaParada?.regexLinhaParada || "");

  if (!linhaParada) return null;

  const handleTipoChange = (tipo: LinhaParadaTipo) => {
    const updated: ConfiguracaoRegex["linhaParada"] = {
      ...linhaParada,
      tipo,
      // Limpar campos que não são mais necessários
      regexLinhaParada: tipo === "parar_total" ? undefined : linhaParada.regexLinhaParada,
      novaConfiguracaoAbaixo: tipo !== "ignorar_e_continuar" ? undefined : linhaParada.novaConfiguracaoAbaixo,
    };
    onUpdate(updated);
  };

  const handleNomeChange = (nome: string) => {
    onUpdate({ ...linhaParada, nome });
  };

  const handleRegexChange = (regex: string) => {
    // Separar por vírgula para detectar variações
    const variacoes = regex
      .split(/[,\n]/)
      .map((v) => v.trim())
      .filter((v) => v.length > 0);

    // Manter o valor do input enquanto digita
    setRegexInputValue(regex);

    // Armazenar apenas a string original no estado da parada
    onUpdate({ ...linhaParada, regexLinhaParada: regex });
  };

  const handleNovaConfiguracaoChange = (novaConfig: ConfiguracaoRegex) => {
    onUpdate({ ...linhaParada, novaConfiguracaoAbaixo: novaConfig });
  };

  const handleAdicionarNovaConfiguracao = () => {
    const novaConfig: ConfiguracaoRegex = {
      inicio: "",
      variacoes: [],
      regexAtivado: false,
      aplicarRegex: "inicial",
    };
    onUpdate({ ...linhaParada, novaConfiguracaoAbaixo: novaConfig });
  };

  return (
    <Card className={`mt-4 ${level > 0 ? "ml-6 border-l-2 border-l-primary/30" : ""}`}>
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CollapsibleTrigger asChild>
              <div className="flex items-center gap-2 cursor-pointer flex-1">
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
                <CardTitle className="text-lg">Linha de Parada</CardTitle>
              </div>
            </CollapsibleTrigger>
          </div>
        </CardHeader>

        <CollapsibleContent>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="nome-parada">Nome da linha de parada *</Label>
              <Input
                id="nome-parada"
                placeholder="Digite o nome da linha de parada..."
                value={linhaParada.nome}
                onChange={(e) => handleNomeChange(e.target.value)}
              />
            </div>

            <div className="space-y-3">
              <Label>O que fazer ao encontrar a linha de parada? *</Label>
              <RadioGroup
                value={linhaParada.tipo}
                onValueChange={(value) => handleTipoChange(value as LinhaParadaTipo)}
              >
                <div className="flex items-start space-x-2 space-y-0 rounded-md border p-4">
                  <RadioGroupItem value="parar_total" id="parar-total" className="mt-1" />
                  <div className="flex-1 space-y-1">
                    <Label htmlFor="parar-total" className="font-normal cursor-pointer">
                      <strong>OPÇÃO A — Parar totalmente</strong>
                    </Label>
                    <p className="text-sm text-muted-foreground">
                      Parar totalmente ao encontrar esta linha. Nenhuma linha, incluindo esta, recebe regex.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-2 space-y-0 rounded-md border p-4">
                  <RadioGroupItem value="aplicar_e_parar" id="aplicar-parar" className="mt-1" />
                  <div className="flex-1 space-y-1">
                    <Label htmlFor="aplicar-parar" className="font-normal cursor-pointer">
                      <strong>OPÇÃO B — Aplicar regex nesta linha e parar</strong>
                    </Label>
                    <p className="text-sm text-muted-foreground">
                      A linha de parada recebe um regex próprio, mas a lógica encerra abaixo dela.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-2 space-y-0 rounded-md border p-4">
                  <RadioGroupItem value="ignorar_e_continuar" id="ignorar-continuar" className="mt-1" />
                  <div className="flex-1 space-y-1">
                    <Label htmlFor="ignorar-continuar" className="font-normal cursor-pointer">
                      <strong>OPÇÃO C — Ignorar a linha de parada, aplicar um regex próprio nela e iniciar nova configuração abaixo</strong>
                    </Label>
                    <p className="text-sm text-muted-foreground">
                      A lógica principal para nesta linha; esta linha recebe seu próprio regex; e uma nova configuração começa abaixo usando um novo regex.
                    </p>
                  </div>
                </div>
              </RadioGroup>
            </div>

            {/* Campo de regex para opção B e C */}
            {(linhaParada.tipo === "aplicar_e_parar" || linhaParada.tipo === "ignorar_e_continuar") && (
              <div className="space-y-2">
                <Label htmlFor="regex-parada">
                  {linhaParada.tipo === "aplicar_e_parar"
                    ? "Regex específico para esta linha de parada"
                    : "Regex da linha de parada"}
                </Label>
                <Input
                  id="regex-parada"
                  placeholder="Exemplo: A6, A2, A1"
                  value={regexInputValue}
                  onChange={(e) => handleRegexChange(e.target.value)}
                  type="text"
                />
                {regexInputValue.trim().length > 0 && (
                  <div className="space-y-2">
                    <p className="text-xs text-muted-foreground">
                      Padrões detectados:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {regexInputValue
                        .split(/[,\n]/)
                        .map((v) => v.trim())
                        .filter((v) => v.length > 0)
                        .map((padrao, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-700"
                          >
                            {padrao}
                            <button
                              type="button"
                              onClick={() => {
                                const padroes = regexInputValue
                                  .split(/[,\n]/)
                                  .map((v) => v.trim())
                                  .filter((v) => v.length > 0);
                                const novosPadroes = padroes.filter((_, i) => i !== idx);
                                const novoRegex = novosPadroes.join(", ");
                                handleRegexChange(novoRegex);
                              }}
                              className="ml-1 inline-flex h-4 w-4 items-center justify-center rounded-full hover:bg-blue-200"
                            >
                              ×
                            </button>
                          </span>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Nova configuração para opção C */}
            {linhaParada.tipo === "ignorar_e_continuar" && (
              <div className="mt-4 pt-4 border-t">
                {linhaParada.novaConfiguracaoAbaixo ? (
                  <ConfiguracaoCard
                    config={linhaParada.novaConfiguracaoAbaixo}
                    onUpdate={handleNovaConfiguracaoChange}
                    onRemove={() => onUpdate({ ...linhaParada, novaConfiguracaoAbaixo: undefined })}
                    onDuplicate={() => {
                      const duplicated = JSON.parse(JSON.stringify(linhaParada.novaConfiguracaoAbaixo));
                      onUpdate({ ...linhaParada, novaConfiguracaoAbaixo: duplicated });
                    }}
                    level={level + 1}
                    isRoot={false}
                  />
                ) : (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleAdicionarNovaConfiguracao}
                    className="w-full"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Adicionar Nova Configuração Abaixo
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
};

/**
 * Componente para construir uma configuração de regex
 */
const ConfiguracaoCard = ({
  config,
  onUpdate,
  onRemove,
  onDuplicate,
  level = 0,
  isRoot = true,
}: ConfiguracaoCardProps) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [variacoesInputValue, setVariacoesInputValue] = useState(config.variacoes.join(", "));

  const handleInicioChange = (inicio: string) => {
    onUpdate({ ...config, inicio });
  };

  const handleVariacoesChange = (variacoesStr: string) => {
    // Manter o valor do input enquanto digita
    setVariacoesInputValue(variacoesStr);

    // Suportar tanto separação por vírgula quanto por quebra de linha
    const variacoes = variacoesStr
      .split(/[,\n]/)
      .map((v) => v.trim())
      .filter((v) => v.length > 0);

    onUpdate({ ...config, variacoes });
  }; const handleRegexAtivadoChange = (ativado: boolean) => {
    const updated: ConfiguracaoRegex = {
      ...config,
      regexAtivado: ativado,
      // Se desativar regex, resetar aplicarRegex
      aplicarRegex: ativado ? config.aplicarRegex : "inicial",
    };
    onUpdate(updated);
  };

  const handleAplicarRegexChange = (aplicarRegex: AplicarRegexTipo) => {
    const updated: ConfiguracaoRegex = {
      ...config,
      aplicarRegex,
      // Se mudar para "inicial", remover linha de parada
      linhaParada: aplicarRegex === "inicial" ? undefined : config.linhaParada,
    };
    onUpdate(updated);
  };

  const handleLinhaParadaChange = (linhaParada: ConfiguracaoRegex["linhaParada"]) => {
    onUpdate({ ...config, linhaParada });
  };

  const handleAdicionarLinhaParada = () => {
    const novaLinhaParada = {
      nome: "",
      tipo: "parar_total" as LinhaParadaTipo,
    };
    onUpdate({ ...config, linhaParada: novaLinhaParada });
  };

  const variacoesStr = variacoesInputValue;

  return (
    <Card className={level > 0 ? "ml-6 border-l-2 border-l-primary/30" : ""}>
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between gap-4">
            <CollapsibleTrigger asChild>
              <button className="flex items-center gap-2 cursor-pointer text-left flex-1 hover:opacity-70">
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4 flex-shrink-0" />
                ) : (
                  <ChevronRight className="h-4 w-4 flex-shrink-0" />
                )}
                <CardTitle className="text-lg">
                  {isRoot ? "Configuração Inicial" : "Nova Configuração Abaixo"}
                </CardTitle>
              </button>
            </CollapsibleTrigger>
            <div className="flex items-center gap-1 flex-shrink-0">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={onDuplicate}
                title="Duplicar configuração"
              >
                <Copy className="h-4 w-4" />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={onRemove}
                title="Remover configuração"
              >
                <Trash2 className="h-4 w-4 text-black" />
              </Button>
            </div>
          </div>
        </CardHeader>

        <CollapsibleContent>
          <CardContent className="space-y-4">
            {/* Nome da linha inicial */}
            <div className="space-y-2">
              <Label htmlFor="inicio">Nome da linha inicial *</Label>
              <Input
                id="inicio"
                placeholder="Digite o nome da linha inicial…"
                value={config.inicio}
                onChange={(e) => handleInicioChange(e.target.value)}
              />
            </div>

            {/* Variações iniciais */}
            <div className="space-y-2">
              <Label htmlFor="variacoes">Variações iniciais *</Label>
              <Input
                id="variacoes"
                placeholder="Exemplo: A6, A2, A1"
                value={variacoesStr}
                onChange={(e) => handleVariacoesChange(e.target.value)}
                type="text"
              />
              {config.variacoes.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">
                    {config.variacoes.length} variação(ões) detectada(s):
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {config.variacoes.map((variacao, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary"
                      >
                        {variacao}
                        <button
                          type="button"
                          onClick={() => {
                            const novasVariacoes = config.variacoes.filter((_, i) => i !== idx);
                            onUpdate({ ...config, variacoes: novasVariacoes });
                          }}
                          className="ml-1 inline-flex h-4 w-4 items-center justify-center rounded-full hover:bg-primary/20"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Ativar regex */}
            <div className="flex items-center justify-between space-x-2 rounded-md border p-4">
              <div className="space-y-0.5 flex-1">
                <Label htmlFor="regex-ativado">Ativar regex?</Label>
                <p className="text-sm text-muted-foreground">
                  Habilite para aplicar regras de regex nesta configuração
                </p>
              </div>
              <Switch
                id="regex-ativado"
                checked={config.regexAtivado}
                onCheckedChange={handleRegexAtivadoChange}
              />
            </div>

            {/* Como aplicar o regex */}
            {config.regexAtivado && (
              <div className="space-y-3">
                <Label>Como aplicar o regex? *</Label>
                <RadioGroup
                  value={config.aplicarRegex}
                  onValueChange={(value) => handleAplicarRegexChange(value as AplicarRegexTipo)}
                >
                  <div className="flex items-start space-x-2 space-y-0 rounded-md border p-4">
                    <RadioGroupItem value="inicial" id="aplicar-inicial" className="mt-1" />
                    <div className="flex-1 space-y-1">
                      <Label htmlFor="aplicar-inicial" className="font-normal cursor-pointer">
                        Aplicar regex apenas nesta linha inicial
                      </Label>
                    </div>
                  </div>

                  <div className="flex items-start space-x-2 space-y-0 rounded-md border p-4">
                    <RadioGroupItem value="abaixo" id="aplicar-abaixo" className="mt-1" />
                    <div className="flex-1 space-y-1">
                      <Label htmlFor="aplicar-abaixo" className="font-normal cursor-pointer">
                        Aplicar regex em todas as linhas abaixo (até o evento de parada)
                      </Label>
                    </div>
                  </div>
                </RadioGroup>
              </div>
            )}

            {/* Linha de parada - só aparece se aplicarRegex === "abaixo" */}
            {config.regexAtivado && config.aplicarRegex === "abaixo" && (
              <div className="mt-4 pt-4 border-t">
                {config.linhaParada ? (
                  <LinhaParadaCard
                    linhaParada={config.linhaParada}
                    onUpdate={handleLinhaParadaChange}
                    level={level}
                  />
                ) : (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleAdicionarLinhaParada}
                    className="w-full"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Adicionar Linha de Parada
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
};

/**
 * Componente principal ConfigRegexBuilder
 */
export const ConfigRegexBuilder = ({ value, onChange, onExport }: ConfigRegexBuilderProps) => {
  const { toast } = useToast();
  const [configuracoes, setConfiguracoes] = useState<ConfiguracaoRegex[]>(
    value || []
  );
  const [jsonFinal, setJsonFinal] = useState<ConfiguracaoRegex[]>([]);

  const handleConfigUpdate = useCallback(
    (index: number, updatedConfig: ConfiguracaoRegex) => {
      const newConfigs = [...configuracoes];
      newConfigs[index] = updatedConfig;
      setConfiguracoes(newConfigs);
      onChange?.(newConfigs);
    },
    [configuracoes, onChange]
  );

  const handleConfigRemove = useCallback(
    (index: number) => {
      const newConfigs = configuracoes.filter((_, i) => i !== index);
      setConfiguracoes(newConfigs);
      onChange?.(newConfigs);
    },
    [configuracoes, onChange]
  );

  const handleConfigDuplicate = useCallback(
    (index: number) => {
      const duplicated = JSON.parse(JSON.stringify(configuracoes[index]));
      const newConfigs = [...configuracoes, duplicated];
      setConfiguracoes(newConfigs);
      onChange?.(newConfigs);
    },
    [configuracoes, onChange]
  );

  const handleAddConfig = useCallback(() => {
    const novaConfig: ConfiguracaoRegex = {
      inicio: "",
      variacoes: [],
      regexAtivado: false,
      aplicarRegex: "inicial",
    };
    const newConfigs = [...configuracoes, novaConfig];
    setConfiguracoes(newConfigs);
    onChange?.(newConfigs);
  }, [configuracoes, onChange]);

  const handleExport = useCallback(() => {
    // Limpar campos vazios e undefined antes de exportar
    const cleanConfig = (config: ConfiguracaoRegex): any => {
      const cleaned: any = {
        inicio: config.inicio.trim(),
        variacoes: config.variacoes.filter((v) => v.trim().length > 0).map((v) => v.trim()),
        regexAtivado: config.regexAtivado,
        aplicarRegex: config.aplicarRegex,
      };

      if (config.linhaParada && config.linhaParada.nome.trim().length > 0) {
        const cleanedParada: any = {
          nome: config.linhaParada.nome.trim(),
          tipo: config.linhaParada.tipo,
        };

        // Adicionar regexLinhaParada apenas se existir e não estiver vazio
        if (
          config.linhaParada.regexLinhaParada &&
          config.linhaParada.regexLinhaParada.trim().length > 0 &&
          (config.linhaParada.tipo === "aplicar_e_parar" || config.linhaParada.tipo === "ignorar_e_continuar")
        ) {
          cleanedParada.regexLinhaParada = config.linhaParada.regexLinhaParada.trim();
        }

        // Adicionar novaConfiguracaoAbaixo apenas se existir e for válida
        if (config.linhaParada.novaConfiguracaoAbaixo && config.linhaParada.tipo === "ignorar_e_continuar") {
          const subConfig = cleanConfig(config.linhaParada.novaConfiguracaoAbaixo);
          if (subConfig.inicio && subConfig.variacoes.length > 0) {
            cleanedParada.novaConfiguracaoAbaixo = subConfig;
          }
        }

        cleaned.linhaParada = cleanedParada;
      }

      return cleaned;
    };

    // Filtrar apenas as configurações válidas
    const configsValidas = configuracoes
      .filter((config) => config.inicio.trim().length > 0 && config.variacoes.some((v) => v.trim().length > 0))
      .map(cleanConfig);

    // Adicionar ao JSON final
    const novoJsonFinal = [...jsonFinal, ...configsValidas];
    setJsonFinal(novoJsonFinal);

    // Exportar o JSON final completo
    const json = JSON.stringify(novoJsonFinal, null, 2);
    onExport?.(json);

    // Copiar para clipboard
    navigator.clipboard.writeText(json).catch(() => {
      // Ignorar erro de clipboard
    });

    // Mostrar toast de sucesso
    toast({
      title: "✓ Config adicionada com sucesso!",
      description: `${configsValidas.length} configuração(ões) adicionada(s) ao JSON final. Total: ${novoJsonFinal.length}`,
      variant: "default",
    });

    // Limpar as configurações atuais após exportar
    setConfiguracoes([]);
  }, [configuracoes, jsonFinal, onExport, toast]);

  // Validação básica - regex é opcional
  const isValid = configuracoes.every((config) => {
    // Obrigatório: nome e variações
    if (!config.inicio || config.inicio.trim().length === 0) return false;
    if (config.variacoes.length === 0) return false;

    // Se regex está ativado, validar campos de regex
    if (config.regexAtivado && config.aplicarRegex === "abaixo" && config.linhaParada) {
      if (!config.linhaParada.nome || config.linhaParada.nome.trim().length === 0) return false;
      if (config.linhaParada.tipo === "aplicar_e_parar" && !config.linhaParada.regexLinhaParada) return false;
      if (config.linhaParada.tipo === "ignorar_e_continuar") {
        if (!config.linhaParada.regexLinhaParada) return false;
        if (config.linhaParada.novaConfiguracaoAbaixo) {
          // Validação recursiva
          const subConfig = config.linhaParada.novaConfiguracaoAbaixo;
          if (!subConfig.inicio || subConfig.inicio.trim().length === 0) return false;
          if (subConfig.variacoes.length === 0) return false;
        }
      }
    }
    return true;
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Construtor de Configuração Regex</h2>
        <div className="flex gap-2">
          <Button onClick={handleAddConfig} variant="outline">
            <Plus className="h-4 w-4 mr-2" />
            Adicionar Configuração
          </Button>
          {isValid && configuracoes.length > 0 && (
            <Button onClick={handleExport}>
              Exportar
            </Button>
          )}
        </div>
      </div>

      {!isValid && configuracoes.length > 0 && (
        <div className="rounded-md border border-yellow-500 bg-yellow-50 p-4 text-sm text-yellow-800">
          <strong>Atenção:</strong> Preencha todos os campos obrigatórios marcados com * antes de exportar a config (Nome da linha inicial e Variações iniciais são obrigatórios).
        </div>
      )}

      {configuracoes.length === 0 && (
        <div className="rounded-md border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800 text-center">
          <p>Nenhuma configuração adicionada. Clique em <strong>"Adicionar Configuração"</strong> para começar.</p>
        </div>
      )}

      <div className="space-y-4">
        {configuracoes.map((config, index) => (
          <ConfiguracaoCard
            key={index}
            config={config}
            onUpdate={(updated) => handleConfigUpdate(index, updated)}
            onRemove={() => handleConfigRemove(index)}
            onDuplicate={() => handleConfigDuplicate(index)}
            level={0}
            isRoot={true}
          />
        ))}
      </div>
    </div>
  );
};

