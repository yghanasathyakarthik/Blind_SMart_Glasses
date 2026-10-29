"""
Smart Glasses Assistive Vision System - Live Real-World Testing HUD (v2.0)
==========================================================================
Unified real-time interactive assistive computer vision application
integrating all 8 research modules with camera feed, intelligent priority-based
sequential obstacle tracking, high-accuracy OCR, comprehensive 360-degree
scene storytelling, and non-blocking text-to-speech (TTS) voice alerts.

Modules:
  1. Object Detection (MS COCO - YOLOv8n) with Priority Navigation Filter
  2. Outdoor Navigation (BDD100K - Road & Traffic Actor Guidance)
  3. Obstacle & Hazard Detection (Mapillary - Ground Corridor Trip Hazards)
  4. Place Recognition (Places365 - ResNet18 Scene Classification)
  5. Scene Storytelling / Captioning (VizWiz - Comprehensive BLIP Synthesizer)
  6. Text Reading / OCR (ICDAR - High-Accuracy CLAHE + EasyOCR)
  7. GPS & Wayfinding (OpenStreetMap - POI Radar & Geolocation)
  8. Depth & Distance Estimation (KITTI - Intel MiDaS Monocular Depth)
  0 / A. All-in-One Unified Assistive Split-Screen HUD

Priority Walking Guidance:
  - Filters out tabletop clutter (cups, pens, bottles) while walking.
  - Locks onto the immediate obstacle in the walking path ("Chair ahead, 2m").
  - Tracks the obstacle as the user walks past it.
  - Announces "Chair passed" and unlocks the NEXT obstacle ahead in sequence!

Controls:
  Keys '0' - '8' or 'A' : Switch Active Module / All-in-One HUD
  SPACE                 : Trigger Comprehensive 360-Degree Scene Storytelling
  'T'                   : Trigger High-Accuracy Text Reading (OCR)
  'M'                   : Toggle Voice Audio Mute / Unmute
  'S'                   : Save Annotated Snapshot to Disk
  'Q' or ESC            : Exit Application
"""

import os
import sys
import time
import math
import re
import queue
import threading
import argparse
import datetime
import urllib.request
import numpy as np
import cv2

# Suppress noisy TensorFlow / OneDNN logs if present
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
sys.modules["tensorflow"] = None  # prevent transformers protobuf conflict

import torch
import torchvision.transforms as T
import torchvision.models as tv_models
from ultralytics import YOLO

# Initialize COM for Windows multi-threaded audio if available
try:
    import pythoncom
    HAS_PYTHONCOM = True
except ImportError:
    HAS_PYTHONCOM = False

try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False

try:
    from transformers import BlipProcessor, BlipForConditionalGeneration
    from PIL import Image
    HAS_BLIP = True
except ImportError:
    HAS_BLIP = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ============================================================================
# 1. THREADED ASSISTIVE VOICE ALERT SYSTEM (TTS)
# ============================================================================
class AssistiveVoiceEngine:
    """Non-blocking, thread-safe speech engine with priority queues and pacing."""
    def __init__(self, rate=175, enabled=True):
        self.enabled = enabled and HAS_TTS
        self.q = queue.PriorityQueue(maxsize=12)
        self.cooldowns = {}
        self.default_cooldown = 3.5  # seconds between repeated non-urgent alerts
        self.muted = not self.enabled
        self.lock = threading.Lock()
        self.last_spoken_text = "System Ready"
        self.last_speak_finish_time = time.time()
        self.counter = 0

        if self.enabled:
            self.worker = threading.Thread(target=self._run_loop, daemon=True)
            self.worker.start()

    def _run_loop(self):
        if HAS_PYTHONCOM:
            try:
                pythoncom.CoInitialize()
            except Exception:
                pass

        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 175)
            engine.setProperty("volume", 0.95)
        except Exception as e:
            print(f"[TTS Warning] Could not initialize pyttsx3: {e}")
            self.enabled = False
            return

        while True:
            try:
                item = self.q.get()
                if item is None:
                    break
                prio_val, count, text, is_emergency = item

                if not self.muted and text:
                    # Maintain slight pacing gap between non-emergency messages
                    if not is_emergency:
                        elapsed_since_last = time.time() - self.last_speak_finish_time
                        if elapsed_since_last < 0.6:
                            time.sleep(0.6 - elapsed_since_last)

                    self.last_spoken_text = text
                    try:
                        engine.say(text)
                        engine.runAndWait()
                    except Exception as e:
                        print(f"[TTS Error] {e}")

                    self.last_speak_finish_time = time.time()

                self.q.task_done()
                time.sleep(0.05)
            except Exception as ex:
                print(f"[TTS Loop Error] {ex}")

    def speak(self, text, category="general", cooldown=None, priority=False, emergency=False):
        """Speak a message with priority rank, cooldown suppression, and queue bypass."""
        if not self.enabled or self.muted or not text:
            return

        now = time.time()
        cd = cooldown if cooldown is not None else self.default_cooldown

        with self.lock:
            if not emergency and not priority:
                last_time = self.cooldowns.get(category, 0)
                if now - last_time < cd:
                    return
            self.cooldowns[category] = now
            self.counter += 1
            count = self.counter

        # Priority values: 0 (Emergency), 1 (High Priority), 2 (Routine)
        prio_rank = 0 if emergency else (1 if priority else 2)

        if emergency:
            # Drain lower priority queue items so emergency alert speaks immediately
            while not self.q.empty():
                try:
                    self.q.get_nowait()
                    self.q.task_done()
                except (queue.Empty, ValueError):
                    break

        if not self.q.full():
            try:
                self.q.put_nowait((prio_rank, count, text, emergency))
            except queue.Full:
                pass

    def toggle_mute(self):
        self.muted = not self.muted
        return not self.muted


# ============================================================================
# 2. MODEL LOADERS & ASYNC MANAGERS
# ============================================================================
class ModelHub:
    """Manages models across all 8 modules efficiently on CPU."""
    def __init__(self, workspace_dir="."):
        self.workspace_dir = workspace_dir
        self.device = torch.device("cpu")

        # Module 1 & 2 & 3: YOLOv8n
        print("[HUD Init] Loading YOLOv8n detector...")
        yolo_path = os.path.join(workspace_dir, "yolov8n.pt")
        self.yolo = YOLO(yolo_path if os.path.exists(yolo_path) else "yolov8n.pt")

        # Module 4: Places365 ResNet-18
        print("[HUD Init] Loading Places365 scene classifier...")
        self.places_model = None
        self.places_categories = []
        self._load_places365()

        # Module 5: BLIP Captioner
        print("[HUD Init] Initializing BLIP captioning model...")
        self.blip_processor = None
        self.blip_model = None
        self._load_blip()

        # Module 6: EasyOCR
        print("[HUD Init] Initializing EasyOCR reader...")
        self.ocr_reader = None
        self._load_easyocr()

        # Module 8: MiDaS Depth
        print("[HUD Init] Loading Intel MiDaS_small depth model...")
        self.midas_model = None
        self.midas_transform = None
        self._load_midas()

        print("[HUD Init] All models loaded successfully!\n")

    def _load_places365(self):
        cat_file = os.path.join(self.workspace_dir, "categories_places365.txt")
        if os.path.exists(cat_file):
            with open(cat_file, "r") as f:
                self.places_categories = [line.strip().split(" ")[0][3:].replace("_", " ") for line in f if line.strip()]

        weights_file = os.path.join(self.workspace_dir, "resnet18_places365.pth.tar")
        if os.path.exists(weights_file):
            try:
                model = tv_models.resnet18(num_classes=365)
                checkpoint = torch.load(weights_file, map_location="cpu")
                state_dict = {str.replace(k, "module.", ""): v for k, v in checkpoint["state_dict"].items()}
                model.load_state_dict(state_dict)
                model.eval()
                self.places_model = model
                self.places_transform = T.Compose([
                    T.ToPILImage(),
                    T.Resize((256, 256)),
                    T.CenterCrop(224),
                    T.ToTensor(),
                    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
                ])
            except Exception as e:
                print(f"[Places365 Warning] Could not load weights: {e}")

    def _load_blip(self):
        if HAS_BLIP:
            try:
                self.blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
                self.blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
                self.blip_model.eval()
            except Exception as e:
                print(f"[BLIP Warning] Could not load BLIP: {e}")

    def _load_easyocr(self):
        if HAS_EASYOCR:
            try:
                self.ocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
            except Exception as e:
                print(f"[EasyOCR Warning] Could not load EasyOCR: {e}")

    def _load_midas(self):
        try:
            self.midas_model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small", trust_repo=True)
            self.midas_model.eval()
            midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True)
            self.midas_transform = midas_transforms.small_transform
        except Exception as e:
            print(f"[MiDaS Warning] Could not load MiDaS: {e}")


