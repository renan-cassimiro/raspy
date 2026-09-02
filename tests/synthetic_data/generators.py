# generators.py
# Geradores de datasets sintéticos usados pelos testes (tests/unit,
# tests/pipeline) e disponíveis para exploração manual (ver
# SPEC/experiments.md, EXP-001).
#
# Cada gerador cria arquivos reais em disco (não apenas arrays em
# memória), porque as funções de raspy operam sobre caminhos de
# arquivo, não sobre arrays.
#
# Catálogo completo planejado em CONTEXT.md ("Tarefa atual"). Apenas o
# dataset #1 está implementado até o momento — ver SPEC/experiments.md,
# EXP-001, para o que ainda falta.

from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box


def dataset_01_classe_zero_coincide_com_nodata(diretorio: str):
    """
    Dataset sintético #1 (prioridade máxima no catálogo de CONTEXT.md).

    Raster categórico 20x20, CRS EPSG:4326, com:
    - uma região de classe 0 (LEGÍTIMA, não é nodata);
    - uma região de nodata original = -1;
    - o restante com classe 1.

    Serve para expor DIV-07 / o item QUESTIONÁVEL do item 8 de
    SPEC/scientific.md: se, ao reclassificar com nodata_saida=0, a
    classe 0 legítima se torna indistinguível de nodata.

    Também inclui um GeoPackage com um polígono cobrindo a metade
    superior do raster (linhas 0-9 em coordenadas de imagem, ou seja,
    a metade "norte"), útil para testar clip() no mesmo dataset.

    Retorna
    -------
    dict com as chaves 'raster' e 'gpkg' (caminhos dos arquivos gerados).
    """
    diretorio = Path(diretorio)
    diretorio.mkdir(parents=True, exist_ok=True)

    caminho_raster = str(diretorio / "dataset01_entrada.tif")
    caminho_gpkg = str(diretorio / "dataset01_area.gpkg")

    largura, altura = 20, 20
    transform = from_origin(0, 20, 1, 1)

    dados = np.ones((altura, largura), dtype="int16")       # classe 1 (padrão)
    dados[0:5, 0:5] = 0                                       # classe 0 legítima
    dados[15:20, 15:20] = -1                                  # nodata original

    perfil = {
        "driver": "GTiff",
        "height": altura,
        "width": largura,
        "count": 1,
        "dtype": "int16",
        "crs": "EPSG:4326",
        "transform": transform,
        "nodata": -1,
    }
    with rasterio.open(caminho_raster, "w", **perfil) as dst:
        dst.write(dados, 1)

    # Polígono cobrindo a metade "norte" do raster (y de 10 a 20 em
    # coordenadas geográficas, já que a origem está em y=20 e a
    # resolução é 1 na direção sul).
    geometria = box(0, 10, 20, 20)
    gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[geometria], crs="EPSG:4326")
    gdf.to_file(caminho_gpkg, driver="GPKG")

    return {"raster": caminho_raster, "gpkg": caminho_gpkg}


def raster_simples_sem_nodata(diretorio: str, nome: str = "sem_nodata.tif"):
    """
    Raster 10x10 contínuo (float32), sem nodata definido no perfil.

    Auxiliar mínimo para exercitar o aviso de clip.py quando
    src.nodata is None (REQ-002, REQ-011) — ainda não incorporado a um
    dataset numerado do catálogo por não precisar de GeoPackage próprio;
    use em conjunto com o gpkg do dataset #1.
    """
    diretorio = Path(diretorio)
    diretorio.mkdir(parents=True, exist_ok=True)
    caminho = str(diretorio / nome)

    largura, altura = 10, 10
    transform = from_origin(0, 20, 1, 1)
    dados = np.linspace(0, 100, largura * altura, dtype="float32").reshape(altura, largura)

    perfil = {
        "driver": "GTiff",
        "height": altura,
        "width": largura,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": transform,
        # nodata deliberadamente omitido
    }
    with rasterio.open(caminho, "w", **perfil) as dst:
        dst.write(dados, 1)

    return caminho
