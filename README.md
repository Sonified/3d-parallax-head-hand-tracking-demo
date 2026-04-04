# Single-Camera Head-Coupled Parallax + Hand Gesture Input for Interactive 3D

A browser-based system that uses a single consumer webcam to simultaneously drive head-coupled 3D parallax and hand gesture recognition for real-time interactive input. No depth sensor, no plugins, no special hardware. Runs entirely in a standard web browser on commodity laptops and desktops.

## Method

A single RGB camera feed (via `getUserMedia`) is shared between two concurrent processing pipelines running in separate Web Workers:

1. **Face Detection Worker**: Runs MediaPipe FaceDetector to extract head position from eye keypoints. The midpoint of the two eyes gives horizontal/vertical position (normalized -1 to +1). Inter-eye distance relative to a calibration reference gives depth (closer to camera = larger apparent eye distance). These three values drive real-time camera offset in a 3D scene, creating head-coupled parallax (also known as "fish-tank VR" or "window effect").

2. **Hand Landmark Worker**: Runs MediaPipe HandLandmarker to extract 21 3D hand landmarks per frame. Gesture recognition is performed on the extracted landmarks. In this demo, pinch detection uses the Euclidean distance between thumb tip (landmark 4) and index finger tip (landmark 8). The gesture state drives game input (e.g., pinch-to-fire).

Both workers receive video frames as `ImageBitmap` objects transferred via `postMessage` (zero-copy transfer of ownership). This keeps all ML inference off the main thread, preserving smooth 60fps+ rendering.

The 3D scene (Three.js) applies the head position data as camera translation, creating the illusion of looking through a window into 3D space. The viewer's physical head movement maps to perspective changes in the rendered scene. Simultaneously, hand gestures trigger interactive events (projectile firing in this demo).

## Architecture

```
                          getUserMedia (single RGB webcam)
                                      |
                                   <video>
                                      |
                          requestVideoFrameCallback
                                      |
                    createImageBitmap x2 (one per worker)
                           /                    \
                    [transfer]              [transfer]
                         |                        |
                  Face Worker              Hand Worker
                  (FaceDetector)          (HandLandmarker)
                         |                        |
                  postMessage              postMessage
                  {face keypoints}         {hand landmarks}
                         \                       /
                          \                     /
                           Main Thread (60fps)
                          /                     \
                Head-Coupled Parallax     Gesture Detection
                (camera.position.set)     (pinch distance)
                          \                     /
                           Three.js Render Loop
```

## Key Technical Details

- **ImageBitmap Transfer**: Video frames are converted to `ImageBitmap` and transferred (not copied) to workers via the structured clone algorithm's transfer list. Workers call `image.close()` after inference to release GPU/memory resources.

- **Independent Frame Rates**: Face and hand tracking can run at different rates. The face detector is lightweight (BlazeFace, ~2ms) while hand tracking is heavier (~8-15ms). The system degrades gracefully if either worker falls behind.

- **Head Position Extraction**: Only two data points per frame are needed for parallax: the midpoint of the two eyes (x, y position) and the inter-eye distance (z depth proxy). No full face mesh is required.

- **Pinch Detection**: The 3D Euclidean distance between MediaPipe landmarks 4 (thumb tip) and 8 (index finger tip), thresholded at ~0.05 normalized units. This extends to arbitrary gesture classification using the full 21-landmark set.

- **ESM-to-Worker Patch**: MediaPipe's vision bundle is distributed as an ES module, which cannot be loaded in classic Web Workers via `importScripts`. The workers fetch the ESM source and patch the export statement to assign to `self.$mediapipe`, making it available in worker scope.

## Requirements

- Modern browser with WebRTC (`getUserMedia`), Web Workers, `createImageBitmap`, and `requestVideoFrameCallback` support
- Consumer webcam (built-in laptop camera works)
- No build step, no dependencies to install

## Running

Serve the directory over HTTP (required for Worker and MediaPipe WASM loading):

```bash
# Python
python3 -m http.server 8080

# Node
npx serve .
```

Open `http://localhost:8080` in Chrome, Edge, or another Chromium-based browser. Click "Start Camera" and grant camera permission.

