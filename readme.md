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
project/
│
├── SPEC/                # documentação de fonte de verdade (científica, requisitos, decisões)
├── CONTEXT.md
│
├── src/raspy/
│   ├── __init__.py      # expõe os módulos, incluindo RasterPipeline
│   ├── ingest.py        # abertura e validação do raster
│   ├── clip.py          # recorte espacial por geometria de GeoPackage
│   ├── transform.py     # transformação de valores em blocos (escala, reclassificação)
│   ├── cog.py           # conversão e validação COG
│   ├── metadata.py      # geração de metadados YAML
│   └── pipeline.py      # RasterPipeline — composição de pipeline com finalização automática
│
├── tests/
│   ├── unit/            # testes de função
│   ├── pipeline/        # testes de integração (RasterPipeline)
│   └── synthetic_data/  # geradores de datasets sintéticos usados pelos testes
│
├── examples/            # scripts de pipelines reais (ver seção "Como usar")
├── data/
├── docs/
│
├── pyproject.toml       # permite `pip install -e .`
├── README.md
└── CHANGELOG.md
```

---

## Instalação

```bash
conda env create -f environment.yml
conda activate raspy_env
pip install -e .
```

O `pip install -e .` é o que torna `import raspy` disponível em qualquer lugar (inclusive nos testes) — sem ele, `python examples/algum_script.py` e `pytest` só funcionam por acidente de diretório atual, e podem falhar de forma diferente em cada máquina/sistema operacional (isso já aconteceu — ver `CHANGELOG.md`).

Para rodar os testes, instale também o `pytest` (ferramenta de desenvolvimento, não faz parte de `environment.yml`):

```bash
pip install pytest
pytest tests/
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

### 1. Usando `RasterPipeline` (recomendado)

`RasterPipeline` compõe `clip()`, `scale()` e `reclassify()` em qualquer ordem, qualquer quantidade de vezes, e finaliza automaticamente o pipeline (conversão para COG, validação e metadados) ao sair do bloco `with` — sem que você precise chamar `cog.converter_para_cog()`, `cog.validar_cog()` nem `metadata.gerar_metadados()` manualmente, e sem risco de os parâmetros registrados nos metadados divergirem do que de fato foi executado (ver `CHANGELOG.md`, DIV-04/DIV-05/DIV-12).

**Exemplo A — dado contínuo (ex.: elevação em cm → m), sem recorte:**

```python
from raspy import RasterPipeline

with RasterPipeline("entrada.tif", "saida_cog.tif") as p:
    p.scale(fator=100.0)
    # resampling_overview é inferido automaticamente como "average"
    # depois de scale() — não precisa ser informado aqui.

print("COG válido:", p.cog_valido)
print("Metadados em:", p.metadata_path)
```

**Exemplo B — dado categórico (ex.: mapa de classes), com recorte e reclassificação:**

```python
from raspy import RasterPipeline

with RasterPipeline("entrada.tif", "saida_cog.tif") as p:
    p.clip("area.gpkg", crop=True)
    p.reclassify(mapeamento={1: 0, 2: 1, 3: 1}, nodata_saida=0, dtype="uint8")
    # resampling_overview é inferido automaticamente como "nearest"
    # depois de reclassify().

print("COG válido:", p.cog_valido)
print("Metadados em:", p.metadata_path)
```

> Se nenhuma etapa for chamada dentro do `with`, o raster de entrada é convertido para COG diretamente, sem transformação. Se uma exceção ocorrer dentro do `with`, nada é finalizado (nenhum COG nem metadado é gerado a partir de um pipeline incompleto) e a exceção é sempre propagada.

### 2. Usando os módulos individualmente (modo manual/avançado)

Ainda é possível chamar `ingest`, `clip`, `transform`, `cog` e `metadata` diretamente, sem `RasterPipeline` — por exemplo, para inspecionar um resultado intermediário antes de decidir o próximo passo. Nesse modo, **você é responsável por manter os parâmetros passados a `metadata.gerar_metadados()` (fator de escala, `nodata_saida`, `resampling_overview`) idênticos ao que de fato foi executado nas etapas anteriores** — é exatamente esse trabalho manual que `RasterPipeline` elimina.

```python
from raspy import ingest, clip, transform, cog, metadata

info = ingest.abrir_raster("entrada.tif")
clip.recortar_por_gpkg("entrada.tif", "area.gpkg", "clip.tif", crop=True)
transform.reclassificar("clip.tif", "temp.tif", mapeamento={1: 0, 2: 1, 3: 1}, nodata_saida=0, dtype="uint8")
cog.converter_para_cog("temp.tif", "saida_cog.tif", resampling_overview="nearest")
cog.validar_cog("saida_cog.tif")
metadata.gerar_metadados(
    "clip.tif", "saida_cog.tif",
    info_raster=info,
    resampling_overview="nearest",  # precisa bater com o valor usado acima — ninguém garante isso por você aqui
)
```

### 3. Rodando um exemplo completo

```bash
conda activate raspy_env
python examples/<nome_do_script>.py
```

Os scripts em `examples/` são pipelines reais de datasets científicos do projeto (HESS 2015, Souza 2025), cada um usando `RasterPipeline` com a combinação de `clip`/`reclassify` que faz sentido para aquele dataset específico — não é um template único copiado 5 vezes (ver `CHANGELOG.md` para o que isso corrigiu).

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

**v0.3** — API de pipeline (`RasterPipeline`) para compor etapas de forma programática, com padronização automática do passo final (conversão para COG, validação e geração de metadados) *(concluído)*; migração dos 5 scripts de `examples/` para `RasterPipeline` *(concluído)*

**v0.4** — reprojeção e alinhamento espacial

**v0.5** — CLI com Typer

**v0.6** — integração com object storage S3-compatible
 
