import { useMemo } from 'react';
import { Card } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { MergeConfig as MergeConfigType, UploadedFile, ColumnMapping } from '@/types/spreadsheet';
import { GitMerge } from 'lucide-react';

interface MergeConfigProps {
  custoFile: UploadedFile | null;
  vendaFile: UploadedFile | null;
  config: MergeConfigType | null;
  onConfigChange: (config: MergeConfigType) => void;
  columnMappings: ColumnMapping[]; // Mapeamentos de colunas do gabarito
}

export const MergeConfig = ({ custoFile, vendaFile, config, onConfigChange, columnMappings }: MergeConfigProps) => {
  // Obter colunas do gabarito que foram mapeadas e que têm dados (não estão vazias)
  const mappedGabaritoColumns = useMemo(() => {
    const columns = new Set<string>();
    columnMappings.forEach((mapping) => {
      // Verificar se a coluna tem dados (não é __EMPTY__)
      let hasData = false;
      
      if (mapping.sourceColumn === "__EMPTY__" || mapping.sourceColumn === null || mapping.sourceColumn === undefined) {
        hasData = false;
      } else if (Array.isArray(mapping.sourceColumn)) {
        // Se for array, verificar se tem pelo menos um elemento não vazio
        hasData = mapping.sourceColumn.length > 0 && 
                  mapping.sourceColumn.some(col => col && col.trim() !== "" && col !== "__EMPTY__");
      } else {
        // Se for string, verificar se não está vazia
        hasData = String(mapping.sourceColumn).trim() !== "" && mapping.sourceColumn !== "__EMPTY__";
      }
      
      if (hasData) {
        columns.add(mapping.gabaritoColumn);
      }
    });
    return Array.from(columns).sort();
  }, [columnMappings]);

  const updateConfig = (updates: Partial<MergeConfigType>) => {
    onConfigChange({
      leftFile: config?.leftFile || 'custo',
      rightFile: config?.rightFile || 'venda',
      leftKey: config?.leftKey || '',
      rightKey: config?.rightKey || '',
      how: 'inner', // Sempre inner join
      includeVariationKey: true, // Sempre ativado
      ...updates,
      how: 'inner', // Garantir que sempre seja inner
      includeVariationKey: true, // Garantir que sempre seja true
    });
  };

  if (!custoFile || !vendaFile) {
    return null;
  }

  return (
    <Card className="p-6 border-2 border-primary">
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <GitMerge className="h-5 w-5 text-primary" />
          <h3 className="font-semibold text-lg text-foreground">Configuração de Merge</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <Label className="text-sm font-medium mb-2">Arquivo Base (Left)</Label>
              <Select
                value={config?.leftFile || 'custo'}
                onValueChange={(value: 'custo' | 'venda') => updateConfig({ leftFile: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="custo">Planilha de Custo</SelectItem>
                  <SelectItem value="venda">Planilha de Venda</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-sm font-medium mb-2">Coluna de Referência (Left Key)</Label>
              <Select
                value={config?.leftKey || ''}
                onValueChange={(value) => updateConfig({ leftKey: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione a coluna do gabarito..." />
                </SelectTrigger>
                <SelectContent>
                  {mappedGabaritoColumns.map((col) => (
                    <SelectItem key={col} value={col}>
                      {col}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <Label className="text-sm font-medium mb-2">Arquivo Secundário (Right)</Label>
              <Select
                value={config?.rightFile || 'venda'}
                onValueChange={(value: 'custo' | 'venda') => updateConfig({ rightFile: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="custo">Planilha de Custo</SelectItem>
                  <SelectItem value="venda">Planilha de Venda</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-sm font-medium mb-2">Coluna de Referência (Right Key)</Label>
              <Select
                value={config?.rightKey || ''}
                onValueChange={(value) => updateConfig({ rightKey: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione a coluna do gabarito..." />
                </SelectTrigger>
                <SelectContent>
                  {mappedGabaritoColumns.map((col) => (
                    <SelectItem key={col} value={col}>
                      {col}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <div className="p-3 bg-muted/30 rounded-lg border border-border">
          <div className="flex items-center gap-2">
            <Label className="text-sm font-medium">Tipo de Merge:</Label>
            <span className="text-sm text-muted-foreground">Inner Join (apenas correspondências)</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            O merge sempre será realizado como Inner Join para incluir apenas registros que correspondem em ambas as planilhas.
          </p>
        </div>

        <div className="p-3 bg-muted/30 rounded-lg border border-border">
          <div className="flex items-center gap-2">
            <Label className="text-sm font-medium">Incluir variação (COR) no join:</Label>
            <span className="text-sm text-muted-foreground">Sempre ativado</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            A coluna de variação (COR) será sempre usada junto com a chave para o merge.
          </p>
        </div>
      </div>
    </Card>
  );
};
