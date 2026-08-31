# Especificação Científica — raspy (Raster Preparation System)

> Reconstrução provisória a partir de código, documentação e exemplos. Não assume que o comportamento atual esteja correto. Itens não decididos estão marcados `[EM ABERTO]`.

## 1. Objetivo científico

- **EXPLÍCITO**: reduzir problemas de projetos GIS exploratórios (duplicação de arquivos, inconsistência de projeções, pipelines pouco reproduzíveis) por meio de preparação, padronização e conversão de rasters ambientais para COG, com validação e metadados de processamento.
- **IMPLÍCITO**: funcionar como camada intermediária de preparação de dados raster ambientais, genérica o suficiente para atender múltiplos datasets além do exemplo FathomDEM.
- `[EM ABERTO]`: se o objetivo científico do projeto é apenas viabilizar armazenamento/acesso eficiente (formato COG), ou também garantir corretude/comparabilidade científica dos valores transformados entre datasets.

## 2. Perguntas de pesquisa

- `DESCONHECIDO`: não há, no material disponível, perguntas de pesquisa formuladas explicitamente. O projeto se apresenta como ferramenta de infraestrutura de dados, não como estudo com hipóteses próprias.
- `[EM ABERTO]`

## 3. Modelo conceitual

- **EXPLÍCITO** (fluxo documentado originalmente): `Raster bruto → ingest → transform → cog → metadata → COG final + YAML`.
- **IMPLÍCITO** (fluxo reconstruído do código atual): `ingest → clip (recorte por GeoPackage) → transform (escala e/ou reclassificação) → cog (conversão) → {validar_cog, gerar_metadados}`.
- **QUESTIONÁVEL**: o modelo conceitual documentado e o modelo conceitual implementado divergem (ausência de `clip` e de `reclassificar()` na documentação original), o que compromete a confiabilidade da documentação como fonte de verdade do fluxo atual.

## 4. Dados de entrada

- **EXPLÍCITO**: raster de entrada (formato mencionado: GeoTIFF), aberto via `rasterio`; deve possuir CRS e pelo menos uma banda.
- **EXPLÍCITO**: GeoPackage, usado como fonte de geometria para recorte (`caminho_gpkg`, `layer`, `crop`, `all_touched`).
- **IMPLÍCITO**: as transformações em `transform.py` parecem desenhadas para rasters de banda única (leitura/escrita explícita da banda 1), mesmo que a ingestão aceite rasters multibanda.
- `DESCONHECIDO`: requisitos de resolução espacial, extensão geográfica, sistema de referência específico exigido, ou faixa de valores válidos de entrada.

## 5. Variáveis

- **EXPLÍCITO**: variável contínua tratada por `aplicar_fator_escala()` (ex.: elevação, com exemplo de conversão cm → m no caso FathomDEM).
- **EXPLÍCITO**: variável categórica tratada por `reclassificar()`, via dicionário `valor_original: novo_valor`.
- `DESCONHECIDO`: unidades de entrada/saída não são validadas ou verificadas automaticamente pelo sistema — a conversão de unidade (ex.: cm → m) depende do fator informado externamente pelo usuário, sem checagem de consistência.
- `[EM ABERTO]`: se o sistema deveria validar unidades declaradas versus fator aplicado.

## 6. Pressupostos

- **IMPLÍCITO**: rasters podem ser grandes demais para caber inteiramente em memória — daí o processamento por blocos (`block_windows`).
- **IMPLÍCITO**: as operações numéricas assumem raster de banda única.
- **IMPLÍCITO**: dados contínuos e dados categóricos exigem métodos de overview diferentes (`average` vs. `nearest`), reconhecendo uma distinção metodológica entre magnitude numérica e classe.
- **QUESTIONÁVEL**: pressupõe-se que a ordem de aplicação das operações (recorte, escala, reclassificação, COG) não afeta a validade científica do resultado, quando na prática ordens diferentes (`A → B` vs. `B → A`) podem produzir resultados cientificamente distintos, e essa ordem não é imposta pela biblioteca.

## 7. Método

- **EXPLÍCITO**: pipeline sequencial de etapas independentes (ingest, clip, transform, cog, metadata), cada uma implementada como função/módulo isolado.
- **IMPLÍCITO**: a composição do método (quais etapas, em qual ordem, com quais parâmetros) é definida no script de orquestração (`examples/fathomdem.py`), não na biblioteca em si.
- **QUESTIONÁVEL**: por não haver uma estrutura de pipeline formalizada (ex.: uma classe `Pipeline` com ordem declarada e validada), o método efetivamente executado em cada caso de uso não é garantidamente reprodutível apenas a partir da biblioteca — depende do script externo.

