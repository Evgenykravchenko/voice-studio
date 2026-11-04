/** One reusable graph per media element; original files and global listening volume stay separate. */
interface PreviewChannel {
  context:AudioContext;source:MediaElementAudioSourceNode;gain:GainNode;limiter:DynamicsCompressorNode;output:GainNode;connected:boolean;initialized:boolean;
}
let sharedContext:AudioContext|undefined;
const channels=new WeakMap<HTMLMediaElement,PreviewChannel>();
export function previewGain(db:number){return 10**(Math.max(-18,Math.min(12,db))/20);}
export function connectPreview(element:HTMLMediaElement):PreviewChannel {
  let channel=channels.get(element);
  if(!channel){
    const context=sharedContext??=new AudioContext();
    const source=context.createMediaElementSource(element),gain=context.createGain(),limiter=context.createDynamicsCompressor(),output=context.createGain();
    limiter.threshold.value=-.45;limiter.knee.value=0;limiter.ratio.value=20;limiter.attack.value=.003;limiter.release.value=.05;
    channel={context,source,gain,limiter,output,connected:false,initialized:false};channels.set(element,channel);
  }
  if(!channel.connected){channel.source.connect(channel.gain);channel.gain.connect(channel.limiter);channel.limiter.connect(channel.output);channel.output.connect(channel.context.destination);channel.connected=true;}
  return channel;
}
export function updatePreview(channel:PreviewChannel,db:number,volume:number,muted:boolean){
  const now=channel.context.currentTime;
  const gain=previewGain(db),listening=muted?0:volume;
  channel.gain.gain.cancelScheduledValues(now);channel.output.gain.cancelScheduledValues(now);
  if(!channel.initialized){channel.gain.gain.setValueAtTime(gain,now);channel.output.gain.setValueAtTime(listening,now);channel.initialized=true;}
  else{channel.gain.gain.setTargetAtTime(gain,now,.008);if(!listening)channel.output.gain.setValueAtTime(0,now);else channel.output.gain.setTargetAtTime(listening,now,.008);}
}
export function disconnectPreview(element:HTMLMediaElement){
  const channel=channels.get(element);if(!channel || !channel.connected)return;
  element.pause();channel.source.disconnect();channel.gain.disconnect();channel.limiter.disconnect();channel.output.disconnect();channel.connected=false;
}
