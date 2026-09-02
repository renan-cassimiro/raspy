# Requisitos — raspy

> Requisitos derivados do comportamento observado no código, documentação e exemplos. Cada um indica também evidência, componente responsável e grau de confiança, como informação suplementar ao template. Requisitos marcados como candidatos ainda não têm critério de aceitação fechado — ficam `[EM ABERTO]` até uma decisão ser registrada em `decisions.md`.

---

## REQ-001
**Descrição:** O sistema deve validar, ao abrir um raster de entrada, que o arquivo existe, possui CRS definido e contém pelo menos uma banda.
**Tipo:** computacional
**Critério de aceitação:**
- um caminho de arquivo inexistente deve resultar em erro explícito;
- um raster sem CRS definido deve resultar em `ValueError`;
- um raster com zero bandas deve resultar em `ValueError`;
- um raster válido (CRS definido, ≥1 banda) deve retornar um dicionário com `perfil`, `nodata`, `crs`, `resolucao`, `bandas`, `bounds`.
**Teste relacionado:** TEST-001 (não implementado)
**Status:** implementado e estável; sem divergência conhecida.
*Evidência: `ingest.py::abrir_raster()`. Grau de confiança: alto.*

---

## REQ-002
**Descrição:** O sistema deve recortar um raster a partir da geometria de um GeoPackage, reprojetando a geometria para o CRS do raster quando necessário.
**Tipo:** computacional
**Critério de aceitação:**
- o raster de saída deve corresponder à área definida pela geometria do GeoPackage;
- se `gdf.crs != src.crs`, a geometria deve ser reprojetada antes do recorte;
- `crop=True` deve ajustar o extent da saída à geometria; `crop=False` deve preservar o extent original;
- `all_touched=True` deve incluir pixels de borda; `all_touched=False` deve incluir apenas pixels com centro dentro da geometria;
- se o raster de entrada não tiver `nodata` definido, o sistema deve emitir um aviso explícito informando que a área fora da geometria será preenchida com `0`.
**Teste relacionado:** TEST-002 (não implementado)
**Status:** o último critério (aviso de `nodata=None`) foi implementado em 2026-08-30 (DEC-007, resolve DIV-11). Os demais critérios já eram atendidos.
*Evidência: `clip.py::recortar_por_gpkg()`. Grau de confiança: alto.*

---

## REQ-003
**Descrição:** O sistema deve aplicar um fator de escala a um raster contínuo, dividindo cada valor de pixel válido pelo fator informado, com saída em `float32`, processada em blocos.
**Tipo:** científico e computacional
**Critério de aceitação:**
- para um raster de entrada com valores conhecidos e um fator conhecido, a saída deve corresponder a `entrada / fator`, no tipo `float32`;
- pixels originalmente `nodata` na entrada devem receber `nodata_saida` na saída, e não `nodata_original / fator`.
**Teste relacionado:** TEST-003 (não implementado)
**Status:** implementado; **nunca exercitado de ponta a ponta** em nenhum dos 5 exemplos disponíveis (DIV-14) — decisão de ignorar por ora (DEC-009).
*Evidência: `transform.py::aplicar_fator_escala()`. Grau de confiança: alto para a lógica; nenhuma evidência de execução real.*

---

## REQ-004
**Descrição:** O sistema deve reclassificar um raster categórico segundo um dicionário `{valor_original: novo_valor}`, atribuindo `nodata_saida` a qualquer pixel sem regra de mapeamento e a qualquer pixel originalmente `nodata`.
**Tipo:** científico e computacional
**Critério de aceitação:**
- todo pixel cujo valor original conste no dicionário deve receber o novo valor correspondente;
- todo pixel cujo valor original não conste no dicionário deve receber `nodata_saida`;
- todo pixel originalmente `nodata` na entrada deve receber `nodata_saida` na saída;
- **[QUESTIONÁVEL — não é critério de aceitação fechado]**: se uma classe válida do mapeamento for igual a `nodata_saida` (ex.: `mapeamento={0: 0, ...}` com `nodata_saida=0`, caso real observado em `hess2015_..._reclassified.py`), o sistema atualmente **não distingue** essa classe de nodata/valor-sem-regra no produto final. Não há decisão registrada sobre se isso deve continuar permitido silenciosamente, gerar aviso, ou ser bloqueado.
**Teste relacionado:** TEST-004 (não implementado) — o dataset sintético #1 (classe 0 legítima + nodata=0), já planejado, deve cobrir exatamente o item questionável acima.
**Status:** implementado; ambiguidade conhecida e não resolvida.
*Evidência: `transform.py::reclassificar()`. Grau de confiança: alto para o comportamento; QUESTIONÁVEL quanto à adequação metodológica.*

