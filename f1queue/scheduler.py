from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo('America/Sao_Paulo')

def sale_time(sale):
    if not sale.get('time'):
        return None
    return datetime.fromisoformat(f"{sale['date']}T{sale['time']}").replace(tzinfo=TZ)

def countdown(sale, now):
    when = sale_time(sale)
    return None if when is None else int((when-now).total_seconds())

def due(sale, now):
    when = sale_time(sale)
    return when is not None and when-timedelta(minutes=sale['lead']) <= now <= when+timedelta(hours=6)
