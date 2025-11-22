import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Copy, Download, CheckCircle2 } from 'lucide-react';
import { FormEvent, useState } from 'react';
import { useToast } from '@/hooks/use-toast';
import { PandasConfig } from '@/types/spreadsheet';

interface JsonOutputProps {
  config: PandasConfig;
  regexConfig?: any;
}

export const JsonOutput = ({ config, regexConfig }: JsonOutputProps) => {
  const [copied, setCopied] = useState(false);
  const [isDownloadDialogOpen, setIsDownloadDialogOpen] = useState(false);
  const [fileNameInput, setFileNameInput] = useState('');
  const { toast } = useToast();

  // Mesclar os configs em um único objeto
  const finalConfig = regexConfig && regexConfig.length > 0 
    ? { ...config, regexConfig }
    : config;

  const jsonString = JSON.stringify(finalConfig, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    toast({
      title: 'Copiado!',
      description: 'JSON copiado para a área de transferência',
    });
    setTimeout(() => setCopied(false), 2000);
  };

  const triggerDownload = (finalName: string) => {
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = finalName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast({
      title: 'Download iniciado!',
      description: `O arquivo ${finalName} está sendo baixado`,
    });
  };

  const openDownloadDialog = () => {
    setFileNameInput('');
    setIsDownloadDialogOpen(true);
  };

  const handleFileNameSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const sanitizedInput = fileNameInput
      .trim()
      .replace(/\s+/g, '_')
      .replace(/[^a-zA-Z0-9_-]/g, '');

    const processedName = sanitizedInput
      .replace(/^config_/i, '')
      .replace(/\.json$/i, '');

    if (!processedName) {
      toast({
        title: 'Nome inválido',
        description:
          'Informe um nome válido para o arquivo. Exemplo: MEU_ARQUIVO',
        variant: 'destructive',
      });
      return;
    }

    const finalName = `config_${processedName.toUpperCase()}.json`;
    triggerDownload(finalName);
    setIsDownloadDialogOpen(false);
    setFileNameInput('');
  };

  const handleFileNameChange = (value: string) => {
    const sanitizedValue = value
      .replace(/\s+/g, '_')
      .replace(/[^a-zA-Z0-9_-]/g, '');
    setFileNameInput(sanitizedValue.toUpperCase());
  };

  return (
    <Card className="p-6 border-2 border-success">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-lg text-foreground flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-success" />
            JSON Gerado
          </h3>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              className="gap-2"
            >
              {copied ? <CheckCircle2 className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              {copied ? 'Copiado!' : 'Copiar'}
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={openDownloadDialog}
              className="gap-2"
            >
              <Download className="h-4 w-4" />
              Download
            </Button>
          </div>
        </div>

        <div className="bg-muted/30 rounded-lg p-4 overflow-x-auto">
          <pre className="text-xs text-foreground font-mono whitespace-pre-wrap break-words">
            {jsonString}
          </pre>
        </div>

      </div>

      <Dialog open={isDownloadDialogOpen} onOpenChange={setIsDownloadDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Definir nome do arquivo</DialogTitle>
          </DialogHeader>

          <form onSubmit={handleFileNameSubmit} className="space-y-4">
            <div className="flex items-center gap-2 rounded-md border border-input bg-muted/30 px-3 py-2">
              <span className="text-sm text-muted-foreground">config_</span>
              <Input
                autoFocus
                value={fileNameInput}
                onChange={(event) => handleFileNameChange(event.target.value)}
                placeholder="Nome do arquivo"
                className="border-0 bg-transparent px-0 shadow-none focus-visible:ring-0"
              />
              <span className="text-sm text-muted-foreground">.json</span>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setIsDownloadDialogOpen(false);
                  setFileNameInput('');
                }}
              >
                Cancelar
              </Button>
              <Button type="submit">Baixar</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </Card>
  );
};
