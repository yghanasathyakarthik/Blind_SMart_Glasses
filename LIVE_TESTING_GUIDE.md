# Smart Glasses Assistive Vision System - Real-World Live Testing Guide (v2.0)

## 1. Overview
The **Smart Glasses Live HUD** (`smart_glasses_live_hud.py`) is an interactive, real-time computer vision application that connects directly to your computer webcam or smartphone camera. It integrates all **8 research evaluation modules** into an assistive vision display with intelligent **priority-based walking guidance**, **high-accuracy text reading (OCR)**, **360-degree scene storytelling**, and **non-blocking text-to-speech (TTS)** voice feedback.

---

## 2. Quick Start

### Method A: One-Click Launcher
Double-click `run_live_hud.bat` inside `D:\Blind_SMart_Glasses\`.

### Method B: Terminal / PowerShell
Open your terminal, navigate to the directory, and run:
```powershell
cd D:\Blind_SMart_Glasses
python smart_glasses_live_hud.py
```

### Method C: Using your Phone Camera (IP Webcam / DroidCam)
To test as wearable smart glasses using your smartphone camera:
1. Install **DroidCam** or **IP Webcam** (free from Google Play Store or iOS App Store).
2. Connect your phone and PC to the same Wi-Fi network.
3. Start the app on your phone to get the video stream URL (e.g., `http://192.168.1.5:8080/video` or `http://192.168.1.5:4747/video`).
4. Launch with:
```powershell
python smart_glasses_live_hud.py --camera "http://192.168.1.5:8080/video"
```

---

## 3. Intelligent Priority Walking Guidance ("Pass & Announce Next")
When a visually impaired person walks through an environment:
- **Tabletop Clutter Suppression**: Non-critical small items (`cups`, `bottles`, `pens`, `phones`, `cutlery`) are filtered out so they do not produce audio clutter.
- **Immediate Path Obstacle Lock**: Identifies the nearest actionable obstacle or person in the direct walking corridor (e.g., *"Chair ahead, about 2 meters, center"*).
- **Sequential Obstacle Progression**:
  1. The system locks onto the active target obstacle and displays a cyan target indicator.
  2. While approaching, it remains silent to prevent distracting audio spam.
  3. The moment the user maneuvers past the obstacle, the system announces: *"Chair passed. Path clear ahead."*
  4. It immediately scans for the **next closest obstacle ahead in sequence** (e.g., *"Next: Person standing 3 meters ahead"*).

---

## 4. High-Accuracy Text Extraction (OCR)
- **CLAHE Adaptive Contrast Enhancement**: Normalizes lighting variations, washed-out webcam frames, and glare.
- **Bilateral Filtering & Unsharp Mask**: Denoises sensor grain while sharpening individual character strokes.
- **1.4x Super-Resolution Upscaling**: Detects small text on medicine bottles, doors, books, and computer screens.
- **Artifact Cleaning & Line Reconstruction**: Discards stray symbols (`/`, `|`, `.`) and groups words geometrically into grammatically natural sentences.

---

## 5. Comprehensive 360-Degree Scene Storytelling
Pressing `SPACE` triggers a multi-modal synthesized narrative that comprehensively describes everything the camera sees:
1. **Setting / Environment**: Informs whether the user is in an indoor office, living room, corridor, or outdoor street (Places365).
2. **Visual Narrative**: Describes the core visual scene (Salesforce BLIP).
3. **Spatial Distribution**: Identifies key items to the left, center, and right.
4. **Floor Walking Condition**: Confirms whether the footstep corridor is open or obstructed.
5. **Signage / Text**: Reads any prominent signboards in the view.
6. **Forward Spatial Extent**: Informs open space clearance in meters (MiDaS).

---

## 6. Interactive Controls & Hotkeys

| Key | Mode / Action | Description |
|---|---|---|
| **`0` or `A`** | **All-in-One Assistive HUD** | **Split-Screen Display**: RGB detection & hazard corridor on left, MiDaS thermal depth heatmap on right, place recognition top banner, priority target badge, and 360 storytelling bottom card. |
| **`1`** | **Module 1: Priority Object Detection (COCO)** | Navigational obstacle tracking with sequential "pass and announce next" state machine. |
| **`2`** | **Module 2: Outdoor Navigation (BDD100K)** | Filters traffic actors (`vehicles`, `pedestrians`, `bicycles`, `traffic lights`). Evaluates pedestrian crosswalk safety and traffic signal state (`RED STOP` vs `GREEN WALK`). |
| **`3`** | **Module 3: Obstacle & Hazard Detection** | Monitors ground walking corridor (bottom 45% of frame). Outlines floor tripping hazards (bags, dropped items, shoes, steps) in glowing red with immediate voice alerts. |
| **`4`** | **Module 4: Place Recognition (Places365)** | Scene classification across 365 categories. Informs room transitions (`office`, `kitchen`, `street`) only when the environment actually changes. |
| **`5`** | **Module 5: 360 Scene Storytelling (VizWiz)** | Full conversational scene narration describing all visual details. |
| **`6`** | **Module 6: High-Accuracy Text Reading (OCR)** | Preprocessed EasyOCR text reader. Auto-scans every 2.5s in Mode 6 or on-demand via `T`. |
| **`7`** | **Module 7: GPS Wayfinding (OpenStreetMap)** | Visual compass rose with nearest Points of Interest (`Pharmacy`, `Bus Stop`, `Hospital`, `Crosswalk`) and step-by-step distance/bearing cues. |
| **`8`** | **Module 8: Depth & Distance (KITTI / MiDaS)** | Monocular depth estimation with colorized Inferno heatmap. Flashes an emergency red collision alert if an obstacle is within 1.0 meter. |
| **`SPACE`** | **360 Scene Story Snapshot** | Triggers an immediate comprehensive multi-modal narration. |
| **`T`** | **High-Accuracy Text Read (OCR)** | Scans and reads any visible text in the frame aloud. |
| **`M`** | **Mute / Unmute Audio** | Toggles assistive voice alerts on or off. |
| **`S`** | **Save Snapshot** | Saves current annotated HUD frame to disk with timestamp. |
| **`Q` or `ESC`**| **Quit Application** | Safely shuts down video feed, speech engine, and closes windows. |
