# Contexto do Projeto

## O que este projeto faz

**raspy — Raster Preparation System (Python)** é uma ferramenta para preparação de dados raster ambientais, com foco em:

- ingestão e validação de rasters;
- recorte espacial por geometria de GeoPackage;
- transformação de valores (escala e reclassificação categórica);
- conversão para Cloud Optimized GeoTIFF (COG);
- validação do COG gerado;
- geração de metadados de processamento em YAML.

A motivação declarada é reduzir problemas comuns em projetos GIS exploratórios: duplicação de arquivos, inconsistência de projeções e pipelines pouco reproduzíveis.

O projeto está migrando de uma coleção de funções soltas orquestradas manualmente em scripts para uma arquitetura com uma API de pipeline (`RasterPipeline`) que padroniza a etapa final (COG → validação → metadados), mantendo a composição das transformações livre para o usuário.

## Status atual

- Pipeline funcional cobrindo: ingestão → recorte (opcional) → transformação numérica (escala e/ou reclassificação, opcional) → conversão para COG → validação → geração de metadados.
- Uma reconstrução completa do projeto (fluxo, componentes, dependências, riscos) foi feita a partir do código-fonte e registrada em `SPEC/scientific.md` e `SPEC/requirements.md`.
- Uma matriz de divergências (`divergence-matrix.md`) comparou especificação científica, requisitos, implementação e testes, identificando 14 divergências (DIV-01 a DIV-14).
- Em 2026-08-30, decisões foram tomadas para cada divergência (registradas em `SPEC/decisions.md`, DEC-001 a DEC-010) e as correções de baixo risco já foram aplicadas:
  - `readme.md`: roadmap, exemplo de uso e tabela de dependências corrigidos (DIV-01, DIV-02, DIV-03).
  - `environment.yml`: dependências sem uso identificável removidas; caminho de máquina pessoal removido (DIV-09).
  - `clip.py`: aviso explícito adicionado para o caso de raster sem `nodata` definido (DIV-11).
  - Os 5 scripts de exemplo: `resampling_overview` dos metadados alinhado ao valor real usado na conversão para COG (DIV-12); decisão de manter `remover_temp=False` documentada via comentário (DIV-13).
- Ficou decidido (DEC-001) que a API `RasterPipeline` usará um objeto com **context manager** (`with RasterPipeline(...) as p:`), permitindo composição livre das transformações mas automatizando a etapa final do pipeline. **Ainda não implementada.**
- Divergências que dependem da `RasterPipeline` para serem resolvidas de forma estrutural (não pontual) ficaram deliberadamente pendentes: DIV-04 (nodata_saida incorreto nos metadados), DIV-05 (caminho_entrada inconsistente), DIV-06/07/08 (scripts de exemplo duplicados e sem pipeline comum).
- DIV-14 (a função `aplicar_fator_escala()` nunca é exercitada nos exemplos reais) foi deliberadamente ignorada por ora (DEC-009).

## Tarefa atual

Construir um catálogo de **datasets sintéticos** para revelar, de forma controlada, os erros mais perigosos identificados na matriz de divergências — antes de investir em uma suíte de testes formal (`tests/unit`, `tests/pipeline`). Ordem de prioridade combinada:

1. Raster categórico com classe `0` legítima e `nodata_saida=0` (ataca REQ-004, item questionável / DIV-07).
2. Raster sem `nodata` definido, usado com `clip.py` (ataca REQ-002/REQ-011, DIV-11).
3. Raster multibanda (ataca o pressuposto implícito de banda única em `transform.py`).
4. Raster com `nodata` original diferente de `nodata_saida` (caso "feliz" de propagação de nodata).
5. Par contínuo vs. categórico, mesmos parâmetros de COG (valida a recomendação `average`/`nearest` do item 8.4 de `SPEC/scientific.md`).
6. Geometria de recorte que não intersecta o raster de entrada.
7. Raster grande o suficiente para múltiplos blocos, com nodata cruzando a fronteira de um bloco.

## Arquitetura (resumo)

Cinco responsabilidades principais, hoje encadeadas manualmente pelo script de orquestração:

```text
ingest.py   → "O arquivo é utilizável?"
clip.py     → "Qual parte do raster interessa?" (opcional)
transform.py→ "Como os pixels devem mudar?" (escala e/ou reclassificação, opcional)
cog.py      → "Como o produto será armazenado?" (conversão + validação)
metadata.py → "Como registrar o que foi feito?"
```

Planejado (DEC-001, ainda não implementado):

```text
with RasterPipeline(entrada) as p:
    p.clip(...)          # opcional, qualquer ordem
    p.scale(...)          # opcional
    p.reclassify(...)     # opcional
# ao sair do bloco: cog + validação + metadados executados
# automaticamente, com os mesmos parâmetros reais usados acima
```

