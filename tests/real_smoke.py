"""Playwright sobre HTML local interceptado no domínio virtual. Não acessa a Eventim."""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.async_api import async_playwright
from f1queue.real import RealAdapter
from f1queue.monitor import State
from f1queue.storage import Store

async def main():
    fixture=(Path(__file__).resolve().parents[1]/'f1queue/sim/real-fixture.html').read_text()
    with tempfile.TemporaryDirectory() as d:
        store=Store(Path(d));store.set('purchase',{'quantity':4,'sectors':['Setor A']})
        adapter=RealAdapter(store)
        async with async_playwright() as p:
            args={'headless':True}
            if os.environ.get('F1_TEST_CHROMIUM'):args['executable_path']=os.environ['F1_TEST_CHROMIUM']
            browser=await p.chromium.launch(**args)
            page=await browser.new_page()
            async def local(route):
                await route.fulfill(content_type='text/html',body='<p>Desafio local</p>' if 'bframe' in route.request.url else fixture)
            # Todas as requisições são interceptadas; nenhum endpoint externo é acessado.
            await page.route('**/*',local)
            await page.goto('https://www.eventim.com.br/evento-fixture-2027')
            scan=await adapter.scan(page)
            assert 'NAO-LER' not in str(scan)
            assert not any('Pagar' in c['label'] or 'Confirmar' in c['label'] for c in scan['candidates'])
            choose=lambda scan,label:next(c['id'] for c in scan['candidates'] if c['label']==label)
            binding={'entry':choose(scan,'Acessar sala de espera')}
            try:
                await adapter.configure(page,scan['scan_id'],binding,False)
                raise AssertionError('Consentimento de entrada deveria ser exigido')
            except ValueError:pass
            await adapter.configure(page,scan['scan_id'],binding,True)
            assert (await adapter.observe(page))[0]==State.WAIT_AVAILABLE
            await page.locator('#verification').evaluate('(e)=>e.hidden=false')
            assert (await adapter.observe(page))[0]==State.HUMAN
            await adapter.step(page,State.WAIT_AVAILABLE,'run')
            assert await page.evaluate('counts.entries')==0
            await page.locator('#verification').evaluate('(e)=>e.hidden=true')
            await asyncio.gather(adapter.step(page,State.WAIT_AVAILABLE,'run'),adapter.step(page,State.WAIT_AVAILABLE,'run'))
            assert await page.evaluate('counts.entries')==1
            scan=await adapter.scan(page)
            await adapter.configure(page,scan['scan_id'],{'waiting':choose(scan,'Você está na sala de espera')})
            assert (await adapter.observe(page))[0]==State.WAITING
            await adapter.step(page,State.WAITING,'run')
            await page.evaluate("phase('queue')")
            scan=await adapter.scan(page)
            await adapter.configure(page,scan['scan_id'],{'queue':choose(scan,'Você está na fila virtual')})
            assert (await adapter.observe(page))[0]==State.QUEUE
            await page.evaluate("phase('selection')")
            scan=await adapter.scan(page)
            await adapter.configure(page,scan['scan_id'],{'selection':choose(scan,'Escolha seus ingressos'),'quantity':choose(scan,'Quantidade de ingressos'),'sector':choose(scan,'Setor prioritário')})
            assert (await adapter.observe(page))[0]==State.SELECT
            await asyncio.gather(adapter.step(page,State.SELECT,'run'),adapter.step(page,State.SELECT,'run'))
            assert await page.locator('#quantity').input_value()=='4'
            assert await page.locator('#sector').input_value()=='Setor A'
            assert await page.evaluate('counts.quantity')==1
            assert await page.evaluate('counts.sector')==1
            await page.locator('#quantity').fill('2')
            await adapter.step(page,State.SELECT,'run')
            assert await page.locator('#quantity').input_value()=='2'
            # Um setor inexistente nunca é substituído por outra preferência silenciosamente.
            other=RealAdapter(store);store.set('purchase',{'quantity':4,'sectors':['Setor inexistente']})
            scan=await other.scan(page)
            await other.configure(page,scan['scan_id'],{'selection':choose(scan,'Escolha seus ingressos'),'sector':choose(scan,'Setor prioritário')})
            await other.step(page,State.SELECT,'other')
            assert await page.locator('#sector').input_value()=='Setor A'
            assert 'não disponível' in other.message
            # Mudanças de DOM e URL invalidam as ações, mesmo no mesmo domínio.
            stale=RealAdapter(store);scan=await stale.scan(page)
            await stale.configure(page,scan['scan_id'],{'selection':choose(scan,'Escolha seus ingressos'),'quantity':choose(scan,'Quantidade de ingressos')})
            await page.locator('#quantity').evaluate("el=>el.parentElement.firstChild.textContent='Preço máximo '")
            await stale.step(page,State.SELECT,'stale')
            assert await page.locator('#quantity').input_value()=='2'
            await page.evaluate("history.pushState({},'', '?queue=NAO-PERSISTIR-TOKEN')")
            assert (await adapter.observe(page))[0]==State.UNKNOWN
            assert RealAdapter(store).status()['configured']==[]
            # Um desafio visível bloqueia ações, sem tocar no iframe ou em seu conteúdo.
            await page.evaluate("()=>{const f=document.createElement('iframe');f.src='/recaptcha/api2/bframe';document.body.append(f)}")
            assert (await adapter.observe(page))[0]==State.HUMAN
            assert await page.evaluate('counts.orders')==0
            assert 'NAO-' not in str(store.history())
            await page.goto('https://untrusted.invalid/fixture')
            try:
                await adapter.scan(page)
                raise AssertionError('Domínio externo deveria ser rejeitado')
            except ValueError:pass
            await browser.close()
    print('PASS: adaptador real configurável, consentimento, entrada única concorrente, sala/fila/seleção, preenchimento, pausa MFA/CAPTCHA, DOM/URL alterados, privacidade, setor indisponível e nenhuma compra enviada. Somente fixtures locais.')

if __name__=='__main__':asyncio.run(main())
