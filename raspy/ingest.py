# ingest.py
# Responsável por abrir o raster de entrada, validar sua integridade
# e retornar o perfil (metadados espaciais) para uso nas etapas seguintes.

import rasterio


def abrir_raster(caminho: str) -> dict:
    """
    Abre um raster GeoTIFF e retorna seus metadados espaciais (perfil).

    Valida:
    - se o arquivo existe e pode ser lido
    - se possui CRS definido
    - se possui pelo menos uma banda

    Parâmetros
    ----------
    caminho : str
        Caminho completo para o arquivo raster de entrada.

    Retorna
    -------
    dict com chaves:
        - 'perfil': dict com metadados rasterio (crs, dtype, nodata, etc.)
        - 'nodata': valor de nodata original (pode ser None)
        - 'crs': CRS do raster
        - 'resolucao': tupla (res_x, res_y) em unidades do CRS
        - 'bandas': número de bandas
    """
    with rasterio.open(caminho) as src:

        # Valida se o arquivo tem CRS definido
        if src.crs is None:
            raise ValueError(f"O raster '{caminho}' não possui CRS definido.")

        # Valida se há pelo menos uma banda
        if src.count < 1:
            raise ValueError(f"O raster '{caminho}' não possui bandas.")

        perfil = src.profile.copy()
        nodata = src.nodata
        crs = src.crs
        resolucao = src.res       # (res_x, res_y)
        bandas = src.count
        bounds = src.bounds       # bounding box: left, bottom, right, top

    return {
        "perfil": perfil,
        "nodata": nodata,
        "crs": crs,
        "resolucao": resolucao,
        "bandas": bandas,
        "bounds": bounds,
    }