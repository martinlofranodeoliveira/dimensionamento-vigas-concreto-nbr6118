from __future__ import annotations

import math
from fractions import Fraction
from typing import Optional, List, Dict, Any, Tuple

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


def raiz_quadrada_fracao(frac: Fraction, precisao: int = 12) -> Fraction:
    """Calcula a raiz quadrada exata de uma fração sem admitir float IEEE-754."""
    if frac <= 0:
        return Fraction(0, 1)
    fator = 10 ** (2 * precisao)
    p, q = frac.numerator, frac.denominator
    r = math.isqrt(p * q * fator)
    return Fraction(r, q * (10 ** precisao))


def obter_cobrimento_nominal(materiais: PropriedadesMateriais) -> Fraction:
    """Retorna o cobrimento nominal c_nom em centímetros (cm)."""
    if materiais.cobrimento_nominal_cm is not None:
        return materiais.cobrimento_nominal_cm
    caa_info = TABELA_CAA_NBR6118.get(materiais.classe_agressividade, TABELA_CAA_NBR6118["CAA_II"])
    c_nom_mm = caa_info["cobrimento_nominal_mm"]
    return Fraction(c_nom_mm, 10)  # mm -> cm


def dimensionar_flexao_elu(
    secao: SecaoViga,
    materiais: PropriedadesMateriais,
    esforcos: EsforcosSolicitantes,
    detalhamento: PreferenciasDetalhamento,
) -> ResultadoFlexaoELU:
    """Dimensiona a armadura longitudinal de flexão simples no Estado Limite Último (ELU)."""
    # 1. Momento fletor de cálculo M_sd (kN·m) e M_sd (kN·cm)
    if esforcos.momento_fletor_d_kNm is not None:
        m_sd_kNm = esforcos.momento_fletor_d_kNm
    else:
        m_sd_kNm = esforcos.momento_fletor_k_kNm * GAMMA_F

    m_sd_kNcm = m_sd_kNm * 100

    # 2. Altura útil d (cm)
    d_cm = secao.altura_h_cm - detalhamento.d_linha_estimado_cm
    if d_cm <= 0:
        raise ValueError("Altura útil da viga (d = h - d') deve ser estritamente positiva.")

    # 3. Propriedades do concreto e do aço
    fck = materiais.classe_concreto_fck
    conc_info = TABELA_CONCRETOS_NBR6118.get(fck, TABELA_CONCRETOS_NBR6118[25])
    # fcd em kN/cm² (1 MPa = 0,1 kN/cm²)
    f_cd_kN_cm2 = Fraction(fck, 1) / (Fraction(10, 1) * GAMMA_C)
    sigma_cd = ALPHA_C * f_cd_kN_cm2

    # fyd em kN/cm² (CA-50: 50 / 1,15)
    aco_info = TABELA_ACOS_NBR6118.get(materiais.tipo_aco_longitudinal, TABELA_ACOS_NBR6118["CA_50"])
    f_yd_kN_cm2 = aco_info["fyd_kn_cm2"]

    # 4. Parâmetro adimensional reduzido mu
    bw = secao.largura_bw_cm
    den_mu = bw * (d_cm ** 2) * sigma_cd
    mu = m_sd_kNcm / den_mu if den_mu > 0 else Fraction(0, 1)

    # Limite de ductilidade da NBR 6118 (xi <= 0,45 para fck <= 50 MPa)
    xi_lim = XI_LIMITE_DUCTILIDADE  # 0,45
    # mu_lim = 0,80 * xi_lim * (1 - 0,40 * xi_lim) = 0,80 * 0,45 * (1 - 0,18) = 0,36 * 0,82 = 0,2952
    mu_lim = LAMBDA_C * xi_lim * (Fraction(1, 1) - Fraction(4, 10) * xi_lim)

    obs: List[str] = []
    area_as_comp_cm2 = Fraction(0, 1)

    if mu <= mu_lim:
        # Armadura Simples (Domínio 2 ou 3)
        tipo_armadura = "simples"
        atende_ductilidade = True
        termo_raiz = Fraction(1, 1) - Fraction(2, 1) * mu
        raiz_val = raiz_quadrada_fracao(termo_raiz)
        xi = (Fraction(1, 1) - raiz_val) / LAMBDA_C
        posicao_x_cm = xi * d_cm

        # Braço de alavanca z = d * (1 - 0,40 * xi)
        z_cm = d_cm * (Fraction(1, 1) - Fraction(4, 10) * xi)
        area_as_calc_cm2 = m_sd_kNcm / (f_yd_kN_cm2 * z_cm)

        if xi <= Fraction(259, 1000):
            dominio = "Domínio 2"
            obs.append("Deformação plástica do aço com escoamento pleno a 10‰ (Domínio 2).")
        else:
            dominio = "Domínio 3"
            obs.append("Encurtamento do concreto a 3,5‰ com escoamento do aço (Domínio 3).")
    else:
        # Armadura Dupla necessária para garantir ductilidade (xi = 0,45)
        tipo_armadura = "dupla"
        atende_ductilidade = True  # Atende pois armadura dupla garante xi = 0,45
        dominio = "Domínio 3 (Armadura Dupla)"
        xi = xi_lim
        posicao_x_cm = xi * d_cm

        # Momento suportado pela armadura simples limite
        m_sd1_kNcm = mu_lim * bw * (d_cm ** 2) * sigma_cd
        delta_m_kNcm = m_sd_kNcm - m_sd1_kNcm

        z_lim_cm = d_cm * (Fraction(1, 1) - Fraction(4, 10) * xi_lim)
        as1_cm2 = m_sd1_kNcm / (f_yd_kN_cm2 * z_lim_cm)

        # Braço da armadura de compressão (d - d')
        d_linha = detalhamento.d_linha_estimado_cm
        braco_comp_cm = d_cm - d_linha
        if braco_comp_cm <= 0:
            braco_comp_cm = Fraction(1, 1)

        # Tensão no aço comprimido (CA-50 escoa se x >= 2 * d')
        f_s_comp_kN_cm2 = f_yd_kN_cm2
        area_as_comp_cm2 = delta_m_kNcm / (f_s_comp_kN_cm2 * braco_comp_cm)
        delta_as_cm2 = delta_m_kNcm / (f_yd_kN_cm2 * braco_comp_cm)

        area_as_calc_cm2 = as1_cm2 + delta_as_cm2
        obs.append(
            f"Momento fletor elevado (mu={float(mu):.3f} > {float(mu_lim):.3f}): dimensionada armadura dupla (As'={float(area_as_comp_cm2):.2f} cm²)."
        )

    # 5. Armadura Mínima e Máxima (NBR 6118 Tabela 17.3 e item 17.3.5.2)
    area_concreto_ac = bw * secao.altura_h_cm
    rho_min = conc_info["rho_min"]
    area_as_min_cm2 = rho_min * area_concreto_ac
    area_as_max_cm2 = RHO_MAXIMO_SECAO * area_concreto_ac

    # Armadura de tração final adotada
    area_as_tracao_final = max(area_as_calc_cm2, area_as_min_cm2)
    if area_as_calc_cm2 < area_as_min_cm2:
        obs.append(
            f"Armadura calculada ({float(area_as_calc_cm2):.2f} cm²) inferior à mínima normativa ({float(area_as_min_cm2):.2f} cm²); adotada As,min."
        )

    atende_taxa_max = (area_as_tracao_final + area_as_comp_cm2) <= area_as_max_cm2
    if not atende_taxa_max:
        obs.append(
            f"Armadura total ({float(area_as_tracao_final + area_as_comp_cm2):.2f} cm²) excede o limite máximo normativo de 4% ({float(area_as_max_cm2):.2f} cm²). Redimensione a seção transversal."
        )

    return ResultadoFlexaoELU(
        momento_sd_kNm=m_sd_kNm,
        altura_util_d_cm=d_cm,
        parametro_mu=mu,
        posicao_linha_neutra_x_cm=posicao_x_cm,
        relacao_x_d=xi,
        dominio_deformacao=dominio,
        tipo_armadura=tipo_armadura,
        area_aco_tracao_calculada_cm2=area_as_calc_cm2,
        area_aco_compressao_calculada_cm2=area_as_comp_cm2,
        area_aco_minima_cm2=area_as_min_cm2,
        area_aco_maxima_cm2=area_as_max_cm2,
        area_aco_tracao_final_cm2=area_as_tracao_final,
        atende_ductilidade=atende_ductilidade,
        atende_taxa_maxima=atende_taxa_max,
        observacoes=obs,
    )


