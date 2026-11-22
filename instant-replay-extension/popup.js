const $=id=>document.getElementById(id);
const send=(action,extra={})=>chrome.runtime.sendMessage({to:'background',action,...extra});
async function refresh(){try{const s=await send('status');if(!s?.ok)throw Error(s?.error||'Unknown error');$('status').textContent=s.recording?'● Recording active':'Not recording';$('status').className=s.recording?'active':'';$('start').disabled=s.recording;$('stop').disabled=!s.recording;$('save').disabled=!s.recording||s.exporting;$('seconds').disabled=s.recording;$('audio').disabled=s.recording;$('fill').style.width=`${Math.min(100,100*s.available/s.seconds)}%`;$('detail').textContent=`Available: ${s.available}s / ${s.seconds}s · Session: ${s.elapsed}s`;$('left').textContent=`-${Math.floor(s.seconds/60)}:${String(s.seconds%60).padStart(2,'0')}`;}catch(e){$('message').textContent=e.message;}}
async function act(action,extra){$('message').textContent='Working…';try{const r=await send(action,extra);if(!r?.ok)throw Error(r?.error||'Operation failed');$('message').textContent=action==='save'?'Replay download requested. Check playback.':action==='start'?'Recording started.':'Recording stopped.';}catch(e){$('message').textContent=e.message;}await refresh();}
$('start').onclick=async()=>{
  $('message').textContent='Requesting tab capture…';
  $('start').disabled=true;
  try {
    // Request the stream ID directly from the user click, before any awaits.
    // This avoids losing the user activation needed by tabCapture.
    const tabs=await chrome.tabs.query({active:true,currentWindow:true});
    if(!tabs[0]?.id || /^(chrome|edge|about):/.test(tabs[0].url||''))
      throw Error('Open a normal website (e.g. https://example.com) before recording. Chrome internal pages cannot be captured.');
    const streamId=await chrome.tabCapture.getMediaStreamId({targetTabId:tabs[0].id});
    await act('start',{streamId,seconds:Number($('seconds').value),audio:$('audio').checked});
  }catch(e){$('message').textContent='Start failed: '+e.message;await refresh();}
};$('stop').onclick=()=>act('stop');$('save').onclick=()=>act('save');refresh();setInterval(refresh,1000);
