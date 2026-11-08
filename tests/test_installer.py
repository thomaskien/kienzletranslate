import json
from pathlib import Path
import subprocess
import sys
import unittest
from deploy.install import validate, nginx_config

BASE = dict(server_ip='10.0.83.140',server_name='',http_port=80,https_port=443,model_port=8765,
            install_path='/opt/kienzletranslate',model_path='/var/lib/kienzletranslate/model',public_url='https://10.0.83.140')


class InstallerTests(unittest.TestCase):
    def test_confirmation_de_en_and_rejection(self):
        for language, word in [('de','AKZEPTIEREN'),('en','ACCEPT'),('de',''),('en','accept')]:
            result = subprocess.run([sys.executable,'deploy/install.py','--answers','-','--check'],
                input=json.dumps({**BASE,'language':language,'license_acceptance':word}),text=True,capture_output=True)
            self.assertEqual(result.returncode,0 if word in ['AKZEPTIEREN','ACCEPT'] else 1)
    def test_bad_names_conflicting_ports_and_paths_rejected(self):
        for change in [dict(server_name='*'),dict(https_port=80),dict(model_port=65536),dict(server_ip='invalid'),dict(install_path='/'),dict(model_path='/opt/../etc')]:
            with self.assertRaises(ValueError): validate({**BASE,**change})
    def test_custom_ports_and_ram_upload_configuration(self):
        config={**BASE,'http_port':8080,'https_port':8443,'public_url':'https://10.0.83.140:8443'}
        text=nginx_config(validate(config))
        self.assertIn('listen 8080;',text)
        self.assertIn('listen 8443 ssl;',text)
        self.assertIn('fastcgi_request_buffering off;',text)
        self.assertIn('access_log off;',text)


if __name__ == '__main__': unittest.main()
