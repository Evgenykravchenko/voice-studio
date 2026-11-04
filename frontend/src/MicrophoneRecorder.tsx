import {useEffect,useRef,useState} from 'react';
import {Microphone,Stop,Pause,Play,X} from '@phosphor-icons/react';
import type {Locale} from './types';
import {audioTime} from './audio-utils';
import {leveledMicrophoneWave,microphoneLevel} from './microphone-audio';

type Phase='idle'|'requesting'|'recording'|'paused'|'saving';
type Session={recorder:MediaRecorder;stream:MediaStream;chunks:Blob[];discard:boolean;timer:number;context?:AudioContext;analyser?:AnalyserNode;values?:Float32Array<ArrayBuffer>;elapsed:number;started:number};
export function MicrophoneRecorder({locale,file,disabled,onRecorded,onBusy,onStart}:{locale:Locale;file:File|null;disabled:boolean;onRecorded:(file:File)=>void;onBusy:(busy:boolean)=>void;onStart:()=>void}){
  const ru=locale==='ru',L=(a:string,b:string)=>ru?a:b;
  const [phase,setPhase]=useState<Phase>('idle'),[seconds,setSeconds]=useState(0),[level,setLevel]=useState(0),[inputQuality,setInputQuality]=useState<'quiet'|'normal'|'hot'>('quiet'),[error,setError]=useState('');
  const mounted=useRef(true),generation=useRef(0),session=useRef<Session|null>(null),pendingContext=useRef<AudioContext|null>(null),callbacks=useRef({onRecorded,onBusy,onStart});callbacks.current={onRecorded,onBusy,onStart};
  const change=(phase:Phase)=>{if(mounted.current){setPhase(phase);callbacks.current.onBusy(phase!=='idle');}};
  const release=(s:Session)=>{clearInterval(s.timer);s.stream.getTracks().forEach(track=>track.stop());if(s.context)void s.context.close().catch(()=>{});};
  const stop=(discard=false)=>{const s=session.current;if(!s){generation.current++;if(pendingContext.current){void pendingContext.current.close().catch(()=>{});pendingContext.current=null;}change('idle');return;}s.discard=discard;release(s);if(s.recorder.state!=='inactive')s.recorder.stop();};
  useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;generation.current++;stop();};},[]);
  const start=async()=>{
    if(disabled || phase!=='idle')return;
    if(!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder==='undefined'){setError(L('В этом браузере запись недоступна. Загрузите аудиофайл.','Recording is unavailable in this browser. Upload an audio file.'));return;}
    const version=++generation.current;setError('');setSeconds(0);setLevel(0);change('requesting');callbacks.current.onStart();let stream:MediaStream|undefined,context:AudioContext|undefined;
    try{
      // Unlock the meter during the explicit click, before the permission prompt can consume activation.
      try{context=new AudioContext();pendingContext.current=context;void context.resume().catch(()=>{});}catch{/* Capture still works without a meter. */}
      stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:false,noiseSuppression:false,autoGainControl:false}});
      if(!mounted.current || version!==generation.current){stream.getTracks().forEach(t=>t.stop());if(context)void context.close().catch(()=>{});if(pendingContext.current===context)pendingContext.current=null;return;}
      const mime=['audio/webm;codecs=opus','audio/mp4','audio/ogg;codecs=opus'].find(type=>MediaRecorder.isTypeSupported(type));
      const recorder=new MediaRecorder(stream,mime?{mimeType:mime}:undefined),s:Session={recorder,stream,chunks:[],discard:false,timer:0,elapsed:0,started:performance.now()};session.current=s;
      try{s.context=context??new AudioContext();if(pendingContext.current===context)pendingContext.current=null;s.analyser=s.context.createAnalyser();s.analyser.fftSize=1024;s.values=new Float32Array(s.analyser.fftSize);s.context.createMediaStreamSource(stream).connect(s.analyser);void s.context.resume().catch(()=>{});}catch{/* Recording remains available without a level meter. */}
      recorder.ondataavailable=event=>{if(event.data.size)s.chunks.push(event.data);};
      recorder.onerror=()=>{if(mounted.current)setError(L('Запись прервалась. Проверьте микрофон и попробуйте ещё раз.','Recording was interrupted. Check the microphone and try again.'));stop(true);};
      recorder.onstop=async()=>{
        release(s);if(session.current===s)session.current=null;
        if(s.discard){change('idle');return;}change('saving');
        try{
          const data=await new Blob(s.chunks,{type:recorder.mimeType}).arrayBuffer(),decoder=new OfflineAudioContext(1,1,44100),buffer=await decoder.decodeAudioData(data);
          if(buffer.duration<.1)throw new Error(L('Запись слишком короткая. Запишите хотя бы секунду речи.','Recording is too short. Record at least a second of speech.'));
          const stamp=new Date().toISOString().replace(/[:.]/g,'-');callbacks.current.onRecorded(new File([leveledMicrophoneWave(buffer)],`recording-${stamp}.wav`,{type:'audio/wav'}));
        }catch(cause){if(mounted.current)setError(cause instanceof Error && cause.message.includes(ru?'Запись слишком':'Recording is too')?cause.message:L('Не удалось сохранить запись. Попробуйте ещё раз или загрузите файл.','Could not save the recording. Try again or upload a file.'));}
        finally{change('idle');}
      };
      recorder.start(1000);change('recording');
      s.timer=window.setInterval(()=>{
        if(!mounted.current)return;
        const elapsed=s.elapsed+(recorder.state==='recording'?performance.now()-s.started:0);setSeconds(Math.min(300,elapsed/1000));
        if(recorder.state==='recording' && s.analyser && s.values){s.analyser.getFloatTimeDomainData(s.values);let sum=0,peak=0;for(const value of s.values){sum+=value*value;peak=Math.max(peak,Math.abs(value));}const rms=Math.sqrt(sum/s.values.length);setLevel(microphoneLevel(rms));setInputQuality(peak>.97?'hot':rms<.01?'quiet':'normal');}else setLevel(0);
        if(elapsed>=300_000)stop();
      },100);
      stream.getAudioTracks().forEach(track=>track.onended=()=>{if(recorder.state!=='inactive')stop();});
    }catch(cause){stream?.getTracks().forEach(track=>track.stop());if(context)void context.close().catch(()=>{});if(pendingContext.current===context)pendingContext.current=null;if(version!==generation.current || !mounted.current)return;const name=cause instanceof DOMException?cause.name:'';setError(name==='NotAllowedError'?L('Разрешите доступ к микрофону в настройках браузера и попробуйте снова.','Allow microphone access in browser settings and try again.'):name==='NotFoundError'?L('Микрофон не найден. Подключите его или загрузите файл.','No microphone found. Connect one or upload a file.'):L('Не удалось включить микрофон. Проверьте, что он подключён и доступен.','Could not start the microphone. Check that it is connected and available.'));if(session.current){release(session.current);session.current=null;}change('idle');}
  };
  const pause=()=>{const s=session.current;if(!s)return;if(s.recorder.state==='recording'){s.elapsed+=performance.now()-s.started;s.recorder.pause();setLevel(0);change('paused');}else if(s.recorder.state==='paused'){s.started=performance.now();s.recorder.resume();change('recording');}};
  const active=phase==='recording'||phase==='paused';
  return <div className="microphone-recorder">
    {phase==='idle'?<><p className="setting-help">{L('Запишите голос здесь, затем прослушайте и очистите. До 5 минут. Громкость готовой записи выровняем автоматически.','Record here, then listen and clean the audio. Up to 5 minutes. Recording loudness is balanced automatically.')}</p><button type="button" className="quiet microphone-start" disabled={disabled} onClick={()=>void start()}><Microphone size={18} aria-hidden="true"/>{L(file?'Записать заново':'Начать запись',file?'Record again':'Start recording')}</button>{file && <p className="microphone-filename">{file.name}</p>}</>:<>
      <div className="microphone-status"><Microphone size={20} aria-hidden="true"/><strong role="status">{L(phase==='requesting'?'Ожидаем доступ к микрофону':phase==='saving'?'Сохраняем запись':phase==='paused'?'Запись на паузе':'Идёт запись',phase==='requesting'?'Waiting for microphone access':phase==='saving'?'Saving recording':phase==='paused'?'Recording paused':'Recording')}</strong>{active && <span className="microphone-time">{audioTime(seconds)} <span>/ 5:00</span></span>}</div>
      {active && <div className="microphone-level" data-overload={inputQuality==='hot'} role="meter" aria-label={L('Уровень микрофона','Microphone level')} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(level*100)}>{Array.from({length:24},(_,i)=><span key={i} data-lit={level>(i/24)} aria-hidden="true"/>)}</div>}{phase==='recording' && <p className="microphone-input-help">{L(inputQuality==='hot'?'Слишком громкий вход — отодвиньте микрофон.':inputQuality==='quiet'?'Низкий входной уровень. Говорите ближе к микрофону.':'Входной уровень в норме.',inputQuality==='hot'?'Input too loud — move away from the microphone.':inputQuality==='quiet'?'Low input level. Move closer to the microphone.':'Input level is good.')}</p>}
      <div className="microphone-actions">{active && <><button type="button" className="quiet microphone-stop" onClick={()=>stop()}><Stop size={16} weight="fill" aria-hidden="true"/>{L('Завершить запись','Finish recording')}</button><button type="button" className="quiet icon-button" onClick={pause} aria-label={L(phase==='paused'?'Продолжить запись':'Приостановить запись',phase==='paused'?'Resume recording':'Pause recording')}>{phase==='paused'?<Play size={18}/>:<Pause size={18}/>}</button></>}{phase!=='saving' && <button type="button" className="text-link" onClick={()=>stop(true)}><X size={16} aria-hidden="true"/>{L('Отменить','Cancel')}</button>}</div>
    </>}{error && <p className="field-error" role="alert">{error}</p>}
  </div>;
}
