"""Explicit model-family adapters. A common interface does not imply common controls."""
from pathlib import Path
from .cli import PROJECT_DIR
from .models import snapshot, file_path, synthesis_mode

LANGUAGES = {'ru':'Russian','en':'English','zh':'Chinese','ja':'Japanese','ko':'Korean','de':'German','fr':'French','es':'Spanish','pt':'Portuguese','it':'Italian','auto':'auto'}
LANGUAGES.update({'yue':'Cantonese','ar':'Arabic','tr':'Turkish','id':'Indonesian','nl':'Dutch','vi':'Vietnamese','uk':'Ukrainian','th':'Thai','pl':'Polish','ro':'Romanian','el':'Greek','cs':'Czech','fi':'Finnish','hi':'Hindi','ms':'Malay','sv':'Swedish','da':'Danish','fil':'Filipino','fa':'Persian','hu':'Hungarian','mk':'Macedonian'})
EMOTIONS = {'excited':'Speak with strong excitement and joy.','whisper':'Speak in a quiet whisper.','laughing':'Speak playfully, laughing.','angry':'Speak angrily.','calm':'Speak calmly and naturally.'}


def component(model, repo, subdir=''):
    file = next(item for item in model['files'] if item.get('repo',model['repo']) == repo)
    return file_path(model,file).parents[len(Path(file['path']).parts)-1] / subdir


