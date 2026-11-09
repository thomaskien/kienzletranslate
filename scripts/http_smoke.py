"""Run on the installed server. Verifies TLS, consent, auth and the public API.

The short synthetic-silence recording checks transport/lifecycle only; translation
quality is checked separately with synthetic spoken DE/EN samples in gpu_smoke.py.
No credentials are printed.
"""
import http.cookiejar
import io
import json
from pathlib import Path
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import wave


def main():
    config=json.loads(Path('/etc/kienzletranslate/config.json').read_text())
    access=json.loads(Path('/root/kienzletranslate-access.json').read_text())
    context=ssl.create_default_context(cafile='/etc/kienzletranslate/tls/ca.pem')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPSHandler(context=context),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    checks=[]
    def call(url,method='GET',data=None,headers=None):
        req=urllib.request.Request(url,data=data,headers=headers or {},method=method)
        try:
            with opener.open(req,timeout=30) as response: return response.status,response.headers,response.read()
        except urllib.error.HTTPError as exc: return exc.code,exc.headers,exc.read()
    def api(route,method='GET',data=None,headers=None):
        return call(config['public_url']+'/api.php?route='+route,method,data,headers)
    status,headers,body=call(access['setup_url'])
    assert status==200 and b'AKZEPTIEREN' in body
    checks.append('HTTP setup displays licence')
    status,headers,body=call(access['setup_url']+'/setup.php','POST',b'confirmation=wrong',{'Content-Type':'application/x-www-form-urlencoded'})
    assert status==200 and headers.get_content_type()=='text/html'
    status,headers,body=call(access['setup_url']+'/setup.php','POST',b'confirmation=AKZEPTIEREN',{'Content-Type':'application/x-www-form-urlencoded'})
    assert status==200 and body==Path(config['ca_public_path']).read_bytes()
    checks.append('CA download requires exact licence word')
    status,headers,body=call(config['public_url'])
    assert status==200 and b'kienzletranslate' in body
    checks.append('HTTPS chain and IP SAN verified')
    assert api('health')[0]==401
    status,headers,body=api('bootstrap')
    bootstrap=json.loads(body)
    protected=config.get('password_required',bool(config.get('password_hash')))
    if protected:
        assert bootstrap['authenticated'] is False
        status,headers,body=api('login','POST',json.dumps({'password':access['initial_password']}).encode(),{'Content-Type':'application/json'})
        assert status==200,body
    else:
        assert bootstrap['authenticated'] is True and bootstrap['password_required'] is False
    cookie_header=headers.get('Set-Cookie','').lower()
    assert 'httponly' in cookie_header and 'secure' in cookie_header
    bootstrap=json.loads(api('bootstrap')[2])
    assert bootstrap['authenticated'] and len(bootstrap['languages'])==96
    checks.append(('Login' if protected else 'Password-free bootstrap')+', secure cookie, 96 languages')
    assert api('model/load','POST')[0]==403
    headers={'X-CSRF-Token':bootstrap['csrf']}
    assert api('model/load','POST',headers=headers)[0]==200
    for _ in range(40):
        health=json.loads(api('health')[2])
        if health['state']=='ready':break
        time.sleep(.5)
    assert health['state']=='ready',health
    checks.append('CSRF enforced; model loads through PHP')
    buffer=io.BytesIO()
    with wave.open(buffer,'wb') as output:
        output.setnchannels(1);output.setsampwidth(2);output.setframerate(48000);output.writeframes(b'\0\0'*24000)
    uid=str(uuid.uuid4())
    params=urllib.parse.urlencode(dict(utterance_id=uid,speaker_side='bottom',source_lang='eng',target_lang='deu',tts='0',generation=1))
    status,_,body=api('utterances&'+params,'POST',buffer.getvalue(),{**headers,'Content-Type':'audio/wav'})
    assert status==202,(status,body)
    for _ in range(60):
        result=json.loads(api('utterances/'+uid)[2])
        if result['status'] in ['complete','error']:break
        time.sleep(.5)
    assert result['status']=='complete',result
    checks.append('Raw WAV upload, queued inference, result through HTTPS/PHP')
    assert api('session','DELETE',headers=headers)[0]==200
    assert api('utterances/'+uid)[0]==404
    assert api('model/unload','POST',headers=headers)[0]==200
    for _ in range(40):
        health=json.loads(api('health')[2])
        if health['state']=='unloaded':break
        time.sleep(.25)
    assert health['state']=='unloaded',health
    assert api('logout','POST',headers=headers)[0]==200
    assert api('health')[0]==401
    checks.append('Session cleanup, model unload and logout')
    report={'status':'passed','checks':checks}
    Path('/var/lib/kienzletranslate/http-smoke.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
