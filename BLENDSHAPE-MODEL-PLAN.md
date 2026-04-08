# Blendshape Distillation Model Plan

## What We're Building
A personal blendshape model trained in-browser on the user's own face using WebGPU compute shaders. The calibration process IS the gameplay.

## Architecture
- **Input**: 64x64 grayscale face crop = 4,096 features
- **Model**: MLP (4096 → 512 → 256 → 52) with ReLU activations, sigmoid output
- **Output**: 52 ARKit-compatible blendshape coefficients (0-1)
- **Training**: WebGPU atomic gradient accumulation (adapted from Spellaria gesture-trainer-gpu.js)
- **Loss**: MSE (regression, not classification)
- **Teacher**: MediaPipe face landmarks + blendshape model (full pipeline)

## What Changes from gesture-trainer-gpu.js
1. **Loss function**: softmax + cross-entropy → MSE
2. **Labels buffer**: `array<u32>` (class index) → `array<f32>` (52 float targets per sample)
3. **Output activation**: softmax → sigmoid (blendshapes are 0-1)
4. **Backward pass initial gradient**: `buf_b[i] = softmax[i] - one_hot[i]` → `buf_b[i] = 2 * (output[i] - target[i]) / numOutputs`
5. **Input dimensions**: landmark features (~63-126 floats) → 4096 floats (64x64 grayscale pixels)
6. **Predict shader**: remove softmax, add sigmoid

## Pipeline
1. Face detector (already running, 128x128, 409KB, ~3ms) finds face bbox
2. Crop face from camera frame, downsample to 64x64 grayscale
3. Run through personal MLP model (~500KB, < 1ms)
4. Output: 52 blendshape coefficients

## Replaces
- Face landmark model (256x256, 5MB, 13ms)
- Face blendshape model (1.9MB, 2ms)
- Total replaced: 6.9MB, 15ms → ~500KB, < 1ms

## Training Data Already Collected
- File: `~/Downloads/blendshape-training-19129frames-*.bin`
- Format: 4 byte header (uint32 frame count) + per frame: 128x128x3 RGB crop + 52 float32 blendshapes
- 19,129 frames, 900MB
- 48/51 blendshapes have good coverage (cheekPuff, cheekSquint, noseSneer dead -- teacher limitation)

## Training Flow (In-Browser)
1. User opens calibration page
2. Full pipeline runs: face detector → landmarks → blendshapes (teacher)
3. Face crop downsampled to 64x64 grayscale → stored as training sample with teacher's blendshape output as label
4. Every N frames, run a training batch on WebGPU (atomic gradient accumulation)
5. Live loss display, coverage tracker with dancing bars
6. When loss plateaus, model is ready -- export weights, switch to fast inference

## Patent Angle
- On-device personalized model distillation in a web browser
- Zero data leaves the device
- Calibration as gameplay mechanic (Claim III.C from the disclosure)
- Student model eliminates an entire inference stage
- WebGPU compute shader training (novel for browser context)

## Key Files
- `gpu-vision/src/face-pipeline.js` - face tracking pipeline (teacher)
- `explorations/spellaria/prototypes/js/gesture-trainer-gpu.js` - WebGPU training reference
- `blendshape-data-collector.html` - data collection tool (already built)
- `pixel-face-demo.html` - resolution comparison tool
- Training data: `~/Downloads/blendshape-training-19129frames-*.bin`

## Session Context
- All workers optimized with zero-copy GPU paths (palm + face detection)
- enableMemPattern on all ONNX sessions
- Palm model PReLU decomposed
- Face detector-only mode proven for head parallax (7ms vs 13ms)
- Camera latency measured at ~0ms (ISP not the bottleneck)
- Hardware camera max: 30fps (all resolutions)
- Display: 120Hz ProMotion
- Hand filter ranges extended, "no perceived delay" achieved
