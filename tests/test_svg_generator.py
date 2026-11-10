"""Testes unitários para o gerador de painel técnico vetorial SVG 1440x900."""
from fractions import Fraction
import unittest

from vigas_concreto_nbr6118.calculator import dimensionar_viga_concreto
from vigas_concreto_nbr6118.models import (
    SecaoViga,
    PropriedadesMateriais,
    EsforcosSolicitantes,
    ProjetoViga,
)
from vigas_concreto_nbr6118.svg_generator import gerar_painel_svg, escapar_xml


class TestSvgGenerator(unittest.TestCase):
    """Testes de conformidade do gerador SVG."""

    def test_escapar_xml(self) -> None:
        """Verifica escape seguro de caracteres XML."""
        self.assertEqual(escapar_xml("Texto <com> & \"aspas\" 'simples'"), "Texto &lt;com&gt; &amp; &quot;aspas&quot; &#x27;simples&#x27;")

    def test_gerar_painel_svg_estrutura(self) -> None:
        """Garante formato correto de cabeçalho, viewport e tags SVG."""
        proj = ProjetoViga(
            identificacao="Viga V-SVG Teste",
            secao=SecaoViga(largura_bw_cm=Fraction(25), altura_h_cm=Fraction(50), comprimento_vao_m=Fraction(6)),
            materiais=PropriedadesMateriais(classe_concreto_fck=30, classe_agressividade="CAA_II"),
            esforcos=EsforcosSolicitantes(momento_fletor_k_kNm=Fraction(80), forca_cortante_k_kN=Fraction(60)),
        )
        res = dimensionar_viga_concreto(proj)
        svg = gerar_painel_svg(res)

        self.assertTrue(svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"'))
        self.assertIn('viewBox="0 0 1440 900"', svg)
        self.assertIn('width="1440"', svg)
        self.assertIn('height="900"', svg)
        self.assertTrue(svg.strip().endswith('</svg>'))

        # Elementos essenciais do painel
        self.assertIn("LOFRANO TECNOLOGIA", svg)
        self.assertIn("ABNT NBR 6118:2023", svg)
        self.assertIn("Viga V-SVG Teste", svg)
        self.assertIn("DETALHAMENTO DA SEÇÃO TRANSVERSAL", svg)
        self.assertIn("COMPORTAMENTO LONGITUDINAL", svg)
        self.assertIn("MEMÓRIA DE CÁLCULO NORMATIVA", svg)
        self.assertIn("ESTADOS LIMITES DE SERVIÇO", svg)


if __name__ == "__main__":
    unittest.main()
