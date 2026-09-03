# Changelog

Formato inspirado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Datas no formato AAAA-MM-DD.

## [Não lançado]

### Corrigido (pós-empacotamento)
- `tests/conftest.py` inseria `src/` no `sys.path` manualmente, o que falhou em Windows (`ModuleNotFoundError: No module named 'raspy'` ao rodar `pytest`). Substituído por instalação editável do pacote via `pyproject.toml` + `pip install -e .`, que é independente de plataforma e não depende de como o pytest resolve caminhos relativos na coleta de testes.

### Corrigido (pós-empacotamento, 2ª rodada — migração dos exemplos)
- `src/raspy/pipeline.py`: `RasterPipeline` não expunha `cog_valido` nem `metadata_path` como atributos públicos depois do bloco `with` — o resultado de `cog.validar_cog()` e o caminho retornado por `metadata.gerar_metadados()` eram descartados internamente. Bug encontrado ao migrar `examples/` (os scripts novos tentavam imprimir `p.cog_valido` e `p.metadata_path`, e isso quebrava com `AttributeError`). Corrigido armazenando os dois como atributos de instância, e travado com um teste de regressão em `tests/pipeline/test_raster_pipeline.py`.
- `examples/*.py`: os 5 scripts foram **reescritos** para usar `RasterPipeline` (DIV-06, DIV-07, DIV-08 — finalmente resolvidos, não apenas mitigados). Isso eliminou: as variáveis manuais `SAIDA_CLIP`/`SAIDA_TEMP`, as chamadas separadas a `cog.converter_para_cog()`/`cog.validar_cog()`/`metadata.gerar_metadados()`, e o `sys.path.insert()` manual (agora desnecessário graças a `pip install -e .`).
- **Bug de copiar-e-colar encontrado durante a migração** (não fazia parte da matriz de divergências original): todos os 5 exemplos tinham cabeçalho e `origem` de metadados dizendo "FathomDEM", herdados de um template comum — nenhum dos 5 datasets é FathomDEM. Corrigido caso a caso; adicionado `TODO: confirmar citação completa do dataset` onde a URL/citação exata do HESS 2015 não pôde ser confirmada (evitando inventar uma referência).
- Dois dos exemplos (`fathom_dem.py` e `hess2015_wetland_vegetation_dual_season_flood_map.py`, originais) faziam exatamente a mesma coisa (conversão direta para COG, sem nenhuma transformação), diferindo apenas na resolução do raster de entrada (3 arc-seconds vs. AA100m). Renomeados para `hess2015_wetland_vegetation_dual_season_flood_map_3arcsec.py` e `..._aa100m.py` para tornar essa diferença explícita — mas a duplicação de intenção entre os dois permanece e não foi resolvida (é uma decisão do dono do projeto, não uma correção de bug).
- Um dicionário `RECLASSIFICACAO` existia em um dos exemplos (o antigo `fathom_dem.py`) sem nunca ser usado por nenhuma chamada de `reclassificar()`. Mantido comentado no arquivo migrado, com nota explícita — **não foi ativado** por decisão própria, porque isso mudaria o produto científico gerado.

### Adicionado
- `src/raspy/pipeline.py`: `RasterPipeline`, API de composição de pipeline com `clip()`, `scale()` e `reclassify()` livres (qualquer ordem, qualquer quantidade), e finalização automática (conversão para COG, validação e geração de metadados) via context manager (REQ-009, DEC-001, DEC-011).
- `tests/`: primeira suíte de testes automatizados do projeto — 5 testes de integração em `tests/pipeline/` (formalizando os cenários de `SPEC/experiments.md`, EXP-001) e 7 testes unitários em `tests/unit/` para `ingest.py`, `transform.py` e `clip.py`.
- `tests/synthetic_data/generators.py`: primeiro dataset sintético do catálogo planejado em `CONTEXT.md` — raster categórico com classe `0` legítima coincidindo com `nodata=-1` original, e um GeoPackage de recorte associado.
- `SPEC/experiments.md`: log de exploração, separado de `decisions.md` (decisões fechadas) e `requirements.md` (comportamento normativo).
- `CONTEXT.md`, `SPEC/scientific.md`, `SPEC/requirements.md`, `SPEC/decisions.md`: reconstrução completa da documentação do projeto a partir do código-fonte existente.
- `divergence-matrix.md`: matriz comparando especificação científica, requisitos, implementação e testes, identificando 14 divergências (DIV-01 a DIV-14).

