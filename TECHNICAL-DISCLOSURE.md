# Technical Disclosure

**Author:** Robert Alexander
**Date of publication:** April 3, 2026
**Repository:** https://github.com/Sonified/3d-parallax-head-hand-tracking-demo

This document is a public technical disclosure establishing prior art for the methods described below. It was made publicly accessible via the GitHub repository listed above on the date of publication; the git commit history provides timestamped evidence of publication. Earlier versions of this disclosure are preserved in the repository's commit history, with each commit establishing the disclosure date for the specific techniques described in that revision. Some techniques are implemented in this repository; others are implemented in related private repositories and disclosed here. All methods described are the original work of the author.

This disclosure describes four independent invention families. Each independent claim stands alone without requiring the others. Dependent claims within each family add specificity and narrow the implementation space.

### Prior art context

- **Head-coupled parallax** from a webcam: Johnny Lee (Wii Remote, 2007), headtrackr.js (browser, 2012)
- **Hand gesture recognition** from a webcam: GestureTek (1991+), Leap Motion, Microsoft Kinect, Google MediaPipe (2020+)
- **Browser-based ML inference**: TensorFlow.js, MediaPipe Web, ONNX Runtime Web

---

## Claim I. Embodied Interaction System from a Single RGB Camera

A unified real-time system in which a single consumer camera, including but not limited to a built-in webcam, simultaneously drives head-coupled visual parallax, bilateral hand tracking with derived depth, world-locked spatial audio, and GPU-accelerated ML inference (for example via WebGPU compute shaders), all running concurrently in an unmodified browser tab or comparable client-side runtime on commodity hardware. Conventional six-degrees-of-freedom (6DOF) VR requires either a headset with onboard tracking cameras, an external depth sensor, or a multi-camera rig. This system synthesizes equivalent interaction from signals already present in a single RGB stream, including but not limited to a consumer webcam. No prior system is known to combine these elements in this configuration as of the date of this disclosure.

The head-coupled parallax pipeline provides three translational and three rotational degrees of freedom from face landmarks or other facial feature detection methods. Adding depth-estimated hand position extends this into full-body interactive space. A user can, for example, lean left to peer around a virtual object, reach toward the screen and feel their hand move into the scene, and pull back to bring it forward again. The physical metaphor is reaching through a window, not wearing a headset. This interaction model is fully implemented and demonstrated in a related private repository as of the date of this disclosure.

GPU-accelerated inference (for example via WebGPU) at interactive frame rates (for example 120fps or higher), head-coupled parallax, bilateral hand tracking, and fused monocular depth estimation running concurrently in a browser tab or comparable client-side runtime produces a first-person interactive 3D experience requiring no hardware beyond the camera built into any modern laptop or similar consumer device.

### I.A. Head-Coupled Visual Parallax with Concurrent Hand Gesture Input

A single RGB camera feed (for example via `getUserMedia` or another video capture API) is shared between two or more concurrent ML inference pipelines running in separate execution contexts, such as Web Workers, threads, or processes. Face detection extracts head position from facial keypoints, including but not limited to eye landmarks (for example, midpoint for x/y, inter-eye distance for z depth proxy). Hand landmark detection extracts 3D landmarks (for example 21 per hand per frame) for gesture recognition. Inference contexts may receive video frames via zero-copy transfer mechanisms such as `ImageBitmap` via `postMessage`, shared memory, or other efficient frame-sharing approaches. All ML inference runs off the main rendering thread, preserving smooth interactive rendering at rates including 120fps or higher.

The 3D scene (rendered using any suitable 3D engine, such as Three.js, WebGL, or WebGPU) applies head position as camera translation, creating the illusion of looking through a window into 3D space. Forward and backward head movement, derived from facial feature geometry such as inter-eye distance, maps to camera Z translation in the 3D scene. The viewer physically leans in to move deeper into the space, and leans back to retreat. This produces a direct physical metaphor for scene traversal requiring no controller input. Hand gestures simultaneously trigger interactive events.

The specific combination of simultaneous head-coupled parallax rendering and hand gesture interactive input from a single consumer RGB camera, running entirely in a client-side runtime such as a browser without plugins or depth sensors, with concurrent off-thread ML inference sharing one video feed, is a novel system architecture as of the date of this disclosure.

### I.B. Depth-Corrected Hand Projection for Desktop VR Interactions

