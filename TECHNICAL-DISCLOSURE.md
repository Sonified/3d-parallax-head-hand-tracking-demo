# Technical Disclosure

**Author:** Robert Alexander
**Date of publication:** April 3, 2026
**Repository:** https://github.com/Sonified/3d-parallax-head-hand-tracking-demo

This document is a public technical disclosure establishing prior art for the methods described below. Some techniques are implemented in this repository; others are implemented in related private repositories and disclosed here. All methods described are the original work of the author.

### System Claim

The methods described in this document individually draw on established techniques in computer vision, browser ML inference, and spatial audio. The novel contribution is their integration: a unified real-time system in which a single consumer camera, including but not limited to a built-in webcam, simultaneously drives head-coupled visual parallax, bilateral hand tracking with derived depth, world-locked spatial audio, and GPU-accelerated ML inference (for example via WebGPU compute shaders), all running concurrently in an unmodified browser tab or comparable client-side runtime on commodity hardware. The combination produces a first-person audiovisual 3D experience with 6DOF-equivalent interaction requiring no headset, depth sensor, or specialized hardware. No prior system is known to combine these elements in this configuration as of the date of this publication.

---

## 1. Hardware-Free 6DOF Interaction

Conventional 6DOF VR requires either a headset with onboard tracking cameras, an external depth sensor, or a multi-camera rig. This system synthesizes equivalent interaction from signals already present in a single RGB stream, including but not limited to a consumer webcam.

The head-coupled parallax pipeline provides three translational and three rotational degrees of freedom from face landmarks or other facial feature detection methods. Adding depth-estimated hand position extends this into full-body interactive space. A user can, for example, lean left to peer around a virtual object, reach toward the screen and feel their hand move into the scene, and pull back to bring it forward again. The physical metaphor is reaching through a window, not wearing a headset. This interaction model is fully implemented and demonstrated in a related private repository as of the date of this disclosure.

Several techniques make this work:

**Stable anchor cascade for continuous Z estimation.** The landmark-spread depth signal may degrade when the hand partially exits the frame or landmarks are occluded. A stability-aware selection mechanism, such as a visibility-weighted cascade, selects the most geometrically stable anchor point at each frame. On anchor transitions, the system applies a computed offset or other continuity-preserving correction to maintain Z continuity. The effect is that depth tracking remains locked even as the hand moves to the edges of the camera's view. In aiming applications, when distal landmarks such as fingertip positions drop below confidence threshold, the system may anchor to proximal landmarks such as the wrist while preserving the last known depth estimate, maintaining continuous aim ray stability through high-uncertainty poses.

**Face-relative hand depth as a corroborating signal.** The angular relationship between head position and hand position in camera space encodes real geometric depth independent of the landmark-spread signal. As the user's head shifts, that angle changes as a function of true 3D distance. Fusing both signals, for example using confidence weighting, produces depth estimates that are robust when either signal is noisy or degraded. More generally, any technique that combines two or more orthogonal monocular depth cues, including but not limited to landmark spread, face-relative angular geometry, apparent size, or other camera-derived signals, to produce a fused depth estimate falls within this approach.

**The combination.** GPU-accelerated inference (for example via WebGPU) at interactive frame rates (for example 120fps or higher), head-coupled parallax, bilateral hand tracking, and fused monocular depth estimation running concurrently in a browser tab or comparable client-side runtime produces a first-person interactive 3D experience requiring no hardware beyond the camera built into any modern laptop or similar consumer device.

## 2. Single-Camera Head-Coupled Parallax + Hand Gesture Input

A browser-based system using a single consumer webcam to simultaneously drive head-coupled 3D parallax and hand gesture recognition for real-time interactive input. No depth sensor, no plugins, no special hardware.

A single RGB camera feed (for example via `getUserMedia` or another video capture API) is shared between two or more concurrent ML inference pipelines running in separate execution contexts, such as Web Workers, threads, or processes. Face detection extracts head position from facial keypoints, including but not limited to eye landmarks (for example, midpoint for x/y, inter-eye distance for z depth proxy). Hand landmark detection extracts 3D landmarks (for example 21 per hand per frame) for gesture recognition. Inference contexts may receive video frames via zero-copy transfer mechanisms such as `ImageBitmap` via `postMessage`, shared memory, or other efficient frame-sharing approaches. All ML inference runs off the main rendering thread, preserving smooth interactive rendering at rates including 120fps or higher.

