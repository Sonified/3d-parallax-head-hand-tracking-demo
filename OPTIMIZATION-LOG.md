# Optimization Session: Camera-to-Inference Pipeline
**Date:** 2026-04-07 | **Hardware:** MacBook Pro M-series, FaceTime camera, ProMotion display

---

## What We Were Actually Trying to Fix

Perceived ~40ms delay from head movement to scene response. The hypothesis was camera ISP latency or frame transfer overhead. Both turned out to be wrong. The actual bottleneck breakdown (measured):

| Stage | Measured | Pre-session assumption |
|---|---|---|
| Camera ISP latency | ~0ms (captureTime metadata) | "probably 30-40ms" |
| Main thread frame transfer | 0.02ms (VideoFrame) / 0.5ms (createImageBitmap) | unknown |
| Preprocessing (GPU letterbox) | ~2-5ms | "probably fast" |
| Hand inference (WebGPU) | ~8-15ms mean | unknown |
| Face landmark inference | ~13ms mean | unknown |
| Face detector-only inference | ~7.4ms mean | N/A (not yet implemented) |
| 1-Euro filter lag | subjective, tunable | "not the issue" |

**The real latency source was filter smoothing, not the hardware.** The camera was never the problem.

---

## Measured Gains

### Face Mode: Landmark vs Detector-Only
- **Landmark model (478pt):** ~13ms mean inference
- **Detector-only (6pt BlazeFace):** ~7.4ms mean inference
- **Delta: ~5.6ms (~43% reduction)** for the face pipeline
- Trade-off: 6 keypoints instead of 478. For head parallax (only needs 2 eye points), this is lossless.
- This was the single largest measured latency win.

### VideoFrame API vs createImageBitmap (main thread block)
- **createImageBitmap:** ~0.5ms main thread block per frame
- **VideoFrame:** ~0.02ms main thread block per frame
- **Delta: ~25x reduction in main thread stall**
- This matters for render loop smoothness at 120fps (8.3ms budget), not for inference latency.

### Camera Hardware Reality Check
- Mac FaceTime camera hard caps at 30fps regardless of resolution (confirmed via `ffmpeg -f avfoundation`).
- `frameRate: { ideal: 60 }` in getUserMedia does nothing on this hardware.
- `latencyMode: 'realtime'` is a hint with no verifiable effect on Mac.
- **Net gain from camera constraints: 0ms.** Confirmed empirically.

### enableMemPattern
- Added to all 5 ONNX workers. Allows ONNX RT to reuse GPU buffer allocations across inference calls.
- **Measured gain: not isolated.** Expected to reduce first-inference spikes, not steady-state mean. No before/after numbers captured.

### Zero-Copy GPU Path (palm + face detection workers)
- **Before:** GPU letterbox -> CPU readback (mapAsync + slice) -> CPU tensor -> ONNX re-uploads to GPU
- **After:** Shared GPUDevice via `ort.env.webgpu.device`, letterbox stays on GPU, `Tensor.fromGpuBuffer()` skips the roundtrip
- **Measured gain: not isolated in production.** The architectural correctness is clear (eliminated a full GPU->CPU->GPU roundtrip), but we don't have clean before/after benchmark numbers with the same conditions. This is the one gap in the data.

### Filter Tuning (1-Euro filter)
- Extended slider ranges 5x (floor 0-5.0, beta 0-50.0)
- User found settings with "no perceived delay" that were outside old slider range
- **Subjective but significant.** The filter was the real latency source and the old UI prevented tuning it properly.

---

## What Didn't Work (and Why)

### enableGraphCapture
- Requires 100% of graph ops on WebGPU EP. ONNX RT intentionally routes Reshape/Squeeze/Concat/Slice to CPU for shape metadata resolution.
- PReLU decomposition (124->228 nodes) was done specifically to try to unlock this. It worked for those ops but Pad/Resize remained CPU-resident.
- The CPU shape ops carry no tensor data, just shape integers. Cost is near-zero. Not worth fighting.
- **Verdict:** Architectural limitation of ONNX RT's WebGPU EP, not fixable at the model level without forking ONNX RT.

### Preprocessing Optimization (createImageBitmap resize)
- Hypothesis: downsampling before GPU letterbox would reduce letterbox work.
- Shootout result: **the resize was making it slower.** GPU dispatch overhead at 192x192 target size exceeded any savings. CPU canvas was competitive with or faster than GPU letterbox at small sizes.
- **Verdict:** GPU preprocessing wins at large resolutions, not at model input sizes (~192px). The models downsample internally anyway.