Hand landmark models, including but not limited to MediaPipe, produce per-landmark z-values inferred from hand scale and proportions. By smoothing these z-values (for example via a One Euro filter or other adaptive low-pass filter) and mapping them into the head-coupled parallax scene with an inverse projection correction, a hand physically moving toward the camera may be rendered as moving into the 3D scene rather than growing larger on a flat screen. This counteracts the natural 2D projection (where closer objects appear larger) and produces spatially coherent hand movement within the parallax space. For example, a punch toward the webcam reads as a punch into the screen.

The depth mapping may use smoothed absolute z-position, relative z-velocity (z-delta), or a combination of both, depending on the interaction type. For example, smoothed position may provide stable continuous placement for aiming and spatial interaction, while z-velocity derivatives may be used for momentum-dependent interactions such as throwing or striking. This enables desktop VR style interactions, including for example boxing, tennis, or other gesture-driven spatial interactions, from a single consumer webcam, without a depth sensor or headset.

### I.C. Parallax-Coupled Hand Gesture Coordinate System

Hand landmarks are mapped to 3D scene space relative to the current parallax camera position. The hand "rides with" the head-coupled perspective shift. Most systems treat hand position and head tracking as independent coordinate systems. Coupling them makes the hand feel like it exists inside the parallax window rather than floating in front of it. This is central to producing coherent first-person interaction in a head-coupled parallax scene. Applying the same smoothing filter (for example a One Euro filter with matched parameters) to both the hand tracking and head tracking signals may preserve temporal coherence between the two coordinate systems, ensuring that smoothing-induced latency affects both signals equally and the coupled mapping remains aligned.

### I.D. Stable Anchor Cascade for Continuous Z Estimation

The landmark-spread depth signal may degrade when the hand partially exits the frame or landmarks are occluded. A stability-aware selection mechanism, such as a visibility-weighted cascade, selects the most geometrically stable anchor point at each frame. On anchor transitions, the system applies a computed offset or other continuity-preserving correction to maintain Z continuity. The effect is that depth tracking remains locked even as the hand moves to the edges of the camera's view. In aiming applications, for example, when distal landmarks such as fingertip positions drop below a confidence threshold, the system may fall back to more proximal landmarks such as the wrist or palm base while preserving the last known depth estimate, maintaining continuous aim ray stability through high-uncertainty poses.

### I.E. Head-Coupled Aim Ray via Dual-Tracked Regression

In a head-coupled parallax scene, the apparent direction of a pointed finger changes as the viewer's head moves. Leaning right shifts the viewing angle, and a finger pointed at a fixed screen location now corresponds to a different point in 3D scene space. This system derives a continuous world-space aim ray from the geometric relationship between tracked head position and tracked fingertip position, such that the aim ray updates in real time as both head and hand move. The effect is analogous to physically looking down the barrel of a gun: the viewer leans to align their perspective, and the system tracks where they are actually aiming in the 3D scene, not merely where their finger points on the flat screen.

Calibration is performed by displaying a grid of target points across the screen (for example a 5x4 grid spanning 5% to 95% of both axes) and having the user point at each target and perform a capture gesture such as a pinch. Each sample records the known screen coordinate as ground truth alongside the smoothed fingertip position and head position from the face tracking pipeline. The grid cycles indefinitely, allowing additional passes at different head positions to improve robustness across viewing angles. Samples indicating lost hand tracking are discarded before fitting.

From the collected samples, one or more regression models or other learned mappings from pointer and head position to screen coordinates are fit in-browser (for example, two independent regressions, one for each screen axis), taking effect immediately with no page reload. Multiple model variants may be supported, from full models incorporating depth terms to simplified models using only 2D pointer and head position.

The regression output passes through a cascade of smoothing filters with tunable parameters, suppressing jitter on slow movements while preserving fast intentional aim changes.

The calibration mechanic uses the same gesture and tracking pipeline that drives all other system interactions. No additional hardware, no separate calibration device, no page reload. The system calibrates itself using its own input modality, and the resulting aim ray is continuously updated from both head and hand position, producing a world-space interaction ray that responds to physical viewing angle the way a real aimed instrument would.

### I.F. Fused Monocular Depth from Orthogonal Cues

