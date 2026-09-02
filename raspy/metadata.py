# metadata.py
# Responsável por gerar um arquivo YAML de rastreabilidade
# para cada raster processado.
#
# O objetivo é garantir que qualquer arquivo COG gerado tenha
# um registro legível com sua origem, parâmetros e histórico.

import hashlib
import yaml
from datetime import datetime
from pathlib import Path


def calcular_hash(caminho: str, algoritmo: str = "md5") -> str:
    """
    Calcula o hash de um arquivo para verificação de integridade.

    Útil para detectar se um arquivo foi modificado após o processamento.

    Parâmetros
    ----------
    caminho : str
        Caminho do arquivo.
    algoritmo : str
        Algoritmo de hash. Opções: 'md5', 'sha256'.

    Retorna
    -------
    str : hash hexadecimal do arquivo.
    """
    h = hashlib.new(algoritmo)
    with open(caminho, "rb") as f:
        # Lê em blocos para não carregar o arquivo inteiro na RAM
        for bloco in iter(lambda: f.read(8192), b""):
            h.update(bloco)
    return h.hexdigest()


def gerar_metadados(
    caminho_entrada: str,
    caminho_saida: str,
    info_raster: dict,
    fator_escala: float = None,
    nodata_saida: float = None,
    compressao: str = "deflate",
    resampling_overview: str = "average",
    origem: str = None,
    calcular_checksum: bool = True,
) -> str:
    """
    Gera um arquivo YAML com metadados e histórico do processamento.

    O arquivo é salvo no mesmo diretório do COG gerado,
    com o mesmo nome base e extensão .yaml.

    Parâmetros
    ----------
    caminho_entrada : str
        Caminho do raster original.
    caminho_saida : str
        Caminho do COG gerado.
    info_raster : dict
        Dicionário retornado por ingest.abrir_raster().
    fator_escala : float, opcional
        Fator de escala aplicado (ex: 100.0 para cm→m).
    nodata_saida : float, opcional
        Valor de nodata realmente gravado no arquivo de saída (ex.:
        obtido via `rasterio.open(caminho_saida).nodata`). Se informado,
        é registrado exatamente como passado, e deve corresponder ao
        nodata real do arquivo — esta função não valida essa
        correspondência.
        Se omitido, o valor é inferido a partir de `fator_escala`
        (comportamento legado, mantido por compatibilidade com scripts
        existentes; ver DIV-04 em `divergence-matrix.md` — essa
        inferência pode não corresponder ao nodata real quando a
        transformação aplicada foi reclassificação, não escala).
    compressao : str
        Compressão usada na conversão COG.
    resampling_overview : str
        Método de reamostragem dos overviews.
    origem : str, opcional
        Descrição da fonte do dado (ex: 'FABDEM v1.2', 'CHIRPS v2.0').
    calcular_checksum : bool
        Se True, calcula o hash MD5 do arquivo de saída.

    Retorna
    -------
    str : caminho do arquivo YAML gerado.
    """
    bounds = info_raster["bounds"]

    metadados = {
        "raspy_version": "0.1.0",
        "data_processamento": datetime.now().isoformat(),

        "entrada": {
            "arquivo": str(Path(caminho_entrada).resolve()),
            "origem": origem or "não informada",
        },

        "saida": {
            "arquivo": str(Path(caminho_saida).resolve()),
            "formato": "Cloud Optimized GeoTIFF (COG)",
        },

        "espacial": {
            "crs": str(info_raster["crs"]),
            "resolucao_x": info_raster["resolucao"][0],
            "resolucao_y": info_raster["resolucao"][1],
            "bandas": info_raster["bandas"],
            "bounding_box": {
                "left":   bounds.left,
                "bottom": bounds.bottom,
                "right":  bounds.right,
                "top":    bounds.top,
            },
            "nodata_original": info_raster["nodata"],
        },

        "processamento": {
            "fator_escala": fator_escala,
            "nodata_saida": (
                nodata_saida
                if nodata_saida is not None
                else (-9999.0 if fator_escala else info_raster["nodata"])
            ),
            "compressao": compressao,
            "resampling_overview": resampling_overview,
        },
    }

    # Checksum é opcional pois pode ser lento em arquivos grandes
    if calcular_checksum and Path(caminho_saida).exists():
        metadados["saida"]["checksum_md5"] = calcular_hash(caminho_saida)

    # Salva o YAML no mesmo diretório do COG
    caminho_yaml = str(Path(caminho_saida).with_suffix(".yaml"))
    with open(caminho_yaml, "w", encoding="utf-8") as f:
        yaml.dump(metadados, f, allow_unicode=True, sort_keys=False)

    print(f"  Metadados salvos → {caminho_yaml}")
    return caminho_yaml 
 
