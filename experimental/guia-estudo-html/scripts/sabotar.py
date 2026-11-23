#!/usr/bin/env python3
"""Prova de que cada sensor falha com o defeito presente, no curso-modelo da skill.

Rode no assets/curso-modelo da própria skill, depois de mudar um sensor ou o kit. Cada caso troca um texto
exato do curso-modelo. Diante de outro curso, o script sai 2 e diz qual caso não achou o seu texto. O curso
de quem estuda passa pelo rodar-tudo.sh.

Cria uma cópia do curso por caso, com a correção desfeita (a troca de texto abaixo, nos assets ou nas
páginas). O nome do caso é o do sensor; o sufixo "-escuro" marca a segunda passada do mesmo sensor.
Com --bancada, o script faz duas etapas:
  1. Controle: roda cada sensor numa cópia intacta do curso, em controle/. O sensor tem de sair 0. Se não
     sai, o script imprime CONTROLE FALHOU <caso> e sai 2 sem sabotar nada. Sem rede, os sensores do
     Mermaid falham aqui.
  2. Sabotagem: roda o sensor de cada caso na cópia do caso. MORTO quer dizer que o sensor saiu 1 e que
     toda linha FAIL traz a causa do caso. Se não, o caso fica VIVO.
Sai 0 só se todos morrerem. Os sensores de aula rodam só em lessons/*.html; os outros, em todas as páginas
(a mesma divisão do rodar-tudo.sh).

Uso: python3 sabotar.py assets/curso-modelo <pasta nova, fora do repositório> [--bancada <bancada>]
"""
import argparse
import glob
import os
import pathlib
import re
import shutil
import subprocess
import sys

AULAS = {'rodape-sem-indice', 'glossario-longe-da-aula', 'tempo-das-aulas', 'quiz-zera-ao-voltar',
         'foco-sem-contraste', 'quiz-certa-so-pela-cor'}
