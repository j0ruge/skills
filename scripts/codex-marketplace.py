#!/usr/bin/env python3
"""Gera e confere o catálogo Codex a partir dos manifestos canônicos."""

import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile

VALID_PLATFORMS = {'claude-code', 'cursor', 'codex'}
NAME_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
CATALOG = Path('.agents/plugins/marketplace.json')


def read_json(path):
    """Lê JSON de distribuição com erro que identifica sua origem."""
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ValueError(f'JSON ilegível em {path}: {exc}') from exc


def inside(root, path):
    """Recusa caminhos ou links que saem da fronteira do pacote."""
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'escape de caminho: {path}')
    return path


def load_plugins(root):
    """Confere a identidade e os caminhos antes de selecionar plataformas."""
    root = root.resolve()
    catalog = read_json(inside(root, root / '.claude-plugin/marketplace.json'))
    if not isinstance(catalog, dict) or catalog.get('name') != 'chewiesoft-marketplace':
        raise ValueError('name do marketplace deve ser chewiesoft-marketplace')
    entries = catalog.get('plugins')
    if not isinstance(entries, list):
        raise ValueError('plugins deve ser uma lista')
    seen, plugins = set(), []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('entrada de plugin deve ser objeto')
        name = entry.get('name')
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            raise ValueError(f'name inválido: {name!r}')
        if name in seen:
            raise ValueError(f'name duplicado: {name}')
        seen.add(name)
        if entry.get('source') != f'./plugins/{name}':
            raise ValueError(f'{name}: source deve apontar para ./plugins/{name}')
        plugin = inside(root, root / 'plugins' / name)
        for resource in plugin.rglob('*'):
            inside(plugin, resource)
        manifest = read_json(inside(plugin, plugin / '.claude-plugin/plugin.json'))
        if not isinstance(manifest, dict):
            raise ValueError(f'{name}: plugin.json deve ser objeto')
        for key in ['name', 'version', 'description', 'platforms']:
            if not manifest.get(key) or entry.get(key) != manifest.get(key):
                raise ValueError(f'{name}: {key} divergente entre catálogo e plugin.json')
        platforms = manifest['platforms']
        if (not isinstance(platforms, list) or
                any(not isinstance(p, str) or p not in VALID_PLATFORMS for p in platforms) or
                len(set(platforms)) != len(platforms)):
            raise ValueError(f'{name}: platforms inválidas')
        if not isinstance(manifest['description'], str) or not re.fullmatch(
                r'\d+\.\d+\.\d+', str(manifest['version'])):
            raise ValueError(f'{name}: description ou version inválida')
        if 'codex' in platforms:
            skills = manifest.get('skills', ['./skills'] if (plugin / 'skills').is_dir() else [])
            if isinstance(skills, str):
                skills = [skills]
            if not isinstance(skills, list):
                raise ValueError(f'{name}: skills deve ser caminho ou lista')
            for value in skills:
                if not isinstance(value, str) or not value.startswith('./'):
                    raise ValueError(f'{name}: caminho de skills inválido')
                directory = inside(plugin, plugin / value)
                if not directory.is_dir() or not any(directory.rglob('SKILL.md')):
                    raise ValueError(f'{name}: skills ausentes em {value}')
            if not skills and not (plugin / 'codex-adapter.json').is_file():
                raise ValueError(f'{name}: skills ausentes e nenhum adaptador de comandos')
        plugins.append((entry, manifest, plugin))
    return sorted(plugins, key=lambda p: p[0]['name'])


def build_catalog(root):
    """Produz somente o subconjunto explicitamente habilitado para Codex."""
    entries = []
    for entry, manifest, plugin in load_plugins(root):
        if 'codex' not in manifest['platforms']:
            continue
        entries.append(dict(name=manifest['name'],
                            source=dict(source='local', path=entry['source']),
                            policy=dict(installation='AVAILABLE', authentication='ON_INSTALL'),
                            category=entry.get('category', 'development')))
    return dict(name='chewiesoft-marketplace',
                interface=dict(displayName='Chewiesoft'), plugins=entries)


def sync_json(path, expected, write):
    """Compara sem escrever ou substitui o derivado atomicamente."""
    encoded = json.dumps(expected, ensure_ascii=False, indent=2) + '\n'
    if path.is_file() and path.read_text(encoding='utf-8') == encoded:
        return
    if not write:
        raise ValueError(f'derivado ausente ou desatualizado: {path}; execute --write')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.codex-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--write', action='store_true')
    args = parser.parse_args()
    try:
        expected = build_catalog(args.root)
        sync_json(inside(args.root, args.root / CATALOG), expected, args.write)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f'Erro Codex: {exc}', file=sys.stderr)
        return 1
    print('Catálogo Codex atualizado e válido.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
