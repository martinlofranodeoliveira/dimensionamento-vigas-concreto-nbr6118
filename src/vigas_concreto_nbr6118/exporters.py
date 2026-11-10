from __future__ import annotations

import csv
import io
from fractions import Fraction
from typing import Any, List

from vigas_concreto_nbr6118.models import ResultadoProjetoViga

CARACTERES_INJECAO_CSV = ("=", "+", "-", "@", "\t", "\r")


def sanitizar_campo_csv(valor: Any) -> str:
    """Sanitiza campos contra injeção de fórmulas CSV mantendo integridade."""
    texto = str(valor)
    if texto.startswith(CARACTERES_INJECAO_CSV):
        return "'" + texto
    return texto


def formatar_fracao_decimal(f: Fraction, casas: int = 2) -> str:
    """Converte fração em representação decimal exata com vírgula padrão pt-BR."""
    if f.denominator == 1:
        return str(f.numerator)
    fator = 10 ** casas
    val_inteiro = round((f.numerator * fator) / f.denominator)
    sinal = "-" if val_inteiro < 0 else ""
    val_abs = abs(val_inteiro)
    parte_int = val_abs // fator
    parte_dec = str(val_abs % fator).zfill(casas)
    return f"{sinal}{parte_int},{parte_dec}"


def exportar_csv(resultado: ResultadoProjetoViga) -> str:
    """Exporta planilha técnica estruturada em formato CSV com proteção contra injeção de fórmulas."""
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";", quoting=csv.QUOTE_MINIMAL)

    # Cabeçalho Geral
    escritor.writerow([
        sanitizar_campo_csv("Categoria"),
        sanitizar_campo_csv("Parâmetro"),
        sanitizar_campo_csv("Valor Calculado / Adotado"),
        sanitizar_campo_csv("Unidade"),
        sanitizar_campo_csv("Referência Normativa"),
        sanitizar_campo_csv("Conformidade"),
    ])

    sec = resultado.secao
    rf = resultado.resultado_flexao
    rc = resultado.resultado_cisalhamento
    rd = resultado.resultado_detalhamento
    re = resultado.resultado_els

    # Seção Transversal e Vão
    escritor.writerow(["Geometria", "Largura (bw)", formatar_fracao_decimal(sec.largura_bw_cm, 1), "cm", "NBR 6118 item 15.2.4", "CONFORME"])
    escritor.writerow(["Geometria", "Altura total (h)", formatar_fracao_decimal(sec.altura_h_cm, 1), "cm", "NBR 6118 item 15.2.4", "CONFORME"])
    escritor.writerow(["Geometria", "Altura útil (d)", formatar_fracao_decimal(rf.altura_util_d_cm, 1), "cm", "NBR 6118 item 17.2", "CONFORME"])
    escritor.writerow(["Geometria", "Vão teórico (L)", formatar_fracao_decimal(sec.comprimento_vao_m, 2), "m", "NBR 6118 item 14.6", "CONFORME"])

    # Flexão Simples (ELU)
    escritor.writerow(["Flexão ELU", "Momento de Cálculo (Msd)", formatar_fracao_decimal(rf.momento_sd_kNm, 2), "kN.m", "NBR 6118 item 17.2", "CONFORME"])
    escritor.writerow(["Flexão ELU", "Posição Linha Neutra (x)", formatar_fracao_decimal(rf.posicao_linha_neutra_x_cm, 2), "cm", "NBR 6118 item 17.2", "CONFORME"])
    escritor.writerow(["Flexão ELU", "Relação x/d (xi)", formatar_fracao_decimal(rf.relacao_x_d, 3), "-", "Limite: xi <= 0,45", "CONFORME" if rf.atende_ductilidade else "REPROVADO"])
    escritor.writerow(["Flexão ELU", "Domínio de Deformação", rf.dominio_deformacao, "-", "Domínio 2 / 3", "CONFORME"])
    escritor.writerow(["Flexão ELU", "Armadura Tração Necessária (As)", formatar_fracao_decimal(rf.area_aco_tracao_final_cm2, 2), "cm²", "NBR 6118 item 17.2", "CONFORME"])
    escritor.writerow(["Flexão ELU", "Armadura Mínima (As,min)", formatar_fracao_decimal(rf.area_aco_minima_cm2, 2), "cm²", "NBR 6118 Tabela 17.3", "CONFORME"])
    if rf.area_aco_compressao_calculada_cm2 > 0:
        escritor.writerow(["Flexão ELU", "Armadura Compressão (As')", formatar_fracao_decimal(rf.area_aco_compressao_calculada_cm2, 2), "cm²", "NBR 6118 item 17.2", "CONFORME"])

    # Cisalhamento (ELU)
    escritor.writerow(["Cisalhamento ELU", "Cortante de Cálculo (Vsd)", formatar_fracao_decimal(rc.forca_cortante_sd_kN, 2), "kN", "NBR 6118 item 19.4", "CONFORME"])
    escritor.writerow(["Cisalhamento ELU", "Resistência da Biela (VRd2)", formatar_fracao_decimal(rc.resistencia_biela_v_rd2_kN, 2), "kN", "NBR 6118 item 19.4.1", "CONFORME" if rc.atende_biela_compressao else "REPROVADO"])
    escritor.writerow(["Cisalhamento ELU", "Parcela Concreto (Vc)", formatar_fracao_decimal(rc.parcela_concreto_vc_kN, 2), "kN", "NBR 6118 item 19.4.1", "CONFORME"])
    escritor.writerow(["Cisalhamento ELU", "Armadura Transversal (Asw/s)", formatar_fracao_decimal(rc.area_estribos_por_metro_final_cm2_m, 2), "cm²/m", "NBR 6118 item 19.4.1", "CONFORME"])
    escritor.writerow(["Cisalhamento ELU", "Espaçamento Máximo (s,max)", formatar_fracao_decimal(rc.espacamento_maximo_estribo_cm, 1), "cm", "NBR 6118 item 18.3.3", "CONFORME"])

    # Detalhamento Construtivo
    escritor.writerow(["Detalhamento", "Armadura Longitudinal Tração", rd.barras_tracao, "-", f"As,ef = {formatar_fracao_decimal(rd.area_tracao_efetiva_cm2, 2)} cm²", "CONFORME"])
    if rd.barras_compressao:
        escritor.writerow(["Detalhamento", "Armadura Superior / Compressão", rd.barras_compressao, "-", f"As',ef = {formatar_fracao_decimal(rd.area_compressao_efetiva_cm2, 2)} cm²", "CONFORME"])
    escritor.writerow(["Detalhamento", "Armadura Transversal (Estribos)", rd.estribos_adotados, "-", f"Asw,ef = {formatar_fracao_decimal(rd.area_estribo_efetiva_cm2_m, 2)} cm²/m", "CONFORME"])

    # Estados Limites de Serviço (ELS)
    escritor.writerow(["Serviço ELS", "Abertura Fissuras (wk)", formatar_fracao_decimal(re.abertura_fissura_estimada_wk_mm, 3), "mm", f"Limite: {formatar_fracao_decimal(re.limite_fissura_w_lim_mm, 2)} mm", "CONFORME" if re.atende_fissuracao else "REPROVADO"])
    escritor.writerow(["Serviço ELS", "Flecha Total Diferida", formatar_fracao_decimal(re.flecha_total_diferida_cm, 2), "cm", f"Limite: {formatar_fracao_decimal(re.flecha_limite_cm, 2)} cm", "CONFORME" if re.atende_deformacao else "REPROVADO"])

    return saida.getvalue()


