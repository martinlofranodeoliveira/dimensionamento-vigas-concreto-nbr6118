"""Testes unitários para modelos de dados e dataclasses de domínio."""
from fractions import Fraction
import unittest

from vigas_concreto_nbr6118.models import (
    SecaoViga,
    PropriedadesMateriais,
    EsforcosSolicitantes,
    PreferenciasDetalhamento,
    ProjetoViga,
)


class TestModels(unittest.TestCase):
    """Validações de regras de integridade e tipos dos modelos."""

    def test_secao_viga_valida(self) -> None:
        """Criação válida de seção transversal."""
        secao = SecaoViga(
            largura_bw_cm=Fraction(20, 1),
            altura_h_cm=Fraction(50, 1),
            comprimento_vao_m=Fraction(5, 1),
            tipo_apoio="biapoiada",
        )
        self.assertEqual(secao.largura_bw_cm, Fraction(20, 1))
        self.assertEqual(secao.altura_h_cm, Fraction(50, 1))
        self.assertEqual(secao.comprimento_vao_m, Fraction(5, 1))
        self.assertEqual(secao.tipo_apoio, "biapoiada")

    def test_secao_viga_invalidos(self) -> None:
        """Dimensões não positivas devem levantar ValueError."""
        with self.assertRaises(ValueError):
            SecaoViga(largura_bw_cm=Fraction(0), altura_h_cm=Fraction(50), comprimento_vao_m=Fraction(5))
        with self.assertRaises(ValueError):
            SecaoViga(largura_bw_cm=Fraction(-10), altura_h_cm=Fraction(50), comprimento_vao_m=Fraction(5))
        with self.assertRaises(ValueError):
            SecaoViga(largura_bw_cm=Fraction(20), altura_h_cm=Fraction(0), comprimento_vao_m=Fraction(5))
        with self.assertRaises(ValueError):
            SecaoViga(largura_bw_cm=Fraction(20), altura_h_cm=Fraction(50), comprimento_vao_m=Fraction(-1))

    def test_propriedades_materiais_validas(self) -> None:
        """Criação de especificações válidas de materiais."""
        mat = PropriedadesMateriais(classe_concreto_fck=30, classe_agressividade="CAA_III")
        self.assertEqual(mat.classe_concreto_fck, 30)
        self.assertEqual(mat.classe_agressividade, "CAA_III")

    def test_propriedades_materiais_invalidas(self) -> None:
        """Classes fora do escopo Grupo I (C20 a C50) ou CAA inválida."""
        with self.assertRaises(ValueError):
            PropriedadesMateriais(classe_concreto_fck=15)
        with self.assertRaises(ValueError):
            PropriedadesMateriais(classe_concreto_fck=60)
        with self.assertRaises(ValueError):
            PropriedadesMateriais(classe_agressividade="CAA_V")

    def test_esforcos_solicitantes(self) -> None:
        """Validação de esforços característicos."""
        esf = EsforcosSolicitantes(
            momento_fletor_k_kNm=Fraction(100, 1),
            forca_cortante_k_kN=Fraction(50, 1),
        )
        self.assertEqual(esf.momento_fletor_k_kNm, Fraction(100, 1))
        self.assertEqual(esf.forca_cortante_k_kN, Fraction(50, 1))

        with self.assertRaises(ValueError):
            EsforcosSolicitantes(momento_fletor_k_kNm=Fraction(-10), forca_cortante_k_kN=Fraction(50))
        with self.assertRaises(ValueError):
            EsforcosSolicitantes(momento_fletor_k_kNm=Fraction(50), forca_cortante_k_kN=Fraction(-5))

    def test_preferencias_detalhamento(self) -> None:
        """Validação de preferências de detalhamento de armaduras."""
        pref = PreferenciasDetalhamento(
            bitola_longitudinal_sugerida_mm=Fraction(160, 10),
            bitola_estribo_sugerida_mm=Fraction(80, 10),
            numero_ramos_estribo=2,
            d_linha_estimado_cm=Fraction(4, 1),
        )
        self.assertEqual(pref.numero_ramos_estribo, 2)

        with self.assertRaises(ValueError):
            PreferenciasDetalhamento(numero_ramos_estribo=0)
        with self.assertRaises(ValueError):
            PreferenciasDetalhamento(d_linha_estimado_cm=Fraction(-1))

    def test_projeto_viga_completo(self) -> None:
        """Instanciação de um projeto de viga estruturado."""
        proj = ProjetoViga(
            identificacao="Viga Teste Unitário",
            secao=SecaoViga(largura_bw_cm=Fraction(20), altura_h_cm=Fraction(45), comprimento_vao_m=Fraction(4)),
        )
        self.assertEqual(proj.identificacao, "Viga Teste Unitário")
        self.assertEqual(proj.materiais.classe_concreto_fck, 25)
        self.assertEqual(proj.materiais.classe_agressividade, "CAA_II")


if __name__ == "__main__":
    unittest.main()
