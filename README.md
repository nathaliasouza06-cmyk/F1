# F1 QUEUE ASSISTANT 2027

MVP local para Python 3.12+, macOS Intel ou Apple Silicon compatível com Chromium/Playwright. Preparação antecipada, login manual em perfil persistente, calendário SQLite, observação segura, notificações macOS, dashboard e venda simulada. Não é afiliado à Eventim ou à Fórmula 1.

## Instalar no Mac

1. Instale Python 3.12 ou superior de https://www.python.org/downloads/macos/.
2. Coloque a pasta do projeto em um local permanente e abra `scripts/Instalar.command` pelo Finder. A instalação baixa dependências e Chromium. Se o Finder pedir permissão de execução, execute uma vez `chmod +x scripts/*.command` dentro da pasta do projeto. Não desative o Gatekeeper.
3. Abra `scripts/Iniciar.command`. O painel abre automaticamente com a chave local no fragmento da URL, removido em seguida. A chave não aparece nos logs HTTP.
4. Para execução automática ao iniciar sua sessão no Mac, abra `scripts/Agendamento.command`. Depois, use `scripts/Abrir Painel.command`. Não mova o projeto após instalar o serviço. O LaunchAgent mantém o aplicativo em execução na sessão gráfica do usuário.

O aplicativo não inicia um Mac desligado, não desbloqueia uma sessão e não garante alertas com o Mac em repouso. Use a tomada, mantenha a sessão ativa e teste antes da venda. `scripts/Manter Acordado.command` executa `caffeinate -i` por 8 horas opcionalmente. Não é necessário repetir comandos de Terminal para uso normal.

Para remover o serviço: `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/br.local.f1queue.plist`, e remova esse plist. Não encerre o serviço durante uma fila. Iniciar uma segunda instância não abre outro navegador: um lock de processo protege o perfil.

## Primeiro teste — sem acessar uma venda real

No Dashboard, clique **Testar venda simulada**. No navegador visível:

1. Clique em **Login manual simulado**. O cookie local persiste no perfil.
2. Clique em **Abrir sala de espera**; aguarde até 10 segundos pela entrada automática no simulador.
3. Clique em **Entrar manualmente**, **Ativar fila** e **Aguardar sua vez**. A aba não é recarregada ou substituída pelo assistente.
4. Em Minha Compra, salve quantidade e setor. Clique em **Liberar ingressos**: o assistente alerta, traz o navegador ao primeiro plano e preenche os campos simulados uma vez. Revise os dados.
5. Teste **Expirar sessão** e **CAPTCHA simulado**.

Para testar a abertura agendada sem Eventim, clique **Agendar simulação** com o navegador controlado fechado: a preparação ocorrerá em 1–2 minutos, para uma venda fictícia configurada 120 minutos depois. O aplicativo deve permanecer em execução. Confira o evento no Histórico. Não agende esse teste durante uma sessão real.

Também há uma sequência temporizada (15 / 45 / 75 segundos). Não é uma promessa sobre o comportamento da Eventim.

Para testar a persistência, feche o aplicativo somente no simulador, reabra e reconheça o aviso de possível perda da posição antes de abrir o simulador novamente. O login simulado deve persistir. Nenhuma recuperação de fila é prometida.

## Eventim real e preparação

Selecione a modalidade e clique **Preparar agora** ou **Abrir login manual** em Minha Conta. Faça login diretamente no navegador controlado. O aplicativo não lê nem armazena sua senha. Use sempre esse perfil para a sessão principal.

Os quatro registros iniciais usam as datas fornecidas pelo usuário, em `America/Sao_Paulo`. Porto Bank e Amex têm horário inicial 12:00, mas estão **Aguardando confirmação**. A venda geral e sua sala têm horário vazio. Nenhuma data foi confirmada externamente.

No Calendário, edite data, hora, URL oficial e antecedência (padrão 120 minutos; aceita 30, 60, 90, 180 e qualquer valor de 0 a 1440). Marque **Confirmado oficialmente** somente após conferir a fonte oficial. Somente essa marcação habilita abertura automática. O agendador roda a cada 10 segundos e pode preparar uma venda atrasada até 6 horas depois. Horários sem definição não são agendados. Alertas usam os horários cadastrados e indicam seu estado de confirmação.

Se já houver uma aba controlada aberta, o agendador não troca sua URL. Caso a abertura falhe, registra e alerta sem tentar reiniciar automaticamente; use o painel para intervenção. Evite agendar modalidades sobrepostas no mesmo perfil. O serviço não fecha o navegador ao pausar acompanhamento.

