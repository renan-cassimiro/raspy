# Registro de Decisões — raspy

> Histórico de decisões metodológicas e de engenharia. Cada decisão referencia, quando aplicável, o item da matriz de divergências (`divergence-matrix.md`) que a motivou.

---

## DEC-001
**Decisão:** Adotar um objeto `RasterPipeline` combinado com context manager (`with ... as p:`) como forma de permitir que o usuário componha livremente as transformações (clip, escala, reclassificação, em qualquer ordem), mas automatizar a etapa final do pipeline (conversão para COG, validação e geração de metadados), que deixa de ser uma chamada explícita e passa a ser garantida no `__exit__`.
**Contexto:** o usuário levantou a dúvida sobre como fazer com que `converter_para_cog()`, `validar_cog()` e `gerar_metadados()` não precisassem ser chamadas manualmente em cada script, mantendo a composição das transformações livre.
**Alternativas consideradas:**
- Decorator (`@finalizar_pipeline`) envolvendo uma função de pipeline.
- Sistema de eventos/hooks (`pipeline_finished`).
- `__del__` / `atexit` para disparo automático no encerramento do processo.
**Justificativa:** o context manager é idiomático em Python, garante execução mesmo se o usuário esquecer de chamar a etapa final, e não depende de ordem de destruição de objetos (ao contrário de `__del__`/`atexit`, que são frágeis e podem silenciar erros). Também cria naturalmente um ponto único de verdade para os parâmetros passados a `cog.converter_para_cog()` e a `metadata.gerar_metadados()` — o que ataca diretamente a causa raiz de DIV-04, DIV-05 e DIV-12 (parâmetros duplicados manualmente em dois lugares e divergentes entre si).
**Data:** 2026-08-30
**Reversível:** sim — é uma camada nova sobre as funções existentes; nenhuma função atual precisa deixar de existir ou mudar de assinatura.

---

## DEC-002
**Decisão:** Corrigir imediatamente as divergências de documentação (DIV-01, DIV-02, DIV-03) diretamente no `readme.md`, sem esperar pela `RasterPipeline`.
**Contexto:** o roadmap do README ainda listava recorte territorial como funcionalidade futura (já implementada), o exemplo de uso não mencionava `clip`/`reclassificar`, e a tabela de dependências não listava `geopandas`.
**Alternativas consideradas:** esperar a implementação da `RasterPipeline` para reescrever a documentação de uma vez só.
**Justificativa:** são correções de baixo risco e alto impacto imediato para qualquer pessoa nova lendo o projeto hoje; não há razão para que fiquem incorretas enquanto o pipeline builder não existe.
**Data:** 2026-08-30
**Reversível:** sim.

---

## DEC-003
**Decisão:** Adiar a correção estrutural de DIV-04 (nodata_saida incorreto no YAML) e DIV-05 (`caminho_entrada` inconsistente entre a chamada de COG e a de metadados) para quando a `RasterPipeline` (DEC-001) existir, em vez de aplicar remendos pontuais em `metadata.py` agora.
**Contexto:** ambos os bugs têm a mesma causa raiz — os parâmetros usados na conversão real e os parâmetros registrados nos metadados são digitados duas vezes, manualmente, em lugares diferentes do código.
**Alternativas consideradas:** corrigir a lógica de `metadata.gerar_metadados()` agora (ex.: passar explicitamente o nodata real do arquivo de saída, em vez de inferi-lo de `fator_escala`).
**Justificativa:** uma correção pontual em `metadata.py` resolveria o sintoma atual, mas não impede que o mesmo tipo de divergência reapareça em cada novo script de exemplo. A causa raiz é estrutural (duplicação manual de estado) e será eliminada quando os parâmetros passarem a vir de uma única fonte (o objeto de pipeline).
**Data:** 2026-08-30
**Reversível:** sim — nada impede uma correção pontual futura se a `RasterPipeline` atrasar.

---

