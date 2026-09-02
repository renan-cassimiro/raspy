# data/

Diretório reservado para os dados brutos e intermediários usados pelos pipelines reais (FathomDEM, HESS 2015, Souza 2025, Xingu River — ver `examples/`).

Nenhum dado real foi incluído neste empacotamento. Os testes automatizados (`tests/`) não dependem desta pasta — eles geram seus próprios dados sintéticos em `tests/synthetic_data/`.

Se este projeto for versionado em Git, os arquivos de dado (raster, GeoPackage) desta pasta normalmente **não** devem ser commitados — apenas esta nota e, se necessário, um `.gitignore` específico.
