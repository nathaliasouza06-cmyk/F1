"""Integração real configurada pelo DOM presente no Mac, sem seletores presumidos.

As regras valem apenas no processo atual e na URL exata capturada, mantida em
memória. Nenhuma query string, cookie, valor de campo ou DOM é persistido.
"""
import asyncio
import secrets
import time
from urllib.parse import urlsplit
from .monitor import State

# Só se leem rótulos de controles e títulos. Nunca valores digitados.
SCAN_JS = r'''() => {
 const label = el => {
   if (el.getAttribute('aria-label')) return el.getAttribute('aria-label');
   if (el.labels?.length) return [...el.labels].map(l=>{const c=l.cloneNode(true);c.querySelectorAll('input,select,textarea,button').forEach(n=>n.remove());return c.textContent}).join(' ');
   return el.innerText || el.getAttribute('title') || '';
 };
 const path = el => {
   const parts=[];
   while(el && el.nodeType===1 && el!==document.body){
     const tag=el.tagName.toLowerCase();
     const siblings=[...el.parentElement.children].filter(n=>n.tagName===el.tagName);
     parts.unshift(tag+':nth-of-type('+(siblings.indexOf(el)+1)+')');
     el=el.parentElement;
   }
   return 'body > '+parts.join(' > ');
 };
 return [...document.querySelectorAll('button,a,input,select,h1,h2,h3,[role="status"],[aria-live]')]
 .slice(0,600).flatMap(el=>{
   const rect=el.getBoundingClientRect(), style=getComputedStyle(el);
   if(el===document.body || !document.body.contains(el) || !rect.width || !rect.height || style.display==='none' || style.visibility==='hidden' || el.disabled) return [];
   const tag=el.tagName.toLowerCase(), type=(el.type || '').toLowerCase();
   if(tag==='input' && !['number','text'].includes(type)) return [];
   const text=label(el).replace(/\s+/g,' ').trim();
   if(!text || text.length>160 || /[\w.+-]+@[\w.-]+|\d{5,}|\b(cpf|cvv|cvc|senha|password|cartão|card number)\b/i.test(text)) return [];
   let kind='marker';
   if(['button','a'].includes(tag)){
     if(el.target==='_blank' || /pagar|finaliz|concluir|confirm|pedido|pagamento|payment|purchase|checkout|order|logout|sair/i.test(text)) return [];
     if(tag==='a'){
       const u=new URL(el.href,location.href);
       if(u.origin!==location.origin || !['https:','http:'].includes(u.protocol))return [];
     }
     kind='entry';
   } else if(['input','select'].includes(tag)) {
     if(!/quantidade|quantity|setor|sector/i.test(text))return [];
     kind='field';
   }
   return [{selector:path(el),label:text,tag,type,kind}];
 });
}'''

ROLES={'entry','quantity','sector','waiting','queue','selection','human','expired'}


def is_eventim(url):
    parsed=urlsplit(url)
    return parsed.scheme=='https' and parsed.hostname in {'www.eventim.com.br','eventim.com.br'} and parsed.port in (None,443) and not parsed.username and not parsed.password


