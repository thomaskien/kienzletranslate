"""One real model lifecycle test using synthetic speech from the same checkpoint."""
import json
from pathlib import Path
import subprocess
import time
import torch
from backend.model import Model
from backend.audio import encode_wav


def memory():
    return int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],text=True).splitlines()[0])


def main():
    model=Model('/var/lib/kienzletranslate/model')
    report={'before_mib':memory(),'checkpoint':'5f8cc790b19fc3f67a61c105133b20b34e3dcb76','tests':[]}
    started=time.monotonic()
    model.load()
    report['load_seconds']=round(time.monotonic()-started,3)
    report['loaded_mib']=memory()
    samples={}
    for lang,text in [('deu','Guten Morgen. Ich möchte einen Termin vereinbaren.'),('eng','Good morning. I would like to make an appointment.')]:
        inputs=model.processor(text=text,src_lang=lang,return_tensors='pt').to('cuda')
        with torch.inference_mode():
            generated=model.model.generate(**inputs,tgt_lang=lang,generate_speech=True)
        samples[lang]=encode_wav(generated[0][0].float().cpu().numpy(),model.model.config.sampling_rate)
        del inputs,generated
    for source,target,tts in [('deu','eng',False),('eng','deu',True),('eng','ell',True)]:
        result,audio=model.translate(samples[source],source,target,tts)
        assert result['original_text'].strip() and result['translated_text'].strip()
        assert bool(audio)==(tts and target!='ell')
        if target=='ell': assert result['text_only_reason']
        report['tests'].append(result)
        del audio
    model.unload()
    report['unloaded_mib']=memory()
    assert report['loaded_mib']-report['unloaded_mib']>3000, 'GPU memory was not released'
    model.load()
    result,audio=model.translate(samples['deu'],'deu','eng',False)
    assert result['translated_text'].strip()
    report['reload_translation']=result
    model.unload()
    report['final_mib']=memory()
    report['status']='passed'
    Path('/var/lib/kienzletranslate/gpu-smoke.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__': main()
