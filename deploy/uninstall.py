#!/usr/bin/env python3
"""Safe DE/EN uninstaller for kienzletranslate-managed files."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


CONFIG = Path('/etc/kienzletranslate/config.json')
CONFIG_DIR = CONFIG.parent
ACCESS_FILE = Path('/root/kienzletranslate-access.json')
INSTALL_LOG = Path('/var/log/kienzletranslate-install.log')
NGINX_SITE = Path('/etc/nginx/sites-available/kienzletranslate')
NGINX_ENABLED = Path('/etc/nginx/sites-enabled/kienzletranslate')
TMPFILES = Path('/etc/tmpfiles.d/kienzletranslate.conf')
RUNTIME_DIR = Path('/run/kienzletranslate')
PUBLIC_CA = Path('/var/lib/kienzletranslate/root-ca.cer')
SYSTEMD_DIR = Path('/etc/systemd/system')
UNITS = ('kienzletranslate.service', 'kienzletranslate-certificate.service',
         'kienzletranslate-certificate.timer')


def managed_path(value, label):
    if not isinstance(value, str) or not re.fullmatch(r'/(?:opt|srv|var/lib)/[A-Za-z0-9_/-]+', value):
        raise ValueError(label)
    path = Path(value)
    if '..' in path.parts or path in (Path('/opt'), Path('/srv'), Path('/var/lib')):
        raise ValueError(label)
    return path


def bool_answer(answers, key, default=False):
    value = answers.get(key, default)
    if type(value) is not bool:
        raise ValueError(f'{key} must be true or false')
    return value


def load_config():
    try:
        config = json.loads(CONFIG.read_text())
    except (OSError, ValueError) as exc:
        raise RuntimeError('managed configuration not found or invalid') from exc
    required = ('install_path', 'model_path', 'version', 'backend_token')
    if any(not config.get(key) for key in required) or config.get('license') != 'CC-BY-NC-4.0':
        raise RuntimeError('configuration is not a recognized kienzletranslate installation')
    config.setdefault('lid_model_path', '/var/lib/kienzletranslate/lid-model')
    managed_path(config['install_path'], 'install_path')
    managed_path(config['model_path'], 'model_path')
    managed_path(config['lid_model_path'], 'lid_model_path')
    return config


def build_plan(config, remove_data=False, remove_models=False, php_root=Path('/etc/php')):
    root = managed_path(config['install_path'], 'install_path')
    model = managed_path(config['model_path'], 'model_path')
    lid_model = managed_path(config.get('lid_model_path', '/var/lib/kienzletranslate/lid-model'),
                             'lid_model_path')
    plan = [
        ('service', SYSTEMD_DIR/name) for name in UNITS
    ]
    plan += [('nginx', NGINX_ENABLED), ('nginx', NGINX_SITE)]
    plan += [('php', path) for path in sorted(php_root.glob('*/fpm/pool.d/kienzletranslate.conf'))]
    plan += [('tmpfiles', TMPFILES), ('runtime', RUNTIME_DIR),
             ('app', root/'current'), ('app', root/'current.next'),
             ('app', root/'releases'), ('venv', root/'venv'), ('venv', root/'lid-venv'),
             ('log', INSTALL_LOG)]
    if remove_data:
        plan += [('backup', root/'backups'), ('data', CONFIG_DIR), ('data', ACCESS_FILE),
                 ('data', PUBLIC_CA)]
    if remove_models:
        plan += [('model', model), ('lid-model', lid_model)]
    return plan


def _contains(path, text):
    try:
        return text in path.read_text(errors='replace')
    except OSError:
        return False


def _safe_release_tree(path):
    if not path.exists():
        return True
    if path.is_symlink() or not path.is_dir():
        return False
    for child in path.iterdir():
        if child.is_symlink() or not child.is_dir():
            return False
        if not (child/'deploy/install.py').is_file() or not (child/'backend').is_dir():
            return False
    return True


def _safe_venv(path):
    return not path.exists() or (not path.is_symlink() and path.is_dir() and
                                 (path/'pyvenv.cfg').is_file() and (path/'bin/python').exists())


def _safe_model(path, lid=False):
    if not path.exists():
        return True
    if path.is_symlink() or not path.is_dir() or not (path/'config.json').is_file():
        return False
    if lid:
        return (path/'model.bin').is_file() and (path/'tokenizer.json').is_file()
    return any(path.glob('*.safetensors'))


def _safe_service(path):
    if path.is_symlink() or not path.is_file():
        return False
    if path.name == 'kienzletranslate.service':
        return _contains(path, 'Environment=KIENZLE_CONFIG=/etc/kienzletranslate/config.json')
    if path.name == 'kienzletranslate-certificate.service':
        return _contains(path, '/deploy/install.py --renew-certificate')
    if path.name == 'kienzletranslate-certificate.timer':
        return _contains(path, 'Description=Check kienzletranslate local TLS certificate daily')
    return False


def verify_plan(config, plan):
    """Refuse every suspicious existing target before the first mutation."""
    root = managed_path(config['install_path'], 'install_path')
    releases = root/'releases'
    if root.is_symlink() or any(parent.is_symlink() for parent in root.parents):
        raise RuntimeError(f'refusing symlinked installation root: {root}')
    models = [managed_path(config.get(k, '/var/lib/kienzletranslate/lid-model'), k)
              for k in ('model_path', 'lid_model_path')]
    if models[0] == models[1] or models[0] in models[1].parents or models[1] in models[0].parents:
        raise RuntimeError('overlapping model paths')
    for model in models:
        if model == root or model in root.parents:
            raise RuntimeError('model path contains installation root')
        for kind, target in plan:
            if kind not in ('model', 'lid-model') and (target == model or target in model.parents or model in target.parents):
                raise RuntimeError(f'model overlaps managed application data: {model}')
    for kind, path in plan:
        if not path.exists() and not path.is_symlink():
            continue
        safe = not any(parent.is_symlink() for parent in path.parents)
        if not safe:
            raise RuntimeError(f'refusing symlinked parent: {path}')
        if kind == 'service':
            safe = _safe_service(path)
        elif kind == 'nginx':
            if path == NGINX_ENABLED and path.is_symlink():
                safe = path.resolve(strict=False) == NGINX_SITE
            else:
                safe = not path.is_symlink() and path.is_file() and _contains(path, 'Managed by kienzletranslate')
        elif kind == 'php':
            safe = not path.is_symlink() and path.is_file() and _contains(path, '[kienzletranslate]')
        elif kind == 'tmpfiles':
            safe = not path.is_symlink() and path.is_file() and _contains(path, '/run/kienzletranslate')
        elif kind == 'runtime':
            safe = path == RUNTIME_DIR and path.is_dir() and not path.is_symlink()
        elif kind == 'app' and path.name in ('current', 'current.next'):
            safe = path.is_symlink() and releases in path.resolve(strict=False).parents
        elif kind == 'app':
            safe = _safe_release_tree(path)
        elif kind == 'venv':
            safe = _safe_venv(path)
        elif kind == 'model':
            safe = _safe_model(path)
        elif kind == 'lid-model':
            safe = _safe_model(path, lid=True)
        elif kind == 'data' and path == CONFIG_DIR:
            safe = path.is_dir() and not path.is_symlink() and CONFIG.is_file()
        elif kind == 'backup':
            safe = path.is_dir() and not path.is_symlink()
        elif kind in ('data', 'log'):
            safe = path.is_file() and not path.is_symlink()
        if not safe:
            raise RuntimeError(f'refusing suspicious managed path: {path}')


def remove_path(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def command(args, check=False):
    result = subprocess.run([str(value) for value in args], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    if check and result.returncode:
        raise RuntimeError(f'{args[0]} failed: {result.stdout.strip()}')
    return result.returncode


def execute(plan, config):
    existing_units = {path.name for kind, path in plan if kind == 'service' and path.exists()}
    if 'kienzletranslate.service' in existing_units:
        command(['systemctl', 'disable', '--now', 'kienzletranslate.service'], check=True)
    if 'kienzletranslate-certificate.timer' in existing_units:
        command(['systemctl', 'disable', '--now', 'kienzletranslate-certificate.timer'], check=True)
    if 'kienzletranslate-certificate.service' in existing_units:
        command(['systemctl', 'stop', 'kienzletranslate-certificate.service'], check=True)

    php_services = [f'php{path.parts[path.parts.index("php") + 1]}-fpm'
                    for kind, path in plan if kind == 'php' and path.exists()]
    nginx_changed = any(kind == 'nginx' and (path.exists() or path.is_symlink()) for kind, path in plan)
    units_changed = any(kind == 'service' and path.exists() for kind, path in plan)
    for _, path in plan:
        remove_path(path)

    root = managed_path(config['install_path'], 'install_path')
    try:
        root.rmdir()
    except (FileNotFoundError, OSError):
        pass
    if units_changed:
        command(['systemctl', 'daemon-reload'], check=True)
    for service in php_services:
        command(['systemctl', 'try-reload-or-restart', service], check=True)
    if nginx_changed:
        command(['nginx', '-t'], check=True)
        command(['systemctl', 'reload', 'nginx'], check=True)


def main():
    parser = argparse.ArgumentParser(description='kienzletranslate uninstaller')
    parser.add_argument('--answers', help='JSON answers file or - for stdin')
    parser.add_argument('--check', action='store_true', help='show and validate the plan without changes')
    parser.add_argument('--dry-run', action='store_true', help='show and validate the plan without changes')
    args = parser.parse_args()
    try:
        answers = json.load(sys.stdin if args.answers == '-' else open(args.answers)) if args.answers else {}
    except (OSError, ValueError) as exc:
        raise SystemExit(f'Antwortdatei ungültig / Invalid answers file ({exc})')
    language = answers.get('language') or input('Sprache / Language [de/en] (de): ').strip() or 'de'
    if language not in ('de', 'en'):
        raise SystemExit('Bitte de oder en wählen. / Please choose de or en.')
    en = language == 'en'

    def tr(de, eng):
        return eng if en else de

    try:
        remove_data = bool_answer(answers, 'remove_data')
        remove_models = bool_answer(answers, 'remove_models')
    except ValueError as exc:
        raise SystemExit(tr(f'Ungültige Antwort: {exc}.', f'Invalid answer: {exc}.'))
    if not args.answers:
        def ask(question_de, question_en):
            answer = input(tr(question_de + ' [ja/nein] (nein): ',
                              question_en + ' [yes/no] (no): ')).strip().lower()
            if answer not in ('', 'ja', 'j', 'yes', 'y', 'nein', 'n', 'no'):
                raise SystemExit(tr('Bitte ja oder nein eingeben.', 'Please enter yes or no.'))
            return answer in ('ja', 'j', 'yes', 'y')

        remove_data = ask('Auch Konfiguration, CA, Zugangsdaten und Backups entfernen?',
                          'Also remove configuration, CA, access data and backups?')
        remove_models = ask('Auch Haupt- und Spracherkennungsmodell entfernen?',
                            'Also remove the main and language detection models?')
    try:
        config = load_config()
        plan = build_plan(config, remove_data, remove_models)
        verify_plan(config, plan)
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(tr(f'Deinstallation abgebrochen: {exc}', f'Uninstall cancelled: {exc}'))

    print(tr('\nVerwaltete Dienste und Pfade, die entfernt werden:',
             '\nManaged services and paths to be removed:'))
    for kind, path in plan:
        state = tr('vorhanden', 'present') if path.exists() or path.is_symlink() else tr('fehlt', 'absent')
        print(f'  - [{kind}] {path} ({state})')
    retained = []
    if not remove_data:
        retained += [CONFIG_DIR, Path(config['install_path'])/'backups', ACCESS_FILE, PUBLIC_CA]
    if not remove_models:
        retained += [Path(config['model_path']), Path(config['lid_model_path'])]
    if retained:
        print(tr('Beibehalten:', 'Retained:'))
        for path in retained:
            print(f'  - {path}')
    if args.check or args.dry_run:
        print(tr('Plan gültig. Keine Systemänderungen.', 'Plan valid. No system changes.'))
        return
    word = 'UNINSTALL' if en else 'DEINSTALLIEREN'
    confirmation = answers.get('confirmation') if args.answers else input(
        tr('Zum Entfernen DEINSTALLIEREN eingeben: ', 'Type UNINSTALL to remove: '))
    if confirmation != word:
        raise SystemExit(tr('Abgebrochen. Keine Systemänderungen.', 'Cancelled. No system changes.'))
    if os.geteuid() != 0:
        raise SystemExit(tr('Bitte mit sudo ausführen.', 'Please run using sudo.'))
    execute(plan, config)
    print(tr('Deinstallation abgeschlossen.', 'Uninstall complete.'))


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        raise SystemExit('\nAbgebrochen / Cancelled')
    except (OSError, RuntimeError) as exc:
        raise SystemExit(f'Deinstallation fehlgeschlagen / Uninstall failed ({exc})')
