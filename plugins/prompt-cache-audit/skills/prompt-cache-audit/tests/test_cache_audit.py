"""Testes do cache_audit.py com transcritos mínimos escritos à mão (nenhum transcrito real entra no repositório)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import cache_audit  # noqa: E402


def resposta(ident, quando, modelo='modelo-a', entrada=0, lido=0, escrito=0, ttl='1h', lateral=False):
    """Uma linha de resposta do assistente, no formato que o Claude Code grava no transcrito."""
    criacao = {'ephemeral_5m_input_tokens': 0, 'ephemeral_1h_input_tokens': 0}
    criacao[f'ephemeral_{ttl}_input_tokens'] = escrito
    return {'type': 'assistant', 'timestamp': quando, 'isSidechain': lateral,
            'message': {'id': ident, 'model': modelo,
                        'usage': {'input_tokens': entrada, 'cache_read_input_tokens': lido,
                                  'cache_creation_input_tokens': escrito, 'output_tokens': 10,
                                  'cache_creation': criacao}}}


class Transcritos(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def gravar(self, relativo, linhas):
        caminho = self.raiz / relativo
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(''.join(json.dumps(l) + '\n' for l in linhas), encoding='utf-8')
        return caminho

    def auditar(self, **kw):
        return cache_audit.audit(sorted(self.raiz.rglob('*.jsonl')), **kw)

    def test_a_mesma_resposta_gravada_duas_vezes_conta_uma(self):
        linha = resposta('m1', '2026-01-01T10:00:00Z', lido=900, escrito=100)
        self.gravar('p/s.jsonl', [linha, linha, {'type': 'user', 'message': {'content': 'oi'}}])
        modelo = self.auditar()['models']['modelo-a']
        self.assertEqual((modelo['requests'], modelo['read'], modelo['write']), (1, 900, 100))

    def test_a_taxa_lida_e_leitura_sobre_toda_a_entrada(self):
        self.gravar('p/s.jsonl', [resposta('m1', '2026-01-01T10:00:00Z', entrada=100, lido=700, escrito=200)])
        self.assertAlmostEqual(self.auditar()['models']['modelo-a']['read_pct'], 70.0)

    def test_separa_a_conversa_principal_do_subagente_e_o_ttl_de_cada_um(self):
        self.gravar('p/s.jsonl', [resposta('m1', '2026-01-01T10:00:00Z', escrito=1000, ttl='1h')])
        self.gravar('p/s/subagents/agent-x.jsonl', [resposta('m2', '2026-01-01T10:00:00Z', escrito=300, ttl='5m')])
        self.gravar('p/t.jsonl', [resposta('m3', '2026-01-01T10:00:00Z', escrito=50, ttl='5m', lateral=True)])
        escritas = self.auditar()['writes']
        self.assertEqual(escritas['main'], {'5m': 0, '1h': 1000})
        self.assertEqual(escritas['sub'], {'5m': 350, '1h': 0})

    def test_classifica_cada_queda_de_cache_pela_causa(self):
        cheio = dict(lido=40000, escrito=0)
        self.gravar('p/pausa-longa.jsonl', [resposta('a1', '2026-01-01T10:00:00Z', **cheio),
                                           resposta('a2', '2026-01-01T12:00:00Z', escrito=40000)])
        self.gravar('p/pausa-media.jsonl', [resposta('b1', '2026-01-01T10:00:00Z', **cheio),
                                           resposta('b2', '2026-01-01T10:20:00Z', escrito=40000)])
        self.gravar('p/modelo.jsonl', [resposta('c1', '2026-01-01T10:00:00Z', **cheio),
                                      resposta('c2', '2026-01-01T10:01:00Z', modelo='modelo-b', escrito=40000)])
        self.gravar('p/prefixo.jsonl', [resposta('d1', '2026-01-01T10:00:00Z', **cheio),
                                       resposta('d2', '2026-01-01T10:01:00Z', escrito=40000)])
        self.gravar('p/sem-queda.jsonl', [resposta('e1', '2026-01-01T10:00:00Z', **cheio),
                                         resposta('e2', '2026-01-01T12:00:00Z', lido=40000, escrito=500)])
        quedas = {(q['kind'], q['cause']): (q['events'], q['rewritten']) for q in self.auditar()['misses']}
        self.assertEqual(quedas, {('main', 'idle_over_1h'): (1, 40000), ('main', 'idle_5m_to_1h'): (1, 40000),
                                  ('main', 'model_switch'): (1, 40000), ('main', 'prefix_changed'): (1, 40000)})

    def test_prefixo_pequeno_nao_conta_como_queda(self):
        self.gravar('p/s.jsonl', [resposta('a1', '2026-01-01T10:00:00Z', lido=5000),
                                  resposta('a2', '2026-01-01T12:00:00Z', escrito=5000)])
        self.assertEqual(self.auditar()['misses'], [])

    def test_o_ttl_de_1h_so_compensa_acima_do_limiar_de_reescrita(self):
        # 5 min custa 1,25 x; 1h custa 2 x; leitura 0,1 x: compensa quando reescrito > 0,75 / (2 - 0,1) do escrito em 5 min
        self.assertAlmostEqual(cache_audit.ttl_threshold(1.25, 2.0, 0.1), 0.75 / 1.9)
        self.assertFalse(cache_audit.ttl_verdict(written_5m=108, rewritten=20)['worth_1h'])
        self.assertTrue(cache_audit.ttl_verdict(written_5m=100, rewritten=60)['worth_1h'])
        self.assertFalse(cache_audit.ttl_verdict(written_5m=0, rewritten=0)['worth_1h'])

    def test_o_veredito_do_ttl_usa_so_as_pausas_entre_5_min_e_1h(self):
        cheio = dict(lido=40000, escrito=0)
        self.gravar('p/s/subagents/agent-x.jsonl', [resposta('b1', '2026-01-01T10:00:00Z', **cheio),
                                                   resposta('b2', '2026-01-01T10:20:00Z', escrito=40000, ttl='5m'),
                                                   resposta('b3', '2026-01-01T13:00:00Z', escrito=40000, ttl='5m')])
        veredito = self.auditar()['ttl']['sub']
        self.assertEqual((veredito['written_5m'], veredito['rewritten']), (80000, 40000))
        self.assertTrue(veredito['worth_1h'])

    def test_mede_o_tamanho_do_contexto_por_pedido(self):
        self.gravar('p/s.jsonl', [resposta(f'm{i}', f'2026-01-01T10:0{i}:00Z', lido=1000 * (i + 1)) for i in range(5)])
        contexto = self.auditar()['context']['main']
        self.assertEqual((contexto['requests'], contexto['median'], contexto['max']), (5, 3000, 5000))

    def test_transcrito_sem_o_formato_esperado_falha_dizendo_o_que_esperava(self):
        self.gravar('p/s.jsonl', [{'tipo': 'outro', 'dados': 1}, {'type': 'assistant', 'message': {'sem': 'usage'}}])
        with self.assertRaises(cache_audit.UnexpectedFormat) as erro:
            self.auditar()
        self.assertIn('message.usage', str(erro.exception))

    def test_linha_de_comando_devolve_json_e_codigos_de_saida(self):
        self.gravar('p/s.jsonl', [resposta('m1', '2026-01-01T10:00:00Z', lido=900, escrito=100)])
        base = [sys.executable, str(SCRIPTS / 'cache_audit.py'), '--days', '0']
        saida = subprocess.run(base + ['--projects-dir', str(self.raiz), '--json'], capture_output=True, text=True)
        self.assertEqual(saida.returncode, 0, saida.stderr)
        self.assertEqual(json.loads(saida.stdout)['models']['modelo-a']['requests'], 1)
        texto = subprocess.run(base + ['--projects-dir', str(self.raiz)], capture_output=True, text=True)
        self.assertEqual(texto.returncode, 0, texto.stderr)
        self.assertIn('modelo-a', texto.stdout)
        self.assertIn('1 pedidos, mediana 1.000 tokens', texto.stdout)
        vazio = subprocess.run(base + ['--projects-dir', str(self.raiz / 'nao-existe')], capture_output=True, text=True)
        self.assertEqual(vazio.returncode, 2)
        self.assertIn('nao-existe', vazio.stderr)


if __name__ == '__main__':
    unittest.main()