In a system already tracking both head position and hand position from a single camera for parallax and gesture input, the geometric relationship between these two tracked points provides a second depth cue at zero additional sensing cost. As the user's head shifts, the angular relationship between head and hand in camera space changes as a function of true 3D distance, encoding geometric depth independent of the landmark-spread signal. Fusing both signals, for example using confidence weighting, may produce depth estimates that are robust when either signal is noisy or degraded. The novelty is not multi-cue depth fusion itself, but that the system's existing dual-tracking architecture produces orthogonal depth cues as a byproduct of its primary functions, requiring no additional sensor, model, or pipeline stage. More generally, any technique that combines two or more orthogonal monocular depth cues already present in the system, including but not limited to landmark spread, face-relative angular geometry, apparent size, or other camera-derived signals, to produce a fused depth estimate falls within this approach.

### I.G. Real-Time Facial Animation with Geometry-Driven Lip Synchronization

A dedicated blendshape inference model running on a selected subset of face landmarks (for example 146 landmarks) produces a set of blendshape coefficients compatible with a standard blendshape convention (for example 52 ARKit-compatible coefficients) at the tracking frame rate. These coefficients drive morph target deformation on any 3D character mesh rigged with the corresponding blendshape targets, enabling real-time facial puppeting of stylized avatars from webcam input alone. The blendshape inference worker runs fire-and-forget with one frame of latency, adding no fps overhead to the tracking pipeline.

Two approaches to lip synchronization are supported. In geometry-driven lip sync, mouth blendshape coefficients including jawOpen, mouthClose, mouthFunnel, mouthPucker, mouthSmileLeft/Right, and related coefficients are derived from the physical positions of lip and jaw landmarks as observed by the camera. Mouth animation reflects actual jaw movement rather than audio amplitude. A person mouthing words silently produces accurate lip animation. This is geometrically faithful in a way that audio-amplitude-driven lip sync cannot be.

In audio-corroborated lip sync, geometry-driven mouth coefficients are cross-referenced with real-time audio amplitude from the microphone, obtained for example via getUserMedia audio track processed through an AnalyserNode or any equivalent audio analysis mechanism. When speech is detected but mouth blendshapes show minimal movement the system boosts mouth animation. When mouth movement is detected without audio the system identifies silent gesturing. This dual-signal approach disambiguates speaking from non-speaking mouth movement in ways neither signal alone can achieve.

The geometry-driven approach is a key differentiator from existing VTubing and avatar animation software, which typically drives jawOpen or equivalent mouth parameters from audio amplitude alone. This system derives multiple distinct mouth blendshape coefficients (for example 12 or more) from real facial geometry, capturing lip shape, jaw position, and mouth configuration independently of whether the user is speaking.

### I.H. Compact Networked Player State for Browser-Based Facial Presence

Browser-based multiplayer games typically lack facial presence entirely. Players are represented by usernames, static avatars, or at most voice chat. Real-time facial animation of the kind seen in VR social applications or professional motion capture has not been available in browser-based interactive contexts, in part because it has historically required dedicated hardware, specialized software, or bandwidth-intensive video streams.

In the disclosed system, the face landmark pipeline already produces blendshape coefficients as part of its tracking architecture for head-coupled parallax and geometry-driven lip sync (I.G). Transmitting these coefficients to a remote peer is a zero-cost addition: the data already exists, and the complete player state including blendshapes, head pose, and hand landmarks can be as compact as for example under 1KB per frame. At 30fps this is approximately 22KB/sec over a real-time transport channel such as a WebRTC data channel, WebSocket, or other low-latency protocol. For comparison, a voice call uses more bandwidth. The result is that full avatar facial presence, traditionally reserved for VR or studio environments, becomes a byproduct of the existing tracking pipeline rather than an additional system.

### I.I. Mobile Device as 6DOF Interactive Platform

The GPU-accelerated inference pipeline, gesture classification system, and deterministic simulation architecture described in this document are not limited to desktop or laptop environments. Mobile devices with front-facing cameras and GPU compute capability (for example via WebGPU, Metal, or other mobile GPU APIs) may serve as equivalent platforms for the entire system. The front-facing camera of a mobile device provides the same single RGB input that drives head-coupled parallax, face tracking, and hand landmark detection on desktop.

When the device is held in one hand, the user's free hand is available for single-hand gesture input, including the gesture classification and confidence-driven gameplay mechanics described in Claim III. The device screen serves as the parallax window, with head-coupled perspective shift driven by the front-facing camera's view of the user's face, and the free hand interacting in the 3D scene via the same landmark detection and feature classification pipeline.