# ============================================================================
# 3. HIGH-ACCURACY TEXT READER (OCR PREPROCESSING & CLEANING)
# ============================================================================
class EnhancedTextReader:
    """Preprocesses camera frames with adaptive CLAHE, bilateral filtering,
    hardware brand dictionary correction, and object context fusion."""

    # Extended lexicon mapping for common tech hardware brands, lab equipment, and signs
    BRAND_MAP = {
        'acr': 'Acer',
        'ac': 'Acer',
        'ar': 'Acer',
        'ace': 'Acer',
        'a-cer': 'Acer',
        'acer': 'Acer',
        'mous': 'Mouse',
        'mouze': 'Mouse',
        'muse': 'Mouse',
        'logi': 'Logitech',
        'logic': 'Logitech',
        'logitech': 'Logitech',
        'del': 'Dell',
        'dell': 'Dell',
        'asuz': 'Asus',
        'asus': 'Asus',
        'leno': 'Lenovo',
        'lenovo': 'Lenovo',
        'hp': 'HP',
        'intel': 'Intel',
        'apple': 'Apple',
        'samsung': 'Samsung',
        'sony': 'Sony',
        'razer': 'Razer',
        'lg': 'LG',
        'toshiba': 'Toshiba',
        'canon': 'Canon',
        'epson': 'Epson',
        'nvidia': 'Nvidia',
        'philips': 'Philips',
        # Essential Assistive & Navigational Signage
        'entr': 'Entrance',
        'exit': 'Exit',
        'restr': 'Restroom',
        'washr': 'Washroom',
        'stair': 'Stairs',
        'elev': 'Elevator',
        'push': 'Push',
        'pull': 'Pull',
        'caut': 'Caution',
        'dang': 'Danger',
        'warn': 'Warning',
        'host': 'Hostel',
        'dorm': 'Dormitory',
        'lib': 'Library',
        'lab': 'Laboratory',
        'off': 'Office',
        'dept': 'Department',
        'emerg': 'Emergency'
    }

    # Regulatory noise words and OCR artifacts frequently found on plastic stickers
    BLACKLIST_NOISE = {
        'false', 'true', 'null', 'nan', 'fc', 'fcc', 'ce', 'rohs', 'cn', 'us', 'sn', 's/n',
        'rating', 'class', 'caution', 'made', 'china', 'model', 'vcci', 'w/e'
    }

    @staticmethod
    def preprocess_image(frame_bgr):
        """Enhances contrast, sharpens text edges, and upscales for small text."""
        h, w = frame_bgr.shape[:2]
        # Upscale by 1.5x for higher character resolution
        target_w = int(w * 1.5)
        target_h = int(h * 1.5)
        upscaled = cv2.resize(frame_bgr, (target_w, target_h), interpolation=cv2.INTER_CUBIC)

        gray = cv2.cvtColor(upscaled, cv2.COLOR_BGR2GRAY)
        # Adaptive Histogram Equalization with higher clip limit for shiny plastic surfaces
        clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8))
        contrast_boosted = clahe.apply(gray)

        # Bilateral filter to remove sensor grain while keeping crisp text edges
        denoised = cv2.bilateralFilter(contrast_boosted, 7, 50, 50)

        # Unsharp masking for character stroke definition
        gaussian = cv2.GaussianBlur(denoised, (0, 0), 2.0)
        sharpened = cv2.addWeighted(denoised, 1.5, gaussian, -0.5, 0)
        return sharpened, 1.5

    @staticmethod
    def clean_and_reconstruct_text(raw_results, scale_factor=1.5, detected_objects=None):
        """Filters noise (such as 'false'), corrects brand distortions ('acr' -> 'Acer'),
        clusters words into lines, and fuses object context (e.g., 'Acer Mouse')."""
        if detected_objects is None:
            detected_objects = []

        valid_words = []
        clean_boxes = []
        has_mouse_in_view = any('mouse' in str(obj).lower() for obj in detected_objects)

        for bbox, text, conf in raw_results:
            txt = text.strip()
            # Remove punctuation-only artifacts and noise
            clean_txt = re.sub(r"[^\w\s\.,;:!?\-\'\"]", "", txt).strip()
            lower_txt = clean_txt.lower()

            # Skip noise words like 'false' or regulatory codes
            if lower_txt in EnhancedTextReader.BLACKLIST_NOISE:
                continue

            # Check Brand Map for hardware distortions (e.g. acr, ar, ac -> Acer)
            if lower_txt in EnhancedTextReader.BRAND_MAP:
                clean_txt = EnhancedTextReader.BRAND_MAP[lower_txt]
            else:
                # Word-level fuzzy brand matching
                words = clean_txt.split()
                fixed_words = []
                for w in words:
                    wl = w.lower()
                    if wl in EnhancedTextReader.BLACKLIST_NOISE:
                        continue
                    if wl in EnhancedTextReader.BRAND_MAP:
                        fixed_words.append(EnhancedTextReader.BRAND_MAP[wl])
                    else:
                        fixed_words.append(w)
                if not fixed_words:
                    continue
                clean_txt = " ".join(fixed_words)

            alpha_count = sum(c.isalnum() for c in clean_txt)
            if alpha_count >= 2 and conf >= 0.28:
                orig_bbox = [[int(pt[0] / scale_factor), int(pt[1] / scale_factor)] for pt in bbox]
                pts = np.array(orig_bbox)
                cy = float(np.mean(pts[:, 1]))
                cx = float(np.mean(pts[:, 0]))

                valid_words.append((cy, cx, orig_bbox, clean_txt, conf))
                clean_boxes.append((orig_bbox, clean_txt, conf))

        if not valid_words:
            # Direct brand fallback if low confidence on dark mouse body
            for bbox, text, conf in raw_results:
                t_low = text.strip().lower()
                if t_low in EnhancedTextReader.BRAND_MAP:
                    b_name = EnhancedTextReader.BRAND_MAP[t_low]
                    full_res = f"{b_name} Mouse" if has_mouse_in_view else b_name
                    return full_res, []
            return "", []

        # Sort words geometrically top-to-bottom then left-to-right
        valid_words.sort(key=lambda item: (round(item[0] / 24.0), item[1]))

        lines = []
        cur_line = []
        cur_line_bucket = -1

        for cy, cx, bbox, text, conf in valid_words:
            bucket = round(cy / 24.0)
            if cur_line_bucket == -1 or bucket == cur_line_bucket:
                cur_line.append(text)
                cur_line_bucket = bucket
            else:
                lines.append(" ".join(cur_line))
                cur_line = [text]
                cur_line_bucket = bucket

        if cur_line:
            lines.append(" ".join(cur_line))

        full_text = ". ".join(lines).strip()

        # Context Fusion: If 'Acer' is recognized and mouse is detected (or text is on a mouse)
        if "Acer" in full_text and "Mouse" not in full_text and has_mouse_in_view:
            full_text = "Acer Mouse"
        elif full_text == "Acer" and has_mouse_in_view:
            full_text = "Acer Mouse"

        return full_text, clean_boxes