A1 = 'lessons/0001-o-que-cada-uma-diz.html'
A2 = 'lessons/0002-quando-a-media-engana.html'
CSS = 'assets/estudo.css'
JS_QUIZ = 'assets/quiz.js'
# Cada caso tem:
#   trocas: lista de (arquivo, texto velho, texto novo, vezes que o velho aparece; None = uma ou mais);
#   causa:  expressão regular que TODA linha FAIL do sensor tem de trazer. Ela prova que o sensor falhou
#           pelo defeito sabotado, e não por outro motivo (rede, sensor quebrado);
#   exige:  expressão regular que pelo menos uma linha FAIL tem de trazer (opcional);
#   sensor: nome do sensor, quando o caso tem nome diferente dele (opcional).
CASOS = {
    'rede-pendurada': dict(
        trocas=[(A1, '<link rel="stylesheet" href="../assets/estudo.css">',
                 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter&display=swap">\n'
                 '<link rel="stylesheet" href="../assets/estudo.css">', 1)],
        causa=r'TimeoutError em|sem primeira pintura'),
    'diagrama-ilegivel-no-celular': dict(
        trocas=[('assets/diagramas.js', 'var LIMITE = 11;', 'var LIMITE = 0;', 1)],
        causa=r'desenho \d+: menor texto'),
    'desenho-cortado-no-notebook': dict(
        trocas=[('assets/textos.js',
                 "dicaRolagem: 'Desenho largo: para ver tudo, arraste para o lado no toque, ou use Shift com a roda do mouse.',",
                 "dicaRolagem: 'Desenho largo: arraste para o lado para ver tudo.',", 1)],
        causa=r'a dica não fala do mouse'),
    'mermaid-ilegivel-no-escuro-forcado': dict(
        trocas=[(CSS, 'color-scheme: only light;', '', 1)],
        causa=r'rótulo ".*" com contraste'),
    # Primeira passada: um amarelo claro como anel (o claro falha). Segunda: um azul-marinho (só o escuro falha).
    'foco-sem-contraste': dict(
        trocas=[(CSS, '--foco: #e0006e;', '--foco: #ffd54f;', 1)],
        causa=r'opção \d+ \(\w+\): contraste', exige=r'\[claro\]'),
    'foco-sem-contraste-escuro': dict(
        trocas=[(CSS, '--foco: #e0006e;', '--foco: #1a237e;', 1)],
        causa=r'\[escuro\].*opção \d+ \(\w+\): contraste'),
    'texto-dos-graficos-sem-contraste': dict(
        trocas=[(A1, 'fill="#9a1f56"', 'fill="#e0006e"', 1)],
        causa=r'" #[0-9a-f]{3,6} contra #'),
    'rotulo-das-caixas-sem-contraste': dict(
        trocas=[(CSS, 'color: var(--texto-2);\n  margin-bottom: .3rem;', 'color: var(--acento);\n  margin-bottom: .3rem;', 1)],
        causa=r'caixa \d+, rótulo "'),
    'quiz-certa-so-pela-cor': dict(
        trocas=[(JS_QUIZ, 'botao.appendChild(m);', '', 1)],
        causa=r'não tem a marca'),
    'quiz-zera-ao-voltar': dict(
        trocas=[(JS_QUIZ, 'window.sessionStorage.setItem(CHAVE, JSON.stringify(e));', '', 1)],
        causa=r'depois do Voltar: placar'),
    'alvo-de-toque-pequeno': dict(
        trocas=[(CSS, 'min-height: 44px;', 'min-height: 0;', None), (CSS, 'min-width: 44px;', 'min-width: 0;', None)],
        causa=r'menor altura \d+ px -> "'),
    # O summary com display flex perde o triângulo de abrir: o sensor lê o display, não a altura.
    'alvo-de-toque-sem-marcador': dict(
        sensor='alvo-de-toque-pequeno',
        trocas=[(CSS, 'details.lembrar summary {\n  font-weight: 600;', 'details.lembrar summary {\n  display: flex;\n  font-weight: 600;', 1)],
        causa=r'summary sem marcador de abrir'),
    'links-vizinhos-pequenos': dict(
        trocas=[(CSS, 'min-height: 44px; padding: .2rem 0;', 'min-height: 0; padding: .2rem 0;', 1)],
        causa=r'vizinho: "'),
    'rodape-sem-indice': dict(
        trocas=[(A1, '  <a href="../index.html" data-rodape="indice">← Índice do curso</a>\n', '', 1)],
        causa=r'sem o link do índice'),
    'glossario-longe-da-aula': dict(
        trocas=[(A1, ' data-atalho="glossario" target="_blank" rel="noopener">', ' data-atalho="glossario">', 1)],
        causa=r'o glossário dos atalhos abre na mesma aba'),
    'tempo-das-aulas': dict(
        trocas=[('index.html', 'Cerca de <span data-minutos="15">15</span> minutos · média, mediana',
                 'Cerca de <span data-minutos="20">20</span> minutos · média, mediana', 1)],
        causa=r'cabeçalho (\d+); índice (?!\1\b)\d+'),
    'cor-sem-legenda': dict(
        trocas=[(A2, ' Em amarelo, o resultado.', '', 1)],
        causa=r'a legenda não diz amarelo'),
    # Cor por nome e cor de seta: dois caminhos que o sensor não lia (ver o cabeçalho do cor-sem-legenda.js).
    'cor-sem-legenda-nome': dict(
        sensor='cor-sem-legenda',
        trocas=[(A2, '  class V conf\n', '  class V conf\n  style H fill:red\n', 1)],
        causa=r'a legenda não diz cor desconhecida red'),
    'cor-sem-legenda-seta': dict(
        sensor='cor-sem-legenda',
        trocas=[(A2, '  class V conf\n', '  class V conf\n  linkStyle 0 stroke:#e0006e\n', 1)],
        causa=r'a legenda não diz cor desconhecida #e0006e'),
    'retorno-repete-negacao': dict(
        trocas=[(JS_QUIZ, 'if (!acertou) explica = tirarNegacao(explica);', '', 1)],
        causa=r'repete a negação'),
    'caixas-fecham-ao-voltar': dict(
        trocas=[(A2, '<script src="../assets/quiz.js"></script>\n', '', 1)],
        causa=r'depois do Voltar, \d+ caixas abertas'),
}


