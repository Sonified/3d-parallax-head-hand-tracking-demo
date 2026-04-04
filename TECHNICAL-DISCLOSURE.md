# Technical Disclosure

**Author:** Robert Alexander
**Date of publication:** April 3, 2026
**Repository:** https://github.com/Sonified/3d-parallax-head-hand-tracking-demo

This document is a public technical disclosure establishing prior art for the methods described below. Some techniques are implemented in this repository; others are implemented in related private repositories and disclosed here. All methods described are the original work of the author.

---

## 1. Single-Camera Head-Coupled Parallax + Hand Gesture Input

A browser-based system using a single consumer webcam to simultaneously drive head-coupled 3D parallax and hand gesture recognition for real-time interactive input. No depth sensor, no plugins, no special hardware.

A single RGB camera feed (via `getUserMedia`) is shared between two concurrent ML inference pipelines running in separate Web Workers. Face detection extracts head position from eye keypoints (midpoint for x/y, inter-eye distance for z depth proxy). Hand landmark detection extracts 21 3D landmarks per frame for gesture recognition. Both workers receive video frames as `ImageBitmap` objects transferred via `postMessage` (zero-copy). All ML inference runs off the main thread, preserving smooth 120fps+ rendering.

The 3D scene (Three.js) applies head position as camera translation, creating the illusion of looking through a window into 3D space. Hand gestures simultaneously trigger interactive events.

The specific combination of simultaneous head-coupled parallax rendering and hand gesture game input from a single consumer RGB camera, running entirely in-browser without plugins or depth sensors, with concurrent Web Worker ML inference sharing one video feed, is a novel system architecture as of the date of this publication.

### Prior art context

- **Head-coupled parallax** from a webcam: Johnny Lee (Wii Remote, 2007), headtrackr.js (browser, 2012)
- **Hand gesture recognition** from a webcam: GestureTek (1991+), Leap Motion, Microsoft Kinect, Google MediaPipe (2020+)
- **Browser-based ML inference**: TensorFlow.js, MediaPipe Web, ONNX Runtime Web

## 2. Eye-to-Hand Aim Ray via Linear Regression

The face detection pipeline provides eye position while the hand landmark pipeline provides fingertip position. A calibrated linear regression maps the vector from eye position through the index fingertip to a screen-space coordinate, producing a gaze-aligned aim ray. The user points at targets in the 3D scene by physically pointing their finger, with the system inferring aim direction from the spatial relationship between tracked eye and hand landmarks. Calibration captures several known screen points with corresponding eye/hand vectors to fit the regression model.

## 3. WebGPU Compute Shader Inference

The hand and face tracking ML models (BlazePalm, Hand Landmark, BlazeFace, Face Landmark) are extracted as ONNX format neural networks and executed via ONNX Runtime Web with a WebGPU compute shader backend, eliminating the synchronous `glReadPixels` bottleneck present in WebGL-based inference. This enables parallel two-hand landmark inference in separate Web Workers, each with independent WebGPU device contexts.

Benchmarked on MacBook Pro M1 Max: hand tracking improves from ~47fps (MediaPipe) to ~72fps (WebGPU), face tracking from ~55fps to ~77fps, with zero CPU readback during preprocessing (GPU letterbox, GPU affine warp between detection and landmark stages via `Tensor.fromGpuBuffer`). Only 252 bytes per hand and 5.7KB per face cross the GPU-CPU boundary per frame.

