#!/usr/bin/env python3
"""Native Debian/Ubuntu installer. No changes before explicit licence consent."""
import argparse
import datetime
import getpass
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time

CONFIG = Path('/etc/kienzletranslate/config.json')
SOURCE = Path(__file__).resolve().parents[1]
VERSION = '1.7.0'

GIB = 1024 ** 3
MAIN_MODEL_BUDGET = 16 * GIB
LID_MODEL_BUDGET = 2 * GIB
INSTALL_BUDGET = 6 * GIB


def bool_setting(old, answers, key, default):
    value = answers.get(key, old.get(key, default))
    if type(value) is not bool:
        raise ValueError(f'{key} must be true or false')
    return value


def integer_setting(old, answers, key, default, minimum, maximum):
    value = answers.get(key, old.get(key, default))
    if type(value) is not int:
        raise ValueError(key)
    if not minimum <= value <= maximum:
        raise ValueError(key)
    return value


def password_setting(old, answers):
    return bool_setting(old, answers, 'password_required', bool(old.get('password_hash')))


def validate(values):
    ipaddress.ip_address(values['server_ip'])
    name = values.get('server_name', '')
    if name and (len(name) > 253 or not all(re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?', x) for x in name.split('.'))):
        raise ValueError('server_name')
    ports = [int(values[k]) for k in ('http_port', 'https_port', 'model_port')]
    if any(p < 1 or p > 65535 for p in ports) or len(set(ports)) != 3:
        raise ValueError('ports')
    for key in ('install_path', 'model_path', 'lid_model_path'):
        path = values[key]
        if not re.fullmatch(r'/(?:opt|srv|var/lib)/[A-Za-z0-9_/-]+', path) or '..' in Path(path).parts:
            raise ValueError(key)
    root = Path(values['install_path'])
    models = [Path(values[k]) for k in ('model_path', 'lid_model_path')]
    managed = [root/name for name in ('current', 'releases', 'venv', 'lid-venv', 'backups')]
    for model in models:
        if model == root or model in root.parents or any(model == x or model in x.parents or x in model.parents for x in managed):
            raise ValueError('model path overlaps managed application data')
    if models[0] == models[1] or models[0] in models[1].parents or models[1] in models[0].parents:
        raise ValueError('model paths overlap')
    for key, minimum, maximum in (
            ('model_disconnect_seconds', 30, 3600),
            ('model_idle_seconds', 60, 86400),
            ('model_min_free_mib', 1024, 1048576)):
        value = values[key]
        if type(value) is bool or not isinstance(value, int) or not minimum <= value <= maximum:
            raise ValueError(key)
    for key in ('model_autoload', 'model_load_on_use', 'model_auto_unload'):
        if type(values[key]) is not bool:
            raise ValueError(key)
    return values


def existing_ancestor(path):
    path = Path(path)
    while not path.exists():
        if path.parent == path:
            raise ValueError(path)
        path = path.parent
    return path


def preflight_space(config):
    """Check all destination filesystems once, including download/install reserve."""
    requirements = {}
    model_path = Path(config['model_path'])
    lid_path = Path(config['lid_model_path'])
    model_complete = (model_path/'config.json').is_file() and any(model_path.glob('*.safetensors'))
    lid_complete = all((lid_path/name).is_file() for name in
                       ('config.json', 'model.bin', 'tokenizer.json', 'vocabulary.txt'))
    destinations = (
        (config['install_path'], INSTALL_BUDGET),
        (config['model_path'], 0 if model_complete else MAIN_MODEL_BUDGET),
        (config['lid_model_path'], 0 if lid_complete else LID_MODEL_BUDGET),
    )
    for destination, budget in destinations:
        ancestor = existing_ancestor(destination)
        device = ancestor.stat().st_dev
        requirements[device] = (ancestor, requirements.get(device, (ancestor, 0))[1] + budget)
    for ancestor, budget in requirements.values():
        if shutil.disk_usage(ancestor).free < budget:
            raise RuntimeError(f'insufficient free disk space at {ancestor} (need {budget // GIB} GiB including reserve)')


def write(path, content, mode=0o644):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.kt-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as file:
            file.write(content)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run(args, *, data=None, capture=False):
    result = subprocess.run([str(a) for a in args], input=data, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if not capture:
        with open('/var/log/kienzletranslate-install.log', 'a') as log:
            log.write(result.stdout or '')
    if result.returncode:
        raise RuntimeError(Path(str(args[0])).name)
    return result.stdout.strip() if capture else ''


def certificate(config, renew=False):
    tls = Path('/etc/kienzletranslate/tls')
    tls.mkdir(mode=0o700, parents=True, exist_ok=True)
    ca_key, ca = tls/'ca.key', tls/'ca.pem'
    if not ca_key.exists() and not ca.exists():
        run(['openssl', 'req', '-x509', '-newkey', 'rsa:3072', '-sha256', '-nodes', '-days', '3650',
             '-keyout', ca_key, '-out', ca, '-subj', '/CN=kienzletranslate Local CA',
             '-addext', 'basicConstraints=critical,CA:TRUE,pathlen:0',
             '-addext', 'keyUsage=critical,keyCertSign,cRLSign'])
        os.chmod(ca_key, 0o600)
    elif not ca_key.exists() or not ca.exists():
        raise RuntimeError('CA incomplete; restore existing CA before continuing')
    if renew and (tls/'server.pem').exists():
        valid = subprocess.run(['openssl', 'x509', '-checkend', str(30*86400), '-noout', '-in', str(tls/'server.pem')], stdout=subprocess.DEVNULL)
        if valid.returncode == 0:
            return
    san = 'IP:' + config['server_ip']
    if config['server_name']:
        san += ',DNS:' + config['server_name']
    write(tls/'server.ext', 'basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\nsubjectAltName='+san+'\n', 0o600)
    run(['openssl', 'req', '-new', '-newkey', 'rsa:2048', '-nodes', '-sha256', '-keyout', tls/'server-next.key',
         '-out', tls/'server.csr', '-subj', '/CN='+(config['server_name'] or config['server_ip'])])
    run(['openssl', 'x509', '-req', '-in', tls/'server.csr', '-CA', ca, '-CAkey', ca_key,
         '-set_serial', '0x'+secrets.token_hex(16), '-out', tls/'server-next.pem', '-days', '365', '-sha256', '-extfile', tls/'server.ext'])
    os.chmod(tls/'server-next.key', 0o600)
    os.replace(tls/'server-next.key', tls/'server.key')
    os.replace(tls/'server-next.pem', tls/'server.pem')
    public = Path('/var/lib/kienzletranslate/root-ca.cer')
    public.parent.mkdir(parents=True, exist_ok=True)
    run(['openssl', 'x509', '-in', ca, '-outform', 'DER', '-out', public])
    os.chmod(public, 0o644)
    config['ca_public_path'] = str(public)
    config['ca_fingerprint'] = run(['openssl', 'x509', '-in', ca, '-noout', '-fingerprint', '-sha256'], capture=True)


def nginx_config(config):
    root = config['install_path']+'/current/web'
    names = config['server_ip'] + (' '+config['server_name'] if config['server_name'] else '')
    php = '''include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param HTTPS $https;
        fastcgi_pass unix:/run/kienzletranslate/php.sock;
        fastcgi_request_buffering off;
        fastcgi_read_timeout 30s;'''
    return rf'''# Managed by kienzletranslate. Other sites remain untouched.
map $arg_route $kienzle_login_key {{ default ""; login $binary_remote_addr; }}
limit_req_zone $kienzle_login_key zone=kienzle_login:1m rate=5r/m;
server {{
    listen {config['http_port']};
    server_name {names};
    root {root};
    client_max_body_size 8k;
    access_log off;
    location = / {{ rewrite ^ /setup.php last; }}
    location = /setup.php {{ {php} }}
    location / {{ return 302 {config['public_url']}$request_uri; }}
}}
server {{
    listen {config['https_port']} ssl;
    server_name {names};
    root {root};
    index index.php;
    ssl_certificate /etc/kienzletranslate/tls/server.pem;
    ssl_certificate_key /etc/kienzletranslate/tls/server.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    client_max_body_size 16m;
    client_body_buffer_size 16m;
    access_log off;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header Referrer-Policy no-referrer always;
    add_header Permissions-Policy 'microphone=(self), camera=(), geolocation=()' always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; worker-src 'self' blob:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'" always;
    location ~ /\. {{ deny all; }}
    location ~ ^/(index|api|setup)\.php$ {{
        limit_req zone=kienzle_login burst=5 nodelay;
        limit_req_status 429;
        {php}
    }}
    location ~ \.php$ {{ return 404; }}
    location = /sw.js {{ add_header Cache-Control no-cache; }}
    location / {{ try_files $uri $uri/ =404; }}
}}
'''


def main():
    parser = argparse.ArgumentParser(description='kienzletranslate installer')
    parser.add_argument('--answers', help='JSON answers file or - for stdin; requires explicit licence word')
    parser.add_argument('--check', action='store_true', help='Validate answers without changing the system')
    parser.add_argument('--renew-certificate', action='store_true')
    args = parser.parse_args()
    if args.renew_certificate:
        config = json.loads(CONFIG.read_text())
        certificate(config, renew=True)
        run(['nginx', '-t'])
        run(['systemctl', 'reload', 'nginx'])
        return
    answers = json.load(sys.stdin if args.answers == '-' else open(args.answers)) if args.answers else {}
    language = answers.get('language') or input('Sprache / Language [de/en] (de): ').strip() or 'de'
    if language not in ('de', 'en'):
        raise SystemExit('Bitte de oder en wählen. / Please choose de or en.')
    en = language == 'en'
    def tr(de, eng): return eng if en else de
    print(tr('\nMODELLLIZENZ: Meta SeamlessM4T v2 Large — CC BY-NC 4.0.\nNur nichtkommerzielle Nutzung. Kommerzielle Nutzung ist unter dieser Lizenz nicht gestattet.\nNamensnennung und weitere Lizenzbedingungen sind einzuhalten. Anwendungscode: separate MIT-Lizenz.\nTechnischer Prototyp ohne medizinische Validierung; Testdaten verwenden.',
             '\nMODEL LICENCE: Meta SeamlessM4T v2 Large — CC BY-NC 4.0.\nNoncommercial use only. Commercial use is not permitted under this licence.\nAttribution and the other licence terms apply. Application code: separate MIT licence.\nTechnical prototype without medical validation; use test data.'))
    print('https://creativecommons.org/licenses/by-nc/4.0/\nhttps://huggingface.co/facebook/seamless-m4t-v2-large')
    word = 'ACCEPT' if en else 'AKZEPTIEREN'
    consent = answers.get('license_acceptance') if args.answers else input(tr('Zur Bestätigung AKZEPTIEREN eingeben: ', 'Type ACCEPT to confirm: '))
    if consent != word:
        raise SystemExit(tr('Abgebrochen. Keine Systemänderungen.', 'Cancelled. No system changes.'))
    old = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
    defaults = {'server_ip':'10.0.83.140', 'server_name':'', 'http_port':80, 'https_port':443,
                'model_port':8765, 'install_path':'/opt/kienzletranslate', 'model_path':'/var/lib/kienzletranslate/model'}
    labels = {'server_ip':tr('Server-IP', 'Server IP'), 'server_name':tr('Zusätzlicher DNS-Servername (optional)', 'Additional DNS server name (optional)'),
              'http_port':'HTTP-Port', 'https_port':'HTTPS-Port', 'model_port':tr('Lokaler Modell-TCP-Port', 'Local model TCP port'),
              'install_path':tr('Installationspfad', 'Installation path'), 'model_path':tr('Modellpfad', 'Model path')}
    config = dict(old)
    config['language'] = language
    for key, default in defaults.items():
        value = old.get(key, default)
        config[key] = answers.get(key, value) if args.answers else (input(f'{labels[key]} [{value}]: ').strip() or value)
        if key.endswith('_port'):
            try:
                config[key] = int(config[key])
            except (TypeError, ValueError):
                raise SystemExit(tr('Ports müssen ganze Zahlen sein.', 'Ports must be integers.'))
    try:
        config['password_required'] = password_setting(old, answers)
    except ValueError:
        raise SystemExit(tr('password_required muss true oder false sein.', 'password_required must be true or false.'))
    if not args.answers:
        default = tr('ja', 'yes') if config['password_required'] else tr('nein', 'no')
        choice = input(tr(f'Passwortschutz aktivieren? [ja/nein] ({default}): ', f'Enable password protection? [yes/no] ({default}): ')).strip().lower()
        if choice:
            if choice not in ('ja', 'j', 'yes', 'y', 'nein', 'n', 'no'):
                raise SystemExit(tr('Bitte ja oder nein eingeben.', 'Please enter yes or no.'))
            config['password_required'] = choice in ('ja', 'j', 'yes', 'y')
    try:
        config['model_autoload'] = bool_setting(old, answers, 'model_autoload', False)
        config['model_load_on_use'] = bool_setting(old, answers, 'model_load_on_use', True)
        config['model_auto_unload'] = bool_setting(old, answers, 'model_auto_unload', True)
        config['model_disconnect_seconds'] = integer_setting(old, answers, 'model_disconnect_seconds', 90, 30, 3600)
        config['model_idle_seconds'] = integer_setting(old, answers, 'model_idle_seconds', 300, 60, 86400)
        config['model_min_free_mib'] = integer_setting(old, answers, 'model_min_free_mib', 8192, 1024, 1048576)
    except ValueError as exc:
        raise SystemExit(tr(f'Ungültiger Modellwert: {exc}.', f'Invalid model setting: {exc}.'))
    if not args.answers:
        def ask_bool(de, eng, current):
            default = tr('ja', 'yes') if current else tr('nein', 'no')
            answer = input(tr(f'{de} [ja/nein] ({default}): ', f'{eng} [yes/no] ({default}): ')).strip().lower()
            if not answer:
                return current
            if answer not in ('ja', 'j', 'yes', 'y', 'nein', 'n', 'no'):
                raise SystemExit(tr('Bitte ja oder nein eingeben.', 'Please enter yes or no.'))
            return answer in ('ja', 'j', 'yes', 'y')

        config['model_autoload'] = ask_bool('Modell bereits beim Serverstart laden?',
                                            'Load the model when the server starts?', config['model_autoload'])
        config['model_load_on_use'] = ask_bool('Modell bei Benutzung der Webapp automatisch laden?',
                                               'Load the model automatically when the web app is used?', config['model_load_on_use'])
        config['model_auto_unload'] = ask_bool('Automatisch bei Nichtbenutzung entladen?',
                                               'Unload automatically when not in use?', config['model_auto_unload'])
        disconnect = input(tr('Wartezeit ohne verbundenes Gerät in Sekunden',
                              'Time without a connected device in seconds') +
                           f" [{config['model_disconnect_seconds']}]: ").strip()
        idle_minutes = config['model_idle_seconds'] // 60
        idle = input(tr('Inaktivitätszeit trotz geöffneter App in Minuten',
                        'Inactivity time while the app remains open in minutes') +
                     f' [{idle_minutes}]: ').strip()
        try:
            if disconnect:
                config['model_disconnect_seconds'] = int(disconnect)
            if idle:
                config['model_idle_seconds'] = int(idle) * 60
        except ValueError:
            raise SystemExit(tr('Zeitangaben müssen ganze Zahlen sein.', 'Time values must be integers.'))
    config['lid_model_path'] = answers.get('lid_model_path', old.get('lid_model_path', '/var/lib/kienzletranslate/lid-model'))
    config['lid_python'] = config['install_path'] + '/lid-venv/bin/python'
    try:
        validate(config)
    except (ValueError, TypeError):
        raise SystemExit(tr('Ungültige IP, DNS-Angabe, Ports, Pfade oder Modellwerte.',
                            'Invalid IP, DNS name, ports, paths or model settings.'))
    host = config['server_name'] or config['server_ip']
    if ':' in host: host = '['+host+']'
    config['public_url'] = 'https://'+host+(':'+str(config['https_port']) if config['https_port'] != 443 else '')
    password = answers.get('password', '') if args.answers else ''
    if not isinstance(password, str):
        raise SystemExit(tr('Das Passwort muss Text sein.', 'The password must be text.'))
    if password and len(password) < 12:
        raise SystemExit(tr('Bitte mindestens 12 Zeichen verwenden.', 'Please use at least 12 characters.'))
    if args.check:
        print(tr('Eingaben gültig. Keine Systemänderungen.', 'Inputs valid. No system changes.'))
        return
    if os.geteuid() != 0:
        raise SystemExit(tr('Bitte mit sudo ausführen.', 'Please run using sudo.'))
    if old and config['install_path'] != old['install_path']:
        raise SystemExit(tr('Beim Update den bestehenden Installationspfad beibehalten.', 'Keep the existing installation path when updating.'))
    osrelease = Path('/etc/os-release').read_text()
    if not re.search(r'^ID=(?:ubuntu|debian)$', osrelease, re.M):
        raise SystemExit(tr('Ubuntu oder Debian erforderlich.', 'Ubuntu or Debian required.'))
    try:
        preflight_space(config)
    except (ValueError, OSError, RuntimeError) as exc:
        raise SystemExit(tr(f'Nicht genügend freier Speicherplatz: {exc}.',
                            f'Insufficient free disk space: {exc}.'))
    # Confirm availability before touching services. Existing managed ports are allowed.
    existing_ports = {old.get(k) for k in ('http_port','https_port','model_port')} if old else set()
    for key in ('http_port','https_port','model_port'):
        port = config[key]
        if port in existing_ports: continue
        with socket.socket() as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try: sock.bind(('127.0.0.1' if key == 'model_port' else '0.0.0.0', port))
            except OSError: raise SystemExit(tr(f'Port {port} ist belegt. Bitte anderen Port wählen.', f'Port {port} is occupied. Choose a different port.'))
    if config['password_required'] and not args.answers:
        password = getpass.getpass(tr('Zugangspasswort (leer: beibehalten oder sicher erzeugen): ', 'Access password (blank: keep existing or generate): '))
    generated = False
    if config['password_required'] and not password and 'password_hash' not in old:
        password = secrets.token_urlsafe(18)
        generated = True
    if password and len(password) < 12:
        raise SystemExit(tr('Bitte mindestens 12 Zeichen verwenden.', 'Please use at least 12 characters.'))
    print(tr('Installation läuft; technische Details: /var/log/kienzletranslate-install.log', 'Installing; technical details: /var/log/kienzletranslate-install.log'), flush=True)
    log = Path('/var/log/kienzletranslate-install.log')
    log.touch(mode=0o600, exist_ok=True)
    root = Path(config['install_path'])
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = root/'backups'/stamp
    backup.mkdir(parents=True)
    for file in [CONFIG, Path('/etc/nginx/sites-available/kienzletranslate')]:
        if file.exists(): shutil.copy2(file, backup/file.name)
    managed_files = list(Path('/etc/php').glob('*/fpm/pool.d/kienzletranslate.conf'))
    managed_files += [Path('/etc/systemd/system')/name for name in
                      ('kienzletranslate.service','kienzletranslate-certificate.service','kienzletranslate-certificate.timer')]
    for file in managed_files:
        if file.exists():
            target = backup/'managed-files'/str(file).lstrip('/')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, target)
    if CONFIG.parent.joinpath('tls').exists():
        shutil.copytree(CONFIG.parent/'tls', backup/'tls')
    os.chmod(backup, 0o700)
    previous = (root/'current').resolve() if (root/'current').exists() else None
    run(['apt-get','update'])
    run(['env','DEBIAN_FRONTEND=noninteractive','apt-get','install','-y','nginx','php-fpm','php-curl','python3-venv','openssl','ca-certificates'])
    if subprocess.run(['id','kienzletranslate'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
        run(['useradd','--system','--home-dir','/var/lib/kienzletranslate','--shell','/usr/sbin/nologin','kienzletranslate'])
    run(['install','-d','-o','kienzletranslate','-g','kienzletranslate','-m','0750','/var/lib/kienzletranslate'])
    if password:
        config['password_hash'] = run(['php','-r','echo password_hash(stream_get_contents(STDIN), PASSWORD_DEFAULT);'], data=password, capture=True)
    for key in ('backend_token','session_secret'):
        config.setdefault(key, secrets.token_hex(32))
    config.update(version=VERSION, license_accepted_at=stamp, license='CC-BY-NC-4.0')
    venv = root/'venv'
    if not (venv/'bin/python').exists(): run(['python3','-m','venv',venv])
    run([venv/'bin/pip','install','-r', SOURCE/'backend/requirements.lock.txt'])
    lid_venv = root/'lid-venv'
    if not (lid_venv/'bin/python').exists(): run(['python3','-m','venv',lid_venv])
    run([lid_venv/'bin/pip','install','-r', SOURCE/'backend/requirements-lid.lock.txt'])
    print(tr('Modell-Checkpoint wird geprüft/heruntergeladen …', 'Checking/downloading model checkpoint …'), flush=True)
    run([venv/'bin/python', SOURCE/'scripts/download_model.py', config['model_path']])
    print(tr('CPU-Spracherkennungsmodell wird geprüft/heruntergeladen …',
             'Checking/downloading CPU language detection model …'), flush=True)
    run([lid_venv/'bin/python', SOURCE/'scripts/download_lid_model.py', config['lid_model_path']])
    run(['chown','-R','kienzletranslate:kienzletranslate',config['model_path']])
    run(['chown','-R','kienzletranslate:kienzletranslate',config['lid_model_path']])
    certificate(config)
    write(CONFIG, json.dumps(config, ensure_ascii=False, indent=2)+'\n', 0o640)
    run(['chown','root:kienzletranslate',CONFIG])
    release = root/'releases'/stamp
    release.mkdir(parents=True)
    for folder in ('web','backend','deploy','scripts','docs'):
        shutil.copytree(SOURCE/folder, release/folder, ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ('README.md','LICENSE','install.sh','uninstall.sh','a_clean_modern_high_contrast_user_interface_desi.png'):
        if (SOURCE/name).exists(): shutil.copy2(SOURCE/name, release/name)
    # Worktrees/archives may use umask 077. Application source must be readable by
    # nginx and the dedicated PHP/model users; secrets live outside this tree.
    for file in release.rglob('*'):
        os.chmod(file, 0o755 if file.is_dir() or file.name in ('install.sh', 'uninstall.sh') else 0o644)
    phpversion = run(['php','-r','echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;'], capture=True)
    write('/etc/tmpfiles.d/kienzletranslate.conf', 'd /run/kienzletranslate 0755 kienzletranslate kienzletranslate -\n')
    run(['systemd-tmpfiles','--create','/etc/tmpfiles.d/kienzletranslate.conf'])
    write(f'/etc/php/{phpversion}/fpm/pool.d/kienzletranslate.conf', '''[kienzletranslate]
user = kienzletranslate
group = kienzletranslate
listen = /run/kienzletranslate/php.sock
listen.owner = www-data
listen.group = www-data
listen.mode = 0660
pm = ondemand
pm.max_children = 8
pm.process_idle_timeout = 20s
pm.max_requests = 500
clear_env = yes
env[KIENZLE_CONFIG] = /etc/kienzletranslate/config.json
php_admin_value[memory_limit] = 128M
php_admin_value[post_max_size] = 16M
php_admin_value[upload_tmp_dir] = /run/kienzletranslate
php_admin_flag[display_errors] = off
php_admin_flag[log_errors] = off
''')
    write('/etc/systemd/system/kienzletranslate.service', f'''[Unit]
Description=kienzletranslate SeamlessM4T service
After=network.target
[Service]
Type=simple
User=kienzletranslate
Group=kienzletranslate
WorkingDirectory={root}/current
Environment=KIENZLE_CONFIG=/etc/kienzletranslate/config.json
Environment=HF_HUB_OFFLINE=1
Environment=TRANSFORMERS_OFFLINE=1
Environment=TOKENIZERS_PARALLELISM=false
Environment=HF_HOME=/var/lib/kienzletranslate/huggingface
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart={venv}/bin/python -m uvicorn backend.app:create_app --factory --host 127.0.0.1 --port {config['model_port']} --workers 1 --no-access-log
Restart=on-failure
RestartSec=3
TimeoutStopSec=120
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=/var/lib/kienzletranslate
UMask=0077
[Install]
WantedBy=multi-user.target
''')
    write('/etc/systemd/system/kienzletranslate-certificate.service', f'''[Unit]
Description=Renew kienzletranslate local TLS certificate
[Service]
Type=oneshot
ExecStart=/usr/bin/python3 {root}/current/deploy/install.py --renew-certificate
''')
    write('/etc/systemd/system/kienzletranslate-certificate.timer', '''[Unit]
Description=Check kienzletranslate local TLS certificate daily
[Timer]
OnCalendar=daily
Persistent=true
[Install]
WantedBy=timers.target
''')
    temp_link = root/'current.next'
    temp_link.symlink_to(release)
    os.replace(temp_link, root/'current')
    site = Path('/etc/nginx/sites-available/kienzletranslate')
    write(site, nginx_config(config))
    enabled = Path('/etc/nginx/sites-enabled/kienzletranslate')
    if not enabled.exists(): enabled.symlink_to(site)
    try:
        run(['nginx','-t'])
        run(['systemctl','daemon-reload'])
        run(['systemctl','enable','kienzletranslate.service','kienzletranslate-certificate.timer'])
        run(['systemctl','restart',f'php{phpversion}-fpm','kienzletranslate.service'])
        run(['systemctl','enable','--now','nginx','kienzletranslate-certificate.timer'])
        run(['systemctl','reload','nginx'])
        import urllib.request
        for attempt in range(20):
            try:
                req = urllib.request.Request(f'http://127.0.0.1:{config["model_port"]}/health', headers={'Authorization':'Bearer '+config['backend_token']})
                with urllib.request.urlopen(req, timeout=2) as response:
                    if response.status == 200: break
            except (OSError, TimeoutError): time.sleep(1)
        else: raise RuntimeError('healthcheck')
    except Exception:
        if previous:
            (root/'current').unlink()
            (root/'current').symlink_to(previous)
            if (backup/'config.json').exists(): shutil.copy2(backup/'config.json', CONFIG)
            if (backup/'kienzletranslate').exists(): shutil.copy2(backup/'kienzletranslate',site)
            if (backup/'tls').exists(): shutil.copytree(backup/'tls', CONFIG.parent/'tls', dirs_exist_ok=True)
            if (backup/'managed-files').exists():
                for file in (backup/'managed-files').rglob('*'):
                    if file.is_file(): shutil.copy2(file, Path('/')/file.relative_to(backup/'managed-files'))
                run(['systemctl','daemon-reload'])
            run(['systemctl','restart',f'php{phpversion}-fpm','kienzletranslate.service'])
            run(['systemctl','reload','nginx'])
        raise
    info = {'url':config['public_url'], 'setup_url':'http://'+host+(':'+str(config['http_port']) if config['http_port']!=80 else ''),
            'ca_fingerprint':config['ca_fingerprint'], 'version':VERSION, 'password_required':config['password_required']}
    if generated: info['initial_password'] = password
    elif config['password_required'] and not password and Path('/root/kienzletranslate-access.json').exists():
        prior_access = json.loads(Path('/root/kienzletranslate-access.json').read_text())
        if 'initial_password' in prior_access:
            info['initial_password'] = prior_access['initial_password']
    write('/root/kienzletranslate-access.json', json.dumps(info,indent=2)+'\n', 0o600)
    print(tr('Installation abgeschlossen.', 'Installation complete.'))
    print(tr('App: ', 'App: ')+info['url'])
    print(tr('iPad-Einrichtung: ', 'iPad setup: ')+info['setup_url'])
    print(config['ca_fingerprint'])
    if not config['password_required']: print(tr('Passwortschutz deaktiviert: direkter Zugang zur App.', 'Password protection disabled: open the app directly.'))
    if generated: print(tr('Erzeugtes Zugangspasswort: /root/kienzletranslate-access.json', 'Generated access password: /root/kienzletranslate-access.json'))
    print(tr('Vorhandene GPU-Dienste wurden durch diesen Installer nicht umkonfiguriert.', 'Existing GPU services were not reconfigured by this installer.'))


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        raise SystemExit('\nAbgebrochen / Cancelled')
    except (RuntimeError, OSError) as exc:
        raise SystemExit(f'Installation fehlgeschlagen / Installation failed ({exc}). /var/log/kienzletranslate-install.log')
