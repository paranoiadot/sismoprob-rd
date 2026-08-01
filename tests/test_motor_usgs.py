from unittest.mock import Mock, patch

from motor_usgs import (
    calcular_probabilidades_bayes_poisson,
    calcular_valor_b,
    obtener_sismos_caribe,
)


def _feature(mag, lon, lat, place="Test", time_ms=1_700_000_000_000, status="reviewed"):
    return {
        "properties": {"mag": mag, "place": place, "time": time_ms, "status": status},
        "geometry": {"coordinates": [lon, lat]},
    }


def test_obtener_sismos_caribe_filtra_por_magnitud_y_bounding_box():
    geojson = {
        "features": [
            _feature(4.5, -70.0, 18.5),  # dentro de la caja, magnitud suficiente
            _feature(2.0, -70.0, 18.5),  # magnitud insuficiente
            _feature(4.5, 10.0, 18.5),  # fuera de la caja (longitud)
            _feature(None, -70.0, 18.5),  # magnitud nula, debe ignorarse
        ]
    }
    mock_response = Mock(status_code=200)
    mock_response.json.return_value = geojson

    with patch("motor_usgs.requests.get", return_value=mock_response) as mock_get:
        resultado = obtener_sismos_caribe(magnitud_minima=3.0)

    mock_get.assert_called_once()
    assert len(resultado) == 1
    assert resultado[0]["magnitud"] == 4.5
    assert resultado[0]["latitud"] == 18.5


def test_obtener_sismos_caribe_devuelve_lista_vacia_si_falla_la_peticion():
    mock_response = Mock(status_code=503)
    with patch("motor_usgs.requests.get", return_value=mock_response):
        assert obtener_sismos_caribe() == []


def test_calcular_valor_b_sin_sismos_devuelve_uno():
    assert calcular_valor_b([]) == 1.0


def test_calcular_valor_b_con_magnitudes_uniformes_bajas():
    sismos = [{"magnitud": m} for m in [3.0, 3.1, 3.0, 3.2, 3.0, 3.1]]
    assert calcular_valor_b(sismos) == 3.72


def test_calcular_valor_b_con_alta_dispersion():
    sismos = [{"magnitud": m} for m in [3.0, 3.5, 4.2, 3.1, 5.0, 3.3, 3.0]]
    assert calcular_valor_b(sismos) == 0.68


def test_calcular_probabilidades_sin_sismos():
    resultado = calcular_probabilidades_bayes_poisson([])
    assert resultado["tasa_diaria_estimada"] == 0.0
    for ventana in ("24_horas", "7_dias", "30_dias"):
        assert resultado["probabilidades"][ventana]["probabilidad"] == 0.0


def test_calcular_probabilidades_con_quince_sismos_en_30_dias():
    sismos = [{"magnitud": 3.0} for _ in range(15)]
    resultado = calcular_probabilidades_bayes_poisson(sismos)
    probs = resultado["probabilidades"]
    assert probs["24_horas"]["probabilidad"] == 39.3
    assert probs["7_dias"]["probabilidad"] == 97.0
    assert probs["30_dias"]["probabilidad"] == 100.0


def test_intervalo_de_confianza_contiene_siempre_el_valor_central():
    sismos = [{"magnitud": 3.0 + (i % 5) * 0.2} for i in range(8)]
    resultado = calcular_probabilidades_bayes_poisson(sismos)
    for ventana in resultado["probabilidades"].values():
        assert ventana["ic_90_min"] <= ventana["probabilidad"] <= ventana["ic_90_max"]
