import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import deploy.uninstall as uninstall

from deploy.uninstall import (bool_answer, build_plan, managed_path, verify_plan)


CONFIG = {
    'install_path': '/opt/kienzletranslate',
    'model_path': '/var/lib/kienzletranslate/model',
    'lid_model_path': '/var/lib/kienzletranslate/lid-model',
}


class UninstallerTests(unittest.TestCase):
    def test_destructive_paths_are_restricted(self):
        self.assertEqual(managed_path('/opt/kienzletranslate', 'install'), Path('/opt/kienzletranslate'))
        for path in ('/', '/etc', '/etc/kienzletranslate', '/var/lib', '/opt', '/srv',
                     '/var/lib/../etc', 'relative/path'):
            with self.assertRaises(ValueError):
                managed_path(path, 'test')

    def test_removal_choices_require_json_booleans(self):
        self.assertFalse(bool_answer({}, 'remove_data'))
        self.assertTrue(bool_answer({'remove_data': True}, 'remove_data'))
        for value in ('true', 1, None):
            with self.assertRaises(ValueError):
                bool_answer({'remove_data': value}, 'remove_data')

    def test_default_plan_retains_data_and_models(self):
        plan = build_plan(CONFIG, php_root=Path('/nonexistent'))
        paths = {path for _, path in plan}
        self.assertIn(Path('/opt/kienzletranslate/releases'), paths)
        self.assertIn(Path('/opt/kienzletranslate/lid-venv'), paths)
        self.assertNotIn(Path('/etc/kienzletranslate'), paths)
        self.assertNotIn(Path('/var/lib/kienzletranslate/model'), paths)
        full = build_plan(CONFIG, remove_data=True, remove_models=True,
                          php_root=Path('/nonexistent'))
        full_paths = {path for _, path in full}
        self.assertIn(Path('/etc/kienzletranslate'), full_paths)
        self.assertIn(Path('/var/lib/kienzletranslate/model'), full_paths)
        self.assertIn(Path('/var/lib/kienzletranslate/lid-model'), full_paths)

    def test_foreign_managed_file_is_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            unit = Path(directory).resolve()/'kienzletranslate.service'
            unit.write_text('[Service]\nExecStart=/foreign/server\n')
            with self.assertRaises(RuntimeError):
                verify_plan(CONFIG, [('service', unit)])
            unit.write_text('[Service]\nEnvironment=KIENZLE_CONFIG=/etc/kienzletranslate/config.json\n')
            verify_plan(CONFIG, [('service', unit)])

    def test_model_and_symlink_safety(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            model = base/'model'
            model.mkdir()
            (model/'config.json').write_text('{}')
            with self.assertRaises(RuntimeError):
                verify_plan(CONFIG, [('model', model)])
            (model/'weights.safetensors').write_bytes(b'x')
            verify_plan(CONFIG, [('model', model)])
            link = base/'linked-model'
            link.symlink_to(model, target_is_directory=True)
            with self.assertRaises(RuntimeError):
                verify_plan(CONFIG, [('model', link)])

    def test_overlapping_model_and_managed_paths_are_rejected(self):
        config = dict(CONFIG, model_path='/opt/kienzletranslate/releases/model')
        with self.assertRaises(RuntimeError):
            verify_plan(config, build_plan(config, php_root=Path('/nonexistent')))
        config = dict(CONFIG, model_path='/var/lib/kienzletranslate')
        with self.assertRaises(RuntimeError):
            verify_plan(config, build_plan(config, remove_models=True, php_root=Path('/nonexistent')))

    def test_removal_in_sandbox_preserves_defaults_and_removes_opted_in_data(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory).resolve()
            root=base/'app'; release=root/'releases'/'v1.6'
            (release/'deploy').mkdir(parents=True)
            (release/'deploy/install.py').write_text('# marker')
            (release/'backend').mkdir()
            (root/'current').symlink_to(release)
            (root/'notes.txt').write_text('unrelated file')
            configdir=base/'config'; configdir.mkdir()
            (configdir/'config.json').write_text('{}')
            (root/'backups').mkdir()
            model=base/'model'; model.mkdir()
            (model/'config.json').write_text('{}'); (model/'weights.safetensors').write_bytes(b'x')
            lid=base/'lid-model'; lid.mkdir()
            for name in ('config.json','model.bin','tokenizer.json'): (lid/name).write_text('{}')
            config=dict(install_path=str(root),model_path=str(model),lid_model_path=str(lid))
            overrides={
                'CONFIG':configdir/'config.json','CONFIG_DIR':configdir,
                'ACCESS_FILE':base/'access.json','INSTALL_LOG':base/'install.log',
                'NGINX_SITE':base/'nginx/site','NGINX_ENABLED':base/'nginx/enabled',
                'TMPFILES':base/'tmpfiles.conf','RUNTIME_DIR':base/'run',
                'PUBLIC_CA':base/'ca.cer','SYSTEMD_DIR':base/'systemd',
            }
            with patch.multiple(uninstall,**overrides), patch.object(uninstall,'managed_path',side_effect=lambda value,label:Path(value)), patch.object(uninstall,'command',return_value=0):
                plan=uninstall.build_plan(config,php_root=base/'php')
                uninstall.verify_plan(config,plan)
                uninstall.execute(plan,config)
                self.assertFalse((root/'releases').exists())
                self.assertTrue(model.exists() and lid.exists() and configdir.exists())
                self.assertTrue((root/'backups').exists() and (root/'notes.txt').exists())
                plan=uninstall.build_plan(config,True,True,php_root=base/'php')
                uninstall.verify_plan(config,plan)
                uninstall.execute(plan,config)
                self.assertFalse(model.exists() or lid.exists() or configdir.exists())
                self.assertTrue((root/'notes.txt').exists())


if __name__ == '__main__':
    unittest.main()
