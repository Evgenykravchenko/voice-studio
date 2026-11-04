"""File-based offline voice conversion and restoration. No implicit transcription."""
import array
from pathlib import Path
import subprocess
import wave
from .cli import PROJECT_DIR, _load_profile
from .models import snapshot


def process(model,job):
    import numpy as np
    import torch
    import soundfile as sf
    torch.set_num_threads(min(8,__import__('os').cpu_count() or 1))
    torch.manual_seed(job['seed'])
    folder=PROJECT_DIR/'data/studio/inputs'/job['sourceId']
    source=folder/'source';normalized=folder/(job['id']+'.wav')
    try:
        try:
            subprocess.run([str(PROJECT_DIR/'.runtime/bin/ffmpeg'),'-nostdin','-hide_banner','-loglevel','error','-y',
                '-protocol_whitelist','file,pipe','-format_whitelist','wav,mp3,mov,flac,ogg,aac,aiff,matroska,webm','-i',str(source),'-t','181','-vn','-ac','1','-ar','44100','-c:a','pcm_s16le',str(normalized)],check=True,capture_output=True,timeout=90)
        except (subprocess.SubprocessError,OSError) as exc:
            raise ValueError('Не удалось прочитать аудио. Проверьте файл и загрузите запись заново.') from exc
        with wave.open(str(normalized),'rb') as reader:
            if reader.getnframes()/reader.getframerate()>180:raise ValueError('Для обработки выберите запись длительностью до трёх минут.')
        path=snapshot(model)/model.get('artifactSubdir','')
        if model['adapter']=='openvoice':
            from openvoice.api import ToneColorConverter
            converter=ToneColorConverter(str(path/'converter/config.json'),device='cpu',enable_watermark=False)
            converter.load_ckpt(str(path/'converter/checkpoint.pth'))
            _,reference=_load_profile(job['voiceId'])
            embedding_source=folder/(job['id']+'-speaker.wav')
            with wave.open(str(normalized),'rb') as reader,wave.open(str(embedding_source),'wb') as writer:
                writer.setparams(reader.getparams());writer.writeframes(reader.readframes(20*reader.getframerate()))
            try:
                source_se=converter.extract_se([str(embedding_source)])
                target_se=converter.extract_se([str(reference)])
                output=converter.convert(str(normalized),src_se=source_se,tgt_se=target_se,message=None)
                return converter.hps.data.sampling_rate,np.asarray(output,dtype=np.float32)
            finally:embedding_source.unlink(missing_ok=True)
        from resemble_enhance.enhancer.inference import enhance
        audio,rate=sf.read(str(normalized),dtype='float32')
        with torch.inference_mode():output,rate=enhance(torch.from_numpy(audio),rate,'cpu',nfe=32,run_dir=path/'enhancer_stage2')
        return rate,output.cpu().numpy()
    finally:normalized.unlink(missing_ok=True)
