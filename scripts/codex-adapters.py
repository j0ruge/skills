#!/usr/bin/env python3
"""Deriva skills de comandos sem manter uma segunda fonte manual."""

import argparse
import importlib.util
import json
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location('marketplace', Path(__file__).with_name('codex-marketplace.py'))
marketplace = importlib.util.module_from_spec(spec)
spec.loader.exec_module(marketplace)


def local_file(plugin, value):
    """Resolve apenas recursos existentes dentro do pacote canônico."""
    if not isinstance(value, str) or not value.startswith('./'):
        raise ValueError(f'caminho source inválido: {value!r}')
    path = marketplace.inside(plugin, plugin / value)
    if not path.is_file():
        raise ValueError(f'recurso ausente: {path}')
    return path


def build_artifacts(root):
    """Valida todo o lote antes de oferecer qualquer artefato para escrita."""
    try:
        import yaml
    except ImportError as exc:
        raise ValueError('PyYAML é necessário para ler os comandos canônicos') from exc
    artifacts, generated_dirs = {}, []
    for entry, manifest, plugin in marketplace.load_plugins(root):
        config_path = plugin / 'codex-adapter.json'
        if not config_path.exists():
            if (plugin / 'codex-skills').exists() or (plugin / '.codex-plugin/plugin.json').exists():
                raise ValueError(f'adaptador órfão sem codex-adapter.json: {plugin}')
            continue
        config = marketplace.read_json(config_path)
        commands = config.get('commands') if isinstance(config, dict) else None
        if not isinstance(commands, list) or not commands:
            raise ValueError(f'commands inválidos: {config_path}')
        generated = marketplace.inside(plugin, plugin / 'codex-skills')
        generated_dirs.append(generated)
        names = set()
        for command in commands:
            if not isinstance(command, dict):
                raise ValueError('command deve ser objeto')
            name = command.get('name')
            if not isinstance(name, str) or not marketplace.NAME_RE.fullmatch(name) or name in names:
                raise ValueError(f'name de comando inválido ou duplicado: {name!r}')
            names.add(name)
            source = local_file(plugin, command.get('source')).read_text(encoding='utf-8')
            pieces = source.split('---', 2)
            if len(pieces) != 3 or pieces[0].strip():
                raise ValueError(f'frontmatter ausente no comando {name}')
            try:
                metadata = yaml.safe_load(pieces[1])
            except yaml.YAMLError as exc:
                raise ValueError(f'frontmatter inválido no comando {name}: {exc}') from exc
            if not isinstance(metadata, dict) or not isinstance(metadata.get('description'), str):
                raise ValueError(f'description ausente no comando {name}')
            body = pieces[2].lstrip().replace('$ARGUMENTS', 'entrada do usuário nesta invocação')
            skill_dir = marketplace.inside(plugin, generated / name)
            resources = command.get('resources', [])
            if not isinstance(resources, list):
                raise ValueError(f'resources inválidos: {name}')
            targets = set()
            for resource in resources:
                if not isinstance(resource, dict):
                    raise ValueError('resource deve ser objeto')
                source_file = local_file(plugin, resource.get('source'))
                target = resource.get('target')
                if (not isinstance(target, str) or not target.startswith('assets/') or
                        '..' in Path(target).parts or Path(target) in targets):
                    raise ValueError(f'target inválido ou duplicado: {target!r}')
                targets.add(Path(target))
                artifacts[marketplace.inside(skill_dir, skill_dir / target)] = source_file.read_bytes()
                body = body.replace('${CLAUDE_PLUGIN_ROOT}/' + resource['source'][2:], target)
            # Comandos com vários templates referenciam o diretório inteiro.
            if resources and all(r['source'].startswith('./templates/') for r in resources):
                source_templates = {f.name for f in (plugin / 'templates').iterdir() if f.is_file()}
                mapped_templates = {Path(r['source']).name for r in resources}
                if source_templates == mapped_templates:
                    body = body.replace('${CLAUDE_PLUGIN_ROOT}/templates/', 'assets/')
            invocations = command.get('invocations', {})
            if not isinstance(invocations, dict):
                raise ValueError(f'invocations deve ser objeto no comando {name}')
            for old, new in invocations.items():
                if not isinstance(old, str) or not isinstance(new, str) or not new.startswith('$'):
                    raise ValueError('invocations deve mapear nomes para $plugin:skill')
                body = body.replace(old, new)
            if '${CLAUDE_PLUGIN_ROOT}' in body:
                raise ValueError(f'recurso sem tradução CLAUDE_PLUGIN_ROOT em {name}')
            header = (f'---\nname: {name}\ndescription: '
                      + json.dumps(metadata['description'], ensure_ascii=False) + '\n---\n\n')
            instructions = ('Caminhos `assets/` são relativos ao diretório desta skill instalada. '
                            'Resolva-os pelo caminho do SKILL.md carregado. Preserve a preferência '
                            'por templates do projeto consumidor indicada no workflow.\n\n')
            artifacts[skill_dir / 'SKILL.md'] = (header + instructions + body).encode('utf-8')
            if command.get('explicit', False) or metadata.get('disable-model-invocation') is True:
                artifacts[skill_dir / 'agents/openai.yaml'] = (
                    b'policy:\n  allow_implicit_invocation: false\n')
        overlay = {k: manifest[k] for k in ['name', 'version', 'description', 'author',
                                          'license', 'homepage', 'repository', 'keywords']
                   if k in manifest}
        skills = marketplace.skill_paths(plugin, manifest)
        overlay.update(skills=[*skills, './codex-skills'], commands=[])
        artifacts[marketplace.inside(plugin, plugin / '.codex-plugin/plugin.json')] = (
            json.dumps(overlay, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    for path in artifacts:
        marketplace.inside(root, path)
    for directory in generated_dirs:
        stale = {p for p in directory.rglob('*') if p.is_file()} - set(artifacts)
        if stale:
            raise ValueError(f'arquivo derivado órfão; remova após conferir: {sorted(stale)}')
    return artifacts


def sync_artifacts(root, write=False):
    """Confere bytes de todos os derivados; escreve somente no modo explícito."""
    artifacts = build_artifacts(root)
    for path, data in artifacts.items():
        if path.is_file() and path.read_bytes() == data:
            continue
        if not write:
            raise ValueError(f'adaptador ausente ou desatualizado: {path}; execute codex-adapters.py --write')
        marketplace.atomic_write(path, data)


def main():
    """Confere as adaptações ou grava os derivados com --write explícito."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true')
    group.add_argument('--write', action='store_true')
    args = parser.parse_args()
    try:
        sync_artifacts(args.root, args.write)
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        print(f'Erro de adaptação Codex: {exc}', file=sys.stderr)
        return 1
    print('Adaptadores Codex atualizados e válidos.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
