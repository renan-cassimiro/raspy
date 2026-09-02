# conftest.py
# Fixtures compartilhadas entre tests/unit e tests/pipeline.
#
# 'raspy' é importado como pacote instalado (ver pyproject.toml e o
# passo `pip install -e .` no README) — não dependemos de manipular
# sys.path para isso, porque isso se mostrou frágil entre plataformas
# (ver CHANGELOG.md). O único ajuste de sys.path que ainda fazemos é
# para tests/synthetic_data/, que não é um pacote instalado, só um
# módulo auxiliar de teste.

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent / "synthetic_data"))

from generators import (  # noqa: E402
    dataset_01_classe_zero_coincide_com_nodata,
    raster_simples_sem_nodata,
)


@pytest.fixture
def dataset01(tmp_path):
    """Raster categórico + GeoPackage do dataset sintético #1 (ver EXP-001)."""
    return dataset_01_classe_zero_coincide_com_nodata(tmp_path / "dataset01")


@pytest.fixture
def raster_sem_nodata(tmp_path):
    """Raster contínuo 10x10 sem nodata definido no perfil."""
    return raster_simples_sem_nodata(tmp_path / "sem_nodata")
