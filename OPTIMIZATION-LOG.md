# Optimization Log (2026-04-07)

## Changes Made (this repo, branch: webgpu-zero-copy-optimizations)

### 1. Palm Worker: Zero-Copy GPU Path
- **File:** `gpu-vision/src/palm-worker.js`
- **Before:** GPU letterbox wrote to outputBuffer, read back to CPU (`mapAsync` + `slice`), created CPU tensor, ONNX re-uploaded to GPU
- **After:** ONNX session created first, steal its `GPUDevice` via `ort.env.webgpu.device`, build letterbox shader on shared device, use `Tensor.fromGpuBuffer(outputBuffer)` directly. Zero CPU readback for preprocessing.
- Console confirms: "Palm worker: GPU direct path enabled (zero CPU readback, shared device)"

### 2. Face Detection Worker: Same Zero-Copy Fix
- **File:** `gpu-vision/src/face-detection-worker.js`
- Same pattern as palm worker. Was creating its own separate GPUDevice, now shares ONNX RT's device.
- Console confirms: "Face worker: GPU direct path enabled (zero CPU readback, shared device)"

### 3. enableMemPattern on All Workers
- **Files:** All 5 workers (`palm-worker.js`, `landmark-worker.js`, `face-detection-worker.js`, `face-landmark-worker.js`, `face-blendshape-worker.js`)
- Added `enableMemPattern: true` to ONNX session options. Lets ONNX RT reuse GPU memory allocations between inference runs.

### 4. Palm Model: PReLU Decomposition
- **File:** `gpu-vision/models/palm_detection_lite.onnx` (backup at `.onnx.backup`)
- Decomposed 26 PReLU nodes into Relu+Neg+Mul+Sub equivalents
- PReLU was potentially falling back to CPU WASM. Decomposed form uses only GPU-native ops.
- Original 124 nodes -> 228 nodes (more nodes but all GPU-resident)

### 5. Camera Optimizations (index.html)
- `frameRate: { ideal: 60 }` -- request max camera FPS (hardware caps at 30)
- `latencyMode: 'realtime'` -- hint to browser ISP to prioritize speed over quality
- HUD updates throttled to 10fps to avoid DOM thrash
- Head/hand detection debounced (500ms grace period before showing "Not found")
- Hand filter sliders extended: Floor 0-5.0 (was 0-1.0), Beta 0-50.0 (was 0.5-10.0)

### 6. Benchmark Instrumentation (index.html)
- Added `_bench` object that tracks hand/face inference latency per call
- Reports mean, p95, max every 5 seconds to console as `[BENCH]` lines

## What Didn't Work

### enableGraphCapture
- Requires ALL ops on WebGPU EP (no CPU fallbacks)
- ONNX RT intentionally puts Reshape, Squeeze, Concat on CPU for shape metadata
- Even after PReLU decomposition, Pad/Resize kept the palm model off graph capture
- These CPU shape ops are near-zero cost (metadata only, no data transfer), so not worth fighting

## Changes NOT Yet Ported to webgpu-vision Primary Repo

The gpu-vision source files in this repo are a copy. The following need to be ported to the primary `webgpu-vision` repo:
- `palm-worker.js` -- full rewrite of init + detect handlers
- `face-detection-worker.js` -- full rewrite of init + detect handlers  
- `landmark-worker.js` -- enableMemPattern added
- `face-landmark-worker.js` -- enableMemPattern added
- `face-blendshape-worker.js` -- enableMemPattern added
- `models/palm_detection_lite.onnx` -- PReLU-decomposed model

## Shootout Test Pages Created
- `preprocess-shootout.html` -- camera-to-tensor preprocessing strategies
- `pipeline-shootout.html` -- full pipeline with workers, interleaved/burst modes
- `shared-vs-independent-shootout.html` -- SharedArrayBuffer vs independent frame upload
- `pipeline-architecture-shootout.html` -- serial vs fire-and-forget vs double-buffer vs Kalman skip
- `serve.py` -- dev server with COOP/COEP headers for SharedArrayBuffer

## Key Findings from Shootouts
- Camera ISP latency: ~0ms (not the bottleneck we feared)
- Preprocessing: ~2-5ms (already fast, marginal gains from optimization)
- VideoFrame transfer: 0.02ms main thread block (vs 0.5ms for createImageBitmap)
- SharedArrayBuffer vs independent upload: wash at 3 consumers
- Camera hardware max: 30fps (all resolutions, confirmed via ffmpeg)
- Display runs at 120fps (ProMotion), inference at 30fps -- Kalman prediction fills the gap
