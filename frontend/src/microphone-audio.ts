/** PCM WAV keeps a finite duration across browsers, including MediaRecorder WebM. */
export function microphoneWave(buffer: Pick<AudioBuffer,'length'|'sampleRate'|'numberOfChannels'|'getChannelData'>): Uint8Array<ArrayBuffer> {
  const bytes=new Uint8Array(44+buffer.length*2),view=new DataView(bytes.buffer);
  const word=(offset:number,value:string)=>{for(let i=0;i<value.length;i++)view.setUint8(offset+i,value.charCodeAt(i));};
  word(0,'RIFF');view.setUint32(4,bytes.length-8,true);word(8,'WAVE');word(12,'fmt ');view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,1,true);view.setUint32(24,buffer.sampleRate,true);view.setUint32(28,buffer.sampleRate*2,true);view.setUint16(32,2,true);view.setUint16(34,16,true);word(36,'data');view.setUint32(40,buffer.length*2,true);
  const channels=Array.from({length:buffer.numberOfChannels},(_,i)=>buffer.getChannelData(i));
  for(let i=0;i<buffer.length;i++){let value=0;for(const channel of channels)value+=channel[i]/channels.length;value=Number.isFinite(value)?Math.max(-1,Math.min(1,value)):0;view.setInt16(44+i*2,Math.round(value*(value<0?32768:32767)),true);}
  return bytes;
}

/** Offline look-ahead leveling: no startup gain ramp, no changes to timing or source samples. */
export function levelMicrophone(buffer:Pick<AudioBuffer,'length'|'sampleRate'|'numberOfChannels'|'getChannelData'>):Float32Array<ArrayBuffer> {
  const audio=new Float32Array(buffer.length),size=Math.max(1,Math.round(buffer.sampleRate*.05)),frames=Math.ceil(audio.length/size),rms:number[]=[],peaks:number[]=[];
  for(let c=0;c<buffer.numberOfChannels;c++){const channel=buffer.getChannelData(c);for(let i=0;i<audio.length;i++)audio[i]+=(Number.isFinite(channel[i])?channel[i]:0)/buffer.numberOfChannels;}
  for(let start=0;start<audio.length;start+=size){let sum=0,peak=0;const end=Math.min(audio.length,start+size);for(let i=start;i<end;i++){sum+=audio[i]**2;peak=Math.max(peak,Math.abs(audio[i]));}rms.push(Math.sqrt(sum/(end-start)));peaks.push(peak);}
  const active=rms.filter(value=>value>.001).sort((a,b)=>a-b);if(!active.length)return audio;
  const reference=active[Math.min(active.length-1,Math.floor(active.length*.75))],base=.1/reference,maxGain=10**(18/20),ceiling=10**(-1/20);
  const wanted=rms.map(value=>value>.001?Math.max(.25,Math.min(maxGain,base*(reference/value)**(2/3))):NaN);
  let previous=wanted.find(Number.isFinite)??1;
  for(let i=0;i<wanted.length;i++){if(Number.isFinite(wanted[i]))previous=wanted[i];else wanted[i]=previous;}
  const gains=wanted.map((_,i)=>{let sum=0,count=0,peak=0;for(let j=Math.max(0,i-4);j<=Math.min(frames-1,i+4);j++){sum+=Math.log(wanted[j]);count++;}for(let j=Math.max(0,i-1);j<=Math.min(frames-1,i+1);j++)peak=Math.max(peak,peaks[j]);return Math.min(Math.exp(sum/count),peak?ceiling/peak:maxGain);});
  for(let i=0;i<audio.length;i++){const frame=Math.floor(i/size),fraction=(i%size)/size,gain=gains[frame]*(1-fraction)+gains[Math.min(frames-1,frame+1)]*fraction;audio[i]*=gain;}
  return audio;
}
export function leveledMicrophoneWave(buffer:Pick<AudioBuffer,'length'|'sampleRate'|'numberOfChannels'|'getChannelData'>){const audio=levelMicrophone(buffer);return microphoneWave({length:audio.length,sampleRate:buffer.sampleRate,numberOfChannels:1,getChannelData:()=>audio});}
export function microphoneLevel(rms:number){return Math.max(0,Math.min(1,(20*Math.log10(Math.max(1e-8,rms))+60)/54));}
