"""Small PHP boundary test: anonymous sessions must not become authenticated later."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class WebSessionTests(unittest.TestCase):
    def test_access_modes_and_signed_cookie(self):
        lib = json.dumps(str(Path('web/lib.php').resolve()))
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp)/'config.json'
            for protected, authenticated, expected in [(False,False,True),(True,False,False),(True,True,True)]:
                config.write_text(json.dumps({'session_secret':'test-secret-32-characters-long-value','password_required':protected}))
                code = f'require {lib}; $sid = str_repeat("a",32); $_COOKIE["kt_session"] = session_cookie_value($sid, {str(authenticated).lower()}); echo json_encode([session_identity() === $sid, csrf_token($sid)]);'
                result = subprocess.run(['php','-r',code],env={**os.environ,'KIENZLE_CONFIG':str(config)},capture_output=True,text=True,check=True)
                accepted, csrf = json.loads(result.stdout)
                self.assertEqual(accepted, expected)
                self.assertEqual(len(csrf),64)


if __name__ == '__main__': unittest.main()
