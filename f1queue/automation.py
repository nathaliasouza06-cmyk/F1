"""Ações no DOM validado. Nenhum seletor real da Eventim é presumido."""
from urllib.parse import urlsplit
from .monitor import State

class Automation:
    def __init__(self, store):
        self.store=store
        self.attempted=set()

    async def step(self, page, state, simulator, run_id):
        url=urlsplit(page.url)
        if not simulator or url.scheme != 'http' or url.hostname != '127.0.0.1' or not url.path.startswith('/sim/'):
            return 'Fluxo real ainda não validado; ação manual necessária.'
        if state in {State.HUMAN,State.EXPIRED,State.UNKNOWN,State.ERROR}:
            return 'Intervenção necessária. Resolva a verificação no navegador; o acompanhamento continua.'
        key=(run_id,state)
        if key in self.attempted:
            return None
        if state == State.WAIT_AVAILABLE:
            # Registra ANTES do clique para não repetir uma entrada cujo resultado seja incerto.
            self.attempted.add(key)
            await page.get_by_role('button',name='Entrar manualmente',exact=True).click(timeout=5000)
            self.store.event('automação','Entrada realizada pelo botão da sala simulada; aguardando confirmação do estado.')
        elif state == State.SELECT:
            self.attempted.add(key)
            preference=self.store.get('purchase',{})
            await page.get_by_label('Quantidade de ingressos',exact=True).fill(str(preference.get('quantity',4)))
            sector=next(iter(preference.get('sectors',[])),None)
            if sector:
                await page.get_by_label('Setor prioritário',exact=True).fill(sector)
            self.store.event('automação','Preferências preenchidas no simulador. Revise antes de continuar; nenhuma compra foi confirmada.')
        return None