## DEC-004
**Decisão:** Reescrever os 5 scripts de exemplo usando a `RasterPipeline`, em vez de corrigir individualmente as inconsistências estruturais entre eles (DIV-06, DIV-07, DIV-08).
**Contexto:** os exemplos duplicam lógica, têm etapas comentadas/descomentadas manualmente, e não há garantia de que o que é registrado como executado corresponda ao que de fato rodou.
**Alternativas consideradas:** corrigir cada script individualmente agora (remover blocos comentados, uniformizar caminhos).
**Justificativa:** os scripts são o principal sintoma de não existir uma abstração de pipeline — corrigi-los manualmente resolveria a superfície, mas o próximo dataset novo provavelmente reintroduziria o mesmo padrão de duplicação. Faz mais sentido investir o esforço na abstração e migrar os exemplos por ela.
**Data:** 2026-08-30
**Reversível:** sim.

---

## DEC-005
**Decisão:** Corrigir imediatamente, dentro dos scripts de exemplo atuais (ainda não migrados para a `RasterPipeline`), o valor de `resampling_overview` passado para `metadata.gerar_metadados()`, alinhando-o ao valor real usado em `cog.converter_para_cog()` (`"nearest"` em todos os 5 casos).
**Contexto:** DIV-12 — em todos os exemplos, o valor de conversão real e o valor registrado nos metadados divergiam sistematicamente (`nearest` vs. `average`).
**Alternativas consideradas:** deixar a correção para a migração à `RasterPipeline` (mesmo tratamento de DEC-004).
**Justificativa:** diferente de DIV-04/05, aqui a correção é uma simples sincronização de um valor literal já existente no próprio script — não exige mudança de arquitetura, e o custo de deixá-la incorreta até a migração (que ainda não tem prazo) era desnecessário.
**Pressuposto assumido:** os datasets dos 5 exemplos são categóricos (mapas de classe/vegetação/inundação), portanto `"nearest"` é o valor cientificamente correto — e é o valor de `metadata` que estava errado, não o de `cog.converter_para_cog()`. Este pressuposto não foi confirmado pelo usuário e deve ser revisto se algum desses datasets for, na verdade, contínuo.
**Data:** 2026-08-30
**Reversível:** sim.

---

## DEC-006
**Decisão:** Documentar explicitamente, via comentário no código, a decisão de manter `remover_temp=False` em todos os exemplos (DIV-13), em vez de mudar o comportamento para `True`.
**Contexto:** o valor estava hardcoded em todos os scripts sem explicação, apesar do comentário ao lado sugerir a intenção oposta ("remove o arquivo temporário ao final").
**Alternativas consideradas:** mudar o comportamento para `remover_temp=True` (valor padrão já definido em `cog.py`).
**Justificativa:** não há evidência de que manter os arquivos intermediários seja um erro — é plausivelmente proposital para fins de depuração durante o desenvolvimento dos pipelines. Corrigir a *documentação* da decisão (torná-la explícita) resolve a divergência classificada como "decisão não documentada" sem alterar comportamento que pode ser deliberado.
**Data:** 2026-08-30
**Reversível:** sim.

---

## DEC-007
**Decisão:** Tratar explicitamente, em `clip.py`, o caso em que o raster de entrada não possui `nodata` definido (`src.nodata is None`), emitindo um aviso em vez de depender do comportamento padrão implícito do `rasterio.mask.mask()` (preenchimento com `0`).
**Contexto:** DIV-11 — nada no código ou na documentação alertava sobre esse comportamento, que pode colidir com valores de dado válidos.
**Alternativas consideradas:**
- Levantar uma exceção, exigindo que o usuário defina um nodata antes do recorte.
- Definir um nodata padrão internamente quando `None` for detectado.
**Justificativa:** optou-se pelo aviso (não bloqueante) em vez de exceção, para não quebrar pipelines existentes que já dependem, mesmo que sem saber, desse comportamento. A validação mais rígida (ex.: exigir nodata) fica em aberto para quando os datasets sintéticos confirmarem se isso é, na prática, um problema recorrente.
**Data:** 2026-08-30
**Reversível:** sim.

---

## DEC-008
**Decisão:** Limpar `environment.yml`, removendo `pyflwdir`, `requests`, `pyarrow` e `python-duckdb` (sem uso identificável no código-fonte atual), e removendo a linha `prefix:` com caminho de máquina pessoal.
**Contexto:** DIV-09 — o ambiente de desenvolvimento era mais amplo que as dependências reais do projeto.
**Alternativas consideradas:** manter as dependências extras documentando que pertencem a um ambiente de desenvolvimento mais amplo (`PulsAmazonia`), não ao núcleo do `raspy`.
**Justificativa:** como o `raspy` está sendo tratado como projeto com identidade própria (inclusive com `SPEC/` dedicada), faz mais sentido que seu `environment.yml` reflita só o que ele de fato usa. Se as dependências extras forem necessárias para outro projeto, devem viver no `environment.yml` desse outro projeto.
**Data:** 2026-08-30
**Reversível:** sim.

