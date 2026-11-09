# F1 QUEUE ASSISTANT 2027 — v0.2.0

Aplicativo local para macOS, Python 3.12+, Playwright visível, perfil persistente, FastAPI, SQLite, notificações macOS e preparação agendada em America/Sao_Paulo. Não afiliado à Eventim ou à Fórmula 1.

## Instalar no Mac

1. Instale Python 3.12 ou superior em https://www.python.org/downloads/macos/.
2. Baixe o ZIP do repositório, extraia em uma pasta permanente e abra `scripts/Instalar.command` no Finder.
3. Aguarde a instalação de dependências e Chromium; abra `scripts/Iniciar.command`.
4. Mantenha o Terminal aberto. O painel abre autenticado automaticamente, na porta local 8765.

Se o macOS bloquear um script sem assinatura, revise o código e autorize somente esse arquivo em Ajustes do Sistema → Privacidade e Segurança → Abrir Mesmo Assim. Não desative o Gatekeeper. Se faltar permissão de execução, execute uma única vez `chmod +x scripts/*.command` dentro da pasta do projeto.

Para atualizar uma instalação existente, somente quando não houver uma fila real ativa: encerre a execução com Ctrl+C no Terminal; extraia o ZIP atualizado em uma pasta nova; execute novamente Instalar.command e Iniciar.command. As configurações e o perfil continuam em Application Support, não na pasta do projeto. Não apague esses dados. Confira **Versão 0.2.0** no rodapé.

## Usar a venda real

A versão 0.2.0 executa entrada e preenchimento na página real por meio de **controles que você verifica na sessão do Mac**. Não contém seletores presumidos da Eventim. Não foi validada de ponta a ponta em uma compra real: a consulta pública pelo Chromium neste ambiente recebeu HTTP 503. A captura da usuária mostrou página não encontrada na campanha antiga. Uma página indisponível não permite configurar ou automatizar uma compra.

1. Em **Minha Conta**, clique em **Abrir login manual**. A primeira abertura usa a página inicial oficial https://www.eventim.com.br/. Faça login diretamente no navegador controlado. Senha, CAPTCHA e MFA são preenchidos no próprio site.
2. Na mesma aba, navegue pelo link oficial da venda de **2027** fornecido pela Eventim/organizador. Confirme o evento. O endereço inicial `/f1saopaulo` é apenas um ponto de partida; não se presume que esteja disponível ou atualizado.
3. Em **Minha Compra**, salve quantidade e setor prioritário. A quantidade inicial é 4; limites e elegibilidade continuam sujeitos às regras oficiais.
4. Em **Venda real**, clique em **Inspecionar página real**. Isso pausa as ações enquanto você configura e lista rótulos dos controles visíveis; não lê valores de campos, senha, cookies ou tokens.
5. Selecione **Botão para entrar na sala de espera**, usando o texto que aparece no botão real. Confirme sua finalidade na caixa de seleção e clique em **Validar controles e ativar**. O aplicativo tenta o clique uma única vez, se o mesmo controle continuar presente na mesma URL e não houver verificação humana.
6. Quando o site mostrar sala de espera ou fila, inspecione essa tela e selecione o título/mensagem estável que comprova esse estado. A página não será atualizada pelo aplicativo. Sem um indicador verificado, o estado é **Verificação manual necessária**.
7. Quando aparecer a seleção de ingressos, inspecione essa tela e configure o indicador **Escolha de ingressos liberada**, o campo **Quantidade** e o campo **Setor** que estiverem presentes. O aplicativo alerta, traz a janela para frente e preenche cada campo uma vez. Uma opção indisponível nunca é substituída silenciosamente.
8. Revise os dados e conclua a compra manualmente. Não há envio de pedido, pagamento ou confirmação final automatizados.

Configure somente funções que já existam na tela. Não selecione títulos genéricos como prova de fila ou de liberação de ingressos. Controles com rótulos duplicados ou de confirmação/pagamento não são oferecidos. Indicadores e campos podem mudar: se não houver correspondência exata, as ações param e exigem nova configuração. **Pausar ações reais** mantém a aba aberta e continua observando.

### Limites reais desta integração

- Os vínculos são verificados localmente por você; isso não equivale a uma validação independente do fluxo Eventim.
- A configuração só aceita HTTPS nos hosts eventim.com.br e www.eventim.com.br, no documento principal. Controles em iframes, shadow DOM, canvas ou provedores externos de fila exigem interação manual.
- Uma nova URL (incluindo query), alteração no DOM ou rótulo diferente invalida a ação. Não tenta adaptar seletores por aproximação.
- Cada ação é tentada uma vez por controle/sessão, inclusive se houver timeout. Uma falha de resultado incerto exige conferência manual.
- Os vínculos não são restaurados automaticamente após reiniciar: configure novamente. URLs completas e seletores ficam apenas em memória; logs não recebem parâmetros de fila ou rótulos capturados.
- Entrar em outra aba por popup não transfere automaticamente a observação para ela. Preserve a aba oficial e acompanhe manualmente esse fluxo.
- A autenticação real continua **Verificação necessária**; a presença de menus genéricos não comprova conta conectada.
- CAPTCHA configurado por indicador, desafio visível compatível ou campo HTML `autocomplete="one-time-code"` pausa as ações e gera alerta. Outros desafios não reconhecidos exigem acompanhamento manual. Não há resolução automática de CAPTCHA nem recebimento de códigos MFA.
- Não há garantia de ingresso, posição na fila ou entrega de notificações. Não dependa do aplicativo como única fonte de acompanhamento da venda.

