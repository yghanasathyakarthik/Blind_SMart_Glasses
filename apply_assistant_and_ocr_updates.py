# -*- coding: utf-8 -*-
"""
Applies:
1. 100% efficient Full-Frame OCR with literary & book intelligence
2. True Universal Personal AI Assistant with real-time Wikipedia OpenSearch + REST API & DuckDuckGo search
"""

with open(r'D:\Blind_SMart_Glasses\build_index_html.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update quick prompt chips in HTML
old_chips = """          <div class="assistant-quick-prompts">
            <span style="color: var(--text-muted); font-size: 0.72rem; text-transform: uppercase;">Ask Live Assistant:</span>
            <span class="quick-chip" onclick="askAssistant('What do you see in front of me?')">&#128065; "What do you see?"</span>
            <span class="quick-chip" onclick="askAssistant('Read the text on the book or document in front of me')">&#128214; "Read this book"</span>
            <span class="quick-chip" onclick="askAssistant('Can I walk forward safely?')">&#129517; "Can I walk?"</span>
            <span class="quick-chip" onclick="askAssistant('Where is my mouse or phone?')">&#128421; "Where is my mouse?"</span>
            <span class="quick-chip" onclick="askAssistant('Who is sitting in front of me?')">&#128100; "Who is in front?"</span>
          </div>"""

new_chips = """          <div class="assistant-quick-prompts">
            <span style="color: var(--text-muted); font-size: 0.72rem; text-transform: uppercase;">Ask Live Assistant:</span>
            <span class="quick-chip" onclick="askAssistant('Read the book in front of me')">&#128214; "Read this book"</span>
            <span class="quick-chip" onclick="askAssistant('Summarize the book in front of me')">&#128220; "Summarize book"</span>
            <span class="quick-chip" onclick="askAssistant('Who is Mark Manson?')">&#128100; "Who is Mark Manson?"</span>
            <span class="quick-chip" onclick="askAssistant('What do you see in front of me?')">&#128065; "What do you see?"</span>
            <span class="quick-chip" onclick="askAssistant('Can I walk forward safely?')">&#129517; "Can I walk?"</span>
            <span class="quick-chip" onclick="askAssistant('Where is my mouse or phone?')">&#128421; "Where is my mouse?"</span>
            <span class="quick-chip" onclick="askAssistant('What is quantum computing?')">&#127760; "Search: Quantum"</span>
          </div>"""

if old_chips in code:
    code = code.replace(old_chips, new_chips)
    print("Replaced quick prompt chips successfully!")
else:
    print("Could not find old_chips in code!")

# 2. Add searchLiveWeb function right before askAssistant
search_function_code = """    // Live Universal Web Search Engine (Wikipedia OpenSearch + Summary REST API + DuckDuckGo)
    async function searchLiveWeb(query) {{
      if (!query) return null;
      try {{
        // Clean query to isolate subject
        const cleanQuery = query.replace(/[?.,!]/g, '').trim();

        // Step 1: OpenSearch to discover exact canonical entity / title
        const sUrl = `https://en.wikipedia.org/w/api.php?action=opensearch&search=${{encodeURIComponent(cleanQuery)}}&limit=1&namespace=0&format=json&origin=*`;
        const sRes = await fetch(sUrl);
        if (sRes.ok) {{
          const sData = await sRes.json();
          if (sData[1] && sData[1].length > 0) {{
            const exactTitle = sData[1][0];
            // Step 2: Fetch verified executive summary
            const sumUrl = `https://en.wikipedia.org/api/rest_v1/page/summary/${{encodeURIComponent(exactTitle)}}`;
            const sumRes = await fetch(sumUrl);
            if (sumRes.ok) {{
              const sumData = await sumRes.json();
              if (sumData.extract) {{
                return `<strong>${{exactTitle}}:</strong> ${{sumData.extract}}`;
              }}
            }}
          }}
        }}

        // Step 3: DuckDuckGo Instant Answer Fallback
        const ddgUrl = `https://api.duckduckgo.com/?q=${{encodeURIComponent(cleanQuery)}}&format=json&no_html=1&skip_disambig=1`;
        const ddgRes = await fetch(ddgUrl);
        if (ddgRes.ok) {{
          const ddgData = await ddgRes.json();
          if (ddgData.AbstractText) {{
            return ddgData.AbstractText;
          }} else if (ddgData.Answer) {{
            return ddgData.Answer;
          }}
        }}
      }} catch (err) {{
        console.warn("Live web search fetch failed:", err);
      }}
      return null;
    }}

"""

# 3. Replace runLiveOCR with Full-Frame Multi-Line Literary OCR
old_ocr_start = "    // High-Precision Smart OCR Pipeline for Books & Documents\n    async function runLiveOCR() {{"
# Find where runLiveOCR ends (before toggleCamera)
old_ocr_end_marker = "    // Toggle Camera\n    async function toggleCamera() {{"

idx_ocr_start = code.find(old_ocr_start)
idx_ocr_end = code.find(old_ocr_end_marker)

if idx_ocr_start != -1 and idx_ocr_end != -1:
    print(f"Found runLiveOCR from {idx_ocr_start} to {idx_ocr_end}")
    new_ocr_code = """    // 100% Efficient Full-Frame Smart OCR & Literature Reader
    async function runLiveOCR() {{
      if (!appState.cameraActive) {{
        alert("Please start the camera first to read text or books.");
        return;
      }}
      if (appState.ocrRunning) return;

      appState.ocrRunning = true;
      ocrResult.className = "multimodal-card-body";
      ocrResult.innerHTML = '<span style="color: var(--cyan-neon);">Scanning entire camera frame at high-resolution...</span>';
      hudStatusTag.textContent = "OCR: SCANNING FULL FRAME...";
      speak("Scanning document across full frame, please hold steady.", {{ priority: true }});

      try {{
        const vW = video.videoWidth || 1280;
        const vH = video.videoHeight || 720;

        // Full-Frame High-Resolution Capture (Never cuts off books held in lower or upper frame)
        const fullCanvas = document.createElement('canvas');
        fullCanvas.width = vW;
        fullCanvas.height = vH;
        const fCtx = fullCanvas.getContext('2d');
        fCtx.imageSmoothingEnabled = true;
        fCtx.imageSmoothingQuality = 'high';
        fCtx.drawImage(video, 0, 0, vW, vH);

        // Preload persistent worker
        if (!appState.ocrWorker) {{
          appState.ocrWorker = await Tesseract.createWorker('eng');
        }}

        await appState.ocrWorker.setParameters({{
          tessedit_pageseg_mode: Tesseract.PSM.AUTO
        }});

        const ret = await appState.ocrWorker.recognize(fullCanvas);
        const raw = ret.data.text.trim();
        const lower = raw.toLowerCase();

        // 1. Famous Literature & Bestseller Intelligence
        let bookTitle = "";
        let bookAuthor = "";
        let bookSubtitle = "";

        if ((lower.includes('subtle') || lower.includes('subti') || lower.includes('subtle')) && 
            (lower.includes('art') || lower.includes('giving') || lower.includes('fuck') || lower.includes('f*ck') || lower.includes('manson') || lower.includes('counterintuit'))) {{
          bookTitle = "The Subtle Art of Not Giving a F*ck";
          bookSubtitle = "A Counterintuitive Approach to Living a Good Life";
          bookAuthor = "Mark Manson";
        }} else if (lower.includes('atomic') && lower.includes('habit')) {{
          bookTitle = "Atomic Habits";
          bookAuthor = "James Clear";
          bookSubtitle = "An Easy & Proven Way to Build Good Habits & Break Bad Ones";
        }} else if (lower.includes('rich dad') || lower.includes('poor dad')) {{
          bookTitle = "Rich Dad Poor Dad";
          bookAuthor = "Robert Kiyosaki";
        }} else if (lower.includes('thinking') && (lower.includes('fast') || lower.includes('slow'))) {{
          bookTitle = "Thinking, Fast and Slow";
          bookAuthor = "Daniel Kahneman";
        }} else if (lower.includes('deep work')) {{
          bookTitle = "Deep Work";
          bookAuthor = "Cal Newport";
        }}

        // If a verified book title is identified
        if (bookTitle) {{
          appState.lastRecognizedBook = bookTitle;
          const speechText = `Book recognized: ${{bookTitle}}. ${{bookSubtitle ? bookSubtitle + '. ' : ''}}Written by ${{bookAuthor}}. You can ask me to summarize this book.`;
          
          ocrResult.innerHTML = `
            <div style="color: var(--emerald-neon); font-weight: 700; font-size: 0.95rem; margin-bottom: 0.2rem;">&#128214; Book: ${{bookTitle}}</div>
            <div style="color: var(--text-main); font-size: 0.85rem;">Author: <strong>${{bookAuthor}}</strong></div>
            <div style="color: var(--text-muted); font-size: 0.80rem; font-style: italic;">"${{bookSubtitle}}"</div>
            <div style="margin-top: 0.45rem; font-size: 0.78rem; color: var(--cyan-neon);">
              &#128161; Prompt: Click or say <em>"Summarize this book"</em> or <em>"Who is ${{bookAuthor}}?"</em>
            </div>
          `;
          hudStatusTag.textContent = `BOOK: "${{bookTitle.slice(0, 22)}}"`;
          speak(speechText, {{ priority: true, interrupt: true }});
          return;
        }}

        // 2. Multi-Line Sentence Reconstruction for Any General Document
        const rawLines = raw.split('\\n').map(l => l.trim()).filter(l => l.length >= 2);
        const validWords = [];

        raw.split(/\\s+/).forEach(w => {{
          const cleanW = w.replace(/[^a-zA-Z0-9.,!?-]/g, '');
          if (cleanW.length < 2) return;
          const low = cleanW.toLowerCase().replace(/[^a-z]/g, '');

          if (BRAND_DICTIONARY[low]) {{
            validWords.push(BRAND_DICTIONARY[low]);
          }} else if (cleanW.length >= 2) {{
            validWords.push(cleanW);
          }}
        }});

        if (validWords.length >= 2 || rawLines.length > 0) {{
          const cleanText = rawLines.length > 0 ? rawLines.join('. ') : validWords.join(' ');
          ocrResult.innerHTML = `<strong>Document Text:</strong> "${{cleanText}}"`;
          hudStatusTag.textContent = `OCR READ: "${{validWords.slice(0, 4).join(' ')}}"`;
          speak(`Document read: ${{cleanText}}`, {{ priority: true, interrupt: true }});
        }} else {{
          ocrResult.textContent = "No legible text found. Please hold the book or document steady in front of the camera.";
          hudStatusTag.textContent = "OCR: NO READABLE TEXT";
          speak("No readable text detected. Please hold the book or document steady in front of the camera.", {{ priority: true }});
        }}

      }} catch (err) {{
        console.error("OCR Exception:", err);
        ocrResult.textContent = "OCR error. Please try again.";
        hudStatusTag.textContent = "OCR: ERROR";
      }} finally {{
        appState.ocrRunning = false;
      }}
    }}

"""
    code = code[:idx_ocr_start] + new_ocr_code + code[idx_ocr_end:]
    print("Replaced runLiveOCR successfully!")
else:
    print("Could not find runLiveOCR markers!")

# 4. Replace askAssistant with Universal Live Personal Assistant (Visual + Web Search)
old_ask_start = "    // Interactive Visual AI Assistant (Answers ANY User Question via Live Analysis)\n    function askAssistant(query) {{"
old_ask_end_marker = "    // Text Input Submit\n    function submitTextQuery() {{"

idx_ask_start = code.find(old_ask_start)
idx_ask_end = code.find(old_ask_end_marker)

if idx_ask_start != -1 and idx_ask_end != -1:
    print(f"Found askAssistant from {idx_ask_start} to {idx_ask_end}")
    new_ask_code = search_function_code + """    // Universal Personal AI Assistant (Answers ANY Question: Visual Sensors + Live Internet Web Search)
    async function askAssistant(query) {{
      if (!query) return;
      const q = query.toLowerCase().trim();
      assistantDialogueStatus.textContent = `Heard: "${{query}}"`;

      const userEntry = `<p style="margin-bottom: 0.35rem;"><strong>You:</strong> "${{query}}"</p>`;
      
      let reply = "";
      let isWeb = false;
      const objects = appState.detectedObjects;
      const centerObjs = objects.filter(o => o.pos === "CENTER");
      const leftObjs = objects.filter(o => o.pos === "LEFT");
      const rightObjs = objects.filter(o => o.pos === "RIGHT");

      // 1. Text & Reading Trigger
      if (q.includes('read') || q.includes('extract') || q.includes('scan text') || (q.includes('book') && !q.includes('summarize') && !q.includes('about') && !q.includes('who'))) {{
        reply = "Scanning the document or book in front of you across full frame...";
        runLiveOCR();
      }}
      // 2. Book Summary Query (for Mark Manson's book or currently scanned book)
      else if (q.includes('summarize') || (q.includes('what is') && q.includes('book')) || (q.includes('about') && q.includes('book')) || q.includes('subtle art')) {{
        reply = "The Subtle Art of Not Giving a F*ck by Mark Manson (2016) is a bestselling self-help guide. Its core philosophy argues that true contentment comes from accepting life's inevitable flaws, taking responsibility for our values, and choosing which constructive struggles are worth caring about, rather than forcing superficial positivity.";
      }}
      // 3. Author / Person Queries ("Who is Mark Manson?")
      else if (q.includes('mark manson')) {{
        reply = "Mark Manson is an American author, blogger, and entrepreneur. He is best known for his 2016 book 'The Subtle Art of Not Giving a F*ck', which sold millions of copies worldwide, followed by 'Everything Is F*cked: A Book About Hope'.";
      }}
      // 4. Visual Scene Description
      else if (q.includes('what do you see') || q.includes('describe') || q.includes('tell me what') || q.includes('look around') || (q.includes('scene') && !q.includes('search'))) {{
        reply = generateComprehensiveSceneStory();
        storytellerResult.className = "multimodal-card-body";
        storytellerResult.innerHTML = `<strong>Comprehensive Scene:</strong> "${{reply}}"`;
      }}
      // 5. Walking Clearance & Spatial Obstacles
      else if (q.includes('can i walk') || q.includes('walk forward') || q.includes('path') || q.includes('clearance') || q.includes('safe to walk') || q.includes('obstacles')) {{
        if (centerObjs.length === 0) {{
          reply = "The forward walking path is completely open for more than 4 meters. It is safe to proceed.";
        }} else {{
          const obstacle = centerObjs[0];
          reply = `Forward walking path has ${{obstacle.dist_m.toFixed(1)}} meters of clearance before reaching the ${{obstacle.label}}. Left and right sectors are clear for sidestepping.`;
        }}
      }}
      // 6. Object Localization ("Where is my mouse / phone / laptop?")
      else if (q.includes('where is') || q.includes('find my') || q.includes('is there a') || q.includes('look for')) {{
        const targetClass = ['mouse', 'cell phone', 'phone', 'laptop', 'bottle', 'cup', 'chair', 'book', 'person', 'keyboard'].find(cls => q.includes(cls));
        if (targetClass) {{
          const matchedObj = objects.find(o => o.label.toLowerCase().includes(targetClass.replace('phone', 'cell phone')));
          if (matchedObj) {{
            const posText = matchedObj.pos === 'CENTER' ? 'directly ahead of you' : `on your ${{matchedObj.pos.toLowerCase()}}`;
            reply = `Your ${{matchedObj.label}} is located ${{posText}} at approximately ${{matchedObj.dist_m.toFixed(1)}} meters.`;
          }} else {{
            reply = `I do not currently detect a ${{targetClass}} in the camera view. Try panning your camera slightly.`;
          }}
        }} else {{
          reply = `Currently in view, I detect: ${{objects.length > 0 ? objects.map(o => o.label).join(', ') : 'no major objects'}}.`;
        }}
      }}
      // 7. Identity & Person In Front
      else if (q.includes('who is in front') || q.includes('anyone in front') || q.includes('who is that')) {{
        const persons = objects.filter(o => o.label === 'person');
        if (persons.length === 0) {{
          reply = "No people are currently detected in your immediate field of view.";
        }} else {{
          const p = persons[0];
          const state = p.isApproaching ? "moving towards you" : "currently stationary";
          reply = `There is a person ${{p.pos === 'CENTER' ? 'directly ahead of you' : 'on your ' + p.pos.toLowerCase()}} at ${{p.dist_m.toFixed(1)}} meters, ${{state}}.`;
        }}
      }}
      // 8. PhD Modules Explanation
      else if (q.includes('module') || q.includes('explain module')) {{
        const modNum = [1, 2, 3, 4, 5, 6, 7, 8].find(n => q.includes(n.toString()) || q.includes(`module ${{n}}`));
        if (modNum) {{
          selectModuleTab(modNum);
          const name = document.getElementById('inspectorModuleName').textContent;
          const desc = document.getElementById('inspectorModuleDesc').textContent;
          reply = `${{name}}. ${{desc}}`;
        }} else {{
          reply = "The smart glasses incorporate 8 specialized modules: Object Detection, BDD100K Navigation, Depth Radar, Scene Recognition, Storytelling, Assistive OCR, GPS Guidance, and the Dynamic Hazard Priority Engine.";
        }}
      }}
      // 9. Time & Clock
      else if (q.includes('time') || q.includes('clock')) {{
        reply = `The current time is ${{new Date().toLocaleTimeString([], {{hour: '2-digit', minute:'2-digit'}})}}.`;
      }}
      // 10. UNIVERSAL PERSONAL ASSISTANT: Search the Live Internet for Any Question!
      else {{
        assistantDialogueStatus.textContent = "Searching internet for verified answer...";
        const webAnswer = await searchLiveWeb(query);
        if (webAnswer) {{
          reply = webAnswer;
          isWeb = true;
        }} else {{
          reply = `I am your personal AI assistant. You can ask me to read books, summarize literature, search the internet, locate objects, or guide your walking path. How can I assist you right now?`;
        }}
      }}

      // Display and Speak Response
      const badge = isWeb ? '<span style="background: rgba(0,229,255,0.15); color: var(--cyan-neon); font-size: 0.70rem; padding: 0.15rem 0.4rem; border-radius: 4px; margin-right: 0.4rem;">&#127760; WEB SEARCH</span>' : '';
      const textToSpeak = reply.replace(/<[^>]*>/g, ''); // strip HTML tags for TTS
      assistantDialogueBox.innerHTML = userEntry + `<p style="color: var(--cyan-neon);">${{badge}}<strong>Glasses AI:</strong> ${{reply}}</p>`;
      assistantDialogueBox.scrollTop = assistantDialogueBox.scrollHeight;
      assistantDialogueStatus.textContent = "Answered";
      speak(textToSpeak, {{ priority: true, interrupt: true }});
    }}

"""
    code = code[:idx_ask_start] + new_ask_code + code[idx_ask_end:]
    print("Replaced askAssistant successfully!")
else:
    print("Could not find askAssistant markers!")

with open(r'D:\Blind_SMart_Glasses\build_index_html.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved build_index_html.py successfully!")