---

## DEC-009
**Decisão:** Ignorar deliberadamente, por ora, DIV-14 (a função `aplicar_fator_escala()` nunca é de fato executada em nenhum dos 5 exemplos disponíveis).
**Contexto:** é a funcionalidade motivadora original do projeto (conversão cm → m do FathomDEM), mas está sempre comentada nos scripts reais.
**Alternativas consideradas:** reativar a chamada em pelo menos um exemplo agora, para validar que a função ainda funciona.
**Justificativa:** decisão do usuário — não há, no momento, um caso de uso ativo que dependa dela, e forçar sua execução artificialmente não traria valor imediato. Fica registrada como item conhecido e não testado; o dataset sintético #4 (nodata original ≠ nodata_saida) deve, eventualmente, exercitar essa função quando for retomada.
**Data:** 2026-08-30
**Reversível:** sim — a função continua existindo e implementada; a decisão é apenas de não priorizá-la agora.

---

## DEC-010
**Decisão:** Priorizar a construção de um pequeno catálogo de datasets sintéticos (DIV-10) antes de investir na construção de uma suíte de testes formal (`tests/unit`, `tests/pipeline`).
**Contexto:** não existe nenhum teste no projeto até o momento.
**Alternativas consideradas:** escrever testes unitários diretamente contra dados reais/de produção já usados nos exemplos.
**Justificativa:** dados sintéticos pequenos e controlados permitem construir casos-limite que datasets reais não cobrem de forma confiável (ex.: classe 0 coincidindo com nodata, ausência de nodata, multibanda) — exatamente os cenários que a matriz de divergências identificou como mais perigosos.
**Data:** 2026-08-30
**Reversível:** sim.

---

## DEC-011
**Decisão:** Implementar `RasterPipeline` (REQ-009) preenchendo os pontos que o requisito deixava `[EM ABERTO]` da seguinte forma:
- `caminho_saida` é obrigatório já na construção do objeto (`RasterPipeline(entrada, saida, ...)`), não em um método separado, porque a etapa final sempre roda automaticamente e precisa saber onde gravar o COG desde o início.
- `clip()`, `scale()` e `reclassify()` podem ser chamados em qualquer ordem, qualquer número de vezes (inclusive zero). Cada chamada grava um arquivo intermediário próprio (prefixo `.raspy_tmp_`) no mesmo diretório de `caminho_saida`.
- `resampling_overview`, se não informado explicitamente, é inferido automaticamente a partir da última transformação numérica aplicada: `"average"` depois de `scale()`, `"nearest"` depois de `reclassify()`, e `"nearest"` se nenhuma transformação numérica ocorrer — refletindo a distinção contínuo/categórico já reconhecida em `SPEC/scientific.md`, item 8.4. Informar o parâmetro explicitamente sempre tem prioridade sobre essa inferência.
- O raster de entrada original nunca é removido pelo pipeline, mesmo com `remover_temp=True` — apenas os arquivos intermediários criados pelo próprio pipeline entram na lista de limpeza. Isso evita que um pipeline sem nenhuma transformação (`with RasterPipeline(...) as p: pass`) apague o dado bruto do usuário.
- Se uma exceção ocorrer dentro do bloco `with`, a etapa final não é executada, a exceção é sempre propagada (nunca silenciada), e os arquivos intermediários já gerados **permanecem em disco** (não são limpos mesmo com `remover_temp=True`), para permitir inspeção do que foi produzido até a falha.
- `RasterPipeline` não registra a geometria de recorte nem a tabela de reclassificação completa nos metadados — isso continua sendo o escopo do REQ-008, ainda `[EM ABERTO]` e não decidido nesta rodada.
**Contexto:** REQ-009 e DEC-001 aprovaram o desenho geral (objeto + context manager), mas deixaram explicitamente em aberto a assinatura exata da API, o tratamento de erros dentro do `with`, e o formato de saída.
**Alternativas consideradas:**
- Exigir que o usuário sempre informe `resampling_overview` explicitamente, sem inferência automática — descartada por reintroduzir o mesmo tipo de esquecimento manual que causou DIV-12.
- Limpar os arquivos intermediários mesmo em caso de erro — descartada porque dificultaria depurar exatamente qual etapa falhou e com qual resultado intermediário.
**Justificativa:** cada decisão acima foi escolhida por eliminar uma classe inteira de erro humano observada na matriz de divergências (DIV-04, DIV-05, DIV-12), sem exigir que o usuário lembre de fazer algo a mais manualmente — a única exceção é REQ-008, que foi deliberadamente deixado de fora por não ter escopo definido ainda.
**Validação:** testado manualmente em 2026-08-31 com dados sintéticos (raster categórico 20×20 com classe `0` legítima + nodata, e um GeoPackage de recorte), cobrindo os 5 cenários descritos no `Status` de REQ-009. Todos os comportamentos acima foram confirmados na prática, não apenas no código.
**Data:** 2026-08-31
**Reversível:** parcialmente — a assinatura pública (`RasterPipeline(entrada, saida, ...)`, `.clip()`, `.scale()`, `.reclassify()`) tende a ser usada em novo código assim que existir; mudar depois exigiria depreciar, não apenas ajustar.

