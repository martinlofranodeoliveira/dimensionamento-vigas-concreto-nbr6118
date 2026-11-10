from __future__ import annotations

"""Pacote de dimensionamento e verificação de vigas de concreto armado segundo a ABNT NBR 6118:2023.

Desenvolvido por LOFRANO TECNOLOGIA.
Aritmética 100% exata (Zero Float) com Frações e inteiros.
"""

__version__ = "1.0.0"
__author__ = "Martin Lofrano de Oliveira / LOFRANO TECNOLOGIA"
__license__ = "MIT"

from vigas_concreto_nbr6118.constants import (
    GAMMA_C,
    GAMMA_S,
    GAMMA_F,
    ALPHA_C,
    LAMBDA_C,
    XI_LIMITE_DUCTILIDADE,
    ES_KN_CM2,
    TABELA_CAA_NBR6118,
    TABELA_CONCRETOS_NBR6118,
    TABELA_ACOS_NBR6118,
    TABELA_BITOLAS_COMERCIAIS,
    RHO_MAXIMO_SECAO,
)
from vigas_concreto_nbr6118.models import (
    SecaoViga,
    PropriedadesMateriais,
    EsforcosSolicitantes,
    PreferenciasDetalhamento,
    ProjetoViga,
    ResultadoFlexaoELU,
    ResultadoCisalhamentoELU,
    ResultadoDetalhamento,
    ResultadoELS,
    ResultadoProjetoViga,
)
from vigas_concreto_nbr6118.calculator import (
    dimensionar_flexao_elu,
    dimensionar_cisalhamento_elu,
    selecionar_detalhamento_armaduras,
    verificar_els,
    dimensionar_viga_concreto,
)
from vigas_concreto_nbr6118.exporters import (
    exportar_csv,
    gerar_relatorio_memorial,
    formatar_fracao_decimal,
)
from vigas_concreto_nbr6118.svg_generator import gerar_painel_svg, escapar_xml

__all__ = [
    "__version__",
    "GAMMA_C",
    "GAMMA_S",
    "GAMMA_F",
    "ALPHA_C",
    "LAMBDA_C",
    "XI_LIMITE_DUCTILIDADE",
    "ES_KN_CM2",
    "TABELA_CAA_NBR6118",
    "TABELA_CONCRETOS_NBR6118",
    "TABELA_ACOS_NBR6118",
    "TABELA_BITOLAS_COMERCIAIS",
    "RHO_MAXIMO_SECAO",
    "SecaoViga",
    "PropriedadesMateriais",
    "EsforcosSolicitantes",
    "PreferenciasDetalhamento",
    "ProjetoViga",
    "ResultadoFlexaoELU",
    "ResultadoCisalhamentoELU",
    "ResultadoDetalhamento",
    "ResultadoELS",
    "ResultadoProjetoViga",
    "dimensionar_flexao_elu",
    "dimensionar_cisalhamento_elu",
    "selecionar_detalhamento_armaduras",
    "verificar_els",
    "dimensionar_viga_concreto",
    "exportar_csv",
    "gerar_relatorio_memorial",
    "formatar_fracao_decimal",
    "gerar_painel_svg",
    "escapar_xml",
]
