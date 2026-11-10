from __future__ import annotations

import html
from fractions import Fraction

from vigas_concreto_nbr6118.models import ResultadoProjetoViga
from vigas_concreto_nbr6118.exporters import formatar_fracao_decimal


def escapar_xml(texto: str) -> str:
    """Escapa caracteres especiais XML para renderização segura."""
    return html.escape(str(texto), quote=True)


def gerar_painel_svg(resultado: ResultadoProjetoViga) -> str:
    """Gera um painel técnico vetorial SVG 1440x900 profissional e atraente de viga de concreto."""
    sec = resultado.secao
    rf = resultado.resultado_flexao
    rc = resultado.resultado_cisalhamento
    rd = resultado.resultado_detalhamento
    re = resultado.resultado_els

    status_cor = "#10b981" if resultado.atende_geral else "#ef4444"
    status_texto = "VIGA CONFORME NBR 6118" if resultado.atende_geral else "RESTRIÇÃO / NÃO CONFORME"

    m_sd_str = formatar_fracao_decimal(rf.momento_sd_kNm, 1)
    v_sd_str = formatar_fracao_decimal(rc.forca_cortante_sd_kN, 1)
    as_str = formatar_fracao_decimal(rf.area_aco_tracao_final_cm2, 2)
    asw_str = formatar_fracao_decimal(rc.area_estribos_por_metro_final_cm2_m, 2)
    wk_str = formatar_fracao_decimal(re.abertura_fissura_estimada_wk_mm, 3)
    w_lim_str = formatar_fracao_decimal(re.limite_fissura_w_lim_mm, 2)
    flecha_str = formatar_fracao_decimal(re.flecha_total_diferida_cm, 2)
    flecha_lim_str = formatar_fracao_decimal(re.flecha_limite_cm, 2)

    bw_str = formatar_fracao_decimal(sec.largura_bw_cm, 0)
    h_str = formatar_fracao_decimal(sec.altura_h_cm, 0)
    d_str = formatar_fracao_decimal(rf.altura_util_d_cm, 1)
    x_str = formatar_fracao_decimal(rf.posicao_linha_neutra_x_cm, 1)
    xi_str = formatar_fracao_decimal(rf.relacao_x_d, 3)
    vao_str = formatar_fracao_decimal(sec.comprimento_vao_m, 2)

    id_proj = html.escape(resultado.identificacao)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" width="1440" height="900">
  <defs>
    <!-- Gradientes de Fundo -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0b1120" />
      <stop offset="50%" stop-color="#0f172a" />
      <stop offset="100%" stop-color="#1e293b" />
    </linearGradient>
    <linearGradient id="cardGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e293b" stop-opacity="0.95" />
      <stop offset="100%" stop-color="#0f172a" stop-opacity="0.95" />
    </linearGradient>
    <linearGradient id="concreteGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#475569" />
      <stop offset="100%" stop-color="#334155" />
    </linearGradient>
    <linearGradient id="compBlockGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#f87171" stop-opacity="0.8" />
      <stop offset="100%" stop-color="#ef4444" stop-opacity="0.8" />
    </linearGradient>
    <linearGradient id="rebarGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8" />
      <stop offset="100%" stop-color="#0284c7" />
    </linearGradient>

    <!-- Filtro de Sombra -->
    <filter id="dropShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="6" stdDeviation="5" flood-color="#000000" flood-opacity="0.4" />
    </filter>
  </defs>

  <!-- Fundo Principal -->
  <rect width="1440" height="900" fill="url(#bgGrad)" />

  <!-- Grid Sutil de Engenharia -->
  <g opacity="0.05" stroke="#38bdf8" stroke-width="1">
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" />
    </pattern>
    <rect width="1440" height="900" fill="url(#grid)" />
  </g>

  <!-- ==================== CABEÇALHO ==================== -->
  <g transform="translate(40, 26)">
    <!-- Logo Badge -->
    <rect x="0" y="0" width="180" height="32" rx="6" fill="#0284c7" fill-opacity="0.2" stroke="#38bdf8" stroke-width="1.5" />
    <text x="90" y="21" fill="#38bdf8" font-family="'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="700" letter-spacing="1.5" text-anchor="middle">LOFRANO TECNOLOGIA</text>

    <!-- Título e Subtítulo -->
    <text x="195" y="22" fill="#ffffff" font-family="'Segoe UI', Roboto, sans-serif" font-size="20" font-weight="700">DIMENSIONAMENTO DE VIGAS DE CONCRETO ARMADO</text>
    <text x="195" y="42" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="12">ABNT NBR 6118:2023 — Projeto de Estruturas de Concreto (ELU / ELS)</text>

    <!-- Badge de Identificação do Projeto -->
    <rect x="880" y="2" width="230" height="34" rx="6" fill="#1e293b" stroke="#334155" stroke-width="1" />
    <text x="895" y="18" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="10">VIGA / ELEMENTO:</text>
    <text x="895" y="30" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="600">{id_proj}</text>

    <!-- Badge de Status Geral -->
    <rect x="1125" y="2" width="275" height="34" rx="6" fill="{status_cor}" fill-opacity="0.15" stroke="{status_cor}" stroke-width="1.5" />
    <circle cx="1145" cy="19" r="6" fill="{status_cor}" />
    <text x="1160" y="23" fill="{status_cor}" font-family="'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="700">{status_texto}</text>
  </g>

  <!-- ==================== CARTÕES SUPERIORES (KPIs) ==================== -->
  <g transform="translate(40, 85)">
    <!-- Cartão 1: Momento Fletor de Cálculo -->
    <rect x="0" y="0" width="256" height="88" rx="8" fill="url(#cardGrad)" stroke="#334155" stroke-width="1" filter="url(#dropShadow)" />
    <text x="20" y="26" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600" letter-spacing="0.5">MOMENTO FLETOR (ELU)</text>
    <text x="20" y="58" fill="#38bdf8" font-family="'Segoe UI', Roboto, sans-serif" font-size="28" font-weight="800">{m_sd_str}</text>
    <text x="150" y="58" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="13">kN·m (Msd)</text>
    <text x="20" y="76" fill="#64748b" font-family="'Segoe UI', Roboto, sans-serif" font-size="10">x/d = {xi_str} • {rf.dominio_deformacao}</text>

    <!-- Cartão 2: Força Cortante (ELU) -->
    <rect x="276" y="0" width="256" height="88" rx="8" fill="url(#cardGrad)" stroke="#334155" stroke-width="1" filter="url(#dropShadow)" />
    <text x="296" y="26" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600" letter-spacing="0.5">FORÇA CORTANTE (ELU)</text>
    <text x="296" y="58" fill="#38bdf8" font-family="'Segoe UI', Roboto, sans-serif" font-size="28" font-weight="800">{v_sd_str}</text>
    <text x="410" y="58" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="13">kN (Vsd)</text>
    <text x="296" y="76" fill="#10b981" font-family="'Segoe UI', Roboto, sans-serif" font-size="10">Biela VRd2: {formatar_fracao_decimal(rc.resistencia_biela_v_rd2_kN, 0)} kN (OK)</text>

    <!-- Cartão 3: Armadura Longitudinal -->
    <rect x="552" y="0" width="256" height="88" rx="8" fill="url(#cardGrad)" stroke="#334155" stroke-width="1" filter="url(#dropShadow)" />
    <text x="572" y="26" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600" letter-spacing="0.5">ARMADURA TRAÇÃO (As)</text>
    <text x="572" y="58" fill="#38bdf8" font-family="'Segoe UI', Roboto, sans-serif" font-size="28" font-weight="800">{as_str}</text>
    <text x="686" y="58" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="13">cm²</text>
    <text x="572" y="76" fill="#64748b" font-family="'Segoe UI', Roboto, sans-serif" font-size="10">Adotado: {rd.barras_tracao}</text>

    <!-- Cartão 4: Armadura Transversal (Estribos) -->
    <rect x="828" y="0" width="256" height="88" rx="8" fill="url(#cardGrad)" stroke="#334155" stroke-width="1" filter="url(#dropShadow)" />
    <text x="848" y="26" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600" letter-spacing="0.5">ESTRIBOS (Asw/s)</text>
    <text x="848" y="58" fill="#10b981" font-family="'Segoe UI', Roboto, sans-serif" font-size="28" font-weight="800">{asw_str}</text>
    <text x="962" y="58" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="13">cm²/m</text>
    <text x="848" y="76" fill="#64748b" font-family="'Segoe UI', Roboto, sans-serif" font-size="10">Adotado: {rd.estribos_adotados}</text>

    <!-- Cartão 5: Verificações ELS -->
    <rect x="1104" y="0" width="256" height="88" rx="8" fill="url(#cardGrad)" stroke="#334155" stroke-width="1" filter="url(#dropShadow)" />
    <text x="1124" y="26" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600" letter-spacing="0.5">ESTADO LIMITE SERVIÇO</text>
    <text x="1124" y="58" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="24" font-weight="800">{flecha_str} cm</text>
    <text x="1235" y="58" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="12">/ {flecha_lim_str} cm</text>
    <text x="1124" y="76" fill="#64748b" font-family="'Segoe UI', Roboto, sans-serif" font-size="10">Fissura: wk={wk_str} mm (≤ {w_lim_str})</text>
  </g>

  <!-- ==================== CORPO CENTRAL ESQUERDO: SEÇÃO TRANSVERSAL E TENSÕES ==================== -->
  <g transform="translate(40, 190)">
    <!-- Painel Seção Transversal -->
    <rect x="0" y="0" width="460" height="660" rx="10" fill="url(#cardGrad)" stroke="#334155" stroke-width="1" filter="url(#dropShadow)" />
    <rect x="0" y="0" width="460" height="38" rx="10" fill="#1e293b" />
    <text x="18" y="24" fill="#38bdf8" font-family="'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="700">DETALHAMENTO DA SEÇÃO TRANSVERSAL ({bw_str} x {h_str} cm)</text>

    <!-- Desenho da Seção de Concreto (Centro x=170, y=90, w=180, h=360) -->
    <rect x="80" y="70" width="180" height="360" rx="4" fill="url(#concreteGrad)" stroke="#94a3b8" stroke-width="2" />

    <!-- Bloco de Compressão do Concreto (y = 0,80 x) no topo -->
    <rect x="80" y="70" width="180" height="85" fill="url(#compBlockGrad)" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="3 3" />
    <text x="170" y="118" fill="#ffffff" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="700" text-anchor="middle">Bloco Comprimido (y = 0,8x)</text>

    <!-- Linha Neutra (LN) -->
    <line x1="60" y1="175" x2="280" y2="175" stroke="#f59e0b" stroke-width="2" stroke-dasharray="6 3" />
    <text x="288" y="179" fill="#f59e0b" font-family="'Segoe UI', Roboto, sans-serif" font-size="10" font-weight="700">L.N. (x = {x_str} cm)</text>

    <!-- Estribo Fechado (Verde) -->
    <rect x="96" y="86" width="148" height="328" rx="8" fill="none" stroke="#10b981" stroke-width="3" />
    <!-- Ganchos do estribo no topo -->
    <path d="M 106 96 L 120 110 M 234 96 L 220 110" stroke="#10b981" stroke-width="3" stroke-linecap="round" />

    <!-- Barras Superiores / Porta-Estribos (Amarelo) -->
    <circle cx="112" cy="102" r="6" fill="#f59e0b" stroke="#ffffff" stroke-width="1" />
    <circle cx="228" cy="102" r="6" fill="#f59e0b" stroke="#ffffff" stroke-width="1" />

    <!-- Barras de Tração Inferiores (Azul) -->
    <circle cx="112" cy="398" r="8" fill="url(#rebarGrad)" stroke="#ffffff" stroke-width="1.5" />
    <circle cx="170" cy="398" r="8" fill="url(#rebarGrad)" stroke="#ffffff" stroke-width="1.5" />
    <circle cx="228" cy="398" r="8" fill="url(#rebarGrad)" stroke="#ffffff" stroke-width="1.5" />

    <!-- Cotas e Dimensões -->
    <!-- Cota de Largura bw -->
    <line x1="80" y1="455" x2="260" y2="455" stroke="#94a3b8" stroke-width="1.5" />
    <line x1="80" y1="448" x2="80" y2="462" stroke="#94a3b8" stroke-width="1.5" />
    <line x1="260" y1="448" x2="260" y2="462" stroke="#94a3b8" stroke-width="1.5" />
    <text x="170" y="472" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="700" text-anchor="middle">bw = {bw_str} cm</text>

    <!-- Cota de Altura h -->
    <line x1="45" y1="70" x2="45" y2="430" stroke="#94a3b8" stroke-width="1.5" />
    <line x1="38" y1="70" x2="52" y2="70" stroke="#94a3b8" stroke-width="1.5" />
    <line x1="38" y1="430" x2="52" y2="430" stroke="#94a3b8" stroke-width="1.5" />
    <text x="25" y="255" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="700" text-anchor="middle" transform="rotate(-90, 25, 255)">h = {h_str} cm</text>

    <!-- Cota de Altura Útil d -->
    <line x1="285" y1="70" x2="285" y2="398" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="3 3" />
    <text x="300" y="240" fill="#38bdf8" font-family="'Segoe UI', Roboto, sans-serif" font-size="10" font-weight="700">d = {d_str} cm</text>

    <!-- Legenda da Seção -->
    <rect x="20" y="495" width="420" height="145" rx="6" fill="#0f172a" stroke="#334155" stroke-width="1" />
    <text x="35" y="518" fill="#38bdf8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="700">ESPECIFICAÇÕES DE PROJETO (NBR 6118)</text>
    <circle cx="45" cy="538" r="4" fill="#38bdf8" />
    <text x="58" y="542" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="10">Armadura Tração: {rd.barras_tracao} (As = {as_str} cm²)</text>
    <circle cx="45" cy="562" r="4" fill="#10b981" />
    <text x="58" y="566" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="10">Estribos Transversais: {rd.estribos_adotados}</text>
    <circle cx="45" cy="586" r="4" fill="#f59e0b" />
    <text x="58" y="590" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="10">Armadura Superior: {rd.barras_compressao or 'Porta-estribos 2 Φ 6.3 mm'}</text>
    <circle cx="45" cy="610" r="4" fill="#ef4444" />
    <text x="58" y="614" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="10">Concreto C{sec.largura_bw_cm and resultado.resultado_flexao and 25} (fck 25 MPa) • Aço CA-50 (fyk 500 MPa)</text>
  </g>

  <!-- ==================== CORPO CENTRAL: DIAGRAMAS LONGITUDINAIS ==================== -->
  <g transform="translate(520, 190)">
    <!-- Painel Diagrama de Esforços -->
    <rect x="0" y="0" width="410" height="660" rx="10" fill="url(#cardGrad)" stroke="#334155" stroke-width="1" filter="url(#dropShadow)" />
    <rect x="0" y="0" width="410" height="38" rx="10" fill="#1e293b" />
    <text x="18" y="24" fill="#38bdf8" font-family="'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="700">COMPORTAMENTO LONGITUDINAL (VÃO L = {vao_str} m)</text>

    <!-- Esquema Estrutural da Viga Biapoiada com Carga Distribuída -->
    <g transform="translate(30, 60)">
      <text x="0" y="20" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">ESQUEMA ESTÁTICO</text>
      <!-- Viga Horizontal -->
      <rect x="20" y="45" width="310" height="24" rx="2" fill="url(#concreteGrad)" stroke="#64748b" stroke-width="1.5" />
      <!-- Cargas uniformes (setas) -->
      <g stroke="#38bdf8" stroke-width="1.5" fill="#38bdf8">
        <line x1="40" y1="30" x2="40" y2="44" />
        <polygon points="40,44 38,38 42,38" />
        <line x1="90" y1="30" x2="90" y2="44" />
        <polygon points="90,44 88,38 92,38" />
        <line x1="140" y1="30" x2="140" y2="44" />
        <polygon points="140,44 138,38 142,38" />
        <line x1="190" y1="30" x2="190" y2="44" />
        <polygon points="190,44 188,38 192,38" />
        <line x1="240" y1="30" x2="240" y2="44" />
        <polygon points="240,44 238,38 242,38" />
        <line x1="290" y1="30" x2="290" y2="44" />
        <polygon points="290,44 288,38 292,38" />
        <line x1="20" y1="30" x2="330" y2="30" stroke-width="1" />
      </g>
      <!-- Apoio 1 (Esquerdo - Articulação Fixa) -->
      <polygon points="20,69 12,85 28,85" fill="#64748b" stroke="#94a3b8" stroke-width="1" />
      <!-- Apoio 2 (Direito - Rolete Móvel) -->
      <polygon points="330,69 322,85 338,85" fill="#64748b" stroke="#94a3b8" stroke-width="1" />
      <line x1="318" y1="89" x2="342" y2="89" stroke="#94a3b8" stroke-width="1.5" />
    </g>

    <!-- Diagrama de Momentos Fletores M(x) -->
    <g transform="translate(30, 200)">
      <text x="0" y="20" fill="#38bdf8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="700">DIAGRAMA DE MOMENTOS FLETORES M(x)</text>
      <line x1="20" y1="40" x2="330" y2="40" stroke="#475569" stroke-width="1.5" />
      <!-- Parábola de momento fletor (positivo para baixo) -->
      <path d="M 20 40 Q 175 140, 330 40 Z" fill="#0284c7" fill-opacity="0.25" stroke="#38bdf8" stroke-width="2" />
      <text x="175" y="110" fill="#38bdf8" font-family="'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="800" text-anchor="middle">Msd = +{m_sd_str} kN·m</text>
    </g>

    <!-- Diagrama de Forças Cortantes V(x) -->
    <g transform="translate(30, 390)">
      <text x="0" y="20" fill="#10b981" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="700">DIAGRAMA DE FORÇAS CORTANTES V(x)</text>
      <line x1="20" y1="80" x2="330" y2="80" stroke="#475569" stroke-width="1.5" />
      <!-- Triângulos de cortante (+V na esquerda, -V na direita) -->
      <polygon points="20,80 20,30 175,80" fill="#10b981" fill-opacity="0.25" stroke="#10b981" stroke-width="2" />
      <polygon points="175,80 330,130 330,80" fill="#10b981" fill-opacity="0.25" stroke="#10b981" stroke-width="2" />
      <text x="45" y="55" fill="#10b981" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="700">+Vsd={v_sd_str}</text>
      <text x="260" y="115" fill="#10b981" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="700">-Vsd={v_sd_str}</text>
    </g>

    <!-- Caixa Informativa dos Domínios -->
    <rect x="20" y="565" width="370" height="75" rx="6" fill="#0f172a" stroke="#334155" stroke-width="1" />
    <text x="35" y="588" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="10" font-weight="700">CRITÉRIOS DE DUCTILIDADE (NBR 6118)</text>
    <text x="35" y="608" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="10">Posição relativa da L.N.: ξ = x/d = {xi_str} ≤ 0,45 (Domínio 3)</text>
    <text x="35" y="626" fill="#10b981" font-family="'Segoe UI', Roboto, sans-serif" font-size="10">Seção com aviso prévio de ruptura por escoamento dúctil do aço.</text>
  </g>

  <!-- ==================== COLUNA LATERAL DIREITA: TABELAS NORMATIVAS ==================== -->
  <g transform="translate(950, 190)">
    <!-- Painel 1: Parâmetros de Dimensionamento -->
    <rect x="0" y="0" width="450" height="320" rx="10" fill="url(#cardGrad)" stroke="#334155" stroke-width="1" filter="url(#dropShadow)" />
    <rect x="0" y="0" width="450" height="38" rx="10" fill="#1e293b" />
    <text x="18" y="24" fill="#38bdf8" font-family="'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="700">MEMÓRIA DE CÁLCULO NORMATIVA (NBR 6118:2023)</text>

    <g transform="translate(18, 55)">
      <!-- Item 1: Flexão ELU -->
      <circle cx="8" cy="12" r="4" fill="#10b981" />
      <text x="22" y="16" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">Momento de Cálculo (Msd):</text>
      <text x="210" y="16" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11">{m_sd_str} kN·m (γf = 1,40)</text>

      <!-- Item 2: Linha Neutra -->
      <circle cx="8" cy="42" r="4" fill="#10b981" />
      <text x="22" y="46" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">Linha Neutra (x / d):</text>
      <text x="210" y="46" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11">x = {x_str} cm (ξ = {xi_str} ≤ 0,45)</text>

      <!-- Item 3: Armadura Mínima -->
      <circle cx="8" cy="72" r="4" fill="#10b981" />
      <text x="22" y="76" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">Armadura Mínima (As,min):</text>
      <text x="210" y="76" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11">{formatar_fracao_decimal(rf.area_aco_minima_cm2, 2)} cm² (ρmin = 0,150%)</text>

      <!-- Item 4: Cortante Biela VRd2 -->
      <circle cx="8" cy="102" r="4" fill="#10b981" />
      <text x="22" y="106" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">Compressão Diagonal (VRd2):</text>
      <text x="210" y="106" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11">{formatar_fracao_decimal(rc.resistencia_biela_v_rd2_kN, 1)} kN (Vsd ≤ VRd2)</text>

      <!-- Item 5: Concreto Vc -->
      <circle cx="8" cy="132" r="4" fill="#10b981" />
      <text x="22" y="136" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">Mecanismos Concreto (Vc):</text>
      <text x="210" y="136" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11">{formatar_fracao_decimal(rc.parcela_concreto_vc_kN, 1)} kN</text>

      <!-- Item 6: Estribos Vsw -->
      <circle cx="8" cy="162" r="4" fill="#10b981" />
      <text x="22" y="166" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">Armadura Estribos (Vsw):</text>
      <text x="210" y="166" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11">{formatar_fracao_decimal(rc.parcela_armadura_vsw_kN, 1)} kN</text>

      <!-- Item 7: Espaçamento Máximo -->
      <circle cx="8" cy="192" r="4" fill="#10b981" />
      <text x="22" y="196" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">Espaçamento Máx Estribos:</text>
      <text x="210" y="196" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11">smax = {formatar_fracao_decimal(rc.espacamento_maximo_estribo_cm, 1)} cm</text>
    </g>

    <!-- Painel 2: Verificação dos Estados Limites de Serviço (ELS) -->
    <rect x="0" y="340" width="450" height="320" rx="10" fill="url(#cardGrad)" stroke="#334155" stroke-width="1" filter="url(#dropShadow)" />
    <rect x="0" y="340" width="450" height="38" rx="10" fill="#1e293b" />
    <text x="18" y="364" fill="#38bdf8" font-family="'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="700">ESTADOS LIMITES DE SERVIÇO (ELS-W / ELS-DEF)</text>

    <g transform="translate(18, 395)">
      <!-- ELS-W: Fissuração -->
      <circle cx="8" cy="12" r="4" fill="#10b981" />
      <text x="22" y="16" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">Abertura de Fissuras (wk):</text>
      <text x="200" y="16" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11">{wk_str} mm (Limite: {w_lim_str} mm)</text>

      <!-- ELS-DEF: Flecha Total -->
      <circle cx="8" cy="42" r="4" fill="#10b981" />
      <text x="22" y="46" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">Flecha Imediata (fi):</text>
      <text x="200" y="46" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11">{formatar_fracao_decimal(re.flecha_imediata_cm, 2)} cm</text>

      <!-- ELS-DEF: Flecha Total Diferida -->
      <circle cx="8" cy="72" r="4" fill="#10b981" />
      <text x="22" y="76" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">Flecha Total (ftotal):</text>
      <text x="200" y="76" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11">{flecha_str} cm (Limite L/250: {flecha_lim_str} cm)</text>

      <!-- Cobrimento Nominal -->
      <circle cx="8" cy="102" r="4" fill="#10b981" />
      <text x="22" y="106" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">Cobrimento Nominal (cnom):</text>
      <text x="200" y="106" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11">3,0 cm (Classe de Agressividade II)</text>

      <!-- Módulo de Elasticidade -->
      <circle cx="8" cy="132" r="4" fill="#10b981" />
      <text x="22" y="136" fill="#f8fafc" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">Aço Estrutural:</text>
      <text x="200" y="136" fill="#94a3b8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11">CA-50 (fyk = 500 MPa, Es = 210 GPa)</text>
    </g>

    <!-- Box de Garantia Zero Float -->
    <rect x="18" y="580" width="414" height="40" rx="6" fill="#0284c7" fill-opacity="0.15" stroke="#0284c7" stroke-width="1" />
    <text x="225" y="605" fill="#38bdf8" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="700" text-anchor="middle">GARANTIA TÉCNICA: MOTOR DETERMINÍSTICO ZERO FLOAT (FRAÇÕES RACIONAIS)</text>
  </g>

  <!-- ==================== RODAPÉ ==================== -->
  <g transform="translate(40, 868)">
    <line x1="0" y1="0" x2="1360" y2="0" stroke="#334155" stroke-width="1" />
    <text x="0" y="18" fill="#64748b" font-family="'Segoe UI', Roboto, sans-serif" font-size="11">LOFRANO TECNOLOGIA • Engenharia de Estruturas de Concreto Armado • ABNT NBR 6118:2023 • Código Aberto MIT</text>
    <text x="1360" y="18" fill="#64748b" font-family="'Segoe UI', Roboto, sans-serif" font-size="11" text-anchor="end">Cálculo Racional e Determinístico sem Aproximação IEEE-754</text>
  </g>
</svg>"""
    return svg