## 8. Transformações

- **EXPLÍCITO — Espacial**: recorte por geometria de GeoPackage, com reprojeção da geometria para o CRS do raster quando necessário; parâmetros `crop` e `all_touched` controlam o comportamento espacial.
- **EXPLÍCITO — Numérica contínua**: `valor / fator`, saída convertida para `float32`, processada bloco a bloco.
- **EXPLÍCITO — Categórica**: `reclassificar()` aplica um dicionário de mapeamento `valor_original → novo_valor`, com valor padrão (`nodata_saida`) para valores não mapeados.
- **EXPLÍCITO — Estrutural**: conversão de GeoTIFF para COG via `rio-cogeo`, com compressão (`deflate`, `lzw`, `zstd`) e método de overview (`average`, `nearest`, `bilinear`) configuráveis.
- **QUESTIONÁVEL**: em `reclassificar()`, o array de saída é inicializado com `nodata_saida`, de modo que "valor sem regra de mapeamento" e "nodata original" podem se tornar indistinguíveis se `nodata_saida` coincidir com um valor de classe válido (ex.: `0`).

## 9. Controle de qualidade

- **EXPLÍCITO**: `ingest.py` valida existência do arquivo, presença de CRS e de pelo menos uma banda antes do processamento.
- **EXPLÍCITO**: `cog.validar_cog()` retorna `True`/`False` indicando se o arquivo final é um COG válido.
- `DESCONHECIDO`: não há, no material disponível, evidência de controle de qualidade sobre os *valores* resultantes das transformações (ex.: checagem de faixa de valores plausível, comparação estatística antes/depois, detecção de outliers introduzidos pela reclassificação ou escala).
- `[EM ABERTO]`

## 10. Tratamento de dados ausentes

- **EXPLÍCITO**: existe um parâmetro `nodata_saida` tanto na escala quanto na reclassificação, usado para definir o valor de "sem dado" na saída.
- **QUESTIONÁVEL**: ver item 8 — a mesma constante `nodata_saida` é usada tanto para "nodata original propagado" quanto para "valor sem regra de reclassificação", fundindo dois conceitos potencialmente distintos.
- `DESCONHECIDO`: não há evidência de tratamento explícito de nodata na etapa de recorte (`clip.py`) além do comportamento padrão de mascaramento.

## 11. Incerteza

- `DESCONHECIDO`: não há, no material disponível, qualquer tratamento, propagação ou quantificação de incerteza associada aos dados de entrada ou às transformações aplicadas.
- `[EM ABERTO]`

## 12. Saídas esperadas

- **EXPLÍCITO**: GeoTIFF intermediário (produto de recorte e/ou transformação numérica), não necessariamente em formato COG.
- **EXPLÍCITO**: COG final, produto de `cog.converter_para_cog()`.
- **EXPLÍCITO**: arquivo YAML de metadados, contendo informações de entrada/saída, CRS, resolução, número de bandas, bounding box, nodata, parâmetros de processamento e, opcionalmente, checksum MD5.
- **QUESTIONÁVEL**: o YAML de metadados parece registrar apenas parte da cadeia de processamento (parâmetros de escala e de COG), sem estrutura evidente para geometria/parâmetros de recorte, tabela de reclassificação completa ou ordem das operações — o que limita sua função como registro completo e reexecutável do pipeline.

## 13. Limitações científicas

- **QUESTIONÁVEL**: ausência de imposição de ordem entre operações compromete a garantia de reprodutibilidade científica entre execuções diferentes do mesmo tipo de dado.
- **QUESTIONÁVEL**: ausência de validação de unidades/consistência física entre o fator de escala aplicado e a variável real.
- **QUESTIONÁVEL**: sobreposição semântica entre nodata original e valor padrão de reclassificação.
- `DESCONHECIDO`: alcance de validade do sistema para rasters multibanda, dado que as transformações numéricas parecem operar apenas sobre a banda 1.
- `[EM ABERTO]`: limites de escala/volume de dados (tamanho máximo de raster, desempenho esperado) não são declarados nem verificáveis no material disponível.