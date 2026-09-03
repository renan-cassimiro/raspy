# examples/xingu_river_hess2015_wetland_vegetation_dual_season_flood_map.py
#
# HESS 2015 — mapa de vegetação/inundação dual-season, resolução de
# 3 arc-seconds, recortado para a área de estudo do rio Xingu, mantendo
# os códigos de classe originais (sem reclassificação).
#
# NOTA DE MIGRAÇÃO: o bloco de conversão cm->m (aplicar_fator_escala)
# estava comentado no arquivo original e nunca fez sentido para este
# dataset (é um mapa de classes categórico, não uma variável contínua
# como elevação) — removido nesta migração, não apenas comentado,
# porque era código morto sem propósito aqui, não uma transformação
# pendente de ativação (diferente do caso do dicionário RECLASSIFICACAO
# no exemplo "_3arcsec.py", que é uma reclassificação plausível apenas
# desativada).
#
# Como rodar (com o ambiente já configurado — ver README.md):
#   conda activate raspy_env
#   python examples/xingu_river_hess2015_wetland_vegetation_dual_season_flood_map.py

from raspy import RasterPipeline

# ---------------------------------------------------------------------------
# Caminhos — ajuste para o seu ambiente
# ---------------------------------------------------------------------------

ENTRADA = r"C:\Users\renan\OneDrive\Projetos\pulsamazonia\data\abiotico\amazon_basin\hess2015\raw\LC07_Amazon_Wetlands_1284\data\LBA_Amazon_wetland_dual-season_veg_flood_3arcsec.tif"
MASCARA_GPKG = r"input/xingu_river/xingu_river_study_area_bounding_box.gpkg"
SAIDA_FINAL = r"C:\Users\renan\OneDrive\Projetos\pulsamazonia\data\abiotico\xingu_river\hess2015\processed\wetland_vegetation_dual-season_flood_map\LBA_Amazon_wetland_dual-season_veg_flood_3arcsec_cog\LBA_Amazon_wetland_dual-season_veg_flood_3arcsec_cog.tif"

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

with RasterPipeline(
    ENTRADA,
    SAIDA_FINAL,
    origem="HESS 2015 — Amazon wetland dual-season vegetation/flood map (3 arc-seconds), recorte: bacia do rio Xingu",  # TODO: confirmar citação completa do dataset
    remover_temp=False,  # decisão deliberada (DEC-007): mantém intermediários para depuração manual
) as p:
    p.clip(MASCARA_GPKG, crop=True, all_touched=False)

print(f"COG válido: {p.cog_valido}")
print(f"Metadados: {p.metadata_path}")