---

## REQ-005
**Descrição:** O sistema deve converter um GeoTIFF em Cloud Optimized GeoTIFF (COG), com compressão e método de reamostragem de overview configuráveis.
**Tipo:** computacional
**Critério de aceitação:**
- o arquivo de saída deve ser um COG válido segundo `cog.validar_cog()`;
- a compressão e o método de overview efetivamente gravados no arquivo devem corresponder aos parâmetros informados na chamada.
**Teste relacionado:** TEST-005 (não implementado)
**Status:** implementado e estável.
*Evidência: `cog.py::converter_para_cog()`. Grau de confiança: alto.*

---

## REQ-006
**Descrição:** O sistema deve validar se um arquivo é um COG estruturalmente válido, retornando um resultado booleano.
**Tipo:** computacional
**Critério de aceitação:**
- deve retornar `True` para um COG válido conhecido;
- deve retornar `False` para um GeoTIFF comum (não-COG) ou arquivo corrompido.
**Teste relacionado:** TEST-006 (não implementado)
**Status:** implementado; comportamento em casos-limite (arquivo corrompido) não verificado.
*Evidência: `cog.py::validar_cog()`. Grau de confiança: alto para o caso principal; médio para casos-limite.*

---

## REQ-007
**Descrição:** O sistema deve gerar um arquivo YAML de metadados de processamento associado ao produto final, e todo parâmetro nele registrado deve corresponder exatamente ao parâmetro real usado no processamento que gerou o produto.
**Tipo:** computacional
**Critério de aceitação:**
- o YAML deve conter, no mínimo: arquivo de entrada, origem, arquivo de saída, formato, CRS, resolução, número de bandas, bounding box, nodata original, fator de escala (se houver), nodata de saída real, compressão, método de overview real, e checksum MD5 (se solicitado);
- **cada um desses valores deve corresponder ao que foi de fato executado** — em particular, `resampling_overview` registrado deve ser idêntico ao usado em `cog.converter_para_cog()`, e `nodata_saida` registrado deve ser idêntico ao nodata real do arquivo de saída (verificável via `rasterio.open(saida).nodata`).
**Teste relacionado:** TEST-007 (não implementado) — deve incluir verificação cruzada entre o YAML gerado e as propriedades reais do arquivo de saída, não apenas a presença dos campos.
**Status:**
- `resampling_overview` corrigido manualmente nos 5 exemplos existentes em 2026-08-30 (DEC-005, resolve DIV-12 nos exemplos atuais, ainda com duplicação manual).
- `nodata_saida` (DIV-04), `caminho_entrada` (DIV-05) e `resampling_overview` (DIV-12) **resolvidos estruturalmente em 2026-08-31** para quem usa `RasterPipeline` (REQ-009): esses valores agora vêm de uma única fonte (o estado interno do pipeline e o arquivo de saída real), não são mais digitados duas vezes. `metadata.gerar_metadados()` em si não mudou de assinatura — o que mudou é que `pipeline.py` sempre a chama corretamente.
- **Pendência remanescente:** os 5 scripts em `examples/` ainda chamam as funções manualmente (não foram migrados para `RasterPipeline` — DIV-06/07/08, DEC-004). Enquanto isso não acontecer, o risco de divergência manual continua existindo para quem usa os exemplos como referência, mesmo com o pipeline já disponível.
*Evidência: `metadata.py::gerar_metadados()` (inalterado) + `pipeline.py::RasterPipeline._finalizar()`. Grau de confiança: alto — testado de ponta a ponta em 3 cenários (sem transformação, escala, clip+reclassificação).*

---

## REQ-008 — candidato
**Descrição:** O arquivo de metadados deveria registrar a cadeia completa de processamento aplicada ao produto, incluindo geometria/parâmetros de recorte, tabela de reclassificação utilizada e a ordem completa das operações executadas.
**Tipo:** científico
**Critério de aceitação:** `[EM ABERTO]` — depende de decisão sobre até que ponto o YAML deve funcionar como registro de proveniência completo e reexecutável.
**Teste relacionado:** TEST-008 (a definir após decisão de escopo)
**Status:** não implementado; sem decisão registrada em `decisions.md`.

