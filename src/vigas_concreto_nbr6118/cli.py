from __future__ import annotations

import argparse
import sys
from fractions import Fraction
from typing import Optional, List

from vigas_concreto_nbr6118 import __version__
from vigas_concreto_nbr6118.constants import (
    TABELA_CAA_NBR6118,
    TABELA_CONCRETOS_NBR6118,
    TABELA_ACOS_NBR6118,
    TABELA_BITOLAS_COMERCIAIS,
)
from vigas_concreto_nbr6118.models import (
    SecaoViga,
    PropriedadesMateriais,
    EsforcosSolicitantes,
    PreferenciasDetalhamento,
    ProjetoViga,
)
from vigas_concreto_nbr6118.calculator import dimensionar_viga_concreto
from vigas_concreto_nbr6118.codecs import (
    carregar_json_canonico,
    salvar_json_canonico,
    deserializar_projeto,
)
from vigas_concreto_nbr6118.exporters import (
    exportar_csv,
    gerar_relatorio_memorial,
    formatar_fracao_decimal,
)
from vigas_concreto_nbr6118.svg_generator import gerar_painel_svg


def parse_fracao_cli(texto: str) -> Fraction:
    """Converte string recebida na linha de comando em Fraction sem admitir float."""
    t = texto.strip().replace(",", ".")
    if "/" in t:
        partes = t.split("/")
        if len(partes) == 2:
            return Fraction(int(partes[0].strip()), int(partes[1].strip()))
    if "." in t:
        partes = t.split(".")
        if len(partes) == 2:
            num = int(partes[0] + partes[1])
            den = 10 ** len(partes[1])
            return Fraction(num, den)
    return Fraction(int(t), 1)


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vigas-concreto",
        description="Dimensionamento e verificação de vigas de concreto armado segundo a ABNT NBR 6118:2023. LOFRANO TECNOLOGIA.",
    )
    subparsers = parser.add_subparsers(dest="comando", help="Comandos disponíveis")

    # Comando: dimensionar
    p_dim = subparsers.add_parser("dimensionar", help="Dimensiona viga de concreto aos estados limites ELU e ELS")
    p_dim.add_argument("--arquivo", "-a", type=str, help="Caminho do arquivo JSON de projeto")
    p_dim.add_argument("--bw", type=str, default="20", help="Largura da viga bw em cm (padrão: 20 cm)")
    p_dim.add_argument("--h", type=str, default="50", help="Altura total da viga h em cm (padrão: 50 cm)")
    p_dim.add_argument("--vao", type=str, default="5.0", help="Vão teórico livre L em metros (padrão: 5.0 m)")
    p_dim.add_argument("--mk", type=str, help="Momento fletor característico Mk em kN·m (ex: 60)")
    p_dim.add_argument("--vk", type=str, help="Força cortante característica Vk em kN (ex: 45)")
    p_dim.add_argument("--fck", type=int, default=25, choices=[20, 25, 30, 35, 40, 45, 50], help="Resistência característica do concreto em MPa (padrão: 25)")
    p_dim.add_argument("--caa", type=str, default="CAA_II", choices=["CAA_I", "CAA_II", "CAA_III", "CAA_IV"], help="Classe de Agressividade Ambiental (padrão: CAA_II)")

    # Saídas
    p_dim.add_argument("--saida-json", "-j", type=str, help="Caminho para salvar resultado consolidado em JSON")
    p_dim.add_argument("--saida-csv", "-c", type=str, help="Caminho para salvar planilha estruturada em CSV")
    p_dim.add_argument("--saida-relatorio", "-r", type=str, help="Caminho para salvar memorial descritivo em TXT")
    p_dim.add_argument("--painel-svg", "-s", type=str, help="Caminho para gerar e salvar painel técnico em SVG")

    # Comando: tabelas
    subparsers.add_parser("tabelas", help="Exibe as tabelas normativas de durabilidade e taxas mínimas da NBR 6118")

    # Comando: materiais
    subparsers.add_parser("materiais", help="Lista as classes de concreto, aços e bitolas comerciais cadastrados")

    # Comando: versao
    subparsers.add_parser("versao", help="Exibe a versão do pacote")

    return parser