The 3D scene (rendered using any suitable 3D engine, such as Three.js, WebGL, or WebGPU) applies head position as camera translation, creating the illusion of looking through a window into 3D space. Forward and backward head movement, derived from facial feature geometry such as inter-eye distance, maps to camera Z translation in the 3D scene. The viewer physically leans in to move deeper into the space, and leans back to retreat. This produces a direct physical metaphor for scene traversal requiring no controller input. Hand gestures simultaneously trigger interactive events.

The specific combination of simultaneous head-coupled parallax rendering and hand gesture interactive input from a single consumer RGB camera, running entirely in a client-side runtime such as a browser without plugins or depth sensors, with concurrent off-thread ML inference sharing one video feed, is a novel system architecture as of the date of this publication.

### Prior art context

- **Head-coupled parallax** from a webcam: Johnny Lee (Wii Remote, 2007), headtrackr.js (browser, 2012)
- **Hand gesture recognition** from a webcam: GestureTek (1991+), Leap Motion, Microsoft Kinect, Google MediaPipe (2020+)
- **Browser-based ML inference**: TensorFlow.js, MediaPipe Web, ONNX Runtime Web

## 3. Depth-Corrected Hand Projection for Desktop VR Interactions

Hand landmark models, including but not limited to MediaPipe, produce per-landmark z-values inferred from hand scale and proportions. By tracking a smoothed depth derivative such as z-delta over time and applying it as an inverse projection correction in the head-coupled parallax scene, a hand physically moving toward the camera can be rendered as moving away from the viewer into the 3D scene. This counteracts the natural 2D projection (where closer objects appear larger) and produces spatially coherent hand movement within the parallax space. For example, a punch toward the webcam reads as a punch into the screen.

This technique uses relative z-velocity rather than absolute z-position, making it robust to the noise inherent in monocular depth estimation. This enables desktop VR style interactions, including for example boxing, tennis, or other gesture-driven spatial interactions, from a single consumer webcam, without a depth sensor or headset.

## 4. Parallax-Coupled Hand Gesture Coordinate System

Hand landmarks are mapped to 3D scene space relative to the current parallax camera position. The hand "rides with" the head-coupled perspective shift. Most systems treat hand position and head tracking as independent coordinate systems. Coupling them makes the hand feel like it exists inside the parallax window rather than floating in front of it. This is central to producing coherent first-person interaction in a head-coupled parallax scene.

## 5. Head-Tracked Spatial Audio via AudioListener Sync

The same face-tracking data that drives head-coupled visual parallax simultaneously drives a spatial audio listener position, for example via the Web Audio API AudioListener or any equivalent spatial audio system. Each frame, the listener coordinates are set from the parallax camera position, which is itself computed from webcam-tracked facial features such as eye midpoint and inter-eye distance. When the user physically leans left, both the visual perspective and the audio perspective shift together: audio sources pan compensatorily rightward, remaining world-locked in the 3D scene rather than fixed to the listener's head. This is a single face-tracking pipeline producing two output modalities (visual parallax and spatial audio) in real time, coupling two systems that are normally independent.

## 6. Per-Source Doppler Shift via Manual Velocity Projection

Web Audio API's built-in dopplerFactor was deprecated and removed from all major browsers. This system reimplements Doppler from first principles: each frame, the sound source's velocity vector is projected onto the normalized source-to-listener unit vector to obtain radial velocity, then a Doppler frequency scaling formula is applied to the source frequency each frame. This approach applies to any sound source type, including but not limited to oscillators, sampled audio, and synthesized signals. The effective speed of sound is user-tunable, allowing Doppler intensity to range from imperceptible to extreme.

The Doppler ratio may be applied independently to two or more parallel signal paths, for example the primary oscillator frequency and a bandpass noise filter layer. Decoupling these paths allows spectral timbre to shift at a different rate than pitch, producing perceptual realism that uniform scaling cannot achieve. A "drop only" mode clamps the ratio to at most 1.0, producing pitch and timbre drops on recession without corresponding rises on approach, a cinematic rather than physically accurate effect.

Combined with head-tracked listener position, the result is that a projectile passing the listener's head produces correlated changes across four or more perceptual dimensions simultaneously, including visual position, binaural pan, pitch, and timbre.

## 7. Proximity-Driven Spectral Unmasking for Perceptual Mass

As a sound source approaches the listener, a frequency-dependent filter, such as a high-pass filter, applied to the source signal is progressively opened: for example, the cutoff frequency decreases inversely with distance. At range, only high frequencies are present, giving the object a thin, distant quality. At close range, low frequencies are fully present, giving the object physical weight and presence. This models the perceptual reality that proximity reveals bass content that distance masks, and produces the sensation that an approaching object is gaining mass rather than merely gaining volume. The effect is implemented per source in the audio processing graph (for example via Web Audio API or any equivalent audio engine) and updated each frame from the 3D distance between source and listener position.

