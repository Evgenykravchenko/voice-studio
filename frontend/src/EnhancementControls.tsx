import {useId} from 'react';
import type {Locale} from './types';
import type {EnhancementSettings} from './enhancement-settings';
import {DEFAULT_ENHANCEMENT,sameEnhancement} from './enhancement-settings';
export function EnhancementControls({value,onChange,disabled,locale,ready,legacy,onUpdate,onRevert}:{value:EnhancementSettings;onChange:(value:EnhancementSettings)=>void;disabled:boolean;locale:Locale;ready:boolean;legacy:boolean;onUpdate:()=>void;onRevert?:()=>void}){
 const ru=locale==='ru',L=(a:string,b:string)=>ru?a:b,id=useId();
 const range=(key:'noiseReduction'|'strength'|'clarity'|'warmth'|'deEss',title:string,help:string,min=0)=><label className="enhancement-field" htmlFor={id+key}><span>{title}</span><output htmlFor={id+key}>{value[key]??100}{key==='warmth'?'':'%'}</output><input id={id+key} aria-label={title} aria-describedby={id+key+'-help'} type="range" className="studio-range" disabled={disabled} min={min} max={100} step={1} value={value[key]??100} onChange={e=>onChange({...value,[key]:Number(e.target.value)})}/><small id={id+key+'-help'}>{help}</small></label>;
 return <div className="enhancement-controls">
  {range('noiseReduction',L('Удаление шума','Noise removal'),L('100% — полностью используем очищенный голос. Уменьшайте, если хотите оставить часть окружения.','100% uses the cleaned voice. Reduce it to keep some ambience.'))}
  {range('strength',L('Улучшение звучания','Voice restoration'),L('Меньше — естественнее тембр; больше — сильнее восстановление. Шум не возвращается при уменьшении.','Lower values keep a more natural timbre; higher values restore more. Lowering this does not bring noise back.'))}
  <details className="take-source enhancement-details"><summary>{L('Настроить звучание','Adjust the sound')}</summary><div className="enhancement-advanced">
   {range('clarity',L('Чёткость','Clarity'),L('Подчёркивает согласные и разборчивость речи.','Emphasizes consonants and speech intelligibility.'))}
   {range('warmth',L('Теплота','Warmth'),L('Минус — меньше баса; плюс — более тёплый голос.','Lower values reduce bass; higher values add warmth.'),-100)}
   {range('deEss',L('Смягчение свистящих','Sibilance reduction'),L('Приглушает резкие «с», «ш» и свистящие звуки.','Softens harsh S and SH sounds.'))}
   <label className="enhancement-toggle"><input type="checkbox" disabled={disabled} checked={value.leveling} onChange={e=>onChange({...value,leveling:e.target.checked})}/><span>{L('Выровнять громкость','Even out the loudness')}<small>{L('Смягчает скачки между тихими и громкими фразами и подбирает общий уровень.','Reduces differences between quiet and loud phrases and adjusts the overall level.')}</small></span></label>
   <label className="enhancement-toggle"><input type="checkbox" disabled={disabled} checked={value.protectPeaks} onChange={e=>onChange({...value,protectPeaks:e.target.checked})}/><span>{L('Защита от перегрузки','Peak protection')}<small>{L('Ограничивает громкие пики, чтобы звук не хрипел.','Limits loud peaks to avoid clipping.')}</small></span></label>
   <button type="button" className="text-link" disabled={disabled || sameEnhancement(value,DEFAULT_ENHANCEMENT)} onClick={()=>onChange({...DEFAULT_ENHANCEMENT})}>{L('Вернуть автоматические настройки','Restore automatic settings')}</button>
  </div></details>
  {ready && <div className="enhancement-update"><p className="setting-help" role="status">{L(legacy?'Создадим новую версию с отдельным удалением шума. Предыдущая запись сохранена.':'Настройки изменены. Пока звучит предыдущая версия.',legacy?'Create a new version with separate noise removal. Your previous recording is preserved.':'Settings changed. Playback still uses the previous version.')}</p><button type="button" className="primary" disabled={disabled} onClick={onUpdate}>{L(legacy?'Улучшить автоматически':'Обновить результат',legacy?'Enhance automatically':'Update result')}</button>{!legacy && onRevert && <button type="button" className="text-link" disabled={disabled} onClick={onRevert}>{L('Отменить изменения','Discard changes')}</button>}</div>}
 </div>;
}
