# raspy

**Raster Preparation System (Python)**

Ferramenta operacional leve para preparação, padronização e documentação de dados raster ambientais. Desenvolvida para equipes científicas pequenas trabalhando com dados da Amazônia.

---

## Motivação

Projetos GIS exploratórios tendem a acumular arquivos duplicados, projeções inconsistentes e pipelines irreproduziveis. O raspy resolve isso oferecendo uma estrutura modular e rastreável para transformar rasters brutos em produtos padronizados — com foco em Cloud Optimized GeoTIFF (COG).

---

## Funcionalidades (v0.1)

- Ingestão e validação de rasters GeoTIFF
- Transformação de valores em blocos (sem estourar RAM)
- Conversão para COG válido com compressão DEFLATE ou LZW
- Validação de conformidade COG
- Geração automática de metadados YAML com histórico de processamento
- Checksum MD5 opcional para verificação de integridade

---

## Estrutura do projeto

```
raspy/
│
├── raspy/
│   ├── __init__.py     # expõe os módulos
│   ├── ingest.py       # abertura e validação do raster
│   ├── transform.py    # transformação de valores em blocos
│   ├── cog.py          # conversão e validação COG
│   └── metadata.py     # geração de metadados YAML
│
├── examples/
│   └── fathomdem.py    # exemplo completo: FathomDEM cm → m → COG
│
├── logs/
└── README.md
```

---

## Dependências

Gerenciadas pelo seu ambiente conda. Pacotes necessários:

| Pacote | Uso |
|---|---|
| `rasterio` | leitura e escrita de rasters |
| `rio-cogeo` | conversão e validação COG |
| `pyyaml` | geração de metadados |
| `numpy` | manipulação de arrays |

---

## Como usar

### 1. Usando como módulos Python

```python
from raspy import ingest, transform, cog, metadata

# Valida e lê metadados
info = ingest.abrir_raster("entrada.tif")

# Converte valores em blocos (ex: cm → m)
transform.aplicar_fator_escala("entrada.tif", "temp.tif", fator=100.0)

# Converte para COG
cog.converter_para_cog("temp.tif", "saida_cog.tif")

# Valida o COG
cog.validar_cog("saida_cog.tif")

# Gera metadados YAML
metadata.gerar_metadados("entrada.tif", "saida_cog.tif", info_raster=info)
```

### 2. Rodando um exemplo completo

```bash
conda activate seu_ambiente
python examples/fathomdem.py
```

---

## Metadados gerados

Para cada COG gerado, o raspy produz automaticamente um `.yaml` no mesmo diretório:

```yaml
raspy_version: 0.1.0
data_processamento: '2025-06-01T14:32:10'

entrada:
  arquivo: /dados/fathomdem_recortado.tif
  origem: FathomDEM v1.0 — https://www.fathom.global

saida:
  arquivo: /dados/fathomdem_metros_cog.tif
  formato: Cloud Optimized GeoTIFF (COG)
  checksum_md5: a3f1b2c9...

espacial:
  crs: EPSG:4326
  resolucao_x: 0.000277...
  resolucao_y: 0.000277...
  bandas: 1
  bounding_box:
    left: -78.0
    bottom: -20.0
    right: -44.0
    top: 5.5
  nodata_original: -32768

processamento:
  fator_escala: 100.0
  nodata_saida: -9999.0
  compressao: deflate
  resampling_overview: average
```

---

## Pipeline operacional

```
Raster bruto
    ↓
ingest.py    — validação e leitura de metadados
    ↓
transform.py — transformação de valores em blocos
    ↓
cog.py       — conversão para COG + validação
    ↓
metadata.py  — geração de YAML com histórico
    ↓
COG final + .yaml
```

---

## Roadmap

**v0.1** — conversão para COG com rastreabilidade *(atual)*

**v0.2** — recorte territorial (shapefile, GeoPackage, bounding box)

**v0.3** — reprojeção e alinhamento espacial

**v0.4** — CLI com Typer

**v0.5** — integração com object storage S3-compatible
