"""Testes unitários para o motor analítico de cálculo estrutural da NBR 6118."""
from fractions import Fraction
import unittest

from vigas_concreto_nbr6118.calculator import (
    raiz_quadrada_fracao,
    obter_cobrimento_nominal,
    dimensionar_flexao_elu,
    dimensionar_cisalhamento_elu,
    selecionar_detalhamento_armaduras,
    verificar_els,
    dimensionar_viga_concreto,
)
from vigas_concreto_nbr6118.models import (
    SecaoViga,
    PropriedadesMateriais,
    EsforcosSolicitantes,
    PreferenciasDetalhamento,
    ProjetoViga,
)


class TestCalculator(unittest.TestCase):
    """Testes exatos do motor de cálculo da ABNT NBR 6118:2023."""

    def test_raiz_quadrada_fracao_exata(self) -> None:
        """Testa raízes racionais exatas."""
        self.assertEqual(raiz_quadrada_fracao(Fraction(0, 1)), Fraction(0, 1))
        self.assertEqual(raiz_quadrada_fracao(Fraction(4, 1)), Fraction(2, 1))
        self.assertEqual(raiz_quadrada_fracao(Fraction(9, 1)), Fraction(3, 1))
        self.assertEqual(raiz_quadrada_fracao(Fraction(25, 4)), Fraction(5, 2))
        self.assertEqual(raiz_quadrada_fracao(Fraction(144, 25)), Fraction(12, 5))

    def test_raiz_quadrada_fracao_aproximada(self) -> None:
        """Testa aproximação racional de raiz quadrada para frações não quadradas perfeitas."""
        r2 = raiz_quadrada_fracao(Fraction(2, 1), precisao=8)
        # 1.41421356...
        val = float(r2)
        self.assertAlmostEqual(val, 1.41421356, places=6)
        # Erro ao quadrado
        diff = abs(r2 * r2 - Fraction(2, 1))
        self.assertLess(diff, Fraction(1, 1000000))

    def test_obter_cobrimento_nominal(self) -> None:
        """Verifica obtenção do cobrimento nominal conforme classe de agressividade."""
        mat_i = PropriedadesMateriais(classe_agressividade="CAA_I")
        self.assertEqual(obter_cobrimento_nominal(mat_i), Fraction(25, 10))

        mat_ii = PropriedadesMateriais(classe_agressividade="CAA_II")
        self.assertEqual(obter_cobrimento_nominal(mat_ii), Fraction(30, 10))

        mat_iii = PropriedadesMateriais(classe_agressividade="CAA_III")
        self.assertEqual(obter_cobrimento_nominal(mat_iii), Fraction(40, 10))

        mat_iv = PropriedadesMateriais(classe_agressividade="CAA_IV")
        self.assertEqual(obter_cobrimento_nominal(mat_iv), Fraction(50, 10))

        # Sobrescrita manual
        mat_manual = PropriedadesMateriais(cobrimento_nominal_cm=Fraction(35, 10))
        self.assertEqual(obter_cobrimento_nominal(mat_manual), Fraction(35, 10))

    def test_dimensionar_flexao_armadura_simples(self) -> None:
        """Dimensionamento à flexão simples no Domínio 2 ou 3 com armadura simples."""
        secao = SecaoViga(largura_bw_cm=Fraction(20), altura_h_cm=Fraction(45), comprimento_vao_m=Fraction(5))
        materiais = PropriedadesMateriais(classe_concreto_fck=25, classe_agressividade="CAA_II")
        esforcos = EsforcosSolicitantes(momento_fletor_k_kNm=Fraction(48), forca_cortante_k_kN=Fraction(38))
        pref = PreferenciasDetalhamento(d_linha_estimado_cm=Fraction(4))

        res = dimensionar_flexao_elu(secao, materiais, esforcos, pref)
        self.assertEqual(res.tipo_armadura, "simples")
        self.assertTrue(res.atende_ductilidade)
        self.assertTrue(res.atende_taxa_maxima)
        self.assertLessEqual(res.relacao_x_d, Fraction(45, 100))
        self.assertGreater(res.area_aco_tracao_calculada_cm2, 0)
        self.assertEqual(res.area_aco_compressao_calculada_cm2, Fraction(0, 1))

    def test_dimensionar_flexao_armadura_dupla(self) -> None:
        """Dimensionamento com momento elevado exigindo armadura dupla para garantir ductilidade (xi=0.45)."""
        secao = SecaoViga(largura_bw_cm=Fraction(20), altura_h_cm=Fraction(40), comprimento_vao_m=Fraction(3))
        materiais = PropriedadesMateriais(classe_concreto_fck=20, classe_agressividade="CAA_II")
        esforcos = EsforcosSolicitantes(momento_fletor_k_kNm=Fraction(150), forca_cortante_k_kN=Fraction(50))
        pref = PreferenciasDetalhamento(d_linha_estimado_cm=Fraction(4))

        res = dimensionar_flexao_elu(secao, materiais, esforcos, pref)
        self.assertEqual(res.tipo_armadura, "dupla")
        self.assertEqual(res.relacao_x_d, Fraction(45, 100))
        self.assertGreater(res.area_aco_compressao_calculada_cm2, 0)
        self.assertGreater(res.area_aco_tracao_final_cm2, res.area_aco_minima_cm2)

    def test_dimensionar_flexao_armadura_minima(self) -> None:
        """Momento pequeno onde a armadura mínima da Tabela 17.3 governa o dimensionamento."""
        secao = SecaoViga(largura_bw_cm=Fraction(20), altura_h_cm=Fraction(50), comprimento_vao_m=Fraction(5))
        materiais = PropriedadesMateriais(classe_concreto_fck=25, classe_agressividade="CAA_II")
        esforcos = EsforcosSolicitantes(momento_fletor_k_kNm=Fraction(5), forca_cortante_k_kN=Fraction(10))
        pref = PreferenciasDetalhamento(d_linha_estimado_cm=Fraction(4))

        res = dimensionar_flexao_elu(secao, materiais, esforcos, pref)
        self.assertEqual(res.tipo_armadura, "simples")
        self.assertGreater(res.area_aco_minima_cm2, res.area_aco_tracao_calculada_cm2)
        self.assertEqual(res.area_aco_tracao_final_cm2, res.area_aco_minima_cm2)

    def test_cisalhamento_modelo_i(self) -> None:
        """Dimensionamento ao esforço cortante sob Modelo de Cálculo I."""
        secao = SecaoViga(largura_bw_cm=Fraction(20), altura_h_cm=Fraction(45), comprimento_vao_m=Fraction(5))
        materiais = PropriedadesMateriais(classe_concreto_fck=25, classe_agressividade="CAA_II")
        esforcos = EsforcosSolicitantes(momento_fletor_k_kNm=Fraction(50), forca_cortante_k_kN=Fraction(40))
        pref = PreferenciasDetalhamento(d_linha_estimado_cm=Fraction(4))

        res_flexao = dimensionar_flexao_elu(secao, materiais, esforcos, pref)
        res_cis = dimensionar_cisalhamento_elu(secao, materiais, esforcos, pref)

        self.assertTrue(res_cis.atende_biela_compressao)
        self.assertTrue(res_cis.atende_cisalhamento)
        self.assertGreater(res_cis.resistencia_biela_v_rd2_kN, res_cis.forca_cortante_sd_kN)
        self.assertGreater(res_cis.area_estribos_por_metro_final_cm2_m, 0)
        self.assertGreater(res_cis.espacamento_maximo_estribo_cm, 0)

    def test_cisalhamento_esmagamento_biela(self) -> None:
        """Força cortante absurdamente elevada que esmaga a biela comprimida (Vsd > VRd2)."""
        secao = SecaoViga(largura_bw_cm=Fraction(15), altura_h_cm=Fraction(30), comprimento_vao_m=Fraction(4))
        materiais = PropriedadesMateriais(classe_concreto_fck=20, classe_agressividade="CAA_I")
        esforcos = EsforcosSolicitantes(momento_fletor_k_kNm=Fraction(20), forca_cortante_k_kN=Fraction(400))
        pref = PreferenciasDetalhamento(d_linha_estimado_cm=Fraction(4))

        res_flexao = dimensionar_flexao_elu(secao, materiais, esforcos, pref)
        res_cis = dimensionar_cisalhamento_elu(secao, materiais, esforcos, pref)

        self.assertFalse(res_cis.atende_biela_compressao)
        self.assertFalse(res_cis.atende_cisalhamento)
        self.assertGreater(res_cis.taxa_trabalho_biela, Fraction(1, 1))

    def test_detalhamento_armaduras(self) -> None:
        """Detalhamento comercial de barras de tração e estribos."""
        secao = SecaoViga(largura_bw_cm=Fraction(20), altura_h_cm=Fraction(45), comprimento_vao_m=Fraction(5))
        materiais = PropriedadesMateriais(classe_concreto_fck=25, classe_agressividade="CAA_II")
        esforcos = EsforcosSolicitantes(momento_fletor_k_kNm=Fraction(48), forca_cortante_k_kN=Fraction(38))
        pref = PreferenciasDetalhamento(bitola_longitudinal_sugerida_mm=Fraction(125, 10), bitola_estribo_sugerida_mm=Fraction(63, 10))

        res_flex = dimensionar_flexao_elu(secao, materiais, esforcos, pref)
        res_cis = dimensionar_cisalhamento_elu(secao, materiais, esforcos, pref)
        det = selecionar_detalhamento_armaduras(secao, materiais, res_flex, res_cis, pref)

        self.assertGreaterEqual(det.area_tracao_efetiva_cm2, res_flex.area_aco_tracao_final_cm2)
        self.assertGreaterEqual(det.area_estribo_efetiva_cm2_m, res_cis.area_estribos_por_metro_final_cm2_m)
        self.assertEqual(det.bitola_tracao_mm, Fraction(125, 10))
        self.assertEqual(det.bitola_estribo_mm, Fraction(63, 10))

    def test_verificar_els_completo(self) -> None:
        """Verificação dos Estados Limites de Serviço (Fissuração wk e Flecha total L/250)."""
        secao = SecaoViga(largura_bw_cm=Fraction(20), altura_h_cm=Fraction(45), comprimento_vao_m=Fraction(5))
        materiais = PropriedadesMateriais(classe_concreto_fck=25, classe_agressividade="CAA_II")
        esforcos = EsforcosSolicitantes(momento_fletor_k_kNm=Fraction(48), forca_cortante_k_kN=Fraction(38))
        pref = PreferenciasDetalhamento()

        res_flex = dimensionar_flexao_elu(secao, materiais, esforcos, pref)
        res_cis = dimensionar_cisalhamento_elu(secao, materiais, esforcos, pref)
        det = selecionar_detalhamento_armaduras(secao, materiais, res_flex, res_cis, pref)
        res_els = verificar_els(secao, materiais, esforcos, res_flex, det)

        self.assertTrue(res_els.atende_fissuracao)
        self.assertTrue(res_els.atende_deformacao)
        self.assertLessEqual(res_els.abertura_fissura_estimada_wk_mm, res_els.limite_fissura_w_lim_mm)
        self.assertLessEqual(res_els.flecha_total_diferida_cm, res_els.flecha_limite_cm)

    def test_pipeline_completo_projeto_viga(self) -> None:
        """Execução ponta-a-ponta de dimensionamento de viga."""
        proj = ProjetoViga(
            identificacao="Viga V101",
            secao=SecaoViga(largura_bw_cm=Fraction(20), altura_h_cm=Fraction(45), comprimento_vao_m=Fraction(5)),
            materiais=PropriedadesMateriais(classe_concreto_fck=25, classe_agressividade="CAA_II"),
            esforcos=EsforcosSolicitantes(momento_fletor_k_kNm=Fraction(48), forca_cortante_k_kN=Fraction(38)),
        )
        res = dimensionar_viga_concreto(proj)
        self.assertTrue(res.atende_geral)
        self.assertTrue(res.conformidades["flexao_elu"])
        self.assertTrue(res.conformidades["cisalhamento_elu"])
        self.assertTrue(res.conformidades["fissuracao_els"])
        self.assertTrue(res.conformidades["deformacao_els"])

    def test_todas_classes_concreto_flexao(self) -> None:
        """Verifica que o dimensionamento à flexão suporta todas as classes C20 a C50."""
        for fck in (20, 25, 30, 35, 40, 45, 50):
            proj = ProjetoViga(
                identificacao=f"Viga C{fck}",
                secao=SecaoViga(largura_bw_cm=Fraction(20), altura_h_cm=Fraction(50), comprimento_vao_m=Fraction(5)),
                materiais=PropriedadesMateriais(classe_concreto_fck=fck, classe_agressividade="CAA_II"),
                esforcos=EsforcosSolicitantes(momento_fletor_k_kNm=Fraction(60), forca_cortante_k_kN=Fraction(40)),
            )
            res = dimensionar_viga_concreto(proj)
            self.assertGreater(res.resultado_flexao.area_aco_tracao_final_cm2, 0)
            self.assertTrue(res.resultado_flexao.atende_ductilidade)

    def test_viga_transicao_armadura_dupla_aprovada(self) -> None:
        """Verifica viga com armadura dupla e total conformidade aos estados limites."""
        proj = ProjetoViga(
            identificacao="Viga Transição VT02",
            secao=SecaoViga(largura_bw_cm=Fraction(25), altura_h_cm=Fraction(45), comprimento_vao_m=Fraction(24, 10)),
            materiais=PropriedadesMateriais(classe_concreto_fck=25, classe_agressividade="CAA_II"),
            esforcos=EsforcosSolicitantes(momento_fletor_k_kNm=Fraction(180), forca_cortante_k_kN=Fraction(110)),
        )
        res = dimensionar_viga_concreto(proj)
        self.assertTrue(res.atende_geral)
        self.assertEqual(res.resultado_flexao.tipo_armadura, "dupla")
        self.assertGreater(res.resultado_flexao.area_aco_compressao_calculada_cm2, 0)
        self.assertTrue(res.conformidades["deformacao_els"])

    def test_secao_esbelta_reprovada_flecha(self) -> None:
        """Verifica que viga com esbeltez excessiva é reprovada no ELS de deformação."""
        proj = ProjetoViga(
            identificacao="Viga Esbelta",
            secao=SecaoViga(largura_bw_cm=Fraction(15), altura_h_cm=Fraction(30), comprimento_vao_m=Fraction(7)),
            materiais=PropriedadesMateriais(classe_concreto_fck=20, classe_agressividade="CAA_I"),
            esforcos=EsforcosSolicitantes(momento_fletor_k_kNm=Fraction(40), forca_cortante_k_kN=Fraction(25)),
        )
        res = dimensionar_viga_concreto(proj)
        self.assertFalse(res.atende_geral)
        self.assertFalse(res.conformidades["deformacao_els"])
        self.assertIn("Flecha total diferida superior ao limite normativo L/250.", res.alertas)

    def test_taxa_armadura_transversal_minima_nbr6118(self) -> None:
        """Quando Vsd <= Vc, estribos são governados pela armadura transversal mínima."""
        secao = SecaoViga(largura_bw_cm=Fraction(20), altura_h_cm=Fraction(45), comprimento_vao_m=Fraction(5))
        materiais = PropriedadesMateriais(classe_concreto_fck=25, classe_agressividade="CAA_II")
        esforcos = EsforcosSolicitantes(momento_fletor_k_kNm=Fraction(30), forca_cortante_k_kN=Fraction(15))
        pref = PreferenciasDetalhamento()

        res_cis = dimensionar_cisalhamento_elu(secao, materiais, esforcos, pref)
        self.assertEqual(res_cis.parcela_armadura_vsw_kN, Fraction(0, 1))
        self.assertEqual(res_cis.area_estribos_por_metro_final_cm2_m, res_cis.area_estribos_por_metro_minima_cm2_m)

    def test_verificacao_redistribuicao_ductilidade(self) -> None:
        """Garante que a linha neutra na armadura dupla respeita xi = 0.45."""
        secao = SecaoViga(largura_bw_cm=Fraction(20), altura_h_cm=Fraction(40), comprimento_vao_m=Fraction(3))
        materiais = PropriedadesMateriais(classe_concreto_fck=20, classe_agressividade="CAA_II")
        esforcos = EsforcosSolicitantes(momento_fletor_k_kNm=Fraction(160), forca_cortante_k_kN=Fraction(50))
        pref = PreferenciasDetalhamento(d_linha_estimado_cm=Fraction(4))

        res_flex = dimensionar_flexao_elu(secao, materiais, esforcos, pref)
        self.assertEqual(res_flex.relacao_x_d, Fraction(45, 100))
        self.assertEqual(res_flex.posicao_linha_neutra_x_cm, Fraction(45, 100) * res_flex.altura_util_d_cm)


if __name__ == "__main__":
    unittest.main()
