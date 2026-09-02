# pipeline.py
# API de composição de pipeline (REQ-009 / DEC-001, SPEC/decisions.md).
#
# RasterPipeline permite ao usuário encadear livremente as transformações
# disponíveis (clip, escala, reclassificação), em qualquer ordem, e
# automatiza a etapa final do pipeline (conversão para COG, validação e
# geração de metadados) ao sair do bloco `with`.
#
# Este módulo NÃO reimplementa nenhuma transformação: cada método apenas
# chama a função equivalente já existente em clip.py / transform.py /
# cog.py / metadata.py, na mesma ordem em que o usuário as invoca.
#
# O que muda em relação a chamar essas funções manualmente:
#   - o usuário não precisa chamar cog.converter_para_cog(),
#     cog.validar_cog() nem metadata.gerar_metadados() explicitamente;
#   - os parâmetros registrados nos metadados (nodata_saida real,
#     resampling_overview real, caminho_entrada original) vêm de uma
#     única fonte de verdade — a própria execução do pipeline — em vez
#     de serem redigitados manualmente em cada script (isso é o que
#     corrige, na raiz, DIV-04, DIV-05 e DIV-12; ver divergence-matrix.md).
#
# O que NÃO muda / o que este módulo deliberadamente não faz:
#   - não impõe nem valida a ordem cientificamente correta das
#     transformações (SPEC/scientific.md, item 6 — permanece QUESTIONÁVEL,
#     é responsabilidade do usuário);
#   - não registra a geometria de recorte nem a tabela de reclassificação
#     completa nos metadados (REQ-008 permanece [EM ABERTO] — não decidido);
#   - nunca remove o raster de entrada original, mesmo com remover_temp=True
#     (apenas os arquivos intermediários que o próprio pipeline cria).

import os
import uuid
from pathlib import Path

import rasterio

from . import ingest, clip as clip_mod, transform, cog, metadata


