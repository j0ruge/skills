# Os sensores do gate

Cada sensor só merece confiança depois de ficar vermelho num caso sabotado e verde no caso bom. A
coluna "sabotagem" diz como provar.

| # | Sensor | Comando ou forma | Sabotagem que deve reprovar |
|---|---|---|---|
| 1 | pacote instalado num consumidor vazio | ver abaixo | `exports` apontando para `src` |
| 2 | `publint` | `npx publint --strict` sobre o tarball | `types` depois de `default` |
| 3 | `attw` | `npx --yes @arethetypeswrong/cli --pack . --profile esm-only` | `types` apontando para arquivo que não existe |
| 4 | relatório da API (**desenho**) | API Extractor gera `api-report/<pacote>.api.md` de `dist/*.d.ts`; o gate compara com o versionado | um export novo sem atualizar o relatório |
| 5 | contrato exportado | a suíte `./testing` roda contra cada driver | um driver dublê que mente num método |
| 6 | formato gravado | um teste lê uma fixture no formato da versão publicada | mudar a chave do metadado gravado |
| 7 | documentação que compila | os blocos `typescript` do README entram na `typecheck` | um exemplo com assinatura velha |
| 8 | fronteira | a lib não importa nenhum consumidor nem sai da própria pasta | um import de `@consumidor/x` |

## 1. O pacote como o consumidor o recebe

```bash
set -euo pipefail
TGZ=$(npm pack --silent)                   # dentro do pacote
C=$(mktemp -d)                             # consumidor vazio, sempre novo
cd "$C" && npm init -y >/dev/null && npm install "$OLDPWD/$TGZ" --cache "$(mktemp -d)"
node --input-type=module -e "await import('@org/pacote'); await import('@org/pacote/testing')"
tar tzf "$OLDPWD/$TGZ" | grep -E '__tests__|\.env|\.tgz$' && exit 1 || true
```

O `--input-type=module` vem **antes** do `-e`; depois dele, o `node` o ignora e o `await` de topo
quebra. A sequência foi rodada num pacote de prova em 2026-10-16 (Node 22.22, npm 12.0.2).

- **Consumidor novo a cada execução**: um diretório de rodada anterior passa sem testar nada.
- **Cache vazio**: o cache global do npm serve os bytes antigos e esconde o pacote novo.
- **Compile também um uso com `tsc`** no consumidor (`moduleResolution: NodeNext`): o `node` prova o
  runtime, o `tsc` prova os tipos.
- **Em cada Node suportado.** O que falta na estação roda por container, sem instalar nada:
  `docker run --rm -v "$PWD":/w -w /w node:24-alpine sh -c '<os mesmos passos>'`.

## 4. O relatório da API como poka-yoke do semver (desenho)

O relatório transforma "a API mudou?" em diff de arquivo. A regra que fecha o ciclo mora no script de
release: **recusar bump patch quando o relatório mudou desde a última tag do pacote**. Se a mudança é
minor ou major, quem decide é uma pessoa no PR, olhando o diff do relatório. O API Extractor usa a API
programática do TypeScript: com o TypeScript 7.0, que não a tem estável, ele não acompanha (fontes).

## Ordem no gate

Todos os passos rodam mesmo depois de um vermelho, e o código de saída conta as falhas: um gate que
para no primeiro erro esconde o segundo. A ordem: typecheck, testes, build, os sensores 1 a 3 sobre o
tarball, o relatório da API e `shellcheck` dos scripts.

## Evidência sem CI

Sem CI, o gate roda na estação e a evidência vai no commit por status da API do GitHub (que é grátis e
não é Actions), com o resultado real do gate **naquele sha**:

```bash
gh api -X POST "repos/<dono>/<repo>/statuses/$(git rev-parse HEAD)" \
  -f state=success -f context=local/ci -f description="gate ok"
```

Nunca `success` sem ter rodado o gate no sha; `failure` quando um passo reprova. Um hook `pre-push`
versionado (`.githooks/pre-push` com `git config core.hooksPath .githooks`) roda o mesmo gate.
