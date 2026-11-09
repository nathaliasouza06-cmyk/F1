"""Instala serviço opcional por usuário, com caminhos escapados por plistlib."""
import os
import plistlib
import subprocess
import sys
from pathlib import Path

if sys.platform != 'darwin':
    raise SystemExit('Este instalador requer macOS.')
project=Path(__file__).resolve().parents[1]
root=Path.home()/'Library/Application Support/F1 Queue Assistant'
root.mkdir(parents=True,exist_ok=True,mode=0o700)
folder=Path.home()/'Library/LaunchAgents'
folder.mkdir(parents=True,exist_ok=True)
path=folder/'br.local.f1queue.plist'
config={'Label':'br.local.f1queue','ProgramArguments':[str(project/'.venv/bin/python'),'-m','f1queue','--no-open'],'WorkingDirectory':str(project),'RunAtLoad':True,'KeepAlive':True,'ThrottleInterval':30,'StandardOutPath':str(root/'service.log'),'StandardErrorPath':str(root/'service-error.log')}
path.write_bytes(plistlib.dumps(config))
subprocess.run(['launchctl','bootout',f'gui/{os.getuid()}',str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(['launchctl','bootstrap',f'gui/{os.getuid()}',str(path)],check=True)
print('Serviço instalado. Para abrir o painel, use Abrir Painel.command. Não mova a pasta do projeto.')
