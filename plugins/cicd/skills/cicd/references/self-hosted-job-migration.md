# Migrar um job cobrado para o runner self-hosted — o que quebra

## Sumário

- [Quando usar esta reference](#quando-usar-esta-reference)
- [O pré-voo, na ordem de risco medida](#o-pré-voo-na-ordem-de-risco-medida)
- [§1. O runner não tem `yarn` — e o `cache:` do `setup-node` morre antes do `install`](#1-o-runner-não-tem-yarn--e-o-cache-do-setup-node-morre-antes-do-install)
- [§2. O job não alcança o `services:` container](#2-o-job-não-alcança-o-services-container)
  - [Duas hipóteses plausíveis que custam rodadas — e são falsas](#duas-hipóteses-plausíveis-que-custam-rodadas--e-são-falsas)
  - [A causa real: o runner pode estar dentro de um container](#a-causa-real-o-runner-pode-estar-dentro-de-um-container)
  - [Descubra em vez de supor](#descubra-em-vez-de-supor)
- [§3. `container:` não é a saída se o runner estiver desatualizado](#3-container-não-é-a-saída-se-o-runner-estiver-desatualizado)
- [§4. Workspace sujo entre execuções](#4-workspace-sujo-entre-execuções)
- [§5. Como confirmar que a migração pegou](#5-como-confirmar-que-a-migração-pegou)
- [§5b. Produção: qual runner — e quando a mudança passa a valer](#5b-produção-qual-runner--e-quando-a-mudança-passa-a-valer)
- [§6. A migração desvenda a dívida do repositório — e o primeiro verde não está a um passo](#6-a-migração-desvenda-a-dívida-do-repositório--e-o-primeiro-verde-não-está-a-um-passo)
  - [§6a. O runner é root — e o teste de permissão para de medir](#6a-o-runner-é-root--e-o-teste-de-permissão-para-de-medir)
  - [§6b. O timeout default do test runner foi calibrado para a máquina de desenvolvimento](#6b-o-timeout-default-do-test-runner-foi-calibrado-para-a-máquina-de-desenvolvimento)
- [§7. Sem `.env` no CI, um módulo que faz `throw` no import derruba a suíte inteira](#7-sem-env-no-ci-um-módulo-que-faz-throw-no-import-derruba-a-suíte-inteira)
- [§8. Snapshot que grava valor de ambiente força o CI a reproduzir o valor EXATO](#8-snapshot-que-grava-valor-de-ambiente-força-o-ci-a-reproduzir-o-valor-exato)
- [§9. Job de GATE muda de natureza ao migrar — o que vigia o runner não pode rodar nele](#9-job-de-gate-muda-de-natureza-ao-migrar--o-que-vigia-o-runner-não-pode-rodar-nele)
- [§10. A lição que generaliza](#10-a-lição-que-generaliza)
- [§11. Build de imagem no self-hosted: tire o `setup-buildx` e o cache `gha`](#11-build-de-imagem-no-self-hosted-tire-o-setup-buildx-e-o-cache-gha)

## Quando usar esta reference

Você decidiu puxar a alavanca de custo da `ci-cost-minutes.md` §3a — mover `ci` / `build-and-push`
de `ubuntu-latest` para `[self-hosted, <label>]`. Ou o job já foi movido e agora falha em algum
lugar onde nunca falhava.

Esta reference cobre a **outra metade** daquele conselho: o runner hospedado é uma imagem curada,
cheia de coisa pré-instalada e com uma topologia de rede específica. Um runner self-hosted não é
nada disso. O YAML não muda, e mesmo assim o job quebra.

> **Distinção importante:** `self-hosted-runner-docker.md` trata de **construir e registrar** o
> runner (imagem `myoung34`, token, crashloop). Esta trata de **rodar jobs de aplicação** nele.

---

## O pré-voo, na ordem de risco medida

"Service containers exigem Docker no runner" parece o ponto de falha mais provável e **costuma
passar de primeira** — `Initialize containers` sobe o Postgres e o healthcheck fica `healthy` sem
nenhum ajuste. O que quebra é outra coisa, e é isso que a ordem abaixo reflete.

| # | Verificar | Sintoma se faltar |
| - | --------- | ----------------- |
| 1 | **Toolchain que o runner hospedado dá de graça** (`yarn`, `pnpm`, `jq`, `ss`, `ip`) | §1 — `setup-node` morre antes do `install` |
| 2 | **Como o job alcança um `services:` container** | §2 — `P1001` / connection refused, com o container `healthy` |
| 3 | **Versão do runner**, se você pensar em `container:` | §3 — `checkout` nem executa |
| 4 | Step de **limpeza de workspace** replicado | `fatal: missing blob object` no `checkout` |
| 5 | Docker disponível para `services:` | raro; costuma estar OK no host que já faz deploy |
| 6 | Um runner roda **um job por vez** | jobs antes paralelos serializam |

E uma verdade operacional que vale por si: **"movido para self-hosted" não é "funciona em
self-hosted".** Um workflow que teve o `runs-on` trocado e ainda não executou carrega configuração
não testada. Se você mover `ci.yml` e o job `ci` do `cd-staging.yml` juntos, corrija os dois em
paralelo — senão o merge descobre cada armadilha de novo, uma por vez.

> **§1–§5b tratam do runner. §6–§9 tratam do que aparece quando o runner passa a funcionar.**
> Se a migração está saindo de um período de CI bloqueado por cota, o job pode ficar verde de
> primeira e o **repositório** estar vermelho — comece pelo §6, não pela tabela acima.

---

## §1. O runner não tem `yarn` — e o `cache:` do `setup-node` morre antes do `install`

```
##[error]Unable to locate executable file: yarn. Please verify either the file path exists or
the file can be found within a directory specified by the PATH environment variable.
```

**Por que engana:** o step que falha é o `actions/setup-node`, que "não tem nada a ver com yarn".
Tem: `cache: 'yarn'` faz a action **invocar o binário** para descobrir o diretório de cache e
montar a chave. Sem yarn no `PATH`, ela morre — antes de qualquer `yarn install`, e antes de
qualquer chance de instalar o yarn num step seu.

Em `ubuntu-latest` isso nunca aparece porque a imagem traz yarn 1.x pré-instalado.

**Fix** — tirar o cache do `setup-node` e provisionar a ferramenta num step próprio:

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: '22.15.0'
    # sem `cache:` — ver §1

- name: Provisiona o yarn
  run: |
    corepack enable || true
    yarn --version || npm install -g yarn@1.22.22
    yarn --version
```

Perder o cache do Actions custa pouco aqui: no self-hosted o `~/.cache/yarn` sobrevive entre
execuções, que é justamente o que o cache do Actions estava simulando. (E veja
`ci-cost-minutes.md` §3d — `cache:` configurado não garante cache quente de qualquer forma.)

**Generalize:** a mesma classe morde `pnpm`, `jq`, `ss`, `ip`, `zip`. Antes de migrar, rode um step
descartável com `command -v` para cada ferramenta que o workflow assume.

---

## §2. O job não alcança o `services:` container

```
Error: P1001: Can't reach database server at `localhost:5432`
```

(`P1001` é do Prisma; com `psql`/`pg_isready` o sintoma é `Connection refused`.)

**Por que engana muito:** o log mostra o container subindo corretamente —

```
docker create ... --network github_network_<id> --network-alias postgres -p 5432:5432 ...
postgres service is healthy.
```

— e `Initialize containers` fica verde. Mas **o healthcheck roda DENTRO do container**
(`pg_isready` no próprio Postgres). Ele prova que o banco subiu; não prova **nada** sobre o job
conseguir alcançá-lo.

### Duas hipóteses plausíveis que custam rodadas — e são falsas

**"`localhost` resolve para `::1` e o Docker publicou só IPv4."** Verificável em um `grep`: o log do
runner imprime o mapeamento. Se disser

```
5432/tcp -> 0.0.0.0:5432
5432/tcp -> [::]:5432
```

as duas famílias estão publicadas e trocar `localhost` por `127.0.0.1` não muda nada.

**"É só declarar `container:` no job."** Direcionalmente certo (põe o job na rede dos services, onde
o alias `postgres` resolve) mas depende do runner — ver §3.

### A causa real: o runner pode estar dentro de um container

Se o runner roda conteinerizado (comum — é o próprio blueprint da `self-hosted-runner-docker.md`),
então `docker create -p 5432:5432` publica a porta no **host**, enquanto `127.0.0.1` dentro do job é
o loopback **do runner**. Os dois nunca se encontram. O caminho é o **gateway do bridge**.

### Descubra em vez de supor

Este é o ponto da seção. Você geralmente **não tem SSH para o host do runner** — então o job é o
único instrumento de medição disponível. Faça-o reportar o ambiente e escolher o host sozinho:

```yaml
- name: Descobre como alcancar o Postgres
  shell: bash
  run: |
    # `ip` costuma NÃO existir no container do runner; o gateway sai de
    # /proc/net/route (hex little-endian). `strtonum` é extensão do gawk e o
    # Debian traz mawk, então a conversão vai no printf do bash.
    gw=""
    if [ -r /proc/net/route ]; then
      hex=$(awk '$1 != "Iface" && $2 == "00000000" { print $3; exit }' /proc/net/route)
      [ -n "$hex" ] && gw=$(printf '%d.%d.%d.%d' "0x${hex:6:2}" "0x${hex:4:2}" "0x${hex:2:2}" "0x${hex:0:2}")
    fi
    for i in $(seq 1 30); do
      for h in "$gw" 127.0.0.1 host.docker.internal postgres; do
        [ -z "$h" ] && continue
        if (echo > /dev/tcp/"$h"/5432) 2>/dev/null; then
          echo "postgres alcancavel em $h:5432"
          echo "DATABASE_URL=postgres://u:p@$h:5432/test_db" >> "$GITHUB_ENV"
          exit 0
        fi
      done
      sleep 2
    done
    echo "::error::Postgres inalcancavel em todos os candidatos"
    echo "hostname=$(hostname)"
    if [ -f /.dockerenv ]; then echo "job roda DENTRO de container"; else echo "job roda no HOST"; fi
    cat /proc/net/route 2>/dev/null || echo "(ilegivel)"
    exit 1
```

Os demais steps deixam de declarar `DATABASE_URL` — ele vem do `$GITHUB_ENV`. A ordem dos
candidatos cobre as três topologias (runner no host, runner em container, job em container), então
o mesmo workflow serve para as três sem você saber de antemão qual é.

**O bloco de diagnóstico é a parte que paga.** Numa medição real, `hostname=eb386592c048` +
`/.dockerenv` presente respondeu em uma execução o que três hipóteses não tinham respondido.

⚠️ **Cuidado com `2>/dev/null` em sonda de diagnóstico.** Uma primeira versão desse step fazia
`ss -ltn 2>/dev/null | grep 5432` e imprimiu **nada** — o que se lê como "nenhuma porta escutando",
mas era `ss: command not found` engolido pelo redirect. Sonda que pode não existir merece
`command -v` antes, ou a mensagem de erro visível.

---

## §3. `container:` não é a saída se o runner estiver desatualizado

```
OCI runtime exec failed: exec failed: unable to start container process:
exec: "/__e/node24/bin/node": stat /__e/node24/bin/node: no such file or directory
```

**O que está acontecendo:** quando o job declara `container:`, o GitHub monta os `externals` do
runner dentro dele em `/__e` e executa as actions JavaScript com **o Node do runner**. Como o
GitHub força as actions para Node 24, um runner antigo — que só traz `node16`/`node20` — não tem o
binário pedido. O `actions/checkout` **nem chega a rodar**.

**Assinatura de isolamento:** o mesmo workflow funciona **sem** `container:` no mesmo runner. Se
tirar o `container:` conserta, é versão de runner, não rede.

**Fixes, na ordem:**

1. **Atualizar o runner** (correção de verdade; é manutenção de host).
2. **Não usar `container:`** — resolva a rede pelo §2, que não depende da versão do runner.
3. `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION=true` força as actions para Node 20. Desbloqueia, mas é
   band-aid num caminho que o GitHub está removendo — só como ponte até (1).

Aviso relacionado: a linha `Node.js 20 is deprecated … being forced to run on Node.js 24` aparece
como **warning** em execuções que passam. Num runner desatualizado ela é o aviso prévio de (3).

---

## §4. Workspace sujo entre execuções

O runner reaproveita o diretório de trabalho, e um `.git` corrompido de execução anterior derruba o
`checkout` com `fatal: missing blob object`. O job de `deploy` de um blueprint self-hosted
normalmente já carrega o guard; ao **migrar** outros jobs, replique-o como primeiro step de cada um:

```yaml
- name: Clean self-hosted workspace
  shell: bash
  run: |
    if [ -d "${{ github.workspace }}/.git" ]; then
      rm -rf "${{ github.workspace }}/.git"
    fi
```

---

## §5. Como confirmar que a migração pegou

```bash
gh api "/repos/<o>/<r>/actions/runs/<id>/jobs" \
  -q '.jobs[] | [.name, .runner_name, .runner_group_name, .conclusion] | @tsv'
```

- `runner_name` preenchido com o seu runner = rodou onde devia, custo zero.
- `runner_name` **vazio** + **zero steps** + duração de ~3s = **não é falha de código**; é bloqueio
  de cota/cobrança. Ver `ci-cost-minutes.md` §5.

---

## §5b. Produção: qual runner — e quando a mudança passa a valer

A alavanca da §3a foi puxada no `cd-staging.yml` e o job ficou verde. Agora o `cd-production.yml`,
disparado por **tag**, ainda está em `ubuntu-latest` — e sob bloqueio de cota (§5 da
`ci-cost-minutes.md`) ele vai falhar **no dia da release**, o momento de menor tolerância a surpresa.
Duas perguntas que a §3a não responde:

**Em qual runner?** O reflexo é `[self-hosted, production]`, espelhando o `deploy`. Mas o runner de
produção costuma ser de **organização** — este repositório não consegue nem listá-lo
(`gh api repos/<o>/<r>/actions/runners` só mostra os de repositório; `orgs/<o>/actions/runners`
devolve `403` sem `admin:org`) — e você não sabe se ele tem Docker para o `services:`, `buildx`
para o push, ou `yarn`. Estreá-lo na tag é repetir as quatro rodadas da §6 com produção esperando.

Rode `ci` e `build-and-push` no runner **já provado** — o de staging, que executou exatamente esses
jobs no `cd-staging` — e deixe **só o `deploy`** no runner do ambiente. Nada de produção depende de
onde a imagem foi construída: ela vai para o GHCR, e o host de produção só puxa. Copie o job `ci`
inteiro do `cd-staging.yml` e confira com `diff` (ignorando comentários) que ficou byte-idêntico;
no `build-and-push` só as tags da imagem mudam.

```bash
diff <(sed -n '/^  ci:/,/^  build-and-push:/p' .github/workflows/cd-staging.yml    | grep -v '^\s*#') \
     <(sed -n '/^  ci:/,/^  build-and-push:/p' .github/workflows/cd-production.yml | grep -v '^\s*#') \
  && echo "job ci identico"
```

Os grupos de `concurrency` continuam separados (`deploy-staging-*` × `deploy-production-*`); o único
custo é uma release enfileirar atrás de um CI de staging se coincidirem.

**Quando passa a valer?** O GitHub executa o arquivo de workflow **do commit que dispara o evento**.
Para `push` de branch isso é o próprio push (a migração do `cd-staging` vale já no merge que a
traz). Para `tag`, é o commit **taggeado**: a migração precisa estar mesclada na branch de onde a
tag é cortada, *antes* da tag. E não há como ensaiar sem taggear — a evidência aceitável é o
workflow irmão verde com jobs byte-idênticos, mais o CI do PR que trouxe a mudança.

---

## §6. A migração desvenda a dívida do repositório — e o primeiro verde não está a um passo

Tudo acima parte do mesmo modelo: **o job quebra porque falta algo no runner**. Existe outra classe
de falha, e ela aparece justamente quando a migração dá certo.

Medido numa migração real: o runner pegou o job de primeira e o `Type Check` ficou verde em 2m17s.
O que estava vermelho era **o repositório** — 5 testes e 1 erro de ESLint que entraram enquanto o
Actions hospedado estava bloqueado por cota. A aritmética é desconfortável: um CI bloqueado não
reprova nada (§5 e `ci-cost-minutes.md` §5), mas os merges continuaram acontecendo. Quanto mais
tempo durou o bloqueio, mais vermelho se acumulou — e a migração é o que revela tudo de uma vez, no
PR que só queria trocar `runs-on`.

**Triagem: dois PRs, não um.** Deixe o PR de pipeline ser só pipeline. Ele vai ficar vermelho, e
isso é honesto: ele *revela* a dívida, não a criou. Abra um segundo PR para os defeitos. Duas
razões práticas — o histórico fica legível depois ("quem quebrou isto" não vira "quem mexeu no
runner"), e se a correção do defeito for polêmica a mudança de pipeline não afunda junto. Diga a
**ordem de merge** no corpo do PR: o CI do PR de defeitos ainda vai falhar no que o PR de pipeline
conserta.

**Prove que é preexistente antes de afirmar.** Duas medições baratas, nessa ordem:

```bash
git diff origin/<base>...HEAD --stat        # seu PR só tocou .github/workflows/?
git switch --detach origin/<base> && <comando de lint/test>   # reproduz sem a sua mudança?
```

Sem isso a conversa vira "sua migração quebrou o build", e você gasta a rodada seguinte defendendo
a mudança em vez de consertar o repo.

**E não presuma que teste vermelho = código quebrado.** Dos 5 vermelhos aqui, 2 eram defeito real
(uma guarda de segurança dependente de plataforma) e **3 eram setup de teste que contradizia a
própria asserção** — inclusive um assert impossível de satisfazer, porque o `beforeEach` já criava o
registro cuja ausência o teste exigia. A investigação começou supondo defeito de produção e terminou
provando o contrário; o que decidiu foi um teste descartável de 20 linhas imprimindo o estado do
banco logo após o setup, não a leitura do código. Faz sentido: enquanto o CI esteve cego, os testes
introduzidos naquela janela **também nunca executaram** — são tão candidatos a estar errados quanto
o código que cobrem.

---

### §6a. O runner é root — e o teste de permissão para de medir

Um teste que simula falha de disco com `chmod 0o500` e espera o erro **reprova** no runner
self-hosted: o `putObject` passa e o teste recebe `null`. Não é defeito de produção. Um runner
conteinerizado como o `myoung34/github-runner` roda como **root**, e root ignora bit de permissão
(`CAP_DAC_OVERRIDE`). No `ubuntu-latest` o usuário era `runner`, então o teste nunca tinha rodado
num regime em que a premissa dele fosse falsa.

Medido nos dois usuários, com o mesmo script:

| | uid 1001 | uid 0 |
| --- | --- | --- |
| `chmod 0o500` + escrita | `EACCES` | **escreve sem erro** |
| arquivo no lugar do diretório + `mkdir` | `ENOTDIR` | `ENOTDIR` |

**Cura em duas metades, porque cada uma mede uma coisa diferente:**

- O sensor que roda **sempre** usa uma falha que root não contorna. Aponte a raiz do storage para
  um **arquivo**: todo `mkdir` abaixo dela dá `ENOTDIR`. Prefira isso a plantar o arquivo num
  caminho derivado da key, porque drivers costumam guardar o objeto num caminho por hash
  (`<raiz>/<hash[0:2]>/<hash>`) e o teste acoplado ao layout passa a mentir quando ele muda.
- O caso específico de permissão continua, com `it.skipIf(process.getuid?.() === 0)` e o motivo
  escrito no teste. Ele roda nas máquinas de desenvolvimento, que não são root.

**Prove o regime do CI sem esperar o CI:** `docker run --rm -v "$PWD":/repo -w /repo/<pacote>
node:22 npx vitest run <arquivo>` executa como uid 0. Use a imagem Debian, não a Alpine: os
binários nativos do `node_modules` (esbuild, rollup) foram instalados para glibc. Depois saboteie
o embrulho de erro do driver (relançar o erro cru) e confira que o sensor novo reprova **como
root**. Antes de rodar, confirme com `grep` que a sabotagem entrou (ver `cd-verification-and-rollback.md` §6a).

Para achar os outros casos de uma vez: `grep -rln "chmod\|getuid\|EACCES\|EPERM"` nos arquivos
de teste. Um acerto que é só comentário não conta.

### §6b. O timeout default do test runner foi calibrado para a máquina de desenvolvimento

No mesmo primeiro run, o gate do frontend reprovou por **timeout**: uma varredura de ~1500
arquivos versionados levou **11,5 s** contra o default de 5 s do vitest. Na máquina de
desenvolvimento, o arquivo inteiro leva 0,5 s. O host self-hosted típico é compartilhado com
outros serviços, tem poucas CPUs e guarda o `_work` num volume nomeado, e a suíte paralela disputa
o I/O. A lentidão não é uniforme: I/O sofreu 25×, CPU bem menos.

Não conserte só o caso que reprovou, porque os vizinhos estão logo atrás. Liste do log os casos
**individuais** perto do limite. As linhas de arquivo mostram totais e enganam: o limite é por caso.

```bash
gh api repos/<o>/<r>/actions/jobs/<job_id>/logs | sed 's/\x1b\[[0-9;]*m//g' \
  | grep -E 'Z {3,}[✓×] .* [0-9]+ms$' | sed -E 's/^\S+ +//' \
  | awk '{n=$NF; sub(/ms$/,"",n); if (n+0>=2000) print n"ms", $0}' | sort -rn | head
```

Medido: um caso reprovado (11,5 s) e **uma dúzia entre 2,3 e 4,5 s**. O pior deles estava a 90% do
limite.

- **Timeout global com folga sobre o pior medido** (`testTimeout: 15_000`, 3× os 4,5 s), com o
  motivo escrito na config. Sem o porquê, a próxima pessoa "arruma" de volta para o default.
- **Timeout próprio para a varredura de I/O** (`it(..., fn, 60_000)`). O limite dela é da natureza
  do teste, não do default da suíte.
- **Prove que a config vale:** uma sonda descartável com `await new Promise(r => setTimeout(r,
  7000))` tem de **passar** com a config e dar timeout com `--testTimeout=5000`. Sem os dois
  estados, um `testTimeout` digitado no bloco errado do config passa despercebido.

O teto não esconde teste travado: 15 s ainda é rápido para acusar um `await` que nunca resolve.

**E há um segundo timeout, que o `testTimeout` não toca.** O `waitFor`/`findBy*` do Testing
Library desiste em **1 s** por padrão (`asyncUtilTimeout`), independente do limite do caso. No
segundo run, com o `testTimeout` já em 15 s, reprovou outro caso: `Found multiple elements with the
text of: Valor unitário`. O DOM tinha **duas** linhas de item, porque a animação de saída do
`AnimatePresence` mantém o elemento que sai até terminar, e no host compartilhado ela passou de 1 s.
No primeiro run o mesmo caso tinha passado: é sensível a tempo. A cura é
`configure({ asyncUtilTimeout: 5_000 })` no setup global, com o motivo escrito.

- **Reproduza de forma determinística encolhendo o timeout, não tentando deixar a máquina lenta.**
  Uma config temporária que estende a real (`mergeConfig(base, { test: { setupFiles: [...] } })`)
  com um setup que faz `configure({ asyncUtilTimeout: 30 })` reproduziu o erro idêntico ao do CI
  2 de 2 vezes numa máquina rápida. Confirme que a sonda entrou (um `console.log` no setup extra),
  porque o CLI do vitest **não** aceita `--setupFiles` e a sonda silenciosa só parece rodar.
- **`taskset -c 0` não discrimina essa classe.** Com 1 CPU, o caso isolado **passou** sem a correção
  (3 de 3): a falha depende da contenção da suíte paralela inteira, não da CPU lenta. Uma suíte verde
  sob `taskset` é evidência fraca, e não serve como sensor.
- Prove a config nos dois estados: um `waitFor` que só resolve após 2 s tem de passar com o setup
  e falhar com `configure({ asyncUtilTimeout: 1000 })`.

## §7. Sem `.env` no CI, um módulo que faz `throw` no import derruba a suíte inteira

O `.env` é gitignored — corretamente — então o checkout do CI não tem nenhum. Se algum módulo faz
`throw` no **nível do módulo** quando falta uma variável, a falha não é "1 teste falhou": é todo
arquivo de teste que o importa transitivamente morrendo no import.

```
Error: [PortModel] Missing required environment variable VITE_API_URL.
 ❯ src/models/PortModel.ts:3:9
```

A assinatura que economiza tempo: **o mesmo erro repetido em arquivos de teste sem relação entre
si, nomeando um módulo em vez de um teste**. Aqui eram 9 módulos e centenas de linhas idênticas.

Fix — `env` no nível do job:

```yaml
  test:
    runs-on: [self-hosted, staging]
    env:
      VITE_API_URL: http://localhost:3003
      VITE_GOOGLE_CLIENT_ID: ci-placeholder
```

⚠️ Nem todo valor é livre — ver §8.

Por que isso não aparecia antes: **esta classe não é específica de self-hosted**; falharia igual em
`ubuntu-latest`. Ela surge *no momento da migração* porque é quando os testes voltam a rodar de
verdade.

**Descubra a lista completa de uma vez**, em vez de uma rodada de CI por variável:

```bash
grep -rhoP "Missing required environment variable \K[A-Z_]+" src/ | sort -u
# ou reproduza o ambiente do CI localmente:
mv .env .env.bak && npx vitest run; mv .env.bak .env
```

A execução local custa segundos; cada rodada de CI custa minutos, um push e a sua atenção.

---

## §8. Snapshot que grava valor de ambiente força o CI a reproduzir o valor EXATO

Depois do §7 a suíte parou de explodir — e 2 testes de snapshot continuaram falhando, com
`Snapshot ... mismatched`, mensagem que não diz absolutamente nada sobre ambiente.

Causa: o componente renderiza um `href` a partir de `import.meta.env.VITE_*`, e o `.snap`
**versionado** guardou o valor renderizado. Qualquer outro valor falha a comparação. Ou seja: essas
variáveis **não** são placeholder livre como as do §7 — elas têm exatamente um valor aceitável, e
ele está no `.snap`.

Como descobrir em um comando, em vez de por eliminação:

```bash
grep -oP 'href="\K[^"]*' src/**/__snapshots__/*.snap | sort -u   # compare com o .env
```

Duas saídas, e vale dizer qual você escolheu: **injetar os mesmos valores do `.snap`** (rápido,
mantém o acoplamento) ou **desacoplar o componente do env no teste** (mock/fixture; remove a
classe). Qualquer que seja, deixe um comentário no bloco `env` dizendo que o valor está amarrado ao
`.snap` — senão a próxima pessoa "limpa o placeholder" e quebra o CI sem encostar no teste.

---

## §9. Job de GATE muda de natureza ao migrar — o que vigia o runner não pode rodar nele

Esta é traiçoeira porque a mudança de YAML é idêntica à de qualquer outro job, e o job **continua
passando**. O que mudou foi o que o verde dele significa.

Um `preflight` que barra o deploy quando não há runner com o label X online (lição 51) existe para
transformar um `queued` silencioso em falha rápida. Mova-o para `[self-hosted, X]` e ele fica
**tautológico**: com o runner offline, o próprio preflight fica `queued` — exatamente o silêncio que
ele foi escrito para quebrar.

O que decide é **qual runner vigia qual**:

| Gate | Roda em | Vigia | Sobrevive à migração? |
| ---- | ------- | ----- | --------------------- |
| preflight de staging | `[self-hosted, staging]` | label `staging` | ❌ tautológico — perde o fail-fast |
| preflight de produção | `[self-hosted, staging]` | label `production` | ✅ máquinas diferentes, fail-fast intacto |
| preflight de staging | `ubuntu-latest`, **fora** do `needs:` | label `staging` | ⚠️ vigia de fora e deixa o run vermelho, mas **não barra**; sob bloqueio de cota fica vermelho com o deploy verde |
| watchdog agendado (lição 51) | `ubuntu-latest` | qualquer label | ✅ — e por isso **fica** no hospedado |

A terceira linha é a opção que a lista original não tinha, e foi a escolhida num caso real. Com
gates e builds já no self-hosted, o preflight hospedado **no** `needs:` faria o bloqueio de cota
matar o CD inteiro de novo. Levado para o self-hosted, ficaria tautológico. Fora do `needs:`, ele
continua transformando "sem runner" em run vermelho, e não barrar nada custa pouco: sem runner, o
`deploy` também não roda. Sob bloqueio, o vermelho dele é verdadeiro (o vigia não conseguiu
vigiar), e o comentário do job precisa dizer isso para ninguém ler o run como deploy quebrado.

O watchdog é o que **não** deve migrar, nem sob bloqueio de cota. Sob bloqueio ele está morto — mas
alarme morto é melhor que alarme verde que não enxerga, e ele é o que sobra da camada de detecção
quando o preflight do deploy perde o fail-fast.

Na prática, migrar o preflight de staging costuma **ainda** ser a decisão certa: com o `ci` e o
`build-and-push` bloqueados por cota, deixá-lo no hospedado faz o CD inteiro morrer antes do
`deploy` (ele é `needs:` dele). Só não deixe o arquivo afirmando algo que ele não faz mais — o
comentário no job é o único lugar onde a próxima pessoa vai ler o que aquele gate ainda garante.

---

## §10. A lição que generaliza

Foram **quatro rodadas de CI gastas em hipóteses lidas do YAML** (IPv6, `container:`, ordem dos
candidatos) contra **uma** que respondeu: a que fez o job descrever o próprio ambiente.

Quando o runner é uma caixa-preta — sem SSH, sem `docker exec`, sem saber se é host ou container —
**o job é o instrumento de medição**. Um step que imprime `hostname`, `/.dockerenv`, rotas e o
resultado de cada candidato custa segundos e substitui uma rodada inteira de adivinhação.

Faça isso **na primeira falha**, não depois do terceiro palpite.

---

## §11. Build de imagem no self-hosted: tire o `setup-buildx` e o cache `gha`

O `build-and-push` do blueprint hospedado faz `docker/setup-buildx-action` e passa
`cache-from/to: type=gha`. Copiado tal qual para o runner self-hosted, os dois viram peso morto ou
risco:

- **`setup-buildx-action` cria um builder `docker-container` descartável** a cada job. O cache de
  camadas dele morre com o job, e é exatamente o que o host persistente teria de graça. Um runner
  que já traz `docker-ce-cli` com o plugin `buildx` tem o builder `default` (driver `docker`).
  Confira com `docker buildx ls` de dentro do runner e deixe o `build-push-action` usá-lo.
- **`type=gha` não é suportado pelo driver `docker`, e depende da API de cache do Actions**, a
  mesma infraestrutura que um bloqueio de cota derruba (`ci-cost-minutes.md` §5). Migrar para
  sobreviver ao bloqueio e manter o cache nela seria trocar uma dependência por outra.

O custo aparece no disco do host: o cache de camadas passa a crescer a cada deploy, num host que já
serve outros projetos (medido: 84% de disco e 6,4 GB de build cache parado **antes** da migração).
Limite com um prune por idade no job de deploy, depois do `image prune`:

```yaml
- name: Prune imagens órfãs e cache de build
  if: always()
  run: |
    docker image prune -f
    docker builder prune -f --filter until=168h
```

`until=168h` preserva o que a última semana usou, que é o que deixa o próximo build rápido. Um
`--all` ou um teto de tamanho seriam mais agressivos, e o cache é do **daemon**, compartilhado com
os outros projetos do host.

Onde um gate de CI e o `build-and-push` passam a disputar um runner único, **eles serializam**
(tabela do pré-voo, item 6). Um runner efêmero ainda se registra de novo entre jobs. Diga o novo
tempo de CD em voz alta no PR, para ninguém ler a lentidão como regressão.

