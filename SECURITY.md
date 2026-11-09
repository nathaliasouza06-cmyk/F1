# Segurança

Servidor apenas em 127.0.0.1, sem CORS, autenticação por chave aleatória em cada execução, verificação de Host/Origin, política CSP e dados servidos sem cache. A chave fica em arquivo privado e sessionStorage do painel. Não compartilhe a URL de abertura, a chave ou o perfil. Outros processos do mesmo usuário local podem acessar esses dados; isso não protege contra malware no Mac.

SQLite e diretório são privados ao usuário. O perfil é reutilizado diretamente pelo Playwright; cookies não são exportados. Não há senha Eventim no código, CVV, cartão, sincronização externa ou segredo de serviço. Por isso não há uso necessário do Keychain nesta fase. Caso segredos adicionais sejam introduzidos, use Apple Keychain.

Logs contêm eventos controlados pela aplicação, não dumps do DOM, headers ou tokens. Nome de modalidade é informação configurada pelo usuário. Não publique diagnósticos sem revisá-los. Faça backup apenas de dados não sensíveis; nunca publique o perfil do navegador.

O assistente não implementa bypass de CAPTCHA, fingerprints falsos, proxy rotativo, API privada, modificação de cookies da Eventim, posições ou tokens da fila. Há uma única sessão controlada. A observação não recarrega páginas. Entrada e preenchimento automáticos funcionam no simulador e em controles configurados localmente na página real. O fluxo Eventim completo não foi validado independentemente. CAPTCHA pausa as ações; não há serviço de resolução. URL inicial é validada estritamente como HTTPS em eventim.com.br ou www.eventim.com.br. Redirecionamentos naturais do navegador são permitidos porque a fila pode usar provedores oficiais externos.

Reinício deixa aviso conservador de possível perda de fila, inclusive após encerramento normal: reabrir Chromium não comprova recuperar posição. Pausar acompanhamento mantém o navegador aberto; encerrar o aplicativo fecha seu contexto e pode perder a fila. Não há recuperação automática do navegador. Um erro ou estado desconhecido exige intervenção humana.

Não existem acesso remoto, TLS ou Web Push neste MVP. O painel iPhone deve ser implementado com autenticação própria e HTTPS privado confiável em fase posterior, sem compartilhar a sessão Eventim.

## Integração real configurável (0.2.0)

O painel autenticado permite inspecionar rótulos visíveis na página HTTPS oficial atualmente aberta no Mac. Não aceita CSS, JavaScript ou URLs arbitrários fornecidos pelo painel: cada configuração precisa referenciar um candidato obtido daquela inspeção, ainda presente e idêntico, por até 5 minutos. A configuração é local por processo; não é uma autorização ou certificação da Eventim.

Regras guardam a URL exata somente em memória e são invalidadas por mudanças. Seletores são derivados da estrutura do DOM real, comparados a rótulo, tipo e posição, sem aproximações e sem cookies/tokens. Inspecionar pausa ações. Rótulos duplicados, campos sensíveis e botões identificáveis como pagamento/confirmação são excluídos. O usuário deve conferir a função do botão de entrada. Fila, CAPTCHA/MFA e estado incerto impedem ações; verificações não reconhecidas precisam de observação humana. As ações são serializadas e tentadas uma vez, mesmo após falha.

O preenchimento se limita a quantidade e setor. Não há pedido, envio de formulário, pagamento ou confirmação final no código de automação. Uma seleção de setor ausente não provoca tentativa em outro setor. Valores de campos, DOM completo e URLs com query não são exportados nem registrados no histórico. O texto da página é observado em memória para reconhecer erro de página já documentado. Não se usa observação de rede nem endpoints privados.

Testes com domínio virtual interceptam todas as requisições e usam somente HTML local. O teste público de leitura da campanha recebeu HTTP 503; não houve validação de uma transação real. Não há contorno desse bloqueio. Controles fora dos hosts aprovados, em iframes ou em novas abas exigem intervenção manual.
