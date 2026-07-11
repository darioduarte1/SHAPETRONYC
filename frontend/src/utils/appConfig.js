// =============================================================================
// appConfig.js
// -----------------------------------------------------------------------------
// Configuração simples do frontend.
// É usado para ligar/desligar ferramentas temporárias da fase experimental,
// como limpeza de atletas de teste e painéis técnicos de decisão do coach.
// Por defeito fica ligado nesta fase; em produção pode ser desligado com
// VITE_EXPERIMENTAL_MODE=false.
// =============================================================================
export const EXPERIMENTAL_MODE = import.meta.env.VITE_EXPERIMENTAL_MODE !== "false";
