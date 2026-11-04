#!/usr/bin/env python3
"""Exercise each catalog preset with text matching its language, without studio mutations."""
import argparse
from datetime import datetime,timezone
import importlib.util
import json
import hashlib
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from voice_cloner import models
spec=importlib.util.spec_from_file_location('inference_qa',ROOT/'scripts/verify-model-inference.py')
qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
TEXTS={
'en':'Hello. This is a clear and natural voice recording.',
'es':'Hola. Esta es una grabación de voz clara y natural.',
'fr':'Bonjour. Ceci est un enregistrement vocal clair et naturel.',
'hi':'नमस्ते। यह एक स्पष्ट और स्वाभाविक आवाज की रिकॉर्डिंग है।',
'it':'Ciao. Questa è una registrazione vocale chiara e naturale.',
'ja':'こんにちは。これは自然で聞き取りやすい音声のテストです。',
'pt':'Olá. Esta é uma gravação de voz clara e natural.',
'zh':'你好。这是一段清晰自然的语音测试。',
'ru':'Здравствуйте. Это проверка ясной и естественной речи.'}
KOKORO_LANG={'a':'en','b':'en','e':'es','f':'fr','h':'hi','i':'it','j':'ja','p':'pt','z':'zh'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('model');parser.add_argument('--presets',nargs='*')
    parser.add_argument('--directory',type=Path,default=ROOT/'.runtime/release-audit')
    parser.add_argument('--runtime-root',type=Path,default=ROOT)
    args=parser.parse_args();model=models.model_for(args.model)
    if not model or not model.get('presetVoices') or not models.ready(model,ROOT):raise ValueError('Select an installed catalog model with presets')
    directory=args.directory.resolve();directory.mkdir(parents=True,exist_ok=True)
    app=qa.workspace(directory,runtime_root=args.runtime_root.resolve());path=directory/(model['id']+'-presets.json')
    report={'scope':'Actual per-preset output, not a perceptual-quality or release certificate','model':model['id'],'cases':{}}
    if path.is_file():report=json.loads(path.read_text())
    report['runtimeRoot']=str(args.runtime_root.resolve())
    fingerprint=hashlib.sha256(b''.join(p.read_bytes() for p in sorted((ROOT/'src/voice_cloner').glob('*.py')))+(ROOT/'src/voice_cloner/model-catalog.json').read_bytes()).hexdigest()
    for preset in args.presets or model['presetVoices']:
        if preset not in model['presetVoices']:raise ValueError('Unknown preset')
        if report['cases'].get(preset,{}).get('status')=='passed' and report['cases'][preset].get('sourceFingerprint')==fingerprint:continue
        language=KOKORO_LANG[preset[0]] if model['adapter']=='kokoro' else 'ru' if model['languages']==['ru'] else 'en'
        row={'sourceFingerprint':fingerprint,'preset':preset,'language':language,'startedAt':datetime.now(timezone.utc).isoformat(),'status':'running'}
        report['cases'][preset]=row;qa.atomic_json(path,report)
        try:row.update(qa.generate(model,TEXTS[language],app,directory,language=language,preset=preset,case_id=model['id']+'-'+preset),status='passed')
        except Exception as exc:row.update(status='failed',error=str(exc))
        row['completedAt']=datetime.now(timezone.utc).isoformat();qa.atomic_json(path,report)
        print(preset,row['status'],row.get('error','')[:250],flush=True)
    return int(any(r['status']!='passed' for r in report['cases'].values()))


if __name__=='__main__':raise SystemExit(main())