---

## REQ-009
**Descrição:** Deve existir uma API de composição de pipeline (`RasterPipeline`) que permita ao usuário encadear livremente as transformações disponíveis (clip, escala, reclassificação) em qualquer ordem, e que execute automaticamente, ao final (via context manager), a conversão para COG, a validação e a geração de metadados — usando os mesmos parâmetros reais da execução, sem duplicação manual.
**Tipo:** computacional
**Critério de aceitação:**
- `clip()`, `scale()` e `reclassify()` podem ser chamados em qualquer ordem, qualquer quantidade de vezes (inclusive zero vezes);
- ao sair do bloco `with` sem exceção, `cog.converter_para_cog()`, `cog.validar_cog()` e `metadata.gerar_metadados()` são chamados automaticamente, sem intervenção do usuário;
- `resampling_overview` usado na conversão e o registrado nos metadados devem ser sempre idênticos (resolve DIV-12 estruturalmente, não apenas nos exemplos);
- `nodata_saida` registrado nos metadados deve ser lido do arquivo de saída real, não inferido de `fator_escala` (resolve DIV-04 estruturalmente);
- `caminho_entrada` registrado nos metadados deve ser sempre o raster original passado na construção do pipeline (resolve DIV-05 estruturalmente);
- o raster de entrada original nunca deve ser removido pelo pipeline, mesmo com `remover_temp=True` e mesmo que nenhuma transformação seja chamada;
- se uma exceção ocorrer dentro do bloco `with`, a etapa final (COG, validação, metadados) não deve ser executada, e a exceção original deve ser propagada (nunca silenciada).
**Teste relacionado:** TEST-009 (não implementado — os 5 cenários de fumaça descritos no `Status` abaixo devem virar testes automatizados formais)
**Status:** **implementado e validado manualmente em 2026-08-31** com dados sintéticos, cobrindo 5 cenários: (1) nenhuma transformação, (2) apenas `scale()`, (3) `clip()` + `reclassify()` com classe `0` legítima coincidindo com `nodata_saida=0` (caso real de DIV-07), (4) exceção dentro do bloco `with`, (5) `remover_temp=False`. Todos os critérios de aceitação acima foram confirmados nesses testes. Ver `pipeline.py` e DEC-011 para as decisões de design que preencheram o que este requisito deixava `[EM ABERTO]`.
*Evidência: `pipeline.py::RasterPipeline`. Grau de confiança: alto (testado de ponta a ponta); pendente apenas formalizar TEST-009 como teste automatizado.*

---

## REQ-010
**Descrição:** As dependências mínimas necessárias para executar o pipeline atual do `raspy` devem estar claramente delimitadas em `environment.yml`, sem pacotes sem uso identificável no código.
**Tipo:** computacional
**Critério de aceitação:**
- todo pacote listado em `environment.yml` deve ser importado, direta ou transitivamente, por algum módulo do pipeline atual (`ingest.py`, `clip.py`, `transform.py`, `cog.py`, `metadata.py`);
- o arquivo não deve conter caminhos de máquina específicos de um único desenvolvedor (ex.: `prefix:`).
**Teste relacionado:** TEST-010 (não implementado) — verificação de que o pipeline funciona a partir de um ambiente criado só com as dependências declaradas.
**Status:** corrigido em 2026-08-30 (DEC-008, resolve DIV-09) — removidos `pyflwdir`, `requests`, `pyarrow`, `python-duckdb` e a linha `prefix:`.

---

## REQ-011
**Descrição:** O sistema deve avisar explicitamente o usuário quando uma operação de recorte for realizada sobre um raster sem `nodata` definido, dado que a área fora da geometria será preenchida com `0` por padrão pelo `rasterio.mask.mask()`.
**Tipo:** computacional
**Critério de aceitação:**
- ao chamar `clip.recortar_por_gpkg()` com um raster cujo `nodata` seja `None`, uma mensagem de aviso deve ser exibida antes da execução do recorte.
**Teste relacionado:** TEST-011 (não implementado) — dataset sintético #2 (raster sem nodata definido) cobre este requisito.
**Status:** implementado em 2026-08-30 (DEC-007, resolve DIV-11).
*Evidência: `clip.py::recortar_por_gpkg()`. Grau de confiança: alto.*
