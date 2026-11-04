import { useEffect, useRef, useState } from 'react';
import { MagnifyingGlass, DownloadSimple, Check, ArrowClockwise, X, ArrowUpRight, Waveform, TextAlignLeft } from '@phosphor-icons/react';
import { LocalModelImport } from './LocalModelImport';
import { ModelWorkbench } from './ModelWorkbench';
import type { useStudioBackend } from './useStudioBackend';
import type { Locale } from './types';
import { translator } from './i18n';
import { Select } from './Select';
import { catalogFilters, modelBytes, modelLanguages, modelLanguageOptions, modelMatches } from './model-catalog';
import type { useModelCatalog } from './useModelCatalog';
import type {useWorkbenchDrafts} from './useWorkbenchDrafts';

export function ModelsPanel({ locale, models, backend,workbench,openCleanup }: { locale: Locale; models: ReturnType<typeof useModelCatalog>; backend: ReturnType<typeof useStudioBackend>;workbench:ReturnType<typeof useWorkbenchDrafts>;openCleanup:()=>void }) {
  const t = translator(locale), { catalog, error, busy, refresh, action } = models;
  const toolModel=catalog?.models.find(model=>model.id===workbench.activeId);
  const readFilters = () => catalogFilters(location.search);
  const [filters, setFilters] = useState(readFilters);
  const [announcement, setAnnouncement] = useState<{ kind: 'selected' | 'downloaded'; name: string } | null>(null);
  const previousStatuses = useRef(new Map<string,string>());
  const startedDownloads = useRef(new Set<string>());
  useEffect(() => {
    for (const model of catalog?.models ?? []) {
      const previous = previousStatuses.current.get(model.id);
      if ((model.ready || (model.integration !== 'ready' && model.installed)) && (startedDownloads.current.has(model.id) || ['queued','downloading','verifying','preparing'].includes(previous ?? ''))) {
        setAnnouncement({kind:'downloaded',name:model.name}); startedDownloads.current.delete(model.id);
      }
      if (['failed','cancelled'].includes(model.status)) startedDownloads.current.delete(model.id);
      previousStatuses.current.set(model.id,model.status);
    }
  }, [catalog]);
  const [filtersOpen, setFiltersOpen] = useState(() => matchMedia('(min-width: 681px)').matches);
  const [compact, setCompact] = useState(() => matchMedia('(max-width: 680px)').matches);
  useEffect(() => { const media = matchMedia('(min-width: 681px)'); const sync = () => { setFiltersOpen(media.matches); setCompact(!media.matches); }; media.addEventListener('change', sync); return () => media.removeEventListener('change', sync); }, []);
  const [actionError, setActionError] = useState<{ id: string; message: string } | null>(null);
  useEffect(() => { const pop = () => setFilters(readFilters()); addEventListener('popstate', pop); return () => removeEventListener('popstate', pop); }, []);
  const filter = (patch: Partial<typeof filters>) => {
    const next = { ...filters, ...patch }; setFilters(next);
    const url = new URL(location.href);
    for (const [key, value] of Object.entries({ ...next, q: next.query })) {
      if (key === 'query') continue;
      if (!value || value === 'all') url.searchParams.delete(key); else url.searchParams.set(key, value);
    }
    history.replaceState({}, '', url);
  };
  const resetFilters = () => filter(catalogFilters(''));
  const run = async (id: string, operation: 'download' | 'cancel' | 'select') => {
    const model=catalog?.models.find(model=>model.id===id);
    if(operation==='select' && id==='resemble-enhance'){openCleanup();return;}
    if(operation==='select' && model && ['processing','conversion'].includes(model.task)){workbench.open(model.id);requestAnimationFrame(()=>document.querySelector('.model-workbench')?.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}));return;}
    setActionError(null);
    if (operation === 'download') startedDownloads.current.add(id);
    if (operation === 'cancel') startedDownloads.current.delete(id);
    try { await action(id, operation); if (operation === 'select') setAnnouncement({kind:'selected',name:catalog?.models.find(model => model.id === id)?.name ?? ''}); }
    catch (cause) { startedDownloads.current.delete(id); setActionError({ id, message: cause instanceof Error ? cause.message : t('modelActionFailed') }); }
  };
  const visible = catalog?.models.filter(model => modelMatches(model, filters.query, filters.task, filters.status, filters.language, filters.feature, filters.integration)) ?? [];
  const features = { cloning: 'featureCloning', presets: 'featurePresets', design: 'featureDesign', dialogue: 'featureDialogue', emotion: 'featureEmotion', streaming: 'featureStreaming', ssml: 'featureSsml', 'sound-effects': 'featureEffects', enhancement: 'featureEnhancement', conversion: 'featureConversion' } as const;
  const featureName = (feature: string) => feature in features ? t(features[feature as keyof typeof features]) : t('transcription');
  const statusFilter = <div className="catalog-filter"><span>{t('modelFilter')}</span><Select label={t('modelFilter')} value={filters.status} onChange={status => filter({ status })} options={[{ value:'all',label:t('allModels') },{value:'installed',label:t('installedModels')},{value:'available',label:t('availableModels')},{value:'downloads',label:t('modelDownloads')}]} /></div>;
  return <section className="model-catalog" aria-label={t('models')}>
    {toolModel && <ModelWorkbench key={toolModel.id} model={toolModel} locale={locale} backend={backend} workbench={workbench} close={workbench.close}/>}
    <p className="catalog-announcement" role="status">{announcement ? `${t(announcement.kind === 'selected' ? 'modelSelected' : 'modelInstallComplete')}: ${announcement.name}` : ''}</p>
    <p className="catalog-compatibility-help">{t(compact ? 'catalogCompatibilityShort' : 'catalogCompatibilityHelp')}</p>
    <div className="catalog-toolbar">
      <label className="catalog-search"><span>{t('modelSearch')}</span><div><MagnifyingGlass size={18} aria-hidden="true" /><input type="search" maxLength={200} value={filters.query} placeholder="Qwen, Fish, Chatterbox…" onChange={event => filter({ query: event.target.value })} /></div></label>
      {!compact && statusFilter}
    </div>
    <details className="catalog-advanced-filters take-source" open={filtersOpen} onToggle={event => setFiltersOpen(event.currentTarget.open)}>
      <summary>{t('catalogFilters')}{[filters.status,filters.language,filters.feature,filters.integration].some(value => value !== 'all') && <span>({[filters.status,filters.language,filters.feature,filters.integration].filter(value => value !== 'all').length})</span>}</summary>
      <div className="catalog-extra-filters">
      {compact && statusFilter}
      <div className="catalog-filter"><span>{t('modelLanguages')}</span><Select label={t('modelLanguages')} value={filters.language} onChange={language => filter({language})} search={{label:t('catalogLanguageSearch'),empty:t('catalogLanguageEmpty')}} options={[{value:'all',label:t('allLanguages')},...modelLanguageOptions(catalog?.models ?? [],locale,filters.language)]} /></div>
      <div className="catalog-filter"><span>{t('modelFeatures')}</span><Select label={t('modelFeatures')} value={filters.feature} onChange={feature => filter({feature})} options={[{value:'all',label:t('allFeatures')},...Object.keys(features).map(value=>({value,label:featureName(value)}))]} /></div>
      <div className="catalog-filter"><span>{t('modelIntegration')}</span><Select label={t('modelIntegration')} value={filters.integration} onChange={integration => filter({integration})} options={[{value:'all',label:t('allModels')},{value:'ready',label:t('integratedModels')},{value:'other',label:t('otherRuntimes')}]} /></div>
      </div>
    </details>
    <div className="catalog-categories" role="group" aria-label={t('modelTask')}>
      {(['all','synthesis','transcription','processing','conversion'] as const).map(value => <button type="button" key={value} aria-pressed={filters.task === value} onClick={() => filter({ task:value })}>{t(value === 'all' ? 'allTasks' : value)}</button>)}
      {(filters.query || [filters.task,filters.status,filters.language,filters.feature,filters.integration].some(value => value !== 'all')) && <button type="button" className="catalog-reset" onClick={resetFilters}>{t('resetFilters')}</button>}
      {catalog && <span className="catalog-space" role="status" aria-live="polite" aria-atomic="true">{t('modelResults')}: {visible.length} / {catalog.models.length}</span>}
    </div>
    {error && <div className="catalog-feedback" role="alert"><p>{t('catalogUnavailable')}</p><button type="button" className="quiet" onClick={() => void refresh()}><ArrowClockwise size={17} />{t('retryCatalog')}</button></div>}
    {!catalog && !error && <div className="model-grid" aria-busy="true" aria-label={t('loadingModels')}>{[0,1,2,3].map(i => <div className="model-skeleton" key={i}><span /><span /><span /></div>)}</div>}
    {catalog && visible.length === 0 && <div className="catalog-empty"><h2>{t('noModelsFound')}</h2><p>{t('changeModelFilters')}</p><button type="button" className="quiet" onClick={resetFilters}>{t('resetFilters')}</button></div>}
    {catalog && visible.length > 0 && <div className="model-grid">{visible.map(model => {
      const downloading = ['queued','downloading','verifying','preparing'].includes(model.status), pending = busy === model.id;
      const size = model.transfer?.totalBytes || model.sizeBytes || 0;
      const transferred = size ? Math.min(size, model.transfer?.downloadedBytes ?? model.downloadedBytes) : model.transfer?.downloadedBytes ?? model.downloadedBytes;
      const percent = size ? Math.floor(transferred / size * 100) : 0;
      const notEnoughSpace = model.downloadable && !model.ready && size - model.downloadedBytes > catalog.freeBytes - (model.integration === 'ready' && !model.runtimeReady ? 600_000_000 : 100_000_000) - (model.resourceReady ? 0 : model.resourceBytes ?? 0);
      const problem = actionError?.id === model.id ? actionError.message : model.status === 'failed' ? model.transfer?.error : null;
      const integrated = model.integration === 'ready';
      return <article className={`model-card${model.active ? ' model-active' : ''}`} key={model.id} aria-labelledby={`model-${model.id}`}>
        <div className="model-card-top"><span className="model-task">{model.task === 'synthesis' ? <Waveform size={18} /> : <TextAlignLeft size={18} />}{t(model.task)}</span><span className="model-state">{model.active ? <><Check size={14} />{t('modelInUse')}</> : t(model.ready ? 'modelReady' : model.installed && !downloading ? 'modelFilesInstalled' : downloading ? 'modelDownloading' : model.status === 'cancelled' ? 'modelPaused' : model.status === 'failed' ? 'modelFailed' : 'modelNotInstalled')}</span></div>
        <h2 id={`model-${model.id}`}>{model.name}</h2><p className="model-description">{model.description[locale]}</p>
        <ul className="model-capabilities" aria-label={t('modelFeatures')}>{model.features.map(feature => <li key={feature}>{featureName(feature)}</li>)}</ul>
        <dl className="model-facts"><div><dt>{t('modelSize')}</dt><dd>{modelBytes(model.sizeBytes,locale)}</dd></div><div><dt>{t('modelFormat')}</dt><dd>{model.format}</dd></div><div><dt>{t('modelLanguages')}</dt><dd>{modelLanguages(model.languages,locale)}</dd></div></dl>
        <div className={`model-runtime-note${integrated ? ' model-runtime-ready' : ''}`}>{integrated ? <Check size={14} /> : null}<span>{t(integrated ? 'integratedModels' : 'needsRuntime')}</span></div>
        <div className="model-action-area">
          {downloading && <div className="model-download-progress"><div><span>{t(model.status === 'queued' ? 'modelQueued' : model.status === 'preparing' ? 'modelPreparing' : model.status === 'verifying' ? 'modelVerifying' : 'modelDownloading')}</span><span>{modelBytes(transferred,locale)} / {modelBytes(size || null,locale)}</span></div><progress max={size || undefined} value={size ? transferred : undefined} aria-label={`${t('modelDownloading')} ${model.name}`} aria-valuetext={`${percent}%`} /></div>}
          {problem && <p className="field-error" role="alert">{problem}</p>}
          {notEnoughSpace && <p className="field-error">{t('modelDiskSpace')}</p>}
          <div className="model-card-actions">
            {downloading ? <button type="button" className="quiet" aria-disabled={pending} aria-busy={pending} onClick={() => { if (!pending) void run(model.id,'cancel'); }}><X size={17} />{t('cancelDownload')}</button>
            : model.active ? <button type="button" className="quiet model-current" aria-pressed="true" aria-disabled="true"><Check size={17} />{t('selected')}</button>
            : model.ready && integrated ? <button type="button" className="quiet" aria-pressed="false" aria-busy={pending} aria-disabled={pending || !!error} onClick={() => { if (!pending && !error) void run(model.id,'select'); }}>{pending ? t('modelSelecting') : t(['processing','conversion'].includes(model.task)?'openModelTool':'useModel')}</button>
            : model.installed && !integrated ? <button type="button" className="quiet model-current" aria-disabled="true"><Check size={16} />{t('modelFilesInstalled')}</button>
            : model.downloadable ? <button type="button" className="quiet model-install" disabled={notEnoughSpace || !!error} aria-disabled={pending || notEnoughSpace || !!error} aria-busy={pending} onClick={() => { if (!pending && !notEnoughSpace && !error) void run(model.id,'download'); }}><DownloadSimple size={18} />{t(pending ? 'modelQueued' : model.status === 'cancelled' ? 'resumeDownload' : model.status === 'failed' ? 'retryDownload' : integrated ? model.installed ? 'prepareModel' : 'downloadModel' : 'downloadWeights')}</button>
            : <span className="model-external">{t(model.gated ? 'modelAccessRequired' : 'modelAuthorInstall')}</span>}
            <a href={model.sourceUrl} target="_blank" rel="noreferrer" className="model-source" aria-label={`${t('modelSource')} — ${model.name}`}>{t('modelSource')}<ArrowUpRight size={14} /></a>
          </div>
        </div>
        {model.gated && !model.ready && !downloading && <LocalModelImport id={model.id} locale={locale} refresh={refresh}/>}
        <details className="take-source model-license"><summary>{t('modelDetails')}</summary><p>{model.license}</p><p>{t('modelRuntime')}: {model.runtime}</p>{!integrated && <p>{t('runtimeNotIntegrated')}</p>}{model.notes && <p>{model.notes[locale]}</p>}<code>{model.repo}</code></details>
      </article>;
    })}</div>}
    <div className="catalog-footer"><p className="catalog-footnote">{t('expandedCatalogNote')}</p>{catalog && <span>{t('diskFree')}: {modelBytes(catalog.freeBytes,locale)}</span>}</div>
  </section>;
}
