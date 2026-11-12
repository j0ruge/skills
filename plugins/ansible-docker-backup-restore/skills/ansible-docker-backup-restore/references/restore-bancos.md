# Importação de dumps SQL

Mesma filosofia da guarda de volumes: **só importa se o banco não tiver dado**, e
isso é decidido por **linhas numa tabela específica** — não por "o banco existe"
nem por "o schema existe".

Motivo real: um ORM criava o schema e as chaves estrangeiras sozinho ao subir.
Uma guarda por presença de schema diria "já tem dado" e o restore nunca
aconteceria.

## 1. Confira o CONTEÚDO do dump antes de assumir nomes

```bash
zcat <dump>.sql.gz | grep -iE "^(CREATE DATABASE|USE )" | head
zcat <dump>.sql.gz | grep -c "^CREATE TABLE"
```

- A documentação dizia que o dump continha duas bases com nomes conhecidos.
  Continha **uma**, com outro nome. Validar contra o nome errado teria reportado
  falha num restore correto.
- Um banco cujo nome citava um produto continha, na verdade, as tabelas de
  **outro** produto — herança de uma stack criada por copia-e-cola.

Repare também na **forma** do dump, porque ela decide o comando de importação:

| Forma | Como se reconhece | Importa com |
|---|---|---|
| `--all-databases` / `--databases` | tem `CREATE DATABASE` e `USE` | `mysql -u… -p…` sem nomear banco |
| schema único | cabeçalho diz `Database: <x>`, **sem** `CREATE DATABASE` | `mysql -u… -p… <banco>` — nomeando |

Entregar um dump de schema único a um comando que não nomeia o banco falha de
formas confusas, ou importa para o banco errado.

## 2. Postgres: importar "por cima" falha em silêncio

`pg_dumpall` pressupõe destino vazio e adiciona as FKs no fim. Se a aplicação já
criou schema e FKs, o `COPY` colide e **várias tabelas ficam vazias com
`rc=0`** — sucesso aparente, dado ausente.

Derrube e recrie o banco (`DROP DATABASE … WITH FORCE`) — **depois** de gravar e
conferir o dump de segurança do estado atual.

## 3. MySQL: a imagem sobe em duas fases

A imagem oficial inicia um servidor temporário de inicialização, encerra, e sobe
o definitivo. Há uma janela de poucos segundos em que nada aceita conexão, e
**`mysqladmin ping` responde para os dois servidores**. Uma checagem que caia
nessa janela aborta por falso positivo.

Use `until`/`retries`/`delay`, tolerando erro de conexão como transitório e
decidindo só em resultado definitivo (`rc == 0`, ou mensagem de tabela
inexistente):

```yaml
until: >-
  (check.rc == 0) or ("doesn't exist" in (check.stderr | default('')))
retries: 10
delay: 3
```

O `mysqladmin ping` mente de outro jeito também: ele sai 0 com `Access denied`, porque o
servidor está vivo. Medido em 2026-11-12: a espera por ping passou, e a consulta seguinte, com
a mesma senha, levou `ERROR 1045`. Quem prova que a credencial entra é a primeira consulta
autenticada, não o ping.

## 4. Senha em volume MySQL pré-populado

`MYSQL_ROOT_PASSWORD` só vale na **primeira** inicialização do datadir. Um volume
restaurado já traz a senha original gravada — o valor no compose precisa apenas
**coincidir** com ela.

Se não coincidir, **não reinicialize o volume** para "consertar": reporte a
divergência. Reinicializar apaga o banco.

## 4b. Banco novo: quem é o root depende do init da imagem

O restore de DR sobe o banco num volume **vazio**, e quem cria os usuários é o init da imagem,
não o backup. Versões diferentes do init da mesma imagem já criaram usuários diferentes.

Medido em 2026-11-12 com `lscr.io/linuxserver/mariadb:11.4.8`, num volume novo:

- o init preserva o `root@localhost` do `mariadb-install-db`, que só entra por `unix_socket`;
  a senha de `MYSQL_ROOT_PASSWORD` vale para `root@'%'`;
- com `skip_name_resolve=0`, até TCP em `127.0.0.1` resolve para `localhost` e cai na conta
  sem senha: `ERROR 1045 Access denied for user 'root'@'localhost' (using password: YES)`, com
  a senha certa;
