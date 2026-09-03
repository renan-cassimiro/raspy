# examples/hess2015_wetland_vegetation_dual_season_flood_map_reclassified.py
#
# HESS 2015 — mapa de vegetação/inundação dual-season (AA100m), recortado
# para a área de estudo do rio Xingu e reclassificado em máscara binária
# (0 = não-úmido/não-alagado, 1 = úmido/alagado).
#
# Este é o único dos 5 exemplos originais em que recorte + reclassificação
# já estavam de fato ativos (não comentados) — ou seja, o pipeline
# "correto" abaixo já era o comportamento real deste arquivo antes da
# migração; só a forma de escrever mudou.
#
# Como rodar (com o ambiente já configurado — ver README.md):
#   conda activate raspy_env
#   python examples/hess2015_wetland_vegetation_dual_season_flood_map_reclassified.py

from raspy import RasterPipeline

# ---------------------------------------------------------------------------
# Caminhos — ajuste para o seu ambiente
# ---------------------------------------------------------------------------

ENTRADA = r"C:\Users\renan\OneDrive\Projetos\pulsamazonia\data\abiotico\amazon_basin\hess2015\raw\LC07_Amazon_Wetlands_1284\data\LBA_Amazon_wetland_dual-season_veg_flood_AA100m.tif"
MASCARA_GPKG = r"input/xingu_river/xingu_river_study_area_bounding_box.gpkg"
SAIDA_FINAL = r"C:\Users\renan\OneDrive\Projetos\pulsamazonia\data\abiotico\xingu_river\hess2015\processed\wetland_vegetation_dual-season_flood_map_reclassified\xingu_river_wetland_dual-season_veg_flood_AA100m_reclassified_cog\xingu_river_wetland_dual-season_veg_flood_AA100m_reclassified_cog.tif"

RECLASSIFICACAO = {
    0: 0, 1: 0, 11: 1, 13: 1, 21: 1, 23: 1, 33: 1, 41: 1, 44: 0, 45: 1,
    51: 1, 55: 1, 66: 0, 67: 1, 77: 1, 88: 0, 89: 1, 99: 1, 200: 0, 255: 0,
}

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
# NOTA (herdada de SPEC/requirements.md, REQ-004 / DIV-07): a classe
# original 0 é mapeada para 0, e nodata_saida também é 0 — pixels de
# classe 0 legítima e pixels sem regra/nodata ficam indistinguíveis no
# produto final. Isso já acontecia antes da migração; não foi alterado
# aqui, apenas continua sendo um ponto em aberto (ver SPEC/requirements.md).

with RasterPipeline(
    ENTRADA,
    SAIDA_FINAL,
    origem="HESS 2015 — Amazon wetland dual-season vegetation/flood map (AA100m), reclassificado, recorte: bacia do rio Xingu",  # TODO: confirmar citação completa do dataset
    remover_temp=False,  # decisão deliberada (DEC-007): mantém intermediários para depuração manual
) as p:
    p.clip(MASCARA_GPKG, crop=True, all_touched=False)
    p.reclassify(mapeamento=RECLASSIFICACAO, nodata_saida=0, dtype="uint8")

print(f"COG válido: {p.cog_valido}")
print(f"Metadados: {p.metadata_path}")