class RasterPipeline:
    """
    Compõe um pipeline de preparação de raster com finalização automática.

    Uso
    ---
    with RasterPipeline("entrada.tif", "saida_cog.tif") as p:
        p.clip("area.gpkg")
        p.reclassify({1: 0, 2: 1, 3: 1}, nodata_saida=0, dtype="uint8")
    # ao sair do bloco (sem exceção):
    #   1. converte o último resultado para COG
    #   2. valida o COG gerado
    #   3. gera o YAML de metadados, com nodata_saida e
    #      resampling_overview lidos da execução real — não redigitados

    As transformações (`clip`, `scale`, `reclassify`) podem ser chamadas
    em qualquer ordem, qualquer quantidade de vezes, ou nenhuma vez
    (nesse caso o raster bruto é convertido para COG diretamente).

    Se uma exceção for levantada dentro do bloco `with`, a etapa final
    (COG, validação, metadados) NÃO é executada, e os arquivos
    intermediários já gerados permanecem em disco para inspeção.

    Parâmetros
    ----------
    caminho_entrada : str
        Raster de entrada (bruto). Nunca é modificado nem removido.
    caminho_saida : str
        Caminho do COG final.
    diretorio_temp : str, opcional
        Diretório onde os arquivos intermediários são escritos.
        Padrão: mesmo diretório de `caminho_saida`.
    compressao : str
        Compressão usada na conversão para COG ('deflate', 'lzw', 'zstd').
    resampling_overview : str, opcional
        Método de reamostragem dos overviews. Se não informado, é
        escolhido automaticamente a partir da última transformação
        aplicada: 'average' após `scale()` (dado contínuo), 'nearest'
        após `reclassify()` (dado categórico), e 'nearest' se nenhuma
        transformação numérica for aplicada. Informar explicitamente
        aqui sempre tem prioridade sobre essa inferência.
    remover_temp : bool
        Se True (padrão), remove ao final os arquivos intermediários
        criados pelo próprio pipeline (nunca o `caminho_entrada`).
    origem : str, opcional
        Descrição da fonte do dado, repassada a metadata.gerar_metadados().
    calcular_checksum : bool
        Se True, calcula o checksum MD5 do COG final.
    """

    def __init__(
        self,
        caminho_entrada: str,
        caminho_saida: str,
        diretorio_temp: str = None,
        compressao: str = "deflate",
        resampling_overview: str = None,
        remover_temp: bool = True,
        origem: str = None,
        calcular_checksum: bool = True,
    ):
        self.caminho_entrada = caminho_entrada
        self.caminho_saida = caminho_saida
        self.diretorio_temp = Path(diretorio_temp) if diretorio_temp else Path(caminho_saida).resolve().parent
        self.compressao = compressao
        self.remover_temp = remover_temp
        self.origem = origem
        self.calcular_checksum = calcular_checksum

        self._resampling_overview_explicito = resampling_overview
        self._resampling_overview_inferido = None  # atualizado por scale()/reclassify()

        self._caminho_atual = caminho_entrada
        self._arquivos_intermediarios = []  # nunca inclui caminho_entrada
        self._etapas = []  # histórico interno; usado só para depuração, não é exposto integralmente nos metadados (REQ-008 em aberto)

        self._fator_escala_aplicado = None
        self._info_raster_original = None

        # Resultados da etapa final, preenchidos por _finalizar() e
        # disponíveis para o usuário após o bloco `with` (None até lá).
        self.cog_valido = None
        self.metadata_path = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self):
        self._info_raster_original = ingest.abrir_raster(self.caminho_entrada)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Algo deu errado dentro do bloco `with`: não finaliza o
            # pipeline. Os intermediários já gerados ficam em disco.
            return False

        self._finalizar()

        if self.remover_temp:
            self._limpar_intermediarios()

        return False

    # ------------------------------------------------------------------
    # Transformações — cada uma delega para a função já existente
    # ------------------------------------------------------------------

    def clip(self, caminho_gpkg: str, layer: str = None, crop: bool = True, all_touched: bool = False) -> "RasterPipeline":
        """Recorta o resultado atual pela geometria de um GeoPackage (ver clip.recortar_por_gpkg)."""
        destino = self._novo_temp("clip")
        clip_mod.recortar_por_gpkg(
            caminho_raster=self._caminho_atual,
            caminho_gpkg=caminho_gpkg,
            caminho_saida=destino,
            layer=layer,
            crop=crop,
            all_touched=all_touched,
        )
        self._registrar_etapa("clip", caminho_gpkg=caminho_gpkg, layer=layer, crop=crop, all_touched=all_touched)
        self._caminho_atual = destino
        return self

    def scale(self, fator: float, nodata_saida: float = -9999.0) -> "RasterPipeline":
        """Aplica fator de escala ao resultado atual (ver transform.aplicar_fator_escala)."""
        destino = self._novo_temp("scale")
        transform.aplicar_fator_escala(
            caminho_entrada=self._caminho_atual,
            caminho_saida=destino,
            fator=fator,
            nodata_saida=nodata_saida,
        )
        self._registrar_etapa("scale", fator=fator, nodata_saida=nodata_saida)
        self._caminho_atual = destino
        self._fator_escala_aplicado = fator
        self._resampling_overview_inferido = "average"
        return self

    def reclassify(self, mapeamento: dict, nodata_saida: int = 0, dtype: str = "uint8") -> "RasterPipeline":
        """Reclassifica o resultado atual segundo um mapeamento (ver transform.reclassificar)."""
        destino = self._novo_temp("reclassify")
        transform.reclassificar(
            caminho_entrada=self._caminho_atual,
            caminho_saida=destino,
            mapeamento=mapeamento,
            nodata_saida=nodata_saida,
            dtype=dtype,
        )
        self._registrar_etapa("reclassify", mapeamento=mapeamento, nodata_saida=nodata_saida, dtype=dtype)
        self._caminho_atual = destino
        self._resampling_overview_inferido = "nearest"
        return self

    # ------------------------------------------------------------------
    # Finalização automática
    # ------------------------------------------------------------------

    def _finalizar(self) -> None:
        resampling_overview = (
            self._resampling_overview_explicito
            or self._resampling_overview_inferido
            or "nearest"
        )

        # Conversão para COG. remover_temp=False aqui sempre — a limpeza
        # de intermediários é responsabilidade deste pipeline
        # (_limpar_intermediarios), nunca da função de baixo nível, para
        # nunca correr o risco de remover caminho_entrada por engano.
        cog.converter_para_cog(
            caminho_entrada=self._caminho_atual,
            caminho_saida=self.caminho_saida,
            compressao=self.compressao,
            resampling_overview=resampling_overview,
            remover_temp=False,
        )

        self.cog_valido = cog.validar_cog(self.caminho_saida)

        # nodata real gravado no arquivo de saída — não inferido de
        # fator_escala (corrige DIV-04 na origem).
        with rasterio.open(self.caminho_saida) as saida_ds:
            nodata_saida_real = saida_ds.nodata

        self.metadata_path = metadata.gerar_metadados(
            caminho_entrada=self.caminho_entrada,  # sempre o raster bruto original (corrige DIV-05)
            caminho_saida=self.caminho_saida,
            info_raster=self._info_raster_original,
            fator_escala=self._fator_escala_aplicado,
            nodata_saida=nodata_saida_real,
            compressao=self.compressao,
            resampling_overview=resampling_overview,  # idêntico ao usado na conversão acima (corrige DIV-12)
            origem=self.origem,
            calcular_checksum=self.calcular_checksum,
        )

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _novo_temp(self, prefixo: str) -> str:
        nome = f".raspy_tmp_{prefixo}_{uuid.uuid4().hex[:8]}.tif"
        caminho = str(self.diretorio_temp / nome)
        self._arquivos_intermediarios.append(caminho)
        return caminho

    def _registrar_etapa(self, tipo: str, **parametros) -> None:
        self._etapas.append({"tipo": tipo, "parametros": parametros})

    def _limpar_intermediarios(self) -> None:
        # self._caminho_atual, no momento da limpeza, é o último
        # intermediário usado como entrada da conversão para COG — ele
        # também deve ser removido se remover_temp=True. Nunca inclui
        # caminho_entrada, que não passa por _novo_temp().
        for caminho in self._arquivos_intermediarios:
            if os.path.exists(caminho):
                os.remove(caminho)
