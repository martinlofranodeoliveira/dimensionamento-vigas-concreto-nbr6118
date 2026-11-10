"""Testes unitários para empacotamento, metadados e tipagem PEP 561."""
import os
import unittest

import vigas_concreto_nbr6118


class TestPackaging(unittest.TestCase):
    """Validações de versão, metadados e distribuição."""

    def test_versao(self) -> None:
        """Garante versão semântica 1.0.0."""
        self.assertEqual(vigas_concreto_nbr6118.__version__, "1.0.0")

    def test_py_typed_presente(self) -> None:
        """Garante conformidade com PEP 561 para verificação estática de tipos."""
        pacote_dir = os.path.dirname(vigas_concreto_nbr6118.__file__)
        py_typed = os.path.join(pacote_dir, "py.typed")
        self.assertTrue(os.path.exists(py_typed), "Marcador py.typed ausente no pacote.")

    def test_simbolos_exportados_all(self) -> None:
        """Garante que todos os símbolos declarados em __all__ existam no módulo."""
        for simbolo in vigas_concreto_nbr6118.__all__:
            self.assertTrue(
                hasattr(vigas_concreto_nbr6118, simbolo),
                f"Símbolo exportado '{simbolo}' não encontrado no módulo vigas_concreto_nbr6118.",
            )


if __name__ == "__main__":
    unittest.main()
