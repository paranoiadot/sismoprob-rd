from unittest.mock import Mock, patch

import ciclones_nhc
from ciclones_nhc import categoria_saffir_simpson, obtener_tormentas_activas


def _reset():
    ciclones_nhc._cache.update(ts=0.0, datos=None)


def test_categoria_saffir_simpson():
    assert categoria_saffir_simpson(50) == 0
    assert categoria_saffir_simpson(64) == 1
    assert categoria_saffir_simpson(100) == 3
    assert categoria_saffir_simpson(140) == 5


def test_normaliza_tormentas_y_arma_url_del_cono():
    _reset()
    resp = Mock(status_code=200)
    resp.json.return_value = {"activeStorms": [{
        "id": "al092026", "name": "Ivo", "classification": "HU", "intensity": "100",
        "pressure": "960", "latitudeNumeric": 17.2, "longitudeNumeric": -65.1,
        "movementDir": 285, "movementSpeed": 12, "lastUpdate": "2026-10-02T21:00:00.000Z",
    }]}
    with patch("ciclones_nhc.requests.get", return_value=resp):
        datos = obtener_tormentas_activas(ahora=1000)
    t = datos["tormentas"][0]
    assert datos["estado"] == "exito"
    assert t["nombre"] == "Ivo" and t["categoria"] == 3
    assert t["viento_kmh"] == 185
    assert t["cono_img"].endswith("/AT09/AL092026_5day_cone_with_line_and_wind.png")


def test_falla_de_red_devuelve_lista_vacia():
    _reset()
    with patch("ciclones_nhc.requests.get", side_effect=OSError("sin red")):
        datos = obtener_tormentas_activas(ahora=1000)
    assert datos["estado"] == "error" and datos["tormentas"] == []
