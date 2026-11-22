#!/usr/bin/env python3
"""Prova de que cada sensor falha com o defeito presente, no curso-modelo da skill.

Rode no assets/curso-modelo da própria skill, depois de mudar um sensor ou o kit. Cada caso troca um texto
exato do curso-modelo. Diante de outro curso, o script sai 2 e diz qual caso não achou o seu texto. O curso
de quem estuda passa pelo rodar-tudo.sh.

Cria uma cópia do curso por caso, com a correção desfeita (a troca de texto abaixo, nos assets ou nas
páginas). O nome do caso é o do sensor; o sufixo "-escuro" marca a segunda passada do mesmo sensor.
Cada troca confere quantas vezes o texto velho aparece antes de trocar.
Com --bancada, roda o sensor de cada caso na própria cópia e imprime MORTO (o sensor saiu 1) ou VIVO
(saiu 0). Sai 0 só se todos morrerem. Os sensores de aula rodam só em lessons/*.html; os outros, em todas
as páginas (a mesma divisão do rodar-tudo.sh).

Uso: python3 sabotar.py assets/curso-modelo <pasta nova, fora do repositório> [--bancada <bancada>]
"""
import argparse
import glob
import os
import pathlib
import shutil
import subprocess
import sys

AULAS = {'rodape-sem-indice', 'glossario-longe-da-aula', 'tempo-das-aulas', 'quiz-zera-ao-voltar',
         'foco-sem-contraste', 'quiz-certa-so-pela-cor'}
A1 = 'lessons/0001-o-que-cada-uma-diz.html'
A2 = 'lessons/0002-quando-a-media-engana.html'
CSS = 'assets/estudo.css'
JS_QUIZ = 'assets/quiz.js'
# Cada caso: lista de (arquivo, texto velho, texto novo, vezes que o velho aparece; None = uma ou mais),
# mais uma marca que as linhas FAIL do sensor têm de trazer para o caso valer (None = qualquer FAIL serve;
# o prefixo "=" exige que SÓ as linhas com a marca falhem).
CASOS = {
    'rede-pendurada': ([(A1, '<link rel="stylesheet" href="../assets/estudo.css">',
                         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter&display=swap">\n'
                         '<link rel="stylesheet" href="../assets/estudo.css">', 1)], None),
    'diagrama-ilegivel-no-celular': ([('assets/diagramas.js', 'var LIMITE = 11;', 'var LIMITE = 0;', 1)], None),
    'desenho-cortado-no-notebook': ([('assets/textos.js',
                                      "dicaRolagem: 'Desenho largo: para ver tudo, arraste para o lado no toque, ou use Shift com a roda do mouse.',",
                                      "dicaRolagem: 'Desenho largo: arraste para o lado para ver tudo.',", 1)], None),
    'mermaid-ilegivel-no-escuro-forcado': ([(CSS, 'color-scheme: only light;', '', 1)], None),
    # Primeira passada: um amarelo claro como anel (o claro falha). Segunda: um azul-marinho (só o escuro falha).
    'foco-sem-contraste': ([(CSS, '--foco: #e0006e;', '--foco: #ffd54f;', 1)], '[claro]'),
    'foco-sem-contraste-escuro': ([(CSS, '--foco: #e0006e;', '--foco: #1a237e;', 1)], '=[escuro]'),
    'texto-dos-graficos-sem-contraste': ([(A1, 'fill="#9a1f56"', 'fill="#e0006e"', 1)], None),
    'rotulo-das-caixas-sem-contraste': ([(CSS, 'color: var(--texto-2);\n  margin-bottom: .3rem;',
                                          'color: var(--acento);\n  margin-bottom: .3rem;', 1)], None),
    'quiz-certa-so-pela-cor': ([(JS_QUIZ, 'botao.appendChild(m);', '', 1)], None),
    'quiz-zera-ao-voltar': ([(JS_QUIZ, 'window.sessionStorage.setItem(CHAVE, JSON.stringify(e));', '', 1)], None),
    'alvo-de-toque-pequeno': ([(CSS, 'min-height: 44px;', 'min-height: 0;', None),
                               (CSS, 'min-width: 44px;', 'min-width: 0;', None)], None),
    'links-vizinhos-pequenos': ([(CSS, 'min-height: 44px; padding: .2rem 0;', 'min-height: 0; padding: .2rem 0;', 1)], None),
    'rodape-sem-indice': ([(A1, '  <a href="../index.html" data-rodape="indice">← Índice do curso</a>\n', '', 1)], None),
    'glossario-longe-da-aula': ([(A1, ' data-atalho="glossario" target="_blank" rel="noopener">',
                                  ' data-atalho="glossario">', 1)], None),
    'tempo-das-aulas': ([('index.html', 'Cerca de <span data-minutos="15">15</span> minutos · média, mediana',
                          'Cerca de <span data-minutos="20">20</span> minutos · média, mediana', 1)], None),
    'cor-sem-legenda': ([(A2, ' Em amarelo, o resultado.', '', 1)], None),
    'retorno-repete-negacao': ([(JS_QUIZ, 'if (!acertou) explica = tirarNegacao(explica);', '', 1)], None),
    'caixas-fecham-ao-voltar': ([(A2, '<script src="../assets/quiz.js"></script>\n', '', 1)], None),
}