def dimensionar_cisalhamento_elu(
    secao: SecaoViga,
    materiais: PropriedadesMateriais,
    esforcos: EsforcosSolicitantes,
    detalhamento: PreferenciasDetalhamento,
) -> ResultadoCisalhamentoELU:
    """Dimensiona a armadura transversal (estribos) segundo Modelo de Cálculo I da NBR 6118:2023."""
    # 1. Força cortante de cálculo V_sd (kN)
    if esforcos.forca_cortante_d_kN is not None:
        v_sd_kN = esforcos.forca_cortante_d_kN
    else:
        v_sd_kN = esforcos.forca_cortante_k_kN * GAMMA_F

    d_cm = secao.altura_h_cm - detalhamento.d_linha_estimado_cm
    bw = secao.largura_bw_cm
    fck = materiais.classe_concreto_fck
    conc_info = TABELA_CONCRETOS_NBR6118.get(fck, TABELA_CONCRETOS_NBR6118[25])

    # fcd em kN/cm²
    f_cd_kN_cm2 = Fraction(fck, 1) / (Fraction(10, 1) * GAMMA_C)

    # 2. Verificação da biela de compressão de concreto V_Rd2 (item 19.4.1)
    # alpha_v1 = (1 - fck / 250)
    alpha_v1 = Fraction(1, 1) - Fraction(fck, 250)
    # VRd2 = 0,27 * alpha_v1 * fcd * bw * d
    v_rd2_kN = Fraction(27, 100) * alpha_v1 * f_cd_kN_cm2 * bw * d_cm
    atende_biela = v_sd_kN <= v_rd2_kN
    taxa_biela = v_sd_kN / v_rd2_kN if v_rd2_kN > 0 else Fraction(1, 1)

    obs: List[str] = []
    if not atende_biela:
        obs.append(
            f"Esmagamento da biela comprimida de concreto: Vsd ({float(v_sd_kN):.1f} kN) excede VRd2 ({float(v_rd2_kN):.1f} kN). Aumente a seção de concreto ou o fck."
        )

    # 3. Parcela de força cortante resistida pelo concreto V_c
    # fctd = fctk_inf / gamma_c
    fctk_inf_mpa = conc_info["fctk_inf_mpa"]
    fctd_kN_cm2 = (fctk_inf_mpa / GAMMA_C) / Fraction(10, 1)
    # Vc = 0,60 * fctd * bw * d
    v_c_kN = Fraction(6, 10) * fctd_kN_cm2 * bw * d_cm

    # 4. Parcela resistida pela armadura V_sw
    if v_sd_kN <= v_c_kN:
        v_sw_kN = Fraction(0, 1)
        obs.append(
            f"Vsd ({float(v_sd_kN):.1f} kN) inferior a Vc ({float(v_c_kN):.1f} kN): necessária apenas armadura transversal mínima."
        )
    else:
        v_sw_kN = v_sd_kN - v_c_kN

    # 5. Tensão de cálculo dos estribos fywd (NBR 6118 item 19.4.1 limita a 43,5 kN/cm²)
    aco_transv = TABELA_ACOS_NBR6118.get(materiais.tipo_aco_transversal, TABELA_ACOS_NBR6118["CA_50"])
    f_ywd_kN_cm2 = min(aco_transv["fyd_kn_cm2"], Fraction(435, 10))

    # Asw / s = Vsw / (0,9 * d * fywd) (em cm²/cm)
    # Em cm²/m: multiplicar por 100
    if v_sw_kN > 0:
        asw_s_calc_cm2_cm = v_sw_kN / (Fraction(9, 10) * d_cm * f_ywd_kN_cm2)
        asw_s_calc_cm2_m = asw_s_calc_cm2_cm * 100
    else:
        asw_s_calc_cm2_m = Fraction(0, 1)

    # 6. Armadura transversal mínima (item 17.3.5.2.7)
    # (Asw / s)_min = 0,20 * (fctm / fywk) * bw (fctm e fywk em MPa)
    fctm_mpa = conc_info["fctm_mpa"]
    fywk_mpa = Fraction(aco_transv["fyk_mpa"], 1)
    asw_s_min_cm2_cm = Fraction(20, 100) * (fctm_mpa / fywk_mpa) * bw
    asw_s_min_cm2_m = asw_s_min_cm2_cm * 100

    asw_s_final_cm2_m = max(asw_s_calc_cm2_m, asw_s_min_cm2_m)

    # 7. Espaçamento máximo dos estribos s_max (NBR 6118 item 18.3.3.2)
    # Se Vsd <= 0,67 VRd2: s_max = min(0,6 * d, 30 cm)
    # Se Vsd > 0,67 VRd2: s_max = min(0,3 * d, 20 cm)
    limite_v = Fraction(67, 100) * v_rd2_kN
    if v_sd_kN <= limite_v:
        s_max_cm = min(Fraction(6, 10) * d_cm, Fraction(30, 1))
    else:
        s_max_cm = min(Fraction(3, 10) * d_cm, Fraction(20, 1))
        obs.append("Esforço cortante elevado (> 0,67 VRd2): espaçamento máximo reduzido para 0,3d ou 20 cm.")

    atende_cisalhamento = atende_biela

    return ResultadoCisalhamentoELU(
        forca_cortante_sd_kN=v_sd_kN,
        resistencia_biela_v_rd2_kN=v_rd2_kN,
        atende_biela_compressao=atende_biela,
        taxa_trabalho_biela=taxa_biela,
        parcela_concreto_vc_kN=v_c_kN,
        parcela_armadura_vsw_kN=v_sw_kN,
        area_estribos_por_metro_calculada_cm2_m=asw_s_calc_cm2_m,
        area_estribos_por_metro_minima_cm2_m=asw_s_min_cm2_m,
        area_estribos_por_metro_final_cm2_m=asw_s_final_cm2_m,
        espacamento_maximo_estribo_cm=s_max_cm,
        atende_cisalhamento=atende_cisalhamento,
        observacoes=obs,
    )


