# examples/hess2015_wetland_vegetation_dual_season_flood_map_3arcsec.py
#
# HESS 2015 — mapa de vegetação de áreas úmidas / inundação dual-season
# da bacia amazônica, resolução de 3 arc-seconds, escala Amazônia (sem
# recorte para uma sub-região).
#
# NOTA DE MIGRAÇÃO: este arquivo se chamava "fathom_dem.py" e trazia um
# cabeçalho e um "origem" de metadados falando de FathomDEM — um
# copiar-e-colar incorreto, herdado de um template comum aos 5 exemplos
# (nenhum dos 5 é FathomDEM). Corrigido aqui. O dicionário
# RECLASSIFICACAO existia neste arquivo mas nunca era usado (nenhuma
# chamada a reclassificar() existia) — mantido comentado abaixo,
# disponível caso a reclassificação binária também seja desejada nesta
# escala; não a ativei por conta própria porque isso muda o produto
# científico gerado, e essa é uma decisão do dono do projeto, não uma
# correção de bug.
#
# Como rodar (com o ambiente já configurado — ver README.md):
#   conda activate raspy_env
#   python examples/hess2015_wetland_vegetation_dual_season_flood_map_3arcsec.py

from raspy import RasterPipeline

# ---------------------------------------------------------------------------
# Caminhos — ajuste para o seu ambiente
# ---------------------------------------------------------------------------

ENTRADA = r"C:\Users\renan\OneDrive\Projetos\pulsamazonia\data\abiotico\amazon_basin\hess2015\raw\LC07_Amazon_Wetlands_1284\data\LBA_Amazon_wetland_dual-season_veg_flood_3arcsec.tif"
SAIDA_FINAL = r"C:\Users\renan\OneDrive\Projetos\pulsamazonia\data\abiotico\amazon_basin\hess2015\processed\wetland_vegetation_dual-season_flood_map\LBA_Amazon_wetland_dual-season_veg_flood_3arcsec_cog\LBA_Amazon_wetland_dual-season_veg_flood_3arcsec_cog.tif"

# Disponível, mas não usado nesta escala (ver nota de migração acima)
RECLASSIFICACAO = {
    0: 0, 1: 0, 11: 1, 13: 1, 21: 1, 23: 1, 33: 1, 41: 1, 44: 0, 45: 1,
    51: 1, 55: 1, 66: 0, 67: 1, 77: 1, 88: 0, 89: 1, 99: 1, 200: 0, 255: 0,
}

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
# Estado atual: nenhuma transformação é aplicada — apenas ingestão,
# conversão para COG, validação e metadados (comportamento herdado do
# arquivo original, onde recorte e reclassificação estavam desativados).

with RasterPipeline(
    ENTRADA,
    SAIDA_FINAL,
    origem="HESS 2015 — Amazon wetland dual-season vegetation/flood map (3 arc-seconds)",  # TODO: confirmar citação completa do dataset
    remover_temp=False,  # decisão deliberada (DEC-007): mantém intermediários para depuração manual
) as p:
    pass
    # p.reclassify(mapeamento=RECLASSIFICACAO, nodata_saida=0, dtype="uint8")

print(f"COG válido: {p.cog_valido}")
print(f"Metadados: {p.metadata_path}")
