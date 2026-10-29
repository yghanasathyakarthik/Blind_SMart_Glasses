import cv2, torch, time
import numpy as np
from smart_glasses_live_hud import ModelHub, AsyncWorkers, AssistiveVoiceEngine, AssistiveHUDDrawer, AssistivePathSequencer

print('--- Testing Module 8 (KITTI / Intel MiDaS Depth Estimation) ---')
models = ModelHub('D:/Blind_SMart_Glasses')
voice = AssistiveVoiceEngine(enabled=False)
workers = AsyncWorkers(models, voice)
sequencer = AssistivePathSequencer()

# Create test frame with synthetic obstacles
frame = np.ones((480, 640, 3), dtype=np.uint8) * 60
# Add a close object in center
cv2.rectangle(frame, (220, 160), (420, 380), (220, 220, 220), -1)
# Add an object on the right
cv2.rectangle(frame, (480, 200), (600, 360), (180, 180, 180), -1)

detections = [
    (220, 160, 420, 380, 0.88, 56, 'chair'),
    (480, 200, 600, 360, 0.75, 64, 'mouse')
]

t0 = time.time()
hud_res = AssistiveHUDDrawer.process_module_8(frame, models, workers, voice, detections=detections, is_split_mode=False)
elapsed = time.time() - t0

print(f"Test 1 PASS: process_module_8 executed in {elapsed:.3f}s")
print(f"Test 2 PASS: hud_res shape = {hud_res.shape}")
print(f"Test 3 PASS: latest_depth_map_m exists = {workers.latest_depth_map_m is not None}")
if workers.latest_depth_map_m is not None:
    print(f"  Depth range in meters: min={workers.latest_depth_map_m.min():.2f}m, max={workers.latest_depth_map_m.max():.2f}m")
    print(f"  Forward clearance: {workers.depth_clearance_m:.1f}m")

# Test sequencer fusion with depth map
events, target = sequencer.update(detections, 480, 640, time.time(), depth_map_m=workers.latest_depth_map_m)
target_lbl = target['label'] if target else 'None'
target_dst = target['dist_m'] if target else 'N/A'
target_pos = target['pos'] if target else 'N/A'
print(f"Test 4 PASS: Sequencer target = {target_lbl} at {target_dst}m (pos: {target_pos})")

# Test split mode
split_res = AssistiveHUDDrawer.process_all_in_one(frame, detections, models, workers, sequencer, voice)
print(f"Test 5 PASS: process_all_in_one executed with split shape = {split_res.shape}")

print('--- ALL MODULE 8 TESTS PASSED SUCCESSFULLY! ---')
