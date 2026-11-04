import { useRef, useState } from 'react';
import { UploadSimple, FileAudio, X } from '@phosphor-icons/react';
import { translator } from './i18n';
import type { Locale } from './types';
import type { TranslationKey } from './i18n';
import { AUDIO_ACCEPT, recordingError } from './voice-form';

export function FileUpload({ id, file, locale, disabled, error, onChange, onError, onBlur }: {
  id: string; file: File | null; locale: Locale; disabled: boolean; error?: TranslationKey;
  onChange: (file: File | null) => void; onError: (error: TranslationKey) => void; onBlur: () => void;
}) {
  const t = translator(locale), input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const depth = useRef(0);
  const choose = (files: FileList | null) => {
    if (!files?.length) return;
    if (files.length !== 1) { onChange(null); onError('oneRecordingOnly'); return; }
    const next = files[0], invalid = recordingError(next);
    if (invalid) { onChange(null); onError(invalid); if (input.current) input.current.value = ''; return; }
    onChange(next);
  };
  const size = file ? new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(file.size / (1024 * 1024)) : '';
  return <div className="voice-upload">
    <label htmlFor={id}>{t('voiceFile')} <span className="field-required">{t('required')}</span></label>
    <div className={`file-upload ${dragging ? 'is-dragging' : ''} ${error ? 'has-error' : ''}`} onDragEnter={event => { if (disabled || !event.dataTransfer.types.includes('Files')) return; event.preventDefault(); depth.current++; setDragging(true); }} onDragLeave={event => { if (disabled) return; event.preventDefault(); depth.current = Math.max(0, depth.current - 1); if (!depth.current) setDragging(false); }} onDragOver={event => { if (!disabled && event.dataTransfer.types.includes('Files')) { event.preventDefault(); event.dataTransfer.dropEffect = 'copy'; } }} onDrop={event => { event.preventDefault(); depth.current = 0; setDragging(false); if (!disabled) choose(event.dataTransfer.files); }}>
      <div className="file-upload-info" aria-live="polite"><FileAudio size={24} /><span><strong>{dragging ? t('dropRecording') : file?.name ?? t('noFile')}</strong><small>{file ? `${size} ${t('megabytes')}` : t('dropRecordingHelp')}</small></span></div>
      <span className="file-upload-picker"><span className="quiet"><UploadSimple size={18} />{t(file ? 'replaceRecording' : 'chooseFile')}</span><input ref={input} id={id} type="file" aria-label={t('voiceFile')} accept={AUDIO_ACCEPT} disabled={disabled} aria-required="true" aria-invalid={!!error} aria-describedby={`${id}-help${error ? ` ${id}-error` : ''}`} onChange={event => choose(event.target.files)} onBlur={onBlur} /></span>
      {file && <button type="button" className="quiet icon-button" disabled={disabled} aria-label={t('clearRecording')} onClick={() => { if (input.current) input.current.value = ''; onChange(null); input.current?.focus(); }}><X size={18} /></button>}
    </div>
    <p className="setting-help" id={`${id}-help`}>{t('fileHelp')}</p>
    {error && <p className="field-error" id={`${id}-error`}>{t(error)}</p>}
  </div>;
}