- `docker exec <banco> mariadb -uroot --protocol=socket` (root do sistema, sem senha) entra.

O banco de origem, criado por um init antigo da mesma imagem, só tinha `root@'%'`, e lá a senha
funcionava. O restore não pode supor que o destino autentica como a origem:

- sonde antes de importar (a senha da env do container entra? o socket entra?) e use o modo
  que funcionar;
- a importação precisa de um modo sem senha, pelo socket, espelho do modo socket que o dump do
  backup costuma ter. Com `-p<senha>` fixo, a guarda aborta fail-closed e parece defeito do dump.

## 5. O datadir também traz o PLUGIN de autenticação dos usuários

O item acima trata da senha. Existe um segundo atributo que viaja junto e que
quase ninguém confere: **o plugin de autenticação de cada usuário**.

Num datadir restaurado num MySQL 8, os usuários costumam vir com
`caching_sha2_password`. Clientes antigos — `DBD::mysql` do Perl, `mysqli`
velho, drivers JDBC antigos — não fecham esse handshake sem TLS, e a conexão é
recusada **com a senha inteiramente correta**:

```
Authentication plugin 'caching_sha2_password' reported error:
Authentication requires secure connection.
```

Duas armadilhas específicas:

**A flag do compose não corrige.** `--default-authentication-plugin=mysql_native_password`
só decide o plugin de usuários criados **depois** dela. Quem veio dentro do
datadir já chegou pronto, com o plugin gravado. A flag estar presente no compose
faz parecer que o assunto está resolvido — e não está.

**O sintoma aparece em um cliente e não no outro.** Caso real: a interface web
de um serviço funcionava normalmente (o driver do PHP fala `caching_sha2`)
enquanto o endpoint que recebe os agentes, em Perl, não conectava. Um serviço
com dois planos de entrada pode ter só um quebrado — e o plano que ficou de pé
esconde o outro. Como a UI abria, o banco parecia saudável e a investigação foi
para o lugar errado.

Confira o plugin, não só a senha:

```sql
select user, host, plugin from mysql.user;
```

Para corrigir, troque **apenas o plugin**, preservando a mesma senha — não
invente uma nova, e não reinicialize nada:

```
ALTER USER '<usuario>'@'%' IDENTIFIED WITH mysql_native_password BY <a MESMA senha>
```

Passe o valor por *stdin* do cliente `mysql`, não em `argv`, para não expô-lo no
`ps` do host. E antes de alterar qualquer coisa: **confirme de onde a aplicação
lê o usuário e a senha**. Num caso real o usuário efetivo não era o declarado no
arquivo principal de configuração — outro arquivo, carregado depois na ordem
alfabética do diretório de configs, sobrescrevia a variável. Corrigir a
credencial do usuário errado não produz erro nenhum: só continua sem funcionar.

## 5b. `--all-databases` traz os usuários de produção

O dump `--all-databases` leva o schema `mysql`, e com ele os usuários e as senhas da origem. O
import troca as tabelas de grants, e o servidor segue com os grants da memória até
`FLUSH PRIVILEGES` ou um restart. Medido num restore de teste em 2026-11-12:

1. **O usuário da aplicação só passa a existir para o servidor depois do `FLUSH`.** Rode o
   `FLUSH` entre o import e a subida da aplicação.
2. **Depois do `FLUSH`, o root do restore não entra mais:** valem as contas da origem (no caso
   medido, só `root@'%'` com a senha de produção). O socket sem senha e a senha do restore
   levaram `ERROR 1045`. Uma segunda execução do restore bateria na guarda. Torne a
   reexecução idempotente: se o usuário da aplicação já lê a tabela de checagem com dado, pule
   o import e o `FLUSH`.
3. **Conte pelo usuário da aplicação, depois do `FLUSH`.** É o que a aplicação enxerga, e é a
   conta que continua entrando.

## 6. Sempre reconfira depois de importar

Conte as linhas da tabela de checagem **de novo**, depois do import, e aborte se
continuar zero. Um import que devolve `rc=0` e deixa a tabela vazia é
exatamente o modo de falha do item 2 — e é indistinguível de sucesso sem essa
segunda contagem.

Guarde o dump de segurança do estado anterior antes de qualquer import
destrutivo, e cite o caminho dele na mensagem de erro: quem estiver lendo o
aborto às três da manhã precisa saber para onde correr.
