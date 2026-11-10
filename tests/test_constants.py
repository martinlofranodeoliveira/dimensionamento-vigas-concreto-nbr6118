"""Testes unitários para as constantes e tabelas normativas da NBR 6118."""
from fractions import Fraction
import unittest

from vigas_concreto_nbr6118.constants import (
    GAMMA_C,
    GAMMA_S,
    GAMMA_F,
    ALPHA_C,
    LAMBDA_C,
    XI_LIMITE_DUCTILIDADE,
    ES_KN_CM2,
    RHO_MAXIMO_SECAO,
    TABELA_CAA_NBR6118,
    TABELA_CONCRETOS_NBR6118,
    TABELA_ACOS_NBR6118,
    TABELA_BITOLAS_COMERCIAIS,
)


class TestConstants(unittest.TestCase):
    """Validações das constantes e coeficientes da ABNT NBR 6118:2023."""

    def test_coeficientes_ponderacao(self) -> None:
        """Verifica coeficientes de segurança normativos."""
        self.assertEqual(GAMMA_C, Fraction(14, 10))
        self.assertEqual(GAMMA_S, Fraction(115, 100))
        self.assertEqual(GAMMA_F, Fraction(14, 10))
        self.assertEqual(ALPHA_C, Fraction(85, 100))
        self.assertEqual(LAMBDA_C, Fraction(8, 10))
        self.assertEqual(XI_LIMITE_DUCTILIDADE, Fraction(45, 100))
        self.assertEqual(RHO_MAXIMO_SECAO, Fraction(4, 100))

    def test_modulo_elasticidade_aco(self) -> None:
        """Verifica módulo de elasticidade do aço CA-50/60."""
        self.assertEqual(ES_KN_CM2, Fraction(21000, 1))

    def test_tabela_caa(self) -> None:
        """Verifica as 4 classes de agressividade ambiental."""
        self.assertIn("CAA_I", TABELA_CAA_NBR6118)
        self.assertIn("CAA_II", TABELA_CAA_NBR6118)
        self.assertIn("CAA_III", TABELA_CAA_NBR6118)
        self.assertIn("CAA_IV", TABELA_CAA_NBR6118)

        # Cobrimentos nominais mínimos
        self.assertEqual(TABELA_CAA_NBR6118["CAA_I"]["cobrimento_nominal_mm"], 25)
        self.assertEqual(TABELA_CAA_NBR6118["CAA_II"]["cobrimento_nominal_mm"], 30)
        self.assertEqual(TABELA_CAA_NBR6118["CAA_III"]["cobrimento_nominal_mm"], 40)
        self.assertEqual(TABELA_CAA_NBR6118["CAA_IV"]["cobrimento_nominal_mm"], 50)

        # Limites de fissuração w_lim
        self.assertEqual(TABELA_CAA_NBR6118["CAA_I"]["w_limite_mm"], Fraction(4, 10))
        self.assertEqual(TABELA_CAA_NBR6118["CAA_II"]["w_limite_mm"], Fraction(3, 10))
        self.assertEqual(TABELA_CAA_NBR6118["CAA_III"]["w_limite_mm"], Fraction(2, 10))
        self.assertEqual(TABELA_CAA_NBR6118["CAA_IV"]["w_limite_mm"], Fraction(2, 10))

    def test_tabela_concretos(self) -> None:
        """Verifica o grupo I de concretos (C20 a C50)."""
        classes = [20, 25, 30, 35, 40, 45, 50]
        for fck in classes:
            self.assertIn(fck, TABELA_CONCRETOS_NBR6118)
            info = TABELA_CONCRETOS_NBR6118[fck]
            self.assertEqual(info["fck_mpa"], fck)
            self.assertGreater(info["fctm_mpa"], 0)
            self.assertGreater(info["fctk_inf_mpa"], 0)
            self.assertGreater(info["rho_min"], 0)
            self.assertLess(info["rho_min"], Fraction(1, 100))

    def test_tabela_acos(self) -> None:
        """Verifica tipos de aço CA-50 e CA-60."""
        self.assertIn("CA_50", TABELA_ACOS_NBR6118)
        self.assertIn("CA_60", TABELA_ACOS_NBR6118)

        ca50 = TABELA_ACOS_NBR6118["CA_50"]
        self.assertEqual(ca50["fyk_mpa"], 500)
        self.assertEqual(ca50["fyk_kn_cm2"], Fraction(50, 1))
        self.assertEqual(ca50["fyd_kn_cm2"], Fraction(50, 1) / GAMMA_S)

        ca60 = TABELA_ACOS_NBR6118["CA_60"]
        self.assertEqual(ca60["fyk_mpa"], 600)
        self.assertEqual(ca60["fyk_kn_cm2"], Fraction(60, 1))

    def test_tabela_bitolas_comerciais(self) -> None:
        """Verifica bitolas comerciais de 5.0 mm até 32.0 mm."""
        bitolas = [
            Fraction(50, 10),
            Fraction(63, 10),
            Fraction(80, 10),
            Fraction(100, 10),
            Fraction(125, 10),
            Fraction(160, 10),
            Fraction(200, 10),
            Fraction(250, 10),
            Fraction(320, 10),
        ]
        for b in bitolas:
            self.assertIn(b, TABELA_BITOLAS_COMERCIAIS)
            info = TABELA_BITOLAS_COMERCIAIS[b]
            self.assertEqual(info["diametro_mm"], b)
            self.assertGreater(info["area_cm2"], 0)


if __name__ == "__main__":
    unittest.main()