## Preparação e calendário

Os quatro registros iniciais usam as datas fornecidas pelo usuário: Porto Bank 09/11/2026 12:00, Amex 12/11/2026 12:00 e sala/venda geral em 16/11/2026 sem horário. Foram cadastrados como aguardando confirmação/previstos; não são confirmação automática de calendário oficial.

Edite data, horário, URL oficial e antecedência em **Calendário de Vendas**. Padrão 120 minutos; aceita 30, 60, 90, 180 ou qualquer valor de 0 a 1440. Só a marcação **Confirmado oficialmente** habilita abertura automática. Horário vazio não é agendado. O ciclo roda a cada 10 segundos e pode preparar uma venda atrasada até 6 horas após o horário cadastrado. Lembretes: 120, 60, 30, 15, 5 e 0 minutos.

Com uma aba já aberta, o aplicativo não troca a URL pelo agendamento: preserve a sessão e navegue manualmente antes de entrar em espera. Não programe modalidades concorrentes no mesmo perfil. Abrir uma URL pública não comprova que a sala de espera abriu. O monitor observa a página existente sem recarregar, sem APIs privadas e sem múltiplos acessos para disputar posições.

Para iniciar automaticamente com a sessão gráfica do usuário no Mac, execute `scripts/Agendamento.command`. Depois, use `scripts/Abrir Painel.command`. O LaunchAgent usa caminhos absolutos: não mova o projeto após instalá-lo. Para remover o serviço, execute `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/br.local.f1queue.plist` e remova esse plist, somente fora de uma fila ativa.

O Mac deve estar ligado, conectado e com sessão iniciada. O aplicativo não liga ou desbloqueia um Mac. `scripts/Manter Acordado.command` executa `caffeinate -i` por 8 horas opcionalmente. Teste notificações, Foco e repouso antes da venda. Encerrar o aplicativo fecha seu navegador e pode perder a posição. O perfil persistente não garante recuperar fila após reinício.

## Teste sem venda real

Em Dashboard, clique em **Testar venda simulada**. Após reiniciar, confirme a reabertura somente se não houver uma fila real ativa. Na janela simulada:

1. Faça **Login manual simulado**.
2. Clique **Abrir sala de espera** e aguarde até 10 segundos pela entrada automática.
3. Simule **Ativar fila**, **Aguardar sua vez** e **Liberar ingressos**.
4. Configure Minha Compra para verificar o preenchimento de quantidade e setor.
5. Teste **Expirar sessão** e **CAPTCHA simulado**.

**Agendar simulação** prepara em 1–2 minutos para uma venda fictícia com antecedência de 120 minutos. Há também sequência de estados em 15/45/75 segundos. Nada disso contata a Eventim.

## Testes automatizados

Após instalar, na raiz:

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tests/browser_smoke.py
.venv/bin/python tests/real_smoke.py
```

`real_smoke.py` testa o código do adaptador real em HTML local interceptado pelo Playwright, sem requisições à Eventim. Domínios no teste são virtuais. Cobre consentimento, clique único concorrente, alteração do DOM/URL, MFA/CAPTCHA, setor inexistente, privacidade e ausência de pagamento. Isso não é uma compra real validada. No Linux de desenvolvimento, `F1_TEST_CHROMIUM=/usr/bin/chromium` seleciona Chromium instalado. Produção sempre usa navegador visível.

## Notificações e dados

Notificações nativas via AppleScript, deduplicadas por lembrete/transição. Autorize no macOS e teste em **Notificações**. Não há garantia de entrega; eventos ficam no histórico. Abrir o painel por clique na notificação exige integração nativa adicional; use o atalho Abrir Painel.

Pasta padrão: `~/Library/Application Support/F1 Queue Assistant/`:

- `assistant.sqlite3`: calendário, preferências, eventos e deduplicação, criado na primeira execução.
- `browser-profile/`: perfil sensível de navegação, mantido apenas no Mac.
- `panel-token`: chave aleatória renovada a cada execução, arquivo privado.
- `diagnostic.jsonl`: eventos estruturados controlados pela aplicação.
- `service.log` e `service-error.log`: diagnóstico do serviço opcional.

`F1_DATA_DIR` e `F1_PORT` podem ser definidos no ambiente. `.env.example` não é carregado implicitamente. Um lock evita duas instâncias no mesmo perfil. Não publique dados de Application Support. Consulte SECURITY.md.

## Plataforma e próximas fases

Compatibilidade Intel/Apple Silicon depende das versões suportadas de Python/Playwright. Os testes automatizados foram realizados em Linux; instalação, notificações, launchd e comportamento de repouso devem ser conferidos no Mac. A usuária já executou o instalador e abriu o painel no Mac.

PWA remota para iPhone, HTTPS privado, preferências completas por pessoa e Web Push continuam fora desta fase. O servidor fica restrito a 127.0.0.1. Não exponha a porta à internet. iOS Web Push exige HTTPS confiável, instalação na Tela de Início, versão compatível, permissão e infraestrutura de push. Nenhum cookie Eventim é compartilhado com iPhone.