def selecionar_detalhamento_armaduras(
    secao: SecaoViga,
    materiais: PropriedadesMateriais,
    res_flexao: ResultadoFlexaoELU,
    res_cisalha: ResultadoCisalhamentoELU,
    detalhamento: PreferenciasDetalhamento,
) -> ResultadoDetalhamento:
    """Seleciona o número e bitola de barras comerciais para tração, compressão e estribos."""
    obs: List[str] = []

    # 1. Armadura de Tração
    area_nec_tracao = res_flexao.area_aco_tracao_final_cm2
    bitola_long = detalhamento.bitola_longitudinal_sugerida_mm or Fraction(125, 10)  # 12,5 mm padrão

    bitolas_long_opcoes = [
        Fraction(100, 10),
        Fraction(125, 10),
        Fraction(160, 10),
        Fraction(200, 10),
        Fraction(250, 10),
    ]
    if bitola_long not in bitolas_long_opcoes:
        bitola_long = Fraction(125, 10)

    # Área unitária da barra
    area_unit_tracao = TABELA_BITOLAS_COMERCIAIS[bitola_long]["area_cm2"]
    num_barras_tracao = math.ceil(float(area_nec_tracao / area_unit_tracao))
    if num_barras_tracao < 2:
        num_barras_tracao = 2  # Mínimo de 2 barras nos cantos inferiores da viga

    area_tracao_efetiva = Fraction(num_barras_tracao, 1) * area_unit_tracao

    # Verificação de largura para arranjo em 1 camada
    c_nom_cm = obter_cobrimento_nominal(materiais)
    diam_estribo_estimado_cm = Fraction(63, 100)  # 6,3 mm
    espaco_livre_cm = Fraction(20, 10)            # 2,0 cm
    diam_long_cm = bitola_long / 10

    largura_nec_1camada = (
        Fraction(2, 1) * c_nom_cm
        + Fraction(2, 1) * diam_estribo_estimado_cm
        + Fraction(num_barras_tracao, 1) * diam_long_cm
        + Fraction(num_barras_tracao - 1, 1) * espaco_livre_cm
    )

    if largura_nec_1camada <= secao.largura_bw_cm:
        camadas_txt = "1 camada"
    else:
        camadas_txt = "2 camadas (ou feixe)"
        obs.append(
            f"Largura da viga ({float(secao.largura_bw_cm):.1f} cm) exige arranjo das barras em {camadas_txt}."
        )

    barras_tracao_txt = f"{num_barras_tracao} Φ {float(bitola_long):.1f} mm ({camadas_txt})"

    # 2. Armadura de Compressão (se houver armadura dupla)
    num_barras_comp = 0
    bitola_comp: Optional[Fraction] = None
    area_comp_efetiva = Fraction(0, 1)
    barras_comp_txt: Optional[str] = None

    if res_flexao.area_aco_compressao_calculada_cm2 > 0:
        area_nec_comp = res_flexao.area_aco_compressao_calculada_cm2
        bitola_comp = Fraction(100, 10)  # 10 mm
        area_unit_comp = TABELA_BITOLAS_COMERCIAIS[bitola_comp]["area_cm2"]
        num_barras_comp = max(2, math.ceil(float(area_nec_comp / area_unit_comp)))
        area_comp_efetiva = Fraction(num_barras_comp, 1) * area_unit_comp
        barras_comp_txt = f"{num_barras_comp} Φ {float(bitola_comp):.1f} mm"
    else:
        # Armadura porta-estribos mínima (2 barras de 5,0 mm ou 6,3 mm)
        barras_comp_txt = "2 Φ 6.3 mm (porta-estribos construtivo)"

    # 3. Armadura Transversal (Estribos)
    n_ramos = detalhamento.numero_ramos_estribo
    bitola_estribo = detalhamento.bitola_estribo_sugerida_mm or Fraction(63, 10)  # 6,3 mm padrão
    if bitola_estribo not in (Fraction(50, 10), Fraction(63, 10), Fraction(80, 10)):
        bitola_estribo = Fraction(63, 10)

    area_unit_ramo = TABELA_BITOLAS_COMERCIAIS[bitola_estribo]["area_cm2"]
    area_estribo_total = Fraction(n_ramos, 1) * area_unit_ramo  # Asw por estribo (cm²)

    asw_s_nec_cm2_m = res_cisalha.area_estribos_por_metro_final_cm2_m
    s_max_cm = res_cisalha.espacamento_maximo_estribo_cm

    # s = (Asw / (Asw/s_m)) * 100 cm
    if asw_s_nec_cm2_m > 0:
        s_calculado_cm = (area_estribo_total / asw_s_nec_cm2_m) * 100
        s_adotado_cm_val = min(s_calculado_cm, s_max_cm)
    else:
        s_adotado_cm_val = s_max_cm

    # Arredonda espaçamento para baixo para múltiplos inteiros de 1 ou 2,5 cm
    s_adotado_inteiro = math.floor(float(s_adotado_cm_val))
    if s_adotado_inteiro < 5:
        s_adotado_inteiro = 5
    elif s_adotado_inteiro > 30:
        s_adotado_inteiro = 30

    espacamento_estribo_cm = Fraction(s_adotado_inteiro, 1)
    area_estribo_efetiva_cm2_m = (area_estribo_total / espacamento_estribo_cm) * 100

    estribos_txt = f"{n_ramos}R Φ {float(bitola_estribo):.1f} mm c/ {s_adotado_inteiro} cm"

    return ResultadoDetalhamento(
        barras_tracao=barras_tracao_txt,
        numero_barras_tracao=num_barras_tracao,
        bitola_tracao_mm=bitola_long,
        area_tracao_efetiva_cm2=area_tracao_efetiva,
        barras_compressao=barras_comp_txt,
        numero_barras_compressao=num_barras_comp,
        bitola_compressao_mm=bitola_comp,
        area_compressao_efetiva_cm2=area_comp_efetiva,
        estribos_adotados=estribos_txt,
        bitola_estribo_mm=bitola_estribo,
        espacamento_estribo_cm=espacamento_estribo_cm,
        area_estribo_efetiva_cm2_m=area_estribo_efetiva_cm2_m,
        numero_ramos=n_ramos,
        observacoes=obs,
    )