def sensor_de(caso):
    return caso[:-len('-escuro')] if caso.endswith('-escuro') else caso


def conferir_modelo(curso):
    """Confere, antes de copiar, que cada troca acha o seu texto. Devolve o primeiro problema, ou None."""
    for caso, (trocas, _) in CASOS.items():
        for arq, velho, _, n in trocas:
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
    for caso, (trocas, _) in CASOS.items():
        dest = saida / caso
        shutil.copytree(curso, dest)
        for arq, velho, novo, _ in trocas:
            p = dest / arq
            t = p.read_text(encoding='utf-8')
            p.write_text(t.replace(velho, novo), encoding='utf-8')
            print(caso, arq, 'trocas:', t.count(velho))
        pastas[caso] = dest
    return pastas


def rodar(caso, pasta, saida, bancada, sensores):
    sensor = sensor_de(caso)
    aulas = sorted(glob.glob(str(pasta / 'lessons' / '*.html')))
    todas = [str(pasta / 'index.html')] + aulas + sorted(glob.glob(str(pasta / 'reference' / '*.html')))
    alvo = aulas if sensor in AULAS else todas
    env = dict(os.environ, NODE_PATH=str(bancada / 'pw' / 'node_modules'))
    r = subprocess.run(['node', str(sensores / (sensor + '.js')), *alvo], env=env, stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, encoding='utf-8', timeout=600)
    (saida / (caso + '.out')).write_text(r.stdout + r.stderr, encoding='utf-8')
    return r.returncode, r.stdout


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
    if saida.exists() and any(saida.iterdir()):
        print(f'erro: {saida} não está vazia; informe uma pasta nova ou vazia (nada foi apagado).', file=sys.stderr)
        return 2
    saida.mkdir(parents=True, exist_ok=True)
    pastas = criar(curso, saida)
    if not a.bancada:
        return 0
    bancada = pathlib.Path(a.bancada).resolve()
    sensores = pathlib.Path(__file__).resolve().parent / 'sensores'
    vivos = 0
    for caso, pasta in pastas.items():
        rc, saida_sensor = rodar(caso, pasta, saida, bancada, sensores)
        exigir = CASOS[caso][1] or ''
        so = exigir.startswith('=')
        marca = exigir.lstrip('=')
        falhas = [l for l in saida_sensor.splitlines() if l.startswith('FAIL')]
        if rc != 1:
            print('VIVO', caso, f'(rc {rc})')
            vivos += 1
        elif marca and not any(marca in l for l in falhas):
            print('VIVO', caso, f'(falhou, mas não em {marca})')
            vivos += 1
        elif not falhas:
            print('VIVO', caso, '(rc 1 sem linha FAIL: o sensor quebrou, não mediu)')
            vivos += 1
        elif so and any(marca not in l for l in falhas):
            print('VIVO', caso, f'(falhou também fora de {marca})')
            vivos += 1
        else:
            print('MORTO', caso)
    return 1 if vivos else 0


if __name__ == '__main__':
    sys.exit(main())