- Move your head side-to-side, up-down, forward-back to see the parallax effect
- Hold your hand in view and pinch (touch thumb to index finger) then release to fire a projectile

## Additional Implementations

The system architecture described above extends to several additional techniques implemented by the author:

- **Eye-to-hand aim ray via linear regression**: The face detection pipeline provides eye position while the hand landmark pipeline provides fingertip position. A calibrated linear regression maps the vector from eye position through the index fingertip to a screen-space coordinate, producing a gaze-aligned aim ray. The user points at targets in the 3D scene by physically pointing their finger, with the system inferring aim direction from the spatial relationship between tracked eye and hand landmarks. Calibration captures several known screen points with corresponding eye/hand vectors to fit the regression model.

- **WebGPU compute shader inference**: The hand and face tracking ML models (BlazePalm, Hand Landmark, BlazeFace, Face Landmark) can be extracted as ONNX format neural networks and executed via ONNX Runtime Web with a WebGPU compute shader backend, eliminating the synchronous glReadPixels bottleneck present in WebGL-based inference. This enables parallel two-hand landmark inference in separate Web Workers, each with independent WebGPU device contexts. Benchmarked on MacBook Pro M1 Max: hand tracking improves from ~47fps (MediaPipe) to ~72fps (WebGPU), face tracking from ~55fps to ~77fps, with zero CPU readback during preprocessing (GPU letterbox, GPU affine warp between detection and landmark stages via Tensor.fromGpuBuffer). Only 252 bytes per hand and 5.7KB per face cross the GPU-CPU boundary per frame.

- **Compact networked player state via face blendshapes + head pose**: The face landmark pipeline produces 52 blendshape coefficients (eyeBlinkLeft, mouthSmileLeft, browOuterUpRight, jawOpen, etc.) via a dedicated blendshape inference worker running in parallel with the landmark worker. Combined with head position (3 floats) and head rotation derived from landmarks (pitch, yaw, roll as 3 floats), the complete facial expression and head pose state is 232 bytes per frame. At 30fps this is 7KB/sec over a WebRTC data channel, sufficient to drive full avatar facial animation on a remote client. For comparison, a voice call uses more bandwidth. The blendshape worker runs fire-and-forget with one frame of latency, adding zero fps overhead to the tracking pipeline.

- **Depth-corrected hand projection for desktop VR interactions**: MediaPipe hand landmarks include per-landmark z-values inferred from hand scale and proportions. By tracking the smoothed z-delta over time and applying it as an inverse projection correction in the head-coupled parallax scene, a hand physically moving toward the camera can be rendered as moving away from the viewer into the 3D scene. This counteracts the natural 2D projection (where closer objects appear larger) and produces spatially coherent hand movement within the parallax space. A punch toward the webcam reads as a punch into the screen. This technique uses relative z-velocity rather than absolute z-position, making it robust to the noise inherent in monocular depth estimation. This enables desktop VR style interactions such as boxing and tennis from a single consumer webcam, without a depth sensor or headset.

## Prior Art and Context

This project combines several individually well-established techniques into a unified system:

- **Head-coupled parallax** from a webcam: demonstrated by Johnny Lee (Wii Remote, 2007), headtrackr.js (browser, 2012), and others
- **Hand gesture recognition** from a webcam: extensive prior art from GestureTek (1991+), Leap Motion, Microsoft Kinect, Google MediaPipe (2020+)
- **Browser-based ML inference**: TensorFlow.js, MediaPipe Web, ONNX Runtime Web

The specific combination of simultaneous head-coupled parallax rendering and hand gesture game input from a single consumer RGB camera, running entirely in-browser without plugins or depth sensors, with concurrent Web Worker ML inference sharing one video feed, is to the author's knowledge a novel system architecture as of the date of this publication.

## Related: WebGPU Vision

The WebGPU compute shader inference approach described above is implemented as a standalone open-source library: [webgpu-vision](https://github.com/Sonified/webgpu-vision). It provides the full hand and face tracking pipeline running on ONNX Runtime Web with WebGPU backend, replacing MediaPipe's sealed WASM/WebGL binary. This is the recommended approach for bringing ML inference off the main thread and achieving the performance gains described in this document.

## License

MIT License. See [LICENSE](LICENSE).