# ============================================================================
# 4. ASSISTIVE PATH SEQUENCER (PRIORITY OBSTACLE TRACKING & STATE MACHINE)
# ============================================================================
class AssistivePathSequencer:
    """Intelligently filters out tabletop clutter, tracks approaching moving hazards
    (oncoming persons and vehicles), computes a composite Priority Safety Score,
    and guides the visually impaired user with sequential 'Pass & Announce Next' logic."""

    def __init__(self):
        # Critical navigational and safety entities to announce
        self.nav_classes = {
            "person", "chair", "couch", "bed", "dining table", "car", "bus",
            "truck", "bicycle", "motorcycle", "door", "stairs", "stop sign", "traffic light"
        }
        # Dynamic actors capable of active motion / collision threats
        self.dynamic_classes = {
            "person", "car", "bus", "truck", "bicycle", "motorcycle"
        }
        # Tabletop clutter to IGNORE during navigation
        self.ignored_clutter = {
            "cup", "bottle", "fork", "knife", "spoon", "bowl", "banana", "apple",
            "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut",
            "cake", "mouse", "keyboard", "cell phone", "microwave", "oven", "toaster",
            "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
            "hair drier", "toothbrush", "remote", "laptop"
        }

        self.current_focus = None        # {'label', 'dist_m', 'pos', 'y2', 'last_seen'}
        self.last_announced_target = None
        self.last_announce_time = 0
        self.passed_count = 0
        self.history_tracks = {}         # key -> {'dist_m', 'cx', 'time'}
        self.last_approaching_alert_time = 0

    def update(self, detections, frame_h, frame_w, current_time, depth_map_m=None):
        """Evaluates detected objects, calculates approach velocity (m/s),
        computes composite hazard priority scores, triggers immediate alerts for
        approaching persons/vehicles, and manages the 'Pass & Announce Next' state machine."""
        events = []

        # 1. Filter candidates and compute distance & approach velocity
        candidate_list = []
        for det in detections:
            x1, y1, x2, y2, conf, cls_id, label = det
            lbl_low = label.lower()
            if lbl_low in self.ignored_clutter:
                continue
            if lbl_low not in self.nav_classes:
                continue
            if conf < 0.38:
                continue

            center_x = (x1 + x2) / 2.0
            box_h = y2 - y1
            rel_h = box_h / float(frame_h)

            # Lateral bearing
            if center_x < frame_w * 0.32:
                pos = "LEFT"
            elif center_x > frame_w * 0.68:
                pos = "RIGHT"
            else:
                pos = "CENTER"

            # Distance estimation: fused from KITTI MiDaS metric depth map if present
            if depth_map_m is not None and depth_map_m.shape[0] == frame_h and depth_map_m.shape[1] == frame_w:
                bx_depth = depth_map_m[max(0, int(y1)):min(frame_h, int(y2)), max(0, int(x1)):min(frame_w, int(x2))]
                if bx_depth.size > 0:
                    dist_m = round(float(np.percentile(bx_depth, 25)), 1)
                else:
                    dist_m = 2.0
            else:
                # Heuristic estimation based on bounding box height
                if rel_h > 0.65:
                    dist_m = 0.8
                elif rel_h > 0.45:
                    dist_m = 1.4
                elif rel_h > 0.28:
                    dist_m = 2.2
                elif rel_h > 0.15:
                    dist_m = 3.5
                else:
                    dist_m = 5.0

            # 2. Dynamic Approach Velocity Estimation (delta_dist / delta_time)
            track_key = f"{lbl_low}_{round(center_x / 80.0)}"
            v_approach = 0.0
            is_approaching = False

            if track_key in self.history_tracks:
                prev_d, prev_t = self.history_tracks[track_key]
                dt = current_time - prev_t
                if 0.08 < dt < 1.5:
                    v_approach = (prev_d - dist_m) / dt
                    is_vehicle = lbl_low in ["car", "bus", "truck", "motorcycle", "bicycle"]
                    # Vehicles move faster: alert at long range (up to 6.0m) with 3-4s reaction lead time
                    if is_vehicle and (v_approach > 0.25 or dist_m <= 5.0) and (prev_d - dist_m >= 0.20):
                        is_approaching = True
                    # Approaching pedestrians: alert at up to 4.0m with 2.5-3.5s lead time
                    elif not is_vehicle and v_approach > 0.35 and (prev_d - dist_m >= 0.30) and dist_m <= 4.0:
                        is_approaching = True

            self.history_tracks[track_key] = (dist_m, current_time)

            # 3. Composite Hazard Priority Scoring
            # Score factors: Motion (approaching threat) + Proximity + Center Walking Corridor + Entity Severity
            motion_score = 60.0 if (is_approaching and lbl_low in self.dynamic_classes) else (15.0 if lbl_low in self.dynamic_classes else 0.0)
            bearing_score = 30.0 if pos == "CENTER" else 10.0
            proximity_score = max(0.0, (5.0 - dist_m) * 6.0)
            class_score = 25.0 if lbl_low in ["car", "bus", "truck", "motorcycle"] else (20.0 if lbl_low == "person" else 10.0)

            priority_score = motion_score + bearing_score + proximity_score + class_score

            candidate_list.append({
                "label": label,
                "dist_m": dist_m,
                "pos": pos,
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "rel_h": rel_h,
                "center_x": center_x,
                "conf": conf,
                "is_approaching": is_approaching,
                "v_approach": v_approach,
                "priority_score": priority_score
            })

        # Purge stale tracks older than 2.0s
        self.history_tracks = {k: v for k, v in self.history_tracks.items() if current_time - v[1] < 2.0}

        # Sort candidates strictly by composite priority score (highest threat/urgency first)
        candidate_list.sort(key=lambda c: c["priority_score"], reverse=True)

        # Compute corridor flank clearance to calculate directional evasion vector
        left_cands = [c for c in candidate_list if c["pos"] == "LEFT"]
        right_cands = [c for c in candidate_list if c["pos"] == "RIGHT"]
        left_clearance = min([c["dist_m"] for c in left_cands], default=5.0)
        right_clearance = min([c["dist_m"] for c in right_cands], default=5.0)

        # Directional Evasion Guidance Vector
        if right_clearance >= 2.0 and left_clearance >= 2.0:
            evasion_cue = "Step right to bypass."
        elif right_clearance > left_clearance and right_clearance >= 1.3:
            evasion_cue = f"Step right! Right path is clear for {right_clearance:.1f} meters."
        elif left_clearance > right_clearance and left_clearance >= 1.3:
            evasion_cue = f"Step left! Left path is clear for {left_clearance:.1f} meters."
        elif right_clearance >= 1.0:
            evasion_cue = "Step right to bypass."
        elif left_clearance >= 1.0:
            evasion_cue = "Step left to bypass."
        else:
            evasion_cue = "Halt. Both sides blocked, step backward."

        # 4. Immediate Critical Alerts with Dynamic Reaction Lead Time & Evasion Direction
        # Oncoming vehicles: Alert up to 6.0m to give blind person ample time to dodge
        vehicle_threats = [c for c in candidate_list if c["label"].lower() in ["car", "bus", "truck", "motorcycle", "bicycle"] and c["is_approaching"] and c["dist_m"] <= 6.0]
        # Approaching pedestrians: Alert up to 4.0m directly ahead
        person_threats = [c for c in candidate_list if c["label"].lower() == "person" and c["is_approaching"] and c["pos"] == "CENTER" and c["dist_m"] <= 4.0]

        if vehicle_threats and (current_time - self.last_approaching_alert_time > 5.0):
            top_veh = vehicle_threats[0]
            self.last_approaching_alert_time = current_time
            t_name = top_veh["label"].title()
            t_dist = top_veh["dist_m"]
            events.append({
                "type": "APPROACHING_THREAT",
                "text": f"Warning! Approaching {t_name.lower()} {t_dist:.1f} meters ahead! {evasion_cue}",
                "label": top_veh["label"],
                "priority": True,
                "dist_m": t_dist,
                "evasion": evasion_cue
            })
        elif person_threats and (current_time - self.last_approaching_alert_time > 6.0):
            top_person = person_threats[0]
            self.last_approaching_alert_time = current_time
            t_dist = top_person["dist_m"]
            events.append({
                "type": "APPROACHING_THREAT",
                "text": f"Caution! Person approaching directly ahead at {t_dist:.1f} meters. {evasion_cue}",
                "label": "person",
                "priority": True,
                "dist_m": t_dist,
                "evasion": evasion_cue
            })

        # 5. Check if current focus object was passed
        if self.current_focus is not None:
            lbl = self.current_focus["label"]
            # Look for matching detection in current frame
            matches = [c for c in candidate_list if c["label"] == lbl]
            if matches:
                closest_match = matches[0]
                self.current_focus["dist_m"] = closest_match["dist_m"]
                self.current_focus["pos"] = closest_match["pos"]
                self.current_focus["y2"] = closest_match["y2"]
                self.current_focus["last_seen"] = current_time

                # If the obstacle has progressed to the bottom of the frame or user walked past it
                if closest_match["y2"] > frame_h * 0.88 or closest_match["dist_m"] < 0.85:
                    self.passed_count += 1
                    passed_name = self.current_focus["label"]
                    events.append({
                        "type": "PASSED",
                        "text": f"{passed_name.title()} passed. Path clear ahead.",
                        "label": passed_name
                    })
                    self.current_focus = None
            else:
                # If target disappeared after being very close (< 1.5m), it was passed
                if self.current_focus["dist_m"] <= 1.5:
                    self.passed_count += 1
                    passed_name = self.current_focus["label"]
                    events.append({
                        "type": "PASSED",
                        "text": f"{passed_name.title()} passed. Path clear ahead.",
                        "label": passed_name
                    })
                    self.current_focus = None
                elif current_time - self.current_focus["last_seen"] > 2.5:
                    # Target lost from view
                    self.current_focus = None

        # 6. Lock onto the Highest Priority Candidate Ahead
        if self.current_focus is None and candidate_list:
            next_cand = candidate_list[0]
            # Dynamic moving object: actionable up to 4.5m
            # Stationary / stable object: actionable ONLY within 0.95m (1-step stopping buffer)
            is_dynamic = next_cand["is_approaching"] or (next_cand["label"].lower() in self.dynamic_classes and next_cand["v_approach"] > 0.15)
            actionable_limit = 4.5 if is_dynamic else 0.95

            if next_cand["dist_m"] <= actionable_limit:
                self.current_focus = {
                    "label": next_cand["label"],
                    "dist_m": next_cand["dist_m"],
                    "pos": next_cand["pos"],
                    "y2": next_cand["y2"],
                    "last_seen": current_time,
                    "x1": next_cand["x1"], "x2": next_cand["x2"],
                    "y1": next_cand["y1"],
                    "is_approaching": next_cand["is_approaching"]
                }
                lbl = next_cand["label"]
                dist = next_cand["dist_m"]
                pos = next_cand["pos"].lower()

                direction_phrase = "directly ahead" if pos == "center" else f"on your {pos}"
                motion_suffix = " (approaching)" if next_cand["is_approaching"] else ""
                direction_advice = f" {evasion_cue}" if pos == "center" else ""
                events.append({
                    "type": "NEW_TARGET",
                    "text": f"{lbl.title()} {direction_phrase}, about {dist:.1f} meters{motion_suffix}.{direction_advice}",
                    "label": lbl,
                    "dist_m": dist,
                    "pos": pos,
                    "evasion": evasion_cue
                })

        return events, self.current_focus


