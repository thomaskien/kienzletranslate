import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock
from deploy.install import (bool_setting, integer_setting, validate, nginx_config,
                            password_setting, preflight_space)

BASE = dict(server_ip='10.0.83.140',server_name='',http_port=80,https_port=443,model_port=8765,
            install_path='/opt/kienzletranslate',model_path='/var/lib/kienzletranslate/model',
            lid_model_path='/var/lib/kienzletranslate/lid-model',public_url='https://10.0.83.140',
            model_autoload=False,model_load_on_use=True,model_auto_unload=True,
            model_disconnect_seconds=90,model_idle_seconds=300,model_min_free_mib=8192)


class InstallerTests(unittest.TestCase):
    def test_password_optional_default_and_update_preservation(self):
        self.assertFalse(password_setting({}, {}))
        self.assertTrue(password_setting({'password_hash':'old'}, {}))
        self.assertFalse(password_setting({'password_hash':'old'}, {'password_required':False}))
        self.assertFalse(password_setting({'password_hash':'old','password_required':False}, {}))
        self.assertTrue(password_setting({}, {'password_required':True}))
        with self.assertRaises(ValueError): password_setting({}, {'password_required':'false'})
    def test_model_defaults_update_preservation_and_types(self):
        self.assertFalse(bool_setting({}, {}, 'model_autoload', False))
        self.assertTrue(bool_setting({'model_autoload':True}, {}, 'model_autoload', False))
        self.assertFalse(bool_setting({'model_autoload':True}, {'model_autoload':False}, 'model_autoload', False))
        self.assertEqual(integer_setting({}, {}, 'model_idle_seconds', 300, 60, 86400), 300)
        self.assertEqual(integer_setting({'model_idle_seconds':600}, {}, 'model_idle_seconds', 300, 60, 86400), 600)
        for value in (59, 86401, True, '300', 'not-a-number'):
            with self.assertRaises(ValueError):
                integer_setting({}, {'model_idle_seconds':value}, 'model_idle_seconds', 300, 60, 86400)
    def test_confirmation_de_en_and_rejection(self):
        legacy = {key:value for key,value in BASE.items()
                  if key not in ('lid_model_path', 'model_autoload', 'model_load_on_use',
                                 'model_auto_unload', 'model_disconnect_seconds',
                                 'model_idle_seconds', 'model_min_free_mib')}
        for language, word in [('de','AKZEPTIEREN'),('en','ACCEPT'),('de',''),('en','accept')]:
            result = subprocess.run([sys.executable,'deploy/install.py','--answers','-','--check'],
                input=json.dumps({**legacy,'language':language,'license_acceptance':word}),text=True,capture_output=True)
            self.assertEqual(result.returncode,0 if word in ['AKZEPTIEREN','ACCEPT'] else 1)
    def test_bad_names_conflicting_ports_and_paths_rejected(self):
        for change in [dict(server_name='*'),dict(https_port=80),dict(model_port=65536),dict(server_ip='invalid'),
                       dict(install_path='/'),dict(model_path='/opt/../etc'),dict(lid_model_path='/etc/lid'),
                       dict(lid_model_path='/var/lib/kienzletranslate/model'),
                       dict(model_disconnect_seconds=29),dict(model_idle_seconds=86401),
                       dict(model_min_free_mib=1023),dict(model_autoload='false')]:
            with self.assertRaises(ValueError): validate({**BASE,**change})
    def test_custom_ports_and_ram_upload_configuration(self):
        config={**BASE,'http_port':8080,'https_port':8443,'public_url':'https://10.0.83.140:8443'}
        text=nginx_config(validate(config))
        self.assertIn('listen 8080;',text)
        self.assertIn('listen 8443 ssl;',text)
        self.assertIn('fastcgi_request_buffering off;',text)
        self.assertIn('access_log off;',text)
    def test_preflight_combines_budgets_for_one_filesystem(self):
        config={**BASE,'install_path':'/opt/kt-space-test','model_path':'/var/lib/kt-space-test/model',
                'lid_model_path':'/var/lib/kt-space-test/lid-model'}
        with mock.patch('deploy.install.existing_ancestor', return_value=Path('/')):
            with mock.patch('deploy.install.shutil.disk_usage', return_value=mock.Mock(free=10)):
                with self.assertRaises(RuntimeError): preflight_space(config)
    def test_check_accepts_new_defaults_without_system_changes(self):
        answers={**BASE,'language':'en','license_acceptance':'ACCEPT'}
        result=subprocess.run([sys.executable,'deploy/install.py','--answers','-','--check'],
            input=json.dumps(answers),text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('No system changes',result.stdout)
        answers.update(password_required=True,password='short')
        result=subprocess.run([sys.executable,'deploy/install.py','--answers','-','--check'],
            input=json.dumps(answers),text=True,capture_output=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('at least 12',result.stderr)


if __name__ == '__main__': unittest.main()
