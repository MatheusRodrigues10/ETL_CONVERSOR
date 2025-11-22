/**
 * Exemplo de uso do componente ConfigRegexBuilder
 * 
 * Este arquivo demonstra como usar o componente ConfigRegexBuilder
 * em uma página ou outro componente React.
 */

import { useState } from "react";
import { ConfigRegexBuilder } from "./ConfigRegexBuilder";
import { ConfiguracaoRegex } from "@/types/regexConfig";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export const ConfigRegexBuilderExample = () => {
  const [jsonOutput, setJsonOutput] = useState<string>("");

  const handleExport = (json: string) => {
    setJsonOutput(json);
    console.log("JSON Exportado:", json);
  };

  const handleChange = (configs: ConfiguracaoRegex[]) => {
    console.log("Configurações atualizadas:", configs);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <ConfigRegexBuilder
        onChange={handleChange}
        onExport={handleExport}
      />

      {jsonOutput && (
        <Card>
          <CardHeader>
            <CardTitle>JSON Gerado</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-muted p-4 rounded-md overflow-auto text-sm">
              {jsonOutput}
            </pre>
            <Button
              onClick={() => {
                navigator.clipboard.writeText(jsonOutput);
              }}
              className="mt-4"
            >
              Copiar JSON
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