Combined with Doppler shift and head-tracked panning, these three techniques form a unified spatial audio system in which a single moving sound source produces correlated changes across visual position, binaural pan, pitch, timbre, and spectral mass simultaneously, all derived from the same 3D scene state and face-tracking pipeline.

## 8. Head-Coupled Aim Ray via Dual-Tracked Linear Regression

In a head-coupled parallax scene, the apparent direction of a pointed finger changes as the viewer's head moves. Leaning right shifts the viewing angle, and a finger pointed at a fixed screen location now corresponds to a different point in 3D scene space. This system derives a continuous world-space aim ray from the geometric relationship between tracked head position and tracked fingertip position, such that the aim ray updates in real time as both head and hand move. The effect is analogous to physically looking down the barrel of a gun: the viewer leans to align their perspective, and the system tracks where they are actually aiming in the 3D scene, not merely where their finger points on the flat screen.

Calibration is performed by displaying a grid of target points across the screen (for example a 5x4 grid spanning 5% to 95% of both axes) and having the user point at each target and perform a capture gesture such as a pinch. Each sample records the known screen coordinate as ground truth alongside the smoothed fingertip position and head position from the face tracking pipeline. The grid cycles indefinitely, allowing additional passes at different head positions to improve robustness across viewing angles. Samples indicating lost hand tracking are discarded before fitting.

From the collected samples, one or more regression models or other learned mappings from pointer and head position to screen coordinates are fit in-browser (for example, two independent regressions, one for each screen axis), taking effect immediately with no page reload. Multiple model variants may be supported, from full models incorporating depth terms to simplified models using only 2D pointer and head position.

The regression output passes through a cascade of smoothing filters with tunable parameters, suppressing jitter on slow movements while preserving fast intentional aim changes.

The calibration mechanic uses the same gesture and tracking pipeline that drives all other system interactions. No additional hardware, no separate calibration device, no page reload. The system calibrates itself using its own input modality, and the resulting aim ray is continuously updated from both head and hand position, producing a world-space interaction ray that responds to physical viewing angle the way a real aimed instrument would.

## 9. WebGPU Compute Shader Inference

Hand and face tracking ML models, such as BlazePalm, Hand Landmark, BlazeFace, and Face Landmark, are extracted in a portable model format (for example ONNX) and executed via a GPU compute shader backend (for example ONNX Runtime Web with WebGPU), eliminating synchronous CPU readback bottlenecks such as `glReadPixels` present in WebGL-based inference. This enables parallel multi-hand landmark inference in separate execution contexts, such as Web Workers, each with independent GPU device contexts.

As an example benchmark on a MacBook Pro M1 Max: hand tracking improves from ~47fps (MediaPipe) to ~72fps (WebGPU), face tracking from ~55fps to ~77fps, with zero CPU readback during preprocessing (GPU-side letterbox and affine warp between detection and landmark stages, for example via `Tensor.fromGpuBuffer` or equivalent GPU buffer passing). In this configuration, only approximately 252 bytes per hand and 5.7KB per face cross the GPU-CPU boundary per frame. The specific bandwidth reduction will vary by model and hardware, but the principle of minimizing cross-boundary data transfer applies generally.

