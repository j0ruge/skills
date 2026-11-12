# Changelog — gpui (experimental)

Skill sem versão: fica em `experimental/`, fora dos catálogos (ver `../README.md`).
Cada entrada leva a data e o motivo.

## 2026-11-12 — Identidade da cópia e observação após jobs

- O QA identifica por hash a cópia que executa, mantendo o caminho de origem
  separado. Um probe trocou o alias imediatamente após copiar e reproduziu
  `SHA256 reportado não identifica a cópia executada`. Calcular o hash da cópia
  passou; sabotar o cálculo numa cópia do driver voltou a falhar.
- Checagens de ausência de efeito aguardam o trabalho assíncrono. Quando as
  escritas são serializadas, um commit de controle confirmado fornece a barreira
  antes de comparar os registros anteriores. O mutante específico de Enter
  compilou e foi detectado com `Enter alterou uma seleção oculta` após essa
  confirmação; a leitura imediata anterior não tinha esse sensor de conclusão.
- Referência ampliada no modo lean, sem alterar gatilho ou versão. O aviso B4
  preexistente de caminho absoluto permanece fora do escopo deste retrofit.

## 2026-11-12 — QA isolado e oráculo da ação

- Nova referência de QA headless para Xvfb com renderizador de software, sem
  disputar teclado/mouse no desktop em uso. O SKILL.md roteia sua leitura também
  quando o OCR divergir da ação. Não estabelece uma preferência universal nem
  adiciona dependências ao aplicativo.
- A ação precisa de efeito verificável: OCR sob o cursor e variações como está/este
  causaram falsos negativos; confirmar a operação no estado da fixture e usar um
  marcador visual estável resolveu os probes sem mudar o produto para agradar o OCR.
- Escopo medido: Ubuntu 24.04/X11, Rust 1.97.0, GPUI 0.2.2/component 0.5.1;
  abertura, criação e exit 0 em Xvfb/llvmpipe; seis jornadas de foco e quatro de
  inicialização aprovadas. Não é medição de latência nem validação de outros backends.
- Experimental, sem bump ou catálogo. Dívidas anteriores permanecem no histórico.

## 2026-11-12 — entrada no repositório

A skill nasceu como skill pessoal do Codex em `~/.codex/skills/gpui`, fora do git. Ela veio para
`experimental/gpui/` sem nenhuma mudança de conteúdo (`diff -r` vazio contra a origem), e
`~/.codex/skills/gpui` passou a ser um symlink para esta pasta. A única novidade é este arquivo.

**Por que é experimental:** a skill foi escrita e conferida numa aplicação só, um app desktop de
tarefas com GPUI 0.2.2, gpui-component 0.5.1 e Ubuntu 24.04/X11. Nenhum outro projeto GPUI e nenhum
outro backend gráfico a usaram ainda.

Dívida que veio da origem, registrada pelo auditor da `skill-quality-audit` (`--claims --desc-budget 0`)
e não corrigida nesta entrada:

- B4: `references/state-and-x11.md` cita a evidência por um caminho absoluto desta máquina. O caminho
  só resolve aqui. Ele foi mantido para a cópia não divergir da origem.
- F1: o auditor não reconhece quando ler `references/state-and-x11.md`, embora o `SKILL.md` diga o
  assunto que leva até ela.
- F2: o `SKILL.md` não tem seção de armadilhas.
- F4: não há evals de gatilho nem de comportamento.
- A `description` começa com "Use when…" e por isso fica fora do padrão de `plugins/` (ver
  `CLAUDE.md`, *Skill description guidelines*). Isso precisa mudar antes de uma promoção.
