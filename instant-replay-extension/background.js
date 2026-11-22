const OFFSCREEN = 'offscreen.html';

async function ensureOffscreen() {
  const contexts = await chrome.runtime.getContexts({
    contextTypes: ['OFFSCREEN_DOCUMENT'],
    documentUrls: [chrome.runtime.getURL(OFFSCREEN)]
  });
  if (!contexts.length) {
    await chrome.offscreen.createDocument({
      url: OFFSCREEN,
      reasons: ['USER_MEDIA'],
      justification: 'Keep tab recording active when popup is closed'
    });
  }
}

async function sendRecorder(message) {
  await ensureOffscreen();
  return chrome.runtime.sendMessage({ ...message, to: 'recorder' });
}

// The offscreen document can't use chrome.downloads, so it returns a blob URL
// and the service worker performs the download.
async function saveReplay() {
  const r = await sendRecorder({ action: 'save' });
  if (!r?.ok) throw Error(r?.error || 'Save failed');
  await chrome.downloads.download({
    url: r.url,
    filename: r.filename,
    saveAs: true
  });
  return { ok: true, bytes: r.bytes };
}

chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (message.to !== 'background') return;
  (async () => {
    if (message.action === 'start') {
      if (!message.streamId) {
        throw Error('Missing tab capture stream ID. Open a normal website and click Start.');
      }
      return sendRecorder({
        action: 'start',
        streamId: message.streamId,
        seconds: message.seconds || 180,
        audio: message.audio !== false
      });
    }
    if (message.action === 'save') return saveReplay();
    return sendRecorder(message);
  })().then(respond, e => respond({ ok: false, error: e.message }));
  return true;
});

chrome.commands.onCommand.addListener(async command => {
  if (command === 'save-replay') {
    try {
      await saveReplay();
    } catch (e) {
      console.error(e);
    }
  }
});