---

## DEC-012
**Decisão:** Migrar os 5 scripts de `examples/` para `RasterPipeline`, e corrigir um bug real encontrado no processo: `RasterPipeline` não expunha `cog_valido` nem `metadata_path` publicamente (a validação e o caminho do YAML eram calculados em `_finalizar()` mas descartados, não guardados em `self`).
**Contexto:** o usuário apontou que o empacotamento anterior entregou a `RasterPipeline` e a suíte de testes, mas deixou `examples/` como estava — cada script ainda chamando `ingest`/`clip`/`transform`/`cog`/`metadata` manualmente, exatamente a duplicação que DIV-06/07/08 descreviam. Isso não tinha sido pedido explicitamente na rodada anterior e foi deliberadamente adiado (ver `CHANGELOG.md`), mas ficou como pendência visível.
**Como o bug foi encontrado:** ao escrever os exemplos migrados, cada um terminava com `print(p.cog_valido)` e `print(p.metadata_path)` — isso quebrou com `AttributeError` no primeiro teste manual com dado sintético, porque esses atributos nunca tinham sido testados isoladamente antes (a validação anterior, EXP-001, só checava o COG e o YAML diretamente no disco, nunca o retorno do objeto `RasterPipeline` em si).
**Alternativas consideradas:**
- Não expor esses atributos e fazer os exemplos lerem o YAML do disco para confirmar sucesso — descartada por reintroduzir acoplamento com o formato do YAML dentro dos exemplos, exatamente o tipo de duplicação que `RasterPipeline` deveria eliminar.
**Justificativa:** um objeto que executa uma ação (validar um COG, gerar um arquivo de metadados) e descarta o resultado força quem usa a API a repetir o trabalho manualmente para saber se deu certo — o mesmo problema estrutural que motivou toda a `RasterPipeline` em primeiro lugar, só que um nível abaixo.
**Efeito colateral registrado:** ao migrar, também corrigido um bug de copiar-e-colar não catalogado antes (cabeçalho/`origem` de todos os 5 exemplos citando "FathomDEM", quando nenhum dos datasets é FathomDEM) — ver `CHANGELOG.md` para o detalhe completo por arquivo. O dicionário `RECLASSIFICACAO`, presente mas nunca usado em um dos exemplos, foi mantido comentado (não ativado), porque ativá-lo mudaria o produto científico gerado — essa é uma decisão do dono do projeto, não uma correção de bug.
**Validação:** suíte de testes completa (13 testes) re-executada após a correção, mais um teste de fumaça manual reproduzindo a estrutura exata dos exemplos migrados (clip + reclassify com dado sintético), mais um novo teste automatizado (`assert p.cog_valido is True` / `assert p.metadata_path == ...`) adicionado a `tests/pipeline/test_raster_pipeline.py` para travar essa regressão especificamente.
**Data:** 2026-09-01
**Reversível:** sim — adicionar atributos públicos não quebra nenhum uso existente de `RasterPipeline` (é estritamente aditivo).
