import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timedelta
import httpx
from f1queue.storage import Store
from f1queue.scheduler import TZ, sale_time, due, countdown
from f1queue.app import create_app, Sale
from f1queue.monitor import official_url, State, observe
from f1queue.notifications import Notifier
from f1queue.browser import Browser

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.store=Store(self.root)
    def tearDown(self): self.tmp.cleanup()
    def test_persistence_restart(self):
        self.store.set('example',{'quantity':4})
        self.assertEqual(Store(self.root).get('example'),{'quantity':4})
        self.assertEqual(len(self.store.get('sales')),4)
        self.assertIsNone(sale_time(self.store.get('sales')[2]))
    def test_timezone_schedule_countdown(self):
        sale=self.store.get('sales')[0]
        when=sale_time(sale)
        self.assertEqual(when.utcoffset(),timedelta(hours=-3))
        self.assertEqual(when.hour,12)
        self.assertFalse(due(sale,when-timedelta(minutes=121)))
        self.assertTrue(due(sale,when-timedelta(minutes=120)))
        self.assertEqual(countdown(sale,when-timedelta(minutes=120)),7200)
    def test_urls(self):
        for u in ['http://www.eventim.com.br','https://evil.com','https://www.eventim.com.br.evil.com','https://user@www.eventim.com.br','https://www.eventim.com.br:444/a']:
            with self.assertRaises(ValueError): official_url(u)

class AsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_api_auth_security_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            self.root=Path(directory)
            await self.api_check()

    async def api_check(self):
        app=create_app(self.root)
        async with app.router.lifespan_context(app), httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://testserver') as client:
            self.assertEqual((await client.get('/api/status')).status_code,401)
            token=(self.root/'panel-token').read_text()
            h={'Authorization':'Bearer '+token}
            status=(await client.get('/api/status',headers=h)).json()
            self.assertEqual(status['account'],'Verificação necessária')
            self.assertEqual((await client.put('/api/sales',headers=h,json=status['sales'])).status_code,200)
            invalid=status['sales'];invalid[0]['time']='25:99'
            self.assertEqual((await client.put('/api/sales',headers=h,json=invalid)).status_code,422)
            self.assertEqual((await client.post('/api/action',headers={**h,'Origin':'https://evil.com'},json={'action':'stop'})).status_code,403)
            self.assertEqual((await client.get('/',headers={'Host':'evil.com'})).status_code,403)
            self.assertEqual((await client.post('/api/action',headers=h,json={'action':'start'})).status_code,409)
            self.assertEqual((await client.get('/sim/')).status_code,200)
        self.assertTrue((self.root/'diagnostic.jsonl').exists())

    async def test_login_uses_official_home_independent_of_sale(self):
        from unittest.mock import AsyncMock
        with tempfile.TemporaryDirectory() as d:
            app=create_app(Path(d))
            async with app.router.lifespan_context(app), httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://testserver') as client:
                app.state.store.set('sales',[])
                app.state.browser.open=AsyncMock()
                headers={'Authorization':'Bearer '+app.state.token}
                response=await client.post('/api/action',headers=headers,json={'action':'login','acknowledge':True})
                self.assertEqual(response.status_code,200)
                app.state.browser.open.assert_awaited_once_with('https://www.eventim.com.br/',False,True)

    async def test_notification_dedup(self):
        with tempfile.TemporaryDirectory() as d:
            s=Store(Path(d));n=Notifier(s)
            self.assertTrue(await n.send('same','Simulação','Teste'))
            self.assertFalse(await n.send('same','Simulação','Teste'))
            self.assertEqual(len(s.history()),1)
    async def test_monitor_simulated_states(self):
        class Locator:
            async def get_attribute(self,name): return self.values.get(name)
        class Page:
            def locator(self,_): return self.loc
        p=Page();p.loc=Locator()
        for state in State:
            p.loc.values={'data-state':state.value,'data-account':'Conta conectada'}
            self.assertEqual(await observe(p,True),(state,'Conta conectada'))
        self.assertEqual(await observe(p,False),(State.UNKNOWN,'Verificação necessária'))
    async def test_scheduler_prepares_once_at_120_minutes(self):
        from types import SimpleNamespace
        from unittest.mock import AsyncMock, patch
        from f1queue.app import scheduler
        import asyncio
        with tempfile.TemporaryDirectory() as d:
            store=Store(Path(d))
            sale=store.get('sales')[0]
            sale['confirmation']='Confirmado oficialmente'
            store.set('sales',[sale])
            now=sale_time(sale)-timedelta(minutes=120)
            browser=SimpleNamespace(open=AsyncMock(),poll=AsyncMock(),modality='')
            app=SimpleNamespace(state=SimpleNamespace(store=store,browser=browser,notifier=Notifier(store)))
            calls=0
            async def sleep(_):
                nonlocal calls
                calls+=1
                if calls>=2: raise asyncio.CancelledError()
            with patch('f1queue.app.datetime') as clock, patch('f1queue.app.asyncio.sleep',sleep):
                clock.now.return_value=now
                with self.assertRaises(asyncio.CancelledError): await scheduler(app)
            browser.open.assert_awaited_once_with(sale['url'])
            self.assertEqual(browser.poll.await_count,2)

    async def test_open_session_never_replaces_page(self):
        from types import SimpleNamespace
        from unittest.mock import AsyncMock, Mock
        with tempfile.TemporaryDirectory() as d:
            store=Store(Path(d))
            browser=Browser(Path(d),store,Notifier(store))
            browser.context=object()
            page=SimpleNamespace(is_closed=Mock(return_value=False),bring_to_front=AsyncMock(),url='https://www.eventim.com.br/existing-queue')
            browser.page=page
            with self.assertRaisesRegex(ValueError,'sessão aberta'):
                await browser.open('https://www.eventim.com.br/new-sale')
            self.assertIs(browser.page,page)
            page.bring_to_front.assert_awaited_once()

    async def test_browser_launch_failure_reports_safe_reason(self):
        from types import SimpleNamespace
        from unittest.mock import AsyncMock, Mock, patch
        with tempfile.TemporaryDirectory() as d:
            store=Store(Path(d))
            driver=SimpleNamespace(chromium=SimpleNamespace(launch_persistent_context=AsyncMock(side_effect=Exception("Executable doesn't exist at /Users/private/session-secret"))),stop=AsyncMock())
            manager=SimpleNamespace(start=AsyncMock(return_value=driver))
            browser=Browser(Path(d),store,Notifier(store))
            with patch('playwright.async_api.async_playwright',return_value=manager):
                with self.assertRaisesRegex(ValueError,'CHROMIUM_AUSENTE'):
                    await browser.open('https://www.eventim.com.br')
            self.assertNotIn('session-secret',str(store.history()))
            self.assertIsNone(browser.driver)
            self.assertFalse(browser.active)
            driver.stop.assert_awaited_once()

    async def test_recovery_acknowledgment_opens_single_context(self):
        from types import SimpleNamespace
        from unittest.mock import AsyncMock, patch
        with tempfile.TemporaryDirectory() as d:
            store=Store(Path(d))
            store.set('browser_open',True)
            page=SimpleNamespace(goto=AsyncMock())
            context=SimpleNamespace(pages=[page])
            driver=SimpleNamespace(chromium=SimpleNamespace(launch_persistent_context=AsyncMock(return_value=context)))
            manager=SimpleNamespace(start=AsyncMock(return_value=driver))
            browser=Browser(Path(d),store,Notifier(store))
            with patch('playwright.async_api.async_playwright',return_value=manager):
                await browser.open('http://127.0.0.1:8765/sim/',True,True)
            self.assertFalse(browser.recovery_required)
            self.assertTrue(browser.active)
            driver.chromium.launch_persistent_context.assert_awaited_once()
            page.goto.assert_awaited_once()

    async def test_restart_guard(self):
        with tempfile.TemporaryDirectory() as d:
            s=Store(Path(d));s.set('browser_open',True)
            b=Browser(Path(d),s,Notifier(s))
            with self.assertRaisesRegex(ValueError,'interrompida'):
                await b.open('https://www.eventim.com.br')

if __name__=='__main__': unittest.main()