def sensor_de(caso):
    if 'sensor' in CASOS[caso]:
        return CASOS[caso]['sensor']
    return caso[:-len('-escuro')] if caso.endswith('-escuro') else caso


def aulas_do_rodar_tudo(aqui):
    """Lê, no rodar-tudo.sh, a lista dos sensores que rodam só em lessons/*.html. None se não achar."""
    try:
        texto = (aqui / 'rodar-tudo.sh').read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return None
    m = re.search(r'^\s*([a-z0-9|-]+)\)\s*alvo=\("\$\{LESS\[@\]\}"\)', texto, re.M)
    return set(m.group(1).split('|')) if m else None


def conferir_modelo(curso):
    """Confere, antes de copiar, que cada troca acha o seu texto. Devolve o primeiro problema, ou None."""
    for caso, c in CASOS.items():
        for arq, velho, _, n in c['trocas']:
            p = curso / arq
            if not p.is_file():
                return f'o caso {caso} não acha o arquivo {arq}'
            try:
                k = p.read_text(encoding='utf-8').count(velho)
            except (OSError, UnicodeDecodeError) as e:
                return f'o caso {caso} não consegue ler {arq} ({e})'
            if k < 1 or (n is not None and k != n):
                return f'o caso {caso} não acha o texto em {arq} (achou {k} vezes, esperava {n or "1 ou mais"}): {velho!r}'
    return None


def criar(curso, saida):
    """Cria uma cópia por caso e devolve as pastas."""
    pastas = {}
    for caso, c in CASOS.items():
        dest = saida / caso
        shutil.copytree(curso, dest)
        for arq, velho, novo, _ in c['trocas']:
            p = dest / arq
            t = p.read_text(encoding='utf-8')
            p.write_text(t.replace(velho, novo), encoding='utf-8')
            print(caso, arq, 'trocas:', t.count(velho))
        pastas[caso] = dest
    return pastas


