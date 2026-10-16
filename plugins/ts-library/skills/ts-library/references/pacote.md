# O pacote: `package.json` e `tsconfig`

## Manifesto anotado

```json
{
  "name": "@org/object-storage",
  "version": "1.0.0",
  "private": true,
  "license": "UNLICENSED",
  "type": "module",
  "engines": { "node": ">=22" },
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "default": "./dist/index.js"
    },
    "./testing": {
      "types": "./dist/testing/index.d.ts",
      "default": "./dist/testing/index.js"
    }
  },
  "files": ["dist", "src", "!src/**/__tests__", "README.md", "AGENTS.md", "CHANGELOG.md"],
  "scripts": {
    "build": "rm -rf dist && tsc -p tsconfig.build.json",
    "prepack": "npm run build"
  },
  "dependencies": {}
}
```

| Campo | Por quê |
|---|---|
| `private: true` | o tarball sai pelo `npm pack`, que o `private` não bloqueia; um `npm publish` por engano para em `EPRIVATE` antes da rede. Quem migrar para um registro troca o campo de propósito |
| `license: UNLICENSED` | é a convenção do npm para código proprietário; sem o campo, o npm avisa e quem lê não sabe se pode usar |
| `type: module` | só ESM. Os consumidores em Node 22+ carregam ESM, e até `require(esm)` é estável ali |
| `exports` com `types` primeiro | o TypeScript para na primeira condição que casa |
| `exports` para `dist` | o Node recusa remover tipos de `.ts` dentro de `node_modules`; um `exports` para `./src/*.ts` só funciona dentro do monorepo |
| `./testing` | a suíte de contrato vai para o consumidor provar o próprio adapter |
| `files` | lista de permissão. O `src` vai para os mapas resolverem; os testes não |
| sem `main` e `types` de topo | o `exports` já responde; os campos de topo só confundem quando divergem |
| `prepack` com o build | é o script que o `npm pack` roda. O `prepublishOnly` só roda no `npm publish`: sem registro, o tarball sai sem `dist`. Medido em 2026-10-16 (npm 12.0.2), com `dist/` no `.gitignore`: com `prepublishOnly` o tarball levou só o `package.json`; com `prepack`, levou o `dist` |
| `rm -rf dist` antes do `tsc` | arquivo de um build antigo, que o `src` já não gera, entraria no pacote |

## `tsconfig` de build

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "isolatedDeclarations": true,
    "skipLibCheck": true
  },
  "include": ["src"],
  "exclude": ["src/**/__tests__/**"]
}
```

- **`isolatedDeclarations`** obriga tipo explícito em tudo que é exportado. A API pública passa a ser
  escrita e revisável no diff, e não inferida de uma implementação que mudou.
- **`NodeNext`** exige extensão `.js` nos imports relativos: é o que o Node resolve em runtime.
- **TypeScript fixo no lockfile**, na mesma versão dos consumidores. A reconstrução da release depende
  do compilador: outra versão do `tsc` produz outro `dist` e outro sha256.

## Tamanho

Meça o `.tgz` antes e depois de incluir o `src`: `npm pack --dry-run --json | jq '.[].size'`. No npm
12 o JSON é um objeto indexado pelo nome do pacote, não uma lista, e o `.[0]` das receitas antigas
devolve nada; o `.[]` serve às duas formas. Uma lib de ~2,5 mil linhas de produção deu 50 300 bytes
com 85 arquivos, só `dist` com mapas (medido em 2026-10-16).

A negação no `files` (`"!src/**/__tests__"`) funciona: o pacote de prova saiu com `src/index.ts` e sem
`src/__tests__/` (medido em 2026-10-16, npm 12.0.2, `tar tzf` do tarball).
