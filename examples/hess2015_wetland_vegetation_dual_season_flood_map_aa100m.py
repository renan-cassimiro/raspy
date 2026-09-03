# examples/hess2015_wetland_vegetation_dual_season_flood_map_aa100m.py
#
# HESS 2015 — mesmo mapa de vegetação/inundação dual-season, resolução
# AA100m, escala Amazônia (sem recorte para uma sub-região, sem
# reclassificação — conversão direta para COG).
#
# NOTA DE MIGRAÇÃO: cabeçalho e "origem" corrigidos (ver
# hess2015_wetland_vegetation_dual_season_flood_map_3arcsec.py para o
# detalhe do copiar-e-colar incorreto herdado do template original).
#
# Como rodar (com o ambiente já configurado — ver README.md):
#   conda activate raspy_env
#   python examples/hess2015_wetland_vegetation_dual_season_flood_map_aa100m.py

from raspy import RasterPipeline

# ---------------------------------------------------------------------------
# Caminhos — ajuste para o seu ambiente
# ---------------------------------------------------------------------------

ENTRADA = r"C:\Users\renan\OneDrive\Projetos\pulsamazonia\data\abiotico\amazon_basin\hess2015\raw\LC07_Amazon_Wetlands_1284\data\LBA_Amazon_wetland_dual-season_veg_flood_AA100m.tif"
SAIDA_FINAL = r"C:\Users\renan\OneDrive\Projetos\pulsamazonia\data\abiotico\amazon_basin\hess2015\processed\wetland_vegetation_dual-season_flood_map\LBA_Amazon_wetland_dual-season_veg_flood_AA100m_cog\LBA_Amazon_wetland_dual-season_veg_flood_AA100m_cog.tif"

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
# Estado atual: nenhuma transformação — apenas ingestão, conversão para
# COG, validação e metadados (idêntico, em intenção, ao arquivo
# "_3arcsec.py"; a única diferença real entre os dois é a resolução de
# entrada). Se essa duplicação não for intencional, um dos dois pode
# ser removido do projeto.

with RasterPipeline(
    ENTRADA,
    SAIDA_FINAL,
    origem="HESS 2015 — Amazon wetland dual-season vegetation/flood map (AA100m)",  # TODO: confirmar citação completa do dataset
    remover_temp=False,  # decisão deliberada (DEC-007): mantém intermediários para depuração manual
) as p:
    pass

print(f"COG válido: {p.cog_valido}")
print(f"Metadados: {p.metadata_path}")
