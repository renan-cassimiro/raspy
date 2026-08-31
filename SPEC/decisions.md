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