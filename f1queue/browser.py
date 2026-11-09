import asyncio
import secrets
from .monitor import State, PROTECTED, observe
from .automation import Automation

class Browser:
    def __init__(self, root, store, notifier):
        self.automation=Automation(store)
        self.root=root
        self.store=store
        self.notifier=notifier
        self.context=None
        self.page=None
        self.driver=None
        self.state=State.UNKNOWN
        self.account='Verificação necessária'
        self.active=False
        self.simulator=False
        self.modality='Eventim'
        self.lock=asyncio.Lock()
        self.run_id=0
        self.recovery_required=store.get('browser_open',False)
    async def open(self, url, simulator=False, acknowledged=False):
        async with self.lock:
            if self.recovery_required and not acknowledged:
                raise ValueError('Execução anterior interrompida. A posição pode ter sido perdida. Confirme a abertura manual no painel.')
            if self.context:
                if self.page.is_closed():
                    raise ValueError('Aba encerrada. Intervenção manual necessária; não recriaremos a sessão.')
                await self.page.bring_to_front()
                if self.page.url != url:
                    raise ValueError('Há uma sessão aberta. Navegue manualmente para preservar sua fila.')
                return
            from playwright.async_api import async_playwright
            self.driver=await async_playwright().start()
            try:
                self.context=await self.driver.chromium.launch_persistent_context(str(self.root/'browser-profile'),headless=False,no_viewport=True,ignore_default_args=['--use-mock-keychain','--password-store=basic'])
                self.page=self.context.pages[0] if self.context.pages else await self.context.new_page()
                self.simulator=simulator
                self.run_id=secrets.token_hex(8)
                self.recovery_required=False
                self.store.set('browser_open',True)
                await self.page.goto(url,wait_until='domcontentloaded',timeout=45000)
                self.active=True
                self.store.event('navegador','Navegador preparado. Faça login manualmente, se necessário.')
            except Exception:
                self.active=False
                self.state=State.ERROR
                self.store.event('falha','Falha ao abrir navegador/página. Sessão não será reiniciada automaticamente.')
                if not self.context:
                    await self.driver.stop()
                    self.driver=None
                raise ValueError('Falha ao abrir navegador ou página; verifique instalação, conexão e navegador visível.')
    async def poll(self):
        if not self.active or not self.page:
            return
        try:
            state, account=await observe(self.page,self.simulator)
            self.account=account
            if state != self.state:
                self.state=state
                self.store.event('estado',str(state))
                await self.notifier.send(f'state:{self.run_id}:{state}',self.modality,str(state))
                if state == State.WAIT_AVAILABLE and not self.simulator:
                    await self.notifier.send(f'manual:{self.run_id}',self.modality,'Entrada manual necessária: fluxo real ainda não validado.')
                if state == State.SELECT:
                    await self.page.bring_to_front()
            await self.automation.step(self.page,state,self.simulator,self.run_id)
        except Exception:
            self.state=State.ERROR
            await self.notifier.send(f'connection:{self.run_id}',self.modality,'Falha de observação ou ação. Verifique o navegador sem atualizar a fila; nenhuma ação incerta será repetida.')
    async def shutdown(self):
        try:
            if self.context:
                # Fechamento explícito do processo não promete recuperar uma fila.
                await self.context.close()
        finally:
            if self.driver:
                await self.driver.stop()