def verificar_els(
    secao: SecaoViga,
    materiais: PropriedadesMateriais,
    esforcos: EsforcosSolicitantes,
    res_flexao: ResultadoFlexaoELU,
    detalhamento_res: ResultadoDetalhamento,
) -> ResultadoELS:
    """Verifica os Estados Limites de Serviço: Abertura de fissuras (ELS-W) e Deformação (ELS-DEF)."""
    # 1. Momento de serviço M_serv (kN·m)
    m_serv_kNm = esforcos.momento_fletor_k_kNm
    m_serv_kNcm = m_serv_kNm * 100

    # Tensão no aço em serviço sigma_s (kN/cm²)
    d_cm = res_flexao.altura_util_d_cm
    z_cm = d_cm * (Fraction(1, 1) - Fraction(4, 10) * res_flexao.relacao_x_d)
    as_efetiva = detalhamento_res.area_tracao_efetiva_cm2

    sigma_s_kN_cm2 = m_serv_kNcm / (as_efetiva * z_cm) if (as_efetiva * z_cm) > 0 else Fraction(0, 1)
    sigma_s_mpa = sigma_s_kN_cm2 * 10

    # 2. Abertura de fissuras estimada wk (NBR 6118 item 17.3.3.2)
    # wk = (phi / (12,5 * eta1)) * (sigma_s / Es) * (3 * sigma_s / fctm)
    # Para barra nervurada CA-50: eta1 = 2,25 = 9/4
    eta1 = Fraction(9, 4)
    phi_mm = detalhamento_res.bitola_tracao_mm
    fck = materiais.classe_concreto_fck
    conc_info = TABELA_CONCRETOS_NBR6118.get(fck, TABELA_CONCRETOS_NBR6118[25])
    fctm_mpa = conc_info["fctm_mpa"]

    # wk em mm
    termo1 = phi_mm / (Fraction(125, 10) * eta1)
    termo2 = sigma_s_mpa / Fraction(210000, 1)
    termo3 = (Fraction(3, 1) * sigma_s_mpa) / fctm_mpa if fctm_mpa > 0 else Fraction(0, 1)

    wk_estimado_mm = termo1 * termo2 * termo3

    # Limite normativo conforme CAA
    caa_info = TABELA_CAA_NBR6118.get(materiais.classe_agressividade, TABELA_CAA_NBR6118["CAA_II"])
    w_lim_mm = caa_info["w_limite_mm"]
    atende_fissura = wk_estimado_mm <= w_lim_mm

    obs: List[str] = []
    if atende_fissura:
        obs.append(
            f"Abertura de fissuras (wk={float(wk_estimado_mm):.3f} mm) atende ao limite normativo wlim={float(w_lim_mm):.2f} mm."
        )
    else:
        obs.append(
            f"Abertura de fissuras (wk={float(wk_estimado_mm):.3f} mm) excede o limite wlim={float(w_lim_mm):.2f} mm. Aumente o número de barras ou reduza a bitola."
        )

    # 3. Deformação Excessiva (Flecha ELS-DEF)
    # Estimativa de flecha elástica imediata fi e diferida no tempo para viga biapoiada com carga distribuída:
    # fi = (5/384) * (q * L^4) / (Ecs * I_eq) ~ (5/48) * (M * L^2) / (Ecs * I_eq)
    # L em cm, M em kN·cm
    vao_cm = secao.comprimento_vao_m * 100
    # Módulo de elasticidade do concreto Ecs ~ 5600 * sqrt(fck) MPa
    # Para C25: Ecs ~ 28.000 MPa = 2.800 kN/cm²
    raiz_fck = raiz_quadrada_fracao(Fraction(fck, 1))
    e_cs_kN_cm2 = Fraction(560, 1) * raiz_fck

    # Inércia bruta I_c = (bw * h^3) / 12
    bw = secao.largura_bw_cm
    h = secao.altura_h_cm
    i_c_cm4 = (bw * (h ** 3)) / 12

    # Inércia equivalente simplificada (NBR 6118 Modelo de Branson) ~ 0,5 * Ic no Estádio II
    i_eq_cm4 = i_c_cm4 * Fraction(1, 2)

    # Flecha imediata fi (cm)
    den_flecha = Fraction(48, 1) * e_cs_kN_cm2 * i_eq_cm4
    if den_flecha > 0:
        flecha_imediata_cm = (Fraction(5, 1) * m_serv_kNcm * (vao_cm ** 2)) / den_flecha
    else:
        flecha_imediata_cm = Fraction(0, 1)

    # Coeficiente de fluência adicional diferida no tempo alpha_f ~ 1,32 para t > 70 meses
    alpha_f = Fraction(132, 100)
    flecha_total_cm = flecha_imediata_cm * (Fraction(1, 1) + alpha_f)

    # Limite normativo para aceitabilidade sensorial: L / 250
    flecha_limite_cm = vao_cm / 250
    atende_deformacao = flecha_total_cm <= flecha_limite_cm

    if atende_deformacao:
        obs.append(
            f"Flecha total diferida ({float(flecha_total_cm):.2f} cm) atende ao limite normativo L/250 ({float(flecha_limite_cm):.2f} cm)."
        )
    else:
        obs.append(
            f"Flecha total diferida ({float(flecha_total_cm):.2f} cm) excede o limite L/250 ({float(flecha_limite_cm):.2f} cm). Aumente a altura da viga (h)."
        )

    return ResultadoELS(
        momento_servico_kNm=m_serv_kNm,
        tensao_aco_servico_kN_cm2=sigma_s_kN_cm2,
        limite_fissura_w_lim_mm=w_lim_mm,
        abertura_fissura_estimada_wk_mm=wk_estimado_mm,
        atende_fissuracao=atende_fissura,
        flecha_imediata_cm=flecha_imediata_cm,
        flecha_total_diferida_cm=flecha_total_cm,
        flecha_limite_cm=flecha_limite_cm,
        atende_deformacao=atende_deformacao,
        observacoes=obs,
    )