class RealAdapter:
    def __init__(self,store):
        self.store=store
        self.snapshot=None
        self.paused=True
        self.action_lock=asyncio.Lock()
        self.rules={}
        self.attempted=set()
        self.message='Abra a venda real e configure os controles presentes na página.'

    async def scan(self,page):
        if not is_eventim(page.url):
            raise ValueError('A configuração automática é restrita ao domínio HTTPS oficial da Eventim Brasil. Redirecionamentos para provedores de fila continuam manuais.')
        self.paused=True
        source_url=page.url
        nodes=await page.evaluate(SCAN_JS)
        nodes=[node for node in nodes if sum(n['kind']==node['kind'] and n['label']==node['label'] for n in nodes)==1]
        if page.url != source_url:
            raise ValueError('A página mudou durante a inspeção. Aguarde e tente novamente.')
        scan_id=secrets.token_urlsafe(16)
        self.snapshot=dict(id=scan_id,url=source_url,at=time.monotonic(),nodes={str(i):node for i,node in enumerate(nodes)})
        u=urlsplit(source_url)
        return dict(scan_id=scan_id,page=u.scheme+'://'+u.netloc+u.path,candidates=[dict(id=str(i),label=n['label'],kind=n['kind'],tag=n['tag']) for i,n in enumerate(nodes)])

    async def configure(self,page,scan_id,bindings,authorize_entry=False):
        snapshot=self.snapshot
        if not snapshot or snapshot['id']!=scan_id or time.monotonic()-snapshot['at']>300 or page.url!=snapshot['url']:
            raise ValueError('Inspeção expirada ou página alterada. Clique em Inspecionar página real novamente.')
        if not bindings or not set(bindings)<=ROLES:
            raise ValueError('Escolha ao menos um controle ou indicador válido.')
        if 'entry' in bindings and not authorize_entry:
            raise ValueError('Confirme que o botão escolhido serve apenas para entrar na sala de espera.')
        chosen={}
        for role,index in bindings.items():
            node=snapshot['nodes'].get(index)
            expected='entry' if role=='entry' else 'field' if role in {'quantity','sector'} else 'marker'
            if not node or node['kind']!=expected:
                raise ValueError('O controle selecionado não corresponde à função escolhida.')
            current=await self._candidates(page)
            if page.url!=snapshot['url']:
                raise ValueError('A página mudou durante a validação. Inspecione novamente.')
            if sum(n['kind']==node['kind'] and n['label']==node['label'] for n in current)!=1 or not any(n==node for n in current):
                raise ValueError('Um controle mudou desde a inspeção. Inspecione novamente.')
            chosen[role]=dict(node=node,url=snapshot['url'])
        if page.url!=snapshot['url']:
            raise ValueError('A página mudou durante a validação. Inspecione novamente.')
        # Reconfigurar não libera uma segunda tentativa em um botão já acionado.
        self.rules.update(chosen)
        self.paused=False
        self.snapshot=None
        self.message='Controles reais configurados localmente; automação ativa somente enquanto corresponderem à página verificada.'
        self.store.event('integração','Controles da venda real validados pelo usuário: '+', '.join(sorted(chosen)))
        return {'ok':True}

    async def _candidates(self,page):
        return await page.evaluate(SCAN_JS)

    def _match(self,role,url,nodes):
        rule=self.rules.get(role)
        return rule and rule['url']==url and sum(n['kind']==rule['node']['kind'] and n['label']==rule['node']['label'] for n in nodes)==1 and any(n==rule['node'] for n in nodes)

    async def observe(self,page):
        # Evidência genérica de MFA e desafios visíveis; não tenta resolvê-los.
        mfa=page.locator('input[autocomplete="one-time-code"]:visible')
        if await mfa.count():
            self.message='Código MFA necessário: preencha no próprio site. O acompanhamento continua.'
            return State.HUMAN,'Verificação necessária'
        challenges=page.locator('iframe[src*="recaptcha"][src*="bframe"]:visible, iframe[title*="hCaptcha challenge"]:visible')
        if await challenges.count():
            self.message='Verificação humana visível: conclua no navegador. Nenhum clique automático durante o desafio.'
            return State.HUMAN,'Verificação necessária'
        if not is_eventim(page.url):
            self.message='Página externa à integração validada. Preserve a aba e acompanhe manualmente o redirecionamento oficial.'
            return State.UNKNOWN,'Verificação necessária'
        body=(await page.locator('body').inner_text(timeout=5000))[:200000]
        normalized=' '.join(body.casefold().split())
        if 'não conseguimos encontrar a sua página' in normalized or 'upstream connect error' in normalized:
            self.message='Página indisponível. Confira a URL oficial da venda; não há entrada automática neste estado.'
            return State.ERROR,'Verificação necessária'
        nodes=await self._candidates(page)
        for role,state in [('human',State.HUMAN),('expired',State.EXPIRED),('queue',State.QUEUE),('waiting',State.WAITING),('selection',State.SELECT),('entry',State.WAIT_AVAILABLE)]:
            if self._match(role,page.url,nodes):
                self.message='Estado reconhecido por um indicador configurado nesta página real.'
                return state,'Sessão expirada' if state==State.EXPIRED else 'Verificação necessária'
        self.message='Nenhum indicador validado corresponde à página atual. Verificação manual necessária.'
        return State.UNKNOWN,'Verificação necessária'

    async def step(self,page,state,run_id):
        async with self.action_lock:
            if not self.paused:
                await self._step(page,state,run_id)

    async def _step(self,page,state,run_id):
        roles=['entry'] if state==State.WAIT_AVAILABLE else ['quantity','sector'] if state==State.SELECT else []
        for role in roles:
            rule=self.rules.get(role)
            if not rule:
                continue
            key=(run_id,role,rule['url'],rule['node']['selector'])
            if key in self.attempted:
                continue
            # Nova observação bloqueia ações se apareceu CAPTCHA/MFA, fila ou mudou o DOM.
            observed,_=await self.observe(page)
            nodes=await self._candidates(page)
            if observed!=state or not self._match(role,page.url,nodes):
                continue
            locator=page.locator(rule['node']['selector'])
            if await locator.count()!=1 or not await locator.is_visible() or not await locator.is_enabled():
                continue
            preferences=self.store.get('purchase',{})
            if role!='entry':
                value=str(preferences.get('quantity',4)) if role=='quantity' else next(iter(preferences.get('sectors',[])),'')
                if not value:
                    continue
                if rule['node']['tag']=='select':
                    options=locator.locator('option')
                    matches=[]
                    for i in range(await options.count()):
                        option=options.nth(i)
                        if (await option.inner_text()).strip()==value and not await option.is_disabled():
                            matches.append(i)
                    if len(matches)!=1:
                        self.message='Preferência não disponível de forma inequívoca. Escolha manualmente; nenhuma alternativa foi presumida.'
                        continue
            self.attempted.add(key)
            try:
                if role=='entry':
                    await locator.click(timeout=5000,no_wait_after=True)
                elif rule['node']['tag']=='select':
                    await locator.select_option(index=matches[0],timeout=5000)
                else:
                    await locator.fill(value,timeout=5000)
            except Exception:
                self.message='Ação com resultado incerto. Verifique a aba; não repetiremos automaticamente.'
                self.store.event('falha','Ação na venda real não confirmada: '+role)
                raise
            self.store.event('automação','Ação no controle validado da venda real: '+role+'. Revise o resultado no navegador.')

    def status(self):
        return dict(message=self.message,configured=sorted(self.rules),paused=self.paused,validation='Configuração local por sessão; não equivale a validação independente da Eventim.')
