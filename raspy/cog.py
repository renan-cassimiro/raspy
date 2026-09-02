# cog.py
# Responsável por converter um GeoTIFF intermediário em um
# Cloud Optimized GeoTIFF (COG) válido, usando rio-cogeo.
#
# Um COG válido possui:
# - tiling interno
# - overviews (pirâmides) embutidos
# - estrutura de bytes compatível com HTTP range requests

import os
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from rio_cogeo import cog_validate


def converter_para_cog(
    caminho_entrada: str,
    caminho_saida: str,
    compressao: str = "deflate",
    resampling_overview: str = "nearest",
    remover_temp: bool = True,
) -> None:
    """
    Converte um GeoTIFF para COG válido usando rio-cogeo.

    Parâmetros
    ----------
    caminho_entrada : str
        Caminho do GeoTIFF intermediário (gerado pelo transform.py).
    caminho_saida : str
        Caminho do arquivo COG final.
    compressao : str
        Tipo de compressão. Opções: 'deflate', 'lzw', 'zstd'.
        Deflate é recomendado para dados científicos contínuos.
    resampling_overview : str
        Método de reamostragem para geração dos overviews.
        Opções: 'average', 'nearest', 'bilinear'.
        'average' é recomendado para variáveis contínuas como elevação.
    remover_temp : bool
        Se True, remove o arquivo intermediário após a conversão.
    """
    # Obtém o perfil de COG pré-configurado pelo rio-cogeo
    perfil_cog = cog_profiles.get(compressao)

    print(f"  Convertendo para COG ({compressao.upper()})...")

    cog_translate(
        caminho_entrada,
        caminho_saida,
        perfil_cog,
        overview_resampling=resampling_overview,
        quiet=False,
    )

    # Remove arquivo temporário intermediário, se solicitado
    if remover_temp and os.path.exists(caminho_entrada):
        os.remove(caminho_entrada)
        print(f"  Arquivo temporário removido: {caminho_entrada}")


def validar_cog(caminho: str) -> bool:
    """
    Valida se um arquivo GeoTIFF é um COG válido.

    Parâmetros
    ----------
    caminho : str
        Caminho do arquivo a validar.

    Retorna
    -------
    bool : True se for COG válido, False caso contrário.
    """
    is_valid, errors, warnings = cog_validate(caminho)

    if is_valid:
        print(f"  COG válido: {caminho}")
    else:
        print(f"  COG INVÁLIDO: {caminho}")
        for erro in errors:
            print(f"    ERRO: {erro}")

    # Warnings não invalidam o COG, mas são informativos
    for aviso in warnings:
        print(f"    AVISO: {aviso}")

    return is_valid
     
 
