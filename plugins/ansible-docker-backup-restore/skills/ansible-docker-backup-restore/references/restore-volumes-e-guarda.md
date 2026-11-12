# Volumes: nome de projeto, a guarda anti-sobrescrita e montagens

Abra antes de escrever em qualquer volume ou subir qualquer compose. É o arquivo
mais denso da skill porque é onde mora o código que decide se dado de produção
sobrevive.


## Sumário

- [§1. A armadilha nº 1: nome de projeto compose](#1-a-armadilha-nº-1-nome-de-projeto-compose)
- [§2. A guarda anti-sobrescrita](#2-a-guarda-anti-sobrescrita)
- [§3. O formato do tar não é o que a extensão diz](#3-o-formato-do-tar-não-é-o-que-a-extensão-diz)
- [§4. Volume pré-populado e o entrypoint da imagem](#4-volume-pré-populado-e-o-entrypoint-da-imagem) — inclui a config efetiva fora do volume
- [§5. Bind mount de arquivo único](#5-bind-mount-de-arquivo-único)
- [§6. Volume criado fora do Compose](#6-volume-criado-fora-do-compose)
- [§7. Restore isolado (teste de DR)](#7-restore-isolado-teste-de-dr-origem-e-destino-com-nomes-diferentes) — inclui o pré-staging sem SSH e a trava de isolamento

---

## 1. A armadilha nº 1: nome de projeto compose

> Se você ler só uma seção deste arquivo, leia esta. É a falha mais perigosa
> porque é **silenciosa**.

O Docker Compose deriva o nome do projeto do **basename do diretório**, e volumes
nomeados levam esse nome como prefixo:

```
projeto "<projeto>" + volume "app"  →  volume real: <projeto>_app
```

Se o nome do projeto sair errado, o Compose cria um volume **novo e vazio**, os
containers sobem **sem erro nenhum**, e o serviço parece restaurado com o banco
zerado. Ninguém descobre até um usuário abrir o sistema.

### Regra

**Sempre passe `compose_project` explicitamente, derivado do PREFIXO DO VOLUME
existente — nunca do nome da pasta.**

```bash
ssh <user>@<servidor> 'sudo docker volume ls --format "{{.Name}}"'
```

### Formatos de engano já vistos

| Padrão | Por que engana |
|---|---|
| Volume `<x>_app` onde `<x>` é curto e genérico | O serviço é conhecido por um nome mais longo; o diretório tem o nome longo, o volume tem o curto |
| Volume com grafia diferente da dos containers | O volume usa a grafia britânica de uma palavra e os containers a americana (ou vice-versa) — o prefixo tem que casar com o **volume** |
| Dois serviços diferentes com compose em pastas de mesmo nome | Ambos derivam o mesmo projeto e colidem. Num caso real, `--remove-orphans` teria apagado uma API de produção |

Nomes genéricos a **nunca** usar como projeto: `infra`, `docker`, `compose`,
`nodejs`, `postgres`, `app`, `web`, `db`.

### O mesmo problema, na camada de rede

A **service key** do compose também vira alias DNS do container na rede. Numa
rede compartilhada por vários projetos, uma service key genérica faz o alias
apontar para **mais de um container**, e o DNS embutido do Docker devolve os dois
em rodízio.

Caso real: o alias `db` pertencia simultaneamente a um MySQL e a um Postgres de
serviços diferentes. Qualquer aplicação configurada com `DB_HOST=db` conectaria
ora num, ora no outro — falha intermitente, sem padrão óbvio.

```bash
# Quem carrega um dado alias na rede?
docker network inspect <rede> -f '{{range .Containers}}{{.Name}}{{"\n"}}{{end}}' | while read c; do
  [ -z "$c" ] && continue
  al=$(docker inspect "$c" -f '{{range $k,$v := .NetworkSettings.Networks}}{{if eq $k "<rede>"}}{{range $v.Aliases}}{{.}} {{end}}{{end}}{{end}}')
  case " $al " in *" db "*) echo "alias db => $c";; esac
done
```

Faça a service key igual ao `container_name`. Renomeá-la depois exige
`docker compose -p <projeto> down` (sem `-v`) antes do `up`, porque o
`container_name` fica tomado pelo container antigo e `--remove-orphans` é
proibido (regra inviolável 1).

### Validação obrigatória

```bash
# ANTES
sudo docker volume ls --format '{{.Name}}' | sort > /tmp/vols-antes.txt
# ... rodar o playbook ...
# DEPOIS
sudo docker volume ls --format '{{.Name}}' | sort | diff /tmp/vols-antes.txt -
```

**Qualquer volume novo é falha.** Exceção conhecida: volumes **anônimos** (nome
em hash) que a imagem declara via `VOLUME` para diretórios como
`/docker-entrypoint-initdb.d` — ficam vazios e são inofensivos, mas acumulam um
par a cada recriação.

Confirme também a montagem real:

```bash
sudo docker inspect <container> --format '{{range .Mounts}}{{.Name}} -> {{.Destination}}{{println}}{{end}}'
```

---

## 2. A guarda anti-sobrescrita

O código que decide se dados de produção sobrevivem. **Ordem correta, validada em
três rodadas de revisão** — a implementação comentada está em
`assets/restore-volume-guard.yml`:

```
1. Guardas fail-closed  →  2. Snapshot  →  3. Validar snapshot em disco
→  4. Buscar e VALIDAR o tar de substituição  →  5. Asserções de mountpoint
→  6. Checar container em uso  →  7. Limpar  →  8. Extrair
```

### 2.1 `ansible.builtin.find` NÃO falha em caminho ilegível

**Bug crítico real.** Em caminho inexistente ou sem permissão, o módulo devolve
`files: []` com apenas um *warning*. Uma guarda que decide por
`files | length == 0` lê isso como **"volume vazio, pode sobrescrever"** e pula
o snapshot obrigatório.

Falhe fechado nos três pontos:

```yaml
- name: "[volumes] Abortar se o mountpoint não foi resolvido"
  ansible.builtin.fail:
    msg: "docker volume inspect devolveu caminho vazio para {{ vol }}"
  when: (vol_mp.stdout | trim) | length == 0

- name: "[volumes] Conferir o mountpoint"
  ansible.builtin.stat:
    path: "{{ vol_mp.stdout | trim }}"
  register: mp_stat

- name: "[volumes] Abortar se o mountpoint não existe ou não é diretório"
  ansible.builtin.fail:
    msg: "Mountpoint de {{ vol }} não existe ou não é diretório"
  when: not (mp_stat.stat.exists and mp_stat.stat.isdir)

# depois do find:
- name: "[volumes] Abortar se algum caminho foi pulado (ilegível)"
  ansible.builtin.fail:
    msg: "find pulou caminhos em {{ vol }}: {{ vol_content.skipped_paths }}"
  when: vol_content.skipped_paths | default({}) | length > 0
```

O `find` precisa de `hidden: true` e `file_type: any` — senão um volume contendo
só um dotfile, ou só um subdiretório vazio, é lido como vazio.

### 2.2 Ordem importa: nunca limpe antes de ter o substituto

**Bug crítico real.** A limpeza rodava antes de buscar o tar do host de backup.
Um `rsync` que falhasse — falha que a própria mensagem de erro do código
antecipava — **apagaria o volume e só então descobriria que não havia backup
para pôr no lugar**.

Busque e valide (`tar -tf`) o tar de substituição **antes** de qualquer deleção.

### 2.3 `force_restore` substitui, não mescla

Extrair por cima mistura arquivos de duas épocas. Num datadir de Postgres ou
MySQL isso produz um híbrido corrompido, pior que qualquer um dos dois estados
isolados. Limpe antes de extrair — **mas só** com todas estas travas:

1. snapshot gravado e **verificado em disco** (`stat` + `tar -tf`), não apenas
   "a task retornou ok";
2. mountpoint passa em asserções: string não vazia, sob
   `/var/lib/docker/volumes/`, e o nome do volume aparece como componente do
   caminho;
3. **nenhum container em execução usando o volume** —
   `docker ps -q --filter volume=<vol>` vazio. Apagar arquivos abertos por um
   Postgres vivo corrompe o banco de forma pior que qualquer estado anterior;
4. deleção do **conteúdo**, não do diretório:
   `find <mountpoint> -mindepth 1 -delete`. Nunca `docker volume rm` — pode
   haver container segurando.

Existe uma janela de corrida inerente entre os passos 3 e 4. Documente-a no
código.

### 2.4 Teste a guarda em volume descartável

Antes de apontar para qualquer volume real, prove os cenários:

| Cenário | Resultado esperado |
|---|---|
| Volume com dados, sem `force_restore` | Preserva; **não** extrai |
| Volume com dados, com `force_restore` | Extrai, **e o snapshot contém a sentinela anterior** |
| Volume só com dotfile | Tratado como **não** vazio |
| Volume só com subdiretório vazio | Tratado como **não** vazio |
| Mountpoint ausente ou ilegível | **Aborta** |
| Container em uso | **Aborta** nomeando o container |

**A asserção precisa discriminar.** "O arquivo do backup está lá" passa igual sob
mesclagem e sob substituição — asserte também que **o arquivo antigo sumiu**. E
abra o snapshot com `tar -tf` para provar que ele contém o estado *anterior*.

---

## 3. O formato do tar não é o que a extensão diz

A rotina de backup desta skill produz tars POSIX com entradas `./` na raiz —
extraia com `tar -xf`, sem `-z` e sem `--strip-components` (regra inviolável 6).

Mas tar vindo de **outro produtor** pode ser diferente, e a extensão mente:

```bash
file <arquivo>.tar        # pode dizer "gzip compressed data" apesar do .tar
tar -tf <arquivo>.tar | head -5   # as entradas começam com ./ ou com um prefixo?
```

Se o tar tem tudo sob um diretório-prefixo, ele **não** pode ser entregue a uma
guarda que extrai sem strip: o conteúdo cairia um nível abaixo do esperado.
Re-enraíze antes, e faça isso numa máquina de trabalho, não no servidor de
produção (são duas cópias do tamanho do dado em disco temporário):

```bash
tar -xf origem.tar -C stage/            # vira stage/<prefixo>/...
tar -cf destino.tar -C stage/<prefixo> .  # agora './'-rooted, como a guarda espera
tar -tf destino.tar | head -3           # confirme que começa com ./
```

## 4. Volume pré-populado e o entrypoint da imagem

Antes de montar um volume já cheio numa imagem oficial, **leia o entrypoint
dela**. Ele decide o que fazer com o diretório e a lógica costuma ser
condicional a marcadores de "já instalado".

Caso real: uma imagem popular tem todo o bloco de instalação sob
`if [ ! -e <marcador_a> ] && [ ! -e <marcador_b> ]`. Com o volume populado, o
bloco inteiro é pulado — o que é bom (não sobrescreve o conteúdo, não reescreve
a configuração) e ruim: **o `chown` também está lá dentro e não roda**. Se o tar
foi gerado por um usuário diferente, a aplicação sobe sem permissão de escrita e
falha de formas que não apontam para permissão.

Corolário: depois de restaurar um volume de aplicação, ajuste dono e modos
explicitamente, e só então considere o serviço no ar.

### A config efetiva pode não ser a do volume

Em muitas aplicações a variável de ambiente do container vence o arquivo de config (no
Laravel, env real vence o `.env`; conferido no app restaurado: o `config('app.key')` era o
da env, não o do `.env`). O volume restaurado traz o arquivo, não a env. Medido em
2026-11-12: o `APP_KEY` do `.env` dentro do volume de uma aplicação Laravel era uma chave
antiga, e a produção rodava com a do compose. Um restore pelo `.env` subiria com a chave
errada, e o que foi cifrado com a de produção (MFA, sessões) não decifraria.

Antes de restaurar, compare **por hash** (nunca imprima o valor) cada segredo da env do
container com o do arquivo no volume. Onde divergir, a fonte é o compose, e ele precisa estar
no backup: confira o membro no tar.

O caminho inverso também engana: **estado na camada do container não vai para o backup de
volumes.** Na mesma imagem, só cache e sessões apontavam para o volume, e o marcador de
manutenção do Laravel (`storage/framework/down`) ficava na camada do container. A aplicação
restaurada subiu servindo, com a origem em manutenção. Liste o volume (`tar -tf`) antes de
supor que um estado foi junto.

## 5. Bind mount de arquivo único

Duas armadilhas, ambas silenciosas:

1. **Se o arquivo não existe no host, o Docker cria um DIRETÓRIO com aquele
   nome** e monta o diretório. A aplicação passa a ver um "arquivo" de
   configuração que é uma pasta. Antes do `up`, faça `stat` + asserção de que é
   arquivo regular.
2. **Bind de arquivo é preso ao inode.** Módulos que escrevem num temporário e
   renomeiam (`ansible.builtin.copy` entre eles) trocam o inode, e o container em
   execução continua vendo o conteúdo antigo. Alterar o arquivo exige **recriar**
   o container, não reiniciá-lo.

## 6. Volume criado fora do Compose

Se a guarda cria e popula o volume antes do `up`, declare-o no compose com
`name:` explícito e `external: true`. Sem `external`, o Compose valida o volume
pré-existente contra a própria declaração e recusa um volume que ele não criou
(faltam os labels `com.docker.compose.*`). De quebra, `external` impede que um
`docker compose down -v` acidental apague o dado.

## 7. Restore isolado (teste de DR): origem e destino com nomes diferentes

A guarda costuma usar **um** nome para duas coisas: o volume Docker e o tar
(`<vol>_<data>.tar`). Num restore de teste em outro host, o destino não pode ter o
nome da origem: colide com o que já roda lá, e a limpeza do teste precisa achar só os
volumes dele. Separe as duas variáveis:

- `vol` continua sendo a **origem**: só ela compõe o caminho do tar, no staging e no
  host de backup;
- o **destino** é `vol_alvo` = `<prefixo>` ~ `vol` (ex.: `drtest-<stack>_`), e é ele
  que vai em **toda** operação sobre o volume: `docker volume inspect`/`create`, o
  mountpoint, o nome do snapshot, a asserção de mountpoint seguro e o
  `docker ps --filter volume=`.

Com prefixo vazio como padrão, o comportamento é idêntico ao de antes. Prove as duas
pontas (medido em 2026-11-12, com `docker` falso e o tar real, e depois com a regressão
da guarda em Docker de verdade): com prefixo, nada é criado nem inspecionado com o nome
de origem; com o destino já populado, a guarda preserva olhando o **destino**. E no
compose da stack de teste o volume entra como `external: true` com `name:` prefixado
(§6).

**Sem SSH entre o host de backup e o de teste.** O fallback rsync da guarda (buscar o tar no
host de backup) não funciona se um não confia no outro. Passe os arquivos pela máquina do
operador, em fluxo (`ssh <backup> cat <arq> | ssh <teste> 'cat > <arq>.part'`), sem gravar nada
no disco local, e só promova o `.part` para o nome final depois de conferir o tamanho contra o
manifesto do conjunto e o sha256 nas duas pontas. A guarda **usa o arquivo do staging se ele
existir**: um arquivo pela metade com o nome final seria restaurado como se fosse o backup.
Arquivo final que já existe e diverge da origem: falhe, não sobrescreva. Teste a conferência
de sha256 com uma corrupção que **mantém o tamanho**; acrescentar um byte deixa a conferência
de tamanho pegar primeiro, e o teste do sha256 passa sem provar nada (medido em 2026-11-12).

**Trave o isolamento da stack de teste na borda.** Dado restaurado é dado de produção. Antes de
copiar qualquer compose de teste, um checker recusa: rede sem `internal: true` (inclusive a
`default`, que o compose cria para serviço sem `networks:`), porta publicada,
`VIRTUAL_HOST`/`LETSENCRYPT_HOST`, bind para caminho do host, `restart` diferente de `"no"` e
projeto, container ou volume sem o prefixo de teste (sem ele, a limpeza não acha só o que é do
teste). Prove o checker com uma cópia sabotada para cada violação.
