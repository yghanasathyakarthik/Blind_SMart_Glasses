# 👓 Smart Glasses Assistive Vision & Sighted AI Support System
### Meta & Apple Glasses Edge AI Companion for the Visually Impaired

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Netlify-00e5ff?style=for-the-badge&logo=netlify)](https://smartevaluationglasses.netlify.app/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-00f0aa?style=for-the-badge&logo=github)](https://github.com/yghanasathyakarthik/Blind_SMart_Glasses)
[![License: MIT](https://img.shields.io/badge/License-MIT-00f0aa?style=for-the-badge)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-ffb703?style=for-the-badge&logo=python)](https://python.org)
[![TensorFlow.js](https://img.shields.io/badge/TensorFlow.js-4.17.0-ff3366?style=for-the-badge&logo=tensorflow)](https://js.tensorflow.org)

An advanced, multi-modal assistive vision platform and 24/7 personal support system engineered for next-generation smart glasses (inspired by **Meta Ray-Ban Smart Glasses AI** and **Apple Visual Intelligence**). The system empowers visually impaired and blind individuals with real-time sensory augmentation, money reading, wardrobe color matching, ambient lighting detection, medication & expiry inspection, spatial audio sonar item tracking, clock-face mobility guidance, and an emergency SOS beacon.

---

## 🌟 Meta & Apple Glasses AI Sighted Support System

### 1. 💵 Currency & Banknote Denomination Reader
- **Multi-Currency Denomination Engine:** Recognizes Indian Rupees (₹10, ₹20, ₹50, ₹100, ₹200, ₹500, ₹2000), US Dollars ($1, $5, $10, $20, $50, $100), Euros (€5–€100), and British Pounds (£5–£50).
- **Fraud & Error Prevention:** Reads currency text (e.g. *Reserve Bank of India*, *Federal Reserve Note*) combined with central colorimetry. Announces denomination and bill orientation clearly (*"You are holding a ₹500 banknote, note is right side up"*).
- **Voice Trigger:** *"How much money am I holding?"*, *"Check money"* (or **Key M**).

### 2. 🎨 Real-Time Color Detector & Wardrobe Harmony Matcher
- **Central Reticle Colorimeter:** Samples camera center with high-precision RGB $\rightarrow$ HSL color transformation.
- **36 Nuanced Natural Shades:** Detects Jet Black, Pure White, Deep Navy Blue, Charcoal Gray, Crimson Red, Dark Olive Green, Khaki, Chocolate Brown, etc.
- **Blind Wardrobe Pairing Guide:** Automatically speaks styling advice (*"Deep Navy Blue. Pairs well with khaki trousers, white shirts, or beige."*).
- **Voice Trigger:** *"What color is this?"*, *"What color is my shirt?"* (or **Key K**).

### 3. 💡 Smart Lighting & Ambient Lux Monitor
- **Real-Time Sensor Luminance (0%–100% Lux):** Solves the common problem of blind individuals not knowing if room lights are left on or if they are in total darkness.
- **Categorized Awareness:**
  - `0% - 14%`: *"Pitch Black / Room lights appear to be OFF."*
  - `15% - 38%`: *"Dim ambient lighting."*
  - `39% - 85%`: *"Optimal indoor lighting."*
  - `> 85%`: *"Bright direct sunlight glare."*
- **Voice Trigger:** *"Is the light on?"*, *"Is it dark in here?"* (or **Key L**).

### 4. 💊 Medicine Dosage, Expiration & Barcode Inspector
- **Pharmaceutical Scanner:** Identifies medicines and active ingredients (e.g. *Paracetamol 500mg*, *Ibuprofen*, *Amoxicillin*).
- **Expiration Date Extractor:** Scans packaging for `EXP`, `BEST BEFORE`, and `USE BY` dates to prevent consuming expired goods.
- **Native Barcode Detection:** Integrates browser `window.BarcodeDetector` to decode 1D/2D retail barcodes and QR codes.
- **Voice Trigger:** *"Read expiration date"*, *"What medicine is this?"*.

### 5. 🔍 Find My Lost Items with Spatial Audio Sonar Radar
- **Misplaced Item Geolocation:** Helps users find misplaced white canes, phones, keys, water bottles, chairs, laptops, or mugs.
- **Clock-Face Direction:** *"Water bottle is at 1 o'clock, 1.2 meters away."*
- **Directional Acoustic Sonar Pulse:** Emits a Web Audio harmonic ping that rises in frequency (350Hz $\rightarrow$ 880Hz) and speeds up as the user's head turns toward dead center (*"Target dead center! Reach forward 0.7 meters."*).
- **Voice Trigger:** *"Find my water bottle"*, *"Where is my phone?"* (or **Key F**).

### 6. 🧭 Clock-Face Spatial Sighted Guide
- **Universal Blind Mobility Standard:** Translates visual geometry into intuitive clock-face bearings:
  - 12 o'clock: Directly ahead.
  - 1–2 o'clock: Slightly right / right side.
  - 10–11 o'clock: Slightly left / left side.
  - 3 & 9 o'clock: Lateral flanks.
- **Voice Trigger:** *"Give me a sighted report"*, *"Where are objects around me?"*.

### 7. 🚸 Pedestrian Crosswalk & Traffic Signal Safety
- **Zebra Stripe Pavement Engine:** Identifies high-contrast alternating ground stripes marking crosswalk zones.
- **Autonomous Traffic Light Classifier:** Analyzes vertical lamp color (Top Red vs. Bottom Green) without prompting. Halts users at the curb on Red; alerts when Green to proceed.
- **Voice Trigger:** *"Can I cross the street safely?"*, *"Traffic light status"*.

### 8. 🆘 Emergency SOS & GPS Dispatch Beacon
- **Instant Safety Protocol:** Immediately captures high-accuracy GPS coordinates and reverse-geocodes street address and city.
- **One-Touch Emergency Link:** Generates ready-to-dispatch WhatsApp & SMS alerts with Google Maps pin:
  `EMERGENCY ALERT: I am visually impaired and need assistance. My current location is: [Address] https://maps.google.com/?q=lat,lng`
- **Voice Trigger:** *"Emergency"*, *"Help me"*, *"SOS"* (or **Key E**).

### 9. 🤝 24/7 Empathetic Personal Support Companion
- **Anxiety & Emotional Reassurance:** Provides calm, grounded comfort when walking in high-stress or unfamiliar environments:
  > *"I understand feeling anxious. I am right here with you. Your smart glasses are continuously monitoring your surroundings and ground surface. Take slow, measured steps; I will alert you well in advance of any obstacles. You are doing great."*

---

## 🔬 8 PhD Research Modules

| Module | Designation | Architecture / Model | Primary Function |
|---|---|---|---|
| **M1** | Object Detection | MobileNetV2 / COCO-SSD | Real-time object localization & multi-class classification |
| **M2** | Outdoor Navigation | BDD100K Fine-Tuned YOLOv8 | Roadway scene understanding & vehicle hazard vectors |
| **M3** | Depth & Spatial Radar | Metric Gradient + Thermal Radar | Distance estimation & 360° radial sector clearance |
| **M4** | Scene Recognition | Places365 ResNet-18 | Indoor / outdoor contextual topological classification |
| **M5** | Storytelling & Captioning | VizWiz / BLIP Vision-Language | Comprehensive natural scene narrative generation |
| **M6** | Assistive OCR | Android ML Kit + Tesseract.js | Real-time full-frame book & document reading |
| **M7** | GPS Navigation | Nominatim + OSRM Foot Engine | Reverse geocoding & turn-by-turn walking routing |
| **M8** | Dynamic Priority Engine | Mathematical $f_{\text{risk}}$ Model | Multi-threat arbitration & directional evasion routing |

---

## ⌨️ Accessibility Hotkeys

| Hotkey | Function | Voice Feedback |
|---|---|---|
| **Spacebar** | Push-to-Talk Meta Glasses Voice Input | Harmonic Ascending Chime + Listening |
| **Key M** | Currency & Banknote Denomination Reader | Scans & speaks denomination (₹ / $ / € / £) |
| **Key K** | Color Detector & Wardrobe Matcher | Identifies exact shade + clothing pairing |
| **Key L** | Smart Lighting & Lux Meter | Speaks room brightness & light switch status |
| **Key F** | Find My Lost Items with Spatial Sonar | Starts directional acoustic sonar radar |
| **Key E** | Emergency SOS Dispatch Beacon | Siren tone + emergency location dispatch |
| **Key T** | Read Document / Book (OCR) | Scans text across entire camera frame |
| **Key D** | Comprehensive Scene Description | Generates natural environmental narrative |
| **Key C** | Start / Stop Real Camera | Camera state toggle |

---

## 📁 Repository Structure

```text
├── index.html                   # Master single-file web application & PhD portal (210 KB)
├── deploy_site/                 # Production distribution build (ready for Netlify deployment)
│   ├── index.html
│   ├── favicon.ico
│   └── Smart_Glasses_Assistive_Vision_Comprehensive_Project_Report.docx
├── smart_glasses_live_hud.py    # Desktop OpenCV Python HUD & testing runner
├── test_module_8.py             # Unit tests for Module 8 Priority Engine
├── verify_js.py                 # Node.js syntax & compilation validation script
├── LIVE_TESTING_GUIDE.md        # Comprehensive faculty & field evaluation manual
├── resnet18_places365.pth.tar   # Places365 scene recognition model weights
├── yolov8n.pt                   # YOLOv8 nano object detection model weights
└── Smart_Glasses_Comprehensive_Project_Report.docx # Academic thesis & evaluation documentation
```

---

## 🚀 Quick Start

### 1. Run Live Web Portal Locally
No server setup required. Run any static HTTP server:
```bash
python -m http.server 8000
```
Open `http://localhost:8000/` in Google Chrome or any modern browser.

### 2. Verify JavaScript Syntax
```bash
python verify_js.py
```

---

## 🌐 Live Deployment
The web portal is continuously hosted on Netlify:
👉 **[https://smartevaluationglasses.netlify.app/](https://smartevaluationglasses.netlify.app/)**

---

## 👨‍💻 Author
**Y. Ghana Sathya Karthik**  
Email: [yendlurighanasathyakarthik@gmail.com](mailto:yendlurighanasathyakarthik@gmail.com)  
GitHub: [@yghanasathyakarthik](https://github.com/yghanasathyakarthik)
