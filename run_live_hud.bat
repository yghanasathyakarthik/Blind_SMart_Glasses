@echo off
title Smart Glasses Assistive Vision HUD
cd /d "D:\Blind_SMart_Glasses"
echo ========================================================
echo  Launching Smart Glasses Assistive Vision Live HUD
echo ========================================================
echo Camera: Default Camera (Index 0)
echo To use your phone camera via DroidCam or IP Webcam, run:
echo   python smart_glasses_live_hud.py --camera "http://<PHONE_IP>:8080/video"
echo ========================================================
python smart_glasses_live_hud.py
pause
