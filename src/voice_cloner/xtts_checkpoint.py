"""Load the pinned legacy checkpoint without Coqui's on-disk migration."""


def text_parts(text,language,tokenizer):
    from TTS.tts.layers.xtts.tokenizer import split_sentence
    language=language.split('-')[0]
    # Coqui's splitter inserts a space when joining sentences but does not
    # count that space in its limit check. Reserve it, notably for CJK text.
    return split_sentence(text,language,tokenizer.char_limits[language]-1)


def checkpoint_state(path):
    import torch
    from TTS.tts.models.xtts import _legacy_safe_globals
    # coqui-tts0.28 normally reserializes the original XttsConfig into model.pth.
    # This is a verified, immutable Hub artifact: only consume its model state.
    with _legacy_safe_globals():
        return torch.load(path,map_location=torch.device('cpu'),weights_only=True)['model']


def load(config,directory):
    from TTS.tts.models.xtts import Xtts
    class ReadOnlyXtts(Xtts):
        def _load_checkpoint(self,path):
            return checkpoint_state(path)
    voice=ReadOnlyXtts(config)
    voice.load_checkpoint(config,checkpoint_dir=str(directory),use_deepspeed=False)
    voice.eval()
    return voice