The WebGPU compute shader inference approach is implemented as a standalone open-source library: [webgpu-vision](https://github.com/Sonified/webgpu-vision).

## 10. PReLU Decomposition for WebGPU Execution

When a GPU-based ML runtime, such as ONNX Runtime Web's WebGPU execution provider, lacks a native kernel for a given operation, it falls back to CPU execution, pulling data off the GPU, computing on the CPU, and pushing it back. For example, in the face landmark model, the unsupported PReLU operation triggers this fallback dozens of times per frame (for example 69 times), introducing latency that breaks the perceptual coupling between physical head movement and visual response.

The fix is a pre-deployment graph transformation: decompose the unsupported operation (for example PReLU) into a composition of GPU-native ops using an equivalent mathematical identity, such that the runtime never encounters the unsupported kernel. Zero roundtrips, zero accuracy loss, full inference speed recovered.

This technique generalizes beyond any single operation and beyond any single model type. Any neural network model containing ops unsupported by a target runtime, including but not limited to ONNX models on WebGPU, can potentially be unblocked by expressing those ops as compositions of supported primitives. For browser-based ML and other environments where runtime op coverage lags behind native frameworks, this is a practical path to deploying models that would otherwise be GPU-unusable, keeping the entire inference pipeline on the GPU and preserving the perceptual coherence the system depends on.

## 11. GPU-Side Letterbox + Affine Warp Between Detection Stages

In a GPU-accelerated vision pipeline (for example using WebGPU compute shaders), preprocessing steps including but not limited to letterbox padding and affine warping are performed on the GPU between detection stages such as palm detection and landmark inference, keeping image data on GPU with zero CPU readback between stages. Standard browser vision pipelines typically bounce through Canvas or similar CPU-accessible surfaces for preprocessing. Performing these transforms on the GPU eliminates the CPU-GPU-CPU roundtrip that typically dominates preprocessing latency in multi-stage detection pipelines.

## 12. Weighted Non-Maximum Suppression

Overlapping detections are combined using a weighted averaging approach, for example averaged by confidence score, rather than simply keeping the highest-scoring box. This produces smoother bounding boxes, especially at frame edges where detection confidence drops off. The weighted average preserves spatial information from multiple overlapping proposals rather than discarding all but one.

## 13. Compact Networked Player State via Face Blendshapes + Head Pose

The face landmark pipeline produces a set of blendshape coefficients (for example 52 ARKit-compatible coefficients such as eyeBlinkLeft, mouthSmileLeft, browOuterUpRight, jawOpen, among others) via a dedicated blendshape inference worker running in parallel with the landmark worker. Combined with head position (for example 3 floats) and head rotation derived from landmarks (for example pitch, yaw, roll as 3 floats), the complete facial expression and head pose state can be as compact as approximately 232 bytes per frame. At 30fps this is approximately 7KB/sec over a real-time transport channel such as a WebRTC data channel, WebSocket, or other low-latency protocol, sufficient to drive full avatar facial animation on a remote client. For comparison, a voice call uses more bandwidth. The blendshape worker runs fire-and-forget with one frame of latency, adding zero fps overhead to the tracking pipeline.

## 14. Atomic Float Gradient Accumulation on WebGPU

GPU-based gesture training uses an atomic accumulation technique, such as a compare-and-swap loop (for example emulated `atomicAddF32`), to accumulate gradients from all samples in parallel into a single weight-sized buffer. Standard GPU training allocates per-sample gradient arrays and then reduces. This approach is O(weights) memory instead of O(samples x weights). This enables in-browser neural network training on GPU compute (for example via WebGPU) with minimal memory overhead, making real-time on-device gesture model training practical in a browser tab or comparable client-side runtime.

## 15. Derived Geometric Feature Classification for In-Game Gesture Triggers

Hand landmark coordinates from a single RGB camera may be transformed into a computed geometric feature vector prior to classification. The feature vector combines multiple orthogonal feature families, including but not limited to: inter-fingertip contact distances (for example 10 features from all pairwise fingertip combinations), thumb-to-joint distances for relative finger positioning (for example 12 features), per-joint flexion angles measuring curl at each knuckle (for example 15 features), inter-finger spread angles (for example 4 features), palm openness as a scalar (for example 1 feature), and camera-relative palm orientation angles (for example 3 features). Shape features are normalized by palm size for scale invariance and computed relative to the hand's own geometry for rotation invariance, while orientation features preserve camera-relative direction to distinguish poses that differ only in palm facing direction, such as poses as subtle as ASL signs U and H, or P and K.

The resulting feature vector (for example 45 features in one configuration) serves as input to a classifier, such as a multilayer perceptron or other suitable model, trained to map specific hand poses to discrete in-game trigger events, including for example casting a spell, activating an ability, or selecting an action. The classifier is trained entirely in-browser on the user's own device, using captured samples of the user performing each target gesture. Training may be accelerated on the GPU via compute shaders (for example WebGPU), using atomic accumulation techniques such as compare-and-swap loops to emulate float atomic addition for parallel gradient accumulation across all training samples into a single weight-sized buffer. No server, no pre-trained gesture model, no depth sensor, and no specialized hardware are required.

The result is a system in which a player can define, train, and deploy custom gesture triggers within a single browser session, with the trained classifier operating at interactive frame rates from a standard webcam. The combination of in-browser GPU-accelerated training, derived geometric features from orthogonal feature families, and real-time classification into game action triggers represents a novel pipeline for personalizable gesture-driven interaction.

## 16. Real-Time Facial Animation with Geometry-Driven Lip Synchronization

A dedicated blendshape inference model running on a selected subset of face landmarks (for example 146 landmarks) produces a set of blendshape coefficients compatible with a standard blendshape convention (for example 52 ARKit-compatible coefficients) at the tracking frame rate. These coefficients drive morph target deformation on any 3D character mesh rigged with the corresponding blendshape targets, enabling real-time facial puppeting of stylized avatars from webcam input alone.

Two approaches to lip synchronization are supported. In geometry-driven lip sync, mouth blendshape coefficients including jawOpen, mouthClose, mouthFunnel, mouthPucker, mouthSmileLeft/Right, and related coefficients are derived from the physical positions of lip and jaw landmarks as observed by the camera. Mouth animation reflects actual jaw movement rather than audio amplitude. A person mouthing words silently produces accurate lip animation. This is geometrically faithful in a way that audio-amplitude-driven lip sync cannot be.

In audio-corroborated lip sync, geometry-driven mouth coefficients are cross-referenced with real-time audio amplitude from the microphone, obtained for example via getUserMedia audio track processed through an AnalyserNode or any equivalent audio analysis mechanism. When speech is detected but mouth blendshapes show minimal movement the system boosts mouth animation. When mouth movement is detected without audio the system identifies silent gesturing. This dual-signal approach disambiguates speaking from non-speaking mouth movement in ways neither signal alone can achieve.

The combination of geometry-driven facial animation, voice-corroborated lip sync, head-coupled parallax, and hand gesture input running concurrently in a single browser tab from one webcam and one microphone produces a complete embodied player presence. The animated avatar responds to facial expressions, lip movement reflects actual jaw geometry rather than acoustic volume, the scene shifts perspective with head movement, and the hands interact in the same 3D space. Total network payload for the complete player state including blendshapes, head pose, and hand landmarks is for example under 1KB per frame, and at 30fps approximately 22KB/sec, less than the bandwidth of a typical voice call.

The geometry-driven approach is a key differentiator from existing VTubing and avatar animation software, which typically drives jawOpen or equivalent mouth parameters from audio amplitude alone. This system derives multiple distinct mouth blendshape coefficients (for example 12 or more) from real facial geometry, capturing lip shape, jaw position, and mouth configuration independently of whether the user is speaking.

## 17. Integer GPU Compute as Deterministic Multiplayer Simulation Substrate

The game interaction model is not projectile exchange but competing field systems: two players summon extended phenomena, such as a high-pressure fire front meeting an ice storm, that collide and interact at their boundaries. Outcomes are not scripted but emerge from a small integer rule set governing elements such as gravitational attraction, momentum, spin, and material interaction. As with cellular automata such as Conway's Game of Life, where three rules produce gliders and spaceships, a small number of local interaction rules operating on a large grid can generate complex large-scale behavior that neither player explicitly authored. Both players continuously shape the evolution of their systems in real time, making the simulation a co-creative medium rather than a fire-and-forget combat model.

The substrate for this emergent interaction is a parallelized deterministic integer compute simulation running on GPU compute shaders such as WebGPU, serving as the authoritative game state for browser-based peer-to-peer multiplayer. Integer-only arithmetic (including but not limited to u8/u32) guarantees bit-identical output across all hardware. Deterministic systems such as cellular automata are natural fits for this substrate. For example, a 3D CA operating on a voxel grid of up to 128x64x256 cells, each storing 32 bytes of packed integer state, where every active cell reads its 26 neighbors and computes its next state from integer logic alone. No floating point. No rounding ambiguity. No hardware-dependent divergence.

Because the simulation is deterministic, two machines receiving the same inputs produce identical state without exchanging simulation data. Spells and game entities are transmitted as compact recipes of approximately 30 bytes rather than cell-by-cell state. Both machines expand the recipe identically using a shared deterministic PRNG seed. This reduces per-spell network cost by approximately 40x. A complementary two-layer architecture separates the integer simulation layer from a float-precision rendering layer: the integer state is the authoritative truth, synced and deterministic; the float particle rendering is local and diverges freely between machines without affecting game outcome.

Sparse compute dispatch further reduces cost: an active cell list maintains only occupied cells and their neighbor halos, reducing GPU thread dispatch from 2 million to hundreds or thousands for typical sparse scenes. A secondary gravitational field layer at full simulation resolution stores net force vectors per cell, providing long-range spell structure and coherence that local neighbor stencils cannot propagate fast enough to supply.

The determinism of the integer simulation enables GGPO-model rollback netcode: each machine runs speculatively with predicted opponent input, and on mismatch rewinds to the last confirmed state and re-simulates forward. The integer simulation is cheap enough on GPU compute to re-run 3-5 frames in a single tick without dropping below 60fps. No authoritative server is required. The entire multiplayer simulation runs browser-to-browser over WebRTC data channels at approximately 5.9 KB/sec. The specific combination of deterministic integer GPU compute as a simulation substrate, compact recipe-based state sync, and rollback netcode running entirely in a browser represents a novel multiplayer architecture.

---

## License

MIT License. See [LICENSE](LICENSE).
