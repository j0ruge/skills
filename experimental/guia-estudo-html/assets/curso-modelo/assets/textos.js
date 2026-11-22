// Todas as frases que o kit escreve na tela moram aqui, e só aqui. Para outra língua, troque os valores
// deste arquivo: o quiz.js e o diagramas.js leem tudo daqui e os sensores nunca leem texto visível.
// {acertos}, {respondidas}, {total} e {texto} são lugares que o kit preenche.
window.GUIA_TEXTOS = {
  idioma: 'pt-BR',
  palavrasPorMinuto: 130,
  certo: 'Certo.',
  aindaNao: 'Ainda não.',
  // Palavras que abrem a explicação de uma opção errada e repetem o "Ainda não.": o quiz as tira.
  negacoes: ['Não'],
  marcaCerta: '✓ certa',
  marcaSua: '✗ sua resposta',
  placar: 'Primeira tentativa: {acertos} de {respondidas} respondidas ({total} no total)',
  aCerta: 'A certa: “{texto}”.',
  dicaRolagem: 'Desenho largo: para ver tudo, arraste para o lado no toque, ou use Shift com a roda do mouse.',
  // Palavras que a dica e as legendas precisam conter, para o sensor conferir sem ler a língua.
  palavraMouse: 'roda',
  palavraTracejado: 'tracejad',
  // Cor de fundo usada nos diagramas (hex minúsculo) e o nome que a legenda dá a ela.
  cores: {
    '#e2f0f1': 'azul',
    '#fdf3d3': 'amarelo',
    '#f8e6ef': 'rosa',
    '#e4f2e8': 'verde',
    '#f6f6f3': 'cinza'
  }
};
