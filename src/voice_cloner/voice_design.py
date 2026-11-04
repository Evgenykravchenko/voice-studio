"""Map the studio's controlled Spark voice description to native model tokens."""
import re
from contextlib import contextmanager

SPARK_LEVELS={'very_low':0.0,'low':0.5,'moderate':1.0,'high':1.5,'very_high':2.0}


def spark_options(description):
    match=re.fullmatch(r'(male|female), (very_low|low|moderate|high|very_high) pitch, (very_low|low|moderate|high|very_high) speed',str(description))
    if not match:
        raise ValueError('Выберите тип, высоту и темп голоса в настройках Spark-TTS.')
    gender,pitch,speed=match.groups()
    return {'gender':gender,'pitch':SPARK_LEVELS[pitch],'speed':SPARK_LEVELS[speed]}


def spark_global_phase(history,start,end,count=32):
    """The pinned codec requires exactly32 generated speaker-code tokens."""
    try:offset=len(history)-1-history[::-1].index(start)
    except ValueError:return None
    tail=history[offset+1:]
    if end in tail:return None
    return 'codes' if len(tail)<count else 'end'


@contextmanager
def spark_codec_grammar(tokenizer):
    """Constrain the fixed speaker-code segment; never invent or pad codec IDs.

    Quantized Spark can emit ordinary text among its32 global codes. Sampling
    remains model-driven, restricted to the token type accepted by its codec.
    The patch is scoped to one serialized inference child and restored on errors.
    """
    import mlx.core as mx
    from unittest.mock import patch
    from mlx_audio.tts.models.spark import spark
    vocab=tokenizer.get_vocab()
    start=vocab['<|start_global_token|>'];end=vocab['<|end_global_token|>']
    codes=sorted(value for token,value in vocab.items() if re.fullmatch(r'<\|bicodec_global_\d+\|>',token))
    if len(codes)!=4096 or codes!=list(range(codes[0],codes[-1]+1)):
        raise ValueError('Неподдерживаемый словарь кодека Spark-TTS. Обновите модель.')
    def grammar(tokens,logits):
        phase=spark_global_phase(tokens.tolist(),start,end)
        if phase is None:return logits
        indices=mx.arange(logits.shape[-1])
        allowed=(indices>=codes[0])&(indices<=codes[-1]) if phase=='codes' else indices==end
        return mx.where(allowed,logits,-float('inf'))
    original=spark.make_logits_processors
    def processors(*args,**kwargs):return [*original(*args,**kwargs),grammar]
    with patch.object(spark,'make_logits_processors',processors):yield
