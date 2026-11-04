"""Offline Japanese readings for model frontends that cannot consume kanji directly."""
import re

KANJI = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0002fa1f]')
KANA = re.compile(r'[\u3041-\u3096\u30a1-\u30fa]')


def is_japanese(text, language='auto'):
    # Kanji alone can also be Chinese: do not infer Japanese from those glyphs.
    return language == 'ja' or language == 'auto' and bool(KANA.search(text))


def readings(text, model, *, katakana=False):
    if not KANJI.search(text) and (not katakana or not KANA.search(text)):
        return text
    import fugashi
    from .model_resources import dictionary
    path = dictionary(model)
    if path is None:
        raise ValueError('Для японского текста нужен словарь. Повторите установку модели в разделе «Модели».')
    def quote(value):
        return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"') + '"'
    tagger = fugashi.Tagger('-r ' + quote(path / 'mecabrc') + ' -d ' + quote(path))
    words = list(tagger(text))
    trailing = text[len(text.rstrip()):]
    if ''.join(word.white_space + word.surface for word in words) + trailing != text:
        raise ValueError('Не удалось подготовить японский текст без потери символов.')
    result = []
    for word in words:
        surface = word.surface
        if KANJI.search(surface) or katakana and KANA.search(surface):
            reading = getattr(word.feature, 'pron' if katakana else 'kana', None)
            if not reading or reading == '*':
                if KANJI.search(surface):
                    raise ValueError('Не найдено японское чтение: ' + surface + '. Укажите это слово каной.')
                reading = surface
            if katakana:
                surface = ''.join(chr(ord(c) + 0x60) if '\u3041' <= c <= '\u3096' else c for c in reading)
            else:
                surface = ''.join(chr(ord(c) - 0x60) if '\u30a1' <= c <= '\u30f6' else c for c in reading)
        result.append(word.white_space + surface)
    return ''.join(result) + trailing
