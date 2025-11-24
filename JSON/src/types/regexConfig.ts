/**
 * Tipos para a estrutura de configuração de regex
 */

export type AplicarRegexTipo = "inicial" | "abaixo";

export type LinhaParadaTipo =
  | "parar_total"
  | "aplicar_e_parar"
  | "ignorar_e_continuar";

export interface LinhaParada {
  nome: string;
  tipo: LinhaParadaTipo;
  regexLinhaParada?: string;
  novaConfiguracaoAbaixo?: ConfiguracaoRegex;
}

export interface ConfiguracaoRegex {
  inicio: string;
  variacoes: string[];
  regexAtivado: boolean;
  aplicarRegex: AplicarRegexTipo;
  linhaParada?: LinhaParada;
}
