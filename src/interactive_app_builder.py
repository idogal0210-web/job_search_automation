import os
import json
from datetime import datetime

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="he" dir="rtl" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>__TITLE__</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    * {
      transition: background-color 0.2s ease, border-color 0.2s ease;
    }
    .custom-scrollbar::-webkit-scrollbar {
      width: 6px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
      background: transparent;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
      background: #334155;
      border-radius: 4px;
    }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen p-4 md:p-6 font-sans antialiased selection:bg-sky-500 selection:text-white">

  <div class="max-w-4xl mx-auto space-y-5">
    
    <!-- Top Bar: Header & Actions -->
    <header class="bg-slate-900/90 border border-slate-800 backdrop-blur-md rounded-2xl p-5 shadow-xl relative overflow-hidden">
      <div class="absolute -top-24 -left-24 w-60 h-60 bg-sky-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div class="absolute -bottom-24 -right-24 w-60 h-60 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
              __REPORT_TYPE_LABEL__
            </span>
            <span class="text-xs text-slate-400">__NOW_STR__</span>
          </div>
          <h1 class="text-2xl font-black tracking-tight text-white flex items-center gap-2">
            🚀 דשבורד משרות אינטראקטיבי <span class="text-sky-400 font-medium text-lg">| עידו גל</span>
          </h1>
          <p class="text-xs md:text-sm text-slate-400 mt-1">
            סינון, ניהול וסנכרון חכם של משרות אנרגיה ורחפנים בזמן אמת.
          </p>
        </div>

        <div class="flex items-center gap-2.5 self-start md:self-auto">
          <button onclick="toggleTheme()" id="themeBtn" class="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60 shadow-sm" title="החלף ערכת נושא">
            <span id="themeIcon">🌙</span>
          </button>

          <button onclick="triggerSyncModal()" class="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-bold text-xs md:text-sm rounded-xl shadow-lg shadow-sky-500/20 active:scale-95 transition-all">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
            <span>סנכרן למערכת</span>
          </button>
        </div>
      </div>

      <!-- Progress Bar -->
      <div class="mt-5 pt-4 border-t border-slate-800/80">
        <div class="flex justify-between items-center text-xs font-semibold mb-1.5">
          <span class="text-slate-300 flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            התקדמות סקירה
          </span>
          <span id="progressText" class="text-sky-400">סקרת 0 מתוך __TOTAL_JOBS__ משרות (0%)</span>
        </div>
        <div class="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden p-0.5">
          <div id="progressBar" class="h-full bg-gradient-to-r from-sky-400 via-teal-400 to-emerald-400 rounded-full transition-all duration-500" style="width: 0%"></div>
        </div>
      </div>
    </header>

    <!-- Filter & Segment Controls -->
    <nav class="flex flex-col sm:flex-row justify-between items-stretch sm:items-center gap-3 bg-slate-900/60 p-2 rounded-2xl border border-slate-800/80">
      <div class="flex items-center gap-1 bg-slate-950/70 p-1 rounded-xl border border-slate-800/70">
        <button onclick="setFilter('all', this)" class="tab-btn active px-3.5 py-1.5 text-xs font-bold rounded-lg bg-sky-600 text-white shadow-sm">
          הכל (<span id="countAll">__TOTAL_JOBS__</span>)
        </button>
        <button onclick="setFilter('saved', this)" class="tab-btn px-3.5 py-1.5 text-xs font-bold rounded-lg text-slate-400 hover:text-white">
          ✔️ שמורות להגשה (<span id="countSaved">0</span>)
        </button>
        <button onclick="setFilter('rejected', this)" class="tab-btn px-3.5 py-1.5 text-xs font-bold rounded-lg text-slate-400 hover:text-white">
          ✖️ הוסרו (<span id="countRejected">0</span>)
        </button>
      </div>

      <div class="flex items-center gap-2">
        <select id="sectorFilter" onchange="filterCards()" class="w-full sm:w-auto bg-slate-950 text-slate-200 text-xs font-semibold px-3 py-2 rounded-xl border border-slate-800 focus:outline-none focus:border-sky-500">
          <option value="all">🌐 כל התחומים</option>
          <option value="energy">⚡ אנרגיה, גז טבעי ו-SCADA</option>
          <option value="drones">🚁 רחפנים וכטב״ם אוטונומי</option>
          <option value="cuas">🛡️ הגנת C-UAS וביטחון</option>
          <option value="avionics">📡 מטע״דים ואוויוניקה</option>
        </select>
      </div>
    </nav>

    <!-- Job Cards List -->
    <main id="cardsContainer" class="space-y-4"></main>

    <!-- Empty State -->
    <div id="emptyState" class="hidden text-center py-12 bg-slate-900/40 border border-slate-800 rounded-2xl">
      <div class="text-4xl mb-2">🔍</div>
      <div class="text-sm font-bold text-slate-300">לא נמצאו משרות בהתאם לסינון</div>
      <div class="text-xs text-slate-500 mt-1">נסה לבחור לשונית או תחום אחר.</div>
    </div>

    <!-- Toast Notification -->
    <div id="toast" class="fixed bottom-5 right-5 bg-slate-800 border border-slate-700 text-white px-4 py-3 rounded-xl shadow-2xl text-xs font-bold flex items-center gap-2 transform translate-y-20 opacity-0 transition-all duration-300 z-50">
      <span id="toastIcon">🔔</span>
      <span id="toastMsg">ההודעה עודכנה</span>
    </div>

    <!-- Sync Modal -->
    <div id="syncModal" class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50">
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
        <div class="flex items-center gap-3">
          <div class="p-2.5 rounded-full bg-sky-500/20 text-sky-400">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
          </div>
          <div>
            <h3 class="font-bold text-base text-white">סנכרון משרות למערכת</h3>
            <p class="text-xs text-slate-400">שמירת המשרות שהוסרו (✖️) למניעת הצגתן בעתיד</p>
          </div>
        </div>

        <div class="bg-slate-950 p-3.5 rounded-xl border border-slate-800 text-xs space-y-2">
          <div class="flex justify-between items-center text-slate-300">
            <span class="flex items-center gap-1.5"><span class="text-emerald-400">✔️</span> משרות שמורות להגשה:</span>
            <span id="syncSavedCount" class="font-bold text-emerald-400 text-sm">0</span>
          </div>
          <div class="text-[11px] text-slate-400 mr-5">יעד: <span class="font-mono text-emerald-400">data/saved_jobs.json</span></div>

          <div class="flex justify-between items-center text-slate-300 pt-1 border-t border-slate-800/80">
            <span class="flex items-center gap-1.5"><span class="text-rose-400">✖️</span> משרות שסומנו להסרה:</span>
            <span id="syncRejectedCount" class="font-bold text-rose-400 text-sm">0</span>
          </div>
          <div class="text-[11px] text-slate-400 mr-5">יעד: <span class="font-mono text-rose-400">data/rejected_jobs.json</span></div>
        </div>

        <p class="text-xs text-slate-400 leading-relaxed">
          לחיצה על סנכרון תשמור ישירות את המשרות לקובצי הפרויקט במחשב שלך ותעדכן את מסדי הנתונים והדשבורד בזמן אמת.
        </p>

        <div class="flex gap-2 justify-end pt-2">
          <button onclick="closeSyncModal()" class="px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-white bg-slate-800">
            סגור
          </button>
          <button id="syncConfirmBtn" onclick="confirmSync()" class="px-4 py-2 rounded-xl text-xs font-bold text-white bg-sky-500 hover:bg-sky-400 shadow-md shadow-sky-500/20 transition-all">
            בצע סנכרון כעת
          </button>
        </div>
      </div>
    </div>

  </div>

  <script>
    const rawJobsData = __JOBS_JSON__;
    let currentFilter = 'all';
    const STORAGE_KEY = 'ido_job_triage_store';

    function loadTriageState() {
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        return stored ? JSON.parse(stored) : {};
      } catch (e) {
        return {};
      }
    }

    function saveTriageState(state) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      } catch (e) {}
    }

    let jobStates = loadTriageState();

    function renderCards() {
      const container = document.getElementById('cardsContainer');
      container.innerHTML = '';

      if (!rawJobsData || rawJobsData.length === 0) {
        document.getElementById('emptyState').classList.remove('hidden');
        return;
      }

      rawJobsData.forEach((job, idx) => {
        const id = job.link || `job_${idx}`;
        const score = job.match_score || 85;
        const company = job.company || 'חברה';
        const title = job.title || 'משרה ללא כותרת';
        const link = job.link || '#';
        const secKey = job.sector_key || 'energy';
        
        let sectorBadge = '⚡ תשתיות אנרגיה ו-SCADA';
        let badgeColor = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
        if (['drones', 'cuas', 'avionics'].includes(secKey)) {
          if (secKey === 'cuas') {
            sectorBadge = '🛡️ מערכות הגנת C-UAS וביטחון';
            badgeColor = 'bg-rose-500/10 text-rose-400 border-rose-500/20';
          } else if (secKey === 'avionics') {
            sectorBadge = '📡 מטע"דים ואוויוניקה';
            badgeColor = 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
          } else {
            sectorBadge = '🚁 רחפנים וכטב"ם אוטונומי';
            badgeColor = 'bg-purple-500/10 text-purple-400 border-purple-500/20';
          }
        }

        const domain = job.company_domain_product || job.company_summary || 'חברה מובילה בתחומה';
        const loc = job.location || 'ישראל / היברידי';
        const jobSum = job.job_summary || job.company_summary || 'תפקיד משמעותי בתפעול וניטור מערכות מתקדמות.';
        const strengths = job.experience_strengths || job.reasoning || 'התאמה גבוהה לרקע הטכני בהנדסאי מכונות, בקרת 24/7 וסיירת נח"ל.';
        const highlights = job.key_highlights || (job.work_model ? `מודל עבודה: ${job.work_model} | פתיחות: ${job.junior_openness || '🟢 גבוהה'}` : 'פתיחות להנדסאים בעלי זיקה טכנית ויכולת למידה עצמאית.');

        const card = document.createElement('article');
        card.setAttribute('data-id', id);
        card.setAttribute('data-sector', secKey);
        card.className = 'job-card bg-slate-900/80 border border-slate-800/90 rounded-2xl p-5 shadow-lg relative transition-all hover:border-slate-700';

        card.innerHTML = `
          <!-- Top row: Category tag, Big Title, Match Score -->
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3 mb-4">
            <div>
              <span class="text-xs font-bold px-2.5 py-0.5 rounded-full ${badgeColor} border inline-block mb-1.5">
                ${sectorBadge}
              </span>
              <h2 class="text-lg font-bold text-white tracking-tight">${company} - ${title} <span class="text-xs font-normal text-slate-400 mr-2">• ${loc}</span></h2>
            </div>
            <div class="self-start sm:self-auto">
              <span class="px-3 py-1 rounded-full text-xs font-extrabold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                <span>${score}%</span> התאמה
              </span>
            </div>
          </div>

          <!-- 4 Clean, Non-Redundant Sections -->
          <div class="grid grid-cols-1 gap-2.5 text-xs md:text-sm">
            <div class="flex items-start gap-2 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/60">
              <span class="font-bold text-sky-400 shrink-0">🏢 תחום ומוצר החברה:</span>
              <span class="text-slate-300">${domain}</span>
            </div>

            <div class="flex items-start gap-2 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/60">
              <span class="font-bold text-sky-400 shrink-0">📋 תקציר המשרה:</span>
              <span class="text-slate-300">${jobSum}</span>
            </div>

            <div class="flex items-start gap-2 bg-emerald-950/20 p-2.5 rounded-xl border border-emerald-800/40">
              <span class="font-bold text-emerald-400 shrink-0">💪 נקודות חוזק:</span>
              <span class="text-slate-200">${strengths}</span>
            </div>

            <div class="flex items-start gap-2 bg-amber-950/20 p-2.5 rounded-xl border border-amber-800/40">
              <span class="font-bold text-amber-400 shrink-0">🔍 דגשים:</span>
              <span class="text-slate-300">${highlights}</span>
            </div>
          </div>

          <!-- Action Bar -->
          <div class="flex items-center justify-between gap-3 mt-4 pt-3.5 border-t border-slate-800/80">
            <div class="flex items-center gap-2">
              <button onclick="toggleAction('${id.replace(/'/g, "\\'")}', 'saved')" class="action-save-btn px-3 py-1.5 text-xs font-bold rounded-lg border flex items-center gap-1.5 transition-all">
                <span>✔️</span> <span class="btn-text">שמור להגשה</span>
              </button>
              <button onclick="toggleAction('${id.replace(/'/g, "\\'")}', 'rejected')" class="action-reject-btn px-3 py-1.5 text-xs font-bold rounded-lg border flex items-center gap-1.5 transition-all">
                <span>✖️</span> הסר משרה
              </button>
            </div>

            <a href="${link}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-white text-xs font-bold shadow-md shadow-sky-500/20">
              <span>הגש מועמדות ↗</span>
            </a>
          </div>
        `;
        container.appendChild(card);
      });

      updateUI();
    }

    function toggleTheme() {
      const html = document.documentElement;
      const isDark = html.classList.toggle('dark');
      document.getElementById('themeIcon').textContent = isDark ? '🌙' : '☀️';
      if (!isDark) {
        document.body.classList.remove('bg-slate-950', 'text-slate-100');
        document.body.classList.add('bg-slate-100', 'text-slate-900');
      } else {
        document.body.classList.add('bg-slate-950', 'text-slate-100');
        document.body.classList.remove('bg-slate-100', 'text-slate-900');
      }
    }

    function toggleAction(id, action) {
      const current = jobStates[id];
      if (current === action) {
        delete jobStates[id];
        showToast('ℹ️', 'הסטטוס אופס למצב ממתין');
      } else {
        jobStates[id] = action;
        if (action === 'saved') {
          showToast('✔️', 'המשרה נשמרה להגשה');
        } else if (action === 'rejected') {
          showToast('✖️', 'המשרה הוסרה ולא תוצג שוב');
        }
      }
      saveTriageState(jobStates);
      updateUI();
    }

    function setFilter(filter, el) {
      currentFilter = filter;
      document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.remove('bg-sky-600', 'text-white');
        b.classList.add('text-slate-400');
      });
      el.classList.add('bg-sky-600', 'text-white');
      el.classList.remove('text-slate-400');
      updateUI();
    }

    function filterCards() {
      updateUI();
    }

    function updateUI() {
      const selectedSector = document.getElementById('sectorFilter').value;
      const cards = document.querySelectorAll('.job-card');
      let visibleCount = 0;
      let saved = 0, rejected = 0;
      const total = cards.length;

      cards.forEach(card => {
        const id = card.getAttribute('data-id');
        const sector = card.getAttribute('data-sector');
        const state = jobStates[id] || 'pending';

        if (state === 'saved') saved++;
        if (state === 'rejected') rejected++;

        const saveBtn = card.querySelector('.action-save-btn');
        const rejectBtn = card.querySelector('.action-reject-btn');
        const saveText = saveBtn.querySelector('.btn-text');

        if (state === 'saved') {
          saveBtn.className = "action-save-btn px-3 py-1.5 text-xs font-bold rounded-lg border flex items-center gap-1.5 transition-all bg-emerald-500 text-white border-emerald-600 shadow-sm shadow-emerald-500/20";
          saveText.textContent = "נשמר להגשה";
          rejectBtn.className = "action-reject-btn px-3 py-1.5 text-xs font-bold rounded-lg border flex items-center gap-1.5 transition-all bg-slate-800 text-slate-300 border-slate-700 hover:bg-rose-500/10 hover:text-rose-400";
        } else if (state === 'rejected') {
          rejectBtn.className = "action-reject-btn px-3 py-1.5 text-xs font-bold rounded-lg border flex items-center gap-1.5 transition-all bg-rose-500 text-white border-rose-600 shadow-sm shadow-rose-500/20";
          saveBtn.className = "action-save-btn px-3 py-1.5 text-xs font-bold rounded-lg border flex items-center gap-1.5 transition-all bg-slate-800 text-slate-300 border-slate-700 hover:bg-emerald-500/10 hover:text-emerald-400";
          saveText.textContent = "שמור להגשה";
        } else {
          saveBtn.className = "action-save-btn px-3 py-1.5 text-xs font-bold rounded-lg border flex items-center gap-1.5 transition-all bg-slate-800 text-slate-300 border-slate-700 hover:bg-emerald-500/10 hover:text-emerald-400";
          rejectBtn.className = "action-reject-btn px-3 py-1.5 text-xs font-bold rounded-lg border flex items-center gap-1.5 transition-all bg-slate-800 text-slate-300 border-slate-700 hover:bg-rose-500/10 hover:text-rose-400";
          saveText.textContent = "שמור להגשה";
        }

        let matchesTab = false;
        if (currentFilter === 'all') matchesTab = (state !== 'rejected');
        else if (currentFilter === 'saved') matchesTab = (state === 'saved');
        else if (currentFilter === 'rejected') matchesTab = (state === 'rejected');

        let matchesSector = (selectedSector === 'all' || sector === selectedSector);

        if (matchesTab && matchesSector) {
          card.classList.remove('hidden');
          visibleCount++;
        } else {
          card.classList.add('hidden');
        }
      });

      document.getElementById('countAll').textContent = total;
      document.getElementById('countSaved').textContent = saved;
      document.getElementById('countRejected').textContent = rejected;

      const triaged = saved + rejected;
      const pct = total > 0 ? Math.round((triaged / total) * 100) : 0;
      document.getElementById('progressBar').style.width = pct + '%';
      document.getElementById('progressText').textContent = `סקרת ${triaged} מתוך ${total} משרות (${pct}%)`;

      const emptyState = document.getElementById('emptyState');
      if (visibleCount === 0) {
        emptyState.classList.remove('hidden');
      } else {
        emptyState.classList.add('hidden');
      }
    }

    function showToast(icon, msg) {
      const toast = document.getElementById('toast');
      document.getElementById('toastIcon').textContent = icon;
      document.getElementById('toastMsg').textContent = msg;
      toast.classList.remove('translate-y-20', 'opacity-0');
      setTimeout(() => {
        toast.classList.add('translate-y-20', 'opacity-0');
      }, 2500);
    }

    function triggerSyncModal() {
      const savedCount = Object.values(jobStates).filter(s => s === 'saved').length;
      const rejectedCount = Object.values(jobStates).filter(s => s === 'rejected').length;
      document.getElementById('syncSavedCount').textContent = savedCount;
      document.getElementById('syncRejectedCount').textContent = rejectedCount;
      document.getElementById('syncModal').classList.remove('hidden');
    }

    function closeSyncModal() {
      document.getElementById('syncModal').classList.add('hidden');
    }

    async function confirmSync() {
      const savedList = Object.keys(jobStates).filter(id => jobStates[id] === 'saved');
      const rejectedList = Object.keys(jobStates).filter(id => jobStates[id] === 'rejected');
      
      const syncBtn = document.getElementById('syncConfirmBtn');
      if (syncBtn) {
        syncBtn.disabled = true;
        syncBtn.textContent = "מסנכרן למחשב...";
      }

      try {
        const response = await fetch('http://127.0.0.1:8765/api/sync', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ saved: savedList, rejected: rejectedList })
        });
        
        if (response.ok) {
          const data = await response.json();
          closeSyncModal();
          showToast('✅', `סונכרן למחשב בהצלחה! (${data.saved_count} שמורות, ${data.rejected_count} הוסרו)`);
        } else {
          throw new Error('Sync server returned error');
        }
      } catch (err) {
        closeSyncModal();
        showToast('⚠️', 'נשמר בדפדפן. לסנכרון לקובצי המחשב, הפעל: python sync_server.py');
      } finally {
        if (syncBtn) {
          syncBtn.disabled = false;
          syncBtn.textContent = "בצע סנכרון כעת";
        }
      }
    }

    window.onload = renderCards;
  </script>