def dimensionar_viga_concreto(projeto: ProjetoViga) -> ResultadoProjetoViga:
    """Consolida e executa o dimensionamento completo da viga de concreto sob a ABNT NBR 6118:2023."""
    res_flexao = dimensionar_flexao_elu(
        projeto.secao, projeto.materiais, projeto.esforcos, projeto.detalhamento
    )

    res_cisalha = dimensionar_cisalhamento_elu(
        projeto.secao, projeto.materiais, projeto.esforcos, projeto.detalhamento
    )

    res_detalhamento = selecionar_detalhamento_armaduras(
        projeto.secao, projeto.materiais, res_flexao, res_cisalha, projeto.detalhamento
    )

    res_els = verificar_els(
        projeto.secao, projeto.materiais, projeto.esforcos, res_flexao, res_detalhamento
    )

    conformidades = {
        "flexao_elu": res_flexao.atende_ductilidade and res_flexao.atende_taxa_maxima,
        "cisalhamento_elu": res_cisalha.atende_cisalhamento,
        "fissuracao_els": res_els.atende_fissuracao,
        "deformacao_els": res_els.atende_deformacao,
    }

    atende_geral = all(conformidades.values())

    alertas: List[str] = []
    if not res_flexao.atende_taxa_maxima:
        alertas.append("Taxa máxima de armadura (4%) excedida na seção transversal.")
    if not res_cisalha.atende_biela_compressao:
        alertas.append("Ruptura por esmagamento da biela comprimida de concreto (VRd2 insuficiente).")
    if not res_els.atende_fissuracao:
        alertas.append("Abertura característica de fissuras superior ao limite normativo.")
    if not res_els.atende_deformacao:
        alertas.append("Flecha total diferida superior ao limite normativo L/250.")

    recomendacoes: List[str] = []
    if atende_geral:
        recomendacoes.append(
            "Seção transversal e detalhamento plenamente conformes aos Estados Limites Último (ELU) e de Serviço (ELS) da ABNT NBR 6118:2023."
        )
    else:
        recomendacoes.append(
            "Ajuste os parâmetros de dimensionamento (aumento da seção bw x h ou elevação da classe de concreto fck) para mitigar as não conformidades indicadas."
        )

    return ResultadoProjetoViga(
        identificacao=projeto.identificacao,
        norma="ABNT NBR 6118:2023",
        secao=projeto.secao,
        resultado_flexao=res_flexao,
        resultado_cisalhamento=res_cisalha,
        resultado_detalhamento=res_detalhamento,
        resultado_els=res_els,
        atende_geral=atende_geral,
        conformidades=conformidades,
        alertas=alertas,
        recomendacoes=recomendacoes,
    )
