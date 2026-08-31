from datetime import datetime, timezone as dt_timezone

from django.utils import timezone


def dt_now():
    """Timestamp de sistema siempre AWARE (UTC). Usar para TODOS los writes de 'now'."""
    return timezone.now()


def dt_from_timestamp(ts):
    """Convierte un timestamp (float epoch) a datetime AWARE en la TZ activa.

    NOTA: `django.utils.timezone` NO tiene `datetime_from_timestamp` (no existe).
    La forma correcta de construir un datetime aware desde un timestamp es
    `datetime.fromtimestamp(ts, tz=timezone.get_current_timezone())`.
    """
    return datetime.fromtimestamp(ts, tz=timezone.get_current_timezone())


def dt_serialize(value):
    """Serialize un datetime a string sin offset, en hora local de Argentina.

    El frontend (React) consume las fechas como STRINGS NAIVE asumiendo hora local
    de Argentina (helpers en services/formattingDateTime.js: split('T'), split('.'),
    new Date(...) sobre string naive). Por eso NUNCA exponemos offset: el round-trip
    (el frontend arma 'YYYY-MM-DD HH:MM' desde inputs y lo manda sin TZ de vuelta)
    exige que el backend hable naive en hora de Argentina.
    """
    if value is None:
        return None
    aware = value if timezone.is_aware(value) else timezone.make_aware(value)
    local = timezone.localtime(aware)
    return local.replace(tzinfo=None).isoformat()


def dt_parse(value):
    """Parse permissivo de fechas del frontend a datetime AWARE (hora local de Argentina).

    El frontend manda 'YYYY-MM-DD HH:MM[:SS]' SIN offset (hora local del navegador,
    asumida Argentina). También toleramos ISO con 'T' y trailing 'Z' (UTC).
    Devuelve None si no se puede parsear.
    """
    if value is None or value == "":
        return None
    s = str(value).strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    s = s.replace("T", " ")
    parsed = None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            parsed = datetime.strptime(s, fmt)
            break
        except ValueError:
            continue
    if parsed is None:
        try:
            parsed = datetime.fromisoformat(s)
        except ValueError:
            return None
    if timezone.is_aware(parsed):
        return timezone.localtime(parsed)
    return timezone.make_aware(parsed)