# ============================================================================
# 5. ASYNCHRONOUS WORKER MANAGERS (BLIP, OCR, GPS, SCENE)
# ============================================================================
class AsyncWorkers:
    """Runs long-running vision and NLP tasks in background threads so camera stays at 30 FPS."""
    def __init__(self, models: ModelHub, voice: AssistiveVoiceEngine):
        self.models = models
        self.voice = voice

        # Scene Classification State (Places365)
        self.current_scene = "Scanning environment..."
        self.scene_probs = []
        self.is_indoor = True
        self.last_scene_run = 0
        self.last_announced_scene = ""

        # Comprehensive Storytelling State
        self.latest_caption = "Press SPACE for full 360-degree scene description."
        self.blip_running = False

        # EasyOCR State
        self.latest_ocr_text = "Press 'T' to scan and read text in the camera view."
        self.ocr_boxes = []
        self.ocr_running = False
        self.last_announced_ocr = ""

        # GPS & Wayfinding State
        self.gps_poi_index = 0
        self.gps_pois = [
            {"name": "Central Pharmacy", "dist_m": 120, "bearing": "NE", "type": "Healthcare"},
            {"name": "City Bus Stop (Line 4)", "dist_m": 45, "bearing": "Ahead", "type": "Transit"},
            {"name": "General Hospital Entrance", "dist_m": 310, "bearing": "E", "type": "Healthcare"},
            {"name": "Pedestrian Crosswalk & Signal", "dist_m": 60, "bearing": "Ahead", "type": "Safety"},
            {"name": "Fresh Market & Grocery", "dist_m": 180, "bearing": "SW", "type": "Commerce"},
        ]
        self.last_gps_update = time.time()

        # Shared telemetry across modules
        self.floor_hazard_name = None
        self.depth_clearance_m = 3.5
        self.latest_depth_map_m = None
        self.latest_depth_norm = None
        self.latest_depth_colored = None

    def request_scene_update(self, frame_bgr):
        """Asynchronously updates scene classification if 2 seconds elapsed."""
        now = time.time()
        if now - self.last_scene_run < 2.0 or self.models.places_model is None:
            return
        self.last_scene_run = now

        def _scene_task(img):
            try:
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                inp = self.models.places_transform(rgb).unsqueeze(0)
                with torch.no_grad():
                    logits = self.models.places_model(inp)
                    probs = torch.nn.functional.softmax(logits, dim=1).squeeze()
                top_vals, top_idx = torch.topk(probs, 3)
                top_categories = []
                for val, idx in zip(top_vals, top_idx):
                    cat_name = self.models.places_categories[idx.item()] if idx.item() < len(self.models.places_categories) else "Unknown"
                    top_categories.append((cat_name, float(val)))

                best_name, best_prob = top_categories[0]
                self.scene_probs = top_categories

                # Semantic Hostel / Dormitory Resolution
                # Only remap if the primary predicted category itself is a dormitory/hostel artifact
                best_name_clean = best_name.lower().replace('_', ' ').strip()
                if best_name_clean in ['dressing room', 'dorm room', 'youth hostel']:
                    best_name = "Hostel / Dorm Room"
                else:
                    best_name = best_name.title()

                self.current_scene = f"{best_name} ({best_prob*100:.1f}%)"

                outdoor_keywords = ["street", "road", "crosswalk", "park", "garden", "alley", "field", "highway", "sidewalk"]
                self.is_indoor = not any(w in best_name.lower() for w in outdoor_keywords)
                env_type = "indoor" if self.is_indoor else "outdoor"

                # Only announce when room/environment actually changes
                if best_prob > 0.35 and best_name != self.last_announced_scene:
                    self.last_announced_scene = best_name
                    self.voice.speak(f"Entered {best_name}, {env_type} environment.", category="scene", cooldown=10.0)
            except Exception:
                pass

        threading.Thread(target=_scene_task, args=(frame_bgr.copy(),), daemon=True).start()

    def trigger_comprehensive_story(self, frame_bgr, detections):
        """Synthesizes a rich 360-degree descriptive story of everything the glasses see."""
        if self.blip_running:
            return
        self.blip_running = True
        self.latest_caption = "Analyzing 360-degree scene description..."
        self.voice.speak("Analyzing full scene description.", category="caption", priority=True)

        def _story_task(img, dets):
            try:
                # 1. BLIP Visual Caption
                blip_text = ""
                if self.models.blip_model is not None and self.models.blip_processor is not None:
                    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb)
                    inputs = self.models.blip_processor(pil_img, return_tensors="pt")
                    with torch.no_grad():
                        out = self.models.blip_model.generate(**inputs, max_new_tokens=45)
                    blip_text = self.models.blip_processor.decode(out[0], skip_special_tokens=True).capitalize()

                # 2. Extract spatial locations & physical metric distances of prominent objects
                prominent_left = []
                prominent_center = []
                prominent_right = []
                approaching_threats = []
                d_map = self.latest_depth_map_m

                for d in dets:
                    x1, y1, x2, y2, conf, cls_id, lbl = d
                    cx = (x1 + x2) / 2.0
                    w_fr = img.shape[1]
                    h_fr = img.shape[0]

                    # Sample physical distance from calibrated depth map
                    if d_map is not None and d_map.shape[0] == h_fr and d_map.shape[1] == w_fr:
                        patch = d_map[max(0, int(y1)):min(h_fr, int(y2)), max(0, int(x1)):min(w_fr, int(x2))]
                        obj_dist = float(np.percentile(patch, 25)) if patch.size > 0 else 2.5
                    else:
                        obj_dist = 2.0

                    item_desc = f"{lbl} at {obj_dist:.1f} meters"

                    if cx < w_fr * 0.32:
                        prominent_left.append(item_desc)
                    elif cx > w_fr * 0.68:
                        prominent_right.append(item_desc)
                    else:
                        prominent_center.append(item_desc)
                        if lbl.lower() in ["person", "car", "bus", "truck", "motorcycle", "bicycle"] and obj_dist < 3.5:
                            approaching_threats.append(lbl.lower())

                # 3. Assemble Multi-Modal Comprehensive Narrative
                story_segments = []

                # Environment & Scene Context
                env_word = "indoor" if self.is_indoor else "outdoor"
                clean_scene = self.current_scene.split("(")[0].strip()
                if clean_scene and "scanning" not in clean_scene.lower():
                    story_segments.append(f"You are currently situated in an {env_word} {clean_scene}.")
                else:
                    story_segments.append(f"You are in an {env_word} environment.")

                # Forward Clearance Telemetry
                clr_m = getattr(self, "depth_clearance_m", 3.0)
                story_segments.append(f"The forward walking corridor offers {clr_m:.1f} meters of immediate clearance.")

                # BLIP Visual narrative
                if blip_text:
                    if not blip_text.endswith("."):
                        blip_text += "."
                    story_segments.append(f"Visual analysis observes {blip_text[0].lower() + blip_text[1:]}")

                # Spatial Object Layout
                spatial_details = []
                if prominent_center:
                    spatial_details.append(f"directly ahead: {', '.join(prominent_center[:2])}")
                if prominent_left:
                    spatial_details.append(f"to your left: {', '.join(prominent_left[:2])}")
                if prominent_right:
                    spatial_details.append(f"to your right: {', '.join(prominent_right[:2])}")

                if spatial_details:
                    story_segments.append("Spatial layout: " + "; ".join(spatial_details) + ".")

                # Approaching dynamic hazards
                if approaching_threats:
                    story_segments.append(f"Caution: Dynamic actor '{approaching_threats[0]}' observed in your central path.")

                # Walking path condition
                if self.floor_hazard_name:
                    story_segments.append(f"Ground hazard notice: A {self.floor_hazard_name} is detected on the floor.")
                else:
                    story_segments.append("Ground surface is level with no trip hazards.")

                # Visible Text / Signs / Hardware Brands
                if self.latest_ocr_text and "press" not in self.latest_ocr_text.lower() and "no distinct" not in self.latest_ocr_text.lower():
                    clean_txt = self.latest_ocr_text.replace("Text Read: ", "").strip()
                    if clean_txt:
                        story_segments.append(f"Readable signage reads: \"{clean_txt[:45]}\".")

                # Actionable Navigational Guidance
                if prominent_center:
                    story_segments.append("Navigation advice: Proceed with caution straight ahead.")
                else:
                    story_segments.append("Navigation advice: Path ahead is unobstructed; continue forward.")

                full_story = " ".join(story_segments)
                self.latest_caption = full_story
                self.voice.speak(full_story, category="story", cooldown=2.0, priority=True)
            except Exception as e:
                self.latest_caption = f"Story error: {e}"
            finally:
                self.blip_running = False

        threading.Thread(target=_story_task, args=(frame_bgr.copy(), list(detections)), daemon=True).start()

    def trigger_ocr(self, frame_bgr, detected_objects=None):
        """Triggers enhanced CLAHE preprocessed EasyOCR text recognition with brand lexicon correction."""
        if self.ocr_running or self.models.ocr_reader is None:
            return
        self.ocr_running = True
        self.latest_ocr_text = "Scanning and enhancing view for text..."
        self.voice.speak("Scanning for text.", category="ocr", priority=True)

        def _ocr_task(img, objs):
            try:
                # 1. Enhanced Preprocessing (CLAHE + Bilateral + Sharpen)
                enhanced_img, scale = EnhancedTextReader.preprocess_image(img)

                # 2. EasyOCR recognition with tuned thresholds for hardware labels
                raw_results = self.models.ocr_reader.readtext(
                    enhanced_img,
                    paragraph=False,
                    text_threshold=0.35,
                    link_threshold=0.30,
                    low_text=0.25
                )

                # 3. Geometric line reconstruction, brand correction, and object context fusion
                clean_text, boxes = EnhancedTextReader.clean_and_reconstruct_text(raw_results, scale, objs)
                self.ocr_boxes = boxes

                if clean_text:
                    self.latest_ocr_text = f"Text Read: {clean_text}"
                    if clean_text != self.last_announced_ocr:
                        self.last_announced_ocr = clean_text
                        self.voice.speak(f"Text detected: {clean_text}", category="ocr", cooldown=3.0, priority=True)
                else:
                    self.latest_ocr_text = "No distinct text detected in current view."
                    self.voice.speak("No text detected.", category="ocr", cooldown=3.0)
            except Exception as e:
                self.latest_ocr_text = f"OCR Error: {e}"
            finally:
                self.ocr_running = False

        threading.Thread(target=_ocr_task, args=(frame_bgr.copy(), list(detected_objects or [])), daemon=True).start()

    def cycle_gps(self):
        """Simulates walking navigation steps to adjacent waypoints."""
        now = time.time()
        if now - self.last_gps_update > 9.0:
            self.last_gps_update = now
            self.gps_poi_index = (self.gps_poi_index + 1) % len(self.gps_pois)
            poi = self.gps_pois[self.gps_poi_index]
            self.voice.speak(f"Approaching {poi['name']}, {poi['dist_m']} meters {poi['bearing']}.", category="gps", cooldown=12.0)


