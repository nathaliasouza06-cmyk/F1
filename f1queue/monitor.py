from enum import StrEnum
from urllib.parse import urlsplit

class State(StrEnum):
    UNKNOWN='Verificação manual necessária'
    AVAILABLE='Página oficial disponível'
    NOT_STARTED='Venda ainda não iniciada'
    WAIT_AVAILABLE='Sala de espera disponível'
    WAITING='Sala de espera acessada'
    QUEUE='Fila virtual ativa'
    TURN='Aguardando sua vez'
    SELECT='Escolha de ingressos liberada'
    EXPIRED='Sessão expirada'
    HUMAN='CAPTCHA ou verificação humana'
    ERROR='Erro de conexão'

PROTECTED={State.UNKNOWN,State.WAITING,State.QUEUE,State.TURN,State.HUMAN,State.SELECT,State.ERROR}

def official_url(value):
    u=urlsplit(value)
    if u.scheme != 'https' or u.hostname not in {'www.eventim.com.br','eventim.com.br'} or u.username or u.password or u.port not in (None,443) or u.fragment:
        raise ValueError('Use uma URL HTTPS oficial da Eventim Brasil, sem credenciais ou fragmentos.')
    return value

async def observe(page, simulator=False):
    # Não há adaptador Eventim validado. Texto isolado não comprova fila ou autenticação.
    if not simulator:
        return State.UNKNOWN, 'Verificação necessária'
    state=await page.locator('body').get_attribute('data-state')
    account=await page.locator('body').get_attribute('data-account')
    try:
        return State(state), account or 'Verificação necessária'
    except ValueError:
        return State.UNKNOWN, 'Verificação necessária'
