import os
import json
from datetime import datetime, timedelta

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
          <div id="cloudSyncStatus" class="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded-full text-xs font-bold text-emerald-400">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>ענן מסונכרן בלייב</span>
          </div>

          <button onclick="toggleTheme()" id="themeBtn" class="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60 shadow-sm" title="החלף ערכת נושא">
            <span id="themeIcon">🌙</span>
          </button>

          <button onclick="triggerSyncModal()" class="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-bold text-xs md:text-sm rounded-xl shadow-lg shadow-sky-500/20 active:scale-95 transition-all">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
            <span>סנכרון ענן</span>
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
          משרות חדשות (<span id="countAll">__TOTAL_JOBS__</span>)
        </button>
        <button onclick="setFilter('saved', this)" class="tab-btn px-3.5 py-1.5 text-xs font-bold rounded-lg text-slate-400 hover:text-white">
          ✔️ שמורות להגשה (<span id="countSaved">0</span>)
        </button>
        <button onclick="setFilter('rejected', this)" class="tab-btn px-3.5 py-1.5 text-xs font-bold rounded-lg text-slate-400 hover:text-white">
          ✖️ הוסרו (<span id="countRejected">0</span>)
        </button>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <select id="sectorFilter" onchange="filterCards()" class="w-full sm:w-auto bg-slate-950 text-slate-200 text-xs font-semibold px-3 py-2 rounded-xl border border-slate-800 focus:outline-none focus:border-sky-500">
          <option value="all">🌐 כל התחומים</option>
          <option value="energy">⚡ אנרגיה, גז טבעי ו-SCADA</option>
          <option value="drones">🚁 רחפנים וכטב״ם אוטונומי</option>
          <option value="cuas">🛡️ הגנת C-UAS וביטחון</option>
          <option value="avionics">📡 מטע״דים ואוויוניקה</option>
        </select>

        <button id="sortBtn" onclick="toggleSort()" class="flex items-center gap-1.5 px-3.5 py-2 bg-slate-950 hover:bg-slate-800 text-slate-200 text-xs font-bold rounded-xl border border-slate-800 transition-all shadow-sm" title="לחץ לשינוי סדר המיון">
          <span id="sortIcon">🔽</span>
          <span id="sortLabel">התאמה: מגבוה לנמוך</span>
        </button>

        <button onclick="openDuplicatesModal()" class="flex items-center gap-1.5 px-3.5 py-2 bg-slate-950 hover:bg-amber-500/10 text-amber-400 text-xs font-bold rounded-xl border border-slate-800 hover:border-amber-500/40 transition-all shadow-sm" title="סרוק כפילויות משרות">
          <span>🔍</span>
          <span>בדיקת כפילות משרות</span>
        </button>
      </div>
    </nav>

    <!-- Contextual Action Bar for Saved Jobs (Export to Excel) -->
    <div id="savedActionBar" class="hidden flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-emerald-950/40 border border-emerald-500/30 p-3.5 rounded-2xl">
      <div class="flex items-center gap-2.5">
        <span class="text-xl">⭐</span>
        <div>
          <div class="text-xs font-bold text-emerald-300">משרות ששמרת להגשה</div>
          <div class="text-[11px] text-slate-400">ייצוא מהיר של כל המשרות השמורות לקובץ Excel מסודר עם קישורים ישירים.</div>
        </div>
      </div>
      <button onclick="exportSavedToExcel()" class="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-md shadow-emerald-500/20 active:scale-95 transition-all">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
        <span>ייצוא לאקסל (Excel)</span>
      </button>
    </div>

    <!-- Contextual Action Bar for Rejected Jobs (Permanent Delete & Reset) -->
    <div id="rejectedActionBar" class="hidden flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-rose-950/40 border border-rose-500/30 p-3.5 rounded-2xl">
      <div class="flex items-center gap-2.5">
        <span class="text-xl">🗑️</span>
        <div>
          <div class="text-xs font-bold text-rose-300">משרות שסומנו להסרה (✖️)</div>
          <div class="text-[11px] text-slate-400">לחיצה על מחיקה תנקה את כל הרשימה לצמיתות מכל המכשירים ותאפס את המספר ל-0.</div>
        </div>
      </div>
      <button onclick="clearAllRejected()" class="flex items-center gap-2 px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs rounded-xl shadow-md shadow-rose-500/20 active:scale-95 transition-all">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
        <span>מחיקה לצמיתות ואיפוס</span>
      </button>
    </div>

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
          <div class="text-[11px] text-slate-400 mr-5">יעד: <span class="font-mono text-emerald-400">Firebase (Cloud Sync)</span></div>

          <div class="flex justify-between items-center text-slate-300 pt-1 border-t border-slate-800/80">
            <span class="flex items-center gap-1.5"><span class="text-rose-400">✖️</span> משרות שסומנו להסרה:</span>
            <span id="syncRejectedCount" class="font-bold text-rose-400 text-sm">0</span>
          </div>
        </div>

        <p class="text-xs text-slate-400 leading-relaxed">
          הדשבורד שומר ומעדכן את כל המשרות שסימנת באופן רציף. כל המשרות השמורות והמוסרות נשמרות בהתאמה אישית עבורך.
        </p>

        <div class="pt-2.5 border-t border-slate-800/80 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2 text-xs">
          <span class="text-slate-400">סנכרון מיידי בין מכשירים:</span>
          <button onclick="shareSyncLink()" class="px-3 py-1.5 rounded-lg bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 font-bold text-xs flex items-center justify-center gap-1.5 shadow-sm transition-all" title="פתח את כל המשרות המסומנות במכשיר אחר בלחיצה אחת ללא קודים">
            <span>📲</span> סנכרן למכשיר אחר (בלי קודים)
          </button>
        </div>

        <div class="flex gap-2 justify-end pt-2">
          <button onclick="closeSyncModal()" class="px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-white bg-slate-800">
            סגור
          </button>
          <button id="syncConfirmBtn" onclick="confirmSync()" class="px-4 py-2 rounded-xl text-xs font-bold text-white bg-sky-500 hover:bg-sky-400 shadow-md shadow-sky-500/20 transition-all">
            אשר ושמור
          </button>
        </div>
      </div>
    </div>

    <!-- Duplicates Modal -->
    <div id="duplicatesModal" class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50">
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-4 max-h-[80vh] flex flex-col">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="p-2.5 rounded-full bg-amber-500/20 text-amber-400">
              <span class="text-xl">🔍</span>
            </div>
            <div>
              <h3 class="font-bold text-base text-white">בדיקת כפילות משרות</h3>
              <p class="text-xs text-slate-400">זיהוי משרות זהות או דומות לפי כותרת וחברה</p>
            </div>
          </div>
          <button onclick="closeDuplicatesModal()" class="text-slate-500 hover:text-white text-xl font-bold leading-none">✕</button>
        </div>

        <div id="duplicatesContent" class="overflow-y-auto custom-scrollbar flex-1 space-y-3 text-xs">
          <!-- filled by JS -->
        </div>

        <div class="pt-3 border-t border-slate-800/80 flex justify-end">
          <button onclick="closeDuplicatesModal()" class="px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-white bg-slate-800">סגור</button>
        </div>
      </div>
    </div>

  </div>

  <script>
    const rawJobsData = __JOBS_JSON__;
    const initialSavedLinks = __INITIAL_SAVED_JSON__;
    const initialRejectedLinks = __INITIAL_REJECTED_JSON__;
    let currentFilter = 'all';
    let currentSort = 'desc';
    const STORAGE_KEY = 'ido_job_triage_store';

    function loadTriageState() {
      let state = {};
      if (typeof initialSavedLinks !== 'undefined' && Array.isArray(initialSavedLinks)) {
        initialSavedLinks.forEach(link => { state[link] = 'saved'; });
      }
      if (typeof initialRejectedLinks !== 'undefined' && Array.isArray(initialRejectedLinks)) {
        initialRejectedLinks.forEach(link => { state[link] = 'rejected'; });
      }
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          const userState = JSON.parse(stored);
          Object.assign(state, userState);
        }
      } catch (e) {}
      return state;
    }

    
    const CLOUD_SYNC_URL = 'https://job-finder-auto-default-rtdb.firebaseio.com/triage.json';
    let cloudSyncTimeout = null;
    let cloudLastUpdated = 0;

    async function fetchCloudSync() {
      const cloudBadge = document.getElementById('cloudSyncStatus');
      try {
        const resp = await fetch(CLOUD_SYNC_URL, { cache: 'no-cache' });
        if (resp.ok) {
          const data = await resp.json();
          if (data) {
            if (data.updated_at) {
              cloudLastUpdated = new Date(data.updated_at).getTime();
            }
            let changed = false;
            if (Array.isArray(data.purged)) {
              data.purged.forEach(link => {
                if (jobStates[link] !== 'purged') {
                  jobStates[link] = 'purged';
                  changed = true;
                }
              });
            }
            if (Array.isArray(data.saved)) {
              data.saved.forEach(link => {
                if (jobStates[link] !== 'saved') {
                  jobStates[link] = 'saved';
                  changed = true;
                }
              });
            }
            if (Array.isArray(data.rejected)) {
              data.rejected.forEach(link => {
                // If the job was purged locally, NEVER resurrect it to rejected
                if (jobStates[link] !== 'purged' && jobStates[link] !== 'saved') {
                  if (jobStates[link] !== 'rejected') {
                    jobStates[link] = 'rejected';
                    changed = true;
                  }
                }
              });
            }
            if (changed) {
              saveTriageState(jobStates);
              updateUI();
            }
            if (cloudBadge) {
              cloudBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-400"></span> <span>ענן מסונכרן</span>';
            }
          }
        }
      } catch (e) {
        if (cloudBadge) {
          cloudBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-slate-500"></span> <span>מקומי</span>';
        }
      }
    }

    function scheduleCloudPush() {
      if (cloudSyncTimeout) clearTimeout(cloudSyncTimeout);
      cloudSyncTimeout = setTimeout(pushCloudSync, 400);
    }

    async function pushCloudSync() {
      const cloudBadge = document.getElementById('cloudSyncStatus');
      if (cloudBadge) {
        cloudBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span> <span>מעדכן ענן...</span>';
      }

      try {
        const savedList = Object.keys(jobStates).filter(id => jobStates[id] === 'saved');
        const rejectedList = Object.keys(jobStates).filter(id => jobStates[id] === 'rejected');
        const purgedList = Object.keys(jobStates).filter(id => jobStates[id] === 'purged');
        
        const timestamp = new Date().toISOString();
        const payload = {
          saved: savedList,
          rejected: rejectedList,
          purged: purgedList,
          updated_at: timestamp
        };

        const resp = await fetch(CLOUD_SYNC_URL, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (resp.ok && cloudBadge) {
          cloudBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-400"></span> <span>ענן מסונכרן</span>';
        }
      } catch (e) {
        if (cloudBadge) {
          cloudBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-slate-500"></span> <span>מקומי</span>';
        }
      }
    }

    function extractJobId(link) {
      if (!link) return '';
      const match = link.match(/(\\d{7,12})/);
      return match ? match[1] : link;
    }

    function getSyncDelta() {
      const delta = {};
      const baseSaved = new Set(typeof initialSavedLinks !== 'undefined' && Array.isArray(initialSavedLinks) ? initialSavedLinks : []);
      const baseRejected = new Set(typeof initialRejectedLinks !== 'undefined' && Array.isArray(initialRejectedLinks) ? initialRejectedLinks : []);

      for (const [link, state] of Object.entries(jobStates)) {
        const wasSaved = baseSaved.has(link);
        const wasRejected = baseRejected.has(link);
        if (state === 'saved' && !wasSaved) {
          delta[extractJobId(link)] = 's';
        } else if (state === 'rejected' && !wasRejected) {
          delta[extractJobId(link)] = 'r';
        }
      }
      return delta;
    }

    function checkUrlSync() {
      try {
        const urlParams = new URLSearchParams(window.location.search);
        const syncData = urlParams.get('sync');
        if (syncData) {
          let incomingDelta = null;
          try {
            incomingDelta = JSON.parse(atob(decodeURIComponent(syncData)));
          } catch(e) {
            try {
              incomingDelta = JSON.parse(decodeURIComponent(escape(atob(decodeURIComponent(syncData)))));
            } catch(e2) {
              incomingDelta = JSON.parse(decodeURIComponent(syncData));
            }
          }

          if (incomingDelta && typeof incomingDelta === 'object') {
            let count = 0;
            for (const [idOrLink, val] of Object.entries(incomingDelta)) {
              const fullState = (val === 's' || val === 'saved') ? 'saved' : 'rejected';
              const match = rawJobsData.find(j => j.link && (j.link === idOrLink || j.link.includes(idOrLink)));
              if (match) {
                jobStates[match.link] = fullState;
                count++;
              } else {
                jobStates[idOrLink] = fullState;
                count++;
              }
            }
            saveTriageState(jobStates);
            window.history.replaceState({}, document.title, window.location.pathname);
            setTimeout(() => {
              showToast('🎉', count > 0 ? `סונכרנו בהצלחה ${count} משרות חדשות!` : 'הדשבורד מסונכרן ומעודכן!');
              updateUI();
            }, 300);
          }
        }
      } catch (e) {}
    }

    async function shareSyncLink() {
      const delta = getSyncDelta();
      const deltaKeys = Object.keys(delta);
      let shareUrl = window.location.origin + window.location.pathname;
      if (deltaKeys.length > 0) {
        const payload = encodeURIComponent(btoa(JSON.stringify(delta)));
        shareUrl += '?sync=' + payload;
      }
      
      if (navigator.share) {
        try {
          await navigator.share({
            title: 'דשבורד משרות - עידו גל',
            text: deltaKeys.length > 0 ? `סנכרון ${deltaKeys.length} משרות חדשות שסימנתי` : 'דשבורד משרות מעודכן',
            url: shareUrl
          });
          showToast('📲', 'הקישור שותף בהצלחה!');
          return;
        } catch (err) {}
      }
      
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(shareUrl).then(() => {
          showToast('🔗', 'קישור סנכרון הועתק! פתח אותו במכשיר השני');
        }).catch(() => {
          prompt('פתח קישור זה במכשיר השני לסנכרון מיידי:', shareUrl);
        });
      } else {
        prompt('פתח קישור זה במכשיר השני לסנכרון מיידי:', shareUrl);
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

      let sortedJobs = [...rawJobsData];
      sortedJobs.sort((a, b) => {
        const scoreA = Number(a.match_score) || 0;
        const scoreB = Number(b.match_score) || 0;
        return currentSort === 'desc' ? scoreB - scoreA : scoreA - scoreB;
      });

      sortedJobs.forEach((job, idx) => {
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
        const companyReqs = job.company_requirements || job.key_highlights || (job.snippet ? job.snippet.slice(0, 160) + '...' : '') || 'דרישות סף טכניות בהתאם לתיאור המשרה (פירוט מלא בקישור להגשה).';

        const card = document.createElement('article');
        card.setAttribute('data-id', id);
        card.setAttribute('data-sector', secKey);
        card.className = 'job-card bg-slate-900/80 border border-slate-800/90 rounded-2xl p-5 shadow-lg relative transition-all hover:border-slate-700';

        card.innerHTML = `
          <!-- Top row: Category tag, Big Title, Match Score -->
          <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3 border-b border-slate-800/80 pb-3 mb-4">
            <div class="flex-1">
              <span class="text-xs font-bold px-2.5 py-0.5 rounded-full ${badgeColor} border inline-block mb-1.5">
                ${sectorBadge}
              </span>
              <h2 class="text-lg font-bold text-white tracking-tight">${company} - ${title} <span class="text-xs font-normal text-slate-400 mr-2">• ${loc}</span></h2>
              <!-- Sub-header: דרישות החברה עבור המשרה -->
              <div class="mt-2 text-xs bg-slate-950/80 border border-sky-500/25 rounded-xl px-3 py-2 text-slate-300 flex items-start gap-2 shadow-inner">
                <span class="font-bold text-sky-400 shrink-0 flex items-center gap-1">
                  <span>📌</span> דרישות החברה עבור המשרה:
                </span>
                <span class="leading-relaxed text-slate-200">${companyReqs}</span>
              </div>
            </div>
            <div class="self-start sm:self-auto shrink-0">
              <span class="px-3 py-1 rounded-full text-xs font-extrabold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                <span>${score}%</span> התאמה
              </span>
            </div>
          </div>

          <!-- 3 Clean, Non-Redundant Sections -->
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

    function toggleSort() {
      currentSort = currentSort === 'desc' ? 'asc' : 'desc';
      const icon = document.getElementById('sortIcon');
      const label = document.getElementById('sortLabel');
      if (currentSort === 'desc') {
        if (icon) icon.textContent = '🔽';
        if (label) label.textContent = 'התאמה: מגבוה לנמוך';
        showToast('🔽', 'מיון: ציון התאמה מגבוה לנמוך');
      } else {
        if (icon) icon.textContent = '🔼';
        if (label) label.textContent = 'התאמה: מנמוך לגבוה';
        showToast('🔼', 'מיון: ציון התאמה מנמוך לגבוה');
      }
      renderCards();
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
      scheduleCloudPush();
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
      let saved = 0, rejected = 0, purged = 0;
      const total = cards.length;

      cards.forEach(card => {
        const id = card.getAttribute('data-id');
        const sector = card.getAttribute('data-sector');
        const state = jobStates[id] || 'pending';

        if (state === 'saved') saved++;
        if (state === 'rejected') rejected++;
        if (state === 'purged') purged++;

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
        if (currentFilter === 'all') matchesTab = (state !== 'saved' && state !== 'rejected' && state !== 'purged');
        else if (currentFilter === 'saved') matchesTab = (state === 'saved');
        else if (currentFilter === 'rejected') matchesTab = (state === 'rejected');

        let matchesSector = (selectedSector === 'all' || sector === selectedSector);

        if (matchesTab && matchesSector && state !== 'purged') {
          card.classList.remove('hidden');
          visibleCount++;
        } else {
          card.classList.add('hidden');
        }
      });

      const totalSavedInStore = Object.values(jobStates).filter(s => s === 'saved').length;
      const totalRejectedInStore = Object.values(jobStates).filter(s => s === 'rejected').length;
      const pendingInBatch = total - (saved + rejected + purged);

      document.getElementById('countAll').textContent = Math.max(0, pendingInBatch);
      document.getElementById('countSaved').textContent = totalSavedInStore;
      document.getElementById('countRejected').textContent = totalRejectedInStore;

      const triaged = saved + rejected + purged;
      const pct = total > 0 ? Math.round((triaged / total) * 100) : 0;
      document.getElementById('progressBar').style.width = pct + '%';
      document.getElementById('progressText').textContent = `סקרת ${triaged} מתוך ${total} משרות השבוע (${pct}%) • סה"כ שמורות: ${totalSavedInStore} | סה"כ הוסרו: ${totalRejectedInStore}`;

      const savedBar = document.getElementById('savedActionBar');
      const rejectedBar = document.getElementById('rejectedActionBar');
      if (savedBar) {
        if (currentFilter === 'saved') {
          savedBar.classList.remove('hidden');
        } else {
          savedBar.classList.add('hidden');
        }
      }
      if (rejectedBar) {
        if (currentFilter === 'rejected') {
          rejectedBar.classList.remove('hidden');
        } else {
          rejectedBar.classList.add('hidden');
        }
      }

      const emptyState = document.getElementById('emptyState');
      if (visibleCount === 0) {
        if (currentFilter === 'rejected') {
          emptyState.innerHTML = `
            <div class="text-4xl mb-2">🗑️</div>
            <div class="text-sm font-bold text-slate-300">כל ${totalRejectedInStore} המשרות שהוסרו מנוטרלות לצמיתות</div>
            <div class="text-xs text-slate-500 mt-1">משרות אלו סוננו מחלון ההזדמנויות השבועי ולא ישובו להופיע בדוחות הבאים.</div>
          `;
        } else if (currentFilter === 'saved') {
          emptyState.innerHTML = `
            <div class="text-4xl mb-2">⭐</div>
            <div class="text-sm font-bold text-slate-300">עדיין לא סימנת משרות שמורות מתוך מקבץ זה</div>
            <div class="text-xs text-slate-500 mt-1">לחץ על 'שמור להגשה' בכל כרטיס משרה שמעניינת אותך.</div>
          `;
        } else {
          emptyState.innerHTML = `
            <div class="text-4xl mb-2">🎉</div>
            <div class="text-sm font-bold text-slate-300">סיימת לסקור את כל המשרות החדשות!</div>
            <div class="text-xs text-slate-500 mt-1">כל המשרות במקבץ זה כבר מוינו (נשמרו או הוסרו).</div>
          `;
        }
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
        syncBtn.textContent = "שומר סימונים...";
      }

      saveTriageState(jobStates);
      await pushCloudSync();

      closeSyncModal();
      showToast('☁️', `כל הסימונים סונכרנו לענן בהצלחה! (${savedList.length} שמורות, ${rejectedList.length} הוסרו)`);
      if (syncBtn) {
        syncBtn.disabled = false;
        syncBtn.textContent = "סנכרן עכשיו לענן";
      }
    }

    function openDuplicatesModal() {
      const content = document.getElementById('duplicatesContent');

      // Normalize: lowercase, strip punctuation, collapse spaces
      function normalize(str) {
        if (!str) return '';
        return str.toLowerCase().replace(/[^א-תa-z0-9]/g, ' ').replace(/  +/g, ' ').trim();
      }

      // Group jobs by key = normalize(company) + '|' + normalize(title)
      const groups = {};
      rawJobsData.forEach((job, idx) => {
        const key = normalize(job.company) + '|' + normalize(job.title);
        if (!groups[key]) groups[key] = [];
        groups[key].push({ ...job, _idx: idx });
      });

      const dupGroups = Object.values(groups).filter(g => g.length > 1);

      if (dupGroups.length === 0) {
        content.innerHTML = `
          <div class="text-center py-8">
            <div class="text-4xl mb-3">✅</div>
            <div class="font-bold text-emerald-400 text-sm">לא נמצאו כפילויות!</div>
            <div class="text-slate-500 mt-1">כל ${rawJobsData.length} המשרות בדשבורד ייחודיות.</div>
          </div>`;
      } else {
        const totalDups = dupGroups.reduce((sum, g) => sum + g.length - 1, 0);
        let html = `
          <div class="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3 mb-2 flex items-center gap-2">
            <span class="text-amber-400 font-bold text-sm">⚠️</span>
            <span class="text-amber-300 font-semibold">נמצאו <span class="text-white">${dupGroups.length}</span> קבוצות עם <span class="text-white">${totalDups}</span> כפילויות בסך הכל</span>
          </div>`;

        dupGroups.forEach((group, gi) => {
          const rep = group[0];
          html += `
            <div class="bg-slate-800/60 border border-amber-500/20 rounded-xl p-3 space-y-2">
              <div class="flex items-center gap-2 font-bold text-amber-300">
                <span class="bg-amber-500/20 text-amber-400 rounded-full w-5 h-5 flex items-center justify-center text-[10px] font-extrabold shrink-0">${gi + 1}</span>
                <span>${rep.company || '—'} — ${rep.title || '—'}</span>
                <span class="mr-auto bg-amber-500/20 text-amber-400 text-[10px] px-2 py-0.5 rounded-full">${group.length} הופעות</span>
              </div>
              <div class="space-y-1.5 pr-7">`;
          group.forEach((job, ji) => {
            const score = job.match_score || '—';
            const date = job.date || '—';
            const link = job.link || '#';
            html += `
                <div class="flex items-center justify-between bg-slate-900/70 rounded-lg px-2.5 py-1.5 border border-slate-700/50">
                  <div class="flex items-center gap-2 text-slate-300">
                    <span class="text-[10px] text-slate-500">#${ji + 1}</span>
                    <span class="font-semibold text-emerald-400">${score}%</span>
                    <span class="text-slate-500">${date}</span>
                  </div>
                  <a href="${link}" target="_blank" rel="noopener noreferrer"
                     class="text-sky-400 hover:text-sky-300 font-bold underline underline-offset-2 text-[10px]">
                    פתח ↗
                  </a>
                </div>`;
          });
          html += `</div></div>`;
        });

        content.innerHTML = html;
      }

      document.getElementById('duplicatesModal').classList.remove('hidden');
      showToast('🔍', dupGroups.length > 0 ? `נמצאו ${dupGroups.length} קבוצות כפולות` : 'לא נמצאו כפילויות!');
    }

    function closeDuplicatesModal() {
      document.getElementById('duplicatesModal').classList.add('hidden');
    }

    function clearAllRejected() {
      const rejectedKeys = Object.keys(jobStates).filter(id => jobStates[id] === 'rejected');
      if (rejectedKeys.length === 0) {
        showToast('ℹ️', 'אין משרות מוסרות למחיקה');
        return;
      }

      if (!confirm(`האם אתה בטוח שברצונך למחוק לצמיתות ${rejectedKeys.length} משרות שהוסרו ולאפס את המונה?`)) {
        return;
      }

      // Mark as purged: NEVER show in new jobs, and NEVER show in rejected
      rejectedKeys.forEach(id => {
        jobStates[id] = 'purged';
      });

      saveTriageState(jobStates);
      updateUI();
      pushCloudSync();
      showToast('🗑️', `כל ${rejectedKeys.length} המשרות שהוסרו נמחקו לצמיתות והמונה אופס ל-0`);
    }

    function exportSavedToExcel() {
      const savedJobs = (rawJobsData || []).filter(job => jobStates[job.link] === 'saved');
      if (savedJobs.length === 0) {
        showToast('⚠️', 'לא נמצאו משרות שמורות לייצוא');
        return;
      }

      // UTF-8 BOM for seamless Hebrew display in Microsoft Excel
      const BOM = '\uFEFF';
      const headers = [
        'חברה',
        'כותרת משרה',
        'ציון התאמה',
        'תחום',
        'מיקום',
        'דרישות החברה עבור המשרה',
        'תחום ומוצר החברה',
        'תקציר המשרה',
        'נקודות חוזק מהניסיון',
        'דגשים ומודל עבודה',
        'קישור ישיר להגשה',
        'תאריך'
      ];

      const escapeCSV = (val) => {
        if (val === null || val === undefined) return '""';
        const str = String(val).replace(/"/g, '""');
        return `"${str}"`;
      };

      const rows = savedJobs.map(job => {
        const score = job.match_score ? `${job.match_score}%` : '';
        const reqs = job.company_requirements || job.key_highlights || (job.snippet ? job.snippet.slice(0, 160) : '') || '';
        const domain = job.company_domain_product || job.company_summary || '';
        const summary = job.job_summary || job.company_summary || '';
        const strengths = job.experience_strengths || job.reasoning || '';
        const highlights = job.key_highlights || (job.work_model ? `מודל: ${job.work_model}` : '');
        const date = job.date || '';

        return [
          escapeCSV(job.company || ''),
          escapeCSV(job.title || ''),
          escapeCSV(score),
          escapeCSV(job.sector || job.sector_key || ''),
          escapeCSV(job.location || 'ישראל'),
          escapeCSV(reqs),
          escapeCSV(domain),
          escapeCSV(summary),
          escapeCSV(strengths),
          escapeCSV(highlights),
          escapeCSV(job.link || ''),
          escapeCSV(date)
        ].join(',');
      });

      const csvContent = BOM + [headers.map(escapeCSV).join(','), ...rows].join(String.fromCharCode(13, 10));
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      const dateStr = new Date().toISOString().slice(0, 10);
      a.href = url;
      a.download = `משרות_שמורות_עידו_גל_${dateStr}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      showToast('📊', `יוצאו ${savedJobs.length} משרות שמורות לאקסל בהצלחה!`);
    }

    window.onload = () => {
      checkUrlSync();
      renderCards();
      fetchCloudSync();
    };

    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        fetchCloudSync();
      }
    });

    window.addEventListener('focus', () => {
      fetchCloudSync();
    });
  </script>
