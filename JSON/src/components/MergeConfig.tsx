import { Card } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { MergeConfig as MergeConfigType, UploadedFile } from '@/types/spreadsheet';
import { GitMerge } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface MergeConfigProps {
  custoFile: UploadedFile | null;
  vendaFile: UploadedFile | null;
  config: MergeConfigType | null;
  onConfigChange: (config: MergeConfigType) => void;
}

export const MergeConfig = ({ custoFile, vendaFile, config, onConfigChange }: MergeConfigProps) => {
  const updateConfig = (updates: Partial<MergeConfigType>) => {
    onConfigChange({
      leftFile: config?.leftFile || 'custo',
      rightFile: config?.rightFile || 'venda',
      leftKey: config?.leftKey || '',
      rightKey: config?.rightKey || '',
      how: config?.how || 'inner',
      includeVariationKey: config?.includeVariationKey || false,
      ...updates,
    });
  };

  const isCustomKey = (key: string, file: 'left' | 'right'): boolean => {
    if (!key || key === '') return false;
    const targetFile = file === 'left' 
      ? (config?.leftFile === 'custo' ? custoFile : vendaFile)
      : (config?.rightFile === 'custo' ? custoFile : vendaFile);
    return targetFile ? !targetFile.columns.includes(key) : false;
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
                disabled={isCustomKey(config?.leftKey || '', 'left')}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione a coluna..." />
                </SelectTrigger>
                <SelectContent>
                  {(config?.leftFile === 'custo' ? custoFile : vendaFile)?.columns.map((col) => (
                    <SelectItem key={col} value={col}>
                      {col}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="mt-2 flex gap-2">
                <Input
                  placeholder="Ou digite a coluna..."
                  defaultValue={config?.leftKey || ''}
                  onKeyDown={(e) => {
                    const target = e.target as HTMLInputElement;
                    if (e.key === 'Enter' && target.value.trim()) {
                      updateConfig({ leftKey: target.value.trim() });
                    }
                  }}
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={(e) => {
                    const input = (e.currentTarget.previousElementSibling as HTMLInputElement);
                    if (input && input.value.trim()) {
                      updateConfig({ leftKey: input.value.trim() });
                    }
                  }}
                >Usar</Button>
                {isCustomKey(config?.leftKey || '', 'left') && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => updateConfig({ leftKey: '' })}
                  >Limpar</Button>
                )}
              </div>
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
                disabled={isCustomKey(config?.rightKey || '', 'right')}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione a coluna..." />
                </SelectTrigger>
                <SelectContent>
                  {(config?.rightFile === 'custo' ? custoFile : vendaFile)?.columns.map((col) => (
                    <SelectItem key={col} value={col}>
                      {col}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="mt-2 flex gap-2">
                <Input
                  placeholder="Ou digite a coluna..."
                  defaultValue={config?.rightKey || ''}
                  onKeyDown={(e) => {
                    const target = e.target as HTMLInputElement;
                    if (e.key === 'Enter' && target.value.trim()) {
                      updateConfig({ rightKey: target.value.trim() });
                    }
                  }}
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={(e) => {
                    const input = (e.currentTarget.previousElementSibling as HTMLInputElement);
                    if (input && input.value.trim()) {
                      updateConfig({ rightKey: input.value.trim() });
                    }
                  }}
                >Usar</Button>
                {isCustomKey(config?.rightKey || '', 'right') && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => updateConfig({ rightKey: '' })}
                  >Limpar</Button>
                )}
              </div>
            </div>
          </div>
        </div>

        <div>
          <Label className="text-sm font-medium mb-2">Tipo de Merge</Label>
          <Select
            value={config?.how || 'inner'}
            onValueChange={(value: 'left' | 'right' | 'inner' | 'outer') => updateConfig({ how: value })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="inner">Inner Join (apenas correspondências)</SelectItem>
              <SelectItem value="left">Left Join (todos do arquivo base)</SelectItem>
              <SelectItem value="right">Right Join (todos do arquivo secundário)</SelectItem>
              <SelectItem value="outer">Outer Join (todos os registros)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center justify-between border rounded-md p-3">
          <div>
            <Label className="text-sm font-medium">Incluir variação (COR) no join</Label>
            <div className="text-xs text-muted-foreground">Quando habilitado, a coluna de variação será usada junto com a chave para o merge.</div>
          </div>
          <Switch
            checked={Boolean(config?.includeVariationKey)}
            onCheckedChange={(checked) => updateConfig({ includeVariationKey: Boolean(checked) })}
          />
        </div>
      </div>
    </Card>
  );
};
