# raspy

**Raster Preparation System (Python)**

Ferramenta operacional leve para preparação, padronização e documentação de dados raster ambientais. Desenvolvida para equipes científicas pequenas trabalhando com dados da Amazônia.

---

## Motivação

Projetos GIS exploratórios tendem a acumular arquivos duplicados, projeções inconsistentes e pipelines irreproduziveis. O raspy resolve isso oferecendo uma estrutura modular e rastreável para transformar rasters brutos em produtos padronizados — com foco em Cloud Optimized GeoTIFF (COG).

---

## Funcionalidades (v0.2)

- Ingestão e validação de rasters GeoTIFF
- Recorte espacial por geometria de GeoPackage
- Transformação de valores em blocos (sem estourar RAM): escala e reclassificação categórica
- Conversão para COG válido com compressão DEFLATE, LZW ou ZSTD
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
│   ├── clip.py         # recorte espacial por geometria de GeoPackage
│   ├── transform.py    # transformação de valores em blocos (escala, reclassificação)
│   ├── cog.py          # conversão e validação COG
│   └── metadata.py     # geração de metadados YAML
│
├── examples/
│   └── ...             # scripts de pipelines reais (ver seção "Como usar")
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
| `geopandas` | leitura da geometria de recorte em GeoPackage (usado por `clip.py`) |
| `pyyaml` | geração de metadados |
| `numpy` | manipulação de arrays |

---

## Como usar

### 1. Usando como módulos Python

**Exemplo A — dado contínuo (ex.: elevação em cm → m), sem recorte:**

```python
from raspy import ingest, transform, cog, metadata

# Valida e lê metadados
info = ingest.abrir_raster("entrada.tif")

# Converte valores em blocos (ex: cm → m)
transform.aplicar_fator_escala("entrada.tif", "temp.tif", fator=100.0)

# Converte para COG (overview 'average' é recomendado para dados contínuos)
cog.converter_para_cog("temp.tif", "saida_cog.tif", resampling_overview="average")

# Valida o COG
cog.validar_cog("saida_cog.tif")

# Gera metadados YAML — os parâmetros aqui devem sempre refletir
# os mesmos valores realmente usados nas chamadas acima.
metadata.gerar_metadados(
    "entrada.tif", "saida_cog.tif",
    info_raster=info,
    fator_escala=100.0,
    resampling_overview="average",
)
```

**Exemplo B — dado categórico (ex.: mapa de classes), com recorte e reclassificação:**

```python
from raspy import ingest, clip, transform, cog, metadata

# Valida e lê metadados
info = ingest.abrir_raster("entrada.tif")

# Recorta pela geometria de um GeoPackage
clip.recortar_por_gpkg("entrada.tif", "area.gpkg", "clip.tif", crop=True)

# Reclassifica valores categóricos
transform.reclassificar(
    "clip.tif", "temp.tif",
    mapeamento={1: 0, 2: 1, 3: 1},
    nodata_saida=0,
    dtype="uint8",
)

# Converte para COG ('nearest' é recomendado para dados categóricos)
cog.converter_para_cog("temp.tif", "saida_cog.tif", resampling_overview="nearest")

# Valida o COG
cog.validar_cog("saida_cog.tif")

# Gera metadados YAML — repare que resampling_overview é "nearest"
# aqui também, coerente com a chamada de conversão acima.
metadata.gerar_metadados(
    "clip.tif", "saida_cog.tif",
    info_raster=info,
    resampling_overview="nearest",
)
```

> **Atenção:** `metadata.gerar_metadados()` não deduz automaticamente os parâmetros usados nas etapas anteriores — cada valor (fator de escala, método de overview, etc.) precisa ser repassado manualmente e deve corresponder exatamente ao que foi executado. Divergências aqui já ocorreram em versões anteriores dos scripts de exemplo. A automação desse ponto (para que os metadados sejam derivados diretamente da execução real, e não redigitados) está planejada para uma futura API de pipeline (ver Roadmap).

### 2. Rodando um exemplo completo

```bash
conda activate seu_ambiente
python examples/<nome_do_script>.py
```

Os scripts em `examples/` são pipelines reais de datasets específicos do projeto, não um template único — cada um combina `ingest`, `clip`, `transform` (escala ou reclassificação) e `cog`/`metadata` de acordo com a necessidade daquele dado.

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
clip.py      — recorte espacial por geometria de GeoPackage (opcional)
    ↓
transform.py — transformação de valores em blocos (escala e/ou reclassificação)
    ↓
cog.py       — conversão para COG + validação
    ↓
metadata.py  — geração de YAML com histórico
    ↓
COG final + .yaml
```

> `clip.py` e as transformações de `transform.py` são opcionais e podem ser combinadas em qualquer ordem — a biblioteca não impõe uma sequência fixa. Quem decide quais etapas usar, e em qual ordem, é o script que orquestra o pipeline (ver `examples/`). Isso é uma escolha de design atual, não uma limitação a esconder: dá liberdade ao usuário, mas exige atenção ao montar cada pipeline manualmente.

---

## Roadmap

**v0.1** — conversão para COG com rastreabilidade *(concluído)*

**v0.2** — recorte territorial via GeoPackage; reclassificação categórica de valores *(concluído)*

**v0.3** — API de pipeline (`RasterPipeline`) para compor etapas de forma programática, com padronização automática do passo final (conversão para COG, validação e geração de metadados), reduzindo o risco de metadados divergentes do processamento real *(em planejamento)*

**v0.4** — reprojeção e alinhamento espacial

**v0.5** — CLI com Typer

**v0.6** — integração com object storage S3-compatible