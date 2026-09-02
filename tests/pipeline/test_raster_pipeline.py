# test_raster_pipeline.py
# Formaliza como testes automatizados os 5 cenários que foram validados
# manualmente durante a implementação de RasterPipeline (ver
# SPEC/experiments.md, EXP-001, e SPEC/requirements.md, REQ-009/TEST-009).

import glob
import os

import pytest
import rasterio
import yaml

from raspy import RasterPipeline


def _ler_yaml(caminho_saida):
    caminho_yaml = os.path.splitext(caminho_saida)[0] + ".yaml"
    with open(caminho_yaml, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_pipeline_sem_nenhuma_transformacao(dataset01, tmp_path):
    """Cenário 1: nenhuma etapa chamada -> COG direto do raster bruto,
    e o arquivo de entrada original nunca é tocado (REQ-009)."""
    saida = str(tmp_path / "saida1_cog.tif")

    with RasterPipeline(dataset01["raster"], saida, origem="teste sintético") as p:
        pass

    # Trava a regressão encontrada ao migrar examples/ para RasterPipeline:
    # esses atributos não existiam publicamente antes desta correção.
    assert p.cog_valido is True
    assert p.metadata_path == os.path.splitext(saida)[0] + ".yaml"

    assert os.path.exists(saida)
    assert os.path.exists(dataset01["raster"]), "BUG: entrada original foi apagada"

    with rasterio.open(saida) as ds:
        assert ds.nodata == -1.0

    meta = _ler_yaml(saida)
    assert meta["processamento"]["nodata_saida"] == -1.0
    assert meta["processamento"]["fator_escala"] is None
    assert meta["entrada"]["arquivo"] == str(
        __import__("pathlib").Path(dataset01["raster"]).resolve()
    )


def test_pipeline_apenas_scale(dataset01, tmp_path):
    """Cenário 2: apenas scale() -> nodata_saida e fator_escala corretos,
    resampling_overview inferido como 'average' (dado contínuo)."""
    saida = str(tmp_path / "saida2_cog.tif")

    with RasterPipeline(dataset01["raster"], saida) as p:
        p.scale(fator=10.0, nodata_saida=-9999.0)

    with rasterio.open(saida) as ds:
        assert ds.nodata == -9999.0
        assert ds.dtypes[0] == "float32"

    meta = _ler_yaml(saida)
    assert meta["processamento"]["nodata_saida"] == -9999.0
    assert meta["processamento"]["fator_escala"] == 10.0
    assert meta["processamento"]["resampling_overview"] == "average"


def test_pipeline_clip_e_reclassify_classe_zero_coincide_com_nodata(dataset01, tmp_path):
    """Cenário 3: clip() + reclassify() reproduzindo DIV-07 (classe 0
    legítima mapeada para 0, com nodata_saida=0). O teste documenta o
    comportamento ATUAL (ambíguo, ver REQ-004) — não afirma que esteja
    correto, apenas que é reprodutível e mensurável."""
    saida = str(tmp_path / "saida3_cog.tif")

    with RasterPipeline(dataset01["raster"], saida, origem="teste categórico") as p:
        p.clip(dataset01["gpkg"], crop=True)
        p.reclassify(mapeamento={0: 0, 1: 1}, nodata_saida=0, dtype="uint8")

    with rasterio.open(saida) as ds:
        assert ds.nodata == 0.0
        assert ds.dtypes[0] == "uint8"
        # DIV-07: pixels de classe 0 legítima e pixels de nodata são,
        # de fato, indistinguíveis no arquivo final — o teste comprova
        # a ambiguidade em vez de escondê-la.
        dados = ds.read(1)
        assert (dados == 0).any(), "esperava-se pixels com valor 0 no resultado"

    meta = _ler_yaml(saida)
    assert meta["processamento"]["resampling_overview"] == "nearest"
    assert meta["processamento"]["fator_escala"] is None


def test_pipeline_excecao_nao_gera_cog_nem_metadados(dataset01, tmp_path):
    """Cenário 4: uma exceção dentro do bloco `with` deve impedir a
    etapa final e deve ser propagada, nunca silenciada."""
    saida = str(tmp_path / "saida4_cog.tif")

    with pytest.raises(RuntimeError, match="falha simulada"):
        with RasterPipeline(dataset01["raster"], saida) as p:
            p.scale(fator=10.0)
            raise RuntimeError("falha simulada no meio do pipeline")

    assert not os.path.exists(saida)
    assert not os.path.exists(os.path.splitext(saida)[0] + ".yaml")


def test_pipeline_remover_temp_false_mantem_intermediarios(dataset01, tmp_path):
    """Cenário 5: remover_temp=False deve manter os arquivos
    intermediários criados pelo próprio pipeline."""
    saida_dir = tmp_path / "saida5"
    saida_dir.mkdir()
    saida = str(saida_dir / "saida5_cog.tif")

    with RasterPipeline(dataset01["raster"], saida, remover_temp=False) as p:
        p.scale(fator=10.0)

    temporarios = glob.glob(str(saida_dir / ".raspy_tmp_*"))
    assert len(temporarios) == 1, "esperava-se 1 arquivo intermediário preservado"
