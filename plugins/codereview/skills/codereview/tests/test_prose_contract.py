#!/usr/bin/env python3
"""Testes do contrato de prosa nas references (só biblioteca padrão).

Rodar a partir do diretório da skill:
    python3 tests/test_prose_contract.py

Todo achado de documentação traz um tipo, `behavior` ou `form`, e a linha Documentation sai de uma
tabela escrita, não da leitura livre da escala. O verificador da rodada de verificação e a Fase C
leem esses trechos pelo texto: se um deles some ou muda de redação, este teste fica vermelho.
"""
import unittest
from pathlib import Path

REF = Path(__file__).resolve().parent.parent / "references"


class TestContratoDeProsa(unittest.TestCase):
    def test_agente_por_arquivo_pede_o_tipo(self):
        t = (REF / "per-file-agent.md").read_text(encoding="utf-8")
        for trecho in ("Kind: behavior — contradicted by {file}:{line}",
                       "Kind: behavior — missing evidence: {what}",
                       "Kind: form"):
            self.assertIn(trecho, t)

    def test_template_tem_o_criterio_e_o_balde(self):
        t = (REF / "report-template.md").read_text(encoding="utf-8")
        self.assertIn("### Documentation row", t)
        self.assertIn("**Deferred (form)**", t)
        for linha in (
                "| A | no CRITICAL, HIGH or MEDIUM documentation finding, and no `behavior` finding |",
                "| B | a MEDIUM documentation finding, a LOW `behavior` finding, or exactly one HIGH "
                "documentation finding |",
                "| C | two or more HIGH documentation findings |",
                "| D or F | a CRITICAL documentation finding, by the scale above |"):
            self.assertIn(linha, t)


if __name__ == "__main__":
    unittest.main()
