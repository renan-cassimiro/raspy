# examples/souza2025_wetland_map_article_multiclass_reclassified.py
#
# Souza et al. 2025 — mapa multiclasse de áreas úmidas, reclassificado
# em máscara binária (0 = classe 0 original, 1 = qualquer classe 1-10).
# Sem recorte espacial (processado na extensão original do dado).
#
# Como rodar (com o ambiente já configurado — ver README.md):
#   conda activate raspy_env
#   python examples/souza2025_wetland_map_article_multiclass_reclassified.py

from raspy import RasterPipeline

# ---------------------------------------------------------------------------
# Caminhos — ajuste para o seu ambiente
# ---------------------------------------------------------------------------

ENTRADA = r"C:\Users\renan\OneDrive\Projetos\pulsamazonia\data\abiotico\amazon_basin\souza2025\raw\wetland_map_article_multiclass\wetland_map_article_multiclass.tif"
SAIDA_FINAL = r"C:\Users\renan\OneDrive\Projetos\pulsamazonia\data\abiotico\xingu_river\souza2025\processed\wetland_map_article_multiclass_reclassified_cog\wetland_map_article_multiclass_reclassified_cog\wetland_map_article_multiclass_reclassified_cog.tif"

RECLASSIFICACAO = {0: 0, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1}

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

with RasterPipeline(
    ENTRADA,
    SAIDA_FINAL,
    origem="Enhanced Amazon Wetland Map with Multi-Source Remote Sensing Data — https://www.mdpi.com/2072-4292/17/21/3644",
    remover_temp=False,  # decisão deliberada (DEC-007): mantém intermediários para depuração manual
) as p:
    p.reclassify(mapeamento=RECLASSIFICACAO, nodata_saida=0, dtype="uint8")

print(f"COG válido: {p.cog_valido}")
print(f"Metadados: {p.metadata_path}")
