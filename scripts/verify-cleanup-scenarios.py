#!/usr/bin/env python3
"""Real cleanup of anonymous speech mixed with supplied, hash-verified noise recordings.

Technical/noise measurements are not perceptual or transcript-fidelity certificates.
The caller supplies a local noise manifest; this script never downloads or ships media.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import uuid
import wave

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from voice_cloner import models
from voice_cloner.enhancement import DEFAULTS
from voice_cloner.transcription import read_audio
spec=importlib.util.spec_from_file_location('inference_qa',ROOT/'scripts/verify-model-inference.py')
qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
RATE=44100
NATURAL=dict(noiseReduction=100,strength=0,clarity=0,warmth=0,deEss=0,leveling=False,protectPeaks=False)


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def write(path,audio):
    with wave.open(str(path),'wb') as writer:
        writer.setparams((1,2,RATE,0,'NONE','not compressed'))
        writer.writeframes((np.clip(audio,-1,1)*32767).astype('<i2').tobytes())


def rms(audio):return float(np.sqrt(np.mean(np.asarray(audio,dtype=np.float64)**2)))
def db(ratio):return float(20*np.log10(max(ratio,1e-12)))


def metrics(before,after,clean):
    # Noise-only margins and the known speech interval; do not call this output SNR.
    n=len(before);windows=np.r_[np.arange(RATE//5,4*RATE//5),np.arange(n-4*RATE//5,n-RATE//5)]
    voice=slice(RATE,n-RATE)
    residual=rms(after[windows]);floor=1/65536
    raw=db(rms(before[windows])/max(residual,floor))
    gain=db(rms(after[voice])/max(rms(before[voice]),1e-12))
    truth=clean[voice].astype(np.float64);result=after[voice].astype(np.float64)
    truth-=truth.mean();result-=result.mean()
    projected=truth*(np.dot(result,truth)/max(np.dot(truth,truth),1e-12))
    score=db(rms(projected)/max(rms(result-projected),1e-12))
    return dict(noiseOnlyReductionDb=raw,speechRegionRmsChangeDb=gain,
                noiseReductionRelativeToSpeechDb=raw+gain,zeroLagSiSdrDb=score,
                noiseAfterCensoredAtPcm16Floor=residual<floor,
                noiseMeasurementRule='pcm16-floor-v2; censored reductions are lower bounds',
                clippedFraction=float(np.mean(np.abs(after)>=32760/32768)))


def remeasure(directory):
    report_path=directory/'inference.json';report=json.loads(report_path.read_text())
    for case,row in list(report['models'].items()):
        if row.get('status')!='passed' or not row.get('settings'):continue
        source=directory/'app/data/studio/inputs'/row['job']['sourceId']
        if digest(source/'source')!=row['sourceSha256']:raise ValueError('Source fixture changed after inference')
        before=read_audio(source/'source',RATE);truth=read_audio(source/'clean.wav',RATE);after=read_audio(directory/row['audio'],RATE)
        if len(before)!=len(after):raise ValueError('Recording duration changed')
        row['noiseMeasurements']=metrics(before,after,truth)
        row['measurementScriptSha256']=digest(Path(__file__))
        name=case.rsplit('-',1)[0]+'-before'
        report['models'].setdefault(name,dict(status='passed',job=row['job'],expectedText=row['expectedText'],
             sourceFingerprint=row['sourceFingerprint'],audio=str((source/'source').relative_to(directory)),baseline=True,
             inputSnrDb=row['inputSnrDb'],sourceSha256=row['sourceSha256']))
        language=row['job']['language'];clean=directory/'app/data/profiles'/('qa-'+language)/'reference.wav'
        report['models'].setdefault(language+'-clean-before',dict(status='passed',job=row['job'],expectedText=row['expectedText'],
             sourceFingerprint=row['sourceFingerprint'],audio=str(clean.relative_to(directory)),baseline=True,sourceSha256=digest(clean)))
    report['measurementRule']='PCM16-floor-v2; no inferred suppression beyond the output quantization floor'
    qa.atomic_json(report_path,report)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--noise-manifest',type=Path,required=True)
    parser.add_argument('--snr',nargs='+',type=int,default=[10,20])
    parser.add_argument('--languages',nargs='+',choices=['ru','en'],default=['ru','en'])
    parser.add_argument('--directory',type=Path,default=ROOT/'.runtime/release-audit/cleanup-scenarios')
    parser.add_argument('--repeat',action='store_true')
    parser.add_argument('--measure-only',action='store_true',help='Recompute bounded measurements/add input baselines without any model inference')
    args=parser.parse_args();directory=args.directory.resolve()
    if args.measure_only:
        remeasure(directory);return 0
    app=qa.workspace(directory)
    manifest=args.noise_manifest.resolve();noises=json.loads(manifest.read_text())
    model=models.model_for('resemble-enhance')
    if not models.ready(model,app):raise ValueError('Install Resemble Enhance before running this opt-in verification')
    sources=[]
    for item in noises['files']:
        name=item['filename']
        if Path(name).name!=name:raise ValueError('Noise filename must not contain directories')
        source=manifest.parent/name
        if digest(source)!=item['sha256']:raise ValueError('Noise recording checksum mismatch')
        audio=read_audio(source,RATE)
        if not audio.size or not np.isfinite(audio).all() or rms(audio)<1e-6:raise ValueError('Empty or silent noise fixture')
        sources.append((item,audio))
    fingerprint=hashlib.sha256(b''.join(p.read_bytes() for p in sorted((ROOT/'src/voice_cloner').glob('*.py')))
                              +manifest.read_bytes()+Path(__file__).read_bytes()).hexdigest()
    report_path=directory/'inference.json'
    report=json.loads(report_path.read_text()) if report_path.is_file() else {'scope':__doc__,'models':{}}
    report.update(sourceFingerprint=fingerprint,noiseProvenance=noises)
    for language in args.languages:
        text=qa.RU_REFERENCE if language=='ru' else qa.EN_REFERENCE
        name='qa-'+language;old=ROOT/'.runtime/release-audit/app/data/profiles'/name;target=app/'data/profiles'/name
        if not target.exists() and (old/'profile.json').is_file() and json.loads((old/'profile.json').read_text())['reference_text']==text:
            shutil.copytree(old,target)
        voice=qa.fixture('piper-dmitri' if language=='ru' else 'kokoro',text,name,language,app,directory)
        speech=read_audio(voice,RATE);clean=np.pad(speech,(RATE,RATE))
        for item,recording in sources:
            for snr in args.snr:
                key=f"{language}-{item['category']}-snr{snr}";base_id=None;source_id=None;before=None;source_hash=None
                for label,settings in [('natural',NATURAL),('default',DEFAULTS)]:
                    case=key+'-'+label;previous=report['models'].get(case,{})
                    if previous.get('status')=='passed' and previous.get('sourceFingerprint')==fingerprint and not args.repeat:continue
                    if source_id is None:
                        noise=np.resize(recording,len(clean));noise=noise*(rms(speech)/rms(noise[RATE:-RATE])*10**(-snr/20))
                        scale=min(1.,.85/max(float(np.max(np.abs(clean+noise))),1e-12));before=(clean+noise)*scale;truth=clean*scale
                        source_id=str(uuid.uuid4());folder=app/'data/studio/inputs'/source_id;folder.mkdir(parents=True)
                        write(folder/'source',before);write(folder/'clean.wav',truth)
                        # This marker selects the actual studio cleanup route, not legacy restoration.
                        qa.atomic_json(folder/'cleanup.json',{'maxDuration':7200})
                        source_hash=digest(folder/'source')
                    job_id=str(uuid.uuid4());config=app/'data/studio/cleanups'/(job_id+'.json')
                    qa.atomic_json(config,{'options':settings,**({'baseId':base_id} if base_id else {})})
                    job=dict(id=job_id,modelId=model['id'],sourceId=source_id,text='',voiceId=None,language=language,emotion='calm',seed=42)
                    row=dict(status='running',job=job,expectedText=text,sourceFingerprint=fingerprint,inputSnrDb=snr,
                             noiseSha256=item['sha256'],settings=settings,sourceSha256=source_hash)
                    report['models'][case]=row;qa.atomic_json(report_path,report);print(case,'starting',flush=True)
                    try:
                        artifacts=qa.artifact_state(model,app)
                        events,seconds=qa.run([str(app/'.venv/bin/python'),'-u','-c',qa.GENERATE_CODE],job,'mlx-speech',app,directory/(case+'.log'),900)
                        if events[-1]['event']!='completed':raise ValueError('Cleanup did not complete')
                        output=app/'outputs/studio'/(job_id+'.wav');analysis=json.loads(output.with_suffix('.analysis.json').read_text())
                        if analysis['pipeline']!='separate-noise-v2' or analysis['options']!=settings:raise ValueError('Wrong cleanup pipeline or ignored settings')
                        if base_id is None and not {'denoising','restoring'}<={e.get('stage') for e in events}:raise ValueError('Actual denoise/restoration stages were not executed')
                        if artifacts!=qa.artifact_state(model,app) or not models.ready(model,app):raise ValueError('Cleanup changed pinned model artifacts')
                        after=read_audio(output,RATE)
                        if len(after)!=len(before):raise ValueError('Cleanup changed recording duration')
                        row.update(status='passed',audio=str(output.relative_to(directory)),seconds=seconds,metrics=qa.audio_metrics(output),
                                   noiseMeasurements=metrics(before,after,truth),analysis=analysis,cached=base_id is not None)
                        if base_id is None:base_id=job_id
                    except Exception as exc:row.update(status='failed',error=str(exc))
                    finally:
                        if digest(folder/'source')!=source_hash:raise ValueError('Cleanup modified its source recording')
                        qa.atomic_json(report_path,report)
                    print(case,row['status'],row.get('error') or row.get('noiseMeasurements'),flush=True)
    remeasure(directory)
    return int(any(r.get('status')!='passed' for r in report['models'].values()))


if __name__=='__main__':raise SystemExit(main())
