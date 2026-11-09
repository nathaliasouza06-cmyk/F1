import asyncio
import contextlib
import hmac
import json
import os
import secrets
import logging
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from .storage import Store, URL
from .scheduler import TZ, due, sale_time, countdown
from .monitor import official_url
from .browser import Browser
from .notifications import Notifier

ROOT=Path(os.environ.get('F1_DATA_DIR',str(Path.home()/'Library/Application Support/F1 Queue Assistant')))
ASSETS=Path(__file__).parent
PORT=int(os.environ.get('F1_PORT','8765'))

class Sale(BaseModel):
    id: str=Field(min_length=1,max_length=80,pattern=r'^[a-zA-Z0-9_-]+$')
    name: str=Field(min_length=1,max_length=100)
    date: str
    time: str | None=None
    confirmation: str
    url: str
    lead: int=Field(default=120,ge=0,le=1440)
    @field_validator('url')
    @classmethod
    def url_check(cls,v): return official_url(v)
    @field_validator('confirmation')
    @classmethod
    def confirmation_check(cls,v):
        if v not in {'Confirmado oficialmente','Previsto','Aguardando confirmação'}: raise ValueError('Estado inválido')
        return v
    @field_validator('date')
    @classmethod
    def date_check(cls,v):
        from datetime import date
        date.fromisoformat(v)
        return v
    @field_validator('time')
    @classmethod
    def time_check(cls,v):
        if v is not None:
            import re
            if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',v): raise ValueError('Use HH:MM')
        return v

class Purchase(BaseModel):
    quantity: int=Field(default=4,ge=1,le=10)
    sector: str=Field(default='',max_length=100)

class Action(BaseModel):
    action: str
    sale_id: str='1'
    acknowledge: bool=False

async def scheduler(app):
    while True:
        try:
            now=datetime.now(TZ)
            app.state.heartbeat=now.isoformat()
            simulation=app.state.store.get('simulation')
            if simulation and due(simulation,now) and app.state.store.once('sim-prepare:'+simulation['id']):
                app.state.browser.modality='VENDA SIMULADA'
                try:
                    await app.state.browser.open(f'http://127.0.0.1:{PORT}/sim/',True)
                    await app.state.notifier.send('sim-ready:'+simulation['id'],'VENDA SIMULADA','Preparação de teste iniciada 120 minutos antes da venda fictícia.')
                except ValueError as exc:
                    await app.state.notifier.send('sim-blocked:'+simulation['id'],'VENDA SIMULADA',str(exc))
            for sale in app.state.store.get('sales',[]):
                when=sale_time(sale)
                if when is None: continue
                identity=f"{sale['id']}:{when.isoformat()}"
                for minutes in (120,60,30,15,5,0):
                    seconds=(when-now).total_seconds()
                    if minutes*60-60 < seconds <= minutes*60:
                        await app.state.notifier.send(f'{identity}:reminder:{minutes}',sale['name'],f'{minutes} minutos até o horário cadastrado ({sale["confirmation"]}).')
                # Automação temporal só para horários explicitamente confirmados pelo usuário.
                if sale['confirmation']=='Confirmado oficialmente' and due(sale,now):
                    if app.state.store.once(f'{identity}:prepare:{sale["lead"]}'):
                        app.state.browser.modality=sale['name']
                        try:
                            await app.state.browser.open(sale['url'])
                            await app.state.notifier.send(f'{identity}:prepared',sale['name'],'Preparação iniciada. Verifique login e página oficial.')
                        except ValueError as exc:
                            await app.state.notifier.send(f'{identity}:blocked',sale['name'],str(exc))
            await app.state.browser.poll()
        except Exception:
            app.state.store.event('falha','Falha no ciclo do agendador. Verifique o painel.')
        await asyncio.sleep(10)

