import asyncio
import sys

class Notifier:
    def __init__(self, store):
        self.store=store
    async def send(self, key, modality, reason):
        if not self.store.once(key):
            return False
        self.store.event('alerta', f'{modality}: {reason}')
        if self.store.get('notifications', True) and sys.platform == 'darwin':
            # Argumentos separados: conteúdo jamais interpolado em AppleScript.
            script='on run argv\ndisplay notification (item 2 of argv) with title (item 1 of argv) sound name "Glass"\nend run'
            try:
                proc=await asyncio.create_subprocess_exec('/usr/bin/osascript','-e',script,modality,reason,stdout=asyncio.subprocess.DEVNULL,stderr=asyncio.subprocess.DEVNULL)
                await proc.wait()
                if proc.returncode:
                    self.store.event('falha','Notificação macOS não entregue; consulte o painel.')
            except OSError:
                self.store.event('falha','Notificação macOS indisponível; consulte o painel.')
        return True