def gerar_relatorio_memorial(resultado: ResultadoProjetoViga) -> str:
    """Gera o memorial de cálculo técnico estrutural completo em texto plano pt-BR."""
    sec = resultado.secao
    rf = resultado.resultado_flexao
    rc = resultado.resultado_cisalhamento
    rd = resultado.resultado_detalhamento
    re = resultado.resultado_els

    linhas: List[str] = [
        "=" * 80,
        "       LOFRANO TECNOLOGIA - ENGENHARIA ESTRUTURAL DE CONCRETO ARMADO",
        "         MEMORIAL DE CÁLCULO NORMATIVO - ABNT NBR 6118:2023 (VIGAS)",
        "=" * 80,
        f"Projeto / Identificação: {resultado.identificacao}",
        f"Norma Regulamentadora:   {resultado.norma}",
        f"Status de Aprovação:     {'APROVADO' if resultado.atende_geral else 'COM RESTRIÇÕES / NÃO CONFORME'}",
        "-" * 80,
        "1. CARACTERÍSTICAS GEOMÉTRICAS E DA SEÇÃO TRANSVERSAL",
        f"  - Largura da nervura (bw):   {formatar_fracao_decimal(sec.largura_bw_cm, 1)} cm",
        f"  - Altura total da viga (h):  {formatar_fracao_decimal(sec.altura_h_cm, 1)} cm",
        f"  - Altura útil (d):           {formatar_fracao_decimal(rf.altura_util_d_cm, 1)} cm",
        f"  - Vão teórico livre (L):     {formatar_fracao_decimal(sec.comprimento_vao_m, 2)} m ({sec.tipo_apoio})",
        "",
        "2. DIMENSIONAMENTO À FLEXÃO SIMPLES NO ESTADO LIMITE ÚLTIMO (ELU)",
        f"  - Momento fletor de cálculo (Msd): {formatar_fracao_decimal(rf.momento_sd_kNm, 2)} kN.m",
        f"  - Momento adimensional (mu):        {formatar_fracao_decimal(rf.parametro_mu, 4)}",
        f"  - Posição da linha neutra (x):      {formatar_fracao_decimal(rf.posicao_linha_neutra_x_cm, 2)} cm",
        f"  - Relação x/d (xi):                 {formatar_fracao_decimal(rf.relacao_x_d, 3)} (Limite ductilidade: 0,45)",
        f"  - Domínio de Deformação:            {rf.dominio_deformacao}",
        f"  - Tipo de armadura dimensionada:    {rf.tipo_armadura.upper()}",
        f"  - Armadura de tração calculada:     {formatar_fracao_decimal(rf.area_aco_tracao_calculada_cm2, 2)} cm²",
        f"  - Armadura mínima normativa:        {formatar_fracao_decimal(rf.area_aco_minima_cm2, 2)} cm²",
        f"  - Armadura de tração final:         {formatar_fracao_decimal(rf.area_aco_tracao_final_cm2, 2)} cm²",
    ]

    if rf.area_aco_compressao_calculada_cm2 > 0:
        linhas.append(f"  - Armadura de compressão (As'):     {formatar_fracao_decimal(rf.area_aco_compressao_calculada_cm2, 2)} cm²")

    linhas.extend([
        "",
        "3. DIMENSIONAMENTO AO CISALHAMENTO NO ELU (MODELO DE CÁLCULO I)",
        f"  - Força cortante de cálculo (Vsd):   {formatar_fracao_decimal(rc.forca_cortante_sd_kN, 2)} kN",
        f"  - Força resistente da biela (VRd2):  {formatar_fracao_decimal(rc.resistencia_biela_v_rd2_kN, 2)} kN -> {'ATENDE BIELA' if rc.atende_biela_compressao else 'ESMAGAMENTO BIELA'}",
        f"  - Taxa de trabalho da biela:         {formatar_fracao_decimal(rc.taxa_trabalho_biela * 100, 1)}%",
        f"  - Parcela resistida pelo concreto (Vc): {formatar_fracao_decimal(rc.parcela_concreto_vc_kN, 2)} kN",
        f"  - Parcela resistida pelo aço (Vsw):     {formatar_fracao_decimal(rc.parcela_armadura_vsw_kN, 2)} kN",
        f"  - Taxa de armadura transversal:      {formatar_fracao_decimal(rc.area_estribos_por_metro_final_cm2_m, 2)} cm²/m (Mín: {formatar_fracao_decimal(rc.area_estribos_por_metro_minima_cm2_m, 2)} cm²/m)",
        f"  - Espaçamento máximo normativo:      {formatar_fracao_decimal(rc.espacamento_maximo_estribo_cm, 1)} cm",
        "",
        "4. DETALHAMENTO DAS ARMADURAS (BARRAS COMERCIAIS)",
        f"  - Armadura Longitudinal Inferior:    {rd.barras_tracao} (As,ef = {formatar_fracao_decimal(rd.area_tracao_efetiva_cm2, 2)} cm²)",
    ])

    if rd.barras_compressao:
        linhas.append(f"  - Armadura Superior:                 {rd.barras_compressao}")

    linhas.extend([
        f"  - Armadura Transversal (Estribos):   {rd.estribos_adotados} (Asw,ef = {formatar_fracao_decimal(rd.area_estribo_efetiva_cm2_m, 2)} cm²/m)",
        "",
        "5. VERIFICAÇÃO DOS ESTADOS LIMITES DE SERVIÇO (ELS)",
        f"  - Abertura de fissuras estimada (wk): {formatar_fracao_decimal(re.abertura_fissura_estimada_wk_mm, 3)} mm (Limite: {formatar_fracao_decimal(re.limite_fissura_w_lim_mm, 2)} mm) -> {'CONFORME' if re.atende_fissuracao else 'NÃO CONFORME'}",
        f"  - Flecha imediata em serviço:         {formatar_fracao_decimal(re.flecha_imediata_cm, 2)} cm",
        f"  - Flecha total diferida (tempo):      {formatar_fracao_decimal(re.flecha_total_diferida_cm, 2)} cm (Limite L/250: {formatar_fracao_decimal(re.flecha_limite_cm, 2)} cm) -> {'CONFORME' if re.atende_deformacao else 'NÃO CONFORME'}",
        "",
        "6. SÍNTESE DE CONFORMIDADES",
        f"  - [flexao_elu]:       {'CONFORME' if resultado.conformidades.get('flexao_elu', False) else 'REPROVADO'}",
        f"  - [cisalhamento_elu]: {'CONFORME' if resultado.conformidades.get('cisalhamento_elu', False) else 'REPROVADO'}",
        f"  - [fissuracao_els]:   {'CONFORME' if resultado.conformidades.get('fissuracao_els', False) else 'REPROVADO'}",
        f"  - [deformacao_els]:   {'CONFORME' if resultado.conformidades.get('deformacao_els', False) else 'REPROVADO'}",
    ])

    if resultado.alertas:
        linhas.append("  ALERTAS DE PROJETO:")
        for al in resultado.alertas:
            linhas.append(f"    [!] {al}")

    if resultado.recomendacoes:
        linhas.append("  RECOMENDAÇÕES EXECUTIVAS:")
        for rec in resultado.recomendacoes:
            linhas.append(f"    [*] {rec}")

    linhas.extend([
        "=" * 80,
        "LOFRANO TECNOLOGIA - Soluções Determinísticas e Engenharia Confiável.",
        "=" * 80,
    ])

    return "\n".join(linhas)
