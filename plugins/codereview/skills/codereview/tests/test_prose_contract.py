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
SKILL = REF.parent / "SKILL.md"


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


class TestRodadaDeVerificacao(unittest.TestCase):
    def test_contrato_do_verificador_existe_e_fecha_com_a_sentinela(self):
        t = (REF / "verify-agent.md").read_text(encoding="utf-8")
        for trecho in ("END_OF_VERIFICATION", "Outside scope (max 5)", "Kind:"):
            self.assertIn(trecho, t)

    def test_verificador_nao_carrega_os_passes_de_codigo(self):
        t = (REF / "verify-agent.md").read_text(encoding="utf-8")
        self.assertNotIn("Read {SKILL_DIR}/references/detection-passes.md", t)

    def test_skill_roteia_e_diz_quando_ler(self):
        t = SKILL.read_text(encoding="utf-8")
        for trecho in ("scripts/prose_units.py", "references/verify-agent.md",
                       "verify=off", "without that list, the re-review runs as a full round"):
            self.assertIn(trecho, t)

    def test_skill_fica_abaixo_do_teto(self):
        self.assertLess(len(SKILL.read_text(encoding="utf-8").splitlines()), 280)

    def test_prompt_do_verificador_nao_leva_achado_anterior(self):
        t = SKILL.read_text(encoding="utf-8")
        ini = t.index("Read {SKILL_DIR}/references/verify-agent.md")
        bloco = t[ini: t.index('")', ini)]
        self.assertNotIn("finding", bloco.lower())


if __name__ == "__main__":
    unittest.main()
