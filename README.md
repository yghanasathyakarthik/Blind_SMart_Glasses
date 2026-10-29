# 👓 Smart Glasses Assistive Vision System
### PhD Research Platform & Edge AI Portal for the Visually Impaired

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Netlify-00e5ff?style=for-the-badge&logo=netlify)](https://smartevaluationglasses.netlify.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-00f0aa?style=for-the-badge)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-ffb703?style=for-the-badge&logo=python)](https://python.org)
[![TensorFlow.js](https://img.shields.io/badge/TensorFlow.js-4.17.0-ff3366?style=for-the-badge&logo=tensorflow)](https://js.tensorflow.org)

An advanced, multi-modal assistive vision platform engineered for next-generation smart glasses. The system delivers real-time obstacle detection, corridor navigation, 360° metric depth thermal radar, high-accuracy book & document OCR, autonomous traffic light state announcing, conversational GPS turn-by-turn guidance, and an 8-module dynamic hazard priority arbiter.

---

## 🌟 Key Capabilities

1. **Dual-Layer Corridor Obstacle Detection:**
   - Deep learning bounding box inference via MobileNetV2 / COCO-SSD ($30\text{ FPS}$).
   - High-sensitivity $160\times 120$ floor-plane edge gradient analyzer detecting low-profile steel waiting benches, airport seating, boxes, and obstacles down to $1.1\text{m}$.
2. **Road & Ground Hazard Priority Engine:**
   - Real-time dark road cavity analysis for potholes and open depressions with evasion instructions (*"Caution! Pothole in path at 1.4m. Step right into safe corridor"*).
   - Speed breaker and pavement transverse ridge detection.
3. **Autonomous Traffic Light State Announcer:**
   - Automated vertical spectral color classifier (Red vs. Green) operating without prompting at pedestrian crosswalks.
   - Halts users on Red (*"Traffic light is RED. Please halt safely at the curb"*); prompts safe crossing on Green.
4. **Conversational GPS Navigation Assistant:**
   - Two-step place and locality confirmation via OpenStreetMap Nominatim:
     > *"I found [Destination] in [Area]. Is this the place in [Area] you want to navigate to? Please say Yes or No."*
   - Turn-by-turn walking route calculation with metric distance and walking ETA via OSRM.
5. **Meta Smart Glasses Stationary Silence Standard:**
   - Friendly conversational mode: Zero unprompted auditory interruptions while sitting at desks or conversing with stationary persons.
   - Dynamic approaching hazard escalation: Instant warning when vehicles ($6.0\text{m}$) or pedestrians ($3.5\text{m}$) approach rapidly.
6. **High-Accuracy Assistive OCR Reader:**
   - Client-side Android hardware `window.TextDetector` acceleration ($30\text{ms}$) with adaptive contrast binarization fallback for Tesseract.js.
   - Full document reading and bestseller intelligence (e.g. *The Subtle Art of Not Giving a F\*ck*, *Atomic Habits*).
7. **Universal Visual & Web Assistant:**
   - Real-time Wikipedia OpenSearch and DuckDuckGo integration to answer general knowledge queries hands-free.

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

## 📁 Repository Structure

```text
├── index.html                   # Master single-file web application & PhD portal
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

### 2. Run Python HUD Pipeline
```bash
pip install -r requirements.txt # opencv-python, ultralytics, torch, torchvision
python smart_glasses_live_hud.py
```

### 3. Verify JavaScript Syntax
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
