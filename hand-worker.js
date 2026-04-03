// Hand landmark worker: runs MediaPipe HandLandmarker off main thread
// Key technique: receives ImageBitmap via transferable, returns 21 3D landmarks

const WASM_URL = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm';
const MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task';

let landmarker = null;

async function init(numHands) {
  // Load MediaPipe vision bundle into worker scope (same ESM patch as face-worker)
  const resp = await fetch('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/vision_bundle.mjs');
  let src = await resp.text();
  src = src.replace(/export\{([^}]+)\}/, 'self.$mediapipe={$1}');
  const blob = new Blob([src], { type: 'application/javascript' });
  importScripts(URL.createObjectURL(blob));

  const vision = await self.$mediapipe.FilesetResolver.forVisionTasks(WASM_URL);
  landmarker = await self.$mediapipe.HandLandmarker.createFromOptions(vision, {
    baseOptions: { modelAssetPath: MODEL_URL, delegate: 'GPU' },
    runningMode: 'VIDEO',
    numHands: numHands || 1,
    minHandDetectionConfidence: 0.3,
    minTrackingConfidence: 0.3,
  });
  self.postMessage({ type: 'init', ok: true });
}

self.onmessage = async (e) => {
  const { type, image, timestamp, numHands } = e.data;
  if (type === 'init') { await init(numHands); return; }
  if (type === 'detect' && landmarker) {
    const result = landmarker.detectForVideo(image, timestamp);
    image.close(); // Release the transferred ImageBitmap
    let landmarks = null;
    if (result.landmarks && result.landmarks.length > 0) {
      landmarks = result.landmarks.map(hand => hand.map(p => ({ x: p.x, y: p.y, z: p.z })));
    }
    self.postMessage({ type: 'result', landmarks });
  }
};
