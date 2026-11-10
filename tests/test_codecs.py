"""Testes unitários para o codec canônico JSON (Zero Float, sem BOM, sem duplicatas)."""
import os
import tempfile
from fractions import Fraction
import unittest

from vigas_concreto_nbr6118.codecs import (
    serializar_fracao,
    deserializar_fracao,
    converter_para_dict,
    carregar_json_canonico,
    salvar_json_canonico,
    deserializar_projeto,
    verificar_profundidade,
)
from vigas_concreto_nbr6118.models import ProjetoViga, SecaoViga


class TestCodecs(unittest.TestCase):
    """Testes de conformidade do codec canônico."""

    def test_serializar_deserializar_fracao(self) -> None:
        """Serialização e desserialização de Fraction."""
        f = Fraction(355, 113)
        d = serializar_fracao(f)
        self.assertEqual(d, {"num": 355, "den": 113})
        recup = deserializar_fracao(d)
        self.assertEqual(recup, f)

    def test_deserializar_fracao_formatos_diversos(self) -> None:
        """Aceita inteiros e strings com barras."""
        self.assertEqual(deserializar_fracao(42), Fraction(42, 1))
        self.assertEqual(deserializar_fracao("7/3"), Fraction(7, 3))
        self.assertEqual(deserializar_fracao("5"), Fraction(5, 1))
        self.assertEqual(deserializar_fracao(Fraction(1, 2)), Fraction(1, 2))

        with self.assertRaises(ValueError):
            deserializar_fracao({"num": "abc", "den": 1})
        with self.assertRaises(ValueError):
            deserializar_fracao([1, 2])

    def test_rejeitar_float_na_serializacao(self) -> None:
        """Garante que floats lancem ValueError ao converter para dict."""
        with self.assertRaises(ValueError):
            converter_para_dict(3.14159)
        with self.assertRaises(ValueError):
            converter_para_dict({"taxa": 0.15})

    def test_rejeitar_float_no_json(self) -> None:
        """Garante que floats no JSON de entrada sejam sumariamente rejeitados."""
        json_invalido = '{"largura": 20.5}'
        with self.assertRaises(ValueError):
            carregar_json_canonico(json_invalido)

    def test_rejeitar_chaves_duplicadas(self) -> None:
        """Garante rejeição de chaves duplicadas no JSON."""
        json_duplicado = '{"a": 1, "a": 2}'
        with self.assertRaises(ValueError):
            carregar_json_canonico(json_duplicado)

    def test_rejeitar_bom(self) -> None:
        """Garante que Byte Order Mark UTF-8 seja rejeitado."""
        json_com_bom = "\ufeff" + '{"a": 1}'
        with self.assertRaises(ValueError):
            carregar_json_canonico(json_com_bom)

        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(b"\xef\xbb\xbf" + b'{"a": 1}')
            temp_path = f.name
        try:
            with self.assertRaises(ValueError):
                carregar_json_canonico(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_limite_profundidade(self) -> None:
        """Garante rejeição de aninhamento excessivo (> 32 níveis)."""
        dados: dict = {}
        curr = dados
        for _ in range(35):
            curr["proximo"] = {}
            curr = curr["proximo"]
        with self.assertRaises(ValueError):
            verificar_profundidade(dados, 1, 32)

    def test_salvar_e_carregar_arquivo_canonico(self) -> None:
        """Ciclo completo de escrita e leitura de arquivo JSON canônico."""
        proj = ProjetoViga(
            identificacao="Viga Teste Codec",
            secao=SecaoViga(largura_bw_cm=Fraction(22), altura_h_cm=Fraction(48), comprimento_vao_m=Fraction(6)),
        )
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
            temp_path = f.name

        try:
            salvar_json_canonico(temp_path, proj)
            lido = carregar_json_canonico(temp_path)
            recup_proj = deserializar_projeto(lido)
            self.assertEqual(recup_proj.identificacao, "Viga Teste Codec")
            self.assertEqual(recup_proj.secao.largura_bw_cm, Fraction(22))
            self.assertEqual(recup_proj.secao.altura_h_cm, Fraction(48))
            self.assertEqual(recup_proj.secao.comprimento_vao_m, Fraction(6))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
