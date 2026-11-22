let recorder=null, stream=null, audioContext=null, chunks=[], startTime=0, limit=180, audioEnabled=true, exporting=false;
const now=()=>Date.now();
function state(){return {ok:true,recording:recorder?.state==='recording',elapsed:startTime?Math.floor((now()-startTime)/1000):0,available:chunks.length?Math.min(limit,Math.floor((now()-Math.max(startTime,chunks[0].time))/1000)):0,seconds:limit,exporting};}
function mime(){return ['video/webm;codecs=vp8,opus','video/webm;codecs=vp9,opus','video/webm'].find(t=>MediaRecorder.isTypeSupported(t))||'';}
async function stop(){if(recorder&&recorder.state!=='inactive')recorder.stop();recorder=null;initialHeader=null;if(stream){stream.getTracks().forEach(t=>t.stop());stream=null;}if(audioContext){await audioContext.close().catch(()=>{});audioContext=null;}chunks=[];startTime=0;return state();}
async function start({streamId,seconds,audio}){
  if(recorder?.state==='recording')throw Error('Already recording');
  await stop();limit=Math.max(15,Math.min(600,Number(seconds)||180));audioEnabled=audio;
  try {stream=await navigator.mediaDevices.getUserMedia({audio:audioEnabled?{mandatory:{chromeMediaSource:'tab',chromeMediaSourceId:streamId}}:false,video:{mandatory:{chromeMediaSource:'tab',chromeMediaSourceId:streamId}}});}
  catch(e){throw Error('Tab capture failed ('+e.name+'): '+e.message+'. Try a normal HTTPS tab and reload the extension.');}
  if(audioEnabled&&stream.getAudioTracks().length){audioContext=new AudioContext();const source=audioContext.createMediaStreamSource(stream);source.connect(audioContext.destination);}
  stream.getVideoTracks()[0].addEventListener('ended',()=>{stop().catch(console.error);});
  recorder=new MediaRecorder(stream,{mimeType:mime(),videoBitsPerSecond:3000000});
  recorder.ondataavailable=e=>{if(e.data.size){if(!initialHeader)initialHeader=e.data;chunks.push({blob:e.data,time:now()});const cutoff=now()-(limit+4)*1000;while(chunks.length>1&&chunks[1].time<cutoff)chunks.shift();}};
  recorder.onerror=e=>console.error('Recorder error',e);
  recorder.start(1000);startTime=now();return state();
}
async function save(){
  if(recorder?.state!=='recording')throw Error('Start recording first');
  if(exporting)throw Error('Export already in progress');
  exporting=true;
  try{
    // Request the latest chunk without stopping recording.
    const before=chunks.length;recorder.requestData();await new Promise(r=>setTimeout(r,250));
    const snapshot=chunks.slice();if(!snapshot.length)throw Error('No recorded footage yet');
    // MediaRecorder chunks are stream fragments; Chromium may require the initialization segment.
    // Preserve the first segment header separately for best-effort standalone playback.
    const parts=[];
    if(initialHeader && snapshot[0]?.blob !== initialHeader)parts.push(initialHeader);
    for(const item of snapshot)parts.push(item.blob);
    const blob=new Blob(parts,{type:recorder.mimeType||'video/webm'});
    const url=URL.createObjectURL(blob);
    const stamp=new Date().toISOString().replace(/[:.]/g,'-');
setTimeout(()=>URL.revokeObjectURL(url),120000);
return {ok:true,url,filename:`instant-replay-${stamp}.webm`,bytes:blob.size};
  }finally{exporting=false;}
}
let initialHeader=null;
chrome.runtime.onMessage.addListener((m,sender,reply)=>{
  if(m.to!=='recorder')return;
  (async()=>{
    if(m.action==='start'){initialHeader=null;const result=await start(m);return result;}
    if(m.action==='stop')return stop();
    if(m.action==='status')return state();
    if(m.action==='save')return save();
    throw Error('Unknown action');
  })().then(reply,e=>reply({ok:false,error:e.message}));return true;
});
