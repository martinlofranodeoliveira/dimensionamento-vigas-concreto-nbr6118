"""Testes unitários para a interface de linha de comando (CLI)."""
import os
import tempfile
from fractions import Fraction
import unittest

from vigas_concreto_nbr6118.cli import parse_fracao_cli, main


class TestCLI(unittest.TestCase):
    """Testes dos subcomandos e fluxos da CLI."""

    def test_parse_fracao_cli(self) -> None:
        """Conversão de strings em Fraction sem float."""
        self.assertEqual(parse_fracao_cli("20"), Fraction(20, 1))
        self.assertEqual(parse_fracao_cli("5.0"), Fraction(5, 1))
        self.assertEqual(parse_fracao_cli("4,5"), Fraction(45, 10))
        self.assertEqual(parse_fracao_cli("12/5"), Fraction(12, 5))
        self.assertEqual(parse_fracao_cli("  30  "), Fraction(30, 1))

    def test_cli_versao(self) -> None:
        """Comando versao."""
        codigo = main(["versao"])
        self.assertEqual(codigo, 0)

    def test_cli_tabelas(self) -> None:
        """Comando tabelas normativas."""
        codigo = main(["tabelas"])
        self.assertEqual(codigo, 0)

    def test_cli_materiais(self) -> None:
        """Comando materiais."""
        codigo = main(["materiais"])
        self.assertEqual(codigo, 0)

    def test_cli_sem_subcomando(self) -> None:
        """Execução sem parâmetros deve exibir ajuda e retornar 0."""
        codigo = main([])
        self.assertEqual(codigo, 0)

    def test_cli_dimensionar_arquivo_exemplo(self) -> None:
        """Dimensionamento através de arquivo JSON de exemplo."""
        codigo = main(["dimensionar", "-a", "examples/viga_residencial_biapoiada.json"])
        self.assertEqual(codigo, 0)

    def test_cli_dimensionar_argumentos_diretos(self) -> None:
        """Dimensionamento fornecendo geometria e esforços via linha de comando."""
        codigo = main([
            "dimensionar",
            "--bw", "20",
            "--h", "45",
            "--vao", "5",
            "--mk", "45",
            "--vk", "35",
            "--fck", "25",
            "--caa", "CAA_II",
        ])
        self.assertEqual(codigo, 0)

    def test_cli_dimensionar_sem_esforcos(self) -> None:
        """Sem arquivo e sem esforços deve retornar código 1."""
        codigo = main(["dimensionar"])
        self.assertEqual(codigo, 1)

    def test_cli_dimensionar_gerar_todas_saidas(self) -> None:
        """Verifica a geração de arquivos JSON, CSV, TXT e SVG via CLI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_out = os.path.join(tmpdir, "resultado.json")
            csv_out = os.path.join(tmpdir, "planilha.csv")
            rel_out = os.path.join(tmpdir, "memorial.txt")
            svg_out = os.path.join(tmpdir, "painel.svg")

            codigo = main([
                "dimensionar",
                "-a", "examples/viga_residencial_biapoiada.json",
                "--saida-json", json_out,
                "--saida-csv", csv_out,
                "--saida-relatorio", rel_out,
                "--painel-svg", svg_out,
            ])
            self.assertEqual(codigo, 0)

            self.assertTrue(os.path.exists(json_out))
            self.assertTrue(os.path.exists(csv_out))
            self.assertTrue(os.path.exists(rel_out))
            self.assertTrue(os.path.exists(svg_out))

            self.assertGreater(os.path.getsize(json_out), 100)
            self.assertGreater(os.path.getsize(csv_out), 100)
            self.assertGreater(os.path.getsize(rel_out), 500)
            self.assertGreater(os.path.getsize(svg_out), 1000)


if __name__ == "__main__":
    unittest.main()
