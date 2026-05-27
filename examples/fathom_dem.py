# examples/fathomdem.py
#
# Exemplo de uso do raspy para processar o FathomDEM da bacia amazônica.
#
# O dado original está em centímetros (inteiro) e precisa ser:
# 1. recortado para a área de interesse (GeoPackage)
# 2. convertido para metros (float32, dividir por 100)
# 3. exportado como COG válido com compressão DEFLATE
# 4. documentado com metadados YAML
#
# Como rodar:
#   conda activate raspy
#   python examples/fathomdem.py

import sys
from datetime import datetime
from pathlib import Path

# Permite importar raspy mesmo sem instalar como pacote
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from raspy import ingest, clip, transform, cog, metadata

# ---------------------------------------------------------------------------
# Caminhos — ajuste para o seu ambiente
# ---------------------------------------------------------------------------

ENTRADA      = r"C:\Users\renan\OneDrive\Projetos\pulsamazonia\python\raspy\input\xingu_river\xingu_river_study_area_bounding_box_fathomdem_30m.tif"
MASCARA_GPKG = r"C:\Users\renan\OneDrive\Projetos\pulsamazonia\python\raspy\input\xingu_river\xingu_river_study_area_bounding_box.gpkg"
SAIDA_CLIP   = r"C:\Users\renan\OneDrive\Projetos\pulsamazonia\python\raspy\output\xingu_river\xingu_river_study_area_bounding_box_fathomdem_30m_clip.tif"
SAIDA_TEMP   = r"C:\Users\renan\OneDrive\Projetos\pulsamazonia\python\raspy\output\xingu_river\xingu_river_study_area_bounding_box_fathomdem_30m_temp.tif"
SAIDA_FINAL  = r"C:\Users\renan\OneDrive\Projetos\pulsamazonia\python\raspy\output\xingu_river\xingu_river_study_area_bounding_box_fathomdem_30m_cog.tif"

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

inicio = datetime.now()
print(f"[{inicio}] Iniciando processamento FathomDEM\n")

# Passo 1: Ingestão — valida e lê metadados do raster de entrada
print("→ Passo 1: Ingestão")
info = ingest.abrir_raster(ENTRADA)
print(f"  CRS: {info['crs']}")
print(f"  Resolução: {info['resolucao']}")
print(f"  Bandas: {info['bandas']}")
print(f"  Nodata original: {info['nodata']}")

# Passo 2: Recorte — limita o raster à geometria do GeoPackage
print("\n→ Passo 2: Recorte territorial")
clip.recortar_por_gpkg(
    caminho_raster=ENTRADA,
    caminho_gpkg=MASCARA_GPKG,
    caminho_saida=SAIDA_CLIP,
    # layer="nome_da_camada",  # descomente se o gpkg tiver múltiplas camadas
    crop=True,                 # ajusta o extent ao recorte
    all_touched=False,         # só pixels com centro dentro da geometria
)

# Passo 3: Transformação — converte cm → m em blocos (opera sobre o recorte)
print("\n→ Passo 3: Transformação (÷ 100)")
transform.aplicar_fator_escala(
    caminho_entrada=SAIDA_CLIP,
    caminho_saida=SAIDA_TEMP,
    fator=100.0,
    nodata_saida=-9999.0,
)

# Passo 3: Conversão para COG
print("\n→ Passo 4: Conversão para COG")
cog.converter_para_cog(
    caminho_entrada=SAIDA_TEMP,
    caminho_saida=SAIDA_FINAL,
    compressao="deflate",
    resampling_overview="nearest",
    remover_temp=True,           # remove o arquivo temporário ao final
)

# Passo 4: Validação do COG gerado
print("\n→ Passo 5: Validação COG")
valido = cog.validar_cog(SAIDA_FINAL)

# Passo 5: Geração de metadados YAML
print("\n→ Passo 6: Metadados")
metadata.gerar_metadados(
    caminho_entrada=ENTRADA,
    caminho_saida=SAIDA_FINAL,
    info_raster=info,
    fator_escala=1.0,
    compressao="deflate",
    resampling_overview="average",
    origem="FathomDEM v1.0 — https://www.fathom.global",
    calcular_checksum=True,
)

fim = datetime.now()
print(f"\n[{fim}] Concluído em {fim - inicio}")

