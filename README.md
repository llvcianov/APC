# EyeBlink — Driver Drowsiness Detection

Course project for **Architetture dei Processori e dei Calcolatori (APC)**, Master's Degree in Computer Engineering, University of Naples Federico II.

A driver-drowsiness detection system: a PC-side Python script uses a webcam to detect eye closure in real time and sends an alert signal over a serial link to an STM32 microcontroller, which is meant to drive warning LEDs. Presentation: [`Presentazione SleepDetection.pptx`](Presentazione%20SleepDetection.pptx).

## How it works

- **[`PythonScript/APC.py`](PythonScript/APC.py)** — captures webcam frames with OpenCV, detects the face and both eyes (Haar cascade classifiers), crops each eye region and classifies it as open/closed with a small CNN ([`model15.h5`](PythonScript/model15.h5)). If both eyes are detected as closed continuously for 2 seconds, it sends `'A'` (alert) over the serial port to the microcontroller; it sends `'O'` when eyes are confirmed open again, and combines consecutive closed→open readings to flag a "blink" on screen.
- **[`STMeye_blink/`](STMeye_blink/)** — STM32F303 (Discovery board) firmware (STM32CubeIDE project) that listens on UART4 for messages from the PC and is meant to drive onboard LEDs to signal the alert state, with a push-button/UART reset path to acknowledge and clear it.

## Known limitations

This was built and tested as a course project, not hardened for real use:

- The firmware's UART receive handler only reacts to a reset byte (`'N'`); it doesn't currently act on the `'A'`/`'O'` alert messages the Python script sends, so the LED alert logic (which does exist in the main loop) is never actually triggered as wired up. Left as-is here rather than guessing at the intended fix.
- The webcam-based detection depends on a PC for both the camera and the (comparatively heavy) CNN inference, with a wired serial link to the board — a setup good enough to prove the concept, not to ship.

## Ideas for future work

- Use a camera module directly on the STM32 (or another embedded board) instead of relying on a PC as the camera/compute source.
- Replace the CNN with a lighter-weight model that can run the eye-state prediction on-device, moving the computation fully local instead of over a PC+serial link.
- Add steering-wheel touch/grip sensors as a second, independent drowsiness signal alongside eye tracking.
