from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Optional, List, Dict, Any


@dataclass(frozen=True)
class SecaoViga:
    """Geometria da seção transversal e vão da viga de concreto armado."""
    largura_bw_cm: Fraction
    altura_h_cm: Fraction
    comprimento_vao_m: Fraction
    tipo_apoio: str = "biapoiada"  # "biapoiada", "continua", "engastada_apoiada", "balanco"

    def __post_init__(self) -> None:
        if self.largura_bw_cm <= 0:
            raise ValueError("Largura da viga (bw) deve ser estritamente positiva.")
        if self.altura_h_cm <= 0:
            raise ValueError("Altura da viga (h) deve ser estritamente positiva.")
        if self.comprimento_vao_m <= 0:
            raise ValueError("Vão da viga deve ser estritamente positivo.")
        if self.largura_bw_cm < 12:
            # NBR 6118 item 15.2.4.1 permite 12 cm para vigas normais (ou até 10 cm em casos especiais)
            pass


@dataclass(frozen=True)
class PropriedadesMateriais:
    """Especificações de materiais e durabilidade segundo NBR 6118."""
    classe_concreto_fck: int = 25  # C25
    tipo_aco_longitudinal: str = "CA_50"
    tipo_aco_transversal: str = "CA_50"
    classe_agressividade: str = "CAA_II"
    cobrimento_nominal_cm: Optional[Fraction] = None

    def __post_init__(self) -> None:
        if self.classe_concreto_fck < 20 or self.classe_concreto_fck > 50:
            raise ValueError(f"Classe de concreto C{self.classe_concreto_fck} fora do escopo Grupo I (C20 a C50).")
        if self.classe_agressividade not in ("CAA_I", "CAA_II", "CAA_III", "CAA_IV"):
            raise ValueError(f"Classe de Agressividade Ambiental '{self.classe_agressividade}' inválida.")


@dataclass(frozen=True)
class EsforcosSolicitantes:
    """Esforços solicitantes característicos ou de cálculo atuantes na seção crítica."""
    momento_fletor_k_kNm: Fraction
    forca_cortante_k_kN: Fraction
    momento_fletor_d_kNm: Optional[Fraction] = None
    forca_cortante_d_kN: Optional[Fraction] = None

    def __post_init__(self) -> None:
        if self.momento_fletor_k_kNm < 0:
            raise ValueError("Momento fletor característico deve ser positivo ou nulo (em módulo).")
        if self.forca_cortante_k_kN < 0:
            raise ValueError("Força cortante característica deve ser positiva ou nula (em módulo).")


@dataclass(frozen=True)
class PreferenciasDetalhamento:
    """Preferências para seleção e arranjo de barras longitudinais e estribos."""
    bitola_longitudinal_sugerida_mm: Optional[Fraction] = None
    bitola_estribo_sugerida_mm: Optional[Fraction] = None
    numero_ramos_estribo: int = 2
    d_linha_estimado_cm: Fraction = Fraction(4, 1)  # Distância do centroide da armadura até a face tracionada

    def __post_init__(self) -> None:
        if self.numero_ramos_estribo <= 0:
            raise ValueError("Número de ramos do estribo deve ser maior ou igual a 1.")
        if self.d_linha_estimado_cm <= 0:
            raise ValueError("d' estimado deve ser positivo.")


@dataclass(frozen=True)
class ProjetoViga:
    """Entrada completa para dimensionamento de viga de concreto armado sob NBR 6118."""
    identificacao: str
    secao: SecaoViga
    materiais: PropriedadesMateriais = field(default_factory=PropriedadesMateriais)
    esforcos: EsforcosSolicitantes = field(default_factory=lambda: EsforcosSolicitantes(Fraction(0, 1), Fraction(0, 1)))
    detalhamento: PreferenciasDetalhamento = field(default_factory=PreferenciasDetalhamento)


@dataclass(frozen=True)
class ResultadoFlexaoELU:
    """Resultado do dimensionamento à flexão simples no Estado Limite Último (ELU)."""
    momento_sd_kNm: Fraction
    altura_util_d_cm: Fraction
    parametro_mu: Fraction
    posicao_linha_neutra_x_cm: Fraction
    relacao_x_d: Fraction
    dominio_deformacao: str
    tipo_armadura: str  # "simples" ou "dupla"
    area_aco_tracao_calculada_cm2: Fraction
    area_aco_compressao_calculada_cm2: Fraction
    area_aco_minima_cm2: Fraction
    area_aco_maxima_cm2: Fraction
    area_aco_tracao_final_cm2: Fraction
    atende_ductilidade: bool
    atende_taxa_maxima: bool
    observacoes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResultadoCisalhamentoELU:
    """Resultado do dimensionamento à força cortante no Estado Limite Último (ELU - Modelo I)."""
    forca_cortante_sd_kN: Fraction
    resistencia_biela_v_rd2_kN: Fraction
    atende_biela_compressao: bool
    taxa_trabalho_biela: Fraction
    parcela_concreto_vc_kN: Fraction
    parcela_armadura_vsw_kN: Fraction
    area_estribos_por_metro_calculada_cm2_m: Fraction
    area_estribos_por_metro_minima_cm2_m: Fraction
    area_estribos_por_metro_final_cm2_m: Fraction
    espacamento_maximo_estribo_cm: Fraction
    atende_cisalhamento: bool
    observacoes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResultadoDetalhamento:
    """Detalhamento com barras padronizadas de aço CA-50 / CA-60."""
    barras_tracao: str
    numero_barras_tracao: int
    bitola_tracao_mm: Fraction
    area_tracao_efetiva_cm2: Fraction
    barras_compressao: Optional[str]
    numero_barras_compressao: int
    bitola_compressao_mm: Optional[Fraction]
    area_compressao_efetiva_cm2: Fraction
    estribos_adotados: str
    bitola_estribo_mm: Fraction
    espacamento_estribo_cm: Fraction
    area_estribo_efetiva_cm2_m: Fraction
    numero_ramos: int
    observacoes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResultadoELS:
    """Verificação do Estado Limite de Serviço (Fissuração e Deformação Excessiva)."""
    momento_servico_kNm: Fraction
    tensao_aco_servico_kN_cm2: Fraction
    limite_fissura_w_lim_mm: Fraction
    abertura_fissura_estimada_wk_mm: Fraction
    atende_fissuracao: bool
    flecha_imediata_cm: Fraction
    flecha_total_diferida_cm: Fraction
    flecha_limite_cm: Fraction
    atende_deformacao: bool
    observacoes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResultadoProjetoViga:
    """Resultado consolidado do dimensionamento estrutural e verificação normativa."""
    identificacao: str
    norma: str
    secao: SecaoViga
    resultado_flexao: ResultadoFlexaoELU
    resultado_cisalhamento: ResultadoCisalhamentoELU
    resultado_detalhamento: ResultadoDetalhamento
    resultado_els: ResultadoELS
    atende_geral: bool
    conformidades: Dict[str, bool]
    alertas: List[str]
    recomendacoes: List[str]
