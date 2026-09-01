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

#Pastas fake para jogar direto na estrutura de pastas do projeto dentro do bdc-lab
ENTRADA      = r"../../grupos/inpa/abiotic_data/xingu_river/uhe2025/processed/fathomdem/xingu_river_fathomdem_30m_cog/xingu_river_fathomdem_30m_cog.tif"
SAIDA_TEMP   = r"../../grupos/inpa/abiotic_data/xingu_river/uhe2025/processed/fathomdem/xingu_river_fathomdem_slope_30m_cog/xingu_river_fathomdem_slope_30m_temp.tif"
SAIDA_FINAL  = r"../../grupos/inpa/abiotic_data/xingu_river/uhe2025/processed/fathomdem/xingu_river_fathomdem_slope_30m_cog/xingu_river_fathomdem_slope_30m_cog.tif"

# ---------------------------------------------------------------------------
# Garantir que os diretórios de saída existam
# ---------------------------------------------------------------------------
for caminho in [SAIDA_TEMP, SAIDA_FINAL]:
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

inicio = datetime.now()
print(f"[{inicio}] Iniciando processamento\n")

# Passo 1: Ingestão — valida e lê metadados do raster de entrada
print("→ Passo 1: Ingestão")
info = ingest.abrir_raster(ENTRADA)
print(f"  CRS: {info['crs']}")
print(f"  Resolução: {info['resolucao']}")
print(f"  Bandas: {info['bandas']}")
print(f"  Nodata original: {info['nodata']}")

# Passo 2: Calcular declividade
print("\n→ Passo 3: Transformação (÷ 100)")
transform.calcular_declividade(
    caminho_entrada=ENTRADA,
    caminho_saida=SAIDA_TEMP,
    nodata_saida=-9999.0,
    unidade="percent"
)

# Passo 3: Conversão para COG
print("\n→ Passo 3: Conversão para COG")
cog.converter_para_cog(
    caminho_entrada=SAIDA_TEMP, #mudar quando for rodar transformação
    caminho_saida=SAIDA_FINAL,
    compressao="deflate",
    resampling_overview="average",
    remover_temp=False,           # remove o arquivo temporário ao final
)

# Passo 4: Validação do COG gerado
print("\n→ Passo 4: Validação COG")
valido = cog.validar_cog(SAIDA_FINAL)

# Passo 5: Geração de metadados YAML
print("\n→ Passo 5: Metadados")
metadata.gerar_metadados(
    caminho_entrada=SAIDA_TEMP,
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

