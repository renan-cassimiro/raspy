# Log de Experimentos — raspy

> Este arquivo registra o que foi **exploração** — validação manual, prova de conceito, teste pontual no terminal — e ainda não virou decisão formal (`decisions.md`), requisito fechado (`requirements.md`) ou teste automatizado (`tests/`). Itens aqui podem ser promovidos para esses outros documentos quando amadurecerem; até lá, ficam registrados apenas como o que de fato foram: exploração.

---

## EXP-001 — Validação manual da `RasterPipeline` com dados sintéticos

**Data:** 2026-08-31

**O que foi feito:** após implementar `pipeline.py` (REQ-009), a implementação foi validada manualmente no terminal, não por uma suíte de testes automatizada. Foi gerado um raster sintético 20×20 (categórico, `int16`, com uma região de classe `0` legítima, uma região de `nodata=-1`, e o restante classe `1`) e um GeoPackage com um polígono cobrindo metade do raster. Cinco cenários foram executados manualmente:

1. `RasterPipeline` sem nenhuma transformação chamada.
2. Apenas `.scale(fator=10.0, nodata_saida=-9999.0)`.
3. `.clip("area.gpkg")` seguido de `.reclassify({0: 0, 1: 1}, nodata_saida=0, dtype="uint8")` — reproduzindo deliberadamente o caso real de DIV-07 (classe `0` legítima coincidindo com `nodata_saida=0`).
4. Uma exceção artificial levantada dentro do bloco `with`, depois de `.scale()` já ter rodado.
5. `remover_temp=False`.

**Resultado:** todos os cinco cenários se comportaram conforme o esperado em DEC-011 (nodata real correto, `fator_escala` nunca hardcoded, `resampling_overview` inferido corretamente, arquivo de entrada nunca apagado, exceção sempre propagada, limpeza de temporários respeitando `remover_temp`). Os detalhes de cada execução (incluindo saída de console) estão registrados na conversa que motivou este projeto — não foram salvos como script formal até este empacotamento.

**Por que ainda é só exploração e não um teste formal:** a validação foi feita digitando comandos diretamente, sem `assert` automatizado nem fixture reutilizável, sem verificação de mensagens de aviso e sem execução via CI. **Promovido para teste formal em 2026-08-31**, junto deste empacotamento — ver `tests/pipeline/test_raster_pipeline.py`, que reproduz os cinco cenários com `assert`s automatizados a partir dos geradores em `tests/synthetic_data/`.

**Pendência real:** apenas 1 dos 7 datasets sintéticos planejados em `CONTEXT.md` (o dataset #1: classe `0` legítima + `nodata_saida=0`) foi de fato construído e exercitado. Os outros seis (raster sem `nodata`, raster multibanda, nodata original ≠ `nodata_saida`, par contínuo/categórico, geometria fora da extensão, raster grande com nodata na borda de um bloco) continuam sendo apenas itens de um plano, não exploração realizada.

---

## EXP-002 — Suposição sobre a natureza dos datasets dos 5 exemplos (DEC-005)

**Data:** 2026-08-30

**O que foi feito:** ao corrigir DIV-12 (divergência de `resampling_overview` entre a conversão real e os metadados registrados nos 5 scripts de `examples/`), foi necessário decidir qual dos dois valores estava errado — o usado na conversão (`"nearest"`) ou o registrado nos metadados (`"average"`). A decisão (DEC-005) assumiu que os 5 datasets de exemplo são todos categóricos (mapas de classe/vegetação/inundação), com base apenas nos nomes dos arquivos e no fato de a maioria já usar `reclassificar()`.

**Por que ainda é só exploração:** essa suposição **não foi confirmada pelo usuário/pelo dono do projeto**. Não houve inspeção real dos valores de pixel de nenhum dos datasets reais (`fathom_dem.py` inclusive, cujo raster de entrada — em centímetros — é conceitualmente contínuo, mesmo que o script não aplique de fato nenhuma transformação sobre ele no estado atual, ver DIV-06).

**Como isso pode ser encerrado:** confirmação direta do usuário sobre o tipo de cada um dos 5 datasets, ou inspeção real dos arquivos (`gdalinfo -stats` ou equivalente) para verificar se os valores são consistentes com códigos de classe (poucos valores inteiros distintos) ou com uma variável contínua (muitos valores, distribuição contínua).

---

## EXP-003 — Reconstrução inicial do projeto a partir do código-fonte

**Data:** 2026-08-30 (antes da criação deste log)

**O que foi feito:** a primeira atividade de todo este processo foi reconstruir objetivo, fluxo de dados, componentes, dependências e riscos do projeto **apenas a partir do código-fonte e da documentação existente**, sem acesso a quem escreveu o código. Isso gerou a primeira versão de `SPEC/scientific.md`, `SPEC/requirements.md` e `CONTEXT.md`.

**Por que está registrado aqui:** essa reconstrução é, por definição, inferência sobre intenção alheia — cada item foi marcado como EXPLÍCITO, IMPLÍCITO, DESCONHECIDO ou QUESTIONÁVEL exatamente para deixar claro o que é fato observável no código e o que é leitura/interpretação. Este log existe, em parte, para que essa distinção não se perca à medida que os documentos de `SPEC/` são atualizados e passam a soar mais "definitivos" do que a reconstrução original de fato era.
