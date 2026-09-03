# clip.py
# Responsável por recortar um raster a partir de uma geometria
# definida em um arquivo GeoPackage (.gpkg).
#
# O recorte é feito com rasterio.mask, que aplica a geometria como
# máscara e exporta apenas a região de interesse.
#
# Importante: se o CRS do vetor for diferente do raster, a geometria
# é reprojetada automaticamente antes do recorte.

import rasterio
from rasterio.mask import mask
import geopandas as gpd
from pathlib import Path


def recortar_por_gpkg(
    caminho_raster: str,
    caminho_gpkg: str,
    caminho_saida: str,
    layer: str = None,
    crop: bool = True,
    all_touched: bool = False,
) -> None:
    """
    Recorta um raster usando a geometria de um GeoPackage.

    O arquivo de saída é um GeoTIFF intermediário — a conversão
    para COG acontece depois, no módulo cog.py.

    Parâmetros
    ----------
    caminho_raster : str
        Caminho do raster de entrada (dado bruto).
    caminho_gpkg : str
        Caminho do arquivo GeoPackage com a geometria de recorte.
    caminho_saida : str
        Caminho do raster recortado de saída.
    layer : str, opcional
        Nome da camada dentro do GeoPackage. Se None, usa a primeira.
    crop : bool
        Se True, ajusta o extent do raster à geometria de recorte.
        Se False, mantém o extent original e apenas mascara os pixels.
    all_touched : bool
        Se True, inclui todos os pixels que tocam a geometria (borda).
        Se False, inclui apenas pixels cujo centro está dentro da geometria.
        Use True quando quiser garantir que a borda não seja cortada.
    """
    # Lê a geometria do GeoPackage
    gdf = gpd.read_file(caminho_gpkg, layer=layer)

    if gdf.empty:
        raise ValueError(f"O GeoPackage '{caminho_gpkg}' não contém geometrias.")

    with rasterio.open(caminho_raster) as src:

        # Reprojeta o vetor para o CRS do raster se necessário
        if gdf.crs != src.crs:
            print(f"  Reprojetando geometria de {gdf.crs} para {src.crs}...")
            gdf = gdf.to_crs(src.crs)

        # Extrai as geometrias como lista de dicionários (formato esperado pelo rasterio)
        geometrias = [geom.__geo_interface__ for geom in gdf.geometry]

        # Se o raster de entrada não tem nodata definido, rasterio.mask.mask()
        # preenche a área fora da geometria com 0 por padrão. Isso pode colidir
        # com valores de dado válidos (ex.: uma classe 0 legítima). Avisamos
        # explicitamente em vez de deixar esse comportamento implícito.
        if src.nodata is None:
            print(
                "  AVISO: raster de entrada não possui nodata definido. "
                "A área fora da geometria de recorte será preenchida com 0, "
                "o que pode ser indistinguível de um valor de dado válido. "
                "Considere definir um nodata explícito antes do recorte."
            )

        # Aplica o recorte
        raster_recortado, transform_novo = mask(
            src,
            geometrias,
            crop=crop,
            all_touched=all_touched,
            nodata=src.nodata,
        )

        # Monta o perfil do arquivo de saída mantendo o perfil original
        perfil = src.profile.copy()
        perfil.update(
            height=raster_recortado.shape[1],
            width=raster_recortado.shape[2],
            transform=transform_novo,
        )

        with rasterio.open(caminho_saida, "w", **perfil) as dst:
            dst.write(raster_recortado)

    print(f"  Recorte concluído → {caminho_saida}")
    print(f"  Dimensões: {raster_recortado.shape[1]} x {raster_recortado.shape[2]} pixels") 
 
