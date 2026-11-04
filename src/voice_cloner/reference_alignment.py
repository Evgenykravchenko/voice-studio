"""Bound a cloning reference by aligning its supplied original words locally."""
import gc
import math

from .dia_prompt import SPEAKER


def alignment_text(reference):
    chars=[];positions=[];offset=0
    for marker in SPEAKER.finditer(reference):
        chars.extend(reference[offset:marker.start()]);positions.extend(range(offset,marker.start()));offset=marker.end()
    chars.extend(reference[offset:]);positions.extend(range(offset,len(reference)))
    raw=''.join(chars);left=len(raw)-len(raw.lstrip());right=len(raw.rstrip())
    return raw[left:right],positions[left:right]


def select_prefix(reference, words, *, minimum=5.0, maximum=10.0, maximum_bytes=400, model_name='Dia'):
    text,positions=alignment_text(reference)
    if ''.join(word['word'] for word in words)!=text:
        raise ValueError(f'Не удалось сопоставить слова образца. Выберите более короткий фрагмент для {model_name}.')
    candidates=[];offset=0
    for word in words:
        offset+=len(word['word']);end=float(word['end']);start=float(word['start'])
        if not math.isfinite(start) or not math.isfinite(end) or start<0 or end<start:
            raise ValueError(f'Не удалось определить границы слов образца для {model_name}.')
        if minimum<=end<=maximum and word['word'].strip() and offset:
            prefix=reference[:positions[offset-1]+1].strip()
            if len(prefix.encode('utf-8'))<=maximum_bytes:
                sentence=prefix.rstrip(' \"\'”’)]}').endswith(('.', '!', '?', '。', '！', '？'))
                candidates.append((sentence,prefix,end))
    if not candidates:
        raise ValueError(f'Не удалось подобрать короткий образец для {model_name}. Выберите фрагмент от 5 до 10 секунд.')
    sentences=[candidate for candidate in candidates if candidate[0]]
    _,prefix,end=(sentences or candidates)[-1]
    return prefix,end


def bounded_reference(reference, text, language, aligner_path, *, model_name='Dia', maximum_bytes=400):
    import soundfile as sf
    duration=sf.info(str(reference)).duration
    if duration<=10:return text,None
    if duration>30.1:
        raise ValueError(f'Для {model_name} выберите образец длительностью не более 30 секунд.')
    if aligner_path is None:
        raise ValueError(f'Повторите установку {model_name} для подготовки длинного образца.')
    import mlx.core as mx
    from mlx_whisper.load_models import load_model
    from mlx_whisper.tokenizer import get_tokenizer,LANGUAGES
    from mlx_whisper.audio import log_mel_spectrogram,pad_or_trim,N_FRAMES,N_SAMPLES,HOP_LENGTH
    from mlx_whisper.timing import find_alignment
    from .transcription import read_audio
    model=None
    try:
        audio=read_audio(reference,16000)
        model=load_model(str(aligner_path),dtype=mx.float16)
        mel=pad_or_trim(log_mel_spectrogram(audio,n_mels=model.dims.n_mels,padding=N_SAMPLES),N_FRAMES,axis=-2).astype(mx.float16)
        if language not in list(LANGUAGES)[:model.num_languages]:
            _,probabilities=model.detect_language(mel)
            language=max(probabilities,key=probabilities.get)
        tokenizer=get_tokenizer(model.is_multilingual,num_languages=model.num_languages,language=language,task='transcribe')
        supplied,_=alignment_text(text);tokens=tokenizer.encode(supplied)
        if not tokens or len(tokens)+len(tokenizer.sot_sequence)+2>=model.dims.n_text_ctx:
            raise ValueError(f'Для {model_name} выберите более короткий образец с точной расшифровкой.')
        timings=find_alignment(model,tokenizer,tokens,mel,round(len(audio)/HOP_LENGTH))
        return select_prefix(text,[{'word':w.word,'start':float(w.start),'end':float(w.end)} for w in timings],
                             model_name=model_name,maximum_bytes=maximum_bytes)
    finally:
        del model
        gc.collect()
        mx.clear_cache()