When the device is placed on a stand, tripod, or other stable surface, both of the user's hands are freed for bilateral gesture input, enabling the full two-hand interaction model including dual-hand spell casting, blocking, and other gestures that require simultaneous use of both hands. The transition between one-hand and two-hand interaction modes may be automatic, driven by the hand detection pipeline's count of visible hands.

Multiple devices operating in a shared physical space may enable co-located multiplayer configurations. For example, two players facing each other across a table, each with a device on a stand, can engage in head-to-head gameplay where each device tracks its respective player's face and hands while running the deterministic simulation described in Claim IV. The peer-to-peer sync architecture requires only a low-bandwidth data channel between devices, which may operate over local network, Bluetooth, or any available transport.

The rear-facing camera of a mobile device may additionally serve as an AR viewport: the camera feed captures the physical environment while the system composites game content, such as spell effects, particle systems, or other interactive elements, over the real-world view. Combined with head-coupled parallax from the front-facing camera (or device orientation sensors), the rendered content may be spatially registered to the physical space, producing an augmented reality experience from a standard mobile device without requiring dedicated AR hardware, AR frameworks, or platform-specific AR APIs. The same GPU compute pipeline that drives gesture recognition and deterministic simulation renders the composited AR output.

The result is that the complete system, including head tracking, hand gesture classification, on-device ML training, deterministic multiplayer simulation, and AR compositing, may run on a mobile device in a browser tab or comparable client-side runtime, extending the desktop architecture to mobile with no fundamental change to the pipeline.

*The following spatial audio techniques (I.J through I.L) extend the embodied interaction system into the auditory domain. By deriving audio listener position from the same face-tracking pipeline that drives visual parallax, the system produces correlated audiovisual responses to physical movement that deepen the illusion of spatial presence without requiring any additional sensing hardware or input.*

### I.J. Head-Tracked Spatial Audio

The same face-tracking data that drives head-coupled visual parallax simultaneously drives a spatial audio listener position, for example via the Web Audio API AudioListener or any equivalent spatial audio system. Each frame, the listener coordinates are set from the parallax camera position, which is itself computed from webcam-tracked facial features such as eye midpoint and inter-eye distance. When the user physically leans left, both the visual perspective and the audio perspective shift together: audio sources pan compensatorily rightward, remaining world-locked in the 3D scene rather than fixed to the listener's head. This is a single face-tracking pipeline producing two output modalities (visual parallax and spatial audio) in real time, coupling two systems that are normally independent.

### I.K. Per-Source Doppler Shift via Velocity Projection

Web Audio API's built-in dopplerFactor was deprecated and removed from all major browsers. This system reimplements Doppler from first principles: each frame, the sound source's velocity vector is projected onto the normalized source-to-listener unit vector to obtain radial velocity, then a Doppler frequency scaling formula is applied to the source frequency each frame. This approach applies to any sound source type, including but not limited to oscillators, sampled audio, and synthesized signals. The effective speed of sound is user-tunable, allowing Doppler intensity to range from imperceptible to extreme.

The Doppler ratio may be applied independently to two or more parallel signal paths, for example the primary oscillator frequency and a bandpass noise filter layer. Decoupling these paths allows spectral timbre to shift at a different rate than pitch, producing perceptual realism that uniform scaling cannot achieve. A "drop only" mode clamps the ratio to at most 1.0, producing pitch and timbre drops on recession without corresponding rises on approach, a cinematic rather than physically accurate effect.

Combined with head-tracked listener position, the result is that a projectile passing the listener's head produces correlated changes across four or more perceptual dimensions simultaneously, including visual position, binaural pan, pitch, and timbre.

### I.L. Proximity-Driven Spectral Unmasking for Perceptual Mass

As a sound source approaches the listener, a frequency-dependent filter, such as a high-pass filter, applied to the source signal is progressively opened: for example, the cutoff frequency decreases inversely with distance. At range, only high frequencies are present, giving the object a thin, distant quality. At close range, low frequencies are fully present, giving the object physical weight and presence. This models the perceptual reality that proximity reveals bass content that distance masks, and produces the sensation that an approaching object is gaining mass rather than merely gaining volume. The effect is implemented per source in the audio processing graph (for example via Web Audio API or any equivalent audio engine) and updated each frame from the 3D distance between source and listener position.

