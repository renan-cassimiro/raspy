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

def reclassificar(
    caminho_entrada: str,
    caminho_saida: str,
    mapeamento: dict,
    nodata_saida: int = 0,
    dtype: str = "uint8",
) -> None:
    """
    Reclassifica os valores de um raster usando um dicionário de mapeamento.

    Cada valor encontrado no raster é substituído pelo valor correspondente
    no dicionário.

    Exemplo
    -------
    mapeamento = {
        1: 0,
        2: 1,
        3: 1,
        4: 0,
    }

    Parâmetros
    ----------
    caminho_entrada : str
        Raster de entrada.

    caminho_saida : str
        Raster GeoTIFF intermediário de saída.

    mapeamento : dict
        Dicionário {valor_original: novo_valor}.

    nodata_saida : int
        Valor usado para pixels que não possuem uma regra no mapeamento.

    dtype : str
        Tipo numérico do raster de saída.
        Para reclassificação binária, uint8 é recomendado.
    """

    with rasterio.open(caminho_entrada) as src:

        nodata_original = src.nodata

        perfil = src.profile.copy()
        perfil.update(
            driver="GTiff",
            dtype=dtype,
            compress="DEFLATE",
            predictor=2,
            blockxsize=1024,
            blockysize=1024,
            tiled=True,
            BIGTIFF="YES",
            nodata=nodata_saida,
        )

        total_blocos = sum(1 for _ in src.block_windows(1))

        with rasterio.open(caminho_saida, "w", **perfil) as dst:

            for i, (_, window) in enumerate(src.block_windows(1), 1):

                bloco = src.read(1, window=window)

                # Começa todos os pixels com o valor padrão.
                resultado = np.full(
                    bloco.shape,
                    nodata_saida,
                    dtype=dtype,
                )

                # Aplica cada regra de reclassificação.
                for valor_original, novo_valor in mapeamento.items():
                    mascara = bloco == valor_original
                    resultado[mascara] = novo_valor

                # Preserva explicitamente o nodata original.
                if nodata_original is not None:
                    mascara_nodata = bloco == nodata_original
                    resultado[mascara_nodata] = nodata_saida

                dst.write(resultado, 1, window=window)

                print(f"  Bloco {i}/{total_blocos}", end="\r")

    print(f"\n  Reclassificação concluída → {caminho_saida}")



def calcular_declividade(
    caminho_entrada: str,
    caminho_saida: str,
    unidade: str = "degrees",
    nodata_saida: float = -9999.0,
) -> None:
    """
    Calcula a declividade a partir de um Modelo Digital de Elevação.

    Parâmetros
    ----------
    caminho_entrada : str
        Caminho do raster de elevação (DEM).

    caminho_saida : str
        Caminho do raster temporário de saída.

    unidade : str
        Unidade da declividade:
        - "degrees": graus
        - "percent": porcentagem

    nodata_saida : float
        Valor de nodata do raster de saída.
    """

    with rasterio.open(caminho_entrada) as src:

        if src.count != 1:
            raise ValueError(
                "O cálculo de declividade requer um raster de banda única."
            )

        # Resolução espacial
        res_x, res_y = src.res

        # Perfil de saída
        perfil = src.profile.copy()
        perfil.update(
            driver="GTiff",
            dtype="float32",
            compress="DEFLATE",
            predictor=3,
            blockxsize=1024,
            blockysize=1024,
            tiled=True,
            BIGTIFF="YES",
            nodata=nodata_saida,
        )

        # Leitura do DEM
        dem = src.read(1).astype("float32")

        # Máscara nodata
        if src.nodata is not None:
            mascara_nodata = dem == src.nodata
            dem[mascara_nodata] = np.nan
        else:
            mascara_nodata = np.zeros(dem.shape, dtype=bool)

        # Gradientes horizontal e vertical
        dz_dy, dz_dx = np.gradient(
            dem,
            res_y,
            res_x
        )

        # Magnitude do gradiente
        gradiente = np.sqrt(
            dz_dx**2 +
            dz_dy**2
        )

        # Declividade
        if unidade == "degrees":

            declividade = np.degrees(
                np.arctan(gradiente)
            )

        elif unidade == "percent":

            declividade = gradiente * 100

        else:
            raise ValueError(
                "Unidade inválida. Use 'degrees' ou 'percent'."
            )

        # Define nodata
        declividade[
            np.isnan(declividade) | mascara_nodata
        ] = nodata_saida

        with rasterio.open(
            caminho_saida,
            "w",
            **perfil
        ) as dst:

            dst.write(
                declividade.astype("float32"),
                1
            )

    print(
        f"Declividade calculada ({unidade}) → "
        f"{caminho_saida}"
    )