def comando_tabelas() -> int:
    print("=" * 80)
    print("TABELA 6.1 & 7.2 — CLASSES DE AGRESSIVIDADE AMBIENTAL (ABNT NBR 6118:2023)")
    print("=" * 80)
    print(f"{'Classe':<10} | {'Agressividade':<28} | {'Cobrimento Vigas':<18} | {'w_lim (Fissura)'}")
    print("-" * 80)
    for chave, d in sorted(TABELA_CAA_NBR6118.items()):
        c_mm = d["cobrimento_nominal_mm"]
        w_mm = formatar_fracao_decimal(d["w_limite_mm"], 2)
        print(f"{chave:<10} | {d['nome']:<28} | {c_mm} mm ({c_mm/10:.1f} cm)     | {w_mm} mm")
    print("=" * 80)

    print("\nTABELA 17.3 — TAXA MÍNIMA DE ARMADURA DE FLEXÃO PARA VIGAS (rho_min)")
    print("-" * 60)
    print(f"{'Classe de Concreto':<20} | {'fck (MPa)':<12} | {'rho_min (%)':<15}")
    print("-" * 60)
    for fck, d in sorted(TABELA_CONCRETOS_NBR6118.items()):
        rho_pct = formatar_fracao_decimal(d["rho_min"] * 100, 3)
        print(f"{d['nome']:<20} | {fck:<12} | {rho_pct}%")
    print("=" * 60)
    return 0


def comando_materiais() -> int:
    print("=" * 80)
    print("CATÁLOGO DE MATERIAIS ESTRUTURAIS E BITOLAS COMERCIAIS (ABNT NBR 6118)")
    print("=" * 80)
    print("\n1. AÇOS ESTRUTURAIS PARA CONCRETO ARMADO")
    print("-" * 60)
    for chave, d in sorted(TABELA_ACOS_NBR6118.items()):
        fyd_kn = formatar_fracao_decimal(d["fyd_kn_cm2"], 2)
        print(f"{chave:<10} | {d['nome']:<35} | fyd = {fyd_kn} kN/cm²")

    print("\n2. BITOLAS PADRONIZADAS COMERCIAIS")
    print("-" * 60)
    print(f"{'Diâmetro Nominal':<20} | {'Área da Seção (cm²)':<25} | {'Uso Principal'}")
    print("-" * 60)
    for bit_frac, d in sorted(TABELA_BITOLAS_COMERCIAIS.items(), key=lambda x: x[0]):
        diam_str = formatar_fracao_decimal(d["diametro_mm"], 1) + " mm"
        area_str = formatar_fracao_decimal(d["area_cm2"], 3) + " cm²"
        print(f"Φ {diam_str:<18} | {area_str:<25} | {d['uso_principal']}")
    print("=" * 80)
    return 0


def executar_dimensionamento_cli(args: argparse.Namespace) -> int:
    if args.arquivo:
        dados = carregar_json_canonico(args.arquivo)
        projeto = deserializar_projeto(dados)
    elif args.mk and args.vk:
        bw = parse_fracao_cli(args.bw)
        h = parse_fracao_cli(args.h)
        vao = parse_fracao_cli(args.vao)
        mk = parse_fracao_cli(args.mk)
        vk = parse_fracao_cli(args.vk)

        secao = SecaoViga(largura_bw_cm=bw, altura_h_cm=h, comprimento_vao_m=vao)
        materiais = PropriedadesMateriais(
            classe_concreto_fck=args.fck,
            classe_agressividade=args.caa,
        )
        esforcos = EsforcosSolicitantes(momento_fletor_k_kNm=mk, forca_cortante_k_kN=vk)
        projeto = ProjetoViga(
            identificacao=f"Viga {float(bw):.0f}x{float(h):.0f} cm - L={float(vao):.1f}m",
            secao=secao,
            materiais=materiais,
            esforcos=esforcos,
        )
    else:
        print("Erro: Forneça um arquivo JSON (--arquivo) ou informe os esforços (--mk e --vk).")
        return 1

    resultado = dimensionar_viga_concreto(projeto)

    relatorio = gerar_relatorio_memorial(resultado)
    if args.saida_relatorio:
        with open(args.saida_relatorio, "w", encoding="utf-8") as f:
            f.write(relatorio)
        print(f"Memorial descritivo salvo em: {args.saida_relatorio}")
    else:
        print(relatorio)

    if args.saida_json:
        salvar_json_canonico(args.saida_json, resultado)
        print(f"Resultado JSON canônico salvo em: {args.saida_json}")

    if args.saida_csv:
        csv_texto = exportar_csv(resultado)
        with open(args.saida_csv, "w", encoding="utf-8") as f:
            f.write(csv_texto)
        print(f"Planilha CSV salva em: {args.saida_csv}")

    if args.painel_svg:
        svg_conteudo = gerar_painel_svg(resultado)
        with open(args.painel_svg, "w", encoding="utf-8") as f:
            f.write(svg_conteudo)
        print(f"Painel técnico SVG salvo em: {args.painel_svg}")

    return 0 if resultado.atende_geral else 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = criar_parser()
    args = parser.parse_args(argv)

    if args.comando == "tabelas":
        return comando_tabelas()
    elif args.comando == "materiais":
        return comando_materiais()
    elif args.comando == "versao":
        print(f"vigas-concreto v{__version__} — ABNT NBR 6118:2023 (LOFRANO TECNOLOGIA)")
        return 0
    elif args.comando == "dimensionar":
        return executar_dimensionamento_cli(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
