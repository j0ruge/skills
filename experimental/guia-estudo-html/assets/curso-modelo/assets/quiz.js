// Regra do quiz: o retorno vem logo após o toque, diz o certo e o porquê, e não depende só da cor.
// Marcação de cada pergunta (índice da certa a partir de 1):
//   <div class="pergunta" data-certa="2">
//     <p class="enunciado">…</p>
//     <div class="opcoes"><button class="opcao" data-explica="porquê, com a fonte">…</button></div>
//     <p class="retorno" aria-live="polite"></p>
//   </div>
// Depois do toque: a .pergunta ganha data-resultado="certo" ou "errado"; a opção certa ganha a classe
// "certa" e um span.marca; a escolha errada ganha "errada" e um span.marca. O placar (p.placar) conta
// só a primeira tentativa de cada pergunta, a que mede a memória.
//
// Estado na aba: o placar, as marcas e as caixas <details> abertas vão para o sessionStorage, na chave
// 'guia:' + caminho da página. Voltam depois do Voltar e do recarregar. Fechar a aba apaga tudo.
// Sem sessionStorage (bloqueado, cheio ou janela restrita), a página funciona igual, sem guardar.
// Toda página com quiz ou com <details> carrega este arquivo, depois do textos.js.
(function () {
  'use strict';

  var T = window.GUIA_TEXTOS;
  if (!T) {
    console.error('GUIA_TEXTOS ausente: carregue assets/textos.js antes do quiz.js.');
    return;
  }
  // Com um textos.js parcial, o quiz escreveria "undefined" na tela. Sem as chaves, ele avisa e não liga.
  var CHAVES = ['certo', 'aindaNao', 'marcaCerta', 'marcaSua', 'placar', 'aCerta'];
  var faltam = CHAVES.filter(function (c) { return typeof T[c] !== 'string' || !T[c]; });
  if (faltam.length && document.querySelector('.pergunta')) {
    console.error('GUIA_TEXTOS sem as chaves ' + faltam.join(', ') + ': o quiz não liga.');
    return;
  }

  var CHAVE = 'guia:' + window.location.pathname;
  var VERSAO = 1;

  function lerEstado() {
    try {
      var bruto = window.sessionStorage.getItem(CHAVE);
      if (!bruto) return null;
      var e = JSON.parse(bruto);
      return (e && e.v === VERSAO) ? e : null;
    } catch (erro) {
      return null;
    }
  }

  function gravarEstado(e) {
    try {
      window.sessionStorage.setItem(CHAVE, JSON.stringify(e));
    } catch (erro) {
      // Sem storage: segue sem guardar.
    }
  }

  function lista(n, valor) {
    var a = [];
    for (var k = 0; k < n; k++) a.push(valor);
    return a;
  }

  function mesmoTamanho(a, n) {
    return Array.isArray(a) && a.length === n;
  }

  function escapar(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  // Tira da explicação a negação que abre a frase, porque o retorno já abre com "Ainda não.".
  function tirarNegacao(explica) {
    var lista_ = (T.negacoes || []).map(escapar).join('|');
    if (!lista_) return explica;
    return explica.replace(new RegExp('^(' + lista_ + ')\\.\\s*'), '');
  }

  function preencher(modelo, valores) {
    return String(modelo).replace(/\{(\w+)\}/g, function (todo, nome) {
      return Object.prototype.hasOwnProperty.call(valores, nome) ? valores[nome] : todo;
    });
  }

  function iniciar() {
    var perguntas = Array.prototype.slice.call(document.querySelectorAll('.pergunta'));
    var detalhes = Array.prototype.slice.call(document.querySelectorAll('details'));
    var placar = document.querySelector('.placar');
    var guardado = lerEstado();

    var estado = {
      v: VERSAO,
      primeira: lista(perguntas.length, null),   // opção da primeira tentativa, por pergunta
      ultima: lista(perguntas.length, null),     // última opção marcada, por pergunta
      abertos: detalhes.map(function (d) { return d.open; })
    };
    // O estado guardado só vale se a página tem as mesmas perguntas e caixas de quando foi gravado.
    if (guardado && mesmoTamanho(guardado.primeira, perguntas.length) && mesmoTamanho(guardado.ultima, perguntas.length)) {
      estado.primeira = guardado.primeira;
      estado.ultima = guardado.ultima;
    }
    if (guardado && mesmoTamanho(guardado.abertos, detalhes.length)) {
      estado.abertos = guardado.abertos;
    }

    function atualizarPlacar() {
      if (!placar) return;
      var respondidas = 0;
      var acertos = 0;
      perguntas.forEach(function (p, k) {
        var escolha = estado.primeira[k];
        if (typeof escolha !== 'number') return;
        respondidas += 1;
        if (escolha + 1 === parseInt(p.getAttribute('data-certa'), 10)) acertos += 1;
      });
      placar.textContent = preencher(T.placar, {
        acertos: acertos, respondidas: respondidas, total: perguntas.length
      });
    }

    perguntas.forEach(function (p, k) {
      var certa = parseInt(p.getAttribute('data-certa'), 10);
      var opcoes = Array.prototype.slice.call(p.querySelectorAll('button.opcao'));
      var textos = opcoes.map(function (b) { return b.textContent.replace(/\s+/g, ' ').trim(); });
      var retorno = p.querySelector('.retorno');

      function marcar(botao, tipo) {
        botao.classList.add(tipo);
        var m = document.createElement('span');
        m.className = 'marca';
        m.textContent = tipo === 'certa' ? T.marcaCerta : T.marcaSua;
        botao.appendChild(m);
      }

      function mostrar(i) {
        var botao = opcoes[i];
        if (!botao) return;
        var acertou = (i + 1) === certa;
        opcoes.forEach(function (b) {
          b.classList.remove('certa', 'errada');
          Array.prototype.slice.call(b.querySelectorAll('.marca')).forEach(function (m) {
            m.parentNode.removeChild(m);
          });
        });
        marcar(botao, acertou ? 'certa' : 'errada');
        if (!acertou && opcoes[certa - 1]) marcar(opcoes[certa - 1], 'certa');
        p.setAttribute('data-resultado', acertou ? 'certo' : 'errado');
        if (!retorno) return;
        var explica = (botao.getAttribute('data-explica') || '').trim();
        var partes = [acertou ? T.certo : T.aindaNao];
        if (!acertou) explica = tirarNegacao(explica);
        if (explica) partes.push(explica);
        if (!acertou && textos[certa - 1]) {
          partes.push(preencher(T.aCerta, { texto: textos[certa - 1].replace(/[.;:]+$/, '') }));
        }
        retorno.className = 'retorno ' + (acertou ? 'certo' : 'errado');
        retorno.textContent = partes.join(' ');
      }

      opcoes.forEach(function (botao, i) {
        botao.type = 'button';
        botao.addEventListener('click', function () {
          if (typeof estado.primeira[k] !== 'number') estado.primeira[k] = i;
          estado.ultima[k] = i;
          mostrar(i);
          atualizarPlacar();
          gravarEstado(estado);
        });
      });

      if (typeof estado.ultima[k] === 'number') mostrar(estado.ultima[k]);
    });

    detalhes.forEach(function (d, k) {
      if (d.open !== !!estado.abertos[k]) d.open = !!estado.abertos[k];
      d.addEventListener('toggle', function () {
        estado.abertos[k] = d.open;
        gravarEstado(estado);
      });
    });

    atualizarPlacar();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }
})();
