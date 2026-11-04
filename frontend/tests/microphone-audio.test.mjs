import {test} from 'node:test';
import assert from 'node:assert/strict';
import {microphoneWave} from '../src/microphone-audio.ts';
test('microphone WAV has exact timing, mono PCM16 and safe stereo downmix',()=>{
 const channels=[new Float32Array([1,-1,.5,-.5]),new Float32Array([0,0,.5,-.5])];
 const wave=microphoneWave({length:4,sampleRate:44100,numberOfChannels:2,getChannelData:i=>channels[i]}),view=new DataView(wave.buffer);
 assert.equal(new TextDecoder().decode(wave.slice(0,4)),'RIFF');assert.equal(new TextDecoder().decode(wave.slice(8,12)),'WAVE');
 assert.equal(view.getUint32(4,true)+8,wave.length);assert.equal(view.getUint16(20,true),1);assert.equal(view.getUint16(22,true),1);
 assert.equal(view.getUint32(24,true),44100);assert.equal(view.getUint32(28,true),88200);assert.equal(view.getUint16(34,true),16);
 assert.equal(view.getUint32(40,true),8);assert.deepEqual([...new Int16Array(wave.buffer,44)],[16384,-16384,16384,-16384]);
});
test('microphone PCM clamps overrange and non-finite samples without integer wrap',()=>{
 const wave=microphoneWave({length:5,sampleRate:48000,numberOfChannels:1,getChannelData:()=>new Float32Array([2,-2,NaN,Infinity,0])});
 assert.deepEqual([...new Int16Array(wave.buffer,44)],[32767,-32768,0,0,0]);
});
import {levelMicrophone,microphoneLevel} from '../src/microphone-audio.ts';
test('recording leveling raises quiet opening words without a startup ramp or clipping',()=>{
 const rate=8000,input=new Float32Array(rate*4);for(let i=0;i<input.length;i++)input[i]=Math.sin(2*Math.PI*220*i/rate)*(i<rate?.006:.12);
 const original=input.slice(),output=levelMicrophone({length:input.length,sampleRate:rate,numberOfChannels:1,getChannelData:()=>input});
 const rms=(a,start,end)=>Math.sqrt(a.slice(start,end).reduce((s,v)=>s+v*v,0)/(end-start));
 assert.equal(output.length,input.length);assert.deepEqual(input,original);
 assert.ok(rms(output,0,rate/2)>rms(input,0,rate/2)*5);
 assert.ok(rms(output,rate*2,rate*3)/rms(output,0,rate/2)<5);
 assert.ok(rms(output,0,rate/4)>=rms(output,rate/4,rate/2)*.9);
 assert.ok(output.every(v=>Number.isFinite(v)&&Math.abs(v)<=10**(-1/20)+1e-6));
});
test('recording leveling leaves silence silent and handles loud impulses safely',()=>{
 const input=new Float32Array(8000);assert.ok(levelMicrophone({length:8000,sampleRate:8000,numberOfChannels:1,getChannelData:()=>input}).every(v=>v===0));
 for(let i=0;i<input.length;i++)input[i]=Math.sin(i)*.004;input[3000]=1;
 const output=levelMicrophone({length:8000,sampleRate:8000,numberOfChannels:1,getChannelData:()=>input});
 assert.ok(output.every(v=>Number.isFinite(v)&&Math.abs(v)<=10**(-1/20)+1e-6));
 assert.equal(microphoneLevel(0),0);assert.ok(microphoneLevel(.02)>.4);assert.ok(microphoneLevel(.02)<microphoneLevel(.1));
});
