# Validação realizada

Ambiente: Python 3.12.14, Linux, Chromium local, 08/11/2026.

- 9 testes unitários/HTTP passaram: persistência e reinicialização, fuso São Paulo, contagem regressiva, fronteira de 120 minutos, preparação deduplicada, estados simulados, notificações deduplicadas, URLs oficiais, proteção de autenticação/Host/Origin, validação de calendário, proteção de aba existente e confirmação após reinício.
- Integração Playwright passou: dashboard autenticado, edição do calendário, viewport 390 × 844 sem overflow horizontal, sete mudanças de estado, login simulado e persistência após fechar/reabrir perfil Chromium.
- Compilação Python e sintaxe dos scripts shell verificadas.
- Nenhuma solicitação à Eventim durante os testes.

Os testes HTTP e Chromium precisaram executar fora do sandbox de desenvolvimento por restrições locais de sockets. As execuções finais passaram. O teste de integração usa headless; produção usa navegador visível.

Não verificados neste ambiente: launchd, notificações AppleScript, Keychain do Chromium, arquitetura Intel/Apple Silicon, instalação em um Mac real, comportamento e termos atuais da Eventim. O adaptador real permanece explicitamente sem detecção validada. PWA remota não implementada na primeira fase.

Comandos reproduzíveis estão no README.md.

Atualização validada: entrada automática na sala simulada; preenchimento de quantidade/setor; pausa durante CAPTCHA simulado; proteção contra repetição que sobrescreva edição manual. Os 9 testes anteriores e a integração Chromium passaram novamente. Não houve acesso à Eventim.

09/11/2026 — versão 0.1.1: 11 testes unitários/HTTP passaram. A integração Chromium confirmou a confirmação acessível em Minha Conta, ausência de chamada de abertura sem confirmação e preservação do erro após atualizar o status. Também validou as funcionalidades anteriores. Mensagens de diagnóstico não expõem caminhos ou conteúdo bruto das exceções. Não foi possível reproduzir diretamente o erro de abertura no Mac da usuária; a atualização corrige o painel e permite identificar a causa caso persista.
