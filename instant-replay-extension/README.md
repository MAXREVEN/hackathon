# Instant Replay — Chrome tab recorder (experimental MVP)

## Install (no Node.js needed)
1. Unzip this archive.
2. In Google Chrome open `chrome://extensions`.
3. Turn on **Developer mode** (top right).
4. Click **Load unpacked** and select the extracted `instant-replay-extension` folder containing `manifest.json`.
5. Open a normal website tab, click the extension icon and click **Start recording**.
6. Keep the tab open. Close the popup if desired; recording continues.
7. Click **Save replay** to download the most recent buffered footage.

## Known limitations
- **Experimental MVP, not production-ready.** WebM fragments recorded continuously are not guaranteed to create a fully seekable/playable standalone file when older chunks are dropped. Playback may show incorrect durations or fail. A proper WebM remuxer / segment exporter is required for reliable 3-minute exports.
- The buffer is approximate (based on 1-second chunks); the first segment is retained for initialization. There may be extra frames or gaps.
- Chrome tab capture only; not system-wide game recording.
- The UI timeline is a buffer fill meter, not a scrub/seek timeline.
- Recording data is held in memory and lost if Chrome terminates the offscreen document or the browser closes.
- Saving downloads WebM locally; no sharing or upload is included.
- Capturing restricted Chrome pages is not supported.
- At high bitrates memory consumption can be substantial.

## Privacy
No network requests, no cloud upload, and no analytics. Recording requires clicking Start from the extension popup.

## Troubleshooting Start recording
- Open a normal HTTPS website, not `chrome://extensions`, the Chrome Web Store, or a new-tab page.
- Reload the extension from `chrome://extensions` after replacing the folder.
- Click the extension icon while the target website tab is active, then click Start.
- The popup now shows the underlying capture error.
- If it still fails, inspect the extension service worker and offscreen document in `chrome://extensions` and copy the error message.