def load(model, job, reference=None, profile=None):
    """Return (sample rate, synthesizer yielding mono arrays). Called inside local_resources."""
    import numpy as np
    family = model.get('adapter','piper' if model['runtime']=='piper' else 'qwen')
    path = snapshot(model) / model.get('artifactSubdir','')
    seed = job['seed']
    instruction = job.get('voiceDescription','') or EMOTIONS[job.get('emotion','calm')]
    if job.get('voiceDescription') and job.get('emotion','calm')!='calm':
        instruction+=' '+EMOTIONS[job['emotion']]
    mode = synthesis_mode(model,job)
    preset = job.get('presetVoice') or (model.get('presetVoices') or [None])[0]
    language = job.get('language','auto')
    if family == 'piper':
        import os
        import piper
        # espeak's native path buffer is short. Resolve the environment symlink and
        # use a relative path so a deeply nested project still loads its dictionaries.
        espeak_data = Path(os.path.relpath(Path(piper.__file__).resolve().parent / 'espeak-ng-data'))
        if not (espeak_data / 'phontab').is_file():
            raise ValueError('В окружении Piper отсутствуют фонетические данные. Повторите установку модели.')
        os.environ['ESPEAK_DATA_PATH'] = str(espeak_data)
        from piper import PiperVoice
        voice = PiperVoice.load(str(next(file_path(model,f) for f in model['files'] if f['path'].endswith('.onnx'))), espeak_data_dir=espeak_data)
        return voice.config.sample_rate, lambda text: (chunk.audio_float_array for chunk in voice.synthesize(text))
    if family in {'firered','longcat','dots','vibevoice-speech','moss-sfx'}:
        import mlx.core as mx
        import mlx_speech
        mx.random.seed(seed)
        options = {}
        if model.get('codecRepo'): options['codec_path_or_repo'] = str(component(model,model['codecRepo'],model.get('codecSubdir','')))
        if family=='vibevoice-speech':
            from .vibevoice_checkpoint import load as load_vibevoice_model
            from mlx_speech.models.vibevoice.tokenizer import VibeVoiceTokenizer
            from mlx_speech.tts._adapters.vibevoice import VibeVoiceAdapter
            loaded=load_vibevoice_model(path)
            tokenizer_path=component(model,model['tokenizerRepo']) if model.get('tokenizerRepo') else loaded.model_dir
            voice=VibeVoiceAdapter(loaded.model,VibeVoiceTokenizer.from_path(tokenizer_path),loaded.config.sampling_rate)
        else:
            voice = mlx_speech.tts.load(str(path),**options)
        def synthesize(text):
            options = dict(max_new_tokens=2048)
            if mode == 'clone': options.update(reference_audio=str(reference),reference_text=profile['reference_text'])
            if family == 'firered': options.update(language=LANGUAGES.get(language,'English'),seed=seed)
            if family == 'dots':
                # This family counts audio patches, with a hard native cap512.
                options.pop('max_new_tokens')
                options.update(max_audio_patches=512,language=None if language=='auto' else language,seed=seed)
            if family == 'moss-sfx': options.update(duration_seconds=job.get('durationSeconds') or 6)
            result = voice.generate(text,**options)
            yield np.asarray(result.waveform,dtype=np.float32)
        rate=getattr(voice,'sample_rate',getattr(voice,'_sample_rate',getattr(getattr(voice,'_generator',None),'sample_rate',24000)))
        return rate,synthesize
    if family == 'f5':
        import mlx.core as mx
        from f5_tts_mlx.cfm import F5TTS
        from f5_tts_mlx.utils import convert_char_to_pinyin
        from .transcription import read_audio
        voice = F5TTS.from_pretrained(model['repo'],quantization_bits=4)
        audio = mx.array(read_audio(reference,24000))
        rms=float(mx.sqrt(mx.mean(mx.square(audio))).item())
        if 0<rms<.1:audio=audio*(.1/rms)
        def synthesize(text):
            from unittest.mock import patch
            normal=mx.random.normal
            # F5 passes scalar MLX arrays as shape dimensions; current MLX requires ints.
            def shaped_normal(shape=(),*args,**kwargs):
                return normal(tuple(int(n.item()) if isinstance(n,mx.array) else n for n in shape),*args,**kwargs)
            # Use reference pacing rather than the old duration predictor, which can
            # collapse cross-language references to a fraction of a second.
            reference_seconds=audio.shape[0]/24000
            characters_per_second=max(7,min(20,len(profile['reference_text'])/reference_seconds))
            duration=int(audio.shape[0]//256+max(1.,len(text)/characters_per_second)*24000/256)
            with patch.object(mx.random,'normal',shaped_normal):
                wave,_ = voice.sample(audio[None],text=convert_char_to_pinyin([profile['reference_text']+' '+text]),duration=duration,steps=32,method='euler',speed=1.,cfg_strength=2.,sway_sampling_coef=-1.,seed=seed)
            yield np.asarray(wave).reshape(-1)[audio.shape[0]:]
        return 24000,synthesize
    if family=='index':
        index_emotions={'calm':None,'excited':'happy','angry':'angry'}
        if job.get('emotion','calm') not in index_emotions:
            raise ValueError('IndexTTS 2 поддерживает подачу по образцу, радостно или сердито. Выберите подходящую подачу.')
        from mlx_indextts.generate_v2 import IndexTTSv2
        voice=IndexTTSv2(model_dir=str(path),device='cpu')
        def synthesize(text):
            yield voice.generate(text=text,reference_audio=str(reference),seed=seed,verbose=False,emotion=index_emotions[job.get('emotion','calm')])
        return 22050,synthesize
    if family=='moss-design':
        import torch
        from transformers import AutoModel
        from .moss_design import load_processor
        torch.manual_seed(seed)
        codec=str(component(model,model['codecRepo']))
        processor=load_processor(path,codec)
        voice=AutoModel.from_pretrained(str(path),trust_remote_code=True,attn_implementation='eager',torch_dtype=torch.float32).eval()
        def synthesize(text):
            conversation=[[processor.build_user_message(text=text,instruction=instruction)]]
            batch=processor(conversation,mode='generation')
            with torch.inference_mode():
                result=voice.generate(input_ids=batch['input_ids'],attention_mask=batch['attention_mask'],max_new_tokens=2048,audio_temperature=1.5)
            for message in processor.decode(result):
                for audio in message.audio_codes_list:yield audio.detach().cpu().numpy()
        return processor.model_config.sampling_rate,synthesize
    if family in {'silero','xtts','parler'}:
        import torch
        torch.manual_seed(seed)
        torch.set_num_threads(min(8, max(1, __import__('os').cpu_count() or 1)))
        if family == 'silero':
            voice = torch.package.PackageImporter(str(path/'model.pt')).load_pickle('tts_models','model')
            voice.to(torch.device('cpu'))
            def synthesize(text):
                kwargs = {'ssml_text':text} if text.lstrip().startswith('<speak') else {'text':text}
                yield voice.apply_tts(**kwargs,speaker=preset,sample_rate=48000,put_accent=True,put_yo=True).detach().cpu().numpy()
            return 48000,synthesize
        if family == 'xtts':
            from TTS.tts.configs.xtts_config import XttsConfig
            from .xtts_checkpoint import load as load_xtts, text_parts
            config=XttsConfig(); config.load_json(str(path/'config.json'))
            voice=load_xtts(config,path)
            latent,embedding=voice.get_conditioning_latents(audio_path=[str(reference)])
            def synthesize(text):
                selected_language='en' if language=='auto' else language
                # Shared studio chunks can exceed XTTS's per-language limits.
                for part in text_parts(text,selected_language,voice.tokenizer):
                    with torch.inference_mode():
                        result=voice.inference(part,selected_language,latent,embedding,temperature=.8)
                    yield result['wav']
            return 24000,synthesize
        from parler_tts import ParlerTTSForConditionalGeneration
        from transformers import AutoTokenizer
        voice=ParlerTTSForConditionalGeneration.from_pretrained(str(path),local_files_only=True).eval()
        tokenizer=AutoTokenizer.from_pretrained(str(path))
        description=tokenizer(instruction,return_tensors='pt')
        def synthesize(text):
            prompt=tokenizer(text,return_tensors='pt')
            with torch.inference_mode(): audio=voice.generate(input_ids=description.input_ids,attention_mask=description.attention_mask,prompt_input_ids=prompt.input_ids,prompt_attention_mask=prompt.attention_mask)
            yield audio[0].cpu().numpy()
        return voice.config.sampling_rate,synthesize
    prepared_reference=None
    if mode=='clone' and (family=='dia' or model.get('alignmentRepo')):
        from .reference_alignment import bounded_reference
        prepared_reference=(profile['reference_text'],None)
        if model.get('alignmentRepo'):
            prepared_reference=bounded_reference(reference,profile['reference_text'],profile.get('language','auto'),
                                component(model,model['alignmentRepo']),model_name=model['name'],
                                maximum_bytes=400 if family=='dia' else 2048)
    import mlx.core as mx
    from mlx_audio.tts.utils import load_model
    mx.random.seed(seed)
    model_type={'qwen':'qwen3_tts','chatterbox':'chatterbox','chatterbox-turbo':'chatterbox_turbo','voxcpm2':'voxcpm2','omnivoice':'omnivoice','moss':'moss_tts','kokoro':'kokoro','dia':'dia','spark':'spark','higgs':'higgs_audio','orpheus':'llama','cosyvoice':'cosyvoice3'}[family]
    if family=='cosyvoice':
        from mlx_audio.tts.models.cosyvoice3 import Model,ModelConfig
        voice=Model(ModelConfig(model_path=str(path)))
    elif family=='omnivoice':
        from .rowwise import load_omnivoice
        voice=load_omnivoice(path)
    else:
        voice=load_model(str(path),model_type=model_type,model_name_parts=model['repo'].split('/')[-1].split('-'))
    if family == 'spark':
        # The tokenizer is a plain container, so MLX does not recurse into its
        # BatchNorm/Dropout modules when the parent is switched to inference mode.
        voice.eval()
        voice._audio_tokenizer.model.eval()
        voice._audio_tokenizer.feature_extractor.eval()
    if family == 'kokoro':
        from .model_resources import initialize_kokoro
        initialize_kokoro(voice, model, preset)
    rate=voice.sample_rate
    if family=='moss':
        from .moss_codec import load as load_moss_codec
        voice.audio_tokenizer=load_moss_codec(component(model,model['codecRepo'],model.get('codecSubdir','')))
    omnivoice_reference=None
    if family=='omnivoice' and mode=='clone':
        from mlx_audio.tts.models.omnivoice.utils import create_voice_clone_prompt
        # The native generate wrapper omits ref_text here and can trim a long
        # recording while retaining its full transcript. Encode the matching
        # pair once and reuse its tokens for every target chunk.
        omnivoice_reference=create_voice_clone_prompt(str(reference),tokenizer=voice.audio_tokenizer,
                            ref_text=profile['reference_text'],max_duration_s=30.0)
    if family == 'dia':
        from .dia_prompt import cloning_prompt
        from .transcription import read_audio
        reference_text,reference_end=prepared_reference
        audio=read_audio(reference,rate)
        if reference_end is not None:audio=audio[:round(reference_end*rate)]
        reference_audio=mx.array(audio)
        def synthesize_dia(text):
            prefix, continuation = cloning_prompt(reference_text, text)
            encoded=(prefix+' '+continuation).encode('utf-8').replace(b'[S1]',b'\x01').replace(b'[S2]',b'\x02')
            if len(encoded)>voice.config.data.text_length:
                raise ValueError('Текст и образец слишком длинные для Dia. Сократите текст сцены или образец.')
            # Keep the complete dialogue in one native call. The public wrapper
            # splits turns again and can drop an unfinished speaker/end marker.
            # Use the checkpoint's configured length rather than the generic cap.
            audio, _ = voice._generate(continuation, ref_text=prefix, ref_audio=reference_audio,
                                       max_tokens=voice.config.data.audio_length)
            yield np.asarray(audio, dtype=np.float32)
        return rate, synthesize_dia
    qwen_reference=None
    if family=='qwen' and prepared_reference is not None and prepared_reference[1] is not None:
        from .transcription import read_audio
        reference_text,reference_end=prepared_reference
        qwen_reference=(mx.array(read_audio(reference,rate)[:round(reference_end*rate)]),reference_text)
    def synthesize(text):
        options=dict(verbose=False,max_tokens=2048)
        if mode=='clone':options.update(ref_audio=str(reference),ref_text=profile['reference_text'])
        elif mode=='preset':options['voice']=preset
        if family=='qwen':
            options.update(lang_code=LANGUAGES.get(language,language),temperature=.8)
            if qwen_reference is not None:options.update(ref_audio=qwen_reference[0],ref_text=qwen_reference[1])
            if mode!='clone':options['instruct']=instruction
        elif family=='kokoro':
            options.update(lang_code=preset[0])
        elif family=='cosyvoice':
            from .transcription import read_audio
            from .japanese import is_japanese, readings
            if is_japanese(text,language):
                text=readings(text,model,katakana=True)
            options.update(ref_audio=read_audio(reference,24000),stt_model=None)
            prefix, boundary, reference_text=options['ref_text'].partition('<|endofprompt|>')
            if not boundary:reference_text=prefix
            if is_japanese(reference_text,(profile or {}).get('language','auto')):
                reference_text=readings(reference_text,model,katakana=True)
            options['ref_text']=(prefix+boundary if boundary else '')+reference_text
            # CosyVoice3's zero-shot transcript includes an instruction boundary.
            # The pinned MLX wrapper encodes ref_text verbatim, unlike the author's frontend.
            if '<|endofprompt|>' not in options['ref_text']:
                options['ref_text']='You are a helpful assistant.<|endofprompt|>'+options['ref_text']
        elif family=='chatterbox':
            options['lang_code']='en' if language=='auto' else language
            if language=='ja':
                from .japanese import readings
                text=readings(text,model)
            # Author guidance for multilingual cloning: avoid pulling the
            # reference language/accent into a different requested language.
            reference_language=(profile or {}).get('language','auto')
            if language!='auto' and reference_language!='auto' and language!=reference_language:
                options['cfg_weight']=0.0
        elif family=='chatterbox-turbo':
            from .transcription import read_audio
            audio=read_audio(reference,24000)
            if len(audio)<5*24000:
                raise ValueError('Для Chatterbox Turbo нужен образец длительностью не менее 5 секунд.')
            if len(audio)==5*24000:
                # The native loader asserts strictly >5s. One silent sample
                # admits the app's valid 5s boundary without changing its speech.
                options.update(ref_audio=np.pad(audio,(0,1)),sample_rate=24000)
        elif family=='higgs':
            from .transcription import read_audio
            options['ref_audio']=read_audio(reference,24000)
        elif family=='moss':
            options.update(audio_tokenizer_source=str(component(model,model['codecRepo'],model.get('codecSubdir',''))),audio_temperature=1.7)
            if mode=='design':options.update(instruction=instruction)
        elif family=='omnivoice':
            # This checkpoint was trained with ISO language IDs, not English names.
            options.update(lang_code='None' if language=='auto' else language)
            if mode=='clone':
                from mlx_audio.tts.models.omnivoice.duration import RuleDurationEstimator
                # The wrapper otherwise estimates every voice from a fixed
                # one-second English placeholder, ignoring the actual pacing.
                frames=RuleDurationEstimator().estimate_duration(text,profile['reference_text'],omnivoice_reference.shape[0])
                options.update(ref_tokens=omnivoice_reference,ref_audio_max_duration_s=30.0,
                               duration_s=max(10,int(frames*1.15))/(rate/960))
            if mode=='design':
                from .rowwise import voice_instruction
                options['instruct']=voice_instruction(job['voiceDescription'],text)
        elif family=='voxcpm2':
            if mode=='design' or job.get('emotion','calm')!='calm':options['instruct']=instruction
        elif family=='spark':
            if mode=='design':
                from .voice_design import spark_options
                options.update(spark_options(job['voiceDescription']))
                # Match the author's default sampling for controlled voices.
                options['repetition_penalty']=1.0
            else:
                # Native zero-shot cloning supports speaker codes without a
                # semantic continuation prompt. A long supplied transcript can
                # make that continuation end before producing any target audio.
                options['ref_text']=None
        else:options['lang_code']='en' if language=='auto' else language
        from contextlib import nullcontext
        context=nullcontext()
        if family=='spark' and mode=='design':
            from .voice_design import spark_codec_grammar
            context=spark_codec_grammar(voice.tokenizer)
        with context:
            generated=voice.generate(text,**options)
            results=[generated] if hasattr(generated,'audio') else generated
            for result in results:
                if result.sample_rate!=rate:raise ValueError('Модель изменила частоту аудио.')
                yield np.asarray(result.audio,dtype=np.float32)
    return rate,synthesize
