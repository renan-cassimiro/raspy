# test_transform.py
# Testes unitários para transform.py (REQ-003: aplicar_fator_escala,
# REQ-004: reclassificar).

import numpy as np
import rasterio

from raspy import transform


def test_aplicar_fator_escala_divide_valores_e_preserva_nodata(dataset01, tmp_path):
    saida = str(tmp_path / "escalado.tif")
    transform.aplicar_fator_escala(
        dataset01["raster"], saida, fator=10.0, nodata_saida=-9999.0
    )

    with rasterio.open(dataset01["raster"]) as src_original:
        original = src_original.read(1)

    with rasterio.open(saida) as ds:
        resultado = ds.read(1)
        assert ds.dtypes[0] == "float32"
        assert ds.nodata == -9999.0

    # pixels que eram nodata (-1) na entrada devem virar nodata_saida,
    # não -1/10 = -0.1 (REQ-003, critério de aceitação 2)
    mascara_nodata_original = original == -1
    assert np.all(resultado[mascara_nodata_original] == -9999.0)

    # um pixel de classe 1 (não-nodata) deve ter sido de fato dividido
    mascara_classe_1 = original == 1
    assert np.allclose(resultado[mascara_classe_1], 1 / 10.0)


def test_reclassificar_aplica_mapeamento_e_valor_padrao(dataset01, tmp_path):
    saida = str(tmp_path / "reclassificado.tif")
    transform.reclassificar(
        dataset01["raster"],
        saida,
        mapeamento={1: 100},  # note: classe 0 e nodata (-1) ficam sem regra
        nodata_saida=250,
        dtype="uint8",
    )

    with rasterio.open(saida) as ds:
        resultado = ds.read(1)
        assert ds.nodata == 250

    # pixel mapeado (classe 1 -> 100)
    assert resultado[10, 10] == 100  # dentro da região de classe 1 no dataset01


def test_reclassificar_classe_valida_pode_ficar_indistinguivel_de_nodata(dataset01, tmp_path):
    """
    Documenta o comportamento QUESTIONÁVEL descrito em SPEC/scientific.md
    (item 8) e SPEC/requirements.md (REQ-004): se uma classe válida do
    mapeamento coincidir com nodata_saida, o resultado final não permite
    diferenciar essa classe de nodata/valor-sem-regra. Este teste NÃO
    afirma que esse comportamento esteja correto — apenas o torna
    visível e vigiado (se o comportamento mudar no futuro, este teste
    quebra e força uma decisão consciente).
    """
    saida = str(tmp_path / "ambiguo.tif")
    transform.reclassificar(
        dataset01["raster"],
        saida,
        mapeamento={0: 0, 1: 1},  # classe 0 mapeada explicitamente para 0
        nodata_saida=0,           # mesmo valor da classe 0 legítima
        dtype="uint8",
    )

    with rasterio.open(dataset01["raster"]) as src_original:
        original = src_original.read(1)

    with rasterio.open(saida) as ds:
        resultado = ds.read(1)

    pixel_classe_0_legitima = (10, 2)   # dentro da região original[0:5, 0:5] == 0... ver nota abaixo
    # A região de classe 0 legítima no dataset01 é original[0:5, 0:5].
    assert original[2, 2] == 0
    assert resultado[2, 2] == 0  # classe 0 legítima -> 0 (esperado pelo mapeamento)

    # A região de nodata original é original[15:20, 15:20] == -1
    assert original[17, 17] == -1
    assert resultado[17, 17] == 0  # nodata original também -> 0

    # Ambos os pixels acima têm o MESMO valor final (0), apesar de
    # terem significados completamente diferentes na entrada. Este é
    # exatamente o problema registrado em DIV-07 / REQ-004.
    assert resultado[2, 2] == resultado[17, 17]
