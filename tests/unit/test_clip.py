# test_clip.py
# Testes unitários para clip.py (REQ-002, e REQ-011: aviso quando o
# raster de entrada não possui nodata definido).

import rasterio

from raspy import clip


def test_recortar_por_gpkg_reduz_extensao(dataset01, tmp_path):
    saida = str(tmp_path / "recortado.tif")
    clip.recortar_por_gpkg(dataset01["raster"], dataset01["gpkg"], saida, crop=True)

    with rasterio.open(dataset01["raster"]) as original, rasterio.open(saida) as recortado:
        assert recortado.height < original.height  # gpkg cobre só a metade "norte"
        assert recortado.width == original.width


def test_recortar_por_gpkg_avisa_quando_nodata_e_none(
    raster_sem_nodata, dataset01, tmp_path, capsys
):
    """REQ-011: ao recortar um raster sem nodata definido, o sistema
    deve emitir um aviso explícito (DEC-007, resolve DIV-11)."""
    saida = str(tmp_path / "recortado_sem_nodata.tif")

    clip.recortar_por_gpkg(raster_sem_nodata, dataset01["gpkg"], saida, crop=True)

    saida_console = capsys.readouterr().out
    assert "AVISO" in saida_console
    assert "nodata" in saida_console.lower()


def test_recortar_por_gpkg_nao_avisa_quando_nodata_definido(dataset01, tmp_path, capsys):
    """Caso contrário (nodata definido), nenhum aviso de nodata deve
    ser emitido — evita alarme falso em rasters bem formados."""
    saida = str(tmp_path / "recortado_com_nodata.tif")

    clip.recortar_por_gpkg(dataset01["raster"], dataset01["gpkg"], saida, crop=True)

    saida_console = capsys.readouterr().out
    assert "AVISO" not in saida_console
