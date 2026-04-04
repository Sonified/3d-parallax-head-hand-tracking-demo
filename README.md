# Single-Camera Head-Coupled Parallax + Hand Gesture Input for Interactive 3D

A proof-of-concept demonstrating real-time head-coupled 3D parallax and hand gesture recognition from a single consumer webcam, running entirely in-browser. No depth sensor, no plugins, no special hardware.

Move your head to look around a 3D scene. Use your hands to interact with it. One camera, one browser tab.

## Running

Serve the directory over HTTP:

```bash
# Python
python3 -m http.server 8080

# Node
npx serve .
```

Open `http://localhost:8080` in Chrome or another Chromium-based browser. Click "Start Camera" and grant camera permission.

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
                           Main Thread (120fps)
                          /                     \
                Head-Coupled Parallax     Gesture Detection
                (camera.position.set)     (pinch distance)
                          \                     /
                           Three.js Render Loop
```

## Technical Disclosure

This repository includes a [technical disclosure](TECHNICAL-DISCLOSURE.md) documenting 12 novel methods for browser-based computer vision, ML inference, gesture recognition, and interactive 3D. These span work implemented here and in related repositories. The disclosure establishes prior art and is intended as a public record.

## Related: WebGPU Vision

The WebGPU compute shader inference approach is implemented as a standalone open-source library: [webgpu-vision](https://github.com/Sonified/webgpu-vision).

## Requirements

- Modern browser with WebRTC, Web Workers, `createImageBitmap`, and `requestVideoFrameCallback`
- Consumer webcam (built-in laptop camera works)
- No build step, no dependencies to install

## License

MIT License. See [LICENSE](LICENSE).
