# test_ingest.py
# Testes unitários para ingest.py (REQ-001).

import pytest

from raspy import ingest


def test_abrir_raster_valido_retorna_campos_esperados(dataset01):
    info = ingest.abrir_raster(dataset01["raster"])

    assert info["nodata"] == -1
    assert info["bandas"] == 1
    assert info["crs"] is not None
    assert "resolucao" in info
    assert "bounds" in info


def test_abrir_raster_inexistente_levanta_erro():
    with pytest.raises(Exception):
        ingest.abrir_raster("/caminho/que/nao/existe.tif")