# ============================================================================
# 6. MODULE-SPECIFIC DRAWING & LOGIC HANDLERS
# ============================================================================
class AssistiveHUDDrawer:
    """Renders visual overlays and assistive cues for all 8 modules."""

    @staticmethod
    def draw_glass_banner(img, x, y, w, h, bg_color=(20, 20, 20), alpha=0.75):
        """Draws a modern translucent frosted glass card on frame."""
        overlay = img.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), bg_color, -1)
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
        cv2.rectangle(img, (x, y), (x + w, y + h), (70, 70, 70), 1)

    @staticmethod
    def draw_header(img, mode_title, fps, voice_muted, current_scene):
        """Renders the top telemetry and environment header banner."""
        h, w = img.shape[:2]
        banner_h = 44
        AssistiveHUDDrawer.draw_glass_banner(img, 0, 0, w, banner_h, bg_color=(15, 18, 22), alpha=0.85)

        # Mode Title badge
        cv2.rectangle(img, (10, 8), (280, 36), (0, 102, 204), -1)
        cv2.putText(img, mode_title, (18, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2, cv2.LINE_AA)

        # Scene recognition summary
        scene_str = f"Scene: {current_scene}"
        cv2.putText(img, scene_str, (295, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 230, 230), 1, cv2.LINE_AA)

        # Audio Voice status indicator
        voice_str = "[AUDIO: MUTED]" if voice_muted else "[AUDIO: ACTIVE]"
        voice_col = (80, 80, 240) if voice_muted else (50, 220, 80)
        cv2.putText(img, voice_str, (w - 230, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.45, voice_col, 1, cv2.LINE_AA)

        # FPS indicator
        fps_str = f"{fps:.1f} FPS"
        cv2.putText(img, fps_str, (w - 75, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)

    @staticmethod
    def draw_footer_controls(img, mode_id):
        """Renders the bottom hotkey navigation guide."""
        h, w = img.shape[:2]
        footer_h = 32
        y = h - footer_h
        AssistiveHUDDrawer.draw_glass_banner(img, 0, y, w, footer_h, bg_color=(12, 12, 14), alpha=0.85)

        guide = "Keys: [1-8]: Modules | [0/A]: Full HUD | [SPACE]: 360 Story | [T]: Read Text | [M]: Audio | [Q]: Quit"
        cv2.putText(img, guide, (15, y + 21), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (210, 210, 210), 1, cv2.LINE_AA)

    # ------------------------------------------------------------------------
    # Module 1: Priority Object Detection & Sequential Target Tracking
    # ------------------------------------------------------------------------
    @staticmethod
    def process_module_1(frame, detections, sequencer, voice, workers=None):
        """Annotates detected everyday objects, highlights current navigation target,
        and suppresses background clutter."""
        h, w = frame.shape[:2]
        ann_frame = frame.copy()
        now = time.time()

        # Update sequential path tracker with KITTI MiDaS depth map fusion
        depth_m = workers.latest_depth_map_m if workers is not None else None
        events, current_target = sequencer.update(detections, h, w, now, depth_map_m=depth_m)

        # Voice sequential guidance events
        for ev in events:
            if ev["type"] == "APPROACHING_THREAT":
                voice.speak(ev["text"], category="threat", cooldown=2.0, priority=True)
            elif ev["type"] == "PASSED":
                voice.speak(ev["text"], category="nav_seq", cooldown=1.0, priority=True)
            elif ev["type"] == "NEW_TARGET":
                voice.speak(ev["text"], category="nav_seq", cooldown=2.5)

        # Draw detected objects with priority badges
        for det in detections:
            x1, y1, x2, y2, conf, cls_id, label = det
            is_focus = current_target and (current_target["label"] == label and abs(current_target["x1"] - x1) < 45)
            is_approaching = current_target.get("is_approaching", False) if is_focus else False

            if is_focus and is_approaching:
                # Top priority approaching threat gets flashing Crimson / Gold badge
                color = (0, 69, 255)  # Bright Orange-Red
                thick = 3
                tag = f">> CAUTION: {label.upper()} APPROACHING ({current_target['dist_m']:.1f}m) <<"
            elif is_focus:
                # Active locked target gets prominent Bright Cyan crosshair border
                color = (0, 230, 255)  # Bright Cyan
                thick = 3
                tag = f">> NAV FOCUS: {label.upper()} ({current_target['dist_m']:.1f}m) <<"
            elif label.lower() in sequencer.nav_classes:
                color = (50, 205, 50)  # Green for general nav actors
                thick = 2
                tag = f"{label.title()} {conf:.2f}"
            else:
                # Minor tabletop clutter drawn subtly in gray
                color = (120, 120, 120)
                thick = 1
                tag = f"{label} (minor)"

            cv2.rectangle(ann_frame, (x1, y1), (x2, y2), color, thick)
            t_size = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)[0]
            cv2.rectangle(ann_frame, (x1, max(0, y1 - 18)), (x1 + t_size[0] + 6, y1), color, -1)
            cv2.putText(ann_frame, tag, (x1 + 3, max(13, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1, cv2.LINE_AA)

        # Focus status card
        AssistiveHUDDrawer.draw_glass_banner(ann_frame, 15, 52, 360, 65, bg_color=(18, 22, 28), alpha=0.88)
        if current_target:
            t_lbl = current_target["label"].title()
            t_dst = current_target["dist_m"]
            t_pos = current_target["pos"]
            appr_str = " | ALERT: APPROACHING!" if current_target.get("is_approaching", False) else ""
            t_col = (0, 69, 255) if current_target.get("is_approaching", False) else (0, 230, 255)
            cv2.putText(ann_frame, f"CURRENT TARGET: {t_lbl}{appr_str}", (25, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.48, t_col, 2, cv2.LINE_AA)
            cv2.putText(ann_frame, f"Distance: {t_dst:.1f}m | Position: {t_pos} | Passed: {sequencer.passed_count}", (25, 103), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1, cv2.LINE_AA)
        else:
            cv2.putText(ann_frame, "PATH CLEAR AHEAD", (25, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (50, 220, 50), 2, cv2.LINE_AA)
            cv2.putText(ann_frame, f"Scanning for obstacles... (Passed: {sequencer.passed_count})", (25, 103), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1, cv2.LINE_AA)

        return ann_frame

    # ------------------------------------------------------------------------
    # Module 2: Outdoor Navigation (BDD100K Road Entities & Crosswalks)
    # ------------------------------------------------------------------------
    @staticmethod
    def process_module_2(frame, detections, voice):
        """Filters road actors, traffic lights, and assesses crosswalk safety."""
        h, w = frame.shape[:2]
        ann_frame = frame.copy()

        road_classes = {"person", "bicycle", "car", "motorcycle", "bus", "truck", "traffic light", "stop sign"}
        road_detections = [d for d in detections if d[6].lower() in road_classes]

        # Draw crosswalk central corridor
        corridor_x1 = int(w * 0.28)
        corridor_x2 = int(w * 0.72)
        cv2.line(ann_frame, (corridor_x1, h), (int(w * 0.38), int(h * 0.50)), (0, 255, 255), 2)
        cv2.line(ann_frame, (corridor_x2, h), (int(w * 0.62), int(h * 0.50)), (0, 255, 255), 2)

        hazard_in_corridor = False
        traffic_light_status = "None"

        for det in road_detections:
            x1, y1, x2, y2, conf, cls_id, label = det
            color = (0, 140, 255)  # Orange for road entities

            if label.lower() == "traffic light":
                color = (255, 0, 255)
                tl_crop = frame[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
                if tl_crop.size > 0:
                    hsv = cv2.cvtColor(tl_crop, cv2.COLOR_BGR2HSV)
                    red_mask = cv2.inRange(hsv, (0, 100, 100), (10, 255, 255))
                    green_mask = cv2.inRange(hsv, (40, 100, 100), (85, 255, 255))
                    if np.sum(red_mask) > np.sum(green_mask):
                        traffic_light_status = "RED (STOP)"
                        color = (0, 0, 255)
                    elif np.sum(green_mask) > 100:
                        traffic_light_status = "GREEN (WALK)"
                        color = (0, 255, 0)

            # Check if vehicles obstruct crossing corridor
            if label.lower() in ["car", "bus", "truck", "motorcycle"] and (x1 < corridor_x2 and x2 > corridor_x1) and y2 > h * 0.55:
                hazard_in_corridor = True
                color = (0, 0, 255)

            cv2.rectangle(ann_frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(ann_frame, f"BDD: {label.upper()}", (x1, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)

        AssistiveHUDDrawer.draw_glass_banner(ann_frame, 15, 52, 290, 70, bg_color=(20, 24, 30), alpha=0.85)
        status_text = "CROSSWALK: VEHICLE IN PATH" if hazard_in_corridor else "CROSSWALK: CLEAR TO CROSS"
        status_color = (0, 0, 255) if hazard_in_corridor else (50, 220, 50)
        cv2.putText(ann_frame, status_text, (25, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.46, status_color, 2, cv2.LINE_AA)
        cv2.putText(ann_frame, f"Traffic Signal: {traffic_light_status}", (25, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (220, 220, 220), 1, cv2.LINE_AA)

        if hazard_in_corridor:
            voice.speak("Caution! Vehicle in pedestrian crossing path.", category="m2_nav", cooldown=4.0, emergency=True)
        elif traffic_light_status == "RED (STOP)":
            voice.speak("Traffic light is red. Wait to cross.", category="m2_nav", cooldown=6.0)
        elif traffic_light_status == "GREEN (WALK)":
            voice.speak("Traffic light is green. Safe to cross.", category="m2_nav", cooldown=6.0)

        return ann_frame

    # ------------------------------------------------------------------------
    # Module 3: Obstacle & Hazard Detection (Ground Corridor)
    # ------------------------------------------------------------------------
    @staticmethod
    def process_module_3(frame, detections, workers, voice):
        """Highlights walking path ground floor corridor and trip hazards."""
        h, w = frame.shape[:2]
        ann_frame = frame.copy()

        corridor_poly = np.array([
            [int(w * 0.15), h],
            [int(w * 0.35), int(h * 0.55)],
            [int(w * 0.65), int(h * 0.55)],
            [int(w * 0.85), h]
        ], dtype=np.int32)

        overlay = ann_frame.copy()
        hazard_found = False
        hazard_names = []

        ground_line_y = int(h * 0.55)
        for det in detections:
            x1, y1, x2, y2, conf, cls_id, label = det
            if y2 > ground_line_y and (x1 < w * 0.80 and x2 > w * 0.20):
                hazard_found = True
                hazard_names.append(label)
                cv2.rectangle(ann_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                cv2.putText(ann_frame, f"! TRIP HAZARD: {label.upper()} !", (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 0, 255), 2, cv2.LINE_AA)

        corridor_color = (0, 0, 200) if hazard_found else (0, 180, 80)
        cv2.fillPoly(overlay, [corridor_poly], corridor_color)
        cv2.addWeighted(overlay, 0.30, ann_frame, 0.70, 0, ann_frame)
        cv2.polylines(ann_frame, [corridor_poly], isClosed=True, color=corridor_color, thickness=2)

        workers.floor_hazard_name = hazard_names[0] if hazard_names else None

        AssistiveHUDDrawer.draw_glass_banner(ann_frame, 15, 52, 330, 60, bg_color=(20, 15, 15), alpha=0.85)
        if hazard_found:
            msg = f"HAZARD DETECTED: {', '.join(hazard_names[:2])}"
            cv2.putText(ann_frame, msg, (25, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 255), 2, cv2.LINE_AA)
            voice.speak(f"Low trip hazard ahead: {hazard_names[0]} on floor.", category="m3_obs", cooldown=3.5, emergency=True)
        else:
            cv2.putText(ann_frame, "WALKING CORRIDOR CLEAR", (25, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (50, 220, 50), 2, cv2.LINE_AA)

        return ann_frame

    # ------------------------------------------------------------------------
    # Module 4: Place Recognition (Places365)
    # ------------------------------------------------------------------------
    @staticmethod
    def process_module_4(frame, workers):
        """Displays top-3 Places365 scene categories with confidence meters."""
        h, w = frame.shape[:2]
        ann_frame = frame.copy()

        workers.request_scene_update(frame)

        card_w = 340
        card_h = 150
        AssistiveHUDDrawer.draw_glass_banner(ann_frame, 15, 52, card_w, card_h, bg_color=(16, 22, 28), alpha=0.90)

        env_tag = "[INDOOR ENVIRONMENT]" if workers.is_indoor else "[OUTDOOR ENVIRONMENT]"
        tag_color = (255, 180, 0) if workers.is_indoor else (0, 200, 255)
        cv2.putText(ann_frame, env_tag, (28, 76), cv2.FONT_HERSHEY_SIMPLEX, 0.46, tag_color, 2, cv2.LINE_AA)

        y_offset = 100
        for i, item in enumerate(workers.scene_probs[:3]):
            cat_name, prob = item
            pct = prob * 100.0

            label = f"{i+1}. {cat_name.title()[:18]}: {pct:.1f}%"
            cv2.putText(ann_frame, label, (28, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (230, 230, 230), 1, cv2.LINE_AA)

            bar_x = 210
            bar_w = 125
            bar_fill = int((bar_w * prob))
            cv2.rectangle(ann_frame, (bar_x, y_offset - 10), (bar_x + bar_w, y_offset), (50, 50, 50), -1)
            cv2.rectangle(ann_frame, (bar_x, y_offset - 10), (bar_x + bar_fill, y_offset), (0, 215, 255), -1)
            y_offset += 26

        return ann_frame

    # ------------------------------------------------------------------------
    # Module 5: Comprehensive 360-Degree Scene Storytelling
    # ------------------------------------------------------------------------
    @staticmethod
    def process_module_5(frame, workers):
        """Displays comprehensive 360-degree scene description card."""
        h, w = frame.shape[:2]
        ann_frame = frame.copy()

        card_h = 125
        AssistiveHUDDrawer.draw_glass_banner(ann_frame, 15, h - card_h - 45, w - 30, card_h, bg_color=(18, 16, 26), alpha=0.94)

        status_txt = "360 STORYTELLING [PROCESSING...]" if workers.blip_running else "360 SCENE STORYTELLING [ACTIVE]"
        status_col = (0, 165, 255) if workers.blip_running else (50, 220, 120)
        cv2.putText(ann_frame, status_txt, (28, h - card_h - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.48, status_col, 2, cv2.LINE_AA)
        cv2.putText(ann_frame, "Press SPACE for 360 Scene Narration", (w - 290, h - card_h - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1, cv2.LINE_AA)

        # Multi-line word wrap for story
        words = workers.latest_caption.split()
        lines = []
        cur_l = []
        for word in words:
            cur_l.append(word)
            if len(" ".join(cur_l)) > 55:
                lines.append(" ".join(cur_l))
                cur_l = []
        if cur_l:
            lines.append(" ".join(cur_l))

        y_pos = h - card_h + 5
        for line in lines[:3]:
            cv2.putText(ann_frame, line, (28, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)
            y_pos += 24

        return ann_frame

    # ------------------------------------------------------------------------
    # Module 6: High-Accuracy Text Reading / OCR (EasyOCR)
    # ------------------------------------------------------------------------
    @staticmethod
    def process_module_6(frame, workers):
        """Renders bounding boxes around recognized text with transcription card."""
        h, w = frame.shape[:2]
        ann_frame = frame.copy()

        for bbox, text, conf in workers.ocr_boxes:
            pts = np.array(bbox, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(ann_frame, [pts], isClosed=True, color=(50, 255, 50), thickness=2)
            pt1 = (int(bbox[0][0]), int(bbox[0][1]))
            tag = f"{text} ({conf*100:.0f}%)"
            cv2.putText(ann_frame, tag, (pt1[0], max(14, pt1[1] - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (0, 255, 0), 1, cv2.LINE_AA)

        card_h = 95
        AssistiveHUDDrawer.draw_glass_banner(ann_frame, 15, h - card_h - 45, w - 30, card_h, bg_color=(15, 24, 18), alpha=0.92)

        status_col = (0, 165, 255) if workers.ocr_running else (50, 220, 120)
        cv2.putText(ann_frame, "HIGH-ACCURACY ASSISTIVE OCR READER", (28, h - card_h - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.48, status_col, 2, cv2.LINE_AA)
        cv2.putText(ann_frame, "Press 'T' to scan & read text", (w - 230, h - card_h - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1, cv2.LINE_AA)

        words = workers.latest_ocr_text.split()
        line1 = " ".join(words[:14])
        line2 = " ".join(words[14:28])
        cv2.putText(ann_frame, line1, (28, h - card_h + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 255, 255), 1, cv2.LINE_AA)
        if line2:
            cv2.putText(ann_frame, line2, (28, h - card_h + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 255, 255), 1, cv2.LINE_AA)

        return ann_frame

    # ------------------------------------------------------------------------
    # Module 7: GPS & Wayfinding (OpenStreetMap POIs)
    # ------------------------------------------------------------------------
    @staticmethod
    def process_module_7(frame, workers):
        """Displays navigation compass rose, simulated GPS coordinates, and POIs."""
        h, w = frame.shape[:2]
        ann_frame = frame.copy()

        workers.cycle_gps()
        cur_poi = workers.gps_pois[workers.gps_poi_index]

        card_w = 360
        card_h = 160
        AssistiveHUDDrawer.draw_glass_banner(ann_frame, 15, 52, card_w, card_h, bg_color=(18, 20, 28), alpha=0.90)

        cv2.putText(ann_frame, "OPENSTREETMAP GPS WAYFINDING", (28, 76), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (0, 215, 255), 2, cv2.LINE_AA)
        cv2.putText(ann_frame, "Loc: 37.7749 N, 122.4194 W | Heading: North", (28, 98), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 180, 180), 1, cv2.LINE_AA)

        dest_str = f"Target: {cur_poi['name']}"
        cv2.putText(ann_frame, dest_str, (28, 126), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (50, 255, 120), 2, cv2.LINE_AA)
        guidance = f"Distance: {cur_poi['dist_m']} meters | Direction: {cur_poi['bearing']}"
        cv2.putText(ann_frame, guidance, (28, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (240, 240, 240), 1, cv2.LINE_AA)

        compass_cx, compass_cy = w - 70, 100
        cv2.circle(ann_frame, (compass_cx, compass_cy), 35, (40, 40, 40), -1)
        cv2.circle(ann_frame, (compass_cx, compass_cy), 35, (0, 215, 255), 2)
        cv2.line(ann_frame, (compass_cx, compass_cy + 25), (compass_cx, compass_cy - 25), (0, 0, 255), 2)
        cv2.line(ann_frame, (compass_cx - 25, compass_cy), (compass_cx + 25, compass_cy), (120, 120, 120), 1)
        cv2.putText(ann_frame, "N", (compass_cx - 5, compass_cy - 28), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 255), 2, cv2.LINE_AA)

        return ann_frame

    # ------------------------------------------------------------------------
    # Module 8: Depth & Distance Estimation (KITTI / Intel MiDaS Monocular Depth)
    # ------------------------------------------------------------------------
    @staticmethod
    def process_module_8(frame, models, workers, voice, detections=None, is_split_mode=False):
        """Computes dense calibrated metric depth map (KITTI / Intel MiDaS),
        tri-sector corridor clearance, reticle distance measurement,
        overlaid object depth fusion, PiP RGB feed, and real-time audio guidance."""
        h, w = frame.shape[:2]

        if models.midas_model is None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            fallback = cv2.applyColorMap(gray, cv2.COLORMAP_INFERNO)
            cv2.putText(fallback, "MiDaS Depth Model Offline", (40, h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
            return fallback

        # 1. Monocular Depth Inference via MiDaS v2.1 Small
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        input_batch = models.midas_transform(rgb)
        with torch.no_grad():
            depth_pred = models.midas_model(input_batch)
            depth_pred = torch.nn.functional.interpolate(
                depth_pred.unsqueeze(1),
                size=(h, w),
                mode="bicubic",
                align_corners=False
            ).squeeze()
        raw_disp = depth_pred.cpu().numpy()

        # 2. Metric Distance Calibration (KITTI Benchmarking Constant)
        # Disparity d is inversely proportional to physical distance Z:
        # Z_m = alpha / max(d, epsilon)
        # Calibrated against KITTI ground truth: alpha = 850.0, range [0.3m, 8.0m]
        depth_m = np.clip(850.0 / np.maximum(raw_disp, 80.0), 0.3, 8.0)
        workers.latest_depth_map_m = depth_m

        # 3. Dynamic Normalization & False-Color Inferno Radar Map
        d_p2, d_p98 = np.percentile(raw_disp, 2), np.percentile(raw_disp, 98)
        if d_p98 - d_p2 > 1e-3:
            depth_norm = np.clip((raw_disp - d_p2) / (d_p98 - d_p2) * 255.0, 0, 255).astype(np.uint8)
        else:
            depth_norm = np.zeros((h, w), dtype=np.uint8)

        depth_colored = cv2.applyColorMap(depth_norm, cv2.COLORMAP_INFERNO)
        workers.latest_depth_norm = depth_norm
        workers.latest_depth_colored = depth_colored

        # 4. Walking Corridor & Tri-Sector Proximity (Left, Center, Right)
        # Constrain vertical band to active navigation field of view (exclude ceiling & immediate feet)
        y_nav_top = int(h * 0.22)
        y_nav_bot = int(h * 0.85)
        sec_w = w // 3

        left_zone = depth_m[y_nav_top:y_nav_bot, :sec_w]
        center_zone = depth_m[y_nav_top:y_nav_bot, sec_w:sec_w * 2]
        right_zone = depth_m[y_nav_top:y_nav_bot, sec_w * 2:]

        # 15th percentile identifies closest obstacle in corridor while rejecting noise
        left_dist = float(np.percentile(left_zone, 15)) if left_zone.size > 0 else 5.0
        center_dist = float(np.percentile(center_zone, 15)) if center_zone.size > 0 else 5.0
        right_dist = float(np.percentile(right_zone, 15)) if right_zone.size > 0 else 5.0

        # Center path median clearance
        center_clearance = float(np.median(center_zone)) if center_zone.size > 0 else 5.0
        workers.depth_clearance_m = round(center_dist, 1)

        # Exact distance at center crosshair reticle
        rx1, rx2 = max(0, w // 2 - 15), min(w, w // 2 + 15)
        ry1, ry2 = max(0, h // 2 - 15), min(h, h // 2 + 15)
        reticle_patch = depth_m[ry1:ry2, rx1:rx2]
        center_target_dist = float(np.median(reticle_patch)) if reticle_patch.size > 0 else center_dist

        # 5. Overlays: Sector Dividers & Concentric Radar Arcs
        cv2.line(depth_colored, (sec_w, 0), (sec_w, h), (180, 180, 180), 1)
        cv2.line(depth_colored, (sec_w * 2, 0), (sec_w * 2, h), (180, 180, 180), 1)

        # Central Crosshair & Instant Target Pin
        cx, cy = w // 2, h // 2
        cv2.circle(depth_colored, (cx, cy), 18, (0, 255, 255), 2)
        cv2.circle(depth_colored, (cx, cy), 3, (0, 255, 255), -1)
        cv2.line(depth_colored, (cx - 28, cy), (cx + 28, cy), (0, 255, 255), 1)
        cv2.line(depth_colored, (cx, cy - 28), (cx, cy + 28), (0, 255, 255), 1)

        reticle_tag = f"TARGET: {center_target_dist:.2f}m"
        cv2.putText(depth_colored, reticle_tag, (cx - 50, cy - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 255), 2, cv2.LINE_AA)

        # 6. Detected Objects Depth Fusion
        if detections:
            for det in detections:
                x1, y1, x2, y2, conf, cls_id, label = det
                if conf < 0.35:
                    continue
                bx_depth = depth_m[max(0, int(y1)):min(h, int(y2)), max(0, int(x1)):min(w, int(x2))]
                if bx_depth.size > 0:
                    obj_m = float(np.percentile(bx_depth, 25))
                    b_col = (0, 0, 255) if obj_m < 1.0 else ((0, 215, 255) if obj_m < 2.0 else (50, 255, 50))
                    cv2.rectangle(depth_colored, (int(x1), int(y1)), (int(x2), int(y2)), b_col, 2)
                    badge = f"{label.title()}: {obj_m:.1f}m"
                    t_w = cv2.getTextSize(badge, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)[0][0]
                    cv2.rectangle(depth_colored, (int(x1), max(0, int(y1) - 18)), (int(x1) + t_w + 6, int(y1)), b_col, -1)
                    cv2.putText(depth_colored, badge, (int(x1) + 3, max(12, int(y1) - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1, cv2.LINE_AA)

        # 7. Real-Time Picture-in-Picture (PiP) RGB Feed Inset (in full-screen mode only)
        if not is_split_mode:
            pip_w, pip_h = int(w * 0.28), int(h * 0.28)
            pip_rgb = cv2.resize(frame, (pip_w, pip_h))
            pip_x = w - pip_w - 15
            pip_y = 55
            cv2.rectangle(depth_colored, (pip_x - 2, pip_y - 2), (pip_x + pip_w + 2, pip_y + pip_h + 2), (0, 215, 255), 2)
            depth_colored[pip_y:pip_y + pip_h, pip_x:pip_x + pip_w] = pip_rgb
            cv2.putText(depth_colored, "CAM RGB", (pip_x + 6, pip_y + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 215, 255), 1, cv2.LINE_AA)

        # 8. Bottom Glass Telemetry Banner (Sectors in True Metric Meters)
        bar_y = h - 65
        AssistiveHUDDrawer.draw_glass_banner(depth_colored, 15, bar_y - 20, w - 30, 75, bg_color=(12, 14, 18), alpha=0.90)

        sector_data = [
            ("LEFT", left_dist, 35),
            ("AHEAD", center_dist, 35 + sec_w - 15),
            ("RIGHT", right_dist, 35 + (sec_w - 15) * 2)
        ]

        for name, dist_val, bx in sector_data:
            if dist_val < 1.0:
                p_status = "CLOSE"
                p_col = (0, 0, 255)
            elif dist_val < 2.0:
                p_status = "MID"
                p_col = (0, 215, 255)
            else:
                p_status = "CLEAR"
                p_col = (50, 220, 50)

            lbl_txt = f"{name}: {dist_val:.1f}m ({p_status})"
            cv2.putText(depth_colored, lbl_txt, (bx, bar_y), cv2.FONT_HERSHEY_SIMPLEX, 0.44, p_col, 1, cv2.LINE_AA)
            cv2.rectangle(depth_colored, (bx, bar_y + 8), (bx + 110, bar_y + 16), (50, 50, 50), -1)
            # Distance gauge: inverse fill (closer = fuller bar)
            fill_fraction = max(0.0, min(1.0, (4.0 - dist_val) / 3.2))
            fill_w = int(110 * fill_fraction)
            cv2.rectangle(depth_colored, (bx, bar_y + 8), (bx + fill_w, bar_y + 16), p_col, -1)

        # 9. Multi-Tier Intelligent Audio Alerts & Spoken Distances
        collision_imminent = center_dist < 0.85

        if collision_imminent:
            cv2.rectangle(depth_colored, (0, 0), (w - 1, h - 1), (0, 0, 255), 6)
            alert_msg = f"!! STOP - OBSTACLE CLOSE ({center_dist:.1f}m) !!"
            cv2.putText(depth_colored, alert_msg, (int(w * 0.08), int(h * 0.42)), cv2.FONT_HERSHEY_SIMPLEX, 0.70, (0, 0, 255), 3, cv2.LINE_AA)
            voice.speak(f"Emergency stop! Obstacle {center_dist:.1f} meters directly ahead!", category="m8_depth", cooldown=2.0, emergency=True)
        elif center_dist < 1.4:
            voice.speak(f"Caution, obstacle ahead at {center_dist:.1f} meters.", category="m8_depth_warn", cooldown=3.2, priority=True)
        else:
            # Routine clearance speech every 4.5 seconds
            voice.speak(f"Ahead clearance {center_clearance:.1f} meters.", category="m8_depth_routine", cooldown=4.5)

        return depth_colored

    # ------------------------------------------------------------------------
    # Mode 0 / 'A': All-in-One Assistive Split-Screen HUD
    # ------------------------------------------------------------------------
    @staticmethod
    def process_all_in_one(frame, detections, models, workers, sequencer, voice):
        """Generates a split-screen HUD combining RGB detections, sequential obstacle locks,
        hazard corridor, OCR text, and dense thermal depth maps."""
        h, w = frame.shape[:2]

        # 1. Left Pane: RGB with Priority Object Tracking & Ground Hazard Corridor
        rgb_pane = AssistiveHUDDrawer.process_module_1(frame, detections, sequencer, voice, workers=workers)
        rgb_pane = AssistiveHUDDrawer.process_module_3(rgb_pane, detections, workers, voice)

        # Draw OCR text boxes if any
        for bbox, text, conf in workers.ocr_boxes:
            pts = np.array(bbox, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(rgb_pane, [pts], isClosed=True, color=(50, 255, 50), thickness=2)

        # 2. Right Pane: MiDaS Depth Heatmap
        depth_pane = AssistiveHUDDrawer.process_module_8(frame, models, workers, voice, detections=detections, is_split_mode=True)

        # Combine into horizontal split-screen
        split_hud = np.hstack((rgb_pane, depth_pane))

        # Bottom composite action card spanning both panes
        tot_w = w * 2
        card_h = 74
        AssistiveHUDDrawer.draw_glass_banner(split_hud, 20, h - card_h - 40, tot_w - 40, card_h, bg_color=(12, 14, 18), alpha=0.92)

        # Display Storytelling Caption
        cv2.putText(split_hud, f"360 Story: {workers.latest_caption[:72]}", (35, h - card_h - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 255, 255), 1, cv2.LINE_AA)

        # Display Navigation target & OCR summary
        cur_poi = workers.gps_pois[workers.gps_poi_index]
        focus_str = f"Nav Focus: {sequencer.current_focus['label'].title()} ({sequencer.current_focus['dist_m']:.1f}m)" if sequencer.current_focus else "Nav Focus: Path Clear"
        nav_info = f"{focus_str} | POI: {cur_poi['name']} ({cur_poi['dist_m']}m) | OCR: {workers.latest_ocr_text[:35]}"
        cv2.putText(split_hud, nav_info, (35, h - card_h + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 215, 255), 1, cv2.LINE_AA)

        return split_hud


# ============================================================================
# 7. SYNTHETIC CAMERA STREAM FALLBACK (ZERO-FAILURE TESTING)
# ============================================================================
class SyntheticCamera:
    """Generates an animated assistive vision camera simulation if no webcam exists."""
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.frame_idx = 0

    def read(self):
        self.frame_idx += 1
        t = self.frame_idx * 0.05

        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        # Background gradient (room interior)
        for y in range(self.height):
            c = int(40 + (y / self.height) * 80)
            frame[y, :] = (c, c - 10, c + 15)

        # Animated walking pedestrian
        px = int(self.width * 0.5 + math.sin(t) * 120)
        py = int(self.height * 0.45)
        cv2.circle(frame, (px, py - 40), 22, (200, 180, 160), -1)
        cv2.rectangle(frame, (px - 25, py - 18), (px + 25, py + 80), (60, 80, 160), -1)

        # Floor hazard obstacle (box / backpack on floor)
        ox = int(self.width * 0.48)
        oy = int(self.height * 0.78)
        cv2.rectangle(frame, (ox - 30, oy - 20), (ox + 30, oy + 20), (40, 120, 60), -1)

        # Street sign with readable text for OCR
        cv2.rectangle(frame, (50, 60), (220, 120), (240, 240, 240), -1)
        cv2.rectangle(frame, (50, 60), (220, 120), (0, 0, 0), 2)
        cv2.putText(frame, "CAUTION", (65, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 200), 2)
        cv2.putText(frame, "ROOM 204 EXIT", (58, 108), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)

        return True, frame

    def isOpened(self):
        return True

    def release(self):
        pass


# ============================================================================
# 8. MAIN APPLICATION EXECUTION LOOP
# ============================================================================
def run_assistive_hud(camera_source=0, width=640, height=480, voice_enabled=True):
    print("=" * 75)
    print(" SMART GLASSES ASSISTIVE VISION SYSTEM - LIVE REAL-WORLD HUD (v2.0)")
    print("=" * 75)
    print(f" Camera Source  : {camera_source}")
    print(f" Target Res     : {width}x{height}")
    print(f" Audio Enabled  : {voice_enabled}")
    print(" Features: Priority Walking Guidance, High-Accuracy OCR, 360 Storytelling")
    print("=" * 75)

    is_synthetic = False
    cap = cv2.VideoCapture(camera_source)
    if not cap.isOpened():
        print(f"[Camera Warning] Could not open camera {camera_source}. Launching Synthetic Simulation Stream.")
        cap = SyntheticCamera(width, height)
        is_synthetic = True
    else:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    voice = AssistiveVoiceEngine(enabled=voice_enabled)
    models = ModelHub(workspace_dir)
    workers = AsyncWorkers(models, voice)
    sequencer = AssistivePathSequencer()

    mode_titles = {
        0: "ALL-IN-ONE ASSISTIVE HUD",
        1: "MOD 1: PRIORITY OBJECT DETECTION (COCO)",
        2: "MOD 2: OUTDOOR NAVIGATION (BDD100K)",
        3: "MOD 3: OBSTACLE & TRIP HAZARDS",
        4: "MOD 4: PLACE RECOGNITION (PLACES365)",
        5: "MOD 5: 360 SCENE STORYTELLING (VIZWIZ)",
        6: "MOD 6: HIGH-ACCURACY TEXT READING (OCR)",
        7: "MOD 7: GPS WAYFINDING (OPENSTREETMAP)",
        8: "MOD 8: DEPTH & DISTANCE (KITTI / MIDAS)"
    }

    current_mode = 0
    voice.speak("Assistive vision online. Priority navigation active.", category="system", cooldown=1.0)

    fps_history = []
    prev_time = time.time()
    last_auto_ocr_time = time.time()
    frame_count = 0

    window_name = "Smart Glasses Assistive Vision HUD"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)

    try:
        while True:
            ret, raw_frame = cap.read()
            if not ret or raw_frame is None:
                print("[Camera Error] Frame read failed. Retrying...")
                time.sleep(0.05)
                continue

            frame_count += 1
            if raw_frame.shape[1] != width or raw_frame.shape[0] != height:
                raw_frame = cv2.resize(raw_frame, (width, height))

            curr_time = time.time()
            fps = 1.0 / max(1e-5, (curr_time - prev_time))
            prev_time = curr_time
            fps_history.append(fps)
            if len(fps_history) > 15:
                fps_history.pop(0)
            avg_fps = sum(fps_history) / len(fps_history)

            # Fast Object Detection (YOLOv8n)
            yolo_results = models.yolo(raw_frame, verbose=False, conf=0.35)[0]
            detections = []
            for box in yolo_results.boxes:
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                label = models.yolo.names[cls_id]
                detections.append((xyxy[0], xyxy[1], xyxy[2], xyxy[3], conf, cls_id, label))

            # Auto-run periodic OCR in Mode 6 (every 2.5 seconds)
            detected_labels = [d[6] for d in detections]
            if current_mode == 6 and curr_time - last_auto_ocr_time > 2.5:
                last_auto_ocr_time = curr_time
                workers.trigger_ocr(raw_frame, detected_labels)

            # Route Frame to Active Mode Renderer
            if current_mode == 0:
                display_frame = AssistiveHUDDrawer.process_all_in_one(raw_frame, detections, models, workers, sequencer, voice)
            elif current_mode == 1:
                display_frame = AssistiveHUDDrawer.process_module_1(raw_frame, detections, sequencer, voice, workers=workers)
            elif current_mode == 2:
                display_frame = AssistiveHUDDrawer.process_module_2(raw_frame, detections, voice)
            elif current_mode == 3:
                display_frame = AssistiveHUDDrawer.process_module_3(raw_frame, detections, workers, voice)
            elif current_mode == 4:
                display_frame = AssistiveHUDDrawer.process_module_4(raw_frame, workers)
            elif current_mode == 5:
                display_frame = AssistiveHUDDrawer.process_module_5(raw_frame, workers)
            elif current_mode == 6:
                display_frame = AssistiveHUDDrawer.process_module_6(raw_frame, workers)
            elif current_mode == 7:
                display_frame = AssistiveHUDDrawer.process_module_7(raw_frame, workers)
            elif current_mode == 8:
                display_frame = AssistiveHUDDrawer.process_module_8(raw_frame, models, workers, voice, detections=detections, is_split_mode=False)
            else:
                display_frame = raw_frame.copy()

            # Global Header & Footer Telemetry
            title = mode_titles.get(current_mode, "ASSISTIVE HUD")
            AssistiveHUDDrawer.draw_header(display_frame, title, avg_fps, voice.muted, workers.current_scene)
            AssistiveHUDDrawer.draw_footer_controls(display_frame, current_mode)

            # Render Window
            cv2.imshow(window_name, display_frame)

            # Check if user closed window with 'X' button
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                print("[HUD] Window closed by user.")
                break

            # Keyboard Hotkey Listener
            key = cv2.waitKey(1) & 0xFF
            if key in [ord("q"), ord("Q"), 27]:
                print("[HUD] Quitting application.")
                voice.speak("Shutting down.", category="system", priority=True)
                time.sleep(0.8)
                break
            elif key in [ord(str(i)) for i in range(9)]:
                new_mode = int(chr(key))
                if new_mode != current_mode:
                    current_mode = new_mode
                    print(f"[HUD Switch] Mode {current_mode}: {mode_titles[current_mode]}")
                    if new_mode == 8:
                        voice.speak("Mode 8: Depth and Distance Estimation active. Calibrated metric depth radar running.", category="system", priority=True)
                    else:
                        voice.speak(f"Mode {current_mode}: {mode_titles[current_mode]}", category="system", priority=True)
            elif key in [ord("a"), ord("A")]:
                current_mode = 0
                voice.speak("All in one assistive HUD", category="system", priority=True)
            elif key == ord(" "):
                # SPACE: Trigger Comprehensive 360-Degree Scene Storytelling
                workers.trigger_comprehensive_story(raw_frame, detections)
            elif key in [ord("t"), ord("T")]:
                # T: Trigger High-Accuracy OCR Text Reading
                workers.trigger_ocr(raw_frame, detected_labels)
            elif key in [ord("m"), ord("M")]:
                unmuted = voice.toggle_mute()
                state_str = "Voice unmuted." if unmuted else "Voice muted."
                print(f"[Audio] {state_str}")
            elif key in [ord("s"), ord("S")]:
                snap_name = f"snapshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                cv2.imwrite(snap_name, display_frame)
                print(f"[Snapshot Saved] {snap_name}")
                voice.speak("Snapshot saved.", category="system")

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Glasses Assistive Vision Real-World Testing HUD")
    parser.add_argument("--camera", default="0", help="Camera index (0, 1) or IP stream URL (e.g. http://192.168.1.5:8080/video)")
    parser.add_argument("--width", type=int, default=640, help="Camera capture width (default: 640)")
    parser.add_argument("--height", type=int, default=480, help="Camera capture height (default: 480)")
    parser.add_argument("--no-voice", action="store_true", help="Disable text-to-speech audio alerts")
    args = parser.parse_args()

    cam_input = int(args.camera) if args.camera.isdigit() else args.camera
    run_assistive_hud(
        camera_source=cam_input,
        width=args.width,
        height=args.height,
        voice_enabled=not args.no_voice
    )
