# Измерения моделей

Контрольный короткий прогон 31.10.2026 на Apple Silicon с 36 ГиБ общей памяти. Все перечисленные задачи завершились в двух окружениях: рабочем и независимо установленном, затем перенесённом. Веса для второго прогона использовались из проверенного локального кэша.

XTTS отдельно повторно измерена 01.11 после исправления разбиения и добавления
языковых зависимостей. SHA-256 её выходного WAV совпал с соответствующим
проверенным двумя ASR коротким результатом в каждом окружении.

Silero отдельно измерена 02.11 после восстановления доступности официального
источника. Синтез в обоих окружениях выполнен с запретом сети; короткие WAV
совпали по SHA-256, а их слова подтвердили Whisper Large V3 и Qwen-ASR.

RSS обозначает измеренный максимум резидентной памяти процесса через macOS `/usr/bin/time -l`, включая учёт ожидаемых дочерних процессов. Это не сумма всех процессов и не минимальное требование к RAM. Расход macOS, Java, браузера и полная память GPU здесь не измерены. На 8 ГБ эти модели отдельно не проверялись.

| Модель | Рабочее окружение, RSS ГиБ | Перенесённое, RSS ГиБ | Задача |
| --- | ---: | ---: | --- |
| Fish S2 Pro | 6.12 | 9.56 | synthesis |
| Qwen3-TTS 1.7B Base | 2.69 | 2.68 | synthesis |
| Qwen3-TTS 0.6B Base | 2.19 | 2.19 | synthesis |
| Qwen3-TTS 0.6B Base BF16 | 2.81 | 2.81 | synthesis |
| Qwen3-TTS CustomVoice | 2.61 | 2.61 | synthesis |
| Qwen3-TTS VoiceDesign | 2.61 | 2.61 | synthesis |
| Chatterbox Multilingual V3 | 3.50 | 3.50 | synthesis |
| Chatterbox Turbo | 1.34 | 1.34 | synthesis |
| CosyVoice 3 | 2.92 | 2.92 | synthesis |
| VoxCPM2 | 2.63 | 2.63 | synthesis |
| OmniVoice | 4.55 | 4.55 | synthesis |
| MOSS-TTS | 10.76 | 11.76 | synthesis |
| MOSS VoiceGenerator | 12.37 | 12.37 | synthesis |
| FireRedTTS3 Base | 5.41 | 5.41 | synthesis |
| XTTS v2 | 4.09 | 4.10 | synthesis |
| Kokoro 82M | 0.88 | 0.88 | synthesis |
| Silero TTS v5.6 RU | 1.00 | 1.01 | synthesis |
| Piper Dmitri | 0.21 | 0.21 | synthesis |
| Piper Irina | 0.24 | 0.24 | synthesis |
| Piper Denis | 0.21 | 0.21 | synthesis |
| Piper Ruslan | 0.21 | 0.21 | synthesis |
| F5-TTS v1 Base | 0.71 | 0.72 | synthesis |
| IndexTTS 2 | 7.27 | 7.40 | synthesis |
| VibeVoice 1.5B | 5.21 | 5.21 | synthesis |
| VibeVoice Large | 9.54 | 9.54 | synthesis |
| LongCat AudioDiT 3.5B | 5.08 | 5.08 | synthesis |
| dots.tts SOAR | 3.30 | 3.30 | synthesis |
| dots.tts MeanFlow | 3.30 | 3.30 | synthesis |
| Parler-TTS Mini | 5.47 | 5.47 | synthesis |
| Dia 1.6B | 3.79 | 3.79 | synthesis |
| Spark-TTS 0.5B | 2.44 | 2.44 | synthesis |
| Higgs Audio V2 | 7.06 | 7.06 | synthesis |
| Orpheus 3B | 2.47 | 2.47 | synthesis |
| OpenVoice V2 | 1.64 | 1.64 | conversion |
| MOSS SoundEffect | 5.55 | 5.56 | processing |
| Resemble Enhance | 6.19 | 6.15 | processing |
| Whisper Base | 0.41 | 0.41 | transcription |
| Whisper Small | 0.55 | 0.55 | transcription |
| Whisper Large V3 Turbo | 0.74 | 0.73 | transcription |
| Whisper Medium | 0.92 | 0.91 | transcription |
| Whisper Large V3 | 1.42 | 1.42 | transcription |
| GigaAM v3 | 1.68 | 1.68 | transcription |
| Qwen3-ASR 1.7B | 1.97 | 1.97 | transcription |
| Parakeet TDT 0.6B v3 | 2.75 | 2.75 | transcription |
| Faster Whisper Large V3 | 3.39 | 3.39 | transcription |

OpenAudio не измерялась и исключена из каталога по решению пользователя. Размер файлов модели в каталоге не равен памяти после загрузки.

Это доказательство выполнения конкретных задач и наблюдаемой памяти на одном компьютере. Оно не гарантирует сходство любого голоса, правильность всех ударений, все языки и любую длину текста. Сырые журналы этой локальной проверки находятся в игнорируемой папке `.runtime/release-audit/` и не входят в публичную поставку.
