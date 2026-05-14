# transform.py
# Responsável por aplicar transformações nos valores do raster
# processando bloco a bloco para economizar memória RAM.
#
# Cada função recebe o caminho de entrada, o caminho de saída temporário
# e parâmetros da transformação desejada.

import rasterio
import numpy as np


def aplicar_fator_escala(
    caminho_entrada: str,
    caminho_saida: str,
    fator: float,
    nodata_saida: float = -9999.0,
) -> None:
    """
    Divide todos os pixels válidos por um fator de escala, bloco a bloco.

    Útil para converter unidades — por exemplo, centímetros para metros (fator=100).

    O arquivo de saída é um GeoTIFF intermediário (não é COG ainda).
    A conversão para COG acontece no módulo cog.py.

    Parâmetros
    ----------
    caminho_entrada : str
        Caminho do raster de entrada.
    caminho_saida : str
        Caminho do arquivo temporário de saída.
    fator : float
        Valor pelo qual os pixels serão divididos.
    nodata_saida : float
        Valor de nodata a ser usado no arquivo de saída.
    """
    with rasterio.open(caminho_entrada) as src:
        nodata_original = src.nodata

        # Monta o perfil do arquivo de saída
        perfil = src.profile.copy()
        perfil.update(
            driver="GTiff",
            dtype="float32",
            compress="DEFLATE",
            predictor=3,          # predictor=3 é otimizado para dados float
            blockxsize=1024,
            blockysize=1024,
            tiled=True,
            BIGTIFF="YES",        # necessário para arquivos maiores que 4 GB
            nodata=nodata_saida,
        )

        total_blocos = sum(1 for _ in src.block_windows(1))

        with rasterio.open(caminho_saida, "w", **perfil) as dst:
            for i, (_, window) in enumerate(src.block_windows(1), 1):

                # Lê o bloco atual como float32
                bloco = src.read(1, window=window).astype("float32")

                if nodata_original is not None:
                    # Identifica pixels de nodata antes de transformar
                    mascara_nodata = bloco == nodata_original
                    bloco = bloco / fator
                    # Reaplica nodata nos pixels identificados
                    bloco[mascara_nodata] = nodata_saida
                else:
                    bloco = bloco / fator

                dst.write(bloco, 1, window=window)

                print(f"  Bloco {i}/{total_blocos}", end="\r")

    print(f"\n  Transformação concluída → {caminho_saida}")