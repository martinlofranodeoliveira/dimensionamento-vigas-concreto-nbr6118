"""Testes unitários para exportação de dados (CSV seguro e Memorial Descritivo)."""
from fractions import Fraction
import csv
import io
import unittest

from vigas_concreto_nbr6118.calculator import dimensionar_viga_concreto
from vigas_concreto_nbr6118.exporters import (
    sanitizar_campo_csv,
    formatar_fracao_decimal,
    exportar_csv,
    gerar_relatorio_memorial,
)
from vigas_concreto_nbr6118.models import (
    SecaoViga,
    PropriedadesMateriais,
    EsforcosSolicitantes,
    ProjetoViga,
)


class TestExporters(unittest.TestCase):
    """Testes de formatação, sanitização e exportação de resultados."""

    def test_sanitizar_campo_csv(self) -> None:
        """Garante que caracteres perigosos de fórmula recebam apóstrofo como prefixo."""
        self.assertEqual(sanitizar_campo_csv("=SOMA(A1:A10)"), "'=SOMA(A1:A10)")
        self.assertEqual(sanitizar_campo_csv("+12345"), "'+12345")
        self.assertEqual(sanitizar_campo_csv("-500"), "'-500")
        self.assertEqual(sanitizar_campo_csv("@CMD"), "'@CMD")
        self.assertEqual(sanitizar_campo_csv("\ttab"), "'\ttab")
        self.assertEqual(sanitizar_campo_csv("\rretorno"), "'\rretorno")
        # Texto normal sem prefixo perigoso
        self.assertEqual(sanitizar_campo_csv("Viga V101"), "Viga V101")
        self.assertEqual(sanitizar_campo_csv("CONFORME"), "CONFORME")

    def test_formatar_fracao_decimal(self) -> None:
        """Garante formatação em padrão pt-BR com vírgula."""
        self.assertEqual(formatar_fracao_decimal(Fraction(25, 1)), "25")
        self.assertEqual(formatar_fracao_decimal(Fraction(1, 2)), "0,50")
        self.assertEqual(formatar_fracao_decimal(Fraction(3, 4), casas=2), "0,75")
        self.assertEqual(formatar_fracao_decimal(Fraction(1, 8), casas=3), "0,125")
        self.assertEqual(formatar_fracao_decimal(Fraction(-7, 2)), "-3,50")

    def test_exportar_csv_integridade(self) -> None:
        """Valida que o CSV gerado possui estrutura de colunas e dados consistentes."""
        proj = ProjetoViga(
            identificacao="Viga Teste CSV",
            secao=SecaoViga(largura_bw_cm=Fraction(20), altura_h_cm=Fraction(45), comprimento_vao_m=Fraction(5)),
            materiais=PropriedadesMateriais(classe_concreto_fck=25, classe_agressividade="CAA_II"),
            esforcos=EsforcosSolicitantes(momento_fletor_k_kNm=Fraction(45), forca_cortante_k_kN=Fraction(35)),
        )
        res = dimensionar_viga_concreto(proj)
        csv_texto = exportar_csv(res)

        leitor = csv.reader(io.StringIO(csv_texto), delimiter=";")
        linhas = list(leitor)
        self.assertGreater(len(linhas), 10)

        cabecalho = linhas[0]
        self.assertIn("Categoria", cabecalho)
        self.assertIn("Parâmetro", cabecalho)
        self.assertIn("Valor Calculado / Adotado", cabecalho)
        self.assertIn("Referência Normativa", cabecalho)

        # Não deve haver fórmulas sem prefixo
        for row in linhas:
            for col in row:
                if col.startswith(("=", "@", "+")):
                    self.fail(f"Campo CSV não sanitizado detectado: {col}")

    def test_gerar_relatorio_memorial(self) -> None:
        """Valida a geração do memorial descritivo completo em pt-BR."""
        proj = ProjetoViga(
            identificacao="Viga Teste Memorial",
            secao=SecaoViga(largura_bw_cm=Fraction(20), altura_h_cm=Fraction(45), comprimento_vao_m=Fraction(5)),
            materiais=PropriedadesMateriais(classe_concreto_fck=25, classe_agressividade="CAA_II"),
            esforcos=EsforcosSolicitantes(momento_fletor_k_kNm=Fraction(45), forca_cortante_k_kN=Fraction(35)),
        )
        res = dimensionar_viga_concreto(proj)
        memorial = gerar_relatorio_memorial(res)

        self.assertIn("LOFRANO TECNOLOGIA", memorial)
        self.assertIn("ABNT NBR 6118:2023", memorial)
        self.assertIn("1. CARACTERÍSTICAS GEOMÉTRICAS", memorial)
        self.assertIn("2. DIMENSIONAMENTO À FLEXÃO SIMPLES", memorial)
        self.assertIn("3. DIMENSIONAMENTO AO CISALHAMENTO", memorial)
        self.assertIn("4. DETALHAMENTO DAS ARMADURAS", memorial)
        self.assertIn("5. VERIFICAÇÃO DOS ESTADOS LIMITES DE SERVIÇO", memorial)
        self.assertIn("6. SÍNTESE DE CONFORMIDADES", memorial)


if __name__ == "__main__":
    unittest.main()
