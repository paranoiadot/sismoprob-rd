"""Tormentas tropicales activas del NHC (NOAA).

El NHC no permite CORS en CurrentStorms.json, así que el navegador no puede
leerlo directo: este módulo lo consulta desde el servidor, lo normaliza a un
formato simple y lo guarda en caché unos minutos.
"""
import time

import requests

NHC_URL = "https://www.nhc.noaa.gov/CurrentStorms.json"
CACHE_SEGUNDOS = 600
_cache = {"ts": 0.0, "datos": None}

CLASIFICACION = {
    "HU": "Huracán",
    "MH": "Huracán mayor",
    "TS": "Tormenta tropical",
    "TD": "Depresión tropical",
    "STS": "Tormenta subtropical",
    "SD": "Depresión subtropical",
    "PTC": "Ciclón potencial",
    "PC": "Ciclón postropical",
    "TY": "Tifón",
}


def categoria_saffir_simpson(viento_kt):
    """Categoría 1–5 a partir del viento sostenido en nudos (0 si no es huracán)."""
    if viento_kt is None:
        return 0
    if viento_kt >= 137:
        return 5
    if viento_kt >= 113:
        return 4
    if viento_kt >= 96:
        return 3
    if viento_kt >= 83:
        return 2
    if viento_kt >= 64:
        return 1
    return 0


def _num(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def normalizar_tormenta(s):
    sid = (s.get("id") or "").lower()  # p. ej. al092026
    viento_kt = _num(s.get("intensity"))
    cono = None
    if len(sid) == 8 and sid[:2] in ("al", "ep", "cp"):
        cuenca = {"al": "AT", "ep": "EP", "cp": "CP"}[sid[:2]]
        cono = (
            f"https://www.nhc.noaa.gov/storm_graphics/{cuenca}{sid[2:4]}/"
            f"{sid.upper()}_5day_cone_with_line_and_wind.png"
        )
    clase = s.get("classification") or ""
    return {
        "id": sid,
        "nombre": s.get("name") or "Sin nombre",
        "clase": clase,
        "clase_texto": CLASIFICACION.get(clase, clase or "Sistema tropical"),
        "categoria": categoria_saffir_simpson(viento_kt) if clase in ("HU", "MH") else 0,
        "viento_kt": viento_kt,
        "viento_kmh": round(viento_kt * 1.852) if viento_kt is not None else None,
        "presion_mb": _num(s.get("pressure")),
        "lat": _num(s.get("latitudeNumeric")),
        "lon": _num(s.get("longitudeNumeric")),
        "movimiento_dir": _num(s.get("movementDir")),
        "movimiento_kmh": round(_num(s.get("movementSpeed")) * 1.609)
        if _num(s.get("movementSpeed")) is not None
        else None,
        "actualizado": s.get("lastUpdate"),
        "cono_img": cono,
        "aviso_url": (s.get("publicAdvisory") or {}).get("url"),
    }


def obtener_tormentas_activas(ahora=None):
    ahora = time.time() if ahora is None else ahora
    if _cache["datos"] is not None and ahora - _cache["ts"] < CACHE_SEGUNDOS:
        return _cache["datos"]
    try:
        r = requests.get(NHC_URL, timeout=10, headers={"User-Agent": "SismoPro RD"})
        if r.status_code != 200:
            raise ValueError(f"HTTP {r.status_code}")
        tormentas = [normalizar_tormenta(s) for s in (r.json().get("activeStorms") or [])]
        datos = {"estado": "exito", "fuente": "NHC/NOAA", "tormentas": tormentas}
    except Exception as e:  # noqa: BLE001 — cualquier fallo de red/JSON
        if _cache["datos"] is not None:
            return _cache["datos"]
        return {"estado": "error", "detalle": str(e), "tormentas": []}
    _cache.update(ts=ahora, datos=datos)
    return datos