### SharedArrayBuffer Multi-Consumer Upload
- Hypothesis: one worker uploads camera frame to shared buffer, multiple consumers read from it (zero redundant uploads).
- Shootout result: **wash at 3 consumers.** Atomics.notify latency (~0.1ms) plus buffer sync overhead canceled the savings.
- **Verdict:** Only worth it at many consumers (5+) or very large frames.

---

## Architecture Insights (for future work)

**Fire-and-forget beats serial.** Hand + face workers running independently, never blocking the render loop, was the key architectural win. The render loop at 120fps never waits for inference; it just uses the last result. This decoupling is why the system feels responsive even at 30fps inference.

**Kalman at 120fps from 30fps camera.** With fire-and-forget architecture, you get results at ~30fps (camera rate) but render at 120fps. A Kalman predictor between inference frames fills the gap with predicted positions, making motion appear 120fps-smooth. This was demonstrated in `pipeline-architecture-shootout.html` but not yet wired into the main demo.

**The real latency is perceptual.** Camera ISP: 0ms. Frame transfer: 0.02ms. Inference: 8-13ms. The "lag" the user felt was the 1-Euro filter's smoothing function, which trades latency for stability. The right solution is tunable filter params — which is exactly what the extended sliders provide.

---

## Patent Signal Analysis

| Technique | Novel? | Notes |
|---|---|---|
| Zero-copy GPU path via shared ONNX device | **Potentially novel** | `ort.env.webgpu.device` sharing + `Tensor.fromGpuBuffer()` as a pattern isn't documented in ONNX RT WebGPU examples. The specific pattern of stealing the ONNX device for preprocessing work may be new. Relates to Claim II. |
| Detector-only mode for parallax (6pt -> 2pt) | **No** | Model selection is engineering, not invention. |
| PReLU decomposition for WebGPU EP | **Weak** | Known technique (graph surgery to force GPU-resident ops). Not browser-specific. |
| enableGraphCapture + why it fails | **No** | ONNX RT limitation, documented in their issues. Documenting the failure isn't a claim. |
| Fire-and-forget worker architecture | **Weak** | Decoupled inference/render is known. The specific pattern in WebGPU + worker context may have a narrow claim but it's thin. |
| Kalman prediction between camera frames | **No** | Standard technique. Nothing browser-specific. |
| 1-Euro filter for head/hand tracking in browser | **Potentially already in Claim I** | Review I.A - if it's not explicitly mentioned, it belongs there. |
| VideoFrame zero-copy main thread | **No** | WebCodecs API, standard usage pattern. |

**Strongest signal:** The zero-copy shared-device pattern (preprocessing on the same GPUDevice as ONNX RT, eliminating the GPU->CPU->GPU roundtrip for inference input) is architecturally novel in the browser WebGPU context and directly supports Claim II.A's framerate-latency tradeoff elimination argument.

---

## Files Created This Session

| File | Purpose |
|---|---|
| `preprocess-shootout.html` | 7 camera-to-tensor strategies benchmarked |
| `pipeline-shootout.html` | Full pipeline with workers, burst/interleaved modes, camera latency breakdown |
| `shared-vs-independent-shootout.html` | SharedArrayBuffer vs independent upload for N consumers |
| `pipeline-architecture-shootout.html` | Serial vs fire-and-forget vs double-buffer vs Kalman, decoupled render/camera |
| `blendshape-data-collector.html` | Teacher model data collection (128x128 RGB + 52 blendshape labels) |
| `pixel-face-demo.html` | Face crop resolution comparison (128/64/32/16px, grayscale) |
| `serve.py` | Dev server with COOP/COEP headers (required for SharedArrayBuffer + WebGPU in workers) |
| `BLENDSHAPE-MODEL-PLAN.md` | Architecture plan for in-browser WebGPU blendshape distillation model |

## Data Collected

- **19,129 frames** of labeled blendshape training data
- Format: 4-byte frame count header + (128x128x3 RGB + 52x float32 blendshapes) per frame
- Coverage: 48/51 blendshapes with good distribution; cheekPuff/cheekSquint variants sparse
- ~900MB binary file

## What Still Needs Before/After Numbers

The zero-copy GPU path is the one optimization where we have the architecture right but no clean isolated measurement. To get this: add timing around the old `mapAsync` + readback path in a test page, compare to `Tensor.fromGpuBuffer()` path under identical conditions. Expected win: 1-3ms per inference call (the GPU->CPU->GPU roundtrip, which is synchronization-bound).