Combined with Doppler shift and head-tracked panning, these three techniques form a unified spatial audio system in which a single moving sound source produces correlated changes across visual position, binaural pan, pitch, timbre, and spectral mass simultaneously, all derived from the same 3D scene state and face-tracking pipeline.

---

## Claim II. Zero-Readback GPU-Accelerated ML Pipeline for Monocular 3D Interaction

Real-time vision-driven interaction systems, including but not limited to head-coupled parallax and gesture recognition, depend on maintaining inference latency below the threshold of perceptual coherence. When tracking latency exceeds this threshold, the coupling between physical movement and visual response breaks down, and the illusion of spatial presence collapses. Achieving sub-threshold latency in a client-side runtime such as a browser is most reliably accomplished through a complete pipeline in which ML inference, inter-stage preprocessing, and post-processing remain GPU-resident, with minimal data crossing the GPU-CPU boundary.

This disclosure describes such a pipeline: a system for deploying multi-stage ML vision models to GPU compute in a client-side runtime, encompassing model extraction from sealed upstream frameworks, conversion to a portable format (for example ONNX), execution via GPU compute shaders (for example WebGPU) in parallel off-thread execution contexts (for example Web Workers), GPU-resident preprocessing between detection stages, and minimized GPU-CPU data transfer limited to final inference outputs. Benchmarked against the leading sealed framework on identical hardware and workloads, the complete pipeline demonstrates approximately 2.6x throughput improvement and 68% latency reduction when concurrently tracking two hands and one face (see II.A for detailed conditions). The architectural elimination of inter-stage CPU readback is the primary driver of this improvement.

