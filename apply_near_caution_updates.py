# -*- coding: utf-8 -*-
"""
Applies calibrated perspective distance calculation and robust near proximity caution alerts
to build_index_html.py.
"""

with open(r'D:\Blind_SMart_Glasses\build_index_html.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update distance calculation in detectFrameObjects
old_dist_calc = """          const relArea = Math.max(0.001, (bw * bh) / (w * h));
          let rawDist = Math.max(0.4, Math.min(6.5, (1.28 / Math.sqrt(relArea))));"""

new_dist_calc = """          // Calibrated Perspective Pin-hole Distance Estimation
          const relH = Math.max(0.04, bh / h);
          const relW = Math.max(0.04, bw / w);
          const scaleMetric = Math.max(relH, relW * 0.72);
          let rawDist = Math.max(0.35, Math.min(6.5, (0.55 / scaleMetric)));"""

if old_dist_calc in code:
    code = code.replace(old_dist_calc, new_dist_calc)
    print("Replaced distance formula successfully!")
else:
    print("Could not find old_dist_calc in code!")

# 2. Update processBackgroundGuidance
old_guidance = """      // 3. STATIONARY / STABLE OBSTACLES: Alert ONLY when user reaches 0.9m critical buffer!
      // (Beyond 0.9m, remains completely silent so the user is never irritated)
      const closeStationary = objects.find(o => !o.isApproaching && o.pos === "CENTER" && o.dist_m <= 0.95);
      if (closeStationary) {
        if (now - appState.lastCautionSpokenTime > 6000) {
          appState.lastCautionSpokenTime = now;
          const alertMsg = `Caution. ${closeStationary.label.charAt(0).toUpperCase() + closeStationary.label.slice(1)} directly ahead at 0.9 meters.`;
          liveNarrativeText.textContent = `"${alertMsg}"`;
          speak(alertMsg, { priority: true, cooldown: 6000 });
        }
        return;
      }"""

# In the template curly braces are doubled: {{ and }}
old_guidance_in_template = """      // 3. STATIONARY / STABLE OBSTACLES: Alert ONLY when user reaches 0.9m critical buffer!
      // (Beyond 0.9m, remains completely silent so the user is never irritated)
      const closeStationary = objects.find(o => !o.isApproaching && o.pos === "CENTER" && o.dist_m <= 0.95);
      if (closeStationary) {{
        if (now - appState.lastCautionSpokenTime > 6000) {{
          appState.lastCautionSpokenTime = now;
          const alertMsg = `Caution. ${{closeStationary.label.charAt(0).toUpperCase() + closeStationary.label.slice(1)}} directly ahead at 0.9 meters.`;
          liveNarrativeText.textContent = `"${{alertMsg}}"`;
          speak(alertMsg, {{ priority: true, cooldown: 6000 }});
        }}
        return;
      }}"""

new_guidance = """      // 3. NEAR OBSTACLE & PERSON PROXIMITY CAUTION (Center corridor <= 1.35m or Flanks <= 0.95m)
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
      }}"""

if old_guidance_in_template in code:
    code = code.replace(old_guidance_in_template, new_guidance)
    print("Replaced guidance with robust near caution successfully!")
else:
    print("Could not find old_guidance_in_template in code!")

# 3. Update Bounding Box Drawing in render()
old_render_boxes = """        if (obj.isApproaching) {{
          col = '#ff3366';
          badge = `>> APPROACHING: ${{obj.label.toUpperCase()}} (${{obj.dist_m}}m) <<`;
          ctx.shadowColor = '#ff3366';
          ctx.shadowBlur = 10;
        }} else if (obj.label === 'person') {{
          col = '#00e5ff';
          badge = `STATIONARY PERSON [${{obj.dist_m}}m]`;
          ctx.shadowColor = '#00e5ff';
          ctx.shadowBlur = 6;
        }} else {{
          ctx.shadowBlur = 0;
        }}"""

new_render_boxes = """        if (obj.isApproaching) {{
          col = '#ff3366';
          badge = `>> APPROACHING: ${{obj.label.toUpperCase()}} (${{obj.dist_m}}m) <<`;
          ctx.shadowColor = '#ff3366';
          ctx.shadowBlur = 10;
        }} else if (obj.pos === 'CENTER' && obj.dist_m <= 0.85) {{
          col = '#ff3366';
          badge = `>> CRITICAL PROXIMITY: ${{obj.label.toUpperCase()}} (${{obj.dist_m}}m) <<`;
          ctx.shadowColor = '#ff3366';
          ctx.shadowBlur = 10;
        }} else if (obj.pos === 'CENTER' && obj.dist_m <= 1.35) {{
          col = '#ffb703';
          badge = `>> CAUTION CLOSE: ${{obj.label.toUpperCase()}} (${{obj.dist_m}}m) <<`;
          ctx.shadowColor = '#ffb703';
          ctx.shadowBlur = 8;
        }} else if (obj.label === 'person') {{
          col = '#00e5ff';
          badge = `PERSON [${{obj.dist_m}}m | ${{obj.pos}}]`;
          ctx.shadowColor = '#00e5ff';
          ctx.shadowBlur = 6;
        }} else {{
          ctx.shadowBlur = 0;
        }}"""

if old_render_boxes in code:
    code = code.replace(old_render_boxes, new_render_boxes)
    print("Replaced render boxes successfully!")
else:
    print("Could not find old_render_boxes in code!")

with open(r'D:\Blind_SMart_Glasses\build_index_html.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved build_index_html.py successfully!")