</body>
</html>"""

def generate_interactive_html(jobs, rejected_links, title="דוח משרות אינטראקטיבי | עידו גל", is_weekly=False):
    saved_links = []
    
    total_jobs = len(jobs)
    now_str = datetime.now().strftime("%d.%m.%Y")
    report_type_label = "סיכום שבועי" if is_weekly else "סריקה יומית"
    jobs_json = json.dumps(jobs, ensure_ascii=False)
    saved_json = json.dumps(saved_links, ensure_ascii=False)
    rejected_json = json.dumps(rejected_links, ensure_ascii=False)

    html = HTML_TEMPLATE
    html = html.replace("__TITLE__", title)
    html = html.replace("__REPORT_TYPE_LABEL__", report_type_label)
    html = html.replace("__NOW_STR__", now_str)
    html = html.replace("__TOTAL_JOBS__", str(total_jobs))
    html = html.replace("__JOBS_JSON__", jobs_json)
    html = html.replace("__INITIAL_SAVED_JSON__", saved_json)
    html = html.replace("__INITIAL_REJECTED_JSON__", rejected_json)
    return html

def build_and_save_docs_app(jobs, rejected_links, project_root, is_weekly=False):
    docs_dir = os.path.join(project_root, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    out_file = os.path.join(docs_dir, "index.html")
    
    html = generate_interactive_html(jobs, rejected_links, is_weekly=is_weekly)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[+] Successfully generated GitHub Pages interactive web app at: {out_file}")
    return out_file

def update_weekly_archive(new_jobs, archive_file_path, rejected_set):
    archive = []
    if os.path.exists(archive_file_path):
        try:
            with open(archive_file_path, "r", encoding="utf-8") as f:
                archive = json.load(f)
        except Exception:
            archive = []
            
    cutoff_date = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")
    archive = [j for j in archive if j.get("date", "") >= cutoff_date]
    
    archive = [j for j in archive if j.get("link") not in rejected_set]

    seen_links = {j.get("link") for j in archive}
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    if new_jobs:
        for job in new_jobs:
            link = job.get("link")
            if link and link not in seen_links and link not in rejected_set:
                seen_links.add(link)
                job_copy = dict(job)
                job_copy["date"] = today_str
                archive.append(job_copy)
            
    with open(archive_file_path, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=2)

    return archive