**Limitação real deliberada:** nenhum seletor, API ou estado de autenticação da Eventim foi validado. `monitor.observe()` retorna **Verificação manual necessária** e **Verificação necessária** para páginas reais. Você deve observar a página e entrar manualmente na sala. O MVP não identifica de forma confiável abertura real da sala ou sua vez; os alertas desses estados estão funcionais no simulador. Não dependa dele como única fonte de alerta na venda real.

O ponto de extensão é `f1queue/monitor.py`. Antes de implementar um adaptador real, valide DOM, navegação, sinais de autenticação e evidências de cada estado em uma sessão autorizada; mantenha testes locais. Entrada e preenchimento automáticos estão implementados no simulador. Na Eventim real, continuam pendentes de validação do DOM e do fluxo. Não há seletores reais inventados. CAPTCHA, MFA, compra, pagamento e confirmação são manuais.

## Notificações

Notificações nativas via AppleScript, sem interpolação de conteúdo em comandos. Autorize notificações no macOS, confira Foco/Não Perturbe e clique **Testar notificação**. Alertas são deduplicados em SQLite. Não há garantia de entrega pelo sistema operacional. O histórico mantém os avisos mesmo quando notificações estão desativadas. Clique na notificação para abrir o painel ainda exige integração nativa adicional; use o atalho **Abrir Painel**.

## Dados e diagnóstico

Dados padrão: `~/Library/Application Support/F1 Queue Assistant/`:

- `assistant.sqlite3`: calendário, preferências iniciais, eventos e deduplicação.
- `browser-profile/`: perfil Chromium sensível, incluindo sessão local.
- `panel-token`: chave aleatória, renovada a cada execução.
- `diagnostic.jsonl`: eventos estruturados gravados durante a execução.
- `service.log` e `service-error.log`: diagnóstico do LaunchAgent.

`F1_DATA_DIR` e `F1_PORT` podem ser definidos no ambiente antes de iniciar. `.env.example` é documentação; não há carregamento implícito de `.env`. O banco é criado na primeira execução; não distribuímos um banco com sessão ou segredos.

## Testes

Na raiz, após instalar: `.venv/bin/python -m unittest discover -s tests -v`.

Teste de navegador: `.venv/bin/python tests/browser_smoke.py`. Usa Chromium headless apenas para testes locais, sem acessar a Eventim. No desenvolvimento Linux, `F1_TEST_CHROMIUM=/usr/bin/chromium` permite usar Chromium instalado. O aplicativo de produção sempre usa navegador visível.

## Escopo desta entrega

Primeira fase funcional e testável com simulador. As dez áreas de navegação estão presentes; preferências completas além de quantidade e setor, PWA instalável, acesso iPhone, HTTPS privado e Web Push são segunda fase e não estão implementados. O layout já é responsivo, mas não habilita acesso remoto. Para iOS, PWA e Web Push requerem HTTPS confiável, instalação na Tela de Início, iOS compatível e infraestrutura de push com consentimento. Não exponha esta porta diretamente à internet.

Compatibilidade com os dois tipos de processador depende das versões suportadas pelo Python e Playwright. Não foram executados testes nativos neste ambiente Linux; valide notificações, launchd, repouso e navegador no Mac antes de usar em uma venda.

## Atualização de automação

`f1queue/automation.py` executa uma entrada por sessão e preenche quantidade/setor no simulador. CAPTCHA, sessão expirada e estado incerto suspendem ações; a observação continua e permite seguir quando a página sair desses estados. Não há solucionador de CAPTCHA, serviço externo de resolução, envio de documentos, pagamento ou confirmação de compra. O fluxo real continua exigindo validação. Campos adicionais devem ser definidos e configurados localmente, sem enviar documentos ou credenciais pelo chat.

## Atualização 0.1.1 — confirmação de reabertura

A confirmação após reinício aparece em todas as páginas, inclusive Minha Conta. Marque-a somente se não há uma fila real ativa. Em seguida, clique em Testar venda simulada ou Abrir login manual. O aviso de reabertura não sobrescreve mais o erro real a cada atualização do painel. Falhas distinguem Chromium ausente, perfil em uso e carregamento da página.

Para atualizar pelo ZIP do GitHub, encerre o aplicativo com Ctrl+C no Terminal somente quando não houver uma fila real ativa. Extraia o ZIP atualizado em uma pasta nova, execute scripts/Instalar.command e depois scripts/Iniciar.command. As configurações e o perfil ficam na pasta Application Support do usuário; não os apague. Confira Versão 0.1.1 no rodapé do painel.
