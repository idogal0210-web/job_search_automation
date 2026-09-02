import os
import json
from datetime import datetime

def generate_interactive_html(jobs, title="דוח משרות אינטראקטיבי | עידו גל", is_weekly=False):
    """
    Generate a standalone, responsive, RTL interactive HTML dashboard for GitHub Pages.
    Clean 3-4 color palette:
    - Primary Navy: #0f172a
    - Slate Text/Muted: #475569 / #94a3b8
    - Brand Blue Accent: #0284c7
    - Success Green: #16a34a
    - Danger Red: #dc2626
    """
    
    total_jobs = len(jobs)
    now_str = datetime.now().strftime("%d.%m.%Y")
    report_type_label = "סיכום שבועי" if is_weekly else "סריקה יומית"

    jobs_json = json.dumps(jobs, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --navy-dark: #0f172a;
            --slate-gray: #475569;
            --blue-accent: #0284c7;
            --blue-hover: #0369a1;
            --success-green: #16a34a;
            --danger-red: #dc2626;
            --bg-page: #f8fafc;
            --bg-card: #ffffff;
            --border-light: #e2e8f0;
        }}

        body {{
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-page);
            color: var(--navy-dark);
            margin: 0;
            padding: 16px;
            direction: rtl;
            line-height: 1.5;
        }}

        .container {{
            max-width: 920px;
            margin: 0 auto;
        }}

        /* Header Banner */
        .header-card {{
            background: linear-gradient(135deg, var(--navy-dark) 0%, #1e293b 100%);
            color: #ffffff;
            padding: 24px;
            border-radius: 16px;
            box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
            margin-bottom: 20px;
        }}

        .header-title {{
            margin: 0 0 6px 0;
            font-size: 24px;
            font-weight: 800;
        }}

        .header-meta {{
            font-size: 14px;
            color: #94a3b8;
            margin-bottom: 16px;
        }}

        .progress-bar-bg {{
            background: #334155;
            height: 10px;
            border-radius: 5px;
            overflow: hidden;
        }}

        .progress-bar-fill {{
            background: linear-gradient(90deg, #38bdf8, #4ade80);
            height: 100%;
            width: 0%;
            transition: width 0.4s ease;
        }}

        .progress-text {{
            font-size: 13px;
            color: #cbd5e1;
            margin-top: 6px;
            text-align: left;
        }}

        /* Controls & Filter Bar */
        .controls-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 20px;
        }}

        .tabs-group {{
            display: flex;
            background: #e2e8f0;
            padding: 4px;
            border-radius: 10px;
            gap: 4px;
        }}

        .tab-btn {{
            border: none;
            background: transparent;
            padding: 8px 16px;
            font-size: 13.5px;
            font-weight: 600;
            color: var(--slate-gray);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .tab-btn.active {{
            background: #ffffff;
            color: var(--blue-accent);
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        .sector-filter-select {{
            padding: 8px 14px;
            font-size: 13.5px;
            border: 1px solid var(--border-light);
            border-radius: 8px;
            background: #ffffff;
            color: var(--navy-dark);
            font-weight: 600;
            outline: none;
            cursor: pointer;
        }}

        /* Sector Header Group */
        .sector-group-title {{
            font-size: 17px;
            font-weight: 800;
            color: var(--navy-dark);
            margin: 24px 0 12px 0;
            padding-bottom: 6px;
            border-bottom: 2px solid #e2e8f0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        /* Job Cards */
        .jobs-list {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        .job-card {{
            background: var(--bg-card);
            border-radius: 14px;
            border: 1px solid var(--border-light);
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.04);
            transition: all 0.25s ease;
            position: relative;
        }}

        .job-card.saved {{
            border-right: 6px solid var(--success-green);
            background: #fafdfb;
        }}

        .job-card.rejected {{
            opacity: 0.4;
            display: none;
        }}

        .job-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 12px;
        }}

        .job-title {{
            font-size: 18px;
            font-weight: 700;
            color: var(--navy-dark);
            margin: 0 0 4px 0;
        }}

        .job-company {{
            font-size: 14px;
            color: var(--blue-accent);
            font-weight: 600;
        }}

        .match-badge {{
            background: #dcfce7;
            color: #15803d;
            font-weight: 700;
            font-size: 13px;
            padding: 4px 10px;
            border-radius: 20px;
            white-space: nowrap;
        }}

        /* Company Intel Box */
        .intel-box {{
            background: #f8fafc;
            border: 1px solid #f1f5f9;
            border-radius: 10px;
            padding: 14px;
            margin: 12px 0 16px 0;
            font-size: 13.5px;
        }}

        .intel-row {{
            margin-bottom: 8px;
            display: flex;
            align-items: baseline;
            gap: 8px;
        }}

        .intel-row:last-child {{
            margin-bottom: 0;
        }}

        .intel-label {{
            font-weight: 700;
            color: #334155;
            min-width: 140px;
        }}

        .intel-val {{
            color: var(--slate-gray);
        }}

        /* Actions Bar */
        .actions-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid #f1f5f9;
            padding-top: 14px;
        }}

        .triage-btns {{
            display: flex;
            gap: 8px;
        }}

        .btn-action {{
            border: none;
            padding: 8px 14px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }}

        .btn-v {{
            background: #f0fdf4;
            color: var(--success-green);
            border: 1px solid #bbf7d0;
        }}

        .btn-v:hover, .btn-v.active {{
            background: var(--success-green);
            color: #ffffff;
        }}

        .btn-x {{
            background: #fef2f2;
            color: var(--danger-red);
            border: 1px solid #fecaca;
        }}

        .btn-x:hover {{
            background: var(--danger-red);
            color: #ffffff;
        }}

        .btn-apply {{
            background: var(--blue-accent);
            color: #ffffff;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            transition: background 0.2s;
        }}

        .btn-apply:hover {{
            background: var(--blue-hover);
        }}

        .empty-state {{
            text-align: center;
            padding: 40px;
            color: var(--slate-gray);
            font-size: 15px;
            display: none;
        }}

        @media (max-width: 640px) {{
            .job-header {{
                flex-direction: column;
            }}
            .actions-bar {{
                flex-direction: column;
                gap: 12px;
                align-items: stretch;
            }}
            .btn-apply {{
                text-align: center;
            }}
        }}
    </style>
</head>
<body>

<div class="container">
    <!-- Header Banner -->
    <div class="header-card">
        <h1 class="header-title">🚀 דוח משרות אינטראקטיבי | עידו גל</h1>
        <div class="header-meta">סוג דוח: {report_type_label} | תאריך: {now_str} | סה"כ משרות נבחרות: <span id="total-count">{total_jobs}</span></div>
        
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" id="progress-fill"></div>
        </div>
        <div class="progress-text" id="progress-text">סקרת 0 מתוך {total_jobs} משרות (0% הושלמו)</div>
    </div>

    <!-- Controls Bar -->
    <div class="controls-bar">
        <div class="tabs-group">
            <button class="tab-btn active" onclick="setTab('all', event)">הכל (<span id="tab-all-count">{total_jobs}</span>)</button>
            <button class="tab-btn" onclick="setTab('saved', event)">סומנו להגשה ✔️ (<span id="tab-saved-count">0</span>)</button>
            <button class="tab-btn" onclick="setTab('rejected', event)">הוסרו ✖️ (<span id="tab-rejected-count">0</span>)</button>
        </div>

        <select class="sector-filter-select" id="sector-select" onchange="applyFilters()">
            <option value="all">כל התחומים</option>
            <option value="energy">⚡ תשתיות אנרגיה, גז טבעי ו-SCADA</option>
            <option value="drones">🚁 רחפנים, כטב"ם אוטונומי ורובוטיקה</option>
            <option value="cuas">🛡️ מערכות הגנת C-UAS וביטחון</option>
            <option value="avionics">📡 מטע"דים, אלקטרו-אופטיקה ואוויוניקה</option>
        </select>
    </div>

    <!-- Jobs Container -->
    <div class="jobs-list" id="jobs-container"></div>
    <div class="empty-state" id="empty-state">אין משרות להצגה בלשונית/סינון זה.</div>
</div>

<script>
    const rawJobsData = {jobs_json};
    let currentTab = 'all';
    const STORAGE_KEY = 'ido_job_triage_store';

    function loadTriageState() {{
        try {{
            const stored = localStorage.getItem(STORAGE_KEY);
            return stored ? JSON.parse(stored) : {{}};
        }} catch (e) {{
            return {{}};
        }}
    }}

    function saveTriageState(state) {{
        try {{
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        }} catch (e) {{}}
    }}

    let triageState = loadTriageState();

    function renderJobs() {{
        const container = document.getElementById('jobs-container');
        container.innerHTML = '';

        const sectorMap = {{
            'energy': {{ title: '⚡ תשתיות אנרגיה, גז טבעי ו-SCADA', jobs: [] }},
            'drones': {{ title: '🚁 רחפנים, כטב"ם אוטונומי ורובוטיקה', jobs: [] }},
            'cuas': {{ title: '🛡️ מערכות הגנת C-UAS וביטחון', jobs: [] }},
            'avionics': {{ title: '📡 מטע"דים, אלקטרו-אופטיקה ואוויוניקה', jobs: [] }}
        }};

        rawJobsData.forEach((job, idx) => {{
            const id = job.link || `job_${{idx}}`;
            const sec = job.sector_key || 'energy';
            if (!sectorMap[sec]) {{
                sectorMap[sec] = {{ title: job.sector || 'תחום כללי', jobs: [] }};
            }}
            sectorMap[sec].jobs.push({{ ...job, id }});
        }});

        Object.keys(sectorMap).forEach(secKey => {{
            const secGroup = sectorMap[secKey];
            if (secGroup.jobs.length === 0) return;

            const secHeader = document.createElement('div');
            secHeader.className = 'sector-group-title';
            secHeader.dataset.sectorKey = secKey;
            secHeader.innerHTML = secGroup.title;
            container.appendChild(secHeader);

            secGroup.jobs.forEach(job => {{
                const status = triageState[job.id] || 'pending';
                const card = document.createElement('div');
                card.className = `job-card ${{status}}`;
                card.id = `card_${{btoa(unescape(encodeURIComponent(job.id))).replace(/=/g, '')}}`;
                card.dataset.jobId = job.id;
                card.dataset.status = status;
                card.dataset.sectorKey = secKey;

                const score = job.match_score || 85;
                const company = job.company || 'חברה בלתי מפורטת';
                const title = job.title || 'משרה ללא כותרת';
                const link = job.link || '#';

                const summary = job.company_summary || 'חברת טכנולוגיה ותשתיות מובילה בתחומה.';
                const size = job.company_size || 'עובדים בתמיכה מורחבת';
                const openness = job.junior_openness || '🟢 גבוהה – פתוחים להנדסאים/מהנדסים בעלי זיקה טכנית ותשוקה ללמידה.';
                const workModel = job.work_model || 'היברידי';

                card.innerHTML = `
                    <div class="job-header">
                        <div>
                            <h2 class="job-title">${{title}}</h2>
                            <div class="job-company">${{company}}</div>
                        </div>
                        <div class="match-badge">${{score}}% התאמה</div>
                    </div>

                    <div class="intel-box">
                        <div class="intel-row">
                            <span class="intel-label">💡 אודות החברה:</span>
                            <span class="intel-val">${{summary}}</span>
                        </div>
                        <div class="intel-row">
                            <span class="intel-label">👥 גודל חברה:</span>
                            <span class="intel-val">${{size}}</span>
                        </div>
                        <div class="intel-row">
                            <span class="intel-label">🎓 פתיחות ללא ניסיון:</span>
                            <span class="intel-val">${{openness}}</span>
                        </div>
                        <div class="intel-row">
                            <span class="intel-label">🏢 סביבת עבודה:</span>
                            <span class="intel-val">${{workModel}}</span>
                        </div>
                    </div>

                    <div class="actions-bar">
                        <div class="triage-btns">
                            <button class="btn-action btn-v ${{status === 'saved' ? 'active' : ''}}" onclick="triageJob('${{job.id.replace(/'/g, "\\'")}}', 'saved')">✔️ שמור להגשה</button>
                            <button class="btn-action btn-x" onclick="triageJob('${{job.id.replace(/'/g, "\\'")}}', 'rejected')">✖️ הסר משרה</button>
                        </div>
                        <a href="${{link}}" target="_blank" class="btn-apply">הגש מועמדות למשרה ↗</a>
                    </div>
                `;
                container.appendChild(card);
            }});
        }});

        updateStats();
        applyFilters();
    }}

    function triageJob(jobId, action) {{
        if (triageState[jobId] === action) {{
            delete triageState[jobId];
        }} else {{
            triageState[jobId] = action;
        }}
        saveTriageState(triageState);
        renderJobs();
    }}

    function updateStats() {{
        const allCards = document.querySelectorAll('.job-card');
        let savedCount = 0;
        let rejectedCount = 0;

        allCards.forEach(c => {{
            if (c.dataset.status === 'saved') savedCount++;
            if (c.dataset.status === 'rejected') rejectedCount++;
        }});

        const total = allCards.length;
        const triaged = savedCount + rejectedCount;
        const pct = total > 0 ? Math.round((triaged / total) * 100) : 0;

        document.getElementById('tab-all-count').innerText = total;
        document.getElementById('tab-saved-count').innerText = savedCount;
        document.getElementById('tab-rejected-count').innerText = rejectedCount;

        document.getElementById('progress-fill').style.width = pct + '%';
        document.getElementById('progress-text').innerText = `סקרת ${{triaged}} מתוך ${{total}} משרות (${{pct}}% הושלמו)`;
    }}

    function setTab(tab, evt) {{
        currentTab = tab;
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        if (evt && evt.target) evt.target.classList.add('active');
        applyFilters();
    }}

    function applyFilters() {{
        const selectedSector = document.getElementById('sector-select').value;
        const allCards = document.querySelectorAll('.job-card');
        const allHeaders = document.querySelectorAll('.sector-group-title');

        let visibleCount = 0;

        allCards.forEach(c => {{
            const status = c.dataset.status;
            const secKey = c.dataset.sectorKey;

            let matchesTab = false;
            if (currentTab === 'all') matchesTab = status !== 'rejected';
            else if (currentTab === 'saved') matchesTab = status === 'saved';
            else if (currentTab === 'rejected') matchesTab = status === 'rejected';

            let matchesSector = selectedSector === 'all' || secKey === selectedSector;

            if (matchesTab && matchesSector) {{
                c.style.display = 'block';
                visibleCount++;
            }} else {{
                c.style.display = 'none';
            }}
        }});

        allHeaders.forEach(h => {{
            const secKey = h.dataset.sectorKey;
            const hasVisible = Array.from(allCards).some(c => c.dataset.sectorKey === secKey && c.style.display === 'block');
            h.style.display = hasVisible ? 'flex' : 'none';
        }});

        document.getElementById('empty-state').style.display = visibleCount === 0 ? 'block' : 'none';
    }}

    window.onload = renderJobs;
</script>
</body>
</html>"""
    return html_content

def build_and_save_docs_app(jobs, is_weekly=False):
    """Save the generated interactive HTML into docs/index.html for GitHub Pages publishing."""
    docs_dir = os.path.join(os.path.dirname(__file__), "docs")
    os.makedirs(docs_dir, exist_ok=True)
    out_file = os.path.join(docs_dir, "index.html")
    
    html = generate_interactive_html(jobs, is_weekly=is_weekly)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[+] Successfully generated GitHub Pages interactive web app at: {out_file}")
    return out_file
