# Segurança

Servidor apenas em 127.0.0.1, sem CORS, autenticação por chave aleatória em cada execução, verificação de Host/Origin, política CSP e dados servidos sem cache. A chave fica em arquivo privado e sessionStorage do painel. Não compartilhe a URL de abertura, a chave ou o perfil. Outros processos do mesmo usuário local podem acessar esses dados; isso não protege contra malware no Mac.

SQLite e diretório são privados ao usuário. O perfil é reutilizado diretamente pelo Playwright; cookies não são exportados. Não há senha Eventim no código, CVV, cartão, sincronização externa ou segredo de serviço. Por isso não há uso necessário do Keychain nesta fase. Caso segredos adicionais sejam introduzidos, use Apple Keychain.

Logs contêm eventos controlados pela aplicação, não dumps do DOM, headers ou tokens. Nome de modalidade é informação configurada pelo usuário. Não publique diagnósticos sem revisá-los. Faça backup apenas de dados não sensíveis; nunca publique o perfil do navegador.

O assistente não implementa bypass de CAPTCHA, fingerprints falsos, proxy rotativo, API privada, modificação de cookies da Eventim, posições ou tokens da fila. Há uma única sessão controlada. A observação não recarrega páginas. Entrada e preenchimento automáticos funcionam apenas no simulador local validado, com uma tentativa por estado e sessão. Na Eventim real, o adaptador de ações ainda precisa ser validado. CAPTCHA pausa as ações; não há serviço de resolução. URL inicial é validada estritamente como HTTPS em eventim.com.br ou www.eventim.com.br. Redirecionamentos naturais do navegador são permitidos porque a fila pode usar provedores oficiais externos.

Reinício deixa aviso conservador de possível perda de fila, inclusive após encerramento normal: reabrir Chromium não comprova recuperar posição. Pausar acompanhamento mantém o navegador aberto; encerrar o aplicativo fecha seu contexto e pode perder a fila. Não há recuperação automática do navegador. Um erro ou estado desconhecido exige intervenção humana.

Não existem acesso remoto, TLS ou Web Push neste MVP. O painel iPhone deve ser implementado com autenticação própria e HTTPS privado confiável em fase posterior, sem compartilhar a sessão Eventim.
