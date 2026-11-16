# 👓 Smart Glasses Assistive Vision & Sighted AI Companion (v2.0)
### Next-Gen Meta & Apple Glasses Edge AI Companion for the Blind & Visually Impaired

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Netlify-00e5ff?style=for-the-badge&logo=netlify)](https://smartevaluationglasses.netlify.app/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-00f0aa?style=for-the-badge&logo=github)](https://github.com/yghanasathyakarthik/Blind_SMart_Glasses)
[![Client-Side Architecture](https://img.shields.io/badge/Edge%20AI-Zero%20Cloud%20Cost-10b981?style=for-the-badge)](https://smartevaluationglasses.netlify.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

---

## 🌟 Executive Overview

**Smart Glasses Assistive Vision v2.0** transforms standard hardware and webcams into a world-class, autonomous assistive vision wearable inspired by **Meta Ray-Ban Smart Glasses** and **Apple Visual Intelligence**.

The system replaces legacy, cluttered academic layouts with a **streamlined, clutter-free glassmorphic cockpit** divided into **5 accessible top-level tabs**, ensuring visually impaired users and academic examiners enjoy an effortless, high-precision experience.

---

## 🧭 The 5 Dedicated Accessible Spaces

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                       SMART GLASSES ASSISTIVE VISION & AI COMPANION                         │
│  [👓 Vision & Radar]  [⚡ Blind Daily Tools]  [📖 Slow Book Reader]  [📝 Task & Memory]  [🎓 PhD Studio] │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1. 👓 Vision & Radar Cockpit
* **Dual Live HUD & 360° Radar:** Real-time object bounding boxes with calibrated pin-hole metric distance estimation ($0.35\text{m} - 8.0\text{m}$) and peripheral clock positions (`LEFT`, `CENTER`, `RIGHT`).
* **Directional Clearance & Evasion Vector:** Continuously assesses lateral corridor space and recommends the safest escape route (`STEP RIGHT`, `STEP LEFT`, `PATH CLEAR`).
* **Meta Voice Orb Visualizer:** Pulsing multi-state orb indicating listening, thinking, and speaking states.
* **Autonomous Crosswalk & Traffic Light AI:** Autonomously inspects traffic lights in the camera view; warns if RED (`"Traffic light is RED. Halt at curb."`) and immediately announces when it switches to GREEN (`"Traffic light turned GREEN! Crosswalk clear, you may proceed."`).

### 2. ⚡ Blind Daily Living Tools
* **Real-Time Currency Scanner:** Recognizes USD ($1, $5, $10, $20, $50, $100), Indian Rupees (₹10, ₹20, ₹50, ₹100, ₹200, ₹500), Euros, GBP, and Yen using OCR + color histogram validation.
* **Wardrobe Colorimeter:** Samples central garment colors and speaks exact shade names (Navy Blue, Crimson Red, Charcoal, Emerald Green) for independent dressing and outfit matching.
* **Ambient Lux Lighting Detector:** Measures ambient lumen levels and alerts the user if the room is pitch dark, dimly lit, well-lit, or glaringly overexposed.
* **Audio Clock-Face Spatial Compass:** Converts spatial obstacle coordinates into standard clock positions (*"Water bottle at 2 o'clock, 1.2 meters"*).
* **1-Touch Emergency SOS Siren & Beacon:** Flashes visual strobe, sounds a 900Hz piercing beacon, and broadcasts GPS coordinates.

### 3. 📖 Articulate Slow Book & Document Reader
* **User-Requested Pacing:** Reads books, letters, menus, and medicine labels **slowly and clearly** at $0.82\times - 0.88\times$ rate so visually impaired individuals can comfortably absorb and understand every word.
* **Natural Breath Pauses:** Inserts $450\text{ms}$ acoustic breath pauses between sentences.
* **Sentence Karaoke Highlighting:** Visually tracks the active sentence in real time.
* **Accessible Audio Controls:** Full voice and touch controls (`Play`, `Pause`, `Resume`, `Stop`, `Next`, `Previous`, `Speed Toggle`).

### 4. 📝 Task & Spatial Memory Hub
* **Voice-Driven Task Checklist:** Enables users to manage daily tasks hands-free (*"Add task take morning medicine"*, *"Mark task 1 as done"*, *"What are my tasks?"*).
* **Spatial Item Memory Engine:** Solves common misplacement challenges for visually impaired users. Users can speak *"Remember my white cane is beside the front door"* or *"Remember my wallet is on the dining table"*, and later ask *"Where did I leave my cane?"* or *"Where is my wallet?"* to retrieve the stored location instantly from persistent `localStorage`.

### 5. 🎓 PhD Research Studio
* Houses the complete academic evaluation platform for faculty examiners and peer reviewers:
  * **Module 1:** Multi-Dataset Object Detection (MS-COCO SSD MobileNet v2)
  * **Module 2:** Autonomous Driving & Transit Semantics (BDD100K)
  * **Module 3:** Low-Elevation Trip Hazards (Mapillary Vistas)
  * **Module 4:** Scene & Context Recognition (MIT Places365 ResNet-18)
  * **Module 5:** Captioning & Dense Narrative Synthesis (Salesforce BLIP)
  * **Module 6:** Assistive Optical Character Recognition (Tesseract.js & Android ML Kit)
  * **Module 7:** Geospatial Positioning & Orientation (GPS & OSM Nominatim)
  * **Module 8:** Multi-Tier Hazard Prioritization Engine
  * Includes LaTeX mathematical models, spatial clearance formulas, and benchmark comparisons.

---

## 🛠️ Critical Engineering Fixes in v2.0

| Issue | Root Cause | Solution Implemented |
|---|---|---|
| **False-Positive Pothole Alert** | Dark shirts, torsos, and shadows in webcam view were evaluated by floor heuristics. | Added strict human/indoor occlusion guard (`hasPersonOrIndoor`). Road hazards are strictly limited to outdoor navigation modes and require high background asphalt brightness ($>75$) and dense cavity contrast ($>85$). |
| **Voice Assistant Echo Feedback** | Speech recognition picked up the glasses' own speaker audio. | Implemented **Echo Guard** (`appState.isSpeaking`), muting microphone input during speech output, plus automatic 350ms restart resilience on Chrome/Edge. |
| **Rushed Book Reading** | Standard TTS rates (1.0x - 1.2x) were too fast for cognitive comprehension of printed text. | Built a dedicated Slow Book Reader with sentence splitting, $0.82\times$ pace, $450\text{ms}$ breath intervals, and sentence highlighting. |
| **Cluttered Monolithic UI** | All 8 academic modules, support cards, HUD, and sandboxes were stacked on one long page. | Refactored into 5 dedicated top-level accessible tabs with high-contrast keyboard navigation (`c` camera, `t` text, `d` describe, `space` voice prompt). |
| **Navigation Confirmation** | Users needed multi-turn confirmation to avoid wrong routes. | Added conversational destination dialog: Target Place $\rightarrow$ Area/District Prompt $\rightarrow$ User Confirmation $\rightarrow$ Active Route Guidance. |

---

## 🚀 Live Deployment & Local Setup

### Live Production URL
The project is deployed and live at: **[https://smartevaluationglasses.netlify.app/](https://smartevaluationglasses.netlify.app/)**

### Local Run
Simply open `index.html` in any modern web browser (Google Chrome, Microsoft Edge, Brave) supporting WebRTC and Web Speech API:
```bash
# Clone the repository
git clone https://github.com/yghanasathyakarthik/Blind_SMart_Glasses.git
cd Blind_SMart_Glasses

# Run a lightweight local server (or open index.html directly)
python -m http.server 8080
# Visit http://localhost:8080 in your browser
```

---

## 📄 License
This project is open-source under the MIT License.
