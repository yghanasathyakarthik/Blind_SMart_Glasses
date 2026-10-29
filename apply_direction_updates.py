# -*- coding: utf-8 -*-
"""
Applies Intelligent Directional Evasion Guidance to build_index_html.py:
1. Calculates optimal safe bypass direction (LEFT, RIGHT, BACK) based on sector clearances
2. Tells the blind user exactly which direction to step / move during caution and emergency alerts
3. Visual pulsing evasion banner and arrow on HUD + Telemetry sector
4. Voice AI Assistant handles "Which direction to move?" queries
"""

with open(r'D:\Blind_SMart_Glasses\build_index_html.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add Evasion Direction to Telemetry in HTML
old_telemetry = """          <!-- Telemetry Sectors -->
          <div class="telemetry-sectors">
            <div class="sector-item">
              <div class="sector-label">Left Corridor</div>
              <div class="sector-val safe" id="valLeft">CLEAR</div>
            </div>
            <div class="sector-item">
              <div class="sector-label">Center Target</div>
              <div class="sector-val safe" id="valCenter">CLEAR</div>
            </div>
            <div class="sector-item">
              <div class="sector-label">Right Flank</div>
              <div class="sector-val safe" id="valRight">CLEAR</div>
            </div>
          </div>"""

new_telemetry = """          <!-- Telemetry Sectors with Dynamic Evasion Guidance -->
          <div class="telemetry-sectors">
            <div class="sector-item">
              <div class="sector-label">Left Corridor</div>
              <div class="sector-val safe" id="valLeft">CLEAR</div>
            </div>
            <div class="sector-item">
              <div class="sector-label">Center Target</div>
              <div class="sector-val safe" id="valCenter">CLEAR</div>
            </div>
            <div class="sector-item">
              <div class="sector-label">Right Flank</div>
              <div class="sector-val safe" id="valRight">CLEAR</div>
            </div>
            <div class="sector-item" style="border-color: var(--cyan-neon);">
              <div class="sector-label">Safe Evasion Direction</div>
              <div class="sector-val safe" id="valEvasion">FORWARD CLEAR</div>
            </div>
          </div>"""

if old_telemetry in code:
    code = code.replace(old_telemetry, new_telemetry)
    print("Replaced telemetry sectors HTML successfully!")
else:
    print("Could not find old_telemetry in code!")

# 2. Add quick prompt chip for "Which direction to move?"
old_chips = """            <span class="quick-chip" onclick="askAssistant('Where is my mouse or phone?')">&#128421; "Where is my mouse?"</span>"""
new_chips = """            <span class="quick-chip" onclick="askAssistant('Which direction should I move to avoid the obstacle?')">&#10145; "Which direction to move?"</span>
            <span class="quick-chip" onclick="askAssistant('Where is my mouse or phone?')">&#128421; "Where is my mouse?"</span>"""

if old_chips in code:
    code = code.replace(old_chips, new_chips)
    print("Added direction prompt chip successfully!")
else:
    print("Could not find old_chips in code!")

# 3. Add getEvasionVector function & integrate with processBackgroundGuidance
old_guidance_full = """    // Useful, Quiet Guidance (NO UNPROMPTED REPETITION)
    function processBackgroundGuidance(objects, centerClearance) {{
      const now = Date.now();

      // Update text in HUD silently
      if (objects.length === 0) {{
        liveNarrativeText.textContent = `"Forward walking path is unobstructed. Corridor offers ${{centerClearance.toFixed(1)}} meters of clearance."`;
      }} else {{
        const centerObjs = objects.filter(o => o.pos === "CENTER");
        if (centerObjs.length > 0) {{
          liveNarrativeText.textContent = `"Obstacle in center: ${{centerObjs[0].label}} at ${{centerObjs[0].dist_m.toFixed(1)}} meters."`;
        }} else {{
          liveNarrativeText.textContent = `"Forward corridor clear for ${{centerClearance.toFixed(1)}} meters. Objects present on periphery."`;
        }}
      }}

      // 1. DYNAMIC MOVING VEHICLE THREATS: Alert at long range (up to 6.0m) giving 3.5-4.5s lead time to dodge
      const vehicleThreat = objects.find(o => ['car', 'bus', 'truck', 'motorcycle', 'bicycle'].includes(o.label) && (o.isApproaching || o.dist_m <= 5.0));
      if (vehicleThreat) {{
        if (now - appState.lastCautionSpokenTime > 5000) {{
          appState.lastCautionSpokenTime = now;
          const alertMsg = `Warning! ${{vehicleThreat.label.toUpperCase()}} approaching at ${{vehicleThreat.dist_m.toFixed(1)}} meters! Step to the side immediately!`;
          liveNarrativeText.textContent = `"${{alertMsg}}"`;
          speak(alertMsg, {{ priority: true, interrupt: true, cooldown: 5000 }});
        }}
        return;
      }}

      // 2. APPROACHING PEDESTRIANS: Alert up to 4.0m directly ahead (2.5-3.5s lead time)
      const personThreat = objects.find(o => o.label === 'person' && o.isApproaching && o.dist_m <= 4.0);
      if (personThreat) {{
        if (now - appState.lastCautionSpokenTime > 6000) {{
          appState.lastCautionSpokenTime = now;
          const alertMsg = `Caution! Person approaching directly ahead at ${{personThreat.dist_m.toFixed(1)}} meters.`;
          liveNarrativeText.textContent = `"${{alertMsg}}"`;
          speak(alertMsg, {{ priority: true, cooldown: 6000 }});
        }}
        return;
      }}

      // 3. NEAR OBSTACLE & PERSON PROXIMITY CAUTION (Center corridor <= 1.35m or Flanks <= 0.95m)
      const nearCenterObstacle = objects.find(o => o.pos === "CENTER" && o.dist_m <= 1.35);
      const nearFlankObstacle = objects.find(o => (o.pos === "LEFT" || o.pos === "RIGHT") && o.dist_m <= 0.95);

      if (nearCenterObstacle) {{
        const obsLabel = nearCenterObstacle.label.charAt(0).toUpperCase() + nearCenterObstacle.label.slice(1);
        const distStr = nearCenterObstacle.dist_m.toFixed(1);
        let alertMsg = "";
        
        if (nearCenterObstacle.dist_m <= 0.85) {{
          alertMsg = `Caution! ${{obsLabel}} very close directly ahead at ${{distStr}} meters!`;
        }} else {{
          alertMsg = `Caution. ${{obsLabel}} directly ahead at ${{distStr}} meters.`;
        }}
        
        liveNarrativeText.textContent = `"${{alertMsg}}"`;

        // Prompt alert: trigger when entering near proximity
        const alertKey = `${{nearCenterObstacle.label}}_${{Math.round(nearCenterObstacle.dist_m * 2)}}`;
        if (appState.lastAlertKey !== alertKey && (now - appState.lastCautionSpokenTime > 3800)) {{
          appState.lastCautionSpokenTime = now;
          appState.lastAlertKey = alertKey;
          speak(alertMsg, {{ priority: true, cooldown: 3800 }});
        }}
        return;
      }} else if (nearFlankObstacle) {{
        const obsLabel = nearFlankObstacle.label.charAt(0).toUpperCase() + nearFlankObstacle.label.slice(1);
        const alertMsg = `Notice: ${{obsLabel}} close on your ${{nearFlankObstacle.pos.toLowerCase()}} at ${{nearFlankObstacle.dist_m.toFixed(1)}} meters.`;
        liveNarrativeText.textContent = `"${{alertMsg}}"`;

        const alertKey = `${{nearFlankObstacle.label}}_flank`;
        if (appState.lastAlertKey !== alertKey && (now - appState.lastCautionSpokenTime > 4500)) {{
          appState.lastCautionSpokenTime = now;
          appState.lastAlertKey = alertKey;
          speak(alertMsg, {{ priority: false, cooldown: 4500 }});
        }}
        return;
      }} else {{
        appState.lastAlertKey = null;
      }}

      // In Walking Guide mode, speak only every 20 seconds
      if (appState.audioMode === 'walk_guide' && (now - appState.lastRoutineSpokenTime > 20000)) {{
        appState.lastRoutineSpokenTime = now;
        speak(liveNarrativeText.textContent.replace(/"/g, ''), {{ priority: false, cooldown: 20000 }});
      }}
    }}"""

new_guidance_full = """    // Directional Evasion Vector Calculator (Determines which way blind user should move)
    function calculateEvasionVector(leftClearance, rightClearance) {{
      if (rightClearance >= 2.0 && leftClearance >= 2.0) {{
        return {{ dir: "RIGHT", text: "Step to your right to bypass.", badge: "➔ STEP RIGHT", phrase: "move right" }};
      }} else if (rightClearance > leftClearance && rightClearance >= 1.3) {{
        return {{ dir: "RIGHT", text: `Step right! Right path is open for ${{rightClearance.toFixed(1)}} meters.`, badge: `➔ STEP RIGHT (${{rightClearance.toFixed(1)}}m)`, phrase: "move right" }};
      }} else if (leftClearance > rightClearance && leftClearance >= 1.3) {{
        return {{ dir: "LEFT", text: `Step left! Left path is open for ${{leftClearance.toFixed(1)}} meters.`, badge: `← STEP LEFT (${{leftClearance.toFixed(1)}}m)`, phrase: "move left" }};
      }} else if (rightClearance >= 1.0) {{
        return {{ dir: "RIGHT", text: "Step to your right to bypass.", badge: "➔ STEP RIGHT", phrase: "move right" }};
      }} else if (leftClearance >= 1.0) {{
        return {{ dir: "LEFT", text: "Step to your left to bypass.", badge: "← STEP LEFT", phrase: "move left" }};
      }} else {{
        return {{ dir: "BACK", text: "Halt! Both sides blocked — step backward.", badge: "⬇ STEP BACK", phrase: "step backward" }};
      }}
    }}

    // Useful, Quiet Guidance with Directional Evasion (TELLS USER WHICH DIRECTION TO MOVE)
    function processBackgroundGuidance(objects, centerClearance, leftClearance = 5.0, rightClearance = 5.0) {{
      const now = Date.now();
      const valEvasion = document.getElementById('valEvasion');

      // Calculate directional evasion guidance
      const evasion = calculateEvasionVector(leftClearance, rightClearance);
      appState.currentEvasion = evasion;

      // Update text in HUD silently
      if (objects.length === 0) {{
        liveNarrativeText.textContent = `"Forward walking path is unobstructed. Corridor offers ${{centerClearance.toFixed(1)}} meters of clearance."`;
        if (valEvasion) valEvasion.textContent = "FORWARD CLEAR";
      }} else {{
        const centerObjs = objects.filter(o => o.pos === "CENTER");
        if (centerObjs.length > 0) {{
          liveNarrativeText.textContent = `"Obstacle in center: ${{centerObjs[0].label}} at ${{centerObjs[0].dist_m.toFixed(1)}} meters. Safe route: ${{evasion.phrase}}."`;
          if (valEvasion) valEvasion.textContent = evasion.badge;
        }} else {{
          liveNarrativeText.textContent = `"Forward corridor clear for ${{centerClearance.toFixed(1)}} meters. Objects present on periphery."`;
          if (valEvasion) valEvasion.textContent = "FORWARD CLEAR";
        }}
      }}

      // 1. DYNAMIC MOVING VEHICLE THREATS: Alert at long range (up to 6.0m) + DIRECTION TO DODGE!
      const vehicleThreat = objects.find(o => ['car', 'bus', 'truck', 'motorcycle', 'bicycle'].includes(o.label) && (o.isApproaching || o.dist_m <= 5.0));
      if (vehicleThreat) {{
        if (now - appState.lastCautionSpokenTime > 5000) {{
          appState.lastCautionSpokenTime = now;
          const alertMsg = `Warning! ${{vehicleThreat.label.toUpperCase()}} approaching at ${{vehicleThreat.dist_m.toFixed(1)}} meters! ${{evasion.text}}`;
          liveNarrativeText.textContent = `"${{alertMsg}}"`;
          if (valEvasion) valEvasion.textContent = `>> ${{evasion.badge}} <<`;
          speak(alertMsg, {{ priority: true, interrupt: true, cooldown: 5000 }});
        }}
        return;
      }}

      // 2. APPROACHING PEDESTRIANS: Alert up to 4.0m directly ahead + DIRECTION TO MOVE!
      const personThreat = objects.find(o => o.label === 'person' && o.isApproaching && o.dist_m <= 4.0);
      if (personThreat) {{
        if (now - appState.lastCautionSpokenTime > 5500) {{
          appState.lastCautionSpokenTime = now;
          const alertMsg = `Caution! Person approaching directly ahead at ${{personThreat.dist_m.toFixed(1)}} meters. ${{evasion.text}}`;
          liveNarrativeText.textContent = `"${{alertMsg}}"`;
          if (valEvasion) valEvasion.textContent = evasion.badge;
          speak(alertMsg, {{ priority: true, cooldown: 5500 }});
        }}
        return;
      }}

      // 3. NEAR OBSTACLE PROXIMITY CAUTION (Center corridor <= 1.35m) + DIRECTION TO BYPASS!
      const nearCenterObstacle = objects.find(o => o.pos === "CENTER" && o.dist_m <= 1.35);
      const nearFlankObstacle = objects.find(o => (o.pos === "LEFT" || o.pos === "RIGHT") && o.dist_m <= 0.95);

      if (nearCenterObstacle) {{
        const obsLabel = nearCenterObstacle.label.charAt(0).toUpperCase() + nearCenterObstacle.label.slice(1);
        const distStr = nearCenterObstacle.dist_m.toFixed(1);
        let alertMsg = "";
        
        if (nearCenterObstacle.dist_m <= 0.85) {{
          alertMsg = `Caution! ${{obsLabel}} very close directly ahead at ${{distStr}} meters! ${{evasion.text}}`;
        }} else {{
          alertMsg = `Caution. ${{obsLabel}} directly ahead at ${{distStr}} meters. ${{evasion.text}}`;
        }}
        
        liveNarrativeText.textContent = `"${{alertMsg}}"`;
        if (valEvasion) valEvasion.textContent = evasion.badge;

        const alertKey = `${{nearCenterObstacle.label}}_${{Math.round(nearCenterObstacle.dist_m * 2)}}`;
        if (appState.lastAlertKey !== alertKey && (now - appState.lastCautionSpokenTime > 3800)) {{
          appState.lastCautionSpokenTime = now;
          appState.lastAlertKey = alertKey;
          speak(alertMsg, {{ priority: true, cooldown: 3800 }});
        }}
        return;
      }} else if (nearFlankObstacle) {{
        const obsLabel = nearFlankObstacle.label.charAt(0).toUpperCase() + nearFlankObstacle.label.slice(1);
        const flankEvasion = nearFlankObstacle.pos === "LEFT" ? "Move slightly to your right." : "Move slightly to your left.";
        const alertMsg = `Notice: ${{obsLabel}} close on your ${{nearFlankObstacle.pos.toLowerCase()}} at ${{nearFlankObstacle.dist_m.toFixed(1)}} meters. ${{flankEvasion}}`;
        liveNarrativeText.textContent = `"${{alertMsg}}"`;

        const alertKey = `${{nearFlankObstacle.label}}_flank`;
        if (appState.lastAlertKey !== alertKey && (now - appState.lastCautionSpokenTime > 4500)) {{
          appState.lastCautionSpokenTime = now;
          appState.lastAlertKey = alertKey;
          speak(alertMsg, {{ priority: false, cooldown: 4500 }});
        }}
        return;
      }} else {{
        appState.lastAlertKey = null;
      }}

      // In Walking Guide mode, speak periodically
      if (appState.audioMode === 'walk_guide' && (now - appState.lastRoutineSpokenTime > 20000)) {{
        appState.lastRoutineSpokenTime = now;
        speak(liveNarrativeText.textContent.replace(/"/g, ''), {{ priority: false, cooldown: 20000 }});
      }}
    }}"""

if old_guidance_full in code:
    code = code.replace(old_guidance_full, new_guidance_full)
    print("Replaced guidance with evasion guidance successfully!")
else:
    print("Could not find old_guidance_full in code!")

# 4. Update call in detectFrameObjects to pass leftMin and rightMin
old_call = "        processBackgroundGuidance(newObjects, centerMin);"
new_call = "        processBackgroundGuidance(newObjects, centerMin, leftMin, rightMin);"
if old_call in code:
    code = code.replace(old_call, new_call)
    print("Updated processBackgroundGuidance call with sector clearances!")
else:
    print("Could not find old_call in code!")

# 5. Update askAssistant to handle "which direction to move" / "which way to go"
old_nav_query = """      // 5. Walking Clearance & Spatial Obstacles
      else if (q.includes('can i walk') || q.includes('walk forward') || q.includes('path') || q.includes('clearance') || q.includes('safe to walk') || q.includes('obstacles')) {{"""

new_nav_query = """      // 5. Directional Evasion Guidance ("Which direction should I move?")
      else if (q.includes('which direction') || q.includes('which way') || q.includes('where to move') || q.includes('how to dodge') || q.includes('evasion') || q.includes('where to step') || q.includes('how to bypass')) {{
        const leftC = parseFloat(valLeft.textContent) || 5.0;
        const rightC = parseFloat(valRight.textContent) || 5.0;
        const evasion = calculateEvasionVector(leftC, rightC);
        if (centerObjs.length > 0) {{
          reply = `The central walking corridor is obstructed by a ${{centerObjs[0].label}} at ${{centerObjs[0].dist_m.toFixed(1)}} meters. ${{evasion.text}}`;
        }} else {{
          reply = `The forward walking path is completely open. If you wish to veer, ${{evasion.text}}`;
        }}
      }}
      // 5b. Walking Clearance & Spatial Obstacles
      else if (q.includes('can i walk') || q.includes('walk forward') || q.includes('path') || q.includes('clearance') || q.includes('safe to walk') || q.includes('obstacles')) {{"""

if old_nav_query in code:
    code = code.replace(old_nav_query, new_nav_query)
    print("Added direction answering to askAssistant successfully!")
else:
    print("Could not find old_nav_query in code!")

# 6. Draw Directional Evasion Banner on Canvas in render()
old_render_end = """      // Divider Line between Panes
      ctx.strokeStyle = 'rgba(0, 229, 255, 0.4)';"""

new_render_end = """      // Directional Evasion Banner on HUD when Caution is Active
      if (appState.currentEvasion && (valCenter.textContent !== 'CLEAR' && parseFloat(valCenter.textContent) <= 1.4)) {{
        const ev = appState.currentEvasion;
        ctx.fillStyle = 'rgba(0, 15, 30, 0.88)';
        ctx.strokeStyle = ev.dir === 'BACK' ? '#ff3366' : '#00e5ff';
        ctx.lineWidth = 2;
        const bW = halfW * 0.70;
        const bH = 34;
        const bX = (halfW - bW) / 2;
        const bY = h * 0.88;
        ctx.fillRect(bX, bY, bW, bH);
        ctx.strokeRect(bX, bY, bW, bH);

        ctx.fillStyle = ev.dir === 'BACK' ? '#ff3366' : '#00f0aa';
        ctx.font = 'bold 12px "JetBrains Mono", monospace';
        ctx.fillText(`EVASION ROUTE: ${{ev.badge}}`, bX + 16, bY + 22);
      }}

      // Divider Line between Panes
      ctx.strokeStyle = 'rgba(0, 229, 255, 0.4)';"""

if old_render_end in code:
    code = code.replace(old_render_end, new_render_end)
    print("Added evasion banner rendering on HUD canvas successfully!")
else:
    print("Could not find old_render_end in code!")

with open(r'D:\Blind_SMart_Glasses\build_index_html.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved build_index_html.py successfully!")