def rodar(sensor, nome, pasta, saida, bancada, sensores):
    """Roda um sensor nas páginas de uma pasta e grava a saída em <saida>/<nome>.out."""
    aulas = sorted(glob.glob(str(pasta / 'lessons' / '*.html')))
    todas = [str(pasta / 'index.html')] + aulas + sorted(glob.glob(str(pasta / 'reference' / '*.html')))
    alvo = aulas if sensor in AULAS else todas
    env = dict(os.environ, NODE_PATH=str(bancada / 'pw' / 'node_modules'))
    try:
        r = subprocess.run(['node', str(sensores / (sensor + '.js')), *alvo], env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, encoding='utf-8', timeout=600)
        rc, texto = r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        rc, texto = 124, 'o sensor passou de 600 s\n'
    except OSError as e:
        rc, texto = 127, f'o node não rodou: {e}\n'
    (saida / (nome + '.out')).write_text(texto, encoding='utf-8')
    return rc, [l for l in texto.splitlines() if l.startswith('FAIL')]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('curso')
    ap.add_argument('saida')
    ap.add_argument('--bancada')
    a = ap.parse_args()
    curso = pathlib.Path(a.curso).resolve()
    saida = pathlib.Path(a.saida).resolve()
    if not curso.is_dir():
        print(f'erro: a pasta do curso {curso} não existe.', file=sys.stderr)
        return 2
    problema = conferir_modelo(curso)
    if problema:
        print(f'erro: este curso não é o curso-modelo: {problema}.', file=sys.stderr)
        print('O sabotar.py prova os sensores no assets/curso-modelo da skill. O curso de quem estuda passa '
              'pelo rodar-tudo.sh. Nada foi criado.', file=sys.stderr)
        return 2
    # A lista dos sensores de aula mora aqui e no case do rodar-tudo.sh. Se as duas divergem, o sabotar.py mediria
    # um sensor em páginas que o rodar-tudo.sh não usa, e o MORTO não valeria para o curso real.
    do_sh = aulas_do_rodar_tudo(pathlib.Path(__file__).resolve().parent)
    if do_sh != AULAS:
        print('erro: a lista de sensores de aula do sabotar.py (AULAS) difere da do case do rodar-tudo.sh: '
              + ('o case não foi achado.' if do_sh is None else
                 f'só em AULAS {sorted(AULAS - do_sh)}; só no rodar-tudo.sh {sorted(do_sh - AULAS)}.'), file=sys.stderr)
        return 2
    bancada = pathlib.Path(a.bancada).resolve() if a.bancada else None
    if bancada and not (bancada / 'pw' / 'node_modules' / 'playwright').is_dir():
        print(f'erro: {bancada} não é uma bancada do preparar.sh (falta pw/node_modules/playwright).', file=sys.stderr)
        return 2
    if saida.exists() and any(saida.iterdir()):
        print(f'erro: {saida} não está vazia; informe uma pasta nova ou vazia (nada foi apagado).', file=sys.stderr)
        return 2
    saida.mkdir(parents=True, exist_ok=True)
    if not bancada:
        criar(curso, saida)
        return 0
    sensores = pathlib.Path(__file__).resolve().parent / 'sensores'

    # 1. Controle: o curso intacto tem de passar em cada sensor. Se não passa, um MORTO não prova nada.
    controle = saida / 'controle'
    shutil.copytree(curso, controle)
    medidos = {}
    falhou = 0
    for caso in CASOS:
        sensor = sensor_de(caso)
        if sensor not in medidos:
            medidos[sensor] = rodar(sensor, 'controle-' + sensor, controle, saida, bancada, sensores)
        rc, falhas = medidos[sensor]
        if rc != 0 or falhas:
            print('CONTROLE FALHOU', caso, f'(rc {rc}):', falhas[0][:200] if falhas else 'sem linha FAIL')
            falhou += 1
    if falhou:
        print(f'erro: {falhou} casos falharam no curso intacto (ver controle-*.out); a sabotagem não rodou.',
              file=sys.stderr)
        return 2
    print('controle: os', len(medidos), 'sensores passam no curso intacto')

    # 2. Sabotagem: cada sensor tem de falhar na sua cópia, e pela causa do caso.
    pastas = criar(curso, saida)
    vivos = 0
    for caso, pasta in pastas.items():
        rc, falhas = rodar(sensor_de(caso), caso, pasta, saida, bancada, sensores)
        causa = CASOS[caso]['causa']
        exige = CASOS[caso].get('exige')
        outra = [l for l in falhas if not re.search(causa, l)]
        if rc != 1:
            print('VIVO', caso, f'(rc {rc})')
            vivos += 1
        elif not falhas:
            print('VIVO', caso, '(rc 1 sem linha FAIL: o sensor quebrou antes de medir)')
            vivos += 1
        elif outra:
            print('VIVO', caso, f'(falhou por outra causa: {outra[0][:160]})')
            vivos += 1
        elif exige and not any(re.search(exige, l) for l in falhas):
            print('VIVO', caso, f'(falhou, mas nenhuma linha FAIL traz {exige})')
            vivos += 1
        else:
            print('MORTO', caso, f'({len(falhas)} linhas FAIL, todas com /{causa}/)')
    return 1 if vivos else 0


if __name__ == '__main__':
    sys.exit(main())