## Arquivos importantes

- `ingest.py` — abertura e validação inicial do raster.
- `clip.py` — recorte espacial via geometria de um GeoPackage; agora avisa quando `nodata` não está definido.
- `transform.py` — transformações numéricas: `aplicar_fator_escala()` e `reclassificar()`.
- `cog.py` — conversão para COG (via `rio-cogeo`) e validação do COG.
- `metadata.py` — geração de metadados de processamento em YAML; **ponto central de divergência ainda não resolvida** (DIV-04, DIV-05).
- `examples/` — 5 scripts de pipelines reais de datasets específicos; corrigidos pontualmente, mas ainda não migrados para `RasterPipeline`.
- `environment.yml` — limpo; reflete apenas as dependências efetivamente usadas.
- `SPEC/scientific.md` — especificação científica provisória (EXPLÍCITO/IMPLÍCITO/DESCONHECIDO/QUESTIONÁVEL/`[EM ABERTO]`).
- `SPEC/requirements.md` — requisitos derivados do comportamento observado, com critérios de aceitação testáveis.
- `SPEC/decisions.md` — histórico de decisões (DEC-001 a DEC-010).
- `divergence-matrix.md` — matriz de divergências entre especificação, requisitos, implementação e testes.

## Decisões ativas

Ver `SPEC/decisions.md` para o registro completo. Destaques:

- **DEC-001**: `RasterPipeline` com context manager para automatizar a etapa final do pipeline.
- **DEC-003/DEC-004**: correções estruturais de metadados (nodata_saida, caminho_entrada) e reescrita dos exemplos ficam condicionadas à existência da `RasterPipeline`, em vez de remendos pontuais repetidos.
- **DEC-009**: `aplicar_fator_escala()` não será exercitada nos exemplos por ora — decisão deliberada, não esquecimento.
- **DEC-010**: dados sintéticos antes de suíte de testes formal.

## Problemas conhecidos

| Divergência | Status |
|---|---|
| DIV-01 (roadmap desatualizado) | ✅ Corrigido (2026-08-30) |
| DIV-02 (exemplo de uso incompleto) | ✅ Corrigido (2026-08-30) |
| DIV-03 (dependência `geopandas` não listada) | ✅ Corrigido (2026-08-30) |
| DIV-04 (`nodata_saida` incorreto nos metadados) | ⏳ Pendente — depende da `RasterPipeline` (DEC-003) |
| DIV-05 (`caminho_entrada` inconsistente) | ⏳ Pendente — depende da `RasterPipeline` (DEC-003) |
| DIV-06 (COG/metadados gerados a partir de dado bruto não processado) | ⏳ Pendente — depende da migração dos exemplos (DEC-004) |
| DIV-07 (classe válida coincide com nodata) | ⏳ Pendente — aberto em `SPEC/requirements.md` (REQ-004); dataset sintético #1 planejado |
| DIV-08 (exemplos duplicados sem pipeline comum) | ⏳ Pendente — depende da migração dos exemplos (DEC-004) |
| DIV-09 (dependências sem uso no ambiente) | ✅ Corrigido (2026-08-30) |
| DIV-10 (ausência de testes) | ⏳ Em andamento — próxima tarefa é construir os datasets sintéticos |
| DIV-11 (`nodata=None` no recorte sem tratamento) | ✅ Corrigido (2026-08-30) |
| DIV-12 (`resampling_overview` divergente nos metadados) | ✅ Corrigido nos exemplos atuais (2026-08-30); correção estrutural definitiva depende da `RasterPipeline` |
| DIV-13 (`remover_temp=False` não documentado) | ✅ Corrigido — decisão documentada via comentário (2026-08-30) |
| DIV-14 (`aplicar_fator_escala()` nunca exercitada) | ❌ Ignorado deliberadamente (DEC-009) |

## Testes atuais

Nenhum teste automatizado existe no projeto até o momento. A tarefa atual (ver acima) é construir datasets sintéticos que sirvam de base para os primeiros testes, priorizando os cenários que revelam erros silenciosos de dados (não apenas erros de execução).

## Últimas mudanças

- Matriz de divergências (`divergence-matrix.md`) produzida comparando especificação científica, requisitos, implementação e testes.
- Decisões registradas para todas as 14 divergências (`SPEC/decisions.md`, DEC-001 a DEC-010), incluindo a aprovação do design da `RasterPipeline` com context manager.
- Correções aplicadas: `readme.md`, `environment.yml`, `clip.py` e os 5 scripts de `examples/`.
- Reorganização da documentação de especificação para a estrutura `SPEC/` (`scientific.md`, `requirements.md`, `decisions.md`), conforme modelo combinado.
- `SPEC/scientific.md` e `SPEC/requirements.md` atualizados para refletir o que foi corrigido e o que permanece em aberto.