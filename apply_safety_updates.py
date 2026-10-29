# -*- coding: utf-8 -*-
"""
Updater for build_index_html.py to implement:
- Dynamic Moving Hazards (Vehicles up to 6.0m with 3.5-4.5s lead time to dodge)
- Approaching Pedestrians (up to 4.0m with 2.5-3.5s lead time)
- Stationary / Stable Obstacles (Alert ONLY at 0.9m critical 1-step buffer, silent beyond 0.9m)
"""

with open(r'D:\Blind_SMart_Glasses\build_index_html.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace detection and tracking logic in detectFrameObjects
old_tracking_block = """            const olderPoint = track.history.find(pt => (now - pt.time) >= 900);
            if (olderPoint) {
              const dt = (now - olderPoint.time) / 1000.0;
              const netDisplacement = olderPoint.dist - track.emaDist;
              const v = netDisplacement / dt;
              track.sustainedVelocity = v;

              // Rigorous approach criteria: sustained velocity > 0.45 m/s & net approach >= 0.40m
              if (netDisplacement >= 0.40 && v >= 0.45 && track.emaDist <= 3.5) {
                track.isApproaching = true;
              } else {
                track.isApproaching = false;
              }
            } else {
              track.isApproaching = false;
            }"""

# In the template, curly braces are doubled: {{ and }}
old_tracking_block_in_template = """            const olderPoint = track.history.find(pt => (now - pt.time) >= 900);
            if (olderPoint) {{
              const dt = (now - olderPoint.time) / 1000.0;
              const netDisplacement = olderPoint.dist - track.emaDist;
              const v = netDisplacement / dt;
              track.sustainedVelocity = v;

              // Rigorous approach criteria: sustained velocity > 0.45 m/s & net approach >= 0.40m
              if (netDisplacement >= 0.40 && v >= 0.45 && track.emaDist <= 3.5) {{
                track.isApproaching = true;
              }} else {{
                track.isApproaching = false;
              }}
            }} else {{
              track.isApproaching = false;
            }}"""

new_tracking_block = """            const olderPoint = track.history.find(pt => (now - pt.time) >= 800);
            if (olderPoint) {{
              const dt = (now - olderPoint.time) / 1000.0;
              const netDisplacement = olderPoint.dist - track.emaDist;
              const v = netDisplacement / dt;
              track.sustainedVelocity = v;

              const isVehicle = ['car', 'bus', 'truck', 'motorcycle', 'bicycle'].includes(p.class);
              // Vehicles move fast: alert at long range (up to 6.0m) to provide 3.5-4.5s reaction lead time to dodge
              if (isVehicle && (v >= 0.25 || track.emaDist <= 5.5) && (netDisplacement >= 0.20 || track.emaDist <= 4.5)) {{
                track.isApproaching = true;
              }}
              // Approaching pedestrians: alert at up to 4.0m with 2.5-3.5s lead time
              else if (!isVehicle && v >= 0.35 && netDisplacement >= 0.30 && track.emaDist <= 4.0) {{
                track.isApproaching = true;
              }} else {{
                track.isApproaching = false;
              }}
            }} else {{
              track.isApproaching = false;
            }}"""

if old_tracking_block_in_template in code:
    code = code.replace(old_tracking_block_in_template, new_tracking_block)
    print("Replaced tracking block successfully!")
else:
    print("Tracking block string not found in template, searching...")

# Replace processBackgroundGuidance
old_guidance = """      // ONLY Speak Unprompted if TRUE Emergency Collision Threat Occurs
      const approachingThreat = objects.find(o => o.isApproaching && (o.label === 'person' || o.label === 'car' || o.label === 'bicycle'));
      if (approachingThreat) {{
        if (now - appState.lastCautionSpokenTime > 8000) {{
          appState.lastCautionSpokenTime = now;
          speak(`Caution! ${{approachingThreat.label}} approaching directly ahead at ${{approachingThreat.dist_m.toFixed(1)}} meters.`, {{ priority: true, cooldown: 8000 }});
        }}
        return;
      }}"""

new_guidance = """      // 1. DYNAMIC MOVING VEHICLE THREATS: Alert at long range (up to 6.0m) giving 3.5-4.5s lead time to dodge
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

      // 3. STATIONARY / STABLE OBSTACLES: Alert ONLY when user reaches 0.9m critical buffer!
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

if old_guidance in code:
    code = code.replace(old_guidance, new_guidance)
    print("Replaced guidance block successfully!")
else:
    print("Guidance block string not found in template, searching...")

# Replace updatePrioritySandbox
old_sandbox = """      let cueText = "";
      if (isApproaching || dist < 1.2) {{
        tierTag.textContent = "Tier 1: High Priority Hazard";
        tierTag.className = "priority-tier-tag urgent";
        cueText = `Caution! ${{entity.toUpperCase()}} ${{isApproaching ? 'approaching directly ahead' : 'at critical proximity'}}, ${{dist.toFixed(1)}} meters!`;
      }} else if (dist < 2.5) {{
        tierTag.textContent = "Tier 2: Secondary Caution";
        tierTag.className = "priority-tier-tag caution";
        cueText = `${{entity.charAt(0).toUpperCase() + entity.slice(1)}} ${{pos === 'center' ? 'directly ahead' : 'on your ' + pos}}, about ${{dist.toFixed(1)}} meters.`;
      }} else {{
        tierTag.textContent = "Tier 3: Routine Spatial Clearance";
        tierTag.className = "priority-tier-tag routine";
        cueText = `Forward path clearance is ${{dist.toFixed(1)}} meters.`;
      }}"""

new_sandbox = """      const isVehicle = ['car', 'bus', 'truck', 'motorcycle', 'bicycle'].includes(entity);
      let cueText = "";

      // 1. Moving Vehicle Hazard: Alert up to 6.0m (Reaction Lead Time: 3.5s to dodge)
      if (isVehicle && (isApproaching || dist <= 5.0)) {{
        tierTag.textContent = "Tier 1: High-Speed Vehicle Hazard (Lead Time: 3.5s)";
        tierTag.className = "priority-tier-tag urgent";
        cueText = `Warning! Approaching ${{entity.toUpperCase()}} ${{dist.toFixed(1)}} meters ahead! Step to the side immediately!`;
      }}
      // 2. Approaching Pedestrian: Alert up to 4.0m (Lead Time: 3.0s)
      else if (entity === 'person' && isApproaching && dist <= 4.0) {{
        tierTag.textContent = "Tier 1: Approaching Pedestrian (Lead Time: 3.0s)";
        tierTag.className = "priority-tier-tag urgent";
        cueText = `Caution! Person approaching directly ahead at ${{dist.toFixed(1)}} meters!`;
      }}
      // 3. Stationary / Stable Obstacle: Alert ONLY at 0.9m (1-Step Stopping Buffer)
      else if (!isApproaching && dist <= 0.95 && pos === 'center') {{
        tierTag.textContent = "Tier 2: Stationary Obstacle (1-Step Buffer: 0.9m)";
        tierTag.className = "priority-tier-tag caution";
        cueText = `Caution. ${{entity.charAt(0).toUpperCase() + entity.slice(1)}} directly ahead at 0.9 meters.`;
      }}
      // 4. Stable Obstacle beyond 0.9m: Quiet Monitoring
      else {{
        tierTag.textContent = "Tier 3: Stable Obstacle (Quiet — No Alarm until 0.9m)";
        tierTag.className = "priority-tier-tag routine";
        cueText = `[Silent Guidance] ${{entity.charAt(0).toUpperCase() + entity.slice(1)}} at ${{dist.toFixed(1)}}m. Path safe until 0.9m proximity.`;
      }}"""

if old_sandbox in code:
    code = code.replace(old_sandbox, new_sandbox)
    print("Replaced sandbox block successfully!")
else:
    print("Sandbox block string not found in template, searching...")

with open(r'D:\Blind_SMart_Glasses\build_index_html.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("build_index_html.py updated successfully.")