def create_app(root=ROOT):
    @asynccontextmanager
    async def lifespan(app):
        os.umask(0o077)
        app.state.store=Store(root)
        app.state.notifier=Notifier(app.state.store)
        app.state.browser=Browser(root,app.state.store,app.state.notifier)
        app.state.token=secrets.token_urlsafe(32)
        token_file=root/'panel-token'
        token_file.write_text(app.state.token)
        token_file.chmod(0o600)
        app.state.heartbeat=None
        app.state.store.event('sistema','Aplicativo iniciado. A recuperação de posição na fila não é garantida.')
        task=asyncio.create_task(scheduler(app))
        yield
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError): await task
        await app.state.browser.shutdown()
        app.state.store.event('sistema','Aplicativo encerrado; posição de fila não é recuperada automaticamente.')
    app=FastAPI(title='F1 QUEUE ASSISTANT 2027',lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None)
    @app.middleware('http')
    async def security(request,call_next):
        host=request.headers.get('host','')
        if host not in {f'127.0.0.1:{PORT}',f'localhost:{PORT}','testserver'}:
            return JSONResponse({'detail':'Host não permitido'},status_code=403)
        if request.url.path.startswith('/api/'):
            token=request.headers.get('authorization','').removeprefix('Bearer ')
            if not hmac.compare_digest(token,request.app.state.token):
                return JSONResponse({'detail':'Autenticação necessária'},status_code=401)
            origin=request.headers.get('origin')
            if origin and origin not in {f'http://127.0.0.1:{PORT}',f'http://localhost:{PORT}'}:
                return JSONResponse({'detail':'Origem não permitida'},status_code=403)
        response=await call_next(request)
        response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        return response
    @app.get('/')
    async def index(): return FileResponse(ASSETS/'static/index.html')
    app.mount('/static',StaticFiles(directory=ASSETS/'static'),name='static')
    app.mount('/sim',StaticFiles(directory=ASSETS/'sim',html=True),name='sim')
    @app.get('/api/status')
    async def status():
        b=app.state.browser
        now=datetime.now(TZ)
        sales=app.state.store.get('sales')
        upcoming=sorted([s for s in sales if sale_time(s) and countdown(s,now)>=0],key=sale_time)
        return dict(now=now.isoformat(),sales=sales,next=upcoming[0] if upcoming else None,account=b.account,browser='Aberto' if b.context else 'Fechado',state=b.state,active=b.active,recovery_required=b.recovery_required,heartbeat=app.state.heartbeat,history=app.state.store.history(),purchase=app.state.store.get('purchase'),notifications=app.state.store.get('notifications'),integration='Eventim: adaptador não validado; entrada e verificação manuais. Web Push não configurado.')
    @app.put('/api/sales')
    async def save_sales(sales:list[Sale]):
        if len(sales)>50 or len({s.id for s in sales})!=len(sales): raise HTTPException(422,'IDs duplicados ou calendário muito grande')
        app.state.store.set('sales',[s.model_dump() for s in sales])
        app.state.store.event('configuração','Calendário atualizado')
        return {'ok':True}
    @app.put('/api/purchase')
    async def purchase(body:Purchase):
        preferences=app.state.store.get('purchase',{})
        preferences.update(quantity=body.quantity,sectors=[body.sector] if body.sector else [])
        app.state.store.set('purchase',preferences)
        app.state.store.event('configuração','Preferências de quantidade e setor atualizadas.')
        return {'ok':True}
    @app.post('/api/action')
    async def action(body:Action):
        b=app.state.browser
        try:
            if body.action=='schedule_simulation':
                when=datetime.now(TZ)+timedelta(minutes=122)
                app.state.store.set('simulation',dict(id=secrets.token_hex(8),date=when.date().isoformat(),time=when.strftime('%H:%M'),lead=120))
                app.state.store.event('simulação','Preparação simulada agendada para daqui a 1–2 minutos. Venda fictícia 120 minutos depois da preparação.')
            elif body.action=='simulate':
                b.modality='VENDA SIMULADA'
                await b.open(f'http://127.0.0.1:{PORT}/sim/',True,body.acknowledge)
            elif body.action=='login':
                b.modality='Minha Conta Eventim'
                await b.open('https://www.eventim.com.br/',False,body.acknowledge)
            elif body.action in {'prepare','open'}:
                sale=next((s for s in app.state.store.get('sales') if s['id']==body.sale_id),None)
                if not sale: raise ValueError('Modalidade não encontrada')
                b.modality=sale['name']
                await b.open(official_url(sale['url']),False,body.acknowledge)
            elif body.action=='check':
                if not b.page: raise ValueError('Abra o navegador primeiro')
                await b.poll()
                await b.page.bring_to_front()
            elif body.action=='start':
                if not b.page or b.page.is_closed(): raise ValueError('Prepare o navegador primeiro')
                b.active=True
            elif body.action=='stop':
                b.active=False
                app.state.store.event('monitor','Observação pausada; navegador permanece aberto.')
            elif body.action=='notify':
                await app.state.notifier.send(f'test:{secrets.token_hex(4)}','TESTE','Notificações do F1 Queue Assistant')
            else: raise ValueError('Ação desconhecida')
        except ValueError as exc: raise HTTPException(409,str(exc))
        return {'ok':True}
    @app.put('/api/notifications')
    async def notifications(enabled:bool):
        app.state.store.set('notifications',enabled)
        return {'ok':True}
    return app

app=create_app()