The WebGPU compute shader inference approach is implemented as a standalone open-source library: [webgpu-vision](https://github.com/Sonified/webgpu-vision).

## 4. PReLU Decomposition for WebGPU Execution

ONNX Runtime Web's WebGPU execution provider lacks a native PReLU kernel, causing GPU-CPU roundtrips for each PReLU op -- 69 per frame in the face landmark model alone. Decomposing PReLU(x, slope) = ReLU(x) + slope * (-ReLU(-x)) into four GPU-native ops eliminates all roundtrips with zero accuracy loss, recovering full inference speed. This technique generalizes to any unsupported ONNX operator expressible as a composition of supported ops, and applies to any WebGPU-based inference runtime.

## 5. GPU-Side Letterbox + Affine Warp Between Detection Stages

In the WebGPU vision pipeline, compute shaders handle letterbox padding and affine warping between palm detection and landmark inference, keeping image data on GPU with zero CPU readback between stages. Standard browser vision pipelines bounce through Canvas for preprocessing. This eliminates the CPU-GPU-CPU roundtrip that typically dominates preprocessing latency in multi-stage detection pipelines.

## 6. Weighted Non-Maximum Suppression

Overlapping detections are averaged by confidence score rather than simply keeping the highest-scoring box. This produces smoother bounding boxes, especially at frame edges where detection confidence drops off. The weighted average preserves spatial information from multiple overlapping proposals rather than discarding all but one.

## 7. Compact Networked Player State via Face Blendshapes + Head Pose

The face landmark pipeline produces 52 blendshape coefficients (eyeBlinkLeft, mouthSmileLeft, browOuterUpRight, jawOpen, etc.) via a dedicated blendshape inference worker running in parallel with the landmark worker. Combined with head position (3 floats) and head rotation derived from landmarks (pitch, yaw, roll as 3 floats), the complete facial expression and head pose state is 232 bytes per frame. At 30fps this is 7KB/sec over a WebRTC data channel, sufficient to drive full avatar facial animation on a remote client. For comparison, a voice call uses more bandwidth. The blendshape worker runs fire-and-forget with one frame of latency, adding zero fps overhead to the tracking pipeline.

## 8. Depth-Corrected Hand Projection for Desktop VR Interactions

MediaPipe hand landmarks include per-landmark z-values inferred from hand scale and proportions. By tracking the smoothed z-delta over time and applying it as an inverse projection correction in the head-coupled parallax scene, a hand physically moving toward the camera can be rendered as moving away from the viewer into the 3D scene. This counteracts the natural 2D projection (where closer objects appear larger) and produces spatially coherent hand movement within the parallax space. A punch toward the webcam reads as a punch into the screen.

This technique uses relative z-velocity rather than absolute z-position, making it robust to the noise inherent in monocular depth estimation. This enables desktop VR style interactions such as boxing and tennis from a single consumer webcam, without a depth sensor or headset.

## 9. Parallax-Coupled Hand Gesture Coordinate System

Hand landmarks are mapped to 3D scene space relative to the current parallax camera position. The hand "rides with" the head-coupled perspective shift. Most systems treat hand position and head tracking as independent coordinate systems. Coupling them makes the hand feel like it exists inside the parallax window rather than floating in front of it. This is central to producing coherent first-person interaction in a head-coupled parallax scene.

## 10. Atomic Float Gradient Accumulation on WebGPU

GPU-based gesture training uses a compare-and-swap loop (emulated `atomicAddF32`) to accumulate gradients from all samples in parallel into a single weight-sized buffer. Standard GPU training allocates per-sample gradient arrays and then reduces. This approach is O(weights) memory instead of O(samples x weights). This enables in-browser neural network training on WebGPU with minimal memory overhead, making real-time on-device gesture model training practical in a browser tab.

## 11. Composite 45-Feature Gesture Vector for ASL Classification

The gesture recognition system combines four orthogonal feature families into a single 45-dimensional feature vector: fingertip contact distances, thumb-to-joint distances, per-joint flexion angles, and palm orientation. The first three families are rotation-invariant (relative joint measurements); the fourth adds orientation awareness. Literature review at the time of design found no prior work combining all four feature families. This composite feature engineering is what enables reliable ASL hand sign classification from a single camera in real time.

## 12. Toward Hardware-Free 6DOF Interaction

The depth-corrected hand projection technique points toward a larger result. Conventional 6DOF VR requires either a headset with onboard tracking cameras, an external depth sensor, or a multi-camera rig. This system synthesizes equivalent interaction from signals already present in a single RGB stream.

The head-coupled parallax pipeline provides three translational and three rotational degrees of freedom from face landmarks alone. Adding depth-estimated hand position extends this into full-body interactive space. A user can lean left to peer around a virtual object, reach toward the screen and feel their hand move into the scene, and pull back to bring it forward again. The physical metaphor is reaching through a window, not wearing a headset.

Several directions extend this further:

**Stable anchor cascade for continuous Z estimation.** The landmark-spread depth signal degrades when the hand partially exits the frame or landmarks are occluded. A visibility-weighted cascade selects the most geometrically stable anchor point at each frame, and on anchor transitions applies a computed offset to preserve Z continuity. The effect is that depth tracking remains locked even as the hand moves to the edges of the camera's view.

**Face-relative hand depth as a corroborating signal.** The angular relationship between head position and hand position in camera space encodes real geometric depth independent of the landmark-spread signal. As the user's head shifts, that angle changes as a function of true 3D distance. Fusing both signals with confidence weighting produces depth estimates that are robust when either signal is noisy or degraded -- two orthogonal measurements of the same physical quantity.

**The combination.** WebGPU inference at 120fps, head-coupled parallax, bilateral hand tracking, and fused monocular depth estimation running concurrently in a browser tab produces a first-person interactive 3D experience requiring no hardware beyond the webcam built into any modern laptop.

---

## License

MIT License. See [LICENSE](LICENSE).
