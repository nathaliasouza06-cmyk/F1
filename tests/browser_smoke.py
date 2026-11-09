"""Teste de integração local: servidor real, dashboard e perfil Chromium persistente."""
import asyncio
import os
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.async_api import async_playwright
from f1queue.monitor import observe, State
from f1queue.automation import Automation
from f1queue.storage import Store

async def main():
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        server=subprocess.Popen([sys.executable,'-m','f1queue','--no-open'],env={**os.environ,'F1_DATA_DIR':directory,'F1_PORT':str(port)},stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            for _ in range(100):
                if (root/'panel-token').exists(): break
                if server.poll() is not None: raise RuntimeError(server.stderr.read().decode())
                await asyncio.sleep(.1)
            token=(root/'panel-token').read_text()
            async with async_playwright() as p:
                args={'headless':True}
                if os.environ.get('F1_TEST_CHROMIUM'): args['executable_path']=os.environ['F1_TEST_CHROMIUM']
                context=await p.chromium.launch_persistent_context(str(root/'test-profile'),**args)
                page=await context.new_page()
                errors=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                async def recovering(route):
                    response=await route.fetch()
                    status=await response.json()
                    status['recovery_required']=True
                    await route.fulfill(response=response,json=status)
                actions=[]
                async def fail_action(route):
                    actions.append(route.request.post_data_json)
                    await route.fulfill(status=409,json={'detail':'CHROMIUM_AUSENTE: teste de diagnóstico'})
                await page.route('**/api/status',recovering)
                await page.route('**/api/action',fail_action)
                await page.goto(f'http://127.0.0.1:{port}/#token={token}')
                await page.get_by_text('MAC CONECTADO',exact=False).wait_for()
                await page.get_by_role('button',name='Minha Conta',exact=True).click()
                assert await page.locator('#recovery').is_visible()
                await page.get_by_role('button',name='Abrir login manual',exact=True).click()
                assert not actions
                await page.locator('#ack').check()
                await page.get_by_role('button',name='Abrir login manual',exact=True).click()
                await page.get_by_text('CHROMIUM_AUSENTE: teste de diagnóstico',exact=True).wait_for()
                assert actions[-1]['acknowledge'] is True
                await page.evaluate('refresh()')
                assert await page.locator('#notice').inner_text()=='CHROMIUM_AUSENTE: teste de diagnóstico'
                await page.unroute('**/api/status',recovering)
                await page.unroute('**/api/action',fail_action)
                await page.evaluate('refresh()')
                assert await page.locator('#recovery').is_hidden()
                assert not await page.locator('#ack').is_checked()
                await page.get_by_role('button',name='Calendário de Vendas',exact=True).click()
                assert await page.locator('.sale').count()==4
                await page.get_by_role('button',name='Salvar calendário',exact=True).click()
                await page.get_by_text('Calendário salvo.',exact=True).wait_for()
                await page.set_viewport_size({'width':390,'height':844})
                assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                await page.screenshot(path=str(Path(__file__).resolve().parents[1]/'tests/dashboard-mobile.png'),full_page=True)
                sim=await context.new_page()
                await sim.goto(f'http://127.0.0.1:{port}/sim/')
                await sim.get_by_role('button',name='Login manual simulado',exact=True).click()
                assert (await observe(sim,True))[1]=='Conta conectada'
                for button,state in [('Abrir sala de espera',State.WAIT_AVAILABLE),('Entrar manualmente',State.WAITING),('Ativar fila',State.QUEUE),('Aguardar sua vez',State.TURN),('Liberar ingressos',State.SELECT),('Expirar sessão',State.EXPIRED),('CAPTCHA simulado',State.HUMAN)]:
                    await sim.get_by_role('button',name=button,exact=True).click()
                    assert (await observe(sim,True))[0]==state
                store=Store(root/'automation-test')
                store.set('purchase',{'quantity':3,'sectors':['Setor teste']})
                automation=Automation(store)
                await sim.get_by_role('button',name='Abrir sala de espera',exact=True).click()
                await automation.step(sim,State.WAIT_AVAILABLE,True,'test-run')
                assert (await observe(sim,True))[0]==State.WAITING
                await sim.get_by_role('button',name='CAPTCHA simulado',exact=True).click()
                await automation.step(sim,State.HUMAN,True,'test-run')
                assert (await observe(sim,True))[0]==State.HUMAN
                await sim.get_by_role('button',name='Liberar ingressos',exact=True).click()
                await automation.step(sim,State.SELECT,True,'test-run')
                assert await sim.get_by_label('Quantidade de ingressos',exact=True).input_value()=='3'
                assert await sim.get_by_label('Setor prioritário',exact=True).input_value()=='Setor teste'
                await sim.get_by_label('Quantidade de ingressos',exact=True).fill('2')
                await automation.step(sim,State.SELECT,True,'test-run')
                assert await sim.get_by_label('Quantidade de ingressos',exact=True).input_value()=='2'
                await sim.get_by_role('button',name='Login manual simulado',exact=True).click()
                await context.close()
                context=await p.chromium.launch_persistent_context(str(root/'test-profile'),**args)
                page=await context.new_page()
                await page.goto(f'http://127.0.0.1:{port}/sim/')
                assert (await observe(page,True))[1]=='Conta conectada'
                await context.close()
                assert not errors,errors
                print('PASS: confirmação global, erro preservado após atualização, dashboard, calendário, layout iPhone, 7 estados, login e perfil persistente. entrada automática simulada, preenchimento, pausa CAPTCHA e deduplicação. Sem acesso Eventim.')
        finally:
            server.terminate()
            try: server.wait(timeout=15)
            except subprocess.TimeoutExpired: server.kill();server.wait()

if __name__=='__main__': asyncio.run(main())
