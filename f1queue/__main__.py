import os
import sys
import socket
import threading
import time
import webbrowser
from .app import ROOT, PORT

def main():
    ROOT.mkdir(parents=True,exist_ok=True,mode=0o700)
    # Impede dois processos de controlarem o mesmo perfil SQLite/Chromium.
    import fcntl
    lock=(ROOT/'instance.lock').open('w')
    try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        token_file=ROOT/'panel-token'
        if token_file.exists():
            webbrowser.open(f'http://127.0.0.1:{PORT}/#token='+token_file.read_text().strip())
        print('O aplicativo já está em execução. Painel aberto.')
        return
    def panel():
        token_file=ROOT/'panel-token'
        for _ in range(120):
            time.sleep(.5)
            try:
                with socket.create_connection(('127.0.0.1',PORT),timeout=.2): pass
                token=token_file.read_text().strip()
                webbrowser.open(f'http://127.0.0.1:{PORT}/#token={token}')
                return
            except OSError: pass
    if '--no-open' not in sys.argv: threading.Thread(target=panel,daemon=True).start()
    import uvicorn
    uvicorn.run('f1queue.app:app',host='127.0.0.1',port=PORT,access_log=False)

if __name__=='__main__': main()
