import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { Plus, Trash2, X } from "lucide-react";
import { useState, useCallback, useMemo } from "react";
import { ColumnMapping } from "@/types/spreadsheet";

interface SeparadorConfig {
  coluna: string;
  valorOriginal: string;
  palavras: string;
}

interface SeparadoresBuilderProps {
  value?: { separadores: SeparadorConfig[] };
  onChange?: (config: { separadores: SeparadorConfig[] }) => void;
  onExport?: (json: string) => void;
  columnMappings?: ColumnMapping[]; // Mapeamentos de colunas do gabarito
}

interface SeparadorBlockProps {
  config: SeparadorConfig;
  onUpdate: (config: SeparadorConfig) => void;
  onRemove: () => void;
  index: number;
  gabaritoColumns: string[];
}

const SeparadorBlock = ({
  config,
  onUpdate,
  onRemove,
  index,
  gabaritoColumns,
}: SeparadorBlockProps) => {
  const handleColunaChange = (coluna: string) => {
    onUpdate({ ...config, coluna });
  };

  const handleValorChange = (valorOriginal: string) => {
    onUpdate({ ...config, valorOriginal });
  };

  const handlePalavrasChange = (palavras: string) => {
    onUpdate({ ...config, palavras });
  };

  // Dividir palavras por vírgula e limpar espaços
  const itensSeparados = useMemo(() => {
    return config.palavras
      .split(",")
      .map((item) => item.trim())
      .filter((item) => item.length > 0);
  }, [config.palavras]);

  // Remover um item específico da lista
  const handleRemoveItem = (itemToRemove: string) => {
    const novosItens = itensSeparados.filter((item) => item !== itemToRemove);
    const novasPalavras = novosItens.join(", ");
    onUpdate({ ...config, palavras: novasPalavras });
  };

  return (
    <Card className="border-2">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Bloco {index + 1}</CardTitle>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onRemove}
            title="Remover bloco"
          >
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label htmlFor={`coluna-${index}`}>COLUNA</Label>
            <Select value={config.coluna} onValueChange={handleColunaChange}>
              <SelectTrigger id={`coluna-${index}`}>
                <SelectValue placeholder="Selecione a coluna..." />
              </SelectTrigger>
              <SelectContent>
                {gabaritoColumns.map((col) => (
                  <SelectItem key={col} value={col}>
                    {col}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor={`valor-${index}`}>VALOR</Label>
            <Input
              id={`valor-${index}`}
              placeholder="Ex: MADEIRA E FERRO"
              value={config.valorOriginal}
              onChange={(e) => handleValorChange(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor={`palavras-${index}`}>PALAVRAS</Label>
            <Input
              id={`palavras-${index}`}
              placeholder="Ex: MADEIRA, FERRO"
              value={config.palavras}
              onChange={(e) => handlePalavrasChange(e.target.value)}
            />
            {itensSeparados.length > 0 && (
              <div className="space-y-2 mt-2">
                <p className="text-xs text-muted-foreground">
                  Itens detectados:
                </p>
                <div className="flex flex-wrap gap-2">
                  {itensSeparados.map((item, itemIndex) => (
                    <span
                      key={itemIndex}
                      className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary"
                    >
                      {item}
                      <button
                        type="button"
                        onClick={() => handleRemoveItem(item)}
                        className="ml-1 inline-flex h-4 w-4 items-center justify-center rounded-full hover:bg-primary/20 transition-colors"
                        title={`Remover ${item}`}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export const SeparadoresBuilder = ({
  value,
  onChange,
  onExport,
  columnMappings = [],
}: SeparadoresBuilderProps) => {
  const { toast } = useToast();
  const [separadores, setSeparadores] = useState<SeparadorConfig[]>(
    value?.separadores || []
  );

  // Obter colunas do gabarito que foram mapeadas e que têm dados (não estão vazias)
  const mappedGabaritoColumns = useMemo(() => {
    const columns = new Set<string>();
    columnMappings.forEach((mapping) => {
      // Verificar se a coluna tem dados (não é __EMPTY__)
      let hasData = false;

      if (
        mapping.sourceColumn === "__EMPTY__" ||
        mapping.sourceColumn === null ||
        mapping.sourceColumn === undefined
      ) {
        hasData = false;
      } else if (Array.isArray(mapping.sourceColumn)) {
        // Se for array, verificar se tem pelo menos um elemento não vazio
        hasData =
          mapping.sourceColumn.length > 0 &&
          mapping.sourceColumn.some(
            (col) => col && col.trim() !== "" && col !== "__EMPTY__"
          );
      } else {
        // Se for string, verificar se não está vazia
        hasData =
          String(mapping.sourceColumn).trim() !== "" &&
          mapping.sourceColumn !== "__EMPTY__";
      }

      if (hasData) {
        columns.add(mapping.gabaritoColumn);
      }
    });
    return Array.from(columns).sort();
  }, [columnMappings]);

  const handleSeparadorUpdate = useCallback(
    (index: number, updated: SeparadorConfig) => {
      const newSeparadores = [...separadores];
      newSeparadores[index] = updated;
      setSeparadores(newSeparadores);
      onChange?.({ separadores: newSeparadores });
    },
    [separadores, onChange]
  );

  const handleSeparadorRemove = useCallback(
    (index: number) => {
      const newSeparadores = separadores.filter((_, i) => i !== index);
      setSeparadores(newSeparadores);
      onChange?.({ separadores: newSeparadores });
    },
    [separadores, onChange]
  );

  const handleAddBlock = useCallback(() => {
    const novoBloco: SeparadorConfig = {
      coluna: "",
      valorOriginal: "",
      palavras: "",
    };
    const newSeparadores = [...separadores, novoBloco];
    setSeparadores(newSeparadores);
    onChange?.({ separadores: newSeparadores });
  }, [separadores, onChange]);

  const handleExport = useCallback(() => {
    // Filtrar apenas blocos válidos (com pelo menos coluna e palavras preenchidas)
    const separadoresValidos = separadores
      .filter((s) => s.coluna.trim().length > 0 && s.palavras.trim().length > 0)
      .map((s) => {
        // Dividir palavras por vírgula e limpar espaços
        const itensSeparados = s.palavras
          .split(",")
          .map((item) => item.trim())
          .filter((item) => item.length > 0);

        return {
          coluna: s.coluna.trim(),
          valorOriginal: s.valorOriginal.trim(),
          itensSeparados,
        };
      });

    if (separadoresValidos.length === 0) {
      toast({
        title: "Atenção",
        description:
          "Adicione pelo menos um bloco válido (COLUNA e PALAVRAS são obrigatórios)",
        variant: "destructive",
      });
      return;
    }

    const json = {
      separadores: separadoresValidos,
    };

    const jsonString = JSON.stringify(json, null, 2);
    onExport?.(jsonString);

    // Copiar para clipboard
    navigator.clipboard.writeText(jsonString).catch(() => {
      // Ignorar erro de clipboard
    });

    toast({
      title: "✓ JSON gerado com sucesso!",
      description: `${separadoresValidos.length} separador(es) configurado(s)`,
      variant: "default",
    });
  }, [separadores, onExport, toast]);

  const isValid = separadores.some(
    (s) => s.coluna.trim().length > 0 && s.palavras.trim().length > 0
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Configuração de Separadores</h2>
        <div className="flex gap-2">
          <Button onClick={handleAddBlock} variant="outline">
            <Plus className="h-4 w-4 mr-2" />
            Adicionar nova configuração
          </Button>
          {isValid && separadores.length > 0 && (
            <Button onClick={handleExport}>Adicionar a configuração</Button>
          )}
        </div>
      </div>

      {!isValid && separadores.length > 0 && (
        <div className="rounded-md border border-yellow-500 bg-yellow-50 p-4 text-sm text-yellow-800">
          <strong>Atenção:</strong> Preencha pelo menos COLUNA e PALAVRAS em um
          bloco antes de gerar o JSON.
        </div>
      )}

      {separadores.length === 0 && (
        <div className="rounded-md border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800 text-center">
          <p>
            Nenhum bloco adicionado. Clique em{" "}
            <strong>"Adicionar nova configuração"</strong> para começar.
          </p>
        </div>
      )}

      <div className="space-y-4">
        {separadores.map((separador, index) => (
          <SeparadorBlock
            key={index}
            config={separador}
            onUpdate={(updated) => handleSeparadorUpdate(index, updated)}
            onRemove={() => handleSeparadorRemove(index)}
            index={index}
            gabaritoColumns={mappedGabaritoColumns}
          />
        ))}
      </div>
    </div>
  );
};
