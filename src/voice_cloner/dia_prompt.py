"""Speaker-labelled cloning context for the pinned Dia model.

Author guidelines: https://github.com/nari-labs/dia#generation-guidelines
The reference transcript belongs to the same dialogue as the generated continuation.
"""
import re

SPEAKER = re.compile(r'\[S([12])\]', re.IGNORECASE)


def cloning_prompt(reference: str, text: str) -> tuple[str, str]:
    reference = SPEAKER.sub(lambda m: '[S' + m[1] + ']', reference.strip())
    text = SPEAKER.sub(lambda m: '[S' + m[1] + ']', text.strip())
    if not reference or not text:
        raise ValueError('Для Dia нужны расшифровка образца и произносимый текст.')
    if not reference.startswith('[S1]'):
        reference = '[S1] ' + reference
    current = SPEAKER.findall(reference)[-1]
    first = SPEAKER.match(text)
    # An ordinary single-speaker script continues the cloned speaker's turn.
    # Repeating [S1] across the reference/script boundary violates native guidance.
    if first and first[1] == current:
        text = text[first.end():].lstrip()
    turns = SPEAKER.findall(text)
    last = turns[-1] if turns else current
    if not re.search(r'\[S[12]\]\s*$', text):
        text += ' [S' + ('2' if last == '1' else '1') + ']'
    return reference, text
