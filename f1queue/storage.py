import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

URL = 'https://www.eventim.com.br/f1saopaulo'

class Store:
    def __init__(self, root: Path):
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = root / 'assistant.sqlite3'
        self.log_path = root / 'diagnostic.jsonl'
        with self.connect() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, at TEXT, kind TEXT, message TEXT);
            CREATE TABLE IF NOT EXISTS notices (key TEXT PRIMARY KEY);''')
        self.path.chmod(0o600)
        if self.get('sales') is None:
            self.set('sales', [dict(id=str(i), name=name, date=date, time=time, confirmation=status, url=URL, lead=120) for i,name,date,time,status in [
                (1,'PORTO BANK','2026-11-09','12:00','Aguardando confirmação'),
                (2,'AMERICAN EXPRESS','2026-11-12','12:00','Aguardando confirmação'),
                (3,'SALA DE ESPERA — VENDA GERAL','2026-11-16',None,'Previsto'),
                (4,'VENDA GERAL','2026-11-16',None,'Previsto')]])
            self.set('purchase', {'quantity':4, 'sectors':[], 'budget':None, 'per_ticket':None, 'tickets':[], 'presale':'', 'payment':''})
            self.set('notifications', True)
    def connect(self):
        return sqlite3.connect(self.path)
    def get(self, key, default=None):
        with self.connect() as db:
            row = db.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
        return json.loads(row[0]) if row else default
    def set(self, key, value):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',(key,json.dumps(value)))
    def event(self, kind, message):
        at = datetime.now(timezone.utc).isoformat()
        with self.connect() as db:
            db.execute('INSERT INTO events(at,kind,message) VALUES (?,?,?)',(at,kind,message))
        event = dict(at=at,kind=kind,message=message)
        with self.log_path.open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(event,ensure_ascii=False)+'\n')
        self.log_path.chmod(0o600)
        return event
    def history(self):
        with self.connect() as db:
            return [dict(id=r[0],at=r[1],kind=r[2],message=r[3]) for r in db.execute('SELECT * FROM events ORDER BY id DESC LIMIT 200')]
    def once(self, key):
        with self.connect() as db:
            return db.execute('INSERT OR IGNORE INTO notices VALUES (?)',(key,)).rowcount == 1