### Corrigido
- `readme.md`: roadmap atualizado (recorte territorial e reclassificação categórica já estavam implementados, não mais listados como futuros); exemplo de uso passou a incluir `clip` e `reclassificar`; tabela de dependências passou a listar `geopandas` (DIV-01, DIV-02, DIV-03).
- `environment.yml`: removidas dependências sem uso identificável no código (`pyflwdir`, `requests`, `pyarrow`, `python-duckdb`) e a linha `prefix:` com caminho de máquina pessoal (DIV-09).
- `src/raspy/clip.py`: passou a emitir um aviso explícito quando o raster de entrada não possui `nodata` definido, em vez de depender do comportamento padrão implícito do `rasterio.mask.mask()` (DIV-11).
- `examples/*.py` (5 scripts): `resampling_overview` registrado em `metadata.gerar_metadados()` corrigido para corresponder ao valor real usado em `cog.converter_para_cog()` (DIV-12); decisão de manter `remover_temp=False` documentada via comentário em vez de deixada implícita (DIV-13).
- `src/raspy/metadata.py`: `gerar_metadados()` passou a aceitar um parâmetro `nodata_saida` explícito (opcional, com o comportamento legado mantido por compatibilidade quando omitido) — usado por `RasterPipeline` para reportar o nodata real do arquivo de saída em vez de inferi-lo de `fator_escala` (base da correção estrutural de DIV-04).

### Conhecido / não corrigido nesta versão
- REQ-008 (registro completo de proveniência nos metadados — geometria de recorte, tabela de reclassificação, ordem das operações) permanece `[EM ABERTO]`. `RasterPipeline` já guarda esse histórico internamente (`self._etapas`), mas deliberadamente não o expõe nos metadados ainda.
- A ambiguidade entre classe válida e nodata na reclassificação (DIV-07 / REQ-004) foi confirmada com dado sintético e coberta por teste (`test_reclassificar_classe_valida_pode_ficar_indistinguivel_de_nodata`), mas nenhuma decisão foi tomada sobre bloquear, avisar ou manter o comportamento atual.
- `src/raspy/transform.py::aplicar_fator_escala()` **continua** sem nenhum exemplo real que a exercite de ponta a ponta (DIV-14) — nenhum dos 5 datasets migrados usa `.scale()`, porque nenhum deles é uma variável contínua (todos são mapas de classe categóricos). Decisão original de ignorar (DEC-009) permanece válida, mas agora por um motivo mais concreto: não há, entre os exemplos reais do projeto, nenhum caso de uso genuíno para essa função ainda.
- Dois exemplos (`..._3arcsec.py` e `..._aa100m.py`) fazem exatamente a mesma coisa em resoluções diferentes — pode ser duplicação intencional ou não; não decidido.
- A URL/citação completa do dataset HESS 2015 não foi confirmada (marcado com `TODO` nos exemplos correspondentes) — os metadados gerados por esses scripts terão um campo `origem` incompleto até isso ser resolvido.

## Antes deste histórico

O projeto já continha, antes do início deste processo de documentação e correção: ingestão e validação de raster (`ingest.py`), recorte por GeoPackage (`clip.py`), transformação por escala e por reclassificação (`transform.py`), conversão e validação de COG (`cog.py`), e geração de metadados YAML (`metadata.py`), além de 5 scripts de exemplo com pipelines reais de datasets científicos (FathomDEM, HESS 2015, Souza 2025, Xingu River). Não há registro anterior de changelog para essa fase — este arquivo começa a partir do ponto em que a documentação e o histórico de decisões passaram a ser mantidos formalmente.