</body>
</html>"""

def generate_interactive_html(jobs, title="דוח משרות אינטראקטיבי | עידו גל", is_weekly=False):
    total_jobs = len(jobs)
    now_str = datetime.now().strftime("%d.%m.%Y")
    report_type_label = "סיכום שבועי" if is_weekly else "סריקה יומית"
    jobs_json = json.dumps(jobs, ensure_ascii=False)

    html = HTML_TEMPLATE
    html = html.replace("__TITLE__", title)
    html = html.replace("__REPORT_TYPE_LABEL__", report_type_label)
    html = html.replace("__NOW_STR__", now_str)
    html = html.replace("__TOTAL_JOBS__", str(total_jobs))
    html = html.replace("__JOBS_JSON__", jobs_json)
    return html

def build_and_save_docs_app(jobs, is_weekly=False):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(project_root, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    out_file = os.path.join(docs_dir, "index.html")
    
    html = generate_interactive_html(jobs, is_weekly=is_weekly)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[+] Successfully generated GitHub Pages interactive web app at: {out_file}")
    return out_file

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    archive_file = os.path.join(project_root, "data", "weekly_archive.json")
    if not os.path.exists(archive_file):
        archive_file = os.path.join(project_root, "weekly_archive.json")
        
    if os.path.exists(archive_file):
        try:
            with open(archive_file, "r", encoding="utf-8") as f:
                archived_jobs = json.load(f)
            build_and_save_docs_app(archived_jobs, is_weekly=False)
            print(f"[+] Rebuilt docs/index.html with {len(archived_jobs)} jobs.")
        except Exception as e:
            print(f"[-] Error: {e}")
