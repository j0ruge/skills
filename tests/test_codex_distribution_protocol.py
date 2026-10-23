"""Regressões do transporte JSONL, independentes do cliente instalado."""

import json
import select
import sys
import unittest
from unittest import mock

import test_codex_distribution as distribution


class ProtocolTests(unittest.TestCase):
    def sandbox(self, *args):
        """Emula um servidor que responde em lote e mantém o pipe aberto."""
        messages = [dict(id=1, result={}), dict(id=2, result=dict(data=[
            dict(errors=[], skills=[dict(name='example:skill', pluginId='example@test')])]))]
        script = ('import os, sys\n'
                  'for _ in range(3): sys.stdin.readline()\n'
                  f'os.write(1, {self.payload(messages)!r})\n'
                  'sys.stdin.read()\n')
        return [sys.executable, '-c', script]

    def payload(self, messages):
        """Entrega initialize e skills/list no mesmo write do servidor."""
        return ('\n'.join(map(json.dumps, messages)) + '\n').encode()

    def test_burst_responses_are_read_without_waiting_for_more_bytes(self):
        """A segunda linha pronta não depende de uma terceira escrita no pipe."""
        original = select.select
        with mock.patch('select.select', side_effect=lambda r, w, x, t: original(r, w, x, min(t, .2))):
            self.assertEqual(distribution.DistributionTests.discovered_skills(self), ['example:skill'])

    def test_eof_before_response_has_explicit_diagnostic(self):
        """EOF após initialize informa a falta de skills/list sem travar."""
        with mock.patch.object(self, 'sandbox', return_value=[sys.executable, '-c',
                               'import sys; sys.stdin.readline(); print(\'{"id":1}\')']):
            with self.assertRaisesRegex(AssertionError, 'skills/list não respondeu'):
                distribution.DistributionTests.discovered_skills(self)

    def test_fragmented_json_lines_are_reassembled(self):
        """Um JSONL dividido entre várias leituras mantém todos os bytes."""
        original = distribution.os.read
        with mock.patch('os.read', side_effect=lambda fd, size: original(fd, min(size, 3))):
            self.assertEqual(distribution.DistributionTests.discovered_skills(self), ['example:skill'])


if __name__ == '__main__':
    unittest.main()
