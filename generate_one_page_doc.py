# -*- coding: utf-8 -*-
"""
generate_one_page_doc.py
Generates an executive 1-page summary Word document summarizing the complete v2.0 upgrade.
"""

import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

doc = Document()

# Set tight margins (0.5 inch all around) to fit exactly 1 page
sections = doc.sections
for s in sections:
    s.top_margin = Inches(0.45)
    s.bottom_margin = Inches(0.45)
    s.left_margin = Inches(0.55)
    s.right_margin = Inches(0.55)

# Styling palette
PRIMARY = RGBColor(0, 102, 204)       # Deep Azure
HEADING = RGBColor(15, 23, 42)        # Midnight Navy
TEXT = RGBColor(30, 41, 59)           # Charcoal Slate
SUBTEXT = RGBColor(100, 116, 139)     # Cool Gray
ACCENT_GREEN = RGBColor(16, 185, 129) # Emerald

# Header Title Block
p_title = doc.add_paragraph()
p_title.paragraph_format.space_before = Pt(0)
p_title.paragraph_format.space_after = Pt(2)
run_title = p_title.add_run("Smart Glasses Assistive Vision & Sighted AI Companion")
run_title.font.name = "Segoe UI"
run_title.font.size = Pt(16)
run_title.font.bold = True
run_title.font.color.rgb = PRIMARY

p_sub = doc.add_paragraph()
p_sub.paragraph_format.space_before = Pt(0)
p_sub.paragraph_format.space_after = Pt(8)
run_sub = p_sub.add_run("Executive v2.0 Engineering & Accessibility Upgrade Summary | Inspired by Meta & Apple AI Glasses")
run_sub.font.name = "Segoe UI"
run_sub.font.size = Pt(9.5)
run_sub.font.italic = True
run_sub.font.color.rgb = SUBTEXT

# Key Transformations Table
table = doc.add_table(rows=6, cols=2)
table.alignment = WD_TABLE_ALIGNMENT.CENTER
table.autofit = False

col_widths = [Inches(2.1), Inches(5.3)]

headers = [
    ("1. Clutter-Free Glassmorphic UI (5 Accessible Tabs)",
     "Eliminated the 10-screen vertical scroll. Divided into 5 top-level accessible views:\n"
     "• [Vision & Radar]: Real-time HUD, 360° radar, evasion vector, and animated Meta Orb assistant.\n"
     "• [Daily Blind Tools]: Currency scanner (USD/INR/EUR), wardrobe colorimeter, lux meter, SOS beacon.\n"
     "• [Slow Book Reader]: Multi-sentence OCR reader designed specifically for slow, comfortable comprehension.\n"
     "• [Task & Memory Hub]: Persistent checklist and spatial item memory (e.g. 'Where is my cane?').\n"
     "• [PhD Research Studio]: Houses all 8 faculty modules (M1-M8), BDD100K, Places365 & math formulas."),
    
    ("2. Fixed Pothole / False Hazard Anomaly",
     "Root Cause: Dark clothing / shadows in webcam feeds triggered floor cavity heuristics.\n"
     "Fix: Strict human/indoor occlusion guard ('hasPersonOrIndoor'). Road hazards are restricted strictly to outdoor road navigation and require high background asphalt luminance (>75) and dense cavity contrast (>85)."),
    
    ("3. Articulate Slow Book & Document Reader",
     "Addressed user requirement: 'if asked to read any book it need to read some slowly to understand'.\n"
     "• Splits text into coherent sentences with real-time visual highlight.\n"
     "• Paced articulation at 0.82x - 0.88x speech rate with natural 450ms breath pauses between sentences.\n"
     "• Complete voice & touch playback controls (Play, Pause, Resume, Stop, Next, Previous)."),
    
    ("4. Task & Spatial Memory Hub for the Blind",
     "Addressed user requirement: 'blind people can do any tasks with task remember every task need to be done'.\n"
     "• Voice Task Checklist: 'Add task buy medicine', 'Mark task done', 'What are my tasks?'.\n"
     "• Spatial Item Memory: Stores where items were left ('Remember my cane is at the front door'). Retrieve instantly by asking 'Where did I leave my cane?' or 'Where is my wallet?'."),
    
    ("5. Autonomous Traffic Signals & Crosswalk AI",
     "• Autonomous color classifier continuously crops traffic signal bounding boxes.\n"
     "• Proactively announces without prompt: 'Traffic light is RED. Halt at curb.'\n"
     "• Detects transition to GREEN: 'Traffic light turned GREEN! Crosswalk clear, you may proceed.'"),
    
    ("6. Multi-Turn Conversational Navigation & Echo Guard",
     "• Destination Confirmation: Voice assistant verifies place, prompts for neighborhood/district area, confirms with the user, and initiates walking route only upon user confirmation.\n"
     "• Echo Guard: Speech recognition mutes during TTS output so the glasses never listen to their own voice.\n"
     "• Pedestrian & Hazard Priority: Stationary conversation partners remain quiet; approaching threats trigger early directional evasion ('Car approaching, move right').")
]

for row_idx, (col1_txt, col2_txt) in enumerate(headers):
    row = table.rows[row_idx]
    
    # Cell 1
    c1 = row.cells[0]
    c1.width = col_widths[0]
    p1 = c1.paragraphs[0]
    p1.paragraph_format.space_before = Pt(2)
    p1.paragraph_format.space_after = Pt(2)
    r1 = p1.add_run(col1_txt)
    r1.font.name = "Segoe UI"
    r1.font.size = Pt(8.5)
    r1.font.bold = True
    r1.font.color.rgb = HEADING
    
    # Cell 2
    c2 = row.cells[1]
    c2.width = col_widths[1]
    p2 = c2.paragraphs[0]
    p2.paragraph_format.space_before = Pt(2)
    p2.paragraph_format.space_after = Pt(2)
    r2 = p2.add_run(col2_txt)
    r2.font.name = "Segoe UI"
    r2.font.size = Pt(8.0)
    r2.font.color.rgb = TEXT
    
    # Add subtle background shading to alternating rows
    if row_idx % 2 == 0:
        shading = parse_xml(r'<w:shd {} w:fill="F1F5F9"/>'.format(nsdecls('w')))
        c1._tc.get_or_add_tcPr().append(shading)
        shading2 = parse_xml(r'<w:shd {} w:fill="F8FAFC"/>'.format(nsdecls('w')))
        c2._tc.get_or_add_tcPr().append(shading2)

# Footer Note
p_foot = doc.add_paragraph()
p_foot.paragraph_format.space_before = Pt(6)
p_foot.paragraph_format.space_after = Pt(0)
r_foot = p_foot.add_run("Deployment Status: Client-side single bundle (0 cloud cost). Live at https://smartevaluationglasses.netlify.app/ | GitHub tracked on branch main.")
r_foot.font.name = "Segoe UI"
r_foot.font.size = Pt(7.5)
r_foot.font.italic = True
r_foot.font.color.rgb = SUBTEXT

output_path = r"D:\Blind_SMart_Glasses\Smart_Glasses_Assistive_Vision_Upgrade_Summary.docx"
doc.save(output_path)
print(f"Successfully generated 1-page summary docx at: {output_path}")