The pipeline is implemented as a standalone open-source library ([webgpu-vision](https://github.com/Sonified/webgpu-vision)) and applies to any multi-stage ML vision task deployable to GPU compute in a client-side runtime, including but not limited to hand tracking, face tracking, pose estimation, object detection, or other real-time vision applications.

### II.A. Elimination of Synchronous GPU-CPU Readback in Multi-Stage Vision Pipelines

Prior browser-based ML vision frameworks, including sealed WASM-based inference binaries that advertise GPU acceleration, retain synchronous CPU readback layers between pipeline stages that cannot be bypassed or modified by developers. Specifically, WebGL-based inference pipelines must transfer tensor data from GPU to CPU between stages via synchronous calls such as WebGLRenderingContext.readPixels(), which blocks the calling thread until all pending GPU commands complete and pixel data crosses the GPU-CPU bus. In a two-model cascade such as palm detection followed by hand landmark inference, this architecture requires multiple such stalls per frame. These stalls serialize unavoidably because WebGL contexts are single-threaded.

Benchmarked on identical hardware (MacBook Pro M1 Max, Chrome 146, 640x480 camera), the sealed MediaPipe implementation averages approximately 27fps (39.7ms per frame) when simultaneously tracking two hands and one face. The same workload on the disclosed WebGPU architecture averages approximately 70fps (12.6ms per frame), a 2.6x throughput improvement and 68% latency reduction, attributable to the elimination of synchronous GPU-CPU readbacks between pipeline stages.

This disclosure describes a pipeline in which GPU buffer objects written by one stage are passed directly to the next via zero-copy references, for example via Tensor.fromGpuBuffer(), without returning to CPU. The only CPU readback in the complete pipeline is the final landmark output. For example, 252 bytes per hand and 5.7KB per face cross the GPU-CPU boundary per frame.

### II.B. Op Decomposition for GPU Runtime Compatibility

When a GPU-based ML runtime lacks a native kernel for a given operation, the runtime falls back to CPU execution, pulling data off the GPU, computing on the CPU, and pushing it back. This disclosure describes a pre-deployment graph transformation that decomposes unsupported operations into compositions of GPU-native ops using equivalent mathematical identities, such that the runtime never encounters the unsupported kernel. The result is zero CPU-GPU roundtrips, zero accuracy loss, and full GPU inference speed recovered.

This technique applies to any neural network model containing ops unsupported by a target runtime, including but not limited to ONNX models on WebGPU, and is not limited to any single operation or model type. Any unsupported op that can be expressed as a mathematically equivalent composition of supported primitives may be decomposed in this manner. For browser-based ML and other environments where runtime op coverage lags behind native frameworks, this is a practical path to deploying models that would otherwise be GPU-unusable, keeping the entire inference pipeline on the GPU.

### II.C. PReLU Decomposition for WebGPU Execution

As a specific application of II.B, a neural network model may contain multiple instances of an unsupported activation function, each of which independently triggers a GPU-to-CPU fallback. For example, in one embodiment, a widely deployed face landmark model contains 69 PReLU layers, each triggering a CPU fallback when executed via a WebGPU-based inference runtime, reducing throughput to approximately 9fps (110ms per frame) despite all other operators executing on GPU. Decomposing each instance of the unsupported operation into a composition of GPU-native ops using the method of II.B eliminates all such fallbacks, recovering full GPU inference speed. The source model may originate from any upstream framework (for example extracted from a sealed task bundle and converted from TFLite to ONNX via format conversion tools such as tf2onnx), and the decomposition may be applied to any activation function or other operation type that lacks native GPU kernel support in the target runtime.

### II.D. GPU-Side Preprocessing Between Detection Stages

Standard browser vision pipelines perform preprocessing steps such as letterbox padding and affine warping by routing image data through CPU-accessible surfaces such as Canvas between detection stages. This produces a CPU-GPU-CPU roundtrip that typically dominates preprocessing latency in multi-stage pipelines, regardless of how fast the inference itself runs.

In the disclosed pipeline, these preprocessing steps may be performed entirely via GPU compute shaders or equivalent GPU-side operations, keeping image data GPU-resident between stages such as palm detection and landmark inference. No CPU readback occurs between stages. The preprocessed tensor may be passed directly to the next inference stage via zero-copy GPU buffer reference or equivalent mechanism, consistent with the pipeline architecture described in II.A.

### II.E. Weighted Non-Maximum Suppression

Overlapping detections may be combined using a weighted averaging approach, for example averaged by confidence score, rather than simply keeping the highest-scoring box. This produces smoother bounding boxes, especially at frame edges where detection confidence drops off. The weighted average preserves spatial information from multiple overlapping proposals rather than discarding all but one.

---

## Claim III. In-Browser GPU-Accelerated Gesture Model Training and Real-Time Deployment

A system for defining, training, and deploying hand gesture recognition models entirely within a client-side runtime such as a browser, with no server dependency for any stage of the training or inference pipeline. The complete training pipeline — feature extraction, forward pass, loss computation, gradient accumulation, and weight update — executes on the client GPU via compute shaders. The trained model is available for real-time inference within the same session at interactive frame rates. No data leaves the client device during training or inference unless explicitly transmitted by the application.

### III.A. Derived Geometric Feature Families

Raw hand landmark coordinates from a single RGB camera vary with hand size, camera distance, hand position within the frame, and individual anatomy, making them unsuitable as direct classifier input without normalization. Transforming raw coordinates into derived geometric features produces a representation that is stable across these sources of variation, enabling a classifier trained on one user's hands to generalize across sessions, distances, and camera positions.

Hand landmark coordinates may be transformed into a computed geometric feature vector combining multiple orthogonal feature families, including but not limited to: inter-fingertip contact distances (for example 10 features from all pairwise fingertip combinations), thumb-to-joint distances for relative finger positioning (for example 12 features), per-joint flexion angles measuring curl at each knuckle (for example 15 features), inter-finger spread angles (for example 4 features), palm openness as a scalar (for example 1 feature), and camera-relative palm orientation angles (for example 3 features). Shape features are normalized by palm size for scale invariance and computed relative to the hand's own geometry for rotation invariance, while orientation features preserve camera-relative direction to distinguish poses that differ only in palm facing direction, such as poses as subtle as ASL signs U and H, or P and K.
The resulting feature vector (for example 45 features in one configuration) serves as input to a classifier, such as a multilayer perceptron or other suitable model, trained to map specific hand poses to discrete trigger events, including for example casting a spell, activating an ability, or selecting an action. 

### III.B. Atomic Float Gradient Accumulation for On-Device GPU Training

GPU-based gesture training may use an atomic accumulation technique to accumulate gradients from all training samples in parallel into a single weight-sized buffer. Specifically, WGSL provides atomic operations only on 32-bit unsigned integers. Float gradient accumulation is achieved by reinterpreting float values as unsigned integers via bitcast, performing an atomic compare-and-swap loop (atomicCompareExchangeWeak), and bitcasting back. This enables all training samples to accumulate gradients into a single shared weight buffer in parallel, without per-sample gradient storage.

Standard GPU training allocates per-sample gradient arrays and then reduces them in a second pass. This approach requires memory proportional to the number of weights only (for example 111KB for a 27,776-weight classifier), rather than proportional to the number of training samples multiplied by the number of weights (for example 1.3GB for 13,000 training samples under full-batch gradient descent, or 27MB under mini-batch). This represents a memory reduction of over four orders of magnitude for typical gesture training workloads, making real-time on-device gesture model training practical in a browser tab or comparable client-side runtime.

### III.C. ML Recognition Confidence as Continuous Visible Gameplay Variable

In gesture-driven interactive systems, the recognition confidence score produced by an ML model or other classification system may be exposed as a continuous, real-time visible gameplay variable rather than consumed silently as a binary accept/reject threshold. In one implementation, gesture recognition confidence drives in-game quantities such as spell intensity, shield strength, or ability power, giving the player direct real-time feedback on physical input quality and creating a closed-loop skill acquisition system driven by the model's output.

This approach may be distinguished from binary gesture acceptance, where confidence is consumed internally and the player sees only a recognized or rejected outcome, and from post-hoc scoring as in rhythm games, where input quality is evaluated after the fact. The confidence signal may instead be made continuous, visible, and actionable during the input itself.

In traditional game design, spell failure or degraded ability outcomes are typically governed by random number generation: dice rolls, percentage chances, or pseudorandom draws that the player cannot directly influence through physical skill. In this system, ML model confidence may replace random number generation as the governing variable for outcome variance. A spell fizzles not because a random number fell below a threshold, but because the model's confidence in the detected gesture was low, which in turn reflects the physical clarity of the player's hand pose, lighting conditions, occlusion, or distance from the camera. Unlike a dice roll, this source of variance is learnable: a player may practice gesture form, adjust hand position, or improve lighting to increase model confidence, converting what would traditionally be opaque randomness into a trainable physical skill. Model limitations such as landmark dropout at frame edges, reduced confidence for occluded fingers, or sensitivity to hand orientation may function as the equivalent of environmental gameplay factors that a skilled player learns to manage. The limitations of the ML model become the physics of the game world.

This principle may extend to input vocabulary design: core mechanics may be intentionally mapped to input poses or patterns that maximize model confidence, co-designing the interaction vocabulary with the model's confidence topology such that model strengths become gameplay advantages and model limitations become legible skill feedback rather than invisible failures. This approach applies to any recognition modality, including but not limited to hand pose, body pose, facial expression, or voice command recognition systems.

In a language acquisition context, for example American Sign Language, the same continuous recognition confidence signal that governs gameplay outcomes may be exposed as a visual or auditory feedback channel, providing a learner with real-time indication of how closely their hand pose matches a target sign, enabling self-directed skill acquisition without instructor feedback. The underlying ML model becomes a mirror: the learner continuously adjusts their form in response to a continuously updating signal until the model's confidence reflects correct execution, whether the target behavior is a game mechanic or a handshape in a visual language.

---

## Claim IV. Deterministic Integer GPU Compute as Serverless Peer-to-Peer Multiplayer Substrate

A parallelized deterministic integer compute simulation running on GPU compute shaders (for example WebGPU, or any equivalent GPU compute API), serving as the authoritative game state for peer-to-peer multiplayer in a client-side runtime such as a browser. Integer-only arithmetic (including but not limited to u8, u16, u32, or other fixed-width integer types) guarantees bit-identical output across all hardware. No floating point. No rounding ambiguity. No hardware-dependent divergence. No authoritative server is required.

Two independent machines may each simulate a complete emergent physics world and remain bit-identical across arbitrarily many cell updates, synchronized entirely through compact input recipes rather than state transmission, enabling serverless peer-to-peer multiplayer of emergent physics simulations in a client-side runtime. The specific combination of deterministic integer GPU compute as a simulation substrate, compact recipe-based state sync, and rollback netcode running entirely in a client-side runtime represents a novel multiplayer architecture.

Multiplayer simulation requiring bit-identical state across all participating machines cannot tolerate floating-point arithmetic, which produces hardware-dependent rounding differences that compound across millions of cell updates and produce divergent game states within seconds. Integer-only arithmetic is therefore not a design preference but an architectural requirement for serverless deterministic multiplayer at scale.

Deterministic systems such as cellular automata are natural fits for this substrate. For example, a 3D cellular automaton operating on a voxel grid (for example up to 128x64x256 cells or other grid dimensions), each cell storing packed integer state (for example 32 bytes), where every active cell reads its neighbors (for example 26 in a Moore neighborhood, or 6 in a von Neumann neighborhood, or other stencil configurations) and computes its next state from integer logic alone.

### Prior art context

Per-cell physics simulation as a game world architecture: Noita (Nolla Games, 2019), Sandspiel (2018), Powder Game (2008), and the broader falling sand game genre.

### IV.A. Recipe-Based State Sync

Because the simulation is deterministic, two or more machines receiving the same inputs produce identical state without exchanging simulation data. Game entities such as spells or other interactive objects are transmitted as compact recipes (for example approximately 30 bytes) rather than cell-by-cell state. All machines expand the recipe identically using a shared deterministic PRNG seed or equivalent deterministic expansion method. The expansion relies on integer-only pseudorandom number generation, such as xorshift, which produces bit-identical sequences from identical seeds on all hardware architectures, requiring no floating-point operations and no hardware-specific numerical behavior. This can reduce per-entity network cost by an order of magnitude or more (for example approximately 40x in one configuration). The entire multiplayer simulation may run peer-to-peer over low-latency transport channels such as WebRTC data channels, WebSocket, or other real-time protocols, at bandwidths on the order of kilobytes per second (for example approximately 5.9 KB/sec in one configuration).

### IV.B. Two-Layer Simulation and Rendering Architecture

A complementary two-layer architecture separates the integer simulation layer from a rendering layer that may use float-precision or other visual representations: the integer state is the authoritative truth, synced and deterministic; the rendering is local and may diverge freely between machines without affecting game outcome.

### IV.C. Gravitational Structure Field as Entity Coherence Skeleton

One or more additional compute layers at simulation resolution may each store aggregate quantities per cell, such as net force vectors (for example force X, force Y, force Z, and strength). Each such layer may operate alongside but independently from the primary cellular automaton or other integer simulation grid. When a game entity such as a spell is instantiated, the primary grid may receive the expanded particle mass (element counts, momentum), while one or more field layers may receive a core attractor at the entity's center with configurable strength and angular velocity. The particle mass has no intrinsic knowledge of its membership in an entity. It is integer state with forward momentum. The field core may pull the mass into formation. Shape, rotation, and coherence may emerge from the interaction between the layers rather than being encoded per-particle or per-entity.

As the entity travels through the simulation volume, the field core may travel with it, maintaining rotational structure. When the entity collides with opposing elements, the primary simulation resolves element interactions and mass is consumed. The field core may weaken as its mass depletes. The entity loses coherence and its particles scatter. Entity death is a field structure losing the mass that gave it meaning, not a hit-point counter reaching zero.

Multiple entities may create overlapping field influences that sum across the layer. The simulation reads the net result and each element may respond according to its mass property from a global element table.

In contrast to traditional game architectures where entities are explicitly instantiated objects with properties such as health points, position, and lifetime managed by game logic, in this system no per-entity object or identifier exists. Entity identity is defined by the presence of a field core. Entity coherence is maintained by the field's pull on surrounding mass. Entity lifecycle terminates when the field core loses sufficient mass to maintain structure. The field layer is therefore not an auxiliary force system but the mechanism by which entities exist, cohere, and die within the simulation.

### IV.D. Sparse Compute Dispatch

An active cell list or equivalent sparse data structure maintains only occupied cells and their neighbor halos, reducing GPU thread dispatch from the full grid volume to only the active region (for example dispatching hundreds of threads for a localized entity instead of millions for the full grid). Each tick, the GPU writes back which cells are newly active and which went inactive, maintaining the list frame to frame. A complementary hierarchical approach may divide the grid into chunks with per-chunk active flags, dispatching compute only on active chunks.

### IV.E. Rollback Netcode on GPU Compute

The determinism of the integer simulation enables rollback-based netcode models such as GGPO: each machine runs speculatively with predicted opponent input, and on mismatch rewinds to the last confirmed state and re-simulates forward. The integer simulation is efficient enough on GPU compute to re-run multiple frames (for example 3-5 frames) in a single tick without dropping below interactive frame rates.

---

The source code in this repository is released under the MIT License. This document is a public technical disclosure establishing prior art; it is not a license grant for any patent claims.