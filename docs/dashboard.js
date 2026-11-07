let rawJobsData = (typeof __INLINE_JOBS_FALLBACK__ !== 'undefined') ? __INLINE_JOBS_FALLBACK__ : [];
  window.jobsData = rawJobsData;
  let historicalCatalog = (typeof __INLINE_CATALOG_FALLBACK__ !== 'undefined') ? __INLINE_CATALOG_FALLBACK__ : {};
  let isCatalogLoaded = false;
  let isJobsLoading = false;
  let jobsLoadError = null;
  const initialSavedLinks = [];
  const initialRejectedLinks = [];
  // Preserve legacy application records for explicit user-controlled migration.

  async function fetchJobsData() {
    isJobsLoading = true;
    jobsLoadError = null;
    const container = document.getElementById('cardsContainer');
    if (container && (!rawJobsData || rawJobsData.length === 0)) {
      container.innerHTML = `
        <div class="jobs-loading-state" id="jobsLoadingSpinner">
          <div class="jobs-loading-spinner"></div>
          <div><strong>טוען משרות עדכניות...</strong></div>
        </div>
      `;
    }

    const config = window.__APP_CONFIG__ || {};
    const jobsUrl = config.jobs_data_url || 'data/jobs.json';

    try {
      const resp = await fetch(jobsUrl, { cache: 'no-cache' });
      if (!resp.ok) {
        throw new Error('HTTP ' + resp.status + ' (' + resp.statusText + ')');
      }
      const data = await resp.json();
      const nextJobs = Array.isArray(data) ? data : data.jobs;
      if (!Array.isArray(nextJobs)) throw new Error('מבנה נתוני המשרות אינו תקין');
      if (!Array.isArray(data) && config.build_id && data.build_id && config.build_id !== data.build_id) {
        console.warn('[JOBS_FETCH] Note: Display build (' + config.build_id + ') differs from jobs payload build (' + data.build_id + '). Proceeding with payload rendering.');
      }
      rawJobsData = nextJobs;
      window.jobsData = rawJobsData;
      isJobsLoading = false;
      renderCards();
      updateUI();
      if (typeof populateAtsJobSelector === 'function') {
        populateAtsJobSelector();
      }

      // Preload historical catalog in the background so saved/starred jobs from older cycles are immediately available
      const currentLinks = new Set(rawJobsData.map(job => job.link));
      const needsHistory = [...Object.keys(starredJobs), ...Object.keys(jobStates)].some(link => !currentLinks.has(link));
      if (!isCatalogLoaded && needsHistory) {
        if (typeof window.requestIdleCallback === 'function') {
          window.requestIdleCallback(() => { loadHistoricalCatalogOnDemand(); }, { timeout: 2000 });
        } else {
          setTimeout(() => { loadHistoricalCatalogOnDemand(); }, 300);
        }
      }
    } catch (err) {
      console.warn('[JOBS_FETCH] Notice on fetching external jobs.json:', err);
      isJobsLoading = false;
      if (rawJobsData && rawJobsData.length > 0) {
        renderCards();
        updateUI();
        return;
      }
      jobsLoadError = err.message;
      if (container) {
        container.innerHTML = `
          <div class="jobs-error-banner">
            <div><i class="ph-bold ph-warning-circle" style="font-size: 24px;"></i></div>
            <div><strong>תקלה בטעינת נתוני המשרות</strong> (${escapeHtml(err.message)})</div>
            <div>בדוק חיבור רשת או פתח את הדשבורד תחת שרת מקומי.</div>
            <button type="button" class="btn-retry-load" onclick="fetchJobsData()">
              <i class="ph-bold ph-arrows-clockwise"></i>
              <span>נסה שנית</span>
            </button>
          </div>
        `;
      }
    }
  }

  let catalogLoadPromise = null;
  function loadHistoricalCatalogOnDemand() {
    if (isCatalogLoaded) return Promise.resolve();
    if (!catalogLoadPromise) {
      catalogLoadPromise = fetchHistoricalCatalog().finally(() => { catalogLoadPromise = null; });
    }
    return catalogLoadPromise;
  }

  async function fetchHistoricalCatalog() {
    if (isCatalogLoaded) return;
    const config = window.__APP_CONFIG__ || {};
    const catalogUrl = config.catalog_data_url || 'data/historical_catalog.json';
    try {
      const resp = await fetch(catalogUrl, { cache: 'no-cache' });
      if (resp.ok) {
        const cat = await resp.json();
        if (!cat || typeof cat !== 'object' || Array.isArray(cat)) throw new Error('Invalid catalog');
        historicalCatalog = cat;
        isCatalogLoaded = true;
        renderCards();
        updateUI();
      }
    } catch (e) {
      console.warn('[CATALOG_FETCH] Notice on historical catalog fetch:', e);
    }
  }

  function formatJobSalaryTag(job) {
    if (!job) return '';
    let sal = (job.salary_range || '').trim();
    if (!sal || sal === 'לא צוין במודעה' || sal === 'לא צוין שכר' || sal === 'לא צוין') {
      return '';
    }
    // Clean any accidental word 'הערכה'
    sal = sal.replace(/הערכה\s*(?:חודשית|פנימית|בלבד)?/g, '').replace(/—\s*$/, '').replace(/;\s*:/g, ':').trim();
    sal = sal.replace(/\(\s*\)/g, '').trim();

    const isAd = job.salary_source_type === 'job_ad' || job.salary_source_type === 'ad' || job.salary_source_type === 'employer';
    if (isAd) {
      return `<span class="job-salary-chip salary-chip-ad" title="שכר שפורסם במודעת המשרה"><i class="ph-duotone ph-coins"></i> ${escapeHtml(sal)} (במודעה)</span>`;
    }
    return `<span class="job-salary-chip salary-chip-benchmark" title="טווח שכר ענפי מותאם לתפקיד"><i class="ph-duotone ph-coins"></i> ${escapeHtml(sal)}</span>`;
  }

  function formatJobScopeAndRole(job) {
    if (!job) return 'מידע על תחום ומוצר החברה לא צוין.';
    const domainRaw = stripEmojis(job.company_domain_product || job.company_summary || '').trim();
    const summaryRaw = stripEmojis(job.job_summary || '').trim();
    const domain = (domainRaw && domainRaw !== 'לא צוין' && domainRaw !== 'מידע על החברה לא צוין') ? domainRaw : '';
    const summary = (summaryRaw && summaryRaw !== 'לא צוין' && summaryRaw !== 'לא צוין תיאור מלא למשרה.') ? summaryRaw : '';

    if (domain && summary) {
      if (summary.includes(domain)) return escapeHtml(summary);
      if (domain.includes(summary)) return escapeHtml(domain);
      return `${escapeHtml(domain)} | ${escapeHtml(summary)}`;
    }
    return escapeHtml(domain || summary || 'מידע על תחום ומוצר החברה לא צוין.');
  }

  function formatJobMatchAndGaps(job) {
    if (!job) {
      return {
        isNoGap: true,
        badgeHtml: '<span class="gap-status-pill gap-status-ok">[OK] ללא פערי סף</span>',
        statusHtml: '<span class="gap-text-ok">[OK] עונה על דרישות הסף</span>',
        fullHtml: '<span class="gap-text-ok">[OK] ללא פערי סף מהותיים</span>'
      };
    }
    const insightRaw = stripEmojis(job.reasoning || job.experience_strengths || '').trim();
    const gapsRaw = stripEmojis(job.fit_gaps || '').trim();

    const isNoGap = !gapsRaw ||
      gapsRaw.includes('אין פערי סף') ||
      gapsRaw.includes('אין פער') ||
      gapsRaw.includes('עונה על דרישות') ||
      gapsRaw.includes('ללא פער');

    let badgeHtml = '';
    let statusHtml = '';

    if (isNoGap) {
      badgeHtml = '<span class="gap-status-pill gap-status-ok">[OK] ללא פערי סף</span>';
      statusHtml = '<span class="gap-text-ok">[OK] עונה על דרישות הסף</span>';
    } else {
      badgeHtml = '<span class="gap-status-pill gap-status-alert">[פער] קיים פער סף</span>';
      statusHtml = `<span class="gap-text-alert">[פער] ${escapeHtml(gapsRaw)}</span>`;
    }

    const cleanInsight = (insightRaw && insightRaw !== 'אין ניתוח התאמה מאומת למשרה זו.')
      ? escapeHtml(insightRaw)
      : 'התאמה טכנית ומקצועית לדרישות התפקיד';

    return {
      isNoGap,
      badgeHtml,
      statusHtml,
      fullHtml: `${cleanInsight} | ${statusHtml}`
    };
  }

  function renderEvaluationMetadata(job) {
    return '';
  }

  function renderRequirementAssessmentsHtml(assessments) {
    if (!assessments || !Array.isArray(assessments) || assessments.length === 0) {
      return '<div style="font-size: 12px; color: var(--dashboard-muted); font-style: italic; padding: 4px 0;">אין פירוט ראיות מובנה להערכה זו</div>';
    }

    return `
      <div class="evidence-container">
        ${assessments.filter(item => item && typeof item === 'object').map(item => {
          const req = escapeHtml(stripEmojis(item.requirement || 'דרישה'));
          const imp = item.importance || 'unknown';
          const impLabel = imp === 'required' ? 'חובה' : (imp === 'preferred' ? 'יתרון' : 'כללי');
          const impClass = imp === 'required' ? 'required' : (imp === 'preferred' ? 'preferred' : '');

          const assess = ['match','gap','unknown'].includes(item.assessment) ? item.assessment : 'unknown';
          let assessLabel = 'בבדיקה';
          let assessIcon = 'ph-question';
          if (assess === 'match') {
            assessLabel = 'התאמה מלאה';
            assessIcon = 'ph-check-circle';
          } else if (assess === 'gap') {
            assessLabel = 'פער';
            assessIcon = 'ph-warning';
          }

          const adQuote = (item.ad_evidence && item.ad_evidence.quote) ? escapeHtml(stripEmojis(item.ad_evidence.quote)) : '';
          const profQuote = (item.profile_evidence && item.profile_evidence.quote) ? escapeHtml(stripEmojis(item.profile_evidence.quote)) : '';
          const explanation = item.explanation ? escapeHtml(stripEmojis(item.explanation)) : '';

          return `
            <div class="evidence-item">
              <div class="evidence-header">
                <span class="evidence-req-title">
                  <span class="badge-importance ${impClass}">${impLabel}</span>
                  <span>${req}</span>
                </span>
                <span class="badge-assessment ${assess}">
                  <i class="ph-bold ${assessIcon}"></i> ${assessLabel}
                </span>
              </div>
              ${(adQuote || profQuote) ? `
                <div class="evidence-quotes-block">
                  ${adQuote ? `<div class="evidence-quote-line"><strong>ציטוט מהמודעה:</strong> "${adQuote}"</div>` : ''}
                  ${profQuote ? `<div class="evidence-quote-line"><strong>ראיה מהפרופיל:</strong> "${profQuote}"</div>` : ''}
                </div>
              ` : ''}
              ${explanation ? `<div style="font-size: 11.5px; color: #cbd5e1; margin-top: 2px;">${explanation}</div>` : ''}
            </div>
          `;
        }).join('')}
      </div>
    `;
  }
  let currentFilter = 'all';
  let currentSort = 'date_desc';
  const STORAGE_KEY = 'ido_job_triage_store';
  const STARRED_STORAGE_KEY = 'ido_job_starred_store';
  const ALT_LINKS_STORAGE_KEY = 'ido_job_alt_links_store';
  const LAST_LOCAL_EDIT_KEY = 'ido_job_last_local_edit_time';
  const VIEW_MODE_KEY = 'ido_job_view_mode';
  const SORT_STORAGE_KEY = 'ido_job_sort_mode';
  let currentViewMode = 'grid';
  let allJobsMap = {};
  let altLinksStore = loadAltLinksState();

  function recordLocalEdit() {
    try {
      localStorage.setItem(LAST_LOCAL_EDIT_KEY, String(Date.now()));
    } catch (e) {}
  }

  function loadAltLinksState() {
    try {
      const stored = localStorage.getItem(ALT_LINKS_STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed && typeof parsed === 'object') return parsed;
      }
    } catch (e) {}
    return {};
  }

  function saveAltLinksState(state) {
    try {
      localStorage.setItem(ALT_LINKS_STORAGE_KEY, JSON.stringify(state));
    } catch (e) {}
  }
  try {
    const savedView = localStorage.getItem(VIEW_MODE_KEY);
    if (savedView === 'map') {
      currentViewMode = 'map';
    } else {
      currentViewMode = 'grid';
    }
  } catch(e) {
    currentViewMode = 'grid';
  }
  try {
    currentSort = localStorage.getItem(SORT_STORAGE_KEY) || 'date_desc';
  } catch(e) {}
  const DEFAULT_STARRED_JOBS = [
    "https://il.linkedin.com/jobs/view/junior-solar-account-coordinator-at-amarel-ltd-4481350574",
    "https://il.linkedin.com/jobs/view/practical-engineer-at-solaredge-technologies-4481748648",
    "https://il.linkedin.com/jobs/view/system-engineer-renewable-energy-energy-storage-projects-at-nextcom-group-4478214360",
    "https://il.linkedin.com/jobs/view/%D7%AA%D7%94%D7%9C%D7%99%D7%9B%D7%99-%D7%91%D7%A7%D7%A8%D7%94-%D7%95-ai-at-iai-israel-aerospace-industries-4478429532",
    "https://www.comeet.com/jobs/enlightenergy/99.006/project-manager---construction---enlight-local/92.F66",
    "https://il.linkedin.com/jobs/view/high-pressure-natural-gas-project-israel-at-rina-4469463836"
  ];

  const UNSTARRED_STORAGE_KEY = 'ido_job_unstarred_keys';
  const RESTORED_STORAGE_KEY = 'ido_job_restored_keys';

  function loadUnstarredJobs() {
    try {
      const stored = localStorage.getItem(UNSTARRED_STORAGE_KEY);
      if (stored) return JSON.parse(stored) || {};
    } catch (e) {}
    return {};
  }

  function saveUnstarredJobs(map) {
    try {
      localStorage.setItem(UNSTARRED_STORAGE_KEY, JSON.stringify(map || {}));
    } catch (e) {}
  }

  function loadRestoredJobs() {
    try {
      const stored = localStorage.getItem(RESTORED_STORAGE_KEY);
      if (stored) return JSON.parse(stored) || {};
    } catch (e) {}
    return {};
  }

  function saveRestoredJobs(map) {
    try {
      localStorage.setItem(RESTORED_STORAGE_KEY, JSON.stringify(map || {}));
    } catch (e) {}
  }

  let jobStates = loadTriageState();
  let starredJobs = loadStarredJobs();

  function getCanonicalJobKey(link) {
    if (!link) return '';
    try {
      let clean = String(link).trim().split('?')[0].split('#')[0].replace(/\/+$/, '');
      clean = clean.replace(/^(https?:\/\/)[a-z]{2,3}\.linkedin\.com\//i, '$1www.linkedin.com/');
      const liMatch = clean.match(/\/jobs\/view\/(?:[^\/]+-)?(\d{8,12})/i) || clean.match(/\/jobs\/view\/(\d{8,12})/i);
      if (liMatch) return 'li_' + liMatch[1];
      const drushimMatch = clean.match(/\/job\/(\d+)/i);
      if (drushimMatch) return 'drushim_' + drushimMatch[1];
      const comeetMatch = clean.match(/comeet\.com\/jobs\/(?:[^\/]+\/)+([^\/?#]+)/i);
      if (comeetMatch) return 'comeet_' + comeetMatch[1];
      return clean.toLowerCase();
    } catch (e) {
      return String(link).trim().toLowerCase();
    }
  }

  function normalizeTextForHash(text) {
    if (!text) return '';
    let cleaned = String(text).replace(/[\u200b-\u200f\u00a0\ufeff]/g, ' ').toLowerCase();
    cleaned = cleaned.replace(/\/ת\b|\/ה\b|\/ית\b/g, '');
    cleaned = cleaned.replace(/\((?:m\/f|d\/m\/w|גברים\/נשים|מ\/נ|דיסקרטי|דרושים|דרוש|דרושה)\)/g, ' ');
    cleaned = cleaned.replace(/\b(?:בע"מ|בעמ|בע״מ|ltd\.?|inc\.?|corp\.?|gmbh|llc)\b/g, ' ');
    cleaned = cleaned.replace(/[^\w\sא-ת]/g, ' ');
    return cleaned.trim().replace(/\s+/g, ' ');
  }

  function getContentJobHash(jobOrLink) {
    if (!jobOrLink) return '';
    if (typeof jobOrLink === 'object') {
      if (jobOrLink.content_hash) return jobOrLink.content_hash;
      const comp = normalizeTextForHash(jobOrLink.company || '');
      const tit = normalizeTextForHash(jobOrLink.title || '');
      if (comp && tit) {
        let hash = 0;
        const str = `${comp}|${tit}`;
        for (let i = 0; i < str.length; i++) {
          hash = ((hash << 5) - hash) + str.charCodeAt(i);
          hash |= 0;
        }
        return 'ch_' + Math.abs(hash).toString(36);
      }
    }
    return '';
  }

  function getJobKeys(idOrJob) {
    const keys = [];
    if (!idOrJob) return keys;
    let job = null;
    let id = '';
    if (typeof idOrJob === 'string') {
      id = idOrJob;
      job = (typeof allJobsMap !== 'undefined' && allJobsMap[id]) ||
            (rawJobsData || []).find(j => j.link === id) ||
            (typeof historicalCatalog !== 'undefined' && historicalCatalog[id]) || null;
    } else if (typeof idOrJob === 'object') {
      job = idOrJob;
      id = job.link || '';
    }
    if (id) keys.push(id);
    const canon = getCanonicalJobKey(id);
    if (canon && !keys.includes(canon)) keys.push(canon);
    if (job) {
      if (job.stable_job_id && !keys.includes(job.stable_job_id)) keys.push(job.stable_job_id);
      const sid = getStableJobId(job);
      if (sid && !keys.includes(sid)) keys.push(sid);
      if (job.content_hash && !keys.includes(job.content_hash)) keys.push(job.content_hash);
      const ch = getContentJobHash(job);
      if (ch && !keys.includes(ch)) keys.push(ch);
    }
    return keys;
  }

  function getStableJobId(jobOrLink) {
    if (!jobOrLink) return '';
    if (typeof jobOrLink === 'string') return getCanonicalJobKey(jobOrLink);
    if (jobOrLink.stable_job_id) return jobOrLink.stable_job_id;
    const link = jobOrLink.link || '';
    const canon = getCanonicalJobKey(link);
    if (canon && !canon.startsWith('http')) return canon;
    const ch = getContentJobHash(jobOrLink);
    if (ch) return ch;
    return canon || String(link).trim().toLowerCase();
  }

  function getJobState(id) {
    if (!id || typeof jobStates !== 'object' || jobStates === null) return 'pending';
    const keys = getJobKeys(id);
    for (const k of keys) {
      if (jobStates[k]) return jobStates[k];
    }
    return 'pending';
  }

  function isJobStarred(id) {
    if (!id || typeof starredJobs !== 'object' || starredJobs === null) return false;
    const keys = getJobKeys(id);
    const unstarredMap = loadUnstarredJobs();
    for (const k of keys) {
      if (unstarredMap[k]) return false;
    }
    for (const k of keys) {
      if (starredJobs[k]) return true;
    }
    return false;
  }

  function loadStarredJobs() {
    let stars = {};
    let stored = null;
    const unstarredMap = loadUnstarredJobs();
    try {
      stored = localStorage.getItem(STARRED_STORAGE_KEY);
      if (stored !== null) {
        stars = JSON.parse(stored);
      }
    } catch(e) {
      stars = {};
    }

    if (!stars || typeof stars !== 'object') {
      stars = {};
    }

    // Default restore verified starred jobs only on very first clean initialization
    if (stored === null && Array.isArray(DEFAULT_STARRED_JOBS)) {
      DEFAULT_STARRED_JOBS.forEach(link => {
        const canon = getCanonicalJobKey(link);
        if (!unstarredMap[link] && !unstarredMap[canon]) {
          stars[link] = true;
          if (canon) stars[canon] = true;
        }
      });
      try {
        localStorage.setItem(STARRED_STORAGE_KEY, JSON.stringify(stars));
      } catch(e) {}
    }

    // Filter out unstarred tombstones
    Object.keys(unstarredMap).forEach(key => {
      delete stars[key];
    });

    // Authoritative state reconciliation: rejection or purge supersedes starred
    if (typeof jobStates === 'object' && jobStates !== null) {
      Object.keys(stars).forEach(link => {
        const canon = getCanonicalJobKey(link);
        if (stars[link] && (jobStates[link] === 'purged' || jobStates[link] === 'rejected' || jobStates[canon] === 'purged' || jobStates[canon] === 'rejected')) {
          delete stars[link];
          if (canon) delete stars[canon];
        }
      });
    }

    return stars;
  }

  function saveStarredJobs(stars) {
    try {
      localStorage.setItem(STARRED_STORAGE_KEY, JSON.stringify(stars || {}));
    } catch(e) {}
  }

  function updateCubeCountsImmediately() {
    try {
      updateUI();
    } catch(e) {}
  }

  function toggleStar(id, evt) {
    if (evt) {
      evt.stopPropagation();
      evt.preventDefault();
    }
    recordLocalEdit();
    const keys = getJobKeys(id);
    const currentlyStarred = isJobStarred(id);
    const unstarredMap = loadUnstarredJobs();

    if (currentlyStarred) {
      keys.forEach(k => {
        delete starredJobs[k];
        unstarredMap[k] = true;
      });
      for (const k of Object.keys(starredJobs)) {
        if (keys.some(ref => getCanonicalJobKey(k) === getCanonicalJobKey(ref))) delete starredJobs[k];
      }
      saveUnstarredJobs(unstarredMap);
      showToast('ph-star', 'הוסר מהמשרות המסומנות בכוכב');
    } else {
      keys.forEach(k => {
        starredJobs[k] = true;
        delete unstarredMap[k];
        if (jobStates && (jobStates[k] === 'purged' || jobStates[k] === 'rejected')) {
          delete jobStates[k];
        }
      });
      saveUnstarredJobs(unstarredMap);
      saveTriageState(jobStates);
      showToast('ph-fill ph-star', 'המשרה סומנה בכוכב והועברה ללשונית בכוכב');
    }
    saveStarredJobs(starredJobs);
    scheduleCloudPush();

    document.querySelectorAll('.job-card').forEach(card => {
      const cardId = card.getAttribute('data-id');
      if (cardId === id || getCanonicalJobKey(cardId) === canon) {
        const starBtn = card.querySelector('.btn-star');
        const activeStar = isJobStarred(cardId);
        if (starBtn) {
          starBtn.className = activeStar ? 'btn-star is-starred' : 'btn-star';
          starBtn.setAttribute('title', activeStar ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב');
          starBtn.setAttribute('aria-label', activeStar ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב');
          starBtn.innerHTML = activeStar ? '<i class="ph-fill ph-star" style="color: var(--dashboard-gold);"></i>' : '<i class="ph-bold ph-star"></i>';
        }
        card.classList.toggle('is-starred-card', activeStar);
        card.setAttribute('data-starred', activeStar ? 'true' : 'false');
      }
    });

    const currentCardCount = document.querySelectorAll('.job-card').length;
    const availableCount = getAllAvailableJobs().length;
    if (currentCardCount !== availableCount) {
      renderCards();
      return;
    }

    updateUI();
  }

  function setViewMode(mode) {
    currentViewMode = (mode === 'map') ? 'map' : 'grid';
    try {
      localStorage.setItem(VIEW_MODE_KEY, currentViewMode);
    } catch(e) {}
    const container = document.getElementById('cardsContainer');
    const mapContainer = document.getElementById('mapViewContainer');
    const gridBtn = document.getElementById('viewGridBtn');
    const mapBtn = document.getElementById('viewMapBtn');
    if (!container || !mapContainer) return;

    if (currentViewMode === 'map') {
      container.classList.add('is-hidden-by-map');
      container.style.display = 'none';
      mapContainer.style.display = 'block';
      if (gridBtn) gridBtn.classList.remove('active');
      if (mapBtn) mapBtn.classList.add('active');

      if (!liveJobsMapInstance) {
        initLiveJobsMap();
      }
      setTimeout(() => {
        if (liveJobsMapInstance) {
          liveJobsMapInstance.invalidateSize();
        }
      }, 150);
      updateMapMarkers();
    } else {
      mapContainer.style.display = 'none';
      container.classList.remove('is-hidden-by-map');
      container.style.display = '';
      if (gridBtn) gridBtn.classList.add('active');
      if (mapBtn) mapBtn.classList.remove('active');
    }
  }

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

    // Deduplicate / canonicalize pure numeric IDs to full URLs
    Object.keys(state).forEach(key => {
      if (/^\d+$/.test(key)) {
        const matchingLink = Object.keys(state).find(k => k !== key && k.includes(key));
        if (matchingLink) {
          if (state[key] === 'saved' && state[matchingLink] !== 'saved') {
            state[matchingLink] = 'saved';
          }
          delete state[key];
        }
      }
    });

    return state;
  }

  // Authenticated per-user adapter must enforce authorization and conflict-safe writes.
  const privateSync = window.__PRIVATE_SYNC__ || null;
  let cloudSyncTimeout = null;
  let cloudLastUpdated = 0;
  let isSyncInProgress = false;

  function formatSyncTime(ts) {
    if (!ts) return '';
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' });
    } catch(e) {
      return '';
    }
  }

  function setCloudSyncStatus(status, timestamp) {
    const cloudBadge = document.getElementById('cloudSyncStatus');
    const headerDot = document.getElementById('headerSyncDot');
    const headerIcon = document.getElementById('headerSyncIcon');
    const lastSyncEl = document.getElementById('lastSyncTimeChip');

    if (timestamp && lastSyncEl) {
      const timeStr = formatSyncTime(timestamp);
      if (timeStr) lastSyncEl.textContent = `סונכרן: ${timeStr}`;
    }

    if (status === 'synced') {
      if (headerDot) {
        headerDot.className = 'sync-status-dot synced';
        headerDot.title = 'ענן מסונכרן';
      }
      if (headerIcon) headerIcon.classList.remove('ph-spin');
      if (cloudBadge) {
        cloudBadge.className = 'dashboard-chip cloud-synced';
        cloudBadge.style.color = 'var(--dashboard-cyan)';
        cloudBadge.style.borderColor = 'rgba(137, 244, 231, 0.4)';
        cloudBadge.innerHTML = '<span class="dashboard-dot" style="background: var(--dashboard-cyan); box-shadow: 0 0 8px var(--dashboard-cyan);"></span> <i class="ph-duotone ph-cloud-check"></i> <span>ענן מסונכרן</span>';
      }
    } else if (status === 'syncing') {
      if (headerDot) {
        headerDot.className = 'sync-status-dot syncing';
        headerDot.title = 'מעדכן ענן...';
      }
      if (headerIcon) headerIcon.classList.add('ph-spin');
      if (cloudBadge) {
        cloudBadge.className = 'dashboard-chip cloud-syncing';
        cloudBadge.style.color = 'var(--dashboard-gold)';
        cloudBadge.style.borderColor = 'rgba(255, 211, 104, 0.4)';
        cloudBadge.innerHTML = '<span class="dashboard-dot" style="background: var(--dashboard-gold); box-shadow: 0 0 8px var(--dashboard-gold);"></span> <i class="ph-duotone ph-cloud-arrow-up"></i> <span>מעדכן ענן...</span>';
      }
    } else if (status === 'local') {
      if (headerDot) {
        headerDot.className = 'sync-status-dot local';
        headerDot.title = 'אחסון מקומי (פרטי)';
      }
      if (headerIcon) headerIcon.classList.remove('ph-spin');
      if (cloudBadge) {
        cloudBadge.className = 'dashboard-chip cloud-local';
        cloudBadge.style.color = 'var(--dashboard-cyan, #89f4e7)';
        cloudBadge.style.borderColor = 'rgba(137, 244, 231, 0.4)';
        cloudBadge.innerHTML = '<span class="dashboard-dot" style="background: var(--dashboard-cyan, #89f4e7); box-shadow: 0 0 8px var(--dashboard-cyan, #89f4e7);"></span> <i class="ph-duotone ph-hard-drive"></i> <span>אחסון מקומי</span>';
      }
    } else if (status === 'offline' || status === 'error') {
      if (headerDot) {
        headerDot.className = 'sync-status-dot offline';
        headerDot.title = 'לא מקוון / שגיאת סנכרון';
      }
      if (headerIcon) headerIcon.classList.remove('ph-spin');
      if (cloudBadge) {
        cloudBadge.className = 'dashboard-chip cloud-offline';
        cloudBadge.style.color = '#f87171';
        cloudBadge.style.borderColor = 'rgba(248, 113, 113, 0.4)';
        cloudBadge.innerHTML = '<span class="dashboard-dot" style="background: #f87171; box-shadow: 0 0 8px rgba(248, 113, 113, 0.6);"></span> <i class="ph-duotone ph-cloud-slash"></i> <span>לא מקוון</span>';
      }
    }
  }

  async function fetchCloudSync(forceMirror = false) {
    if (isSyncInProgress) return;
    if (typeof navigator !== 'undefined' && navigator.onLine === false) {
      setCloudSyncStatus('offline');
      return;
    }
    isSyncInProgress = true;
    try {
      setCloudSyncStatus('syncing');
      let data = null;
      if (privateSync) {
        try {
          const resp = await privateSync.read();
          if (resp && resp.ok) {
            data = await resp.json();
          }
        } catch(e) {}
      }
      if (!data) {
        const config = window.__APP_CONFIG__ || {};
        const syncUrl = config.sync_data_url || 'data/sync_state.json';
        try {
          const resp = await fetch(syncUrl + (syncUrl.includes('?') ? '&' : '?') + 't=' + Date.now(), { cache: 'no-store' });
          if (resp && resp.ok) {
            data = await resp.json();
          }
        } catch(e) {}
      }
      if (data) {
        const remoteTimestamp = data.updated_at ? new Date(data.updated_at).getTime() : 0;
        if (remoteTimestamp) {
          cloudLastUpdated = remoteTimestamp;
        }

        const lastLocalEdit = Number(localStorage.getItem(LAST_LOCAL_EDIT_KEY) || 0);
        const storedTriage = localStorage.getItem(STORAGE_KEY);
        const storedStarred = localStorage.getItem(STARRED_STORAGE_KEY);
        const isClientVirgin = (lastLocalEdit === 0) && (!storedTriage || storedTriage === '{}') && (!storedStarred || storedStarred === '{}');
        const shouldMirrorFromRemote = forceMirror || isClientVirgin;

        if (shouldMirrorFromRemote) {
          const newJobStates = {};
          if (Array.isArray(data.purged)) {
            data.purged.forEach(link => {
              newJobStates[link] = 'purged';
              const c = getCanonicalJobKey(link);
              if (c) newJobStates[c] = 'purged';
            });
          }
          if (Array.isArray(data.saved)) {
            data.saved.forEach(link => {
              newJobStates[link] = 'saved';
              const c = getCanonicalJobKey(link);
              if (c) newJobStates[c] = 'saved';
            });
          }
          if (Array.isArray(data.rejected)) {
            data.rejected.forEach(link => {
              newJobStates[link] = 'rejected';
              const c = getCanonicalJobKey(link);
              if (c) newJobStates[c] = 'rejected';
            });
          }
          const newStarredJobs = {};
          if (Array.isArray(data.starred)) {
            data.starred.forEach(link => {
              newStarredJobs[link] = true;
              const c = getCanonicalJobKey(link);
              if (c) newStarredJobs[c] = true;
            });
          }
          // Clean up conflicting starred states (rejection/purged trumps starred)
          Object.keys(newStarredJobs).forEach(link => {
            const c = getCanonicalJobKey(link);
            if (newJobStates[link] === 'purged' || newJobStates[link] === 'rejected' || newJobStates[c] === 'purged' || newJobStates[c] === 'rejected') {
              delete newStarredJobs[link];
              if (c) delete newStarredJobs[c];
            }
          });
          jobStates = newJobStates;
          starredJobs = newStarredJobs;
          saveStarredJobs(starredJobs);
          saveTriageState(jobStates);
          renderCards();
          updateUI();
        } else {
          // Device has existing local edits: reconcile safely without overwriting user choices
          let changed = false;
          const unstarredMap = loadUnstarredJobs();
          const restoredMap = loadRestoredJobs();

          if (Array.isArray(data.purged)) {
            data.purged.forEach(link => {
              const c = getCanonicalJobKey(link);
              if (!restoredMap[link] && !restoredMap[c] && jobStates[link] !== 'saved' && jobStates[c] !== 'saved') {
                if (jobStates[link] !== 'purged') {
                  jobStates[link] = 'purged';
                  if (c) jobStates[c] = 'purged';
                  changed = true;
                }
              }
            });
          }
          if (Array.isArray(data.rejected)) {
            data.rejected.forEach(link => {
              const c = getCanonicalJobKey(link);
              if (!restoredMap[link] && !restoredMap[c] && (!jobStates[link] || jobStates[link] === 'pending')) {
                jobStates[link] = 'rejected';
                if (c) jobStates[c] = 'rejected';
                changed = true;
              }
            });
          }
          if (Array.isArray(data.saved)) {
            data.saved.forEach(link => {
              const c = getCanonicalJobKey(link);
              if (!jobStates[link] && !jobStates[c]) {
                jobStates[link] = 'saved';
                if (c) jobStates[c] = 'saved';
                changed = true;
              }
            });
          }
          if (Array.isArray(data.starred)) {
            data.starred.forEach(link => {
              const c = getCanonicalJobKey(link);
              if (!unstarredMap[link] && !unstarredMap[c] && !starredJobs[link] && !starredJobs[c]) {
                if (jobStates[link] !== 'purged' && jobStates[link] !== 'rejected' && jobStates[c] !== 'purged' && jobStates[c] !== 'rejected') {
                  starredJobs[link] = true;
                  if (c) starredJobs[c] = true;
                  changed = true;
                }
              }
            });
          }
          if (changed) {
            saveStarredJobs(starredJobs);
            saveTriageState(jobStates);
            renderCards();
            updateUI();
          }
        }
        setCloudSyncStatus('synced', cloudLastUpdated || Date.now());
      } else {
        setCloudSyncStatus('synced', Date.now());
      }
    } catch (e) {
      setCloudSyncStatus('offline');
    } finally {
      isSyncInProgress = false;
    }
  }

  function scheduleCloudPush() {
    if (cloudSyncTimeout) clearTimeout(cloudSyncTimeout);
    cloudSyncTimeout = setTimeout(pushCloudSync, 400);
  }

  async function pushCloudSync() {
    if (isSyncInProgress) return;
    if (typeof navigator !== 'undefined' && navigator.onLine === false) {
      setCloudSyncStatus('offline');
      return;
    }
    isSyncInProgress = true;
    setCloudSyncStatus('syncing');

    try {
      const savedList = Object.keys(jobStates).filter(id => jobStates[id] === 'saved' && !Boolean(starredJobs[id]));
      const starredList = Object.keys(starredJobs).filter(id => Boolean(starredJobs[id]));
      const rejectedList = Object.keys(jobStates).filter(id => jobStates[id] === 'rejected' && !Boolean(starredJobs[id]));
      const purgedList = Object.keys(jobStates).filter(id => jobStates[id] === 'purged' && !Boolean(starredJobs[id]));
      
      const timestamp = new Date().toISOString();
      const payload = {
        saved: savedList,
        starred: starredList,
        rejected: rejectedList,
        purged: purgedList,
        updated_at: timestamp
      };

      if (!privateSync) { setCloudSyncStatus('local'); return; }
      const resp = await privateSync.compareAndSwap(payload, cloudLastUpdated);
      if (resp.ok) {
        cloudLastUpdated = Date.now();
        setCloudSyncStatus('synced', cloudLastUpdated);
      } else {
        setCloudSyncStatus('offline');
      }
    } catch (e) {
      setCloudSyncStatus('offline');
    } finally {
      isSyncInProgress = false;
    }
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('online', () => { fetchCloudSync(); });
    window.addEventListener('offline', () => { setCloudSyncStatus('offline'); });
  }

  function extractJobId(link) {
    if (!link) return '';
    const match = link.match(/(\d{7,12})/);
    return match ? match[1] : link;
  }

  function getSyncDelta() {
    const delta = {};
    for (const [link, state] of Object.entries(jobStates)) {
      if (state === 'saved') {
        delta[extractJobId(link)] = 's';
      } else if (state === 'rejected') {
        delta[extractJobId(link)] = 'r';
      }
    }
    for (const [link, isStar] of Object.entries(starredJobs)) {
      if (isStar) {
        delta[extractJobId(link)] = '*';
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
            const match = (rawJobsData || []).find(j => j.link && (j.link === idOrLink || j.link.includes(idOrLink)));
            const targetLink = match ? match.link : idOrLink;
            if (val === '*' || val === 'starred') {
              starredJobs[targetLink] = true;
              if (jobStates[targetLink] === 'rejected' || jobStates[targetLink] === 'purged') {
                delete jobStates[targetLink];
              }
            } else if (val === 's' || val === 'saved') {
              jobStates[targetLink] = 'saved';
            } else {
              jobStates[targetLink] = 'rejected';
            }
            count++;
          }
          recordLocalEdit();
          saveStarredJobs(starredJobs);
          saveTriageState(jobStates);
          window.history.replaceState({}, document.title, window.location.pathname);
          setTimeout(() => {
            showToast('ph-check-circle', count > 0 ? `סונכרנו בהצלחה ${count} משרות מהקישור!` : 'הדשבורד מסונכרן ומעודכן!');
            updateCubeCountsImmediately();
            renderCards();
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
        showToast('ph-share-network', 'הקישור שותף בהצלחה!');
        return;
      } catch (err) {}
    }
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(shareUrl).then(() => {
        showToast('ph-link', 'קישור סנכרון הועתק! פתח אותו במכשיר השני');
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

  const KNOWN_COMPANY_DOMAINS = [
    // Energy / Gas / Solar / Infrastructure
    [['iec', 'חברת החשמל', 'חברת חשמל'], 'iec.co.il'],
    [['energean', "אנרג'יאן", "אנרג׳יאן", "אנרג'אן"], 'energean.com'],
    [['alumenergy', "אלומאנרג'י", "אלומנרג'י", "אלומנרג׳י", 'אלומוט'], 'alumenergy.co.il'],
    [['opc', 'או פי סי', 'רותם', 'חדרה'], 'opc-energy.com'],
    [['bazan', 'בזן', 'בז״ן', 'בתי זיקוק'], 'bazan.co.il'],
    [['supergas', 'סופרגז'], 'supergas.co.il'],
    [['paz', 'פז'], 'paz.co.il'],
    [['amisragas', 'אמישראגז', 'אמישרא גז'], 'amisragas.co.il'],
    [['delek', 'דלק'], 'delek.co.il'],
    [['newmed', 'ניומד'], 'newmedenergy.com'],
    [['ratio', 'רציו'], 'ratio-petroleum.com'],
    [['sonol', 'סונול'], 'sonol.co.il'],
    [['dor alon', 'דור אלון'], 'doralon.co.il'],
    [['solaredge', "סולאראדג'", "סולאראדג׳"], 'solaredge.com'],
    [['enlight', 'אנלייט'], 'enlightenergy.co.il'],
    [['energix', "אנרג'יקס", "אנרג׳יקס"], 'energix-group.com'],
    [['doral', 'דוראל'], 'doral-energy.com'],
    [['nofar', 'נופר אנרגיה', 'נופר'], 'nofar-energy.com'],
    [['al-mor', 'אל-מור', 'אל מור', 'אלמור'], 'almor.co.il'],
    [['shikun & binui', 'שיכון ובינוי'], 'shikunbinui.com'],
    [['econergy', 'אקונרגיה', 'אקונרג׳י', "אקונרג'י"], 'econergy-international.com'],
    [['teralight', 'טראלייט'], 'teralight-energy.com'],
    [['meshek energy', 'משק אנרגיה', 'סולגרין'], 'meshek-energy.co.il'],
    [['prime energy', 'פריים אנרגיה', "פריים אנרג'י"], 'prime-energy.co.il'],
    [['nextpower', 'נקסטפאוור'], 'nextpower.com'],
    [['nextcom', 'נקסטקום'], 'nextcomgroup.com'],
    [['h2pro'], 'h2pro.co'],
    [['storedot'], 'store-dot.com'],
    [['electreon', 'אלקטריאון'], 'electreon.com'],
    [['mprest', 'אמפרסט'], 'mprest.com'],
    [['phinergy', 'פינרגיה', "פינרג'י"], 'phinergy.com'],
    [['brenmiller', 'ברנמילר', 'brenx'], 'bren-energy.com'],
    [['augwind', 'אוגווינד', 'airangy'], 'aug-wind.com'],
    [['addionics'], 'addionics.com'],
    [['zooz power', 'zooz', "צ'אקראטק"], 'zoozpower.com'],
    [['isramco', 'ישראמקו'], 'isramco.co.il'],
    [['edeltech', 'אדלטק'], 'edeltech.co.il'],
    [['dalia', 'דליה אנרגיות', 'צפית'], 'dalia-energy.co.il'],
    [['navitas', 'נאוויטס'], 'navitaspet.com'],
    [['tamar petroleum', 'תמר פטרוליום'], 'tamarpetroleum.co.il'],
    [['rimon', 'רימון'], 'rimon.co.il'],
    [['raycatch', "רייקאץ'", 'רייקאץ׳'], 'raycatch.com'],
    [['augury', 'אוגורי'], 'augury.com'],
    [['airtouch', 'איירטאץ', 'איירטאץ׳'], 'airtouchsolar.com'],
    [['ecoppia', 'אקופיה'], 'ecoppia.com'],
    [['gencell', "ג'נסל"], 'gencellenergy.com'],
    [['driivz', 'דרייבז'], 'driivz.com'],
    [['solcold', 'סולקולד'], 'solcold.com'],
    [['nostromo', 'נוסטרומו'], 'nostromo.energy'],
    [['zutacore'], 'zutacore.com'],
    [['eco wave power'], 'ecowavepower.com'],
    [['siemens energy', 'סימנס אנרגיה', 'siemens-energy'], 'siemens-energy.com'],
    [['siemens', 'סימנס'], 'siemens.com'],
    [['ge vernova', 'ge ', "ג'נרל אלקטריק"], 'gevernova.com'],
    [['schneider', 'שניידר'], 'se.com'],
    [['hitachi', "היטאצ'י"], 'hitachienergy.com'],
    [['ormat', 'אורמת'], 'ormat.com'],
    [['edf', 'אי די אף'], 'edf-re.com'],
    [['jinko', "ג'ינקו"], 'jinkosolar.com'],
    [['nt-tao', 'nt tao', 'נו טאו'], 'nt-tao.com'],
    [['concentric power', 'concentric'], 'concentricpower.com'],
    [['plant supervision'], 'plantsupervision.com'],
    [['solar solutions', 'פתרונות סולאריים'], 'solarsolutions.co.il'],
    [['saltworks', 'סולטוורקס'], 'saltworkstech.com'],
    [['x-cooling', 'x cooling', 'אקס קולינג'], 'x-cooling.com'],
    [['allpha innovation', 'allpha'], 'allpha.com'],

    // Defense / Aerospace / UAV / Drones
    [['elbit', 'אלביט'], 'elbitsystems.com'],
    [['rafael', 'רפאל'], 'rafael.co.il'],
    [['iai', 'התעשייה האווירית', 'התעשיה האווירית', 'israel aerospace'], 'iai.co.il'],
    [['tomer', 'תומר', 'תומר חברה ממשלתית'], 'tomer-israel.co.il'],
    [['amarel', 'אמארל', 'אמרל'], 'amarel.net'],
    [['controp', 'קונטרופ'], 'controp.com'],
    [['xtend'], 'xtend.me'],
    [['percepto', 'פרספטו'], 'percepto.com'],
    [['airobotics', 'איירובוטיקס'], 'airoboticsdrones.com'],
    [['bluebird', 'בלובירד'], 'bluebird-uav.com'],
    [['spearuav', 'ספיר'], 'spearuav.com'],
    [['parazero', 'manta air', 'פארזרו'], 'parazero.com'],
    [['flytrex'], 'flytrex.com'],
    [['d-fend', 'די פנד', 'די-פנד'], 'd-fendsolutions.com'],
    [['robotican', 'רובוטיקאן'], 'robotican.co'],
    [['high lander', 'היי לנדר', 'highlander'], 'highlander.io'],
    [['steadicopter', 'סטדיקופטר'], 'steadicopter.com'],
    [['third eye', 'עין שלישית'], 'thirdeye-systems.com'],
    [['smartshooter', 'smart shooter'], 'smart-shooter.com'],
    [['nextvision'], 'nextvision-sys.com'],
    [['birdaero', 'bird aero'], 'birdaero.com'],
    [['aerotor'], 'aerotor.com'],
    [['heven'], 'hevenaerotech.com'],
    [['sentrycs'], 'sentrycs.com'],
    [['roboteam'], 'robo-team.com'],
    [['sightec'], 'sightec.com'],
    [['regulus'], 'regulus.com'],
    [['rada', 'דראס', 'drs rada', 'drs'], 'drs.com'],
    [['bagira', 'בגירה'], 'bagirasys.com'],
    [['aitech'], 'aitechsystems.com'],
    [['airwayz'], 'airwayz.co'],
    [['bet shemesh', 'מנועי בית שמש'], 'bseltd.com'],
    [['uvision', 'יוויז׳ן', "יוויז'ן"], 'uvisionuav.com'],
    [['imco', 'אימקו'], 'imco-ind.com'],

    // Industry / Engineering / Infrastructure
    [['electra', 'אלקטרה'], 'electra.co.il'],
    [['netafim', 'נטפים'], 'netafim.com'],
    [['iscar', 'ישקר'], 'iscar.com'],
    [['tower', 'טאוור'], 'towersemi.com'],
    [['applied materials', 'אפלייד'], 'appliedmaterials.com'],
    [['nova', 'נובה'], 'novami.com'],
    [['kla', 'קיי אל איי'], 'kla.com'],
    [['icl group', 'כימיקלים לישראל', 'כי״ל', 'כיל'], 'icl-group.com'],
    [['adama', 'אדמה'], 'adama.com'],
    [['alumeshet', 'אלומושת'], 'alumeshet.co.il'],
    [['stratasys', 'סטראטסיס'], 'stratasys.com'],
    [['acs motion', 'acs'], 'acsmotioncontrol.com'],
    [['ashtrom', 'אשטרום'], 'ashtrom.co.il'],
    [['shapir', 'שפיר'], 'shapir.co.il'],
    [['shikun', 'שיכון ובינוי'], 'shikunbinui.com'],
    [['danya cebus', 'דניה סיבוס', 'דניה'], 'danya-cebus.co.il'],
    [['baran', 'ברן'], 'baran-group.com'],
    [['alstom', 'אלסטום'], 'alstom.com'],
    [['teva', 'טבע'], 'teva.co.il'],
    [['bruker'], 'bruker.com'],
    [['philips', 'פיליפס'], 'philips.com'],
    [['edwards vacuum', 'edwards'], 'edwardsvacuum.com'],
    [['ultra clean technology', 'uct'], 'uct.com'],
    [['assatec robotics', 'assatec', 'אסאטק'], 'assatec.com'],
    [['e2e solutions', 'e2e'], 'e2e-il.com'],
    [['michlol solutions', 'מיכלול'], 'michlol-sol.co.il'],
    [['advance eng', 'אדוונס הנדסה', 'אדוונס'], 'advance-eng.co.il'],
    [['orion', 'ב.מ. אוריון', 'אוריון ושות', 'אוריון'], 'bmorion.com'],
    [['scheidt & bachmann', 'שיידט את בכמן', 'scheidt'], 'scheidt-bachmann.com'],
    [['snorkel', 'שנייר ליפט', 'שנייר'], 'snorkellifts.com'],
    [['niga', 'ניגא שף', 'ניגא'], 'niga.co.il'],
    [['vpg', 'וי פי ג׳י'], 'vpgsensors.com'],
    [['zoll', 'זול מדיקל'], 'zoll.com'],
    [['robokit', 'רובוקיט'], 'robokit.co.il'],
    [['colmobil', 'כלמוביל'], 'colmobil.co.il'],
    [['pb israel', 'wsp'], 'wsp.com'],
    [['swissport', 'סוויספורט', 'סוויספורט שרותי מטען'], 'swissport.com'],
    [['sheba', 'שיבא', 'מרכז רפואי שיבא', 'תל השומר'], 'sheba.co.il'],
    [['jll', "ג'ונס לאנג"], 'jll.com'],
    [['merck', 'מרק'], 'merckgroup.com'],
    [['flex', 'פלקס'], 'flex.com'],
    [['jacobs', "ג'ייקובס"], 'jacobs.com'],

    // Tech / Software / Staffing
    [['jobsseek', "ג'ובסיק"], 'jobsseek.co.il'],
    [['job space', "ג'וב ספייס"], 'jobspace.co.il'],
    [['shidrug', 'שדרוג מיון והשמה', 'שדרוג'], 'shidrug.co.il'],
    [['dataway', 'דאטה וויי', 'דאטהווי'], 'dataway.co.il'],
    [['entrypoint', 'אנטריפוינט'], 'entrypoint.co.il'],
    [['mertens', 'מרטנס', 'מלם תים', 'malam'], 'malamteam.com'],
    [['zofen', 'צופן'], 'zofen.com'],
    [['cross river', 'קרוס ריבר', 'confidential careers'], 'crossriver.com'],
    [['partner', 'פרטנר'], 'partner.co.il'],
    [['intel', 'realsense', 'אינטל'], 'intel.com'],
    [['apple', 'אפל'], 'apple.com'],
    [['amazon', 'aws', 'אמזון'], 'amazon.com'],
    [['nvidia', 'אנבידיה'], 'nvidia.com'],
    [['tesla', 'טסלה'], 'tesla.com'],
    [['mobileye', 'מובילאיי'], 'mobileye.com'],
    [['cato networks', 'קאטו'], 'catonetworks.com'],
    [['check point', 'checkpoint', "צ'ק פוינט"], 'checkpoint.com'],
    [['palo alto', 'פאלו אלטו'], 'paloaltonetworks.com'],
    [['cyberark', 'סייברארק'], 'cyberark.com'],
    [['biocatch'], 'biocatch.com'],
    [['claroty'], 'claroty.com'],
    [['cheq'], 'cheq.ai'],
    [['wix', 'וויקס'], 'wix.com'],
    [['monday', 'מאנדיי'], 'monday.com'],
    [['fiverr', 'פייבר'], 'fiverr.com'],
    [['gett', 'גט'], 'gett.com'],
    [['lemonade'], 'lemonade.com'],
    [['matrix', 'מטריקס'], 'matrix-globals.com'],
    [['ness', 'נס'], 'ness-tech.co.il'],
    [['manpower', 'מנפאואר'], 'manpower.co.il'],
    [['experis'], 'experis.co.il'],
    [['sqlink'], 'sqlink.com'],
    [['elad software', 'אלעד מערכות', 'אלעד'], 'eladsoft.com'],
    [['michlol', 'מכלול'], 'michlolltd.co.il'],
    [['e2e solutions', 'e2e'], 'e2eil.co.il'],
    [['assatec', 'אסאטק'], 'assatec.co.il'],
    [['nyga', 'ניגא שף', 'ניגא'], 'nyga-chef.co.il'],
    [['mechanical devices', 'm.d. mechanical'], 'mechanical-devices.com'],
    [['microsoft', 'מיקרוסופט'], 'microsoft.com'],
    [['zoll'], 'zoll.com'],
    [['linked magic'], 'linkedmagic.com'],
    [['or holdings', 'אור אחזקות', 'ר.א אור'], 'or-holdings.co.il'],
    [['nestle', 'אסם'], 'nestle.com'],
    [['pepsico', 'קוקה קולה', 'החברה המרכזית'], 'pepsico.com'],
    [['strauss', 'שטראוס'], 'strauss-group.com'],
    [['tnuva', 'תנובה'], 'tnuva.co.il'],
    [["l'oréal", 'loreal', 'לוריאל'], 'loreal.com'],
    [['hilti', 'הילטי'], 'hilti.co.il'],
    [['knapp', 'קנאפפ', 'קנאפ'], 'knapp.com'],
    [['systematics', 'סיסטמטיקס'], 'systematics.co.il'],
    [['tevel metro', 'תבל מטרו', 'תבל'], 'tevelmetro.co.il'],
    [['mrc', 'אם.אר.סי', 'אם אר סי'], 'mrclab.com'],
    [['recruitx', 'ריקורטקס'], 'recruitx.co.il'],
    [['arbex', 'ארבקס'], 'arbex.com'],
    [['segal', 'סגל מערכות', 'סגל'], 'segal.co.il'],
    [['ur tech', 'ur tech jobs', 'יו אר טק'], 'urtechjobs.com'],
    [['dty', 'dty optical', 'ד.ט.י'], 'dty.co.il'],
    [['sle', 'sle logistics', 'ס.ל.א', 'סלא'], 'sle.co.il'],
    [['sun pharma', 'סאן פארמה'], 'sunpharma.com'],
    [['korentec', 'yael korentec', 'קבוצת יעל', 'קורנטק'], 'yaelgroup.com'],
    [['כרמית מיסטר פיקס', 'מיסטר פיקס', 'mr fix', 'mr. fix'], 'carmit-mrfix.com'],
    [['bird aero', 'bird aerosystems', 'בירד'], 'birdaero.com'],
    [['abra', 'אברא'], 'abra-it.com'],
    [['iff'], 'iff.com'],
    [['sungrow', 'סאנגרו'], 'sungrowpower.com'],
    [['kyndryl', 'קינדריל'], 'kyndryl.com'],
    [['drivenets', 'דרייבנטס'], 'drivenets.com'],
    [['kela', 'קלה'], 'kela-tech.com'],
    [['exodigo', 'אקסודיגו'], 'exodigo.com'],
    [['forsight', 'פורסייט רובוטיקס'], 'forsightrobotics.com'],
    [['mda space', 'mda'], 'mda.space'],
    [['mer group', 'מר'], 'mer-group.com'],
    [['commit'], 'commit.tech'],
    [['comblack', 'קומבלק'], 'comblack.co.il'],
    [['nuvei', 'נוביי'], 'nuvei.com'],
    [['mentee', 'mentee robotics', 'מנטי'], 'menteebot.com'],
    [['vishay intertechnology'], 'vishay.com'],
    [['longi solar', 'longi'], 'longi.com'],
    [['sofar', 'sofar solar'], 'sofarsolar.com'],
    [['fieldcore'], 'fieldcore.com'],
    [['cellcom', 'סלקום'], 'cellcom.co.il'],
    [['cbc israel', 'החברה המרכזית למשקאות'], 'cocacola.co.il'],
    [['ortal', 'אורטל ולעבודה'], 'ortal-hr.co.il'],
    [['ducart', 'דוקרט'], 'ducart.co.il'],
    [['kimberly-clark', 'קימברלי קלארק'], 'kimberly-clark.com'],
    [['helios'], 'project-helios.space'],
    [['elmo motion control', 'אלמו'], 'elmomc.com'],
    [['pacaya', 'pacaya hr'], 'pacaya.co.il'],
    [['team 3', 'צוות 3', 'team 3 group'], 'team3.co.il'],
    [['esp710'], 'esp710.com'],
    [['aitan'], 'aitan.com'],
    [['growings robotx', 'growings'], 'growings-robotx.com'],
    [['hct', 'hadarom container', 'הדרום קונטיינר'], 'hct.co.il'],
    [['utron'], 'utron-sys.com'],
    [['tehiru', 'tehiru aerial'], 'tehiru.com'],
    [['magnus metal', 'magnus'], 'magnusmetal.com'],
    [['ein-hashofet', 'עין השופט'], 'ehltg.com'],
    [['utila'], 'utila.io'],
    [['rhino federated', 'rhino'], 'rhinofc.com'],
    [['rina'], 'rina.org'],
    [['ersg'], 'ersg-global.com'],
    [['clou ess', 'clou'], 'clouglobal.com'],
    [['supercom'], 'supercom.com'],
    [['elmor', 'אלמור'], 'elmor.co.il'],
    [['ageera'], 'ageera.co.il'],
    [['nextpower'], 'nextpower.com'],
    [['repair carbon'], 'repair-carbon.com'],
    [['d-fend', 'd-fend solutions'], 'd-fendsolutions.com'],
    [['edwards vacuum', 'edwards'], 'edwardsvacuum.com'],
    [['wds technologies', 'wds'], 'wdstech.co.il'],
    [['sightec'], 'sightec.com'],
    [['spearuav', 'spear uav'], 'spearuav.com'],
    [['percepto', 'פרספטו'], 'percepto.co'],
    [['allpha', 'allpha innovation'], 'allpha-innovation.com']
  ];

  function matchCompanyWord(text, keyword) {
    if (!text || !keyword) return false;
    const t = text.toLowerCase().trim();
    const k = keyword.toLowerCase().trim();
    if (t === k) return true;
    const escaped = k.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
    const regex = new RegExp('(?:^|[^a-zA-Z0-9א-ת])' + escaped + '(?:$|[^a-zA-Z0-9א-ת])', 'i');
    return regex.test(t);
  }

  function cleanCompanyName(name) {
    if (!name) return 'חברה';
    let s = name.trim();
    s = s.replace(/^[+\-~|•\s]+|[+\-~|•\s]+$/g, '');
    return s.trim() || 'חברה';
  }

  function getCompanyBrandColor(str) {
    const palette = [
      ['rgba(0, 229, 255, 0.15)', '#00e5ff'],
      ['rgba(16, 185, 129, 0.15)', '#10b981'],
      ['rgba(99, 102, 241, 0.15)', '#818cf8'],
      ['rgba(245, 158, 11, 0.15)', '#f59e0b'],
      ['rgba(236, 72, 153, 0.15)', '#ec4899'],
      ['rgba(139, 92, 246, 0.15)', '#a78bfa']
    ];
    let hash = 0;
    const s = str || 'חברה';
    for (let i = 0; i < s.length; i++) {
      hash = (hash << 5) - hash + s.charCodeAt(i);
      hash |= 0;
    }
    const idx = Math.abs(hash) % palette.length;
    return palette[idx];
  }

  const LOCAL_COMPANY_LOGOS = [
    [['electra', 'אלקטרה'], 'assets/logos/electra.png'],
    [['alumenergy', 'אלומאנרג\'י', 'אלומנרג\'י', 'אלומנרג׳י', 'אלומוט'], 'assets/logos/alumenergy.png'],
    [['amarel', 'אמראל'], 'assets/logos/amarel.png'],
    [['airobotics', 'איירובוטיקס'], 'assets/logos/airobotics.png'],
    [['alstom', 'אלסטום'], 'assets/logos/alstom.png'],
    [['assatec', 'אסאטק'], 'assets/logos/assatec.png'],
    [['bagira', 'בגירה'], 'assets/logos/bagira.png'],
    [['bet shemesh', 'מנועי בית שמש', 'bseltd'], 'assets/logos/bseltd.svg'],
    [['concentric'], 'assets/logos/concentric.png'],
    [['confidential', 'דיסקרטי', 'חברה מובילה', 'חסויה'], 'assets/logos/confidential.svg'],
    [['cross river', 'crossriver'], 'assets/logos/crossriver.png'],
    [['drs rada', 'rada', 'ראדא'], 'assets/logos/rada.png'],
    [['e2e', 'e2e solutions'], 'assets/logos/e2e.svg'],
    [['edwards', 'edwards vacuum'], 'assets/logos/edwards.png'],
    [['elad', 'אלעד מערכות', 'אלעד'], 'assets/logos/elad.png'],
    [['elbit', 'אלביט'], 'assets/logos/elbit.png'],
    [['enlight', 'אנלייט'], 'assets/logos/enlight.png'],
    [['flex', 'פלקס'], 'assets/logos/flex.png'],
    [['iai', 'התעשייה האווירית', 'התעשיה האווירית', 'תעשייה אווירית'], 'assets/logos/iai.svg'],
    [['imco', 'אימקו'], 'assets/logos/imco.png'],
    [['job space', 'jobspace'], 'assets/logos/jobspace.svg'],
    [['jacobs', 'ג\'ייקובס'], 'assets/logos/jacobs.png'],
    [['jobsseek', 'ג\'ובסיק'], 'assets/logos/jobsseek.svg'],
    [['md-ltd', 'mechanical devices', 'm.d.'], 'assets/logos/md-ltd.svg'],
    [['manta air', 'manta'], 'assets/logos/manta-air.png'],
    [['michlol', 'מכלול'], 'assets/logos/michlol.png'],
    [['microsoft', 'מיקרוסופט'], 'assets/logos/microsoft.png'],
    [['mobileye', 'מובילאיי', 'מובילאי'], 'assets/logos/mobileye.png'],
    [['netafim', 'נטפים'], 'assets/logos/netafim.png'],
    [['nextcom', 'נקסטקום'], 'assets/logos/nextcom.png'],
    [['nextpower', 'נקסטפאוור'], 'assets/logos/nextpower.svg'],
    [['pb israel', 'wsp', 'parsons brinckerhoff', 'pb'], 'assets/logos/wsp.png'],
    [['partner', 'פרטנר'], 'assets/logos/partner.png'],
    [['saltworks', 'סולטוורקס'], 'assets/logos/saltworks.png'],
    [['siemens energy', 'סימנס אנרגיה', 'siemens'], 'assets/logos/siemens-energy.png'],
    [['solaredge', 'סולאראדג\'', 'סולאראדג׳'], 'assets/logos/solaredge.png'],
    [['uvision', 'יוביז\'ן', 'יוביז׳ן'], 'assets/logos/uvision.png'],
    [['vpg', 'vishay'], 'assets/logos/vpg.png'],
    [['x-cooling', 'xcooling'], 'assets/logos/x-cooling.png'],
    [['zoll', 'זול'], 'assets/logos/zoll.png'],
    [['zofen', 'צופן'], 'assets/logos/zofen.svg'],
    [['nt-tao', 'nt tao'], 'assets/logos/nt-tao.png'],
    [['advance', 'אדוונס הנדסה', 'אדוונס'], 'assets/logos/advance.svg'],
    [['el-mor', 'אל-מור', 'אלמור'], 'assets/logos/el-mor.png'],
    [['entrypoint', 'אנטריפוינט'], 'assets/logos/entrypoint.png'],
    [['bmorion', 'אוריון', 'ב.מ. אוריון'], 'assets/logos/bmorion.svg'],
    [['dataway', 'דאטה וויי', 'דאטה ווי'], 'assets/logos/dataway.png'],
    [['colmobil', 'כלמוביל'], 'assets/logos/colmobil.png'],
    [['malamteam', 'מאלם', 'מלם', 'מרטנס'], 'assets/logos/malamteam.png'],
    [['niga', 'ניגא', 'ניגא שף'], 'assets/logos/niga.svg'],
    [['robokit', 'רובוקיט'], 'assets/logos/robokit.png'],
    [['rafael', 'רפאל'], 'assets/logos/rafael.svg'],
    [['shidrug', 'שדרוג'], 'assets/logos/shidrug.png'],
    [['scheidt-bachmann', 'שיידט את בכמן', 'שיידט'], 'assets/logos/scheidt-bachmann.png'],
    [['schnierlift', 'שנייר', 'שנייר ליפט'], 'assets/logos/schnierlift.svg'],
    [['tomer', 'תומר'], 'assets/logos/tomer.png'],
    [['ormash', 'אורמש'], 'assets/logos/ormash.svg'],
    [['hilti', 'הילטי'], 'assets/logos/hilti.svg'],
    [['knapp', 'קנאפפ', 'קנאפ'], 'assets/logos/knapp.svg'],
    [['systematics', 'סיסטמטיקס'], 'assets/logos/systematics.svg'],
    [['tevel metro', 'תבל מטרו', 'תבל'], 'assets/logos/tevel.svg'],
    [['mrc', 'אם.אר.סי', 'אם אר סי'], 'assets/logos/mrc.svg'],
    [['recruitx', 'ריקורטקס'], 'assets/logos/recruitx.svg'],
    [['arbex', 'ארבקס'], 'assets/logos/arbex.svg'],
    [['segal', 'סגל מערכות', 'סגל'], 'assets/logos/segal.svg'],
    [['ur tech', 'ur tech jobs', 'יו אר טק'], 'assets/logos/urtech.svg'],
    [['opc', 'opc-energy', 'או פי סי'], 'assets/logos/opc.svg'],
    [['dty optical', 'dty', 'ד.ט.י'], 'assets/logos/dty.png'],
    [['sle logistics', 'sle', 'ס.ל.א', 'סלא'], 'assets/logos/sle.png'],
    [['sun pharma', 'סאן פארמה'], 'assets/logos/sunpharma.svg'],
    [['yael korentec', 'korentec', 'קבוצת יעל', 'קורנטק'], 'assets/logos/yael.png'],
    [['כרמית מיסטר פיקס', 'מיסטר פיקס', 'mr fix', 'mr. fix'], 'assets/logos/mrfix.png']
  ];

  function getCompanyLogoInfo(companyName, customLogo) {
    const rawName = cleanCompanyName(companyName);
    const norm = rawName.toLowerCase();
    
    // 1. Check local assets repository first (high resolution, zero network latency)
    let localPath = null;
    for (const [keys, path] of LOCAL_COMPANY_LOGOS) {
      if (keys.some(k => matchCompanyWord(norm, k))) {
        localPath = path;
        break;
      }
    }

    let domain = null;
    for (const [keys, dom] of KNOWN_COMPANY_DOMAINS) {
      if (keys.some(k => matchCompanyWord(norm, k))) {
        domain = dom;
        break;
      }
    }

    let cleanWords = rawName
      .replace(/[()[\\]\\-–•,|~+]/g, ' ')
      .split(/\s+/)
      .filter(w => w && !['בע"מ', 'בע״מ', 'בעמ', 'ltd', 'ltd.', 'inc', 'inc.', 'group', 'corp', 'israel', 'ישראל', 'בעל'].includes(w.toLowerCase()));
    if (cleanWords.length === 0) cleanWords = [rawName];
    
    let initials = '';
    let isIcon = false;
    if (cleanWords.length >= 2) {
      initials = (cleanWords[0][0] || '') + (cleanWords[1][0] || '');
    } else if (cleanWords.length === 1 && cleanWords[0].length >= 2) {
      initials = cleanWords[0].slice(0, 2);
    } else if (cleanWords.length === 1 && cleanWords[0].length === 1) {
      initials = cleanWords[0][0];
    } else {
      initials = '<i class="ph-duotone ph-buildings" style="font-size: 20px;"></i>';
      isIcon = true;
    }
    if (!isIcon) initials = escapeHtml(initials.toUpperCase());

    let primaryUrl = localPath;
    let initialStep = 0;
    if (!primaryUrl) {
      if (customLogo) {
        primaryUrl = sanitizeUrl(customLogo);
      } else if (domain) {
        primaryUrl = 'https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://' + encodeURIComponent(domain) + '&size=128';
        initialStep = 1;
      }
    }

    return { rawName, domain, initials, isIcon, primaryUrl, initialStep };
  }

  function handleCompanyLogoError(img, domain) {
    if (!domain) {
      hideCompanyLogoElement(img);
      return;
    }
    const step = parseInt(img.dataset.step || '0', 10);
    if (step === 0) {
      img.dataset.step = '1';
      img.src = 'https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://' + encodeURIComponent(domain) + '&size=128';
    } else if (step === 1) {
      img.dataset.step = '2';
      img.src = 'https://icons.duckduckgo.com/ip3/' + encodeURIComponent(domain) + '.ico';
    } else {
      hideCompanyLogoElement(img);
    }
  }

  function handleCompanyLogoLoad(img, domain) {
    const step = parseInt(img.dataset.step || '0', 10);
    if (img.naturalWidth <= 16 && img.naturalHeight <= 16 && step === 1 && domain) {
      handleCompanyLogoError(img, domain);
    }
  }

  function hideCompanyLogoElement(img) {
    const parent = img.closest('.job-company-logo');
    if (parent) {
      parent.style.display = 'none';
    } else {
      img.style.display = 'none';
    }
  }

  function getCompanyLogoHtml(companyName, customLogo) {
    const info = getCompanyLogoInfo(companyName, customLogo);
    const safeComp = escapeHtml(info.rawName);
    const safeDom = (info.domain || '').replace(/"/g, '&quot;');

    if (info.primaryUrl) {
      return `
        <div class="job-company-logo" title="${safeComp}">
          <img src="${info.primaryUrl}" 
               alt="${safeComp}" 
               class="job-logo-img" 
               loading="lazy" 
               decoding="async" 
               data-step="${info.initialStep}"
               onload="handleCompanyLogoLoad(this, '${safeDom}')" 
               onerror="if(typeof handleCompanyLogoError==='function'){handleCompanyLogoError(this, '${safeDom}');}else{const p=this.closest('.job-company-logo');if(p)p.style.display='none';}" />
        </div>
      `;
    }
    return '';
  }

  // Israeli Geolocation Coordinate Dictionary (Latitude, Longitude)
  const ISRAEL_LOCATIONS_GEO = {
    // Tel Aviv & Dan
    'תל אביב': [32.0853, 34.7818],
    'tel aviv': [32.0853, 34.7818],
    'גוש דן': [32.0853, 34.7818],
    'רמת גן': [32.0822, 34.8143],
    'ramat gan': [32.0822, 34.8143],
    'שיבא': [32.0460, 34.8430],
    'תל השומר': [32.0460, 34.8430],
    'גבעתיים': [32.0722, 34.8089],
    'בני ברק': [32.0833, 34.8333],
    'פתח תקווה': [32.0840, 34.8878],
    'petah tikva': [32.0840, 34.8878],
    'פתח תקוה': [32.0840, 34.8878],
    'חולון': [32.0158, 34.7874],
    'holon': [32.0158, 34.7874],
    'בת ים': [32.0194, 34.7500],
    'bat yam': [32.0194, 34.7500],
    'ראשון לציון': [31.9730, 34.7925],
    'rishon': [31.9730, 34.7925],
    'אור יהודה': [32.0294, 34.8572],
    'קריית אונו': [32.0536, 34.8586],
    'יהוד': [32.0333, 34.8833],
    
    // Center & Shfela & Airport
    'נתב"ג': [32.0005, 34.8707],
    'נתב״ג': [32.0005, 34.8707],
    'לוד': [31.9519, 34.8967],
    'lod': [31.9519, 34.8967],
    'רמלה': [31.9284, 34.8687],
    'ramla': [31.9284, 34.8687],
    'איירפורט סיטי': [32.0120, 34.9220],
    'airport city': [32.0120, 34.9220],
    'נמל תעופה': [32.0005, 34.8707],
    'מודיעין': [31.8986, 35.0104],
    'modiin': [31.8986, 35.0104],
    'שוהם': [31.9986, 34.9458],
    'נס ציונה': [31.9317, 34.7981],
    'נס-ציונה': [31.9317, 34.7981],
    'רחובות': [31.8928, 34.8113],
    'rehovot': [31.8928, 34.8113],
    'יבנה': [31.8781, 34.7397],
    'yavne': [31.8781, 34.7397],
    'שפלה': [31.8928, 34.8113],
    'מרכז': [32.0853, 34.7818],
    'center': [32.0853, 34.7818],
    'מרכז הארץ': [32.0853, 34.7818],

    // Sharon
    'הרצליה': [32.1624, 34.8447],
    'herzliya': [32.1624, 34.8447],
    'רעננה': [32.1848, 34.8713],
    'raanana': [32.1848, 34.8713],
    'כפר סבא': [32.1750, 34.9069],
    'kfar saba': [32.1750, 34.9069],
    'הוד השרון': [32.1528, 34.8878],
    'hod hasharon': [32.1528, 34.8878],
    'נתניה': [32.3215, 34.8532],
    'netanya': [32.3215, 34.8532],
    'פולג': [32.2783, 34.8572],
    'חדרה': [32.4340, 34.9197],
    'hadera': [32.4340, 34.9197],
    'קיסריה': [32.5020, 34.9350],
    'caesarea': [32.5020, 34.9350],
    'עמק חפר': [32.3850, 34.9000],
    'שרון': [32.1848, 34.8713],
    'sharon': [32.1848, 34.8713],

    // South & Ashdod / Ashkelon / Negev
    'אשדוד': [31.8014, 34.6435],
    'ashdod': [31.8014, 34.6435],
    'נמל אשדוד': [31.8260, 34.6530],
    'נמל הדרום': [31.8260, 34.6530],
    'אשקלון': [31.6688, 34.5743],
    'ashkelon': [31.6688, 34.5743],
    'קריית גת': [31.6100, 34.7642],
    'kiryat gat': [31.6100, 34.7642],
    'באר שבע': [31.2529, 34.7915],
    'beer sheva': [31.2529, 34.7915],
    'beersheba': [31.2529, 34.7915],
    'דימונה': [31.0667, 35.0333],
    'dimona': [31.0667, 35.0333],
    'נאות חובב': [31.1350, 34.7890],
    'רמת חובב': [31.1350, 34.7890],
    'ערד': [31.2589, 35.2128],
    'שדרות': [31.5211, 34.5967],
    'קריית מלאכי': [31.7289, 34.7456],
    'אילת': [29.5577, 34.9519],
    'דרום': [31.2529, 34.7915],
    'south': [31.2529, 34.7915],
    'נגב': [31.2529, 34.7915],

    // North & Haifa & Valleys & Galilee
    'חיפה': [32.7940, 34.9896],
    'haifa': [32.7940, 34.9896],
    'מת״ם': [32.7880, 34.9580],
    'מתם': [32.7880, 34.9580],
    'קריות': [32.8300, 35.0700],
    'קריית אתא': [32.8028, 35.1075],
    'קריית ביאליק': [32.8272, 35.0847],
    'קריית מוצקין': [32.8347, 35.0778],
    'קריית ים': [32.8464, 35.0686],
    'נשר': [32.7667, 35.0333],
    'טירת כרמל': [32.7611, 34.9722],
    'עכו': [32.9278, 35.0817],
    'akko': [32.9278, 35.0817],
    'acre': [32.9278, 35.0817],
    'נהריה': [33.0059, 35.0941],
    'nahariya': [33.0059, 35.0941],
    'כרמיאל': [32.9199, 35.2901],
    'karmiel': [32.9199, 35.2901],
    'תפן': [32.9772, 35.2683],
    'יקנעם': [32.6595, 35.1102],
    'yokneam': [32.6595, 35.1102],
    'יקנעם עילית': [32.6595, 35.1102],
    'מגדל העמק': [32.6738, 35.2415],
    'migdal haemek': [32.6738, 35.2415],
    'עפולה': [32.6078, 35.2894],
    'afula': [32.6078, 35.2894],
    'אלון תבור': [32.6517, 35.3524],
    'alon tavor': [32.6517, 35.3524],
    'נצרת': [32.6996, 35.3035],
    'נוף הגליל': [32.7050, 35.3350],
    'ציפורית': [32.7600, 35.3400],
    'טבריה': [32.7922, 35.5312],
    'קריית שמונה': [33.2075, 35.5697],
    'kiryat shmona': [33.2075, 35.5697],
    'קצרין': [32.9917, 35.6900],
    'משגב': [32.8600, 35.2500],
    'צפון': [32.7940, 34.9896],
    'north': [32.7940, 34.9896],
    'גליל': [32.9199, 35.2901],
    'עמקים': [32.6078, 35.2894],

    // Jerusalem & Judea
    'ירושלים': [31.7683, 35.2137],
    'jerusalem': [31.7683, 35.2137],
    'בית שמש': [31.7470, 34.9881],
    'beit shemesh': [31.7470, 34.9881],
    'מעלה אדומים': [31.7917, 35.2972],

    // General Countrywide / Default
    'ישראל': [32.0853, 34.7818],
    'israel': [32.0853, 34.7818],
    'ארצי': [32.0853, 34.7818],
    'היברידי': [32.0853, 34.7818],
    'remote': [32.0853, 34.7818],
    'מרוחק': [32.0853, 34.7818]
  };

  // Company Headquarters & Primary Campuses Geolocation Dictionary
  const COMPANY_HQ_LOCATIONS_GEO = [
    // Semiconductors & High-Tech Hardware
    [['tower semiconductor', 'טאואר', 'towersemi'], [32.6738, 35.2415], 'מגדל העמק'],
    [['ultra clean', 'uct'], [32.6738, 35.2415], 'מגדל העמק'],
    [['kla', 'קיי אל איי'], [32.6738, 35.2415], 'מגדל העמק'],
    [['applied materials', 'אפלייד מטיריאלס', 'אפלייד'], [31.9077, 34.8080], 'פארק המדע רחובות'],
    [['nova', 'נובה'], [31.9055, 34.8075], 'פארק המדע רחובות'],
    [['stratasys', 'סטראטסיס'], [31.9055, 34.8075], 'פארק המדע רחובות'],
    [['merck', 'מרק'], [31.9055, 34.8075], 'פארק המדע רחובות'],
    [['edwards vacuum', 'edwards', 'אדוורדס'], [31.6100, 34.7642], 'קריית גת'],
    [['intel', 'אינטל'], [31.6100, 34.7642], 'קריית גת'],

    // Energy, Gas, Solar, Utilities & CleanTech
    [['siemens energy', 'סימנס אנרגיה', 'siemens'], [32.0833, 34.9572], 'פארק אפק, ראש העין'],
    [['alumenergy', 'אלומאנרג׳י', 'אלומאנרגי', 'אלומושת'], [32.6517, 35.3524], 'אלון תבור'],
    [['nt-tao', 'compact fusion'], [32.1528, 34.8878], 'הוד השרון'],
    [['solaredge', 'סולאראדג'], [32.1624, 34.8080], 'הרצליה פיתוח'],
    [['enlight', 'אנלייט'], [32.0833, 34.9572], 'ראש העין'],
    [['energix', 'אנרג׳יקס', 'אנרגיקס'], [32.0822, 34.8020], 'בורסת רמת גן'],
    [['doral', 'דוראל'], [32.0822, 34.8050], 'רמת גן'],
    [['ormat', 'אורמת'], [31.8781, 34.7397], 'יבנה'],
    [['jinko', 'ג׳ינקו', 'גינקו'], [32.1624, 34.8447], 'הרצליה'],
    [['solar solutions', 'פתרונות סולאריים'], [32.3850, 34.9000], 'עמק חפר'],
    [['plant supervision'], [32.6517, 35.3524], 'אלון תבור'],
    [['bazan', 'בז״ן', 'בזן', 'בתי זיקוק'], [32.7980, 35.0450], 'מפרץ חיפה'],
    [['paz', 'פז'], [32.2530, 34.8450], 'יקום'],
    [['sonol', 'סונול'], [32.2783, 34.8572], 'פולג, נתניה'],
    [['delek', 'דלק', 'ניו-מד', 'newmed'], [32.1624, 34.8080], 'הרצליה'],
    [['isramco', 'ישראמקו', 'נפטא'], [32.0840, 34.8650], 'פתח תקווה'],

    // Defense, Aerospace, UAVs, Drones & Robotics
    [['elbit', 'אלביט'], [32.7880, 34.9580], 'מת״ם חיפה'],
    [['iai', 'התעשייה האווירית', 'התעשיה האווירית', 'אלתא', 'elta'], [32.0030, 34.8850], 'נתב״ג / לוד'],
    [['rafael', 'רפאל'], [32.8650, 35.0850], 'מכון דוד, קריות'],
    [['controp', 'קונטרופ'], [32.1528, 34.8878], 'הוד השרון'],
    [['assatec', 'אסאטק'], [32.9278, 35.0817], 'עכו / נהריה'],
    [['allpha', 'אלפא אינוביישן'], [32.8120, 35.0340], 'מספנות חיפה'],
    [['bagira', 'בגירה'], [32.0158, 34.7874], 'חולון'],
    [['israel shipyards', 'מספנות ישראל'], [32.8120, 35.0340], 'נמל חיפה'],
    [['airobotics', 'איירובוטיקס'], [32.0910, 34.8650], 'פתח תקווה'],
    [['percepto', 'פרספטו'], [31.8986, 35.0104], 'פארק טכנולוגי מודיעין'],
    [['hevendrones', 'הוונדרונס'], [32.6100, 35.0500], 'פארק מבוא כרמל'],
    [['steadicopter', 'סטדיקופטר'], [32.6738, 35.2415], 'מגדל העמק'],
    [['bluebird', 'בלובריד'], [32.2850, 34.9150], 'קדימה-צורן'],
    [['aeronautics', 'אירונאוטיקס'], [31.8781, 34.7397], 'יבנה'],
    [['copterpix', 'קופטרפיקס'], [31.9986, 34.9458], 'שוהם'],

    // Aviation, Logistics & Transportation
    [['swissport', 'סוויספורט'], [32.0005, 34.8707], 'נתב״ג'],
    [['alstom', 'אלסטום'], [32.0628, 34.7865], 'תל אביב'],
    [['pb', 'parsons brinckerhoff'], [32.0120, 34.9220], 'איירפורט סיטי'],

    // Infrastructure, Water, AgTech & Construction
    [['netafim', 'נטפים'], [32.0715, 34.7930], 'תל אביב'],
    [['nextcom', 'נקסטקום'], [32.6595, 35.1102], 'יקנעם עילית'],
    [['shikun', 'שיכון ובינוי'], [32.0120, 34.9220], 'איירפורט סיטי'],
    [['adama', 'אדמה'], [32.0120, 34.9220], 'איירפורט סיטי'],
    [['danya', 'דניה סיבוס', 'דניה'], [32.0294, 34.8572], 'אור יהודה'],
    [['electra', 'אלקטרה'], [31.9850, 34.7750], 'ראשון לציון'],
    [['ashtrom', 'אשטרום'], [32.0620, 34.7870], 'תל אביב'],
    [['shapir', 'שפיר'], [32.0840, 34.8650], 'פתח תקווה'],
    [['baran', 'ברן'], [32.0020, 34.8290], 'בית דגן'],
    [['icl', 'כי״ל', 'כימיקלים לישראל', 'כיל'], [31.2589, 34.8050], 'באר שבע'],

    // Tech, Telecom, Software, Hospitals & Services
    [['michlol', 'מכלול'], [32.0910, 34.8650], 'פתח תקווה'],
    [['e2e solutions', 'e2e'], [32.1100, 34.8350], 'רמת החייל, תל אביב'],
    [['elad', 'אלעד מערכות'], [32.1100, 34.8350], 'רמת החייל, תל אביב'],
    [['sheba', 'שיבא', 'תל השומר'], [32.0460, 34.8430], 'רמת גן'],
    [['mobileye', 'מובילאיי'], [31.8020, 35.2150], 'הר חוצבים, ירושלים'],
    [['check point', 'checkpoint', "צ'ק פוינט"], [32.0720, 34.7950], 'תל אביב'],
    [['cross river'], [31.8020, 35.2150], 'הר חוצבים, ירושלים'],
    [['jll'], [32.0715, 34.7930], 'תל אביב'],
    [['wix', 'וויקס'], [32.1000, 34.7750], 'נמל תל אביב'],
    [['monday', 'מאנדיי'], [32.0650, 34.7750], 'שדרות רוטשילד, תל אביב'],
    [['fiverr', 'פייבר'], [32.0600, 34.7750], 'תל אביב']
  ];

  const GENERIC_LOCATION_TERMS = new Set([
    'ישראל', 'israel', 'ארצי', 'היברידי', 'remote', 'מרוחק', 'כל הארץ', 
    'מרכז הארץ', 'מרכז', 'center', 'שרון', 'sharon', 'דרום', 'south', 
    'צפון', 'north', 'שפלה', 'סדנה ויציאה לשטח', 'בשטח'
  ]);

  function getJobLatLng(job) {
    const rawLoc = (job.location || '').toLowerCase();
    const rawComp = (job.company || '').toLowerCase();
    
    // Deterministic jitter based on job link / ID
    let hash = 0;
    const linkStr = job.link || job.id || (rawComp + rawLoc);
    for (let i = 0; i < linkStr.length; i++) {
      hash = ((hash << 5) - hash) + linkStr.charCodeAt(i);
      hash |= 0;
    }
    const jitterLat = (((Math.abs(hash) % 100) - 50) / 50) * 0.014;
    const jitterLng = (((Math.abs(hash * 31) % 100) - 50) / 50) * 0.014;

    // Step 1: Check if the job location mentions a SPECIFIC municipality or industrial site
    // (excluding generic national/regional terms)
    for (const [key, coords] of Object.entries(ISRAEL_LOCATIONS_GEO)) {
      if (!GENERIC_LOCATION_TERMS.has(key) && rawLoc.includes(key)) {
        return [coords[0] + jitterLat, coords[1] + jitterLng];
      }
    }

    // Step 2: Company Headquarters & Main Campus Geo-Mapping
    // If location is generic or unspecified, resolve by company HQ!
    for (const [keys, coords, desc] of COMPANY_HQ_LOCATIONS_GEO) {
      if (keys.some(k => rawComp.includes(k))) {
        return [coords[0] + jitterLat, coords[1] + jitterLng];
      }
    }

    // Step 3: Regional location matches (e.g., 'שרון', 'שפלה', 'צפון', 'דרום', 'מרכז')
    for (const [key, coords] of Object.entries(ISRAEL_LOCATIONS_GEO)) {
      if (rawLoc.includes(key)) {
        return [coords[0] + jitterLat, coords[1] + jitterLng];
      }
    }

    // Step 4: Fallback to Central Israel (Tel Aviv)
    return [32.0853 + jitterLat, 34.7818 + jitterLng];
  }

  let liveJobsMapInstance = null;
  let markersClusterGroup = null;

  function initLiveJobsMap() {
    const mapEl = document.getElementById('liveJobsMap');
    if (!mapEl || liveJobsMapInstance) return;

    try {
      liveJobsMapInstance = L.map('liveJobsMap', {
        scrollWheelZoom: true,
        zoomControl: true,
        zoomSnap: 0.5,
        zoomDelta: 0.5,
        wheelPxPerZoomLevel: 120,
        wheelDebounceTime: 40,
        zoomAnimation: true,
        zoomAnimationThreshold: 8,
        fadeAnimation: true,
        markerZoomAnimation: true
      }).setView([32.0853, 34.85], 8);

      // Official Google Maps tile layer in English (hl=en)
      L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}&hl=en', {
        maxZoom: 19,
        keepBuffer: 6,
        updateWhenZooming: false,
        updateWhenIdle: true,
        attribution: '&copy; Google Maps'
      }).addTo(liveJobsMapInstance);

      if (typeof L.markerClusterGroup === 'function') {
        markersClusterGroup = L.markerClusterGroup({
          spiderfyOnMaxZoom: true,
          showCoverageOnHover: false,
          zoomToBoundsOnClick: true,
          maxClusterRadius: 40,
          spiderfyDistanceMultiplier: 1.4,
          iconCreateFunction: function(cluster) {
            const count = cluster.getChildCount();
            let sizeClass = 'small';
            if (count > 25) sizeClass = 'large';
            else if (count > 8) sizeClass = 'medium';
            return L.divIcon({
              html: `<div class="custom-cluster-badge ${sizeClass}"><span>${count}</span></div>`,
              className: 'marker-cluster-custom',
              iconSize: L.point(40, 40)
            });
          }
        });
        liveJobsMapInstance.addLayer(markersClusterGroup);
      } else {
        markersClusterGroup = L.layerGroup().addTo(liveJobsMapInstance);
      }
    } catch(e) {
      console.error('Error initializing Live Jobs Map:', e);
    }
  }

  function updateMapMarkers() {
    if (!liveJobsMapInstance || !markersClusterGroup) return;

    markersClusterGroup.clearLayers();

    const visibleCards = document.querySelectorAll('.job-card:not(.is-hidden)');
    const totalVisible = visibleCards.length;
    let mappedCount = 0;

    const latLngBounds = [];

    visibleCards.forEach(card => {
      const id = card.getAttribute('data-id');
      const job = allJobsMap[id];
      if (!job) return;

      const [lat, lng] = getJobLatLng(job);
      if (lat && lng) {
        mappedCount++;
        latLngBounds.push([lat, lng]);
      }

      const score = Math.max(0, Math.min(100, Number(job.base_match_score ?? job.match_score) || 0));
      const scoreColor = score >= 85 ? 'var(--dashboard-cyan)' : (score >= 70 ? 'var(--dashboard-lime)' : 'var(--dashboard-gold)');
      const scoreBorder = score >= 85 ? 'rgba(137, 244, 231, 0.8)' : (score >= 70 ? 'rgba(52, 211, 153, 0.8)' : 'rgba(255, 211, 104, 0.8)');

      const companyNameClean = stripEmojis(job.company || 'חברה');
      const titleClean = stripEmojis(job.title || 'משרה');
      const salaryRangeStr = escapeHtml((job.salary_range && job.salary_range !== 'לא צוין' && job.salary_range !== 'לא צוין במודעה') ? stripEmojis(job.salary_range) + (job.salary_source_type === 'job_ad' ? ' (במודעה)' : '') : 'טווח שכר ענפי מותאם');

      const logoInfo = getCompanyLogoInfo(job.company, job.logo);
      const safeComp = escapeHtml(companyNameClean);
      const safeTitle = escapeHtml(titleClean);
      const safeLink = sanitizeUrl(job.link);
      const safeId = encodeURIComponent(id).replace(/'/g, '%27');

      const markerLogoInner = logoInfo.logoUrl ? `
        <img src="${logoInfo.logoUrl}" alt="${safeComp}" loading="lazy" class="map-pin-logo-img"
             onload="if(this.naturalWidth <= 16 && this.naturalHeight <= 16){ this.style.display='none'; var fb = this.nextElementSibling; if(fb) fb.style.display='flex'; }"
             onerror="if(this.dataset.fallbackTried !== '1' && '${logoInfo.fallbackUrl}'){ this.dataset.fallbackTried = '1'; this.src = '${logoInfo.fallbackUrl}'; } else { this.style.display='none'; var fb = this.nextElementSibling; if(fb) fb.style.display='flex'; }" />
        <div class="map-pin-avatar-fallback" style="display: none;">${logoInfo.initials}</div>
      ` : `
        <div class="map-pin-avatar-fallback">${logoInfo.initials}</div>
      `;

      const customIcon = L.divIcon({
        className: 'custom-map-marker',
        html: `
          <div class="custom-map-marker-inner" title="${safeComp} - ${safeTitle}">
            <div class="map-pin-logo-bubble" style="border-color: ${scoreBorder};">
              <span class="map-pin-score-badge" style="background: ${scoreColor}; color: #0f172a;">${score}%</span>
              ${markerLogoInner}
            </div>
            <div class="map-pin-pointer" style="border-top-color: ${scoreBorder};"></div>
            <div class="map-pin-company-name" dir="auto">${escapeHtml(companyNameClean)}</div>
          </div>
        `,
        iconSize: [96, 70],
        iconAnchor: [48, 45],
        popupAnchor: [0, -45]
      });

      const marker = L.marker([lat, lng], { icon: customIcon });

      const logoHtml = getCompanyLogoHtml(job.company, job.logo);

      const popupHtml = `
        <div style="direction: rtl; text-align: right; min-width: 220px; max-width: 280px; font-family: 'Assistant', sans-serif;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <div style="flex-shrink: 0;">${logoHtml}</div>
            <div style="flex: 1; min-width: 0;">
              <div style="font-size: 11px; color: var(--dashboard-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" dir="auto"><bdi>${safeComp}</bdi></div>
              <div style="font-size: 13px; font-weight: 700; color: #fff; line-height: 1.25; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;" dir="auto"><bdi>${safeTitle}</bdi></div>
            </div>
          </div>
          <div style="font-size: 11.5px; color: var(--dashboard-muted); display: flex; flex-direction: column; gap: 3px; margin-bottom: 10px;">
            <span><i class="ph-duotone ph-map-pin"></i> ${escapeHtml(job.location || 'ישראל')}</span>
            <span style="color: var(--dashboard-lime);"><i class="ph-duotone ph-coins"></i> ${salaryRangeStr}</span>
            <span style="color: ${scoreColor}; font-weight: 700;"><i class="ph-duotone ph-chart-line-up"></i> התאמה ${score}%</span>
          </div>
          <div style="display: flex; gap: 8px; margin-top: 4px;">
            <button onclick="openJobModal(decodeURIComponent('${safeId}'))" class="btn-triage" style="flex: 1; width: auto; min-height: 34px; height: 34px; padding: 6px 10px; font-size: 12px; font-weight: 600; justify-content: center; background: rgba(137, 244, 231, 0.15); color: var(--dashboard-cyan); border: 1px solid rgba(137, 244, 231, 0.4); border-radius: 999px; box-sizing: border-box;">
              <i class="ph-duotone ph-eye" style="font-size: 14px;"></i> צפה בכרטיס
            </button>
            <a href="${safeLink}" target="_blank" rel="noopener noreferrer" class="btn-apply" style="flex: 1; width: auto; min-height: 34px; height: 34px; padding: 6px 10px; font-size: 12px; font-weight: 600; justify-content: center; text-decoration: none; border-radius: 999px; box-sizing: border-box;">
              <i class="ph-bold ph-arrow-square-out" style="font-size: 14px;"></i> הגש
            </a>
          </div>
        </div>
      `;

      marker.bindPopup(popupHtml, {
        maxWidth: 300,
        className: 'glass-leaflet-popup'
      });

      marker.addTo(markersClusterGroup);
    });

    const markerCountEl = document.getElementById('mapMarkersCountText');
    if (markerCountEl) {
      if (mappedCount === 0) {
        markerCountEl.textContent = 'אין משרות להצגה על המפה';
      } else if (mappedCount === 1) {
        markerCountEl.textContent = (totalVisible > 1) ? `מוצגת משרה אחת מתוך ${totalVisible} משרות על המפה` : 'מוצגת משרה אחת על המפה';
      } else {
        markerCountEl.textContent = (mappedCount < totalVisible) ? `מוצגות ${mappedCount} מתוך ${totalVisible} משרות על המפה` : `מוצגות ${mappedCount} משרות על המפה`;
      }
    }

    if (latLngBounds.length > 0) {
      try {
        const bounds = L.latLngBounds(latLngBounds);
        liveJobsMapInstance.fitBounds(bounds, { padding: [40, 40], maxZoom: 12 });
      } catch(e) {}
    }
  }

  function classifyJobSector(job) {
    if (!job) return 'אנרגיה';
    const secKey = (job.sector_key || '').toLowerCase().trim();
    const sec = (job.sector || '').toLowerCase().trim();
    const title = (job.title || '').toLowerCase().trim();

    // 1. Solar
    if (secKey === 'solar' || ['סולאר', 'solar', 'pv'].some(k => sec.includes(k))) {
      return 'סולאר';
    }
    // 2. Drones / Defense / Avionics
    if (['drones', 'cuas', 'avionics'].includes(secKey) || ['רחפן', 'כטב', 'drone', 'uav', 'אוויוניקה', 'תעופה', 'ביטחון'].some(k => sec.includes(k))) {
      return 'רחפנים';
    }
    // 3. Natural Gas
    if (['natural_gas', 'naturalgas', 'gas'].includes(secKey) || ['גז טבעי', ' גז', 'gas'].some(k => sec.includes(k))) {
      return 'גז טבעי';
    }
    // 4. SCADA & Control (Combined into one column as requested by user)
    if (['scada', 'control', 'automation'].includes(secKey) || 
        ['scada', 'בקרה', 'control', 'אוטומציה', 'noc'].some(k => sec.includes(k)) || 
        ['scada', 'בקרה', 'control room', 'noc operator', 'בקר'].some(k => title.includes(k))) {
      return 'בקרה ו-SCADA';
    }
    // 5. Storage & Energy Tech
    if (['energy_tech', 'energytech', 'storage', 'bess'].includes(secKey) || ['אגירה', 'storage', 'bess', "אנרג'י"].some(k => sec.includes(k))) {
      return 'אגירה';
    }
    // 6. Operations & Maintenance
    if (['operations', 'maintenance'].includes(secKey) || ['תפעול', 'אחזקה', 'מכונות', 'ייצור'].some(k => sec.includes(k))) {
      return 'תפעול ואחזקה';
    }
    // 7. Energy General
    return 'אנרגיה';
  }

  function getJobCuratedTags(job) {
    if (!job) return [];

    // Pre-computed curated_tags from Backend
    if (Array.isArray(job.curated_tags) && job.curated_tags.length > 0) {
      return job.curated_tags;
    }

    const tags = [];

    // 1. Stated Salary: strictly from original ad (never model predicted)
    const salarySource = (job.salary_source_type || '').toLowerCase();
    const salaryVal = (job.salary_range || '').trim();
    if ((salarySource === 'job_ad' || salarySource === 'ad' || salarySource === 'employer') && salaryVal && salaryVal !== 'לא צוין במודעה' && salaryVal !== 'לא צוין') {
      tags.push({
        type: 'tag-salary',
        icon: 'ph-bold ph-currency-circle-dollar',
        label: salaryVal
      });
    }

    // Text corpus for keywords
    const texts = [
      job.title || '',
      job.snippet || '',
      job.company_requirements || '',
      job.job_summary || '',
      job.experience_strengths || '',
      job.reasoning || '',
      job.key_highlights || ''
    ];
    const fullText = texts.join(' ').toLowerCase();

    // 2. Field Work (with negative guards)
    const fieldPosRegex = /(?:עבודת שטח|טכנאי שטח|מהנדס שטח|הנדסאי שטח|אנשי שטח|שירות שטח|התקנות שטח|פעילות שטח|אתרי לקוח|שירות באתרי לקוח|אתרי לקוחות|שירות באתרים|field technician|field engineer|field service|field operations)/i;
    const fieldNegRegex = /(?:ללא עבודת שטח|ללא שטח|אינו כולל שטח|אינה כוללת שטח|לא עבודת שטח)/i;
    if (fieldPosRegex.test(fullText) && !fieldNegRegex.test(fullText)) {
      tags.push({
        type: 'tag-field',
        icon: 'ph-bold ph-wrench',
        label: 'עבודת שטח'
      });
    }

    // 3. Company Car (with negative guards, driving license alone does not qualify)
    const carPosRegex = /(?:רכב חברה|רכב צמוד|רכב שירות|כולל רכב|רכב לצרכי עבודה|company car)/i;
    const carNegRegex = /(?:ללא רכב|אינו כולל רכב|אינה כוללת רכב|לא כולל רכב|לא רכב חברה|אין רכב חברה|אין רכב)/i;
    if (carPosRegex.test(fullText) && !carNegRegex.test(fullText)) {
      tags.push({
        type: 'tag-car',
        icon: 'ph-bold ph-car',
        label: 'רכב חברה'
      });
    }

    // 4. 24/7 Shifts / NOC (with negative guards)
    const shiftsPosRegex = /(?:24[/]7|משמרות 24[/]7|סבב 24[/]7|משמרות לילה|לילות וסופ["״]?ש|לילות וסופי שבוע|noc 24[/]7|חדר בקרה 24[/]7|24[/]7 shifts|משמרות כולל לילות|סבב משמרות מלא)/i;
    const shiftsNegRegex = /(?:ללא משמרות|ללא 24[/]7|ללא לילות|ללא סופ["״]?ש|ללא סופי שבוע)/i;
    if (shiftsPosRegex.test(fullText) && !shiftsNegRegex.test(fullText)) {
      tags.push({
        type: 'tag-shifts',
        icon: 'ph-bold ph-clock-countdown',
        label: 'משמרות 24/7'
      });
    }

    // 5. Junior / Entry-Level (with negative guards and senior exclusion)
    const juniorPosRegex = /(?:junior|ג['"״]?וניור|entry[ -]?level|ללא ניסיון|ללא נסיון|0-2 שנות ניסיון|0-1 שנות ניסיון|עד שנתיים ניסיון|מתאים למתחילים|פתיחות לבוגרים ללא ניסיון|פתיחות לבוגרים|בוגרים טריים|הכשרה מלאה על חשבון החברה|דריסת רגל|תפקיד כניסה)/i;
    const juniorNegRegex = /(?:לא מתאים לג['"״]?וניור|לא מתאים למתחילים|דורש ניסיון משמעותי|לא ללא ניסיון)/i;
    const isSeniorTitle = /(?:senior|ראש צוות|lead)/i.test(job.title || '');
    const isJuniorOpen = (job.junior_openness || '').toString().toLowerCase() === 'כן';

    if ((juniorPosRegex.test(fullText) || isJuniorOpen) && !juniorNegRegex.test(fullText) && !isSeniorTitle) {
      tags.push({
        type: 'tag-junior',
        icon: 'ph-bold ph-graduation-cap',
        label: 'Junior'
      });
    }

    return tags.slice(0, 5);
  }

  // jobStates initialized above

  function getAllAvailableJobs() {
    const seenLinks = new Set((rawJobsData || []).map(j => j.link));
    const all = [...(rawJobsData || [])];
    if (typeof historicalCatalog !== 'undefined' && historicalCatalog) {
      Object.keys(jobStates).forEach(link => {
        if ((jobStates[link] === 'saved' || jobStates[link] === 'rejected') && !seenLinks.has(link) && historicalCatalog[link]) {
          all.push(historicalCatalog[link]);
          seenLinks.add(link);
        }
      });
      Object.keys(starredJobs).forEach(link => {
        if (starredJobs[link] && !seenLinks.has(link) && historicalCatalog[link]) {
          all.push(historicalCatalog[link]);
          seenLinks.add(link);
        }
      });
    }
    return all;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function sanitizeUrl(rawUrl) {
    if (!rawUrl) return '#';
    const trimmed = String(rawUrl).trim();
    if (/^(?:https?:\/\/|mailto:)/i.test(trimmed)) {
      try {
        const url = new URL(trimmed);
        if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) return '#';
        return escapeHtml(url.href);
      } catch (_) { return '#'; }
    }
    return '#';
  }

  function classifyJobRegion(locStr) {
    if (!locStr) return 'center';
    const loc = locStr.toLowerCase();
    if (loc.includes('צפון') || loc.includes('חיפה') || loc.includes('קריות') || loc.includes('נשר') || 
        loc.includes('יקנעם') || loc.includes('מגדל העמק') || loc.includes('כרמיאל') || loc.includes('גליל') || 
        loc.includes('דלתון') || loc.includes('יזרעאל') || loc.includes('עפולה') || loc.includes('טבריה') || 
        loc.includes('לוחמי הגטאות')) {
      return 'north';
    }
    if (loc.includes('שרון') || loc.includes('נתניה') || loc.includes('הרצליה') || loc.includes('רעננה') || 
        loc.includes('כפר סבא') || loc.includes('הוד השרון') || loc.includes('עמק חפר') || loc.includes('חדרה')) {
      return 'sharon';
    }
    if (loc.includes('דרום') || loc.includes('אשדוד') || loc.includes('אשקלון') || loc.includes('באר שבע') || 
        loc.includes('קריית גת') || loc.includes('קרית גת') || loc.includes('נאות חובב') || loc.includes('דימונה') || 
        loc.includes('להבים') || loc.includes('נגב') || loc.includes('שפלה')) {
      return 'south';
    }
    if (loc.includes('ארצי') || loc.includes('שטח') || loc.includes('פריסה ארצית') || loc.includes('תחנות כוח')) {
      return 'nationwide';
    }
    return 'center';
  }

  function stripEmojis(str) {
    if (!str) return '';
    return str.replace(/\p{Extended_Pictographic}/gu, '').replace(/[\u2600-\u27BF]/g, '').trim();
  }

  // Native <dialog> helpers: top layer, inert page, focus return and Esc/back-gesture dismissal
  function openDialogEl(el) {
    if (!el) return;
    if (typeof el.showModal === 'function') {
      if (!el.open) el.showModal();
    } else {
      el.setAttribute('open', '');
    }
  }

  function closeDialogEl(el) {
    if (!el) return;
    if (typeof el.close === 'function') {
      if (el.open) el.close();
    } else {
      el.removeAttribute('open');
    }
  }

  // close does not bubble; capture it so Esc and back-gesture dismissal also release scroll lock
  document.addEventListener('close', (e) => {
    if (e.target && e.target.matches && e.target.matches('dialog.dashboard-modal-backdrop')) {
      document.body.style.overflow = '';
    }
  }, true);

  function toggleCardDetails(btn, evt) {
    if (evt) {
      evt.stopPropagation();
      evt.preventDefault();
    }
    const card = btn.closest('.job-card');
    if (!card) return;
    // On phones the full analysis opens in a full-screen sheet instead of growing the feed
    const cardId = card.getAttribute('data-id');
    if (cardId && window.matchMedia('(max-width: 768px)').matches && allJobsMap[cardId]) {
      openJobModal(cardId);
      return;
    }
    const details = card.querySelector('.job-details-collapsible');
    if (!details) return;
    const isExpanded = details.classList.contains('expanded');
    if (isExpanded) {
      details.classList.remove('expanded');
      btn.classList.remove('expanded');
      btn.setAttribute('aria-expanded', 'false');
      btn.innerHTML = '<span>הרחב ניתוח מלא</span> <i class="ph-bold ph-caret-down"></i>';
    } else {
      details.classList.add('expanded');
      btn.classList.add('expanded');
      btn.setAttribute('aria-expanded', 'true');
      btn.innerHTML = '<span>הסתר ניתוח מלא</span> <i class="ph-bold ph-caret-up"></i>';
    }
  }

  function getJobSalaryVal(job) {
    if (!job) return 0;
    if (typeof job.p50 === 'number' && !isNaN(job.p50) && job.p50 > 0) return job.p50;
    if (typeof job.p75 === 'number' && !isNaN(job.p75) && job.p75 > 0) return job.p75;
    if (typeof job.p25 === 'number' && !isNaN(job.p25) && job.p25 > 0) return job.p25;
    if (job.salary_range && typeof job.salary_range === 'string' && job.salary_range !== 'לא צוין במודעה') {
      const clean = job.salary_range.replace(/,/g, '');
      const matches = clean.match(/\\d{4,6}/g);
      if (matches && matches.length > 0) {
        if (matches.length >= 2) {
          return (Number(matches[0]) + Number(matches[1])) / 2;
        }
        return Number(matches[0]);
      }
    }
    return 0;
  }

  function renderCards() {
    const container = document.getElementById('cardsContainer');
    container.innerHTML = '';

    const displayJobs = getAllAvailableJobs();
    if (!displayJobs || displayJobs.length === 0) {
      document.getElementById('emptyState').style.display = 'block';
      return;
    }

    let sortedJobs = [...displayJobs];
    sortedJobs.sort((a, b) => {
      if (currentSort === 'score_desc') {
        const scoreA = Number(a.match_score) || 0;
        const scoreB = Number(b.match_score) || 0;
        if (scoreB !== scoreA) return scoreB - scoreA;
        const dateA = a.date || '0000-00-00';
        const dateB = b.date || '0000-00-00';
        return dateB.localeCompare(dateA);
      } else if (currentSort === 'salary_desc') {
        const salA = getJobSalaryVal(a);
        const salB = getJobSalaryVal(b);
        if (salB !== salA) return salB - salA;
        const scoreA = Number(a.match_score) || 0;
        const scoreB = Number(b.match_score) || 0;
        if (scoreB !== scoreA) return scoreB - scoreA;
        const dateA = a.date || '0000-00-00';
        const dateB = b.date || '0000-00-00';
        return dateB.localeCompare(dateA);
      } else if (currentSort === 'company_asc') {
        const compA = (a.company || '').trim();
        const compB = (b.company || '').trim();
        const compDiff = compA.localeCompare(compB, 'he', { sensitivity: 'base' });
        if (compDiff !== 0) return compDiff;
        const scoreA = Number(a.match_score) || 0;
        const scoreB = Number(b.match_score) || 0;
        if (scoreB !== scoreA) return scoreB - scoreA;
        const dateA = a.date || '0000-00-00';
        const dateB = b.date || '0000-00-00';
        return dateB.localeCompare(dateA);
      } else {
        const dateA = a.date || '0000-00-00';
        const dateB = b.date || '0000-00-00';
        if (dateA > dateB) return -1;
        if (dateA < dateB) return 1;
        const scoreA = Number(a.match_score) || 0;
        const scoreB = Number(b.match_score) || 0;
        return scoreB - scoreA;
      }
    });

    sortedJobs.forEach((job, idx) => {
      const id = job.link || `job_${idx}`;
      const score = Math.max(0, Math.min(100, Number(job.base_match_score ?? job.match_score) || 0));
      const company = stripEmojis(job.company || 'חברה');
      const title = stripEmojis(job.title || 'משרה ללא כותרת');
      const link = job.link || '#';
      const secKey = job.sector_key || 'energy';
      const jobDate = job.date || 'היום';
      const classifiedSector = classifyJobSector(job);

      let scoreClass = 'badge-score-high';
      if (score < 80) scoreClass = 'badge-score-fair';
      else if (score < 90) scoreClass = 'badge-score-med';

      const domain = escapeHtml(stripEmojis(job.company_domain_product || job.company_summary || 'מידע על החברה לא צוין'));
      const loc = escapeHtml(stripEmojis(job.location || 'מיקום לא צוין'));
      const jobSum = escapeHtml(stripEmojis(job.job_summary || job.company_summary || 'לא צוין תיאור מלא למשרה.'));
      const strengths = escapeHtml(stripEmojis(job.experience_strengths || job.reasoning || 'אין ניתוח התאמה מאומת למשרה זו.'));
      const quickInsight = escapeHtml(stripEmojis(job.reasoning || job.experience_strengths || job.job_summary || 'אין ניתוח התאמה מאומת למשרה זו.'));
      const fitGaps = escapeHtml(stripEmojis(job.fit_gaps || 'אין מספיק מידע לאימות פערי ההתאמה.'));
      const companyReqs = escapeHtml(stripEmojis(job.company_requirements || job.key_highlights || (job.snippet ? job.snippet.slice(0, 160) + '...' : '') || 'דרישות סף טכניות בהתאם לתיאור המשרה (פירוט מלא בקישור להגשה).'));
      const scopeAndRole = formatJobScopeAndRole(job);
      const matchInfo = formatJobMatchAndGaps(job);
      const safeCompany = escapeHtml(company);
      const safeTitle = escapeHtml(title);
      const safeLink = sanitizeUrl(link);
      const logoHtml = getCompanyLogoHtml(company, job.logo);

      // Source detection & styling
      let sourceName = job.source;
      if (!sourceName) {
        if (link.includes('drushim.co.il')) sourceName = 'דרושים';
        else if (link.includes('comeet.com') || link.includes('comeet')) sourceName = 'Comeet';
        else if (link.includes('indeed.com')) sourceName = 'Indeed';
        else if (link.includes('glassdoor.com')) sourceName = 'Glassdoor';
        else if (link.includes('linkedin.com')) sourceName = 'LinkedIn';
        else sourceName = 'LinkedIn';
      }

      let sourceChipStyle = 'color: #38bdf8; border-color: rgba(56, 189, 248, 0.35); background: rgba(56, 189, 248, 0.1);';
      let sourceIcon = 'ph-linkedin-logo';
      if (sourceName.toLowerCase().includes('drushim') || sourceName.includes('דרושים')) {
        sourceChipStyle = 'color: var(--dashboard-gold); border-color: rgba(255, 211, 104, 0.4); background: rgba(255, 211, 104, 0.12);';
        sourceIcon = 'ph-briefcase';
      } else if (sourceName.toLowerCase().includes('comeet')) {
        sourceChipStyle = 'color: #c084fc; border-color: rgba(192, 132, 252, 0.4); background: rgba(192, 132, 252, 0.12);';
        sourceIcon = 'ph-buildings';
      } else if (sourceName.toLowerCase().includes('indeed')) {
        sourceChipStyle = 'color: #3b82f6; border-color: rgba(59, 130, 246, 0.4); background: rgba(59, 130, 246, 0.12);';
        sourceIcon = 'ph-magnifying-glass';
      } else if (sourceName.toLowerCase().includes('glassdoor')) {
        sourceChipStyle = 'color: #10b981; border-color: rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.12);';
        sourceIcon = 'ph-door';
      }

      const isStarred = Boolean(starredJobs[id]);
      const state = jobStates[id] || 'pending';
      const classifiedRegion = classifyJobRegion(loc);
      const salaryTagHtml = formatJobSalaryTag(job);

      const curatedTags = getJobCuratedTags(job);
      let tagsHtml = '';
      if (curatedTags && curatedTags.length > 0) {
        const pills = curatedTags.map(t => `<span class="job-tag-pill ${escapeHtml(t.type)}"><i class="${escapeHtml(t.icon)}"></i><span dir="auto">${escapeHtml(t.label)}</span></span>`).join('');
        tagsHtml = `<div class="job-card-tags">${pills}</div>`;
      }

      const card = document.createElement('article');
      card.setAttribute('data-id', id);
      card.setAttribute('data-sector', secKey);
      card.setAttribute('data-classified-sector', classifiedSector);
      card.setAttribute('data-location', loc.toLowerCase());
      card.setAttribute('data-region', classifiedRegion);
      card.setAttribute('data-starred', isStarred ? 'true' : 'false');
      card.setAttribute('data-score', score);
      card.className = `dashboard-card job-card ${isStarred ? 'is-starred-card' : ''}`;

      card.innerHTML = `
        <!-- Top Meta Row -->
        <div class="job-card-topbar">
          <div class="job-card-topbar-primary">
            <div class="job-card-actions-group" style="display: flex; align-items: center; gap: 5px; flex-shrink: 0;">
              <button type="button" class="btn-star ${isStarred ? 'is-starred' : ''}" onclick="toggleStar(${escapeHtml(JSON.stringify(String(id)))}, event)" title="${isStarred ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב'}" aria-label="${isStarred ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב'}">
                <i class="${isStarred ? 'ph-fill ph-star' : 'ph-bold ph-star'}"></i>
              </button>
              <button type="button" class="btn-copy-link" onclick="copyJobLink(${escapeHtml(JSON.stringify(String(link)))}, event)" title="העתק קישור למשרה" aria-label="העתק קישור למשרה">
                <i class="ph-bold ph-share-network"></i>
              </button>
            </div>
            <div class="job-card-topbar-badges" style="display: flex; align-items: center; gap: 6px; min-width: 0; flex: 1; overflow: hidden;">
              ${salaryTagHtml}
              <div class="badge-score ${scoreClass}">
                <span><i class="ph-duotone ph-lightning"></i> ${score}%</span> התאמה
              </div>
            </div>
          </div>
        </div>

        <!-- Title & Company Header -->
        <div class="job-card-main-header">
          ${logoHtml}
          <div class="job-header-text">
            <div class="job-company-name" dir="auto" title="${safeCompany}"><bdi>${safeCompany}</bdi></div>
            <h2 class="job-title-text" dir="auto" title="${safeTitle}"><bdi>${safeTitle}</bdi></h2>
          </div>
        </div>

        <!-- Job Card Meta Row: Date, Location, Source -->
        <div class="job-card-meta-row">
          <span class="meta-item"><i class="ph-duotone ph-calendar-blank"></i> <span class="meta-label">תאריך ברשימה:</span> ${escapeHtml(jobDate)}</span>
          <span class="meta-item"><i class="ph-duotone ph-map-pin"></i> ${loc}</span>
          <span class="meta-item"><i class="ph-duotone ${sourceIcon}"></i> <span class="meta-label">מקור:</span> ${escapeHtml(sourceName)}</span>
        </div>

        <!-- Curated Tags (0 to 5 tags, flexible) -->
        ${tagsHtml}

        <!-- Clean Key Requirements (Anchor 2 of 3) -->
        <div class="job-key-requirements">
          <div class="job-key-requirements-header">
            <i class="ph-duotone ph-check-circle"></i>
            <span>דרישות סף:</span>
          </div>
          <div class="job-key-requirements-content">${companyReqs}</div>
        </div>

        <!-- Collapsible Full Information Panels (Anchors 1 & 3 of 3) -->
        <div class="job-details-collapsible">
          <div class="job-boxes-grid" style="margin-top: 8px;">
            <div class="job-box">
              <strong><i class="ph-duotone ph-buildings"></i> תחום ותפקיד:</strong>
              <span>${scopeAndRole}</span>
            </div>
            <div class="job-box ${matchInfo.isNoGap ? 'highlight-mint' : 'highlight-gold'}">
              <strong><i class="ph-duotone ph-sparkle"></i> התאמה ופערים:</strong>
              <span>${matchInfo.fullHtml}</span>
            </div>
          </div>
        </div>

        <!-- Action Bar -->
        <div class="job-actions-bar">
          <div class="job-actions-top-row">
            <button type="button" class="btn-toggle-details" onclick="toggleCardDetails(this, event)" aria-expanded="false" title="הרחב ניתוח מלא">
              <span>הרחב ניתוח מלא</span>
              <i class="ph-bold ph-caret-down"></i>
            </button>
            ${state === 'rejected' ? `
            <button type="button" onclick="restoreJob(${escapeHtml(JSON.stringify(String(id)))}, event)" class="btn-triage action-restore-btn" title="שחזר לחדשות" aria-label="שחזר לחדשות">
              <i class="ph-duotone ph-arrow-counter-clockwise"></i> <span class="btn-text">שחזר לחדשות</span>
            </button>
            <button type="button" onclick="purgeJobPermanently(${escapeHtml(JSON.stringify(String(id)))}, event)" class="btn-triage action-reject-btn rejected-active" title="מחיקה לצמיתות" aria-label="מחיקה לצמיתות" style="background: rgba(239, 68, 68, 0.25); color: #fca5a5; border-color: rgba(239, 68, 68, 0.5);">
              <i class="ph-duotone ph-trash-simple"></i>
            </button>
            ` : `
            <button type="button" onclick="toggleAction(${escapeHtml(JSON.stringify(String(id)))}, 'saved', event)" class="btn-triage action-save-btn ${state === 'saved' ? 'saved-active' : ''}" title="שמור להגשה">
              <i class="ph-duotone ph-bookmark-simple"></i> <span class="btn-text">${state === 'saved' ? 'נשמר להגשה' : 'שמור להגשה'}</span>
            </button>
            <button type="button" onclick="toggleAction(${escapeHtml(JSON.stringify(String(id)))}, 'rejected', event)" class="btn-triage action-reject-btn" title="הסר משרה" aria-label="הסר משרה">
              <i class="ph-duotone ph-trash"></i>
            </button>
            `}
          </div>
          <div class="job-actions-bottom-row" style="display: flex; gap: 8px; align-items: center;">
            <a href="${safeLink}" target="_blank" rel="noopener noreferrer" class="btn-apply btn-apply-elegant" style="flex: 1;" onclick="event.stopPropagation()">
              <span>הגש מועמדות</span> <i class="ph-duotone ph-arrow-up-right"></i>
            </a>
            ${Array.isArray(altLinksStore[id]) && altLinksStore[id].length > 0 ? `
              <a href="${sanitizeUrl(altLinksStore[id][0])}" target="_blank" rel="noopener noreferrer" class="btn-triage" style="padding: 10px 14px; font-size: 13px; color: var(--dashboard-gold); border-color: rgba(255, 211, 104, 0.4);" onclick="event.stopPropagation()" title="מקור נוסף להגשת מועמדות (מוזג מכפילות)">
                <i class="ph-duotone ph-link"></i> <span>מקור נוסף (${altLinksStore[id].length})</span>
              </a>
            ` : ''}
          </div>
        </div>
      `;

      allJobsMap[id] = job;
      container.appendChild(card);
    });

    updateUI();
  }

  function openJobModal(id) {
    const job = allJobsMap[id];
    if (!job) return;

    const modal = document.getElementById('jobDetailsModal');
    const headerActions = document.getElementById('jobModalTopActions');
    const body = document.getElementById('jobModalBody');
    const bottomBar = document.getElementById('jobModalBottomBar');
    if (!modal || !headerActions || !body || !bottomBar) return;

    const score = Math.max(0, Math.min(100, Number(job.base_match_score ?? job.match_score) || 0));
    const company = stripEmojis(job.company || 'חברה');
    const title = stripEmojis(job.title || 'משרה ללא כותרת');
    const link = job.link || '#';
    const safeCompany = escapeHtml(company);
    const safeTitle = escapeHtml(title);
    const safeLink = sanitizeUrl(link);
    const loc = escapeHtml(stripEmojis(job.location || 'מיקום לא צוין'));
    const jobDate = escapeHtml(job.date || 'היום');
    const classifiedSector = classifyJobSector(job);
    const domain = escapeHtml(stripEmojis(job.company_domain_product || job.company_summary || 'מידע על החברה לא צוין'));
    const jobSum = escapeHtml(stripEmojis(job.job_summary || job.company_summary || 'לא צוין תיאור מלא למשרה.'));
    const strengths = escapeHtml(stripEmojis(job.experience_strengths || job.reasoning || 'אין ניתוח התאמה מאומת למשרה זו.'));
    const companyReqs = escapeHtml(stripEmojis(job.company_requirements || job.key_highlights || (job.snippet ? job.snippet.slice(0, 160) + '...' : '') || 'דרישות סף טכניות בהתאם לתיאור המשרה.'));
    const quickInsight = escapeHtml(stripEmojis(job.reasoning || job.experience_strengths || job.job_summary || 'אין ניתוח התאמה מאומת למשרה זו.'));
    const fitGaps = escapeHtml(stripEmojis(job.fit_gaps || 'אין מספיק מידע לאימות פערי ההתאמה.'));
    const scopeAndRole = formatJobScopeAndRole(job);
    const matchInfo = formatJobMatchAndGaps(job);
    const logoHtml = getCompanyLogoHtml(company, job.logo);
    const companyBdi = `<bdi dir="auto">${safeCompany}</bdi>`;

    let sourceName = job.source;
    if (!sourceName) {
      if (link.includes('drushim.co.il')) sourceName = 'דרושים';
      else if (link.includes('comeet.com') || link.includes('comeet')) sourceName = 'Comeet';
      else if (link.includes('indeed.com')) sourceName = 'Indeed';
      else if (link.includes('glassdoor.com')) sourceName = 'Glassdoor';
      else sourceName = 'LinkedIn';
    }
    let sourceIcon = 'ph-linkedin-logo';
    if (sourceName.toLowerCase().includes('drushim') || sourceName.includes('דרושים')) {
      sourceIcon = 'ph-briefcase';
    } else if (sourceName.toLowerCase().includes('comeet')) {
      sourceIcon = 'ph-buildings';
    } else if (sourceName.toLowerCase().includes('indeed')) {
      sourceIcon = 'ph-magnifying-glass';
    } else if (sourceName.toLowerCase().includes('glassdoor')) {
      sourceIcon = 'ph-door';
    }

    let scoreClass = 'badge-score-high';
    if (score < 80) scoreClass = 'badge-score-fair';
    else if (score < 90) scoreClass = 'badge-score-med';

    const isStarred = Boolean(starredJobs[id]);
    const state = jobStates[id] || 'pending';
    const salaryTagHtml = formatJobSalaryTag(job);

    const curatedTags = getJobCuratedTags(job);
    let tagsHtml = '';
    if (curatedTags && curatedTags.length > 0) {
      const pills = curatedTags.map(t => `<span class="job-tag-pill ${escapeHtml(t.type)}"><i class="${escapeHtml(t.icon)}"></i><span dir="auto">${escapeHtml(t.label)}</span></span>`).join('');
      tagsHtml = `<div class="job-card-tags" style="margin: 6px 0 10px;">${pills}</div>`;
    }

    headerActions.innerHTML = `
      <button type="button" class="btn-star ${isStarred ? 'is-starred' : ''}" onclick="toggleStar(${escapeHtml(JSON.stringify(String(id)))}, event); updateModalStar(${escapeHtml(JSON.stringify(String(id)))});" title="${isStarred ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב'}" aria-label="${isStarred ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב'}">
        <i class="${isStarred ? 'ph-fill ph-star' : 'ph-bold ph-star'}"></i>
      </button>
      <button type="button" class="btn-copy-link" onclick="copyJobLink(${escapeHtml(JSON.stringify(String(link)))}, event)" title="העתק קישור למשרה" aria-label="העתק קישור למשרה">
        <i class="ph-bold ph-share-network"></i>
      </button>
      <div style="display: flex; align-items: center; gap: 8px;">
        ${salaryTagHtml}
        <div class="badge-score ${scoreClass}" title="ציון התאמה ${score}%">
          <span><i class="ph-duotone ph-lightning"></i> ${score}%</span>
        </div>
      </div>
    `;

    body.innerHTML = `
      <div style="display: flex; align-items: flex-start; gap: 14px;">
        ${logoHtml}
        <div style="flex: 1; min-width: 0;">
          <div style="font-size: 13.5px; font-weight: 700; color: var(--dashboard-cyan); margin-bottom: 2px;" dir="auto" title="${safeCompany}"><bdi>${safeCompany}</bdi></div>
          <h2 style="font-size: 17.5px; font-weight: 700; color: #fff; margin: 0 0 6px; line-height: 1.3;" dir="auto" title="${safeTitle}"><bdi>${safeTitle}</bdi></h2>
          <div style="font-size: 12px; color: var(--dashboard-muted); display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
            <span><i class="ph-duotone ph-calendar-blank"></i> תאריך ברשימה: ${escapeHtml(jobDate)}</span>
            <span><i class="ph-duotone ph-map-pin"></i> ${loc}</span>
            <span><i class="ph-duotone ${sourceIcon}"></i> מקור: ${escapeHtml(sourceName)}</span>
          </div>
        </div>
      </div>

      ${tagsHtml}

      <!-- 3 Focused Anchors (Option 1) -->
      <div class="job-boxes-grid" style="grid-template-columns: 1fr; gap: 8px; margin: 4px 0 8px;">
        <div class="job-box">
          <strong><i class="ph-duotone ph-buildings"></i> תחום ותפקיד:</strong>
          <span>${scopeAndRole}</span>
        </div>
        <div class="job-box">
          <strong><i class="ph-duotone ph-check-square"></i> דרישות סף:</strong>
          <span>${companyReqs}</span>
        </div>
        <div class="job-box ${matchInfo.isNoGap ? 'highlight-mint' : 'highlight-gold'}">
          <strong><i class="ph-duotone ph-sparkle"></i> התאמה ופערים:</strong>
          <span>${matchInfo.fullHtml}</span>
        </div>
      </div>
    `;

    bottomBar.innerHTML = `
      <div class="job-actions-top-row" style="width: 100%; display: flex; align-items: center; gap: 8px;">
        ${state === 'rejected' ? `
        <button onclick="restoreJob(${escapeHtml(JSON.stringify(String(id)))}); closeJobModal();" class="btn-triage" style="flex: 1;" title="שחזר למשרות חדשות">
          <i class="ph-duotone ph-arrow-counter-clockwise"></i> <span>שחזר לחדשות</span>
        </button>
        <button onclick="purgeJobPermanently(${escapeHtml(JSON.stringify(String(id)))}); closeJobModal();" class="btn-triage rejected-active" style="flex: 1; border-radius: 12px; min-height: 40px; padding: 0 16px; background: rgba(239, 68, 68, 0.25); color: #fca5a5; border-color: rgba(239, 68, 68, 0.5); display: inline-flex; align-items: center; justify-content: center; gap: 8px;" title="מחק לצמיתות">
          <i class="ph-duotone ph-trash-simple"></i> <span>מחק לצמיתות</span>
        </button>
        ` : `
        <button id="modalSaveBtn" onclick="toggleAction(${escapeHtml(JSON.stringify(String(id)))}, 'saved'); updateModalTriageButtons(${escapeHtml(JSON.stringify(String(id)))});" class="btn-triage action-save-btn ${state === 'saved' ? 'saved-active' : ''}" style="flex: 1;" title="שמור להגשה">
          <i class="ph-duotone ph-bookmark-simple"></i> <span class="btn-text">${state === 'saved' ? 'נשמר להגשה' : 'שמור להגשה'}</span>
        </button>
        <button id="modalRejectBtn" onclick="toggleAction(${escapeHtml(JSON.stringify(String(id)))}, 'rejected'); updateModalTriageButtons(${escapeHtml(JSON.stringify(String(id)))});" class="btn-triage action-reject-btn ${state === 'rejected' ? 'rejected-active' : ''}" title="הסר משרה" aria-label="הסר משרה">
          <i class="ph-duotone ph-trash"></i>
        </button>
        `}
      </div>
      <div class="job-actions-bottom-row" style="width: 100%; margin-top: 8px; display: flex; gap: 8px; align-items: center;">
        <a href="${safeLink}" target="_blank" rel="noopener noreferrer" class="btn-apply btn-apply-elegant" style="flex: 1;">
          <span>הגש מועמדות באתר המשרה</span> <i class="ph-duotone ph-arrow-up-right"></i>
        </a>
        ${Array.isArray(altLinksStore[id]) && altLinksStore[id].length > 0 ? `
          <a href="${sanitizeUrl(altLinksStore[id][0])}" target="_blank" rel="noopener noreferrer" class="btn-triage" style="padding: 10px 14px; font-size: 13px; color: var(--dashboard-gold); border-color: rgba(255, 211, 104, 0.4);" title="מקור נוסף להגשת מועמדות (מוזג מכפילות)">
            <i class="ph-duotone ph-link"></i> <span>מקור נוסף (${altLinksStore[id].length})</span>
          </a>
        ` : ''}
      </div>
    `;

    openDialogEl(modal);
    document.body.style.overflow = 'hidden';
  }

  function updateModalStar(id) {
    const isStarred = Boolean(starredJobs[id]);
    const starBtn = document.querySelector('#jobModalTopActions .btn-star');
    if (starBtn) {
      starBtn.className = `btn-star ${isStarred ? 'is-starred' : ''}`;
      starBtn.setAttribute('title', isStarred ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב');
      starBtn.setAttribute('aria-label', isStarred ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב');
      starBtn.innerHTML = `<i class="${isStarred ? 'ph-fill ph-star' : 'ph-bold ph-star'}"></i>`;
    }
  }

  function updateModalTriageButtons(id) {
    const state = jobStates[id] || 'pending';
    const saveBtn = document.getElementById('modalSaveBtn');
    const rejectBtn = document.getElementById('modalRejectBtn');
    if (saveBtn) {
      saveBtn.className = `btn-triage action-save-btn ${state === 'saved' ? 'saved-active' : ''}`;
      saveBtn.querySelector('span').textContent = state === 'saved' ? 'נשמר להגשה' : 'שמור להגשה';
    }
    if (rejectBtn) {
      rejectBtn.className = `btn-triage action-reject-btn ${state === 'rejected' ? 'rejected-active' : ''}`;
    }
  }

  function closeJobModal() {
    const modal = document.getElementById('jobDetailsModal');
    closeDialogEl(modal);
    document.body.style.overflow = '';
  }

  function updateSortIconAndToast(sortVal, showUserToast = true) {
    const icon = document.getElementById('sortIcon');
    const select = document.getElementById('sortSelect');
    if (select && select.value !== sortVal) {
      select.value = sortVal;
    }
    let iconClass = 'ph-calendar-blank';
    let toastMsg = 'מיון: התאריך החדש קודם';

    if (sortVal === 'score_desc') {
      iconClass = 'ph-sort-descending';
      toastMsg = 'מיון: ציון התאמה מגבוה לנמוך';
    } else if (sortVal === 'salary_desc') {
      iconClass = 'ph-currency-circle-dollar';
      toastMsg = 'מיון: רמת שכר מגבוה לנמוך';
    } else if (sortVal === 'company_asc') {
      iconClass = 'ph-buildings';
      toastMsg = 'מיון: שם חברה מא׳ עד ת׳';
    } else {
      iconClass = 'ph-calendar-blank';
      toastMsg = 'מיון: התאריך החדש קודם';
    }

    if (icon) {
      icon.className = `ph-duotone ${iconClass}`;
    }
    if (showUserToast) {
      showToast(iconClass, toastMsg);
    }
  }

  function changeSort(sortVal) {
    currentSort = sortVal;
    try {
      localStorage.setItem(SORT_STORAGE_KEY, sortVal);
    } catch(e) {}
    updateSortIconAndToast(sortVal, true);
    renderCards();
  }

  function toggleSort() {
    const cycle = ['date_desc', 'score_desc', 'salary_desc', 'company_asc'];
    const currentIdx = cycle.indexOf(currentSort);
    const nextSort = cycle[(currentIdx + 1) % cycle.length];
    changeSort(nextSort);
  }

  function toggleAction(id, action, evt) {
    if (evt) {
      evt.stopPropagation();
      evt.preventDefault();
    }
    recordLocalEdit();
    const current = getJobState(id);
    const keys = getJobKeys(id);

    if (action === 'rejected') {
      keys.forEach(k => {
        delete starredJobs[k];
      });
      for (const k of Object.keys(starredJobs)) {
        if (keys.some(ref => getCanonicalJobKey(k) === getCanonicalJobKey(ref))) delete starredJobs[k];
      }
      saveStarredJobs(starredJobs);

      if (current === 'rejected') {
        keys.forEach(k => {
          jobStates[k] = 'purged';
        });
        showToast('ph-trash', 'המשרה נמחקה לצמיתות ולא תוצג שוב');
      } else {
        keys.forEach(k => {
          jobStates[k] = 'rejected';
        });
        showToast('ph-trash', 'המשרה הועברה למשרות שהוסרו');
      }
    } else if (action === 'saved') {
      if (current === 'saved') {
        keys.forEach(k => {
          delete jobStates[k];
        });
        for (const k of Object.keys(jobStates)) {
          if (keys.some(ref => getCanonicalJobKey(k) === getCanonicalJobKey(ref))) delete jobStates[k];
        }
        showToast('ph-arrow-counter-clockwise', 'המשרה הוסרה מהשמורות והוחזרה לחדשות');
      } else {
        keys.forEach(k => {
          jobStates[k] = 'saved';
        });
        showToast('ph-bookmark-simple', 'המשרה נשמרה להגשה והועברה ללשונית נשמרו');
      }
    }
    saveTriageState(jobStates);
    renderCards();
    updateUI();
    scheduleCloudPush();
  }

  function purgeJobPermanently(id, evt) {
    if (evt) {
      evt.stopPropagation();
      evt.preventDefault();
    }
    recordLocalEdit();
    const keys = getJobKeys(id);
    keys.forEach(k => {
      delete starredJobs[k];
      jobStates[k] = 'purged';
    });
    for (const k of Object.keys(starredJobs)) {
      if (keys.some(ref => getCanonicalJobKey(k) === getCanonicalJobKey(ref))) delete starredJobs[k];
    }
    saveStarredJobs(starredJobs);
    saveTriageState(jobStates);
    renderCards();
    updateUI();
    scheduleCloudPush();
    showToast('ph-trash', 'המשרה נמחקה לצמיתות ולא תוצג שוב');
  }

  function restoreJob(id, evt) {
    if (evt) {
      evt.stopPropagation();
      evt.preventDefault();
    }
    recordLocalEdit();
    const keys = getJobKeys(id);
    const restoredMap = loadRestoredJobs();
    keys.forEach(k => {
      restoredMap[k] = true;
    });
    saveRestoredJobs(restoredMap);

    keys.forEach(k => {
      delete starredJobs[k];
      delete jobStates[k];
    });
    for (const k of Object.keys(starredJobs)) {
      if (keys.some(ref => getCanonicalJobKey(k) === getCanonicalJobKey(ref))) delete starredJobs[k];
    }
    for (const k of Object.keys(jobStates)) {
      if (keys.some(ref => getCanonicalJobKey(k) === getCanonicalJobKey(ref))) delete jobStates[k];
    }
    saveStarredJobs(starredJobs);
    saveTriageState(jobStates);
    renderCards();
    updateUI();
    scheduleCloudPush();
    showToast('ph-arrow-counter-clockwise', 'המשרה שוחזרה בהצלחה למשרות חדשות');
  }

  function setFilter(filter, el) {
    currentFilter = filter;

    const sectorSelect = document.getElementById('sectorFilter');
    if (sectorSelect) sectorSelect.value = 'all';
    const regionSelect = document.getElementById('regionFilter');
    if (regionSelect) regionSelect.value = 'all';

    document.querySelectorAll('.stat-cube-btn').forEach(b => {
      b.classList.remove('active');
      b.removeAttribute('aria-current');
    });
    const targetEl = el || document.getElementById('cube_' + filter);
    if (targetEl) {
      targetEl.classList.add('active');
      targetEl.setAttribute('aria-current', 'page');
    }

    document.querySelectorAll('.metric-summary-pill').forEach(p => p.classList.remove('active-pill'));
    const pillMap = { 'all': 'lime', 'starred': 'gold', 'saved': 'cyan', 'rejected': 'rose' };
    const activePill = document.querySelector(`.metric-summary-pill.${pillMap[filter]}`);
    if (activePill) activePill.classList.add('active-pill');

    if (filter === 'saved' || filter === 'rejected' || filter === 'starred') {
      loadHistoricalCatalogOnDemand();
    }

    const currentCardCount = document.querySelectorAll('.job-card').length;
    const availableCount = getAllAvailableJobs().length;
    if (currentCardCount !== availableCount) {
      renderCards();
    } else {
      updateUI();
    }
  }

  let searchDebounceTimer = null;
  function onSearchInput(val) {
    const wrapper = document.getElementById('searchInputWrapper');
    if (wrapper) {
      wrapper.classList.toggle('has-value', Boolean(val && val.trim().length > 0));
    }
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
    }
    searchDebounceTimer = setTimeout(() => {
      filterCards();
    }, 250);
  }

  function clearSearchInput() {
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
    }
    const input = document.getElementById('searchInput');
    const wrapper = document.getElementById('searchInputWrapper');
    if (input) {
      input.value = '';
      input.focus();
    }
    if (wrapper) {
      wrapper.classList.remove('has-value');
    }
    filterCards();
  }

  function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
  }

  function highlightSearchTerms(el, terms) {
    if (!el) return;
    if (!el.__originalHtml) {
      el.__originalHtml = el.innerHTML;
    }
    if (!terms || terms.length === 0) {
      el.innerHTML = el.__originalHtml;
      return;
    }

    let html = el.__originalHtml;
    terms.forEach(term => {
      const regex = new RegExp(`(?![^<]*>)(${escapeRegex(term)})`, 'gi');
      html = html.replace(regex, '<mark class="search-highlight">$1</mark>');
    });
    el.innerHTML = html;
  }

  function copyJobLink(link, event) {
    if (event) {
      event.stopPropagation();
      event.preventDefault();
    }
    if (!link) return;

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(link).then(() => {
        showToast('ph-share-network', 'הקישור למשרה הועתק ללוח בהצלחה!');
      }).catch(() => {
        fallbackCopy(link);
      });
    } else {
      fallbackCopy(link);
    }
  }

  function fallbackCopy(text) {
    try {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      showToast('ph-share-network', 'הקישור למשרה הועתק ללוח בהצלחה!');
    } catch(e) {
      showToast('ph-link', 'לא ניתן להעתיק אוטומטית');
    }
  }

  function scrollToTop() {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  }

  function resetAllFilters() {
    const sec = document.getElementById('sectorFilter');
    const reg = document.getElementById('regionFilter');
    const inp = document.getElementById('searchInput');
    const wrap = document.getElementById('searchInputWrapper');

    if (sec) sec.value = 'all';
    if (reg) reg.value = 'all';
    if (inp) inp.value = '';
    if (wrap) wrap.classList.remove('has-value');

    filterCards();
    showToast('ph-arrow-counter-clockwise', 'המסננים וחיפוש המשרות אופסו בהצלחה');
  }

  function filterCards() {
    updateUI();
  }

  function updateUI() {
    const selectedSectorEl = document.getElementById('sectorFilter');
    const selectedSector = selectedSectorEl ? selectedSectorEl.value : 'all';
    const searchRaw = document.getElementById('searchInput') ? document.getElementById('searchInput').value.trim() : '';
    const searchInput = searchRaw.toLowerCase();
    const searchTerms = searchRaw.split(/\s+/).filter(t => t.length >= 2);
    
    const wrapper = document.getElementById('searchInputWrapper');
    if (wrapper) {
      wrapper.classList.toggle('has-value', Boolean(searchRaw.length > 0));
    }
    
    const cards = document.querySelectorAll('.job-card');
    const rawJobLinks = new Set((rawJobsData || []).map(j => j.link));
    let visibleCount = 0;
    let countNew = 0, countStarred = 0, countSaved = 0, countRejected = 0;

    cards.forEach(card => {
      const id = card.getAttribute('data-id');
      const state = getJobState(id);

      if (state === 'purged') {
        card.style.display = 'none';
        card.classList.add('is-hidden');
        return;
      }

      const saveBtn = card.querySelector('.action-save-btn');
      const rejectBtn = card.querySelector('.action-reject-btn');
      const saveText = saveBtn ? saveBtn.querySelector('.btn-text') : null;

      if (saveBtn && saveText) {
        if (state === 'saved') {
          saveBtn.className = "btn-triage action-save-btn saved-active";
          saveText.textContent = "נשמר להגשה";
          if (rejectBtn) rejectBtn.className = "btn-triage action-reject-btn";
        } else if (state === 'rejected') {
          if (rejectBtn) rejectBtn.className = "btn-triage action-reject-btn rejected-active";
          saveBtn.className = "btn-triage action-save-btn";
          saveText.textContent = "שמור להגשה";
        } else {
          saveBtn.className = "btn-triage action-save-btn";
          if (rejectBtn) rejectBtn.className = "btn-triage action-reject-btn";
          saveText.textContent = "שמור להגשה";
        }
      }

      const isStarred = isJobStarred(id);
      const isCurrentBatchJob = rawJobLinks.has(id);

      let matchesSector = (selectedSector === 'all');
      if (!matchesSector) {
        const classifiedSector = card.getAttribute('data-classified-sector');
        if (selectedSector === 'scada') {
          matchesSector = (classifiedSector === 'בקרה ו-SCADA');
        } else if (selectedSector === 'solar') {
          matchesSector = (classifiedSector === 'סולאר');
        } else if (selectedSector === 'natural_gas') {
          matchesSector = (classifiedSector === 'גז טבעי');
        } else if (selectedSector === 'drones') {
          matchesSector = (classifiedSector === 'רחפנים');
        } else if (selectedSector === 'energy_tech') {
          matchesSector = (classifiedSector === 'אגירה');
        } else if (selectedSector === 'operations') {
          matchesSector = (classifiedSector === 'תפעול ואחזקה');
        } else if (selectedSector === 'energy') {
          matchesSector = (classifiedSector === 'אנרגיה');
        } else {
          matchesSector = true;
        }
      }

      const selectedRegion = document.getElementById('regionFilter') ? document.getElementById('regionFilter').value : 'all';
      let matchesRegion = (selectedRegion === 'all');
      if (!matchesRegion) {
        const cardRegion = card.getAttribute('data-region') || 'center';
        matchesRegion = (cardRegion === selectedRegion);
      }

      let matchesSearch = true;
      if (searchInput) {
        const cardText = card.textContent.toLowerCase();
        matchesSearch = cardText.includes(searchInput);
      }

      const matchesActiveFilters = matchesSector && matchesRegion && matchesSearch;

      if (matchesActiveFilters) {
        if (isStarred && state !== 'rejected') {
          countStarred++;
        } else if (state === 'saved' && !isStarred) {
          countSaved++;
        } else if (state === 'rejected') {
          countRejected++;
        } else if (isCurrentBatchJob && !isStarred && state !== 'saved' && state !== 'rejected') {
          countNew++;
        }
      }

      let matchesTab = false;
      if (currentFilter === 'all') {
        matchesTab = isCurrentBatchJob && !isStarred && (state !== 'saved' && state !== 'rejected');
      } else if (currentFilter === 'starred') {
        matchesTab = (isStarred && state !== 'rejected');
      } else if (currentFilter === 'saved') {
        matchesTab = !isStarred && (state === 'saved' && state !== 'rejected');
      } else if (currentFilter === 'rejected') {
        matchesTab = (state === 'rejected');
      }

      if (matchesTab && matchesActiveFilters) {
        card.style.display = '';
        card.classList.remove('is-hidden');
        visibleCount++;

        // Apply highlighting to key visible text elements when search is active
        const titleEl = card.querySelector('.job-title-text');
        const compEl = card.querySelector('.job-company-name');
        const domainEl = card.querySelector('.job-bubble-domain .bubble-content');
        const reqsEl = card.querySelector('.job-bubble-reqs .bubble-content');

        if (titleEl) highlightSearchTerms(titleEl, searchTerms);
        if (compEl) highlightSearchTerms(compEl, searchTerms);
        if (domainEl) highlightSearchTerms(domainEl, searchTerms);
        if (reqsEl) highlightSearchTerms(reqsEl, searchTerms);
      } else {
        card.style.display = 'none';
        card.classList.add('is-hidden');
      }
    });

    let tabTotal = 0;
    let tabLabel = '';
    let tabNoun = '';
    if (currentFilter === 'saved') {
      tabTotal = countSaved;
      tabLabel = `סה״כ משרות שנשמרו: ${tabTotal}`;
      tabNoun = 'משרות שנשמרו';
    } else if (currentFilter === 'starred') {
      tabTotal = countStarred;
      tabLabel = `סה״כ משרות שסומנו בכוכב: ${tabTotal}`;
      tabNoun = 'משרות שסומנו בכוכב';
    } else if (currentFilter === 'rejected') {
      tabTotal = countRejected;
      tabLabel = `סה״כ משרות שהוסרו: ${tabTotal}`;
      tabNoun = 'משרות שהוסרו';
    } else {
      tabTotal = countNew;
      tabLabel = `סה״כ משרות חדשות: ${tabTotal}`;
      tabNoun = 'משרות חדשות';
    }

    const visibleJobsCountEl = document.getElementById('visibleJobsCountText');
    if (visibleJobsCountEl) {
      if (visibleCount === tabTotal) {
        visibleJobsCountEl.textContent = tabLabel;
      } else {
        visibleJobsCountEl.textContent = `מציג ${visibleCount} מתוך סה״כ ${tabTotal} ${tabNoun}`;
      }
    }

    // Update Filter Card Footer Result Summary
    const isFiltered = (selectedSector !== 'all' || (document.getElementById('regionFilter') && document.getElementById('regionFilter').value !== 'all') || searchRaw.length > 0);
    const filterStatusTextEl = document.getElementById('filterStatusText');
    if (filterStatusTextEl) {
      if (isFiltered) {
        filterStatusTextEl.textContent = `נמצאו ${visibleCount} משרות תואמות`;
      } else {
        filterStatusTextEl.textContent = `מוצגות כל ${visibleCount} המשרות הפעילות`;
      }
    }

    // Single Source of Truth: Update Counts simultaneously in Desktop and Mobile
    const statNewEl = document.getElementById('statNewCount');
    const statStarredEl = document.getElementById('statStarredCount');
    const statSavedEl = document.getElementById('statSavedCount');
    const statRejectedEl = document.getElementById('statRejectedCount');
    if (statNewEl) statNewEl.textContent = countNew;
    if (statStarredEl) statStarredEl.textContent = countStarred;
    if (statSavedEl) statSavedEl.textContent = countSaved;
    if (statRejectedEl) statRejectedEl.textContent = countRejected;

    const summaryNew = document.getElementById('summaryNewCount');
    const summaryStarred = document.getElementById('summaryStarredCount');
    const summarySaved = document.getElementById('summarySavedCount');
    const summaryRejected = document.getElementById('summaryRejectedCount');
    if (summaryNew) summaryNew.textContent = countNew;
    if (summaryStarred) summaryStarred.textContent = countStarred;
    if (summarySaved) summarySaved.textContent = countSaved;
    if (summaryRejected) summaryRejected.textContent = countRejected;

    const countAllEl = document.getElementById('countAll');
    const countSavedEl = document.getElementById('countSaved');
    const countRejectedEl = document.getElementById('countRejected');
    const countStarredNavEl = document.getElementById('countStarredNav');
    if (countAllEl) countAllEl.textContent = countNew;
    if (countSavedEl) countSavedEl.textContent = countSaved;
    if (countRejectedEl) countRejectedEl.textContent = countRejected;
    if (countStarredNavEl) countStarredNavEl.textContent = countStarred;

    // Ensure Active Cube Highlights Match currentFilter
    const activeCube = document.getElementById('cube_' + currentFilter);
    if (activeCube && !activeCube.classList.contains('active')) {
      document.querySelectorAll('.stat-cube-btn').forEach(b => {
        b.classList.remove('active');
        b.removeAttribute('aria-current');
      });
      activeCube.classList.add('active');
      activeCube.setAttribute('aria-current', 'page');
    }

    // Progress Bar Calculations based on Authoritative Counts
    const activeBatchCount = countNew + countStarred + countSaved + countRejected;
    const triaged = countStarred + countSaved + countRejected;
    const pct = activeBatchCount > 0 ? Math.round((triaged / activeBatchCount) * 100) : 0;
    
    const pctTextEl = document.getElementById('progressPctText');
    const summaryChipEl = document.getElementById('progressSummaryChip');
    if (pctTextEl) pctTextEl.textContent = pct + '%';
    if (summaryChipEl) summaryChipEl.textContent = pct + '% מוינו';

    const radialTextEl = document.getElementById('radialProgressText');
    const radialCircleEl = document.getElementById('radialProgressCircle');
    if (radialTextEl) radialTextEl.textContent = pct + '%';
    if (radialCircleEl) {
      const circ = 188.5;
      radialCircleEl.style.strokeDasharray = circ;
      radialCircleEl.style.strokeDashoffset = (circ * (1 - (pct / 100))).toFixed(1);
    }

    // Segmented progress bar widths
    const segNew = document.getElementById('progressSegNew');
    const segStarred = document.getElementById('progressSegStarred');
    const segSaved = document.getElementById('progressSegSaved');
    const segRej = document.getElementById('progressSegRejected');
    if (segNew && segStarred && segSaved && segRej) {
      const totalSeg = activeBatchCount || 1;
      const pNew = ((countNew / totalSeg) * 100).toFixed(1);
      const pStarred = ((countStarred / totalSeg) * 100).toFixed(1);
      const pSaved = ((countSaved / totalSeg) * 100).toFixed(1);
      const pRej = ((countRejected / totalSeg) * 100).toFixed(1);
      segNew.style.width = pNew + '%';
      segStarred.style.width = pStarred + '%';
      segSaved.style.width = pSaved + '%';
      segRej.style.width = pRej + '%';

      const lblNew = document.getElementById('pctLabelNew');
      const lblStarred = document.getElementById('pctLabelStarred');
      const lblSaved = document.getElementById('pctLabelSaved');
      const lblRej = document.getElementById('pctLabelRejected');
      if (lblNew) lblNew.textContent = pNew + '% חדשות';
      if (lblStarred) lblStarred.textContent = pStarred + '% כוכב';
      if (lblSaved) lblSaved.textContent = pSaved + '% שמורות';
      if (lblRej) lblRej.textContent = pRej + '% הוסרו';
    }

    // Contextual Action Bars
    const savedBar = document.getElementById('savedActionBar');
    const rejectedBar = document.getElementById('rejectedActionBar');
    if (savedBar) {
      savedBar.style.display = (currentFilter === 'saved') ? 'flex' : 'none';
    }
    if (rejectedBar) {
      rejectedBar.style.display = (currentFilter === 'rejected') ? 'flex' : 'none';
    }

    // Empty State Handling
    const emptyState = document.getElementById('emptyState');
    if (emptyState) {
      if (visibleCount === 0) {
        const iconEl = document.getElementById('emptyStateIcon');
        const titleEl = document.getElementById('emptyStateTitle');
        const descEl = document.getElementById('emptyStateDesc');
        if (isFiltered) {
          if (iconEl) iconEl.innerHTML = '<i class="ph-duotone ph-magnifying-glass"></i>';
          if (titleEl) titleEl.textContent = 'לא נמצאו משרות בהתאם לסינון';
          if (descEl) descEl.innerHTML = 'נסה לבחור אזור אחר, לשנות את מילת החיפוש או <button type="button" onclick="resetAllFilters()" style="background:none;border:none;color:var(--dashboard-cyan);cursor:pointer;text-decoration:underline;font:inherit;padding:0;">לאפס את כל המסננים</button>.';
        } else if (currentFilter === 'rejected') {
          if (iconEl) iconEl.innerHTML = '<i class="ph-duotone ph-trash"></i>';
          if (titleEl) titleEl.textContent = totalRejectedInStore > 0 ? `כל ${totalRejectedInStore} המשרות שהוסרו מנוטרלות לצמיתות` : 'אין כרגע משרות שהוסרו מהסבב';
          if (descEl) descEl.textContent = totalRejectedInStore > 0 ? 'משרות אלו סוננו מחלון ההזדמנויות השבועי ולא ישובו להופיע בדוחות הבאים.' : 'כאשר תסיר משרה מהסבב, היא תופיע כאן.';
        } else if (currentFilter === 'saved') {
          if (iconEl) iconEl.innerHTML = '<i class="ph-duotone ph-bookmark-simple"></i>';
          if (titleEl) titleEl.textContent = 'עדיין לא סימנת משרות שמורות מתוך מקבץ זה';
          if (descEl) descEl.textContent = 'לחץ על "שמור להגשה" בכל כרטיס משרה שמעניינת אותך.';
        } else if (currentFilter === 'starred') {
          if (iconEl) iconEl.innerHTML = '<i class="ph-fill ph-star" style="color: var(--dashboard-gold);"></i>';
          if (titleEl) titleEl.textContent = 'עדיין לא סימנת משרות בכוכב';
          if (descEl) descEl.textContent = 'לחץ על סמל הכוכב בפינת כל כרטיס משרה כדי להעביר אותה לכאן.';
        } else {
          if (iconEl) iconEl.innerHTML = '<i class="ph-duotone ph-sparkle"></i>';
          if (titleEl) titleEl.textContent = 'סיימת לסקור את כל המשרות החדשות!';
          if (descEl) descEl.textContent = 'כל המשרות במקבץ זה כבר מוינו (נשמרו, סומנו בכוכב או הוסרו).';
        }
        emptyState.style.display = 'block';
      } else {
        emptyState.style.display = 'none';
      }
    }

    renderSectorChart();

    if (liveJobsMapInstance || currentViewMode === 'map') {
      updateMapMarkers();
    }
  }

  let sectorChartInstance = null;
  function renderSectorChart() {
    try {
      const canvas = document.getElementById('sectorChart');
      if (!canvas || typeof Chart === 'undefined') return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const allAvailableJobs = getAllAvailableJobs();
      const rawJobLinks = new Set((rawJobsData || []).map(j => j.link));

      let sourceJobs = [];
      const chartTitleEl = document.getElementById('chartTitle');
      const chartChipEl = document.getElementById('chartChip');

      if (currentFilter === 'saved') {
        sourceJobs = allAvailableJobs.filter(j => jobStates[j.link] === 'saved' && jobStates[j.link] !== 'rejected' && jobStates[j.link] !== 'purged');
        if (chartTitleEl) chartTitleEl.textContent = 'התפלגות משרות שמורות';
        if (chartChipEl) {
          chartChipEl.innerHTML = `<i class="ph-duotone ph-bookmark-simple"></i> ${sourceJobs.length} שמורות`;
          chartChipEl.style.color = 'var(--dashboard-lime)';
          chartChipEl.style.borderColor = 'rgba(52, 211, 153, 0.4)';
        }
      } else if (currentFilter === 'starred') {
        sourceJobs = allAvailableJobs.filter(j => Boolean(starredJobs[j.link]) && jobStates[j.link] !== 'rejected' && jobStates[j.link] !== 'purged');
        if (chartTitleEl) chartTitleEl.textContent = 'התפלגות משרות בכוכב';
        if (chartChipEl) {
          chartChipEl.innerHTML = `<i class="ph-fill ph-star"></i> ${sourceJobs.length} בכוכב`;
          chartChipEl.style.color = 'var(--dashboard-gold)';
          chartChipEl.style.borderColor = 'rgba(255, 211, 104, 0.4)';
        }
      } else if (currentFilter === 'rejected') {
        sourceJobs = allAvailableJobs.filter(j => jobStates[j.link] === 'rejected');
        if (chartTitleEl) chartTitleEl.textContent = 'התפלגות משרות שהוסרו';
        if (chartChipEl) {
          chartChipEl.innerHTML = `<i class="ph-duotone ph-trash"></i> ${sourceJobs.length} הוסרו`;
          chartChipEl.style.color = '#fca5a5';
          chartChipEl.style.borderColor = 'rgba(252, 165, 165, 0.4)';
        }
      } else {
        // Default / All: active jobs from current scan
        sourceJobs = (allAvailableJobs || []).filter(j => {
          const st = jobStates[j.link] || 'pending';
          const isSt = Boolean(starredJobs[j.link]);
          return rawJobLinks.has(j.link) && !isSt && st !== 'saved' && st !== 'rejected' && st !== 'purged';
        });
        if (chartTitleEl) chartTitleEl.textContent = 'התפלגות משרות חדשות';
        if (chartChipEl) {
          if (sourceJobs.length === 0) {
            chartChipEl.innerHTML = '<i class="ph-duotone ph-chart-bar"></i> 0 משרות';
          } else {
            chartChipEl.innerHTML = `<i class="ph-duotone ph-chart-bar"></i> חדשות (${sourceJobs.length})`;
          }
          chartChipEl.style.color = 'var(--dashboard-cyan)';
          chartChipEl.style.borderColor = 'rgba(137, 244, 231, 0.35)';
        }
      }

      const counts = {};
      sourceJobs.forEach(job => {
        const label = classifyJobSector(job);
        counts[label] = (counts[label] || 0) + 1;
      });

      if (Object.keys(counts).length === 0) {
        ['סולאר', 'רחפנים', 'תפעול ואחזקה', 'בקרה ו-SCADA', 'גז טבעי', 'אגירה'].forEach(s => {
          counts[s] = 0;
        });
      }

      if (sectorChartInstance) {
        sectorChartInstance.destroy();
        sectorChartInstance = null;
      }

      const labels = Object.keys(counts);
      const data = Object.values(counts);

      const colorMap = {
        'סולאר': '#ffd368',
        'בקרה ו-SCADA': '#89f4e7',
        'רחפנים': '#34d399',
        'תפעול ואחזקה': '#b4fcf1',
        'אגירה': '#a0c03e',
        'גז טבעי': '#fca5a5',
        'אנרגיה': '#38bdf8',
        'אין משרות להצגה': '#c0c5be'
      };

      const barColors = labels.map(l => colorMap[l] || '#89f4e7');

      sectorChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            data: data,
            backgroundColor: barColors,
            borderRadius: 8,
            borderSkipped: false,
            maxBarThickness: 32
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: {
            duration: 350
          },
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: '#191d1b',
              titleColor: '#f5f6f0',
              bodyColor: '#c0c5be',
              borderColor: 'rgba(255, 255, 255, 0.16)',
              borderWidth: 1,
              cornerRadius: 12,
              rtl: true,
              textDirection: 'rtl',
              callbacks: {
                label: function(ctx) {
                  return ` ${ctx.raw} משרות`;
                }
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              suggestedMax: 5,
              ticks: { stepSize: 1, color: '#c0c5be', font: { family: 'Google Sans', size: 11 } },
              grid: { color: 'rgba(255, 255, 255, 0.08)' }
            },
            x: {
              ticks: { color: '#c0c5be', font: { family: 'Google Sans', size: 10 } },
              grid: { display: false }
            }
          }
        }
      });
    } catch(e) {
      console.warn('renderSectorChart error:', e);
    }
  }

  let toastHideTimer = null;
  let toastPopoverTimer = null;
  function showToast(icon, msg) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    const iconEl = document.getElementById('toastIcon');
    if (iconEl) {
      if (typeof icon === 'string' && icon.startsWith('ph-')) {
        iconEl.innerHTML = `<i class="ph-duotone ${icon}"></i>`;
      } else {
        iconEl.innerHTML = icon;
      }
    }
    document.getElementById('toastMsg').textContent = msg;
    clearTimeout(toastHideTimer);
    clearTimeout(toastPopoverTimer);
    // Popover keeps the toast in the top layer so it stays visible above open dialogs
    if (typeof toast.showPopover === 'function' && !toast.matches(':popover-open')) {
      try { toast.showPopover(); } catch (e) { /* already open */ }
    }
    void toast.offsetWidth;
    toast.classList.add('show');
    toastHideTimer = setTimeout(() => {
      toast.classList.remove('show');
      toastPopoverTimer = setTimeout(() => {
        if (typeof toast.hidePopover === 'function' && toast.matches(':popover-open')) {
          try { toast.hidePopover(); } catch (e) { /* already closed */ }
        }
      }, 400);
    }, 2800);
  }

  function triggerSyncModal() {
    const savedCount = Object.keys(jobStates).filter(id => jobStates[id] === 'saved' && !isJobStarred(id)).length;
    const starredCount = Object.keys(starredJobs).filter(id => Boolean(starredJobs[id]) && (jobStates[id] || 'pending') !== 'rejected' && (jobStates[id] || 'pending') !== 'purged').length;
    const rejectedCount = Object.values(jobStates).filter(s => s === 'rejected').length;
    const starredEl = document.getElementById('syncStarredCount');
    if (starredEl) starredEl.textContent = starredCount;
    const savedEl = document.getElementById('syncSavedCount');
    if (savedEl) savedEl.textContent = savedCount;
    const rejEl = document.getElementById('syncRejectedCount');
    if (rejEl) rejEl.textContent = rejectedCount;
    openDialogEl(document.getElementById('syncModal'));
  }

  function closeSyncModal() {
    closeDialogEl(document.getElementById('syncModal'));
  }

  const GH_WORKFLOW_URL = 'https://api.github.com/repos/idogal0210-web/job_search_automation/actions/workflows/daily_job_search.yml';
  let cloudSearchPollTimer = null;
  let isCloudSearchActive = false;

  function triggerRunSearchModal() {
    updateRunSearchTokenUI();
    fetchLatestCloudRunStatus();
    openDialogEl(document.getElementById('runSearchModal'));
  }

  function closeRunSearchModal() {
    closeDialogEl(document.getElementById('runSearchModal'));
  }

  function getStoredGitHubToken() {
    try {
      return (localStorage.getItem('gh_dispatch_token') || '').trim();
    } catch (e) {
      return '';
    }
  }

  function updateRunSearchTokenUI() {
    const token = getStoredGitHubToken();
    const displayEl = document.getElementById('runSearchTokenDisplay');
    const inputWrapper = document.getElementById('runSearchTokenInputWrapper');
    const maskedEl = document.getElementById('runSearchTokenMasked');
    const inputEl = document.getElementById('runSearchPatInput');

    if (token) {
      if (displayEl) displayEl.style.display = 'flex';
      if (inputWrapper) inputWrapper.style.display = 'none';
      if (maskedEl) {
        const preview = token.length > 8 ? token.slice(0, 4) + '...' + token.slice(-4) : '••••••••';
        maskedEl.textContent = preview;
      }
    } else {
      if (displayEl) displayEl.style.display = 'none';
      if (inputWrapper) inputWrapper.style.display = 'flex';
      if (inputEl) inputEl.value = '';
    }
  }

  function editRunSearchToken() {
    const displayEl = document.getElementById('runSearchTokenDisplay');
    const inputWrapper = document.getElementById('runSearchTokenInputWrapper');
    const inputEl = document.getElementById('runSearchPatInput');
    if (displayEl) displayEl.style.display = 'none';
    if (inputWrapper) inputWrapper.style.display = 'flex';
    if (inputEl) {
      inputEl.value = getStoredGitHubToken();
      inputEl.focus();
    }
  }

  function saveRunSearchToken() {
    const inputEl = document.getElementById('runSearchPatInput');
    const val = inputEl ? inputEl.value.trim() : '';
    if (!val) {
      if (typeof showToast === 'function') showToast('נא להזין טוקן תקף');
      return;
    }
    try {
      localStorage.setItem('gh_dispatch_token', val);
      updateRunSearchTokenUI();
      if (typeof showToast === 'function') showToast('טוקן GitHub נשמר בהצלחה בדפדפן');
    } catch (e) {
      if (typeof showToast === 'function') showToast('שגיאה בשמירת הטוקן');
    }
  }

  function setCloudSearchRunningUI(isRunning) {
    isCloudSearchActive = isRunning;
    const btn = document.getElementById('headerRunSearchBtn');
    const icon = document.getElementById('headerRunSearchIcon');
    const dot = document.getElementById('headerRunSearchDot');
    const banner = document.getElementById('runSearchProgressBanner');
    const submitBtn = document.getElementById('runSearchSubmitBtn');

    if (btn) {
      if (isRunning) {
        btn.classList.add('is-running');
        btn.setAttribute('title', 'סריקת משרות פעילה כעת בענן');
      } else {
        btn.classList.remove('is-running');
        btn.setAttribute('title', 'הפעלת סריקת משרות בענן');
      }
    }
    if (icon) {
      icon.className = isRunning ? 'ph-duotone ph-spinner ph-spin' : 'ph-duotone ph-play';
    }
    if (dot) {
      dot.style.display = isRunning ? 'inline-block' : 'none';
    }
    if (banner) {
      banner.style.display = isRunning ? 'block' : 'none';
    }
    if (submitBtn) {
      submitBtn.disabled = isRunning;
      submitBtn.style.opacity = isRunning ? '0.6' : '1';
      submitBtn.style.pointerEvents = isRunning ? 'none' : 'auto';
      const textSpan = submitBtn.querySelector('span');
      if (textSpan) textSpan.textContent = isRunning ? 'סריקה פעילה בענן...' : 'הפעל סריקה כעת';
    }
  }

  async function fetchLatestCloudRunStatus() {
    const timeEl = document.getElementById('runSearchLastRunTime');
    const statusEl = document.getElementById('runSearchLastRunStatus');
    try {
      const headers = { 'Accept': 'application/vnd.github+json' };
      const token = getStoredGitHubToken();
      if (token) headers['Authorization'] = 'Bearer ' + token;
      const res = await fetch(GH_WORKFLOW_URL + '/runs?per_page=1', { headers });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      if (data && data.workflow_runs && data.workflow_runs.length > 0) {
        const run = data.workflow_runs[0];
        const dateObj = new Date(run.created_at);
        const timeFormatted = dateObj.toLocaleDateString('he-IL', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
        if (timeEl) timeEl.textContent = timeFormatted;

        if (run.status === 'in_progress' || run.status === 'queued') {
          if (statusEl) {
            statusEl.textContent = 'פעיל כעת';
            statusEl.className = 'dashboard-chip cyan';
          }
          setCloudSearchRunningUI(true);
          startCloudSearchPolling();
        } else if (run.status === 'completed') {
          if (run.conclusion === 'success') {
            if (statusEl) {
              statusEl.textContent = 'הצלחה';
              statusEl.className = 'dashboard-chip lime';
            }
          } else {
            if (statusEl) {
              statusEl.textContent = run.conclusion === 'failure' ? 'נכשלה' : (run.conclusion || 'הושלם');
              statusEl.className = 'dashboard-chip rose';
            }
          }
          if (isCloudSearchActive) {
            setCloudSearchRunningUI(false);
          }
        }
      }
    } catch (e) {
      if (timeEl) timeEl.textContent = 'לא זמין';
      if (statusEl) {
        statusEl.textContent = 'מצב לא ידוע';
        statusEl.className = 'dashboard-chip';
      }
    }
  }

  function startCloudSearchPolling() {
    if (cloudSearchPollTimer) clearInterval(cloudSearchPollTimer);
    cloudSearchPollTimer = setInterval(async () => {
      try {
        const headers = { 'Accept': 'application/vnd.github+json' };
        const token = getStoredGitHubToken();
        if (token) headers['Authorization'] = 'Bearer ' + token;
        const res = await fetch(GH_WORKFLOW_URL + '/runs?per_page=1', { headers });
        if (!res.ok) return;
        const data = await res.json();
        if (data && data.workflow_runs && data.workflow_runs.length > 0) {
          const run = data.workflow_runs[0];
          if (run.status === 'completed') {
            clearInterval(cloudSearchPollTimer);
            cloudSearchPollTimer = null;
            setCloudSearchRunningUI(false);
            fetchLatestCloudRunStatus();
            if (run.conclusion === 'success') {
              if (typeof showToast === 'function') showToast('סריקת המשרות בענן הסתיימה בהצלחה!');
              setTimeout(() => {
                window.location.reload();
              }, 2500);
            } else {
              if (typeof showToast === 'function') showToast('ריצת הסריקה בענן הסתיימה בסטטוס: ' + (run.conclusion || 'הושלם'));
            }
          }
        }
      } catch (e) {
        /* Ignore poll network errors */
      }
    }, 12000);
  }

  async function dispatchCloudJobSearch() {
    const token = getStoredGitHubToken();
    if (!token) {
      editRunSearchToken();
      if (typeof showToast === 'function') showToast('נא להגדיר טוקן GitHub להפעלת סריקה');
      return;
    }

    const submitBtn = document.getElementById('runSearchSubmitBtn');
    if (submitBtn) {
      submitBtn.disabled = true;
      const textSpan = submitBtn.querySelector('span');
      if (textSpan) textSpan.textContent = 'שולח פקודה לענן...';
    }

    try {
      const res = await fetch(GH_WORKFLOW_URL + '/dispatches', {
        method: 'POST',
        headers: {
          'Accept': 'application/vnd.github+json',
          'Authorization': 'Bearer ' + token,
          'X-GitHub-Api-Version': '2022-11-28',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ref: 'main' })
      });

      if (res.status === 204) {
        setCloudSearchRunningUI(true);
        if (typeof showToast === 'function') showToast('סריקת המשרות הופעלה בהצלחה ב-GitHub Actions!');
        setTimeout(() => {
          fetchLatestCloudRunStatus();
          startCloudSearchPolling();
        }, 3000);
      } else if (res.status === 401 || res.status === 403) {
        if (typeof showToast === 'function') showToast('שגיאת הרשאה מול GitHub. ודא שהטוקן כולל הרשאת workflow');
        editRunSearchToken();
        setCloudSearchRunningUI(false);
      } else {
        if (typeof showToast === 'function') showToast('שגיאה בשיגור הסריקה: HTTP ' + res.status);
        setCloudSearchRunningUI(false);
      }
    } catch (err) {
      if (typeof showToast === 'function') showToast('שגיאת רשת בחיבור ל-GitHub: ' + (err.message || ''));
      setCloudSearchRunningUI(false);
    }
  }

  function toggleMetricsExpand() {
    const content = document.getElementById('collapsibleMetricsContent');
    const btn = document.getElementById('metricsToggleBtn');
    const label = document.getElementById('metricsToggleText');
    const icon = document.getElementById('metricsToggleIcon');
    if (!content) return;
    const isExpanded = content.classList.toggle('is-expanded');
    if (btn) btn.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
    if (label) label.textContent = isExpanded ? 'צמצם' : 'פירוט';
    if (icon) {
      icon.className = isExpanded ? 'ph-bold ph-caret-up' : 'ph-bold ph-caret-down';
    }
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeRunSearchModal();
        closeSyncModal();
        closeDuplicatesModal();
        closeInactiveJobsModal();
        if (typeof closeJobModal === 'function') closeJobModal();
      }
    });
  }

  async function pullLatestFromCloud() {
    const pullBtn = document.getElementById('syncPullRemoteBtn');
    if (pullBtn) {
      pullBtn.disabled = true;
      pullBtn.innerHTML = '<i class="ph-bold ph-spinner ph-spin"></i> מושך נתונים מהענן...';
    }

    try {
      localStorage.removeItem(LAST_LOCAL_EDIT_KEY);
      await fetchCloudSync(true);
      await loadHistoricalCatalogOnDemand();
      renderCards();
      updateUI();
      const savedCount = Object.keys(jobStates).filter(id => jobStates[id] === 'saved' && !isJobStarred(id)).length;
      const starredCount = Object.keys(starredJobs).filter(id => Boolean(starredJobs[id]) && (jobStates[id] || 'pending') !== 'rejected' && (jobStates[id] || 'pending') !== 'purged').length;
      const newCount = (rawJobsData || []).filter(j => !isJobStarred(j.link) && (jobStates[j.link] || 'pending') !== 'saved' && (jobStates[j.link] || 'pending') !== 'rejected' && (jobStates[j.link] || 'pending') !== 'purged').length;
      closeSyncModal();
      showToast('ph-cloud-arrow-down', `נתוני הענן נמשכו בהצלחה! (${savedCount} שמורות, ${starredCount} בכוכב, ${newCount} חדשות)`);
    } catch (e) {
      showToast('ph-warning', 'שגיאה במשיכת נתונים מהענן');
    } finally {
      if (pullBtn) {
        pullBtn.disabled = false;
        pullBtn.innerHTML = '<i class="ph-duotone ph-cloud-arrow-down"></i> משוך ושחזר נתונים מהענן לטלפון / מחשב';
      }
    }
  }

  async function confirmSync() {
    const syncBtn = document.getElementById('syncConfirmBtn');
    if (syncBtn) {
      syncBtn.disabled = true;
      syncBtn.textContent = "סנכרון מתבצע...";
    }

    try {
      // 1. Force push existing local triage/starred state into cloud/backend state
      await pushCloudSync();
      // 2. Clear any stale edit flags and reconcile safely
      localStorage.removeItem(LAST_LOCAL_EDIT_KEY);
      await fetchCloudSync(false);
    } catch(e) {}

    const savedCount = Object.keys(jobStates).filter(id => jobStates[id] === 'saved' && !isJobStarred(id)).length;
    const starredCount = Object.keys(starredJobs).filter(id => Boolean(starredJobs[id]) && (jobStates[id] || 'pending') !== 'rejected' && (jobStates[id] || 'pending') !== 'purged').length;
    const rejectedCount = Object.keys(jobStates).filter(id => jobStates[id] === 'rejected').length;
    const newCount = (rawJobsData || []).filter(j => !isJobStarred(j.link) && (jobStates[j.link] || 'pending') !== 'saved' && (jobStates[j.link] || 'pending') !== 'rejected' && (jobStates[j.link] || 'pending') !== 'purged').length;

    closeSyncModal();
    showToast('ph-cloud-check', `סונכרן בהצלחה מול המחשב! (${newCount} חדשות, ${starredCount} בכוכב, ${savedCount} שמורות, ${rejectedCount} הוסרו)`);
    if (syncBtn) {
      syncBtn.disabled = false;
      syncBtn.textContent = "אשר וסנכרן עכשיו";
    }
  }

  function openDuplicatesModal() {
    const modal = document.getElementById('duplicatesModal');
    openDialogEl(modal);
    const content = document.getElementById('duplicatesContent');
    if (!content) return;

    // 1. נרמול טקסט והסרת מילות רעש
    function cleanText(str) {
      if (!str) return '';
      return str.toLowerCase()
        .replace(/[^א-תa-z0-9]/g, ' ')
        .replace(/\b(דרוש|דרושה|דרושים|בכיר|גוניור|junior|senior|remote|hybrid|israel|ישראל|מרכז|צפון|דרום|תל אביב|חיפה|פתח תקווה|משרה מלאה|היברידי)\b/gi, '')
        .replace(/\s+/g, ' ')
        .trim();
    }

    // 2. חישוב דמיון (Levenshtein Distance מנורמל ל-0 עד 100%)
    function getSimilarity(s1, s2) {
      if (s1 === s2) return 100;
      if (!s1 || !s2) return 0;

      const l1 = s1.length;
      const l2 = s2.length;
      const track = Array(l2 + 1).fill(null).map(() => Array(l1 + 1).fill(null));
      for (let i = 0; i <= l1; i += 1) track[0][i] = i;
      for (let j = 0; j <= l2; j += 1) track[j][0] = j;

      for (let j = 1; j <= l2; j += 1) {
        for (let i = 1; i <= l1; i += 1) {
          const indicator = s1[i - 1] === s2[j - 1] ? 0 : 1;
          track[j][i] = Math.min(
            track[j][i - 1] + 1,
            track[j - 1][i] + 1,
            track[j - 1][i - 1] + indicator
          );
        }
      }
      const dist = track[l2][l1];
      return Math.round((1 - dist / Math.max(l1, l2)) * 100);
    }

    // 3. חילוץ מזהה ייחודי מהקישור
    function extractJobId(link) {
      if (!link) return null;
      try {
        const cleanUrl = link.split('?')[0].split('#')[0];
        const drushimMatch = cleanUrl.match(/\/job\/(\d+)/i);
        if (drushimMatch) return 'drushim-' + drushimMatch[1];
        const comeetMatch = cleanUrl.match(/([a-zA-Z0-9]+-[a-zA-Z0-9]+)\/?$/);
        if (comeetMatch && cleanUrl.includes('comeet')) return 'comeet-' + comeetMatch[1];
        const numMatch = cleanUrl.match(/\/(\d{6,12})(?:\/|$)/);
        if (numMatch) return 'id-' + numMatch[1];
      } catch (e) {}
      return null;
    }

    const allJobs = getAllAvailableJobs();
    const activeJobs = allJobs.filter(job => {
      const state = jobStates[job.link] || 'pending';
      const isStarred = Boolean(starredJobs[job.link]);
      if (state === 'rejected' || state === 'purged') return false;
      return isStarred || state === 'saved' || state === 'pending';
    });

    // 4. אשכול משרות לקבוצות חשודות
    const groups = [];

    activeJobs.forEach((job, idx) => {
      const jobCleanTitle = cleanText(job.title);
      const jobCleanCompany = cleanText(job.company);
      const jobId = extractJobId(job.link);
      const jobItem = { ...job, _idx: idx, _cleanTitle: jobCleanTitle, _cleanCompany: jobCleanCompany, _id: jobId };

      let matchedGroup = null;

      for (const group of groups) {
        const leader = group.leader;

        // בדיקת זהות מזהה קישור
        if (jobId && leader._id && jobId === leader._id) {
          matchedGroup = group;
          matchedGroup.matchReason = 'מזהה משרה זהה בקישור';
          matchedGroup.matchScore = 100;
          break;
        }

        // בדיקת דמיון כותרת וחברה
        const titleSim = getSimilarity(jobCleanTitle, leader._cleanTitle);
        const compSim = (jobCleanCompany && leader._cleanCompany)
          ? getSimilarity(jobCleanCompany, leader._cleanCompany)
          : 0;

        // תנאי א: חברה זהה/קרובה (מעל 80%) וכותרת דומה (מעל 70%)
        if (compSim >= 80 && titleSim >= 70) {
          matchedGroup = group;
          matchedGroup.matchReason = `חברה זהה + כותרת דומה (${titleSim}%)`;
          matchedGroup.matchScore = Math.round((titleSim * 0.7) + (compSim * 0.3));
          break;
        }

        // תנאי ב: כותרת כמעט זהה לחלוטין (מעל 88%) גם ללא זיהוי חברה
        if (titleSim >= 88 && jobCleanTitle.length > 7) {
          matchedGroup = group;
          matchedGroup.matchReason = `כותרת כמעט זהה (${titleSim}%)`;
          matchedGroup.matchScore = titleSim;
          break;
        }
      }

      if (matchedGroup) {
        matchedGroup.items.push(jobItem);
      } else {
        groups.push({
          leader: jobItem,
          items: [jobItem],
          matchReason: '',
          matchScore: 0
        });
      }
    });

    // סינון רק לקבוצות שבהן נמצאו 2 משרות ומעלה
    const dupGroups = groups.filter(g => g.items.length > 1);

    // 5. רינדור המודל עם אפשרות בחירה ופעולה בעיצוב כהה תואם
    if (dupGroups.length === 0) {
      content.innerHTML = `
        <div style="padding: 32px 16px; text-align: center; color: var(--dashboard-muted); font-size: 15px;">
          <div style="font-size: 38px; color: var(--dashboard-lime); margin-bottom: 10px;"><i class="ph-duotone ph-check-circle"></i></div>
          <div style="color: #fff; font-weight: 700; font-size: 16px; margin-bottom: 4px;">לא אותרו כפילויות!</div>
          <div>כל ${activeJobs.length} המשרות הפעילות (חדשות, שמורות ובכוכב) ייחודיות לחלוטין.</div>
        </div>
      `;
      openDialogEl(document.getElementById('duplicatesModal'));
      return;
    }

    const totalDups = dupGroups.reduce((sum, g) => sum + g.items.length - 1, 0);

    let html = `
      <div style="display: flex; flex-direction: column; gap: 14px; direction: rtl; text-align: right;">
        <div style="padding: 10px 14px; background: rgba(255, 211, 104, 0.12); border: 1px solid rgba(255, 211, 104, 0.35); border-radius: 12px; font-size: 13px; color: var(--dashboard-gold); display: flex; align-items: center; gap: 8px;">
          <i class="ph-duotone ph-warning" style="font-size: 18px;"></i>
          <span>אותרו <strong>${dupGroups.length}</strong> קבוצות חשודות עם <strong>${totalDups}</strong> כפילויות. באפשרותך לאחד מקורות, להסיר כפילויות או להתעלם.</span>
        </div>
    `;

    dupGroups.forEach((group, gIdx) => {
      const primary = group.items[0];
      const duplicates = group.items.slice(1);
      const safeComp = escapeHtml(primary.company || '—');
      const safeTitle = escapeHtml(primary.title || '—');

      html += `
        <div id="dup-card-${gIdx}" style="border: 1px solid var(--dashboard-edge); border-radius: 14px; padding: 14px; background: rgba(22, 27, 34, 0.85); box-shadow: 0 4px 14px rgba(0,0,0,0.25); display: flex; flex-direction: column; gap: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 10px; gap: 8px; flex-wrap: wrap;">
            <span class="dashboard-chip" style="font-size: 12px; color: var(--dashboard-cyan); border-color: rgba(137, 244, 231, 0.4); padding: 3px 10px; font-weight: 700;">
              <i class="ph-duotone ph-sparkle"></i> ${group.matchReason} (${group.matchScore}%)
            </span>
            <div style="display: flex; gap: 8px;">
              <button onclick="handleMergeDuplicates(${gIdx})" class="btn-triage" style="background: rgba(14, 165, 233, 0.22); color: #38bdf8; border-color: rgba(14, 165, 233, 0.45); padding: 5px 12px; font-size: 12px; font-weight: 600; cursor: pointer;" title="שמור ראשית ומזג קישורים">
                <i class="ph-duotone ph-link"></i> <span>אחד (שמור ומזג קישורים)</span>
              </button>
              <button onclick="handleRemoveDuplicates(${gIdx})" class="btn-triage action-reject-btn" style="background: rgba(239, 68, 68, 0.22); color: #fca5a5; border-color: rgba(239, 68, 68, 0.45); padding: 5px 12px; font-size: 12px; font-weight: 600; cursor: pointer;" title="הסר כפולות">
                <i class="ph-duotone ph-trash-simple"></i> <span>הסר כפולות</span>
              </button>
              <button onclick="handleIgnoreGroup(${gIdx})" class="btn-triage" style="padding: 5px 10px; font-size: 12px; color: var(--dashboard-muted); border-color: rgba(255, 255, 255, 0.15); cursor: pointer;">
                <span>התעלם</span>
              </button>
            </div>
          </div>

          <!-- משרה עיקרית -->
          <div style="padding: 10px 12px; background: rgba(14, 165, 233, 0.08); border-radius: 8px; border-right: 3px solid var(--dashboard-cyan);">
            <div style="font-size: 11px; color: var(--dashboard-cyan); font-weight: 700; margin-bottom: 2px;">משרה מקורית מובילה:</div>
            <div style="font-weight: 700; font-size: 14px; color: #fff;">${safeTitle}</div>
            <div style="font-size: 12px; color: var(--dashboard-muted); margin-top: 4px; display: flex; align-items: center; gap: 8px;">
              <span>${safeComp}</span>
              <span>|</span>
              <a href="${sanitizeUrl(primary.link)}" target="_blank" rel="noopener noreferrer" style="color: var(--dashboard-cyan); text-decoration: underline; text-underline-offset: 3px; display: inline-flex; align-items: center; gap: 4px;">
                פתח קישור <i class="ph-duotone ph-arrow-up-right"></i>
              </a>
            </div>
          </div>

          <!-- משרות כפולות -->
          <div style="padding-right: 6px;">
            <div style="font-size: 11px; color: #fca5a5; font-weight: 700; margin-bottom: 6px;">כפילויות שנמצאו (${duplicates.length}):</div>
            ${duplicates.map(dup => `
              <div style="padding: 8px 10px; border-top: 1px dashed rgba(255, 255, 255, 0.08); font-size: 13px; color: #cbd5e1; display: flex; justify-content: space-between; align-items: center; gap: 8px;">
                <div>
                  <span style="font-weight: 600; color: #fff;">${escapeHtml(dup.title || 'ללא כותרת')}</span>
                  <span style="color: var(--dashboard-muted);"> - ${escapeHtml(dup.company || 'ללא חברה')}</span>
                </div>
                <a href="${sanitizeUrl(dup.link)}" target="_blank" rel="noopener noreferrer" style="color: var(--dashboard-cyan); font-size: 12px; text-decoration: underline; text-underline-offset: 3px; white-space: nowrap; display: inline-flex; align-items: center; gap: 3px;">
                  פתח <i class="ph-duotone ph-arrow-up-right"></i>
                </a>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    });

    html += `</div>`;
    content.innerHTML = html;

    // שמירת הקבוצות בזיכרון הגלובלי לצורך פעולות הכפתורים
    window.__activeDuplicateGroups = dupGroups;
    openDialogEl(document.getElementById('duplicatesModal'));
  }

  // 1. פעולת איחוד: שומרת את הראשית, מעתיקה אליה הערות/קישורים של הכפולות ומנטרלת את הכפילויות
  function handleMergeDuplicates(groupIndex) {
    if (!window.__activeDuplicateGroups) return;
    const group = window.__activeDuplicateGroups[groupIndex];
    if (!group) return;

    const primary = group.items[0];
    const duplicates = group.items.slice(1);

    if (!Array.isArray(altLinksStore[primary.link])) {
      altLinksStore[primary.link] = [];
    }

    duplicates.forEach(dup => {
      if (dup.link && !altLinksStore[primary.link].includes(dup.link)) {
        altLinksStore[primary.link].push(dup.link);
      }
      jobStates[dup.link] = 'purged';
      delete starredJobs[dup.link];
    });

    saveStarredJobs(starredJobs);
    saveAltLinksState(altLinksStore);
    saveTriageState(jobStates);
    updateCubeCountsImmediately();
    renderCards();
    updateUI();
    scheduleCloudPush();

    const card = document.getElementById(`dup-card-${groupIndex}`);
    if (card) {
      card.style.background = 'rgba(34, 197, 94, 0.15)';
      card.style.borderColor = 'rgba(34, 197, 94, 0.4)';
      card.innerHTML = `<div style="color: var(--dashboard-lime); font-size: 13px; font-weight: 600; padding: 8px 12px;"><i class="ph-duotone ph-check-circle"></i> המשרות מוזגו בהצלחה למשרה הראשית! הקישורים הנוספים נשמרו.</div>`;
      setTimeout(() => {
        card.remove();
        checkRemainingDuplicateCards();
      }, 1200);
    }
  }

  // 2. פעולת הסרה: העברת כל המשרות הכפולות (חוץ מהראשונה) לסטטוס 'purged' (מנוטרל לצמיתות)
  function handleRemoveDuplicates(groupIndex) {
    if (!window.__activeDuplicateGroups) return;
    const group = window.__activeDuplicateGroups[groupIndex];
    if (!group) return;

    const duplicates = group.items.slice(1);
    duplicates.forEach(dup => {
      jobStates[dup.link] = 'purged';
      delete starredJobs[dup.link];
    });

    saveStarredJobs(starredJobs);
    saveTriageState(jobStates);
    updateCubeCountsImmediately();
    renderCards();
    updateUI();
    scheduleCloudPush();

    const card = document.getElementById(`dup-card-${groupIndex}`);
    if (card) {
      card.style.background = 'rgba(239, 68, 68, 0.15)';
      card.style.borderColor = 'rgba(239, 68, 68, 0.4)';
      card.innerHTML = `<div style="color: #fca5a5; font-size: 13px; font-weight: 600; padding: 8px 12px;"><i class="ph-duotone ph-trash-simple"></i> ${duplicates.length} כפילויות הוסרו מלוח המשרות.</div>`;
      setTimeout(() => {
        card.remove();
        checkRemainingDuplicateCards();
      }, 1200);
    }
  }

  // 3. התעלמות: הסרת הכרטיס מהחלון בלי לשנות את סטטוס המשרות
  function handleIgnoreGroup(groupIndex) {
    const card = document.getElementById(`dup-card-${groupIndex}`);
    if (card) {
      card.remove();
      checkRemainingDuplicateCards();
    }
  }

  function checkRemainingDuplicateCards() {
    const content = document.getElementById('duplicatesContent');
    if (!content) return;
    const remaining = content.querySelectorAll('[id^="dup-card-"]');
    if (remaining.length === 0) {
      content.innerHTML = `
        <div style="padding: 32px 16px; text-align: center; color: var(--dashboard-muted); font-size: 15px;">
          <div style="font-size: 38px; color: var(--dashboard-lime); margin-bottom: 10px;"><i class="ph-duotone ph-check-circle"></i></div>
          <div style="color: #fff; font-weight: 700; font-size: 16px; margin-bottom: 4px;">כל הכפילויות טופלו בהצלחה!</div>
          <div>לוח המשרות נקי ומסונכרן.</div>
        </div>
      `;
    }
  }

  function closeDuplicatesModal() {
    closeDialogEl(document.getElementById('duplicatesModal'));
  }

  let cachedInactiveJobsReport = null;
  const JOB_CHECK_URL_KEY = 'job_check_worker_url';
  const liveCheckResults = new Map();
  let liveCheckRunning = false;
  let liveCheckProgress = { done: 0, total: 0 };

  function getJobCheckWorkerUrl() {
    let stored = '';
    try { stored = localStorage.getItem(JOB_CHECK_URL_KEY) || ''; } catch (e) {}
    const cfg = (window.__APP_CONFIG__ && window.__APP_CONFIG__.job_check_url) || '';
    return (stored || cfg || '').trim();
  }

  function saveJobCheckWorkerUrl() {
    const input = document.getElementById('jobCheckWorkerInput');
    if (!input) return;
    const raw = input.value.trim();
    if (raw && !/^https:\/\/[^\s]+$/i.test(raw)) {
      showToast('ph-warning', 'כתובת ה-Worker חייבת להתחיל ב-https://');
      return;
    }
    try {
      if (raw) localStorage.setItem(JOB_CHECK_URL_KEY, raw);
      else localStorage.removeItem(JOB_CHECK_URL_KEY);
    } catch (e) {}
    renderInactiveJobsModalContent();
  }

  async function openInactiveJobsModal() {
    const modal = document.getElementById('inactiveJobsModal');
    const content = document.getElementById('inactiveJobsContent');
    if (!modal || !content) return;

    openDialogEl(modal);

    content.innerHTML = `
      <div style="padding: 24px; text-align: center; color: var(--dashboard-muted); font-size: 14px;">
        <i class="ph-duotone ph-spinner-gap ph-spin" style="font-size: 24px; display: block; margin-bottom: 8px;"></i>
        בודק משרות שנסגרו או הוסרו...
      </div>
    `;

    try {
      if (!cachedInactiveJobsReport) {
        const resp = await fetch('data/inactive_jobs.json?t=' + Date.now(), { cache: 'no-store' });
        if (resp && resp.ok) {
          cachedInactiveJobsReport = await resp.json();
        }
      }
    } catch(e) {}

    renderInactiveJobsModalContent();
  }

  function closeInactiveJobsModal() {
    const modal = document.getElementById('inactiveJobsModal');
    closeDialogEl(modal);
  }

  function computeInactiveState() {
    const allJobs = getAllAvailableJobs();
    const activeJobsMap = new Map();
    allJobs.forEach(j => {
      const state = getJobState(j.link);
      if (state !== 'rejected' && state !== 'purged') {
        activeJobsMap.set(getCanonicalJobKey(j.link), j);
      }
    });

    const inactiveList = [];
    const seen = new Set();
    const push = (job, reason, statusCode) => {
      const canon = getCanonicalJobKey(job.link);
      if (seen.has(canon)) return;
      seen.add(canon);
      inactiveList.push({
        link: job.link,
        title: job.title || 'משרה ללא כותרת',
        company: job.company || 'חברה לא צוינה',
        reason: reason,
        status_code: statusCode || 0
      });
    };

    liveCheckResults.forEach((res, canon) => {
      if (res.state === 'inactive' && activeJobsMap.has(canon)) {
        push(activeJobsMap.get(canon), res.reason || 'המשרה אינה פעילה באתר', res.status);
      }
    });

    const report = cachedInactiveJobsReport;
    if (report && Array.isArray(report.inactive_jobs)) {
      report.inactive_jobs.forEach(item => {
        const canon = getCanonicalJobKey(item.link);
        const live = liveCheckResults.get(canon);
        if (live && live.state === 'active') return;
        if (activeJobsMap.has(canon)) {
          push(activeJobsMap.get(canon), item.reason || 'המשרה נסגרה לקבלת מועמדויות', item.status_code);
        }
      });
    }

    activeJobsMap.forEach((j, canon) => {
      if (j.is_active === false || j.is_expired === true || j.is_closed === true) {
        push(j, j.closure_reason || 'המשרה אינה פעילה באתר', 0);
      }
    });

    const verified = new Set();
    if (report && Array.isArray(report.verified_links)) {
      report.verified_links.forEach(l => verified.add(getCanonicalJobKey(l)));
    } else if (report && Array.isArray(report.inactive_jobs)) {
      report.inactive_jobs.forEach(i => verified.add(getCanonicalJobKey(i.link)));
    }
    liveCheckResults.forEach((res, canon) => { if (res.state !== 'unknown') verified.add(canon); });

    let unchecked = 0;
    activeJobsMap.forEach((j, canon) => { if (!verified.has(canon)) unchecked++; });

    return { inactiveList, activeJobsMap, unchecked, totalActive: activeJobsMap.size };
  }

  function inactiveStatusPanelHtml(st) {
    const report = cachedInactiveJobsReport;
    let reportLine = 'אין דוח סריקה זמין.';
    if (report && report.scanned_at) {
      let when = report.scanned_at;
      try { when = new Date(report.scanned_at).toLocaleString('he-IL'); } catch (e) {}
      reportLine = `דוח סריקה אחרון: ${escapeHtml(when)}`;
    }
    const unknownLive = Array.from(liveCheckResults.values()).filter(r => r.state === 'unknown').length;
    const coverage = st.unchecked > 0
      ? `<strong>${st.unchecked}</strong> מתוך ${st.totalActive} משרות לא אומתו (חדשות או חסומות לבדיקה). הדוח אינו מכסה אותן.`
      : `כל ${st.totalActive} המשרות הפעילות נבדקו.`;
    const workerUrl = getJobCheckWorkerUrl();
    let live;
    if (workerUrl) {
      const label = liveCheckRunning
        ? `בודק ${liveCheckProgress.done} מתוך ${liveCheckProgress.total}...`
        : `בדיקה חיה של ${st.totalActive} משרות`;
      live = `
        <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
          <button type="button" id="btnLiveJobCheck" class="tool-btn" style="min-height:44px; padding:8px 14px;" onclick="runLiveJobCheck()" ${liveCheckRunning ? 'disabled aria-disabled="true"' : ''}>
            <i class="ph-duotone ph-broadcast"></i> <span>${label}</span>
          </button>
          <progress id="liveCheckProgress" max="${liveCheckProgress.total || 1}" value="${liveCheckProgress.done}" aria-label="התקדמות הבדיקה החיה" style="${liveCheckRunning ? '' : 'display:none;'} flex:1; min-width:120px;"></progress>
          ${unknownLive ? `<span style="font-size:12px; color:#fcd34d;">${unknownLive} משרות לא ניתנו לאימות בבדיקה האחרונה</span>` : ''}
        </div>`;
    } else {
      live = `
        <div style="display:flex; flex-direction:column; gap:6px;">
          <label for="jobCheckWorkerInput" style="font-size:12px; color:#cbd5e1;">לבדיקה חיה בלחיצה, הדבק כתובת Worker (הוראות: tools/cloudflare-worker/README.md)</label>
          <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <input id="jobCheckWorkerInput" type="url" inputmode="url" dir="ltr" placeholder="https://job-check.example.workers.dev" style="flex:1; min-width:200px; min-height:44px; padding:8px 12px; border-radius:8px; border:1px solid rgba(255,255,255,0.2); background:rgba(15,23,42,0.9); color:#fff;">
            <button type="button" class="tool-btn" style="min-height:44px; padding:8px 14px;" onclick="saveJobCheckWorkerUrl()">שמור</button>
          </div>
        </div>`;
    }
    return `
      <div style="padding:12px 14px; border:1px solid rgba(255,255,255,0.1); border-radius:8px; background:rgba(255,255,255,0.03); display:flex; flex-direction:column; gap:10px; font-size:13px; color:#cbd5e1;">
        <div>${reportLine}</div>
        <div role="status" aria-live="polite">${coverage}</div>
        ${live}
      </div>`;
  }

  async function runLiveJobCheck() {
    const workerUrl = getJobCheckWorkerUrl();
    if (!workerUrl || liveCheckRunning) return;
    const st = computeInactiveState();
    const targets = Array.from(st.activeJobsMap.entries());
    liveCheckRunning = true;
    liveCheckProgress = { done: 0, total: targets.length };
    renderInactiveJobsModalContent();

    const base = workerUrl.replace(/\/+$/, '');
    let cursor = 0;
    const worker = async () => {
      while (cursor < targets.length) {
        const [canon, job] = targets[cursor++];
        try {
          const resp = await fetch(base + '/?u=' + encodeURIComponent(job.link));
          if (!resp.ok) throw new Error('HTTP ' + resp.status);
          const data = await resp.json();
          liveCheckResults.set(canon, { state: data.state || 'unknown', reason: data.reason || '', status: data.status || 0 });
        } catch (e) {
          liveCheckResults.set(canon, { state: 'unknown', reason: 'שגיאת תקשורת מול ה-Worker', status: 0 });
        }
        liveCheckProgress.done++;
        const bar = document.getElementById('liveCheckProgress');
        if (bar) bar.value = liveCheckProgress.done;
        const btn = document.getElementById('btnLiveJobCheck');
        if (btn) {
          const span = btn.querySelector('span');
          if (span) span.textContent = `בודק ${liveCheckProgress.done} מתוך ${liveCheckProgress.total}...`;
        }
      }
    };
    await Promise.all([worker(), worker(), worker(), worker()]);
    liveCheckRunning = false;
    renderInactiveJobsModalContent();
    const found = computeInactiveState().inactiveList.length;
    showToast('ph-check-circle', `הבדיקה החיה הסתיימה: ${found} משרות לא פעילות`);
  }

  function renderInactiveJobsModalContent() {
    const content = document.getElementById('inactiveJobsContent');
    if (!content) return;

    const st = computeInactiveState();
    const inactiveList = st.inactiveList;
    const panel = inactiveStatusPanelHtml(st);

    if (inactiveList.length === 0) {
      const honest = st.unchecked > 0
        ? 'לא אותרו משרות סגורות מבין המשרות שנבדקו. חלק מהמשרות לא אומתו, ולכן ייתכן שיש משרות סגורות שלא זוהו.'
        : 'לא אותרו משרות שנסגרו או הוסרו במאגר הפעיל.';
      content.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:14px; direction: rtl; text-align: right;">
          ${panel}
          <div style="padding: 24px 16px; text-align: center; color: var(--dashboard-muted); font-size: 14.5px;">
            <div style="font-size: 28px; margin-bottom: 8px; color: var(--dashboard-lime);"><i class="ph-duotone ph-check-circle"></i></div>
            <div>${honest}</div>
          </div>
        </div>
      `;
      return;
    }

    let html = `
      <div style="display: flex; flex-direction: column; gap: 14px; direction: rtl; text-align: right;">
        ${panel}
        <div style="padding: 10px 14px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 8px; font-size: 13px; color: #fca5a5; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
          <div>
            אותרו <strong>${inactiveList.length}</strong> משרות שאינן פעילות עוד או שהגשת המועמדות אליהן נסגרה.
          </div>
          <button type="button" onclick="handleRemoveAllInactiveJobs()" class="btn-triage" style="background: rgba(239, 68, 68, 0.3); border-color: rgba(239, 68, 68, 0.6); color: #fff; font-size: 12px; padding: 5px 12px; min-height: 44px; cursor: pointer; border-radius: 6px;">
            <i class="ph-duotone ph-trash"></i> <span>הסר את כולן ללשונית הוסרו</span>
          </button>
        </div>
    `;

    inactiveList.forEach((job, idx) => {
      const safeLink = sanitizeUrl(job.link);
      const safeTitle = escapeHtml(job.title);
      const safeCompany = escapeHtml(job.company);
      const safeReason = escapeHtml(job.reason);

      html += `
        <div id="inactive-card-${idx}" style="border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 12px 14px; background: rgba(255, 255, 255, 0.03); display: flex; justify-content: space-between; align-items: center; gap: 12px;">
          <div style="flex: 1; min-width: 0;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
              <span style="font-size: 11px; background: rgba(239, 68, 68, 0.2); color: #fca5a5; padding: 2px 8px; border-radius: 4px; font-weight: 600;">
                ${safeReason}
              </span>
            </div>
            <div style="font-weight: 600; font-size: 14px; color: #f1f5f9; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
              ${safeTitle}
            </div>
            <div style="font-size: 12px; color: var(--dashboard-muted);">
              ${safeCompany} | <a href="${safeLink}" target="_blank" rel="noopener noreferrer" style="color: var(--dashboard-cyan); text-decoration: none;">בדיקת קישור</a>
            </div>
          </div>
          <div style="display: flex; gap: 8px; flex-shrink: 0;">
            <button type="button" onclick="handleRemoveInactiveJob(${escapeHtml(JSON.stringify(job.link))}, ${idx})" class="btn-triage" style="background: rgba(239, 68, 68, 0.2); border-color: rgba(239, 68, 68, 0.4); color: #fca5a5; font-size: 12px; padding: 5px 10px; min-height: 44px; cursor: pointer; border-radius: 6px;">
              <i class="ph-duotone ph-trash"></i> <span>הסר משרה</span>
            </button>
          </div>
        </div>
      `;
    });

    html += `</div>`;
    content.innerHTML = html;
  }

  function handleRemoveInactiveJob(link, cardIdx) {
    toggleAction(link, 'rejected');
    const card = document.getElementById('inactive-card-' + cardIdx);
    if (card) {
      card.style.opacity = '0.4';
      card.style.pointerEvents = 'none';
      card.innerHTML = `
        <div style="color: var(--dashboard-muted); font-size: 13px; padding: 6px 0;">
          <i class="ph-bold ph-check"></i> המשרה הועברה למשרות שהוסרו
        </div>
      `;
    }
  }

  function handleRemoveAllInactiveJobs() {
    const st = computeInactiveState();
    st.inactiveList.forEach(item => toggleAction(item.link, 'rejected'));
    renderInactiveJobsModalContent();
    showToast('ph-trash', `הוסרו ${st.inactiveList.length} משרות לא פעילות`);
  }


  function clearAllRejected() {
    const rejectedKeys = Object.keys(jobStates).filter(id => jobStates[id] === 'rejected');
    if (rejectedKeys.length === 0) {
      showToast('ph-info', 'אין משרות מוסרות למחיקה');
      return;
    }

    if (!confirm(`האם אתה בטוח שברצונך למחוק לצמיתות ${rejectedKeys.length} משרות שהוסרו ולאפס את המונה?`)) {
      return;
    }

    rejectedKeys.forEach(id => {
      jobStates[id] = 'purged';
    });

    recordLocalEdit();
    saveTriageState(jobStates);
    updateCubeCountsImmediately();
    renderCards();
    updateUI();
    scheduleCloudPush();
    showToast('ph-trash', `כל ${rejectedKeys.length} המשרות שהוסרו נמחקו לצמיתות והמונה אופס ל-0`);
  }

  function exportSavedToExcel() {
    const allPotentialSaved = getAllAvailableJobs();
    const savedJobs = allPotentialSaved.filter(job => jobStates[job.link] === 'saved');
    if (savedJobs.length === 0) {
      showToast('ph-warning', 'לא נמצאו משרות שמורות לייצוא');
      return;
    }

    const BOM = '\uFEFF';
    const headers = [
      'חברה',
      'כותרת משרה',
      'ציון התאמה',
      'תחום',
      'מיקום',
      'טווח שכר צפוי',
      'ביסוס ומקור שכר',
      'דרישות החברה עבור המשרה',
      'תחום ומוצר החברה',
      'תקציר המשרה',
      'נקודות חוזק מהניסיון',
      'דגשים ומודל עבודה',
      'לינק למשרה',
      'תאריך איתור'
    ];

    const escapeCSV = (val) => {
      if (val === null || val === undefined) return '""';
      const str = String(val).replace(/^[=+@\-\t\r]/, "'$&").replace(/"/g, '""');
      return `"${str}"`;
    };

    const rows = savedJobs.map(job => {
      const score = job.match_score || '';
      const reqs = job.company_requirements || '';
      const domain = job.company_domain_product || job.company_summary || '';
      const summary = job.job_summary || job.company_summary || '';
      const strengths = job.experience_strengths || job.reasoning || '';
      const highlights = job.key_highlights || (job.work_model ? `מודל: ${job.work_model}` : '');
      const date = job.date || '';
      let salaryStr = job.salary_range || 'לא צוין';
      if (job.salary_source_label) {
        salaryStr += ` (${job.salary_source_label})`;
      }
      const salaryEvidence = job.salary_evidence || '';

      return [
        escapeCSV(job.company || ''),
        escapeCSV(job.title || ''),
        escapeCSV(score),
        escapeCSV(job.sector || job.sector_key || ''),
        escapeCSV(job.location || 'ישראל'),
        escapeCSV(salaryStr),
        escapeCSV(salaryEvidence),
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

    showToast('ph-file-xls', `יוצאו ${savedJobs.length} משרות שמורות לאקסל בהצלחה!`);
  }

  /* ==========================================================================
     Milestone 1: Architecture Framework & Mode Switcher
     ========================================================================== */
  const APP_ACTIVE_MODE_KEY = 'ido_app_active_mode';
  let currentAppMode = 'radar';

  /**
   * Switches top-level app mode between 'radar' (Job Radar) and 'studio' (Career Studio).
   * @param {string} mode - 'radar' or 'studio'
   * @param {boolean} [updateHash=true] - Whether to update window.location.hash
   */
  function switchDashboardAppMode(mode, updateHash = true) {
    const targetMode = (mode === 'studio') ? 'studio' : 'radar';
    currentAppMode = targetMode;

    const radarWs = document.getElementById('radarWorkspace');
    const studioWs = document.getElementById('careerStudioWorkspace');
    const btnRadar = document.getElementById('modeSwitchRadar');
    const btnStudio = document.getElementById('modeSwitchStudio');
    const progressHub = document.querySelector('.header-progress-hub');

    if (targetMode === 'studio') {
      if (radarWs) {
        radarWs.style.display = 'none';
        radarWs.classList.remove('active');
        radarWs.classList.add('hidden');
      }
      if (studioWs) {
        studioWs.style.display = 'flex';
        studioWs.classList.remove('hidden');
        studioWs.classList.add('active');
      }
      if (btnStudio) {
        btnStudio.classList.add('active');
        btnStudio.setAttribute('aria-selected', 'true');
      }
      if (btnRadar) {
        btnRadar.classList.remove('active');
        btnRadar.setAttribute('aria-selected', 'false');
      }
      if (progressHub) {
        progressHub.classList.add('studio-mode-hub-compact');
      }
      if (typeof populateAtsJobSelector === 'function') {
        populateAtsJobSelector();
      }
      if (updateHash && window.location.hash !== '#studio') {
        window.location.hash = '#studio';
      }
    } else {
      if (studioWs) {
        studioWs.style.display = 'none';
        studioWs.classList.remove('active');
        studioWs.classList.add('hidden');
      }
      if (radarWs) {
        radarWs.style.display = 'block';
        radarWs.classList.remove('hidden');
        radarWs.classList.add('active');
      }
      if (btnRadar) {
        btnRadar.classList.add('active');
        btnRadar.setAttribute('aria-selected', 'true');
      }
      if (btnStudio) {
        btnStudio.classList.remove('active');
        btnStudio.setAttribute('aria-selected', 'false');
      }
      if (progressHub) {
        progressHub.classList.remove('studio-mode-hub-compact');
      }
      if (updateHash && window.location.hash !== '#radar') {
        window.location.hash = '#radar';
      }

      // Invalidate Leaflet map size when returning to radar workspace
      if (typeof liveJobsMapInstance !== 'undefined' && liveJobsMapInstance) {
        setTimeout(() => {
          if (liveJobsMapInstance && typeof liveJobsMapInstance.invalidateSize === 'function') {
            liveJobsMapInstance.invalidateSize();
          }
        }, 150);
      }
    }

    try {
      localStorage.setItem(APP_ACTIVE_MODE_KEY, targetMode);
    } catch (e) {
      console.warn('[STORAGE] Could not persist app active mode:', e);
    }
  }

  /**
   * Switches the active module inside Career Studio workspace.
   * @param {string} moduleId - 'ats', 'writer', 'interview', 'skills'
   */
  function switchStudioModule(moduleId) {
    const modules = ['ats', 'writer', 'interview', 'skills'];
    const activeModule = modules.includes(moduleId) ? moduleId : 'ats';

    const tabMap = {
      ats: 'studioTabAts',
      writer: 'studioTabWriter',
      interview: 'studioTabInterview',
      skills: 'studioTabSkills'
    };

    const panelMap = {
      ats: 'studioModuleAts',
      writer: 'studioModuleWriter',
      interview: 'studioModuleInterview',
      skills: 'studioModuleSkills'
    };

    modules.forEach(m => {
      const tabEl = document.getElementById(tabMap[m]);
      const panelEl = document.getElementById(panelMap[m]);
      const isTarget = (m === activeModule);

      if (tabEl) {
        if (isTarget) {
          tabEl.classList.add('active');
          tabEl.setAttribute('aria-selected', 'true');
        } else {
          tabEl.classList.remove('active');
          tabEl.setAttribute('aria-selected', 'false');
        }
      }

      if (panelEl) {
        if (isTarget) {
          panelEl.style.display = 'block';
          panelEl.classList.add('active');
          if (m === 'ats' && typeof initAtsModule === 'function') {
            initAtsModule();
            initCvUploadState();
          } else if (m === 'writer' && typeof initWriterModule === 'function') {
            initWriterModule();
          }
        } else {
          panelEl.style.display = 'none';
          panelEl.classList.remove('active');
        }
      }
    });
  }

  /**
   * Returns active CV profile (custom uploaded resume if present, or baseline CANONICAL_CV_PROFILE).
   */
  function getActiveCvProfile() {
    if (window.customUploadedCvProfile) {
      return window.customUploadedCvProfile;
    }
    if (window.customUploadedCvText && typeof window.customUploadedCvText === 'string' && window.customUploadedCvText.trim().length > 0) {
      return {
        name: window.customUploadedCvName || "מועמד עצמאי (קובץ שהועלה)",
        name_en: "Candidate (Custom Upload)",
        title_he: "קורות חיים שהועלו עצמאית",
        title_en: "Candidate Uploaded Resume",
        text: window.customUploadedCvText,
        skills: [],
        education: [],
        experience: [window.customUploadedCvText]
      };
    }
    return CANONICAL_CV_PROFILE;
  }

  /**
   * Decodes printable text blocks from ArrayBuffer as an offline/robust fallback.
   */
  function extractRawBinaryText(arrayBuffer) {
    try {
      const decoder = new TextDecoder('utf-8', { fatal: false });
      const rawStr = decoder.decode(arrayBuffer);
      const xmlMatches = rawStr.match(/<w:t[^>]*>(.*?)<\/w:t>/g);
      if (xmlMatches && xmlMatches.length > 0) {
        return xmlMatches.map(m => m.replace(/<[^>]+>/g, '')).join(' ');
      }
      const printable = rawStr.replace(/[^\x20-\x7E\u0590-\u05FF\n\r\t]/g, ' ');
      return printable.replace(/\s{2,}/g, ' ').trim();
    } catch (e) {
      return '';
    }
  }

  /**
   * Extracts text from TXT file.
   */
  function extractTxtText(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result || '');
      reader.onerror = (e) => reject(e);
      reader.readAsText(file);
    });
  }

  /**
   * Extracts text from PDF file via PDF.js with fallback.
   */
  async function extractPdfText(file) {
    const arrayBuffer = await file.arrayBuffer();
    if (typeof window !== 'undefined' && window.pdfjsLib && window.pdfjsLib.getDocument) {
      try {
        if (!window.pdfjsLib.GlobalWorkerOptions.workerSrc) {
          window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        }
        const loadingTask = window.pdfjsLib.getDocument({ data: arrayBuffer });
        const pdf = await loadingTask.promise;
        const pageTexts = [];
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i);
          const textContent = await page.getTextContent();
          const pageStr = textContent.items.map(item => item.str).join(' ');
          pageTexts.push(pageStr);
        }
        const fullText = pageTexts.join('\n').trim();
        if (fullText.length > 0) return fullText;
      } catch (err) {
        console.warn('[PDF.js Extraction Fallback]', err);
      }
    }
    return extractRawBinaryText(arrayBuffer);
  }

  /**
   * Extracts text from DOCX file via Mammoth with XML fallback.
   */
  async function extractDocxText(file) {
    const arrayBuffer = await file.arrayBuffer();
    if (typeof window !== 'undefined' && window.mammoth && window.mammoth.extractRawText) {
      try {
        const result = await window.mammoth.extractRawText({ arrayBuffer: arrayBuffer });
        if (result && result.value && result.value.trim().length > 0) {
          return result.value.trim();
        }
      } catch (err) {
        console.warn('[Mammoth Extraction Fallback]', err);
      }
    }
    return extractRawBinaryText(arrayBuffer);
  }

  /**
   * Generic dispatcher for client-side CV text extraction.
   */
  async function extractTextFromFile(file) {
    const fileName = (file.name || '').toLowerCase();
    const ext = fileName.split('.').pop();
    if (ext === 'txt') {
      return await extractTxtText(file);
    } else if (ext === 'pdf') {
      return await extractPdfText(file);
    } else if (ext === 'docx' || ext === 'doc') {
      return await extractDocxText(file);
    }
    return await extractTxtText(file);
  }

  /**
   * Processes an uploaded CV file: extracts text, updates state, and recalculates ATS matches.
   */
  async function processCvFile(file) {
    if (!file) return;

    const fileName = file.name;
    const fileSizeKb = (file.size / 1024).toFixed(1);
    const ext = fileName.split('.').pop().toLowerCase();

    if (!['pdf', 'docx', 'doc', 'txt'].includes(ext)) {
      if (typeof showToast === 'function') {
        showToast('ph-warning', 'פורמט לא נתמך. אנא העלה קובץ מסוג PDF, DOCX או TXT.');
      }
      return;
    }

    const feedbackEl = document.getElementById('studioCvParseFeedback');
    const feedbackMsgEl = document.getElementById('studioCvParseMsg');
    if (feedbackEl) feedbackEl.style.display = 'flex';
    if (feedbackMsgEl) feedbackMsgEl.textContent = `מחלץ טקסט מתוך ${fileName}...`;

    try {
      const extractedText = await extractTextFromFile(file);
      const cleanText = (extractedText || '').replace(/\s{2,}/g, ' ').trim();
      const wordCount = cleanText ? cleanText.split(/\s+/).filter(Boolean).length : 0;

      window.customUploadedCvName = fileName;
      window.customUploadedCvText = cleanText;
      window.customUploadedCvProfile = {
        name: fileName.replace(/\.[^/.]+$/, ''),
        name_en: "Uploaded Candidate",
        title_he: "מועמד עצמאי (קובץ שהועלה)",
        title_en: "Candidate Uploaded Resume",
        text: cleanText,
        skills: [],
        education: [],
        experience: [cleanText]
      };

      // Update UI elements
      const nameEl = document.getElementById('studioCvFileName');
      const subEl = document.getElementById('studioCvFileSub');
      const resetBtn = document.getElementById('btnResetToBaselineCv');
      const statusIcon = document.getElementById('studioCvStatusIcon');
      const baselineStatusText = document.getElementById('atsBaselineStatusText');

      if (nameEl) nameEl.textContent = fileName;
      if (subEl) subEl.textContent = `${fileSizeKb} KB • ${wordCount} מילים • הועלה עצמאית`;
      if (resetBtn) resetBtn.style.display = 'inline-flex';
      if (statusIcon) {
        statusIcon.className = 'ph-duotone ph-file-text';
        statusIcon.style.color = 'var(--dashboard-cyan)';
      }
      if (baselineStatusText) {
        baselineStatusText.textContent = `מוכן לניתוח מול קובץ שהועלה: ${fileName} (${wordCount} מילים)`;
      }

      // Persist state in localStorage
      try {
        localStorage.setItem('job_studio_custom_cv_name', fileName);
        localStorage.setItem('job_studio_custom_cv_size', `${fileSizeKb} KB`);
        if (cleanText && cleanText.length < 300000) {
          localStorage.setItem('job_studio_custom_cv_text', cleanText);
        }
      } catch (e) {}

      if (feedbackEl) {
        feedbackEl.style.display = 'flex';
        if (feedbackMsgEl) feedbackMsgEl.textContent = `חילוץ טקסט הושלם: ${wordCount} מילים זוהו בהצלחה`;
        setTimeout(() => {
          if (feedbackEl) feedbackEl.style.display = 'none';
        }, 3500);
      }

      if (typeof showToast === 'function') {
        showToast('ph-file-arrow-up', `קובץ ${fileName} נטען וחולץ (${wordCount} מילים)`);
      }

      // Re-trigger ATS evaluation with the newly uploaded CV
      triggerAtsMatching();

    } catch (err) {
      console.error('[CV Extraction Error]', err);
      if (feedbackEl) {
        if (feedbackMsgEl) feedbackMsgEl.textContent = 'שגיאה בחילוץ הטקסט מהקובץ שנבחר.';
      }
      if (typeof showToast === 'function') {
        showToast('ph-x-circle', 'שגיאה בחילוץ תוכן קורות החיים');
      }
    }
  }

  /**
   * Handles user-uploaded CV file input change event.
   */
  function handleManualCvUpload(event) {
    const file = event.target.files && event.target.files[0];
    if (file) {
      processCvFile(file);
    }
  }

  /**
   * Resets active CV back to system baseline (Ido Gal).
   */
  function resetToBaselineCv() {
    try {
      localStorage.removeItem('job_studio_custom_cv_name');
      localStorage.removeItem('job_studio_custom_cv_size');
      localStorage.removeItem('job_studio_custom_cv_text');
    } catch (e) {}

    window.customUploadedCvName = null;
    window.customUploadedCvText = null;
    window.customUploadedCvProfile = null;

    const fileInput = document.getElementById('manualCvFileInput');
    if (fileInput) fileInput.value = '';

    const nameEl = document.getElementById('studioCvFileName');
    const subEl = document.getElementById('studioCvFileSub');
    const resetBtn = document.getElementById('btnResetToBaselineCv');
    const statusIcon = document.getElementById('studioCvStatusIcon');
    const baselineStatusText = document.getElementById('atsBaselineStatusText');
    const feedbackEl = document.getElementById('studioCvParseFeedback');

    if (feedbackEl) feedbackEl.style.display = 'none';
    if (nameEl) nameEl.textContent = 'עידו גל - הנדסאי מכונות (גרסת מערכת)';
    if (subEl) subEl.textContent = 'פרופיל פעיל לניתוח ATS';
    if (resetBtn) resetBtn.style.display = 'none';
    if (statusIcon) {
      statusIcon.className = 'ph-duotone ph-check-circle';
      statusIcon.style.color = 'var(--dashboard-lime)';
    }
    if (baselineStatusText) {
      baselineStatusText.textContent = 'מוכן לניתוח מול פרופיל הבסיס של עידו גל';
    }

    triggerAtsMatching();

    if (typeof showToast === 'function') {
      showToast('ph-arrow-counter-clockwise', 'אופס לקורות החיים המובנים של עידו גל');
    }
  }

  /**
   * Initializes Drag & Drop listeners on #studioCvDropZone.
   */
  function initCvDropZone() {
    const dropZone = document.getElementById('studioCvDropZone');
    if (!dropZone || dropZone.dataset.bound === 'true') return;
    dropZone.dataset.bound = 'true';

    ['dragenter', 'dragover'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add('drag-active');
      });
    });

    ['dragleave', 'dragend'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('drag-active');
      });
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove('drag-active');
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
        processCvFile(e.dataTransfer.files[0]);
      }
    });

    dropZone.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        const input = document.getElementById('manualCvFileInput');
        if (input) input.click();
      }
    });
  }

  /**
   * Restores uploaded CV metadata and extracted text from localStorage on page load.
   */
  function initCvUploadState() {
    try {
      const savedName = localStorage.getItem('job_studio_custom_cv_name');
      const savedSize = localStorage.getItem('job_studio_custom_cv_size');
      const savedText = localStorage.getItem('job_studio_custom_cv_text');

      if (savedName) {
        window.customUploadedCvName = savedName;
        if (savedText) {
          window.customUploadedCvText = savedText;
          window.customUploadedCvProfile = {
            name: savedName.replace(/\.[^/.]+$/, ''),
            name_en: "Uploaded Candidate",
            title_he: "מועמד עצמאי (קובץ שהועלה)",
            title_en: "Candidate Uploaded Resume",
            text: savedText,
            skills: [],
            education: [],
            experience: [savedText]
          };
        }

        const nameEl = document.getElementById('studioCvFileName');
        const subEl = document.getElementById('studioCvFileSub');
        const resetBtn = document.getElementById('btnResetToBaselineCv');
        const statusIcon = document.getElementById('studioCvStatusIcon');
        const baselineStatusText = document.getElementById('atsBaselineStatusText');

        if (nameEl) nameEl.textContent = savedName;
        if (subEl) subEl.textContent = `${savedSize || ''} • הועלה עצמאית`;
        if (resetBtn) resetBtn.style.display = 'inline-flex';
        if (statusIcon) {
          statusIcon.className = 'ph-duotone ph-file-text';
          statusIcon.style.color = 'var(--dashboard-cyan)';
        }
        if (baselineStatusText) {
          baselineStatusText.textContent = `מוכן לניתוח מול קובץ שהועלה: ${savedName}`;
        }
      }
    } catch (e) {}

    initCvDropZone();
  }

  /* ==========================================================================
     CAREER STUDIO: MILESTONE 2 - ATS & STATUTORY HARD GATES ENGINE
     ========================================================================== */

  const CANONICAL_CV_PROFILE = {
    name: "עידו גל",
    name_en: "Ido Gal",
    title_he: "הנדסאי מכונות | בקרת גז טבעי | תפעול מערכות אנרגיה",
    title_en: "Gas Controller | Natural Gas Operations | Practical Mechanical Engineer",
    contact: {
      phone: "052-632-8886",
      phone_intl: "+972-52-632-8886",
      email: "idogal0210@gmail.com",
      linkedin: "https://www.linkedin.com/in/ido-g",
      location: "תל אביב"
    },
    education: [
      "לימודי חשמלאי מוסמך | המרכז האקדמי רופין | צפי סיום: דצמבר 2026",
      "הנדסאי מכונות — התמחות בגז טבעי ובאנרגיה ירוקה | המרכז האקדמי רופין | 2022. פרויקט גמר: השוואת נצילות וכדאיות כלכלית וטכנית בין מערכות סולאריות בעלות פאנלים דו־צדדיים (Bifacial) לבין מערכות בעלות פאנלים חד־צדדיים (Monofacial)."
    ],
    experience: [
      "בקר גז — תפעול ומוצר | Energean Israel Ltd. | נובמבר 2022 – ספטמבר 2026: בקרה 24/7 על אספקת גז טבעי לתחנות כוח ומפעלי תעשייה, ניטור לחצים וספיקות בזמן אמת עם AVEVA System Platform, טיפול ב-Nomination ו-Re-nomination, תיאום מול אסדת ההפקה הימית (FPSO), נתג״ז (INGL) והמחלקה המסחרית, פיתוח סוכן חישוב כמויות גז ב-Microsoft 365 Copilot עבור 10+ לקוחות גדולים, שיפור תהליך העברת משמרת עם סוכן Copilot נפרד, ודוחות Excel ו-SAP כולל דוח משמרות לילה לסמנכ״ל.",
      "אחראי משמרת אבטחה במתקן אנרגיה אסטרטגי | וולקן עוצמה בע״מ / Energean Israel Ltd. | 2020–2022.",
      "ראש צוות ומדריך מכירות | חברות מכירות בפעילות בינלאומית | 2015–2020 (ארה״ב וקו ישראל–גרמניה).",
      "מתקין מערכות סולאריות | MER Group | 2010–2012: התקנה, חיווט והרכבה פיזית של מערכות פוטו־וולטאיות (PV)."
    ],
    military: "סיירת נח״ל | לוחם ומפקד בתחום החבלה וההנדסה הקרבית | 2012–2015 (כולל שירות קבע והובלת תחום החבלה ביחידה). ניסיון מבצעי בהפעלת רחפנים (UAV) לסריקה ומיפוי שטח. הסמכות: רובאי 07, פלס/חבלה 08.",
    skills: [
      "AVEVA System Platform", "SCADA", "PRMS", "Nomination", "Re-nomination", "FPSO", "INGL",
      "SAP", "Microsoft Excel", "Microsoft 365 Copilot", "Google Gemini", "Bifacial PV", "Monofacial PV",
      "ניטור לחצים וספיקות", "אסדת הפקה", "נתג״ז", "חבלה 07", "רובאי 08", "הפעלת רחפנים", "UAV",
      "מתח נמוך", "חוק החשמל"
    ],
    text: `עידו גל הנדסאי מכונות בקרת גז טבעי תפעול מערכות אנרגיה רופין 2022 אנרגיה ירוקה וגז טבעי
פרויקט גמר פאנלים סולאריים דו צדדיים Bifacial PV מול Monofacial
לימודי חשמלאי מוסמך רופין צפי סיום דצמבר 2026 לקראת סיום חוק החשמל חישובים תיאורטיים
Energean Israel Ltd בקר גז תפעול ומוצר נובמבר 2022 ספטמבר 2026 AVEVA System Platform אסדת הפקה FPSO נתג״ז INGL PRMS SCADA Nomination Re-nomination SAP Excel Microsoft 365 Copilot Google Gemini מתקן אנרגיה 24/7
וולקן עוצמה אחראי משמרת אבטחה במתקן אנרגיה אסטרטגי אחמ״ש אבטחה
MER Group מתקין מערכות סולאריות PV שטח עבודה בגובה
סיירת נח״ל לוחם ומפקד בתחום החבלה וההנדסה הקרבית פלס 07 חבלה 08 רובאי 07 רובאי 08 מפעיל רחפנים מבצעי טלמטריה
טלפון 052-632-8886 0526328886 +972-52-632-8886 דואל idogal0210@gmail.com לינקדאין https://www.linkedin.com/in/ido-g`
  };

  const STATUTORY_HARD_GATES = [
    {
      id: "gate_practical_mech_eng",
      name_he: "הנדסאי מכונות מוסמך",
      name_en: "Certified Practical Mechanical Engineer",
      regex: /(?:הנדסאי(?:[\s\/-]+(?:מכונות|תעשייה))?|הנדסאי[\s\/-]+מהנדס[\s-]+מכונות|practical[\s-]+mechanical[\s-]+engineer|mechanical[\s-]+practical[\s-]+engineer)/i,
      candidate_status: "PASS",
      candidate_evidence: "דיפלומה מוסמכת מהמרכז האקדמי רופין (2022) בהתמחות גז טבעי ואנרגיה ירוקה.",
      mandatory_for_roles: ["mechanical_engineer", "plant_technician", "operations_engineer"]
    },
    {
      id: "gate_certified_electrician",
      name_he: "חשמלאי מוסמך",
      name_en: "Certified Electrician",
      regex: /(?:חשמלאי[\s-]+מוסמך|certified[\s-]+electrician|licensed[\s-]+electrician)/i,
      candidate_status: "IN_PROGRESS",
      candidate_evidence: "בלימודים במרכז האקדמי רופין, צפי סיום 2026 (כחודשיים לסיום). ידע תיאורטי, חישובים וחוק החשמל.",
      note_he: "במידה והמשרה דורשת רישיון פעיל ביד כעת - יש להציג סטטוס 'לקראת סיום'.",
      mandatory_for_roles: ["electrical_technician", "solar_lead_installer"]
    },
    {
      id: "gate_degree_bsc_engineer",
      name_he: "תואר מהנדס (B.Sc)",
      name_en: "B.Sc. Engineering Degree",
      regex: /(?:תואר[\s-]+ראשון[\s-]+בהנדס(?:ת|ה)|מהנדס[\s-]+מכונות|מהנדס[\s-]+חשמל|b\.?sc\.?[\s-]+(?:in[\s-]+)?(?:mechanical|electrical)[\s-]+engineer(?:ing)?)/i,
      candidate_status: "GAP",
      candidate_evidence: "למועמד דיפלומת הנדסאי מכונות (לא תואר B.Sc).",
      note_he: "פער סף אם המשרה דורשת מהנדס בלבד ללא גמישות להנדסאי מנוסה.",
      mandatory_for_roles: ["senior_r_and_d_engineer", "statutory_pe_stamping"]
    },
    {
      id: "gate_safety_officer",
      name_he: "ממונה בטיחות בעבודה מוסמך",
      name_en: "Certified Safety Officer",
      regex: /(?:ממונה[\s-]+בטיחות|safety[\s-]+officer|certified[\s-]+safety[\s-]+manager)/i,
      candidate_status: "GAP",
      candidate_evidence: "למועמד ניסיון כאחמ״ש אבטחה במתקן אנרגיה רגיש ואכיפת נהלי בטיחות, אך אינו מחזיק ברישיון ממונה בטיחות סטטוטורי לפי תקנות משרד העבודה.",
      mandatory_for_roles: ["hse_manager", "safety_director"]
    },
    {
      id: "gate_working_at_heights",
      name_he: "הדרכת עבודה בגובה",
      name_en: "Working at Heights Certification",
      regex: /(?:עבודה[\s-]+בגובה|working[\s-]+at[\s-]+heights)/i,
      candidate_status: "PASS_REFRESH_RECOMMENDED",
      candidate_evidence: "ניסיון מעשי בהתקנת מערכות סולאריות בגגות ב-Group MER; נדרש רענון תקופתי שנתי.",
      mandatory_for_roles: ["solar_field_tech", "wind_turbine_tech"]
    },
    {
      id: "gate_hazmat_permit",
      name_he: "היתר רעלים / חומ״ס",
      name_en: "HazMat / Hazardous Materials Permit",
      regex: /(?:היתר[\s-]+רעלים|חומ"ס|חומ״ס|hazardous[\s-]+materials|hazmat)/i,
      candidate_status: "EVALUATE_PER_JOB",
      candidate_evidence: "ניסיון תפעולי בגז טבעי (גז דליק בלחץ גבוה תחת פיקוח רשות הגז), ללא תעודת אחראי רעלים.",
      mandatory_for_roles: ["chemical_plant_operator"]
    },
    {
      id: "gate_asme_iso_standards",
      name_he: "תקני ASME / ISO",
      name_en: "ASME / ISO Engineering Standards",
      regex: /(?:asme(?:\s+b31\.[38])?|iso[\s-]+(?:9001|45001|14001|50001)|תקן[\s-]+איז(?:ו|״ו))/i,
      candidate_status: "FAMILIARITY",
      candidate_evidence: "עבודה בסביבת תפעול מפוקחת תחת נהלי איכות, בטיחות ותקני הולכת גז בינלאומיים.",
      mandatory_for_roles: ["qa_qc_engineer", "pipeline_inspector"]
    }
  ];

  const KEYWORD_TAXONOMY = {
    methodologies: {
      category_he: "מתודולוגיות תפעוליות",
      icon: "ph-duotone ph-tree-structure",
      color: "var(--dashboard-cyan)",
      terms: [
        { name: "Lean", pattern: /\blean\b|לין/i },
        { name: "Six Sigma", pattern: /six[\s-]sigma|שש[\s-]סיגמא/i },
        { name: "5S", pattern: /\b5s\b/i },
        { name: "RCA", pattern: /root[\s-]cause|חקר[\s-]תקלות|rca/i },
        { name: "Kaizen", pattern: /kaizen|קאיזן/i }
      ]
    },
    financials: {
      category_he: "ניהול תקציב והנדסה כלכלית",
      icon: "ph-duotone ph-currency-circle-dollar",
      color: "var(--dashboard-gold)",
      terms: [
        { name: "CAPEX", pattern: /\bcapex\b|תקציב[\s-]השקעות/i },
        { name: "OPEX", pattern: /\bopex\b|תקציב[\s-]תפעולי/i },
        { name: "ROI", pattern: /\broi\b|כדאיות[\s-]כלכלית/i },
        { name: "Procurement / רכש", pattern: /רכש[\s-]טכני|procurement/i }
      ]
    },
    systems: {
      category_he: "מערכות שליטה ואוטומציה",
      icon: "ph-duotone ph-cpu",
      color: "var(--dashboard-lime)",
      terms: [
        { name: "SCADA", pattern: /\bscada\b|סקאדה/i },
        { name: "PLC", pattern: /\bplc\b|בקר[\s-]מתוכנת/i },
        { name: "PRMS", pattern: /\bprms\b|תחנת[\s-]הפחתת[\s-]לחץ/i },
        { name: "HMI", pattern: /\bhmi\b|ממשק[\s-]מפעיל/i },
        { name: "DCS", pattern: /\bdcs\b/i },
        { name: "Modbus / Fieldbus", pattern: /modbus|profibus|fieldbus/i }
      ]
    },
    energy: {
      category_he: "תשתיות אנרגיה וחשמל",
      icon: "ph-duotone ph-lightning",
      color: "#a78bfa",
      terms: [
        { name: "BESS", pattern: /\bbess\b|אגירת[\s-]אנרגיה|אגירה[\s-]בסוללות/i },
        { name: "High Voltage", pattern: /מתח[\s-]גבוה|high[\s-]voltage|\bhv\b/i },
        { name: "Bifacial PV", pattern: /bifacial|דו[\s-]צדדי/i },
        { name: "Grid Connection", pattern: /חיבור[\s-]לרשת|grid[\s-]connection/i },
        { name: "FPSO", pattern: /\bfpso\b|אסדת[\s-]הפקה/i }
      ]
    }
  };

  const ATS_STRUCTURAL_RULES = [
    {
      rule_id: "ats_single_column",
      title_he: "מבנה עמודה יחידה (Single-Column Parsing)",
      description_he: "איסור על טבלאות מורכבות, תיבות טקסט מרחפות או טבלאות צדדיות הפוגעות בסדר הקריאה הלינארי של מערכות ATS ישנות (Taleo, Workday).",
      severity: "CRITICAL"
    },
    {
      rule_id: "ats_standard_fonts",
      title_he: "גופני מערכת סטנדרטיים (Standard Fonts)",
      description_he: "שימוש בלעדי בגופנים נתמכים (Arial, Calibri, Helvetica, Open Sans, Roboto, Rubik) המאפשרים פענוח OCR/טקסט תקין ללא שיבושי קידוד.",
      severity: "HIGH"
    },
    {
      rule_id: "ats_zero_emojis",
      title_he: "איסור מוחלט על אימוג'י (Zero-Emoji ATS Guard)",
      description_he: "אימוג'י בקו״ח גורם לקריסת מנועי סינון, שיבוש תווי יוניקוד וסימני שאלה או מחיקת פסקאות שלמות במערכות גיוס ישראליות.",
      severity: "CRITICAL"
    },
    {
      rule_id: "ats_contact_parseability",
      title_he: "תחביר פרטי התקשרות תקני",
      description_he: "פורמט טלפון ברור ללא תווים חריגים, כתובת מייל תקינה, וקישור לינקדאין ישיר ללא קיצורי קישורים בלתי מוכרים.",
      severity: "MEDIUM"
    }
  ];

  function evaluateHardGates(jobText, cvProfile) {
    if (!jobText || typeof jobText !== 'string' || !jobText.trim()) {
      return [];
    }
    const isCustom = cvProfile && cvProfile.text && cvProfile !== CANONICAL_CV_PROFILE;
    const results = [];
    STATUTORY_HARD_GATES.forEach(gate => {
      if (gate.regex.test(jobText)) {
        let status = gate.candidate_status;
        let evidence = gate.candidate_evidence;
        let note = gate.note_he || '';

        if (isCustom) {
          const cvText = cvProfile.text || '';
          if (gate.regex.test(cvText)) {
            status = 'PASS';
            evidence = 'הדרישה אותרה במסמך קורות החיים שהועלה.';
          } else {
            status = 'GAP';
            evidence = 'הדרישה לא אותרה במסמך קורות החיים שהועלה.';
          }
        } else {
          // Context-aware evaluation for B.Sc. Engineer gate (preference / advantage detection)
          if (gate.id === 'gate_degree_bsc_engineer') {
            const bscRegex = new RegExp(gate.regex.source, 'gi');
            let match;
            let isAdvantage = false;
            let hasExplicitMandatory = false;

            while ((match = bscRegex.exec(jobText)) !== null) {
              const preText = jobText.substring(Math.max(0, match.index - 60), match.index);
              const postText = jobText.substring(match.index + match[0].length, Math.min(jobText.length, match.index + match[0].length + 40));

              const clauseBefore = preText.split(/[\n,;]/).pop() || '';
              const clauseAfter = postText.split(/[\n,;]/)[0] || '';

              const hasPrefPre = /(?:יתרון(?:\s+משמעותי)?|עדיפות(?:\s+משמעותית)?|רצוי|advantage|preferred|preference)/i.test(clauseBefore);
              const hasPrefPost = /(?:יתרון(?:\s+משמעותי)?|עדיפות(?:\s+משמעותית)?|רצוי|advantage|preferred)/i.test(clauseAfter);

              const hasMandatory = /(?:חובה|דרישת[\s-]+סף|תנאי[\s-]+סף|דרישות[\s-]+סף|required|mandatory|must\s+have)/i.test(clauseBefore) ||
                                   /(?:חובה|בלבד|required|mandatory)/i.test(clauseAfter);

              if ((hasPrefPre || hasPrefPost) && !hasMandatory) {
                isAdvantage = true;
              } else if (hasMandatory) {
                hasExplicitMandatory = true;
              }
            }

            if (isAdvantage && !hasExplicitMandatory) {
              status = 'NOTICE';
              evidence = 'למועמד דיפלומת הנדסאי מכונות מוסמך; תואר מהנדס הוגדר במשרה כיתרון / עדיפות בלבד ולא כדרישת סף פוסלת.';
              note = 'דרישת יתרון — אינה מהווה פער סף פוסל (Hard Gate).';
            }
          }
        }

        results.push({
          id: gate.id,
          name: gate.name_he,
          name_he: gate.name_he,
          name_en: gate.name_en,
          status: status,
          evidence: evidence,
          note: note,
          mandatory_for_roles: gate.mandatory_for_roles || [],
          triggered: true
        });
      }
    });
    return results;
  }

  function extractMissingKeywords(jobText, cvProfile) {
    const result = {
      methodologies: [],
      financials: [],
      systems: [],
      energy: [],
      matched: {
        methodologies: [],
        financials: [],
        systems: [],
        energy: []
      },
      details: {
        methodologies: [],
        financials: [],
        systems: [],
        energy: []
      }
    };

    if (!jobText || typeof jobText !== 'string' || !jobText.trim()) {
      return result;
    }

    let cvText = '';
    if (typeof cvProfile === 'string') {
      cvText = cvProfile;
    } else if (cvProfile && typeof cvProfile === 'object') {
      cvText = [
        cvProfile.text || '',
        cvProfile.summary || '',
        ...(cvProfile.skills || []),
        ...(cvProfile.key_competencies || []),
        JSON.stringify(cvProfile)
      ].join(' ');
    } else {
      cvText = CANONICAL_CV_PROFILE.text;
    }

    Object.keys(KEYWORD_TAXONOMY).forEach(cat => {
      const catConfig = KEYWORD_TAXONOMY[cat];
      catConfig.terms.forEach(term => {
        if (term.pattern.test(jobText)) {
          const hasSkillInCv = Boolean(cvText && term.pattern.test(cvText));
          const itemDetail = {
            name: term.name,
            category: cat,
            category_he: catConfig.category_he,
            icon: catConfig.icon,
            color: catConfig.color,
            missing: !hasSkillInCv
          };

          if (hasSkillInCv) {
            result.matched[cat].push(term.name);
          } else {
            result[cat].push(term.name);
            result.details[cat].push(itemDetail);
          }
        }
      });
    });

    return result;
  }

  function checkAtsStructuralCompliance(cvElement) {
    let el = null;
    if (typeof cvElement === 'string') {
      if (typeof document !== 'undefined' && typeof document.querySelector === 'function') {
        el = document.querySelector(cvElement);
      }
    } else if (typeof HTMLElement !== 'undefined' && cvElement instanceof HTMLElement) {
      el = cvElement;
    } else if (cvElement && typeof cvElement === 'object' && cvElement.nodeType) {
      el = cvElement;
    } else if (typeof document !== 'undefined') {
      el = (typeof document.getElementById === 'function' && document.getElementById('careerStudioCvCanvas')) ||
           (typeof document.querySelector === 'function' && document.querySelector('.cv-container')) ||
           (typeof document.getElementById === 'function' && document.getElementById('careerStudioWorkspace')) || null;
    }

    const issues = [];
    const ruleResults = [];

    // Rule 1: Single column parsing
    let hasMultiColumns = false;
    if (el && typeof el.querySelectorAll === 'function') {
      const complexTables = el.querySelectorAll('table table, table[data-layout="multi-column"], .multi-column-layout');
      const floatingDivs = el.querySelectorAll('[style*="float: left"], [style*="float: right"]');
      if (complexTables && complexTables.length > 0) hasMultiColumns = true;
      if (floatingDivs && floatingDivs.length > 0) hasMultiColumns = true;
    }
    if (hasMultiColumns) {
      issues.push({
        rule_id: "ats_single_column",
        title_he: "מבנה עמודה יחידה (Single-Column Parsing)",
        severity: "CRITICAL",
        description_he: "זוהו טבלאות מורכבות או תיבות טקסט צפות העלולות לשבש קריאה ב-ATS."
      });
      ruleResults.push({ rule_id: "ats_single_column", passed: false, severity: "CRITICAL" });
    } else {
      ruleResults.push({ rule_id: "ats_single_column", passed: true, severity: "CRITICAL" });
    }

    // Rule 2: Standard fonts
    const standardFonts = ['arial', 'calibri', 'helvetica', 'open sans', 'roboto', 'rubik', 'sans-serif'];
    let fontSafe = true;
    if (el && typeof window !== 'undefined' && typeof window.getComputedStyle === 'function') {
      try {
        const computed = window.getComputedStyle(el);
        const ff = (computed && computed.fontFamily ? computed.fontFamily : '').toLowerCase();
        fontSafe = standardFonts.some(f => ff.includes(f));
      } catch(e) {
        fontSafe = true;
      }
    }
    if (!fontSafe) {
      issues.push({
        rule_id: "ats_standard_fonts",
        title_he: "גופני מערכת סטנדרטיים (Standard Fonts)",
        severity: "HIGH",
        description_he: "מומלץ להשתמש בגופני מערכת סטנדרטיים (Rubik, Arial, Calibri, Roboto)."
      });
      ruleResults.push({ rule_id: "ats_standard_fonts", passed: false, severity: "HIGH" });
    } else {
      ruleResults.push({ rule_id: "ats_standard_fonts", passed: true, severity: "HIGH" });
    }

    // Rule 3: Zero-Emoji ATS Guard
    const activeCv = (typeof getActiveCvProfile === 'function') ? getActiveCvProfile() : CANONICAL_CV_PROFILE;
    const contentText = (el && (el.innerText || el.textContent)) ? (el.innerText || el.textContent) : (activeCv.text || CANONICAL_CV_PROFILE.text);
    const emojiRegex = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{1F600}-\u{1F64F}\u{1F680}-\u{1F6FF}\u{FE0F}\u{20E3}]|&#(?:12\d{4}|x1[fF][0-9a-fA-F]{3});/u;
    const hasEmoji = emojiRegex.test(contentText);
    if (hasEmoji) {
      issues.push({
        rule_id: "ats_zero_emojis",
        title_he: "איסור מוחלט על אימוג'י (Zero-Emoji ATS Guard)",
        severity: "CRITICAL",
        description_he: "נמצאו אימוג'ים בתוכן קורות החיים; אימוג'ים עלולים לקרוס במנועי ATS ישראליים."
      });
      ruleResults.push({ rule_id: "ats_zero_emojis", passed: false, severity: "CRITICAL" });
    } else {
      ruleResults.push({ rule_id: "ats_zero_emojis", passed: true, severity: "CRITICAL" });
    }

    // Rule 4: Contact Parseability
    const phonePattern = /(?:05\d-?\d{3}-?\d{4}|05\d-?\d{7}|(?:\+?972-?5\d-?\d{7}))/;
    const emailPattern = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/;
    const hasValidPhone = phonePattern.test(contentText);
    const hasValidEmail = emailPattern.test(contentText);
    if (el && (!hasValidPhone || !hasValidEmail)) {
      issues.push({
        rule_id: "ats_contact_parseability",
        title_he: "תחביר פרטי התקשרות תקני",
        severity: "MEDIUM",
        description_he: "ודא שפרטי הטלפון והדוא\"ל מופיעים בפורמט קריא ומלא לקוראי ATS."
      });
      ruleResults.push({ rule_id: "ats_contact_parseability", passed: false, severity: "MEDIUM" });
    } else {
      ruleResults.push({ rule_id: "ats_contact_parseability", passed: true, severity: "MEDIUM" });
    }

    const isPassed = issues.length === 0;
    return {
      passed: isPassed,
      score: isPassed ? 100 : Math.max(0, 100 - issues.length * 25),
      rules_checked: ATS_STRUCTURAL_RULES.length,
      issues: issues,
      rule_results: ruleResults
    };
  }

  function runAtsJobMatching(jobText, cvProfile) {
    if (!jobText || typeof jobText !== 'string' || !jobText.trim()) {
      return {
        matchScore: 0,
        hardGates: [],
        missingKeywords: { methodologies: [], financials: [], systems: [], energy: [] },
        structuralCompliance: checkAtsStructuralCompliance(),
        matchedKeywords: { methodologies: [], financials: [], systems: [], energy: [] },
        summary: "לא הוזן תיאור משרה"
      };
    }

    const hardGates = evaluateHardGates(jobText, cvProfile);

    // Disjunctive & alternative qualification resolution
    const mechGate = hardGates.find(g => g.id === 'gate_practical_mech_eng');
    const bscGate = hardGates.find(g => g.id === 'gate_degree_bsc_engineer');

    if (mechGate && mechGate.status === 'PASS' && bscGate && bscGate.status === 'GAP') {
      const hasOrOrSlash = /(?:הנדסאי[^\n,.]*(?:[\/]|[\s]+או[\s]+|[\s]+or[\s]+)[^\n,.]*מהנדס|מהנדס[^\n,.]*(?:[\/]|[\s]+או[\s]+|[\s]+or[\s]+)[^\n,.]*הנדסאי|practical[^\n,.]*(?:[\/]|[\s]+or[\s]+)[^\n,.]*(?:b\.?sc|engineer)|(?:b\.?sc|engineer)[^\n,.]*(?:[\/]|[\s]+or[\s]+)[^\n,.]*practical)/i.test(jobText);

      const hasPracticalAsThreshold = /(?:(?:דריש(?:ת|ות)[\s-]+סף|תנאי[\s-]+סף|סף)[\s:,-]*[^\n,.]*הנדסאי|הנדסאי[^\n,.]*(?:דריש(?:ת|ות)[\s-]+סף|תנאי[\s-]+סף|הינו[\s-]+סף|הוא[\s-]+סף))/i.test(jobText);

      if (hasOrOrSlash || hasPracticalAsThreshold) {
        bscGate.status = 'NOTICE';
        bscGate.note = 'דרישה חלופית שהתמלאה באמצעות דיפלומת הנדסאי מכונות מוסמך (דרישת סף).';
        bscGate.evidence = 'למועמד דיפלומת הנדסאי מכונות מוסמך העונה על דרישת הסף / החלופה שהוגדרה במשרה.';
      }
    }

    const keywordResult = extractMissingKeywords(jobText, cvProfile);
    const structural = checkAtsStructuralCompliance();

    let score = 70;
    let hasCriticalGap = false;

    hardGates.forEach(g => {
      if (g.status === 'PASS') {
        score += 15;
      } else if (g.status === 'IN_PROGRESS') {
        score += 8;
      } else if (g.status === 'GAP') {
        score -= 30;
        hasCriticalGap = true;
      } else if (g.status === 'PASS_REFRESH_RECOMMENDED' || g.status === 'NOTICE') {
        score += 3;
      }
    });

    const totalMissing = (keywordResult.methodologies.length +
                          keywordResult.financials.length +
                          keywordResult.systems.length +
                          keywordResult.energy.length);
    const totalMatched = (keywordResult.matched.methodologies.length +
                          keywordResult.matched.financials.length +
                          keywordResult.matched.systems.length +
                          keywordResult.matched.energy.length);

    if (totalMissing + totalMatched > 0) {
      const keywordRatio = totalMatched / (totalMissing + totalMatched);
      score += Math.round((keywordRatio - 0.5) * 30);
    }

    if (!structural.passed) {
      score -= (structural.issues.length * 5);
    }

    if (hasCriticalGap) {
      score = Math.min(score, 55);
    }

    score = Math.max(0, Math.min(100, Math.round(score)));

    return {
      matchScore: score,
      hardGates: hardGates,
      missingKeywords: {
        methodologies: keywordResult.methodologies,
        financials: keywordResult.financials,
        systems: keywordResult.systems,
        energy: keywordResult.energy
      },
      structuralCompliance: structural,
      matchedKeywords: keywordResult.matched,
      summary: hasCriticalGap
        ? "זוהה פער סף סטטוטורי (Hard Gate GAP); נדרשת התאמה או בדיקת גמישות מעסיק"
        : (score >= 80 ? "התאמה גבוהה לדרישות התפקיד והסמכות המועמד" : "התאמה בינונית; מומלץ להשלים מילות מפתח")
    };
  }

  function generateCvBulletActionItem(keywordOrGate, jobContext = {}) {
    const term = String(keywordOrGate || '').trim().toLowerCase();
    const company = (jobContext && jobContext.company) ? jobContext.company : 'חברה תעשייתית';

    const bulletTemplates = {
      scada: {
        category: 'systems',
        label: 'SCADA / ממשקי בקרה',
        bulletHe: 'ניטור ובקרת תהליכי שרשרת אספקת גז טבעי 24/7 באמצעות מערכות SCADA וממשקי HMI, כולל תחקור תקלות תקשורת Modbus וספיקות בזמן אמת.',
        bulletEn: '24/7 monitoring and control of continuous natural gas flow operations using industrial SCADA and HMI systems, with real-time Modbus telemetry troubleshooting.'
      },
      plc: {
        category: 'systems',
        label: 'PLC / בקרים מתוכנתים',
        bulletHe: 'איתור תקלות וניטור אותות I/O מול בקרי PLC (Siemens/Rockwell) בסביבת מתקן אנרגיה רגיש, תוך סנכרון רציף עם מהנדסי אוטומציה.',
        bulletEn: 'Fault diagnosis and I/O signal monitoring on industrial PLCs (Siemens/Rockwell) at mission-critical energy facilities in continuous coordination with automation engineers.'
      },
      prms: {
        category: 'systems',
        label: 'PRMS / תחנות הפחתת לחץ',
        bulletHe: 'ניהול תפעולי של תחנות הפחתת לחץ ומדידה (PRMS) של גז טבעי בלחץ גבוה, תוך בקרת שסתומים, וויסות לחץ ועמידה קפדנית בתקני בטיחות סטטוטוריים.',
        bulletEn: 'Operational oversight of high-pressure Natural Gas Pressure Reduction and Metering Stations (PRMS), managing flow control and regulatory compliance.'
      },
      bess: {
        category: 'energy',
        label: 'BESS / אגירת אנרגיה',
        bulletHe: 'ניתוח הנדסי ותפעול מערכות אגירת אנרגיה (BESS) וסוללות ליתיום, תוך בקרה על פרופילי טעינה/פריקה, מערכות קירור וייצוב תדר רשת החשמל.',
        bulletEn: 'Operational analysis and integration of Battery Energy Storage Systems (BESS), overseeing charge/discharge profiles, thermal management, and grid stability.'
      },
      lean: {
        category: 'methodologies',
        label: 'Lean / מצוינות תפעולית',
        bulletHe: 'הטמעת עקרונות תפעול רזה (Lean) במשמרות בקרה, זיהוי צווארי בקבוק וקיצור זמני תגובה לתקלות שטח ב-25%.',
        bulletEn: 'Implemented Lean operational methods across dispatch shifts, eliminating workflow bottlenecks and reducing incident response time by 25%.'
      },
      '5s': {
        category: 'methodologies',
        label: '5S / ארגון ובטיחות סביבת עבודה',
        bulletHe: 'הטמעת מתודולוגיית 5S באזורי חדר בקרה ומחסני ציוד טכני, לשיפור הנגישות, מניעת תאונות עבודה וייעול שגרת האחזקה.',
        bulletEn: 'Rolled out 5S standardization across control centers and technical equipment storage, improving tool retrieval efficiency and workplace safety.'
      },
      rca: {
        category: 'methodologies',
        label: 'RCA / חקר תקלות שורש',
        bulletHe: 'הובלת תהליכי חקר סיבות שורש (Root Cause Analysis) בעקבות אירועי חריגת לחץ בגז, והגדרת פעולות מתקנות (CAPA) למניעת הישנות.',
        bulletEn: 'Conducted Root Cause Analysis (RCA) investigations on pressure surge events, formulating Corrective and Preventive Actions (CAPA).'
      },
      gate_certified_electrician: {
        category: 'statutory',
        label: 'חשמלאי מוסמך (בלימודים לקראת סיום)',
        bulletHe: 'לימודי חשמלאי מוסמך במרכז האקדמי רופין (סיום צפוי: 2026, כחודשיים לסיום) — שליטה מעמיקה בחוק החשמל, מעגלי פיקוד ותכנון לוחות מתח נמוך.',
        bulletEn: 'Certified Electrician coursework near completion at Ruppin Academic Center (expected 2026) — in-depth mastery of the Israeli Electricity Law and LV switchboard design.'
      }
    };

    let matched = bulletTemplates[term];
    if (!matched) {
      const foundKey = Object.keys(bulletTemplates).find(k => term.includes(k) || k.includes(term));
      if (foundKey) matched = bulletTemplates[foundKey];
    }

    if (matched) {
      return {
        keyword: keywordOrGate,
        category: matched.category,
        label: matched.label,
        bulletHe: matched.bulletHe,
        bulletEn: matched.bulletEn,
        actionLabel: `הוסף לניסיון תעסוקתי: "${matched.label}"`,
        tailoredContext: `מותאם לדרישות ${company}`
      };
    }

    const cleanTerm = keywordOrGate.replace(/gate_/g, '').replace(/_/g, ' ');
    return {
      keyword: keywordOrGate,
      category: 'general',
      label: cleanTerm,
      bulletHe: `שילוב והפעלת מערכות ${cleanTerm} במסגרת תפעול מתקני אנרגיה ובקרה רציפה, תוך עמידה בלוחות זמנים ונהלי בטיחות מחמירים.`,
      bulletEn: `Integrated and operated ${cleanTerm} systems in continuous energy and process control environments, ensuring strict regulatory compliance.`,
      actionLabel: `הוסף מילת מפתח לקו"ח: "${cleanTerm}"`,
      tailoredContext: `מותאם לדרישות ${company}`
    };
  }

  /* ATS UI Controller */
  let atsInputDebounceTimer = null;

  let atsEligibleJobs = [];

  function setAtsActiveStep(stepNum) {
    if (typeof document === 'undefined' || typeof document.getElementById !== 'function') return;
    const step1El = document.getElementById('atsStep1Panel');
    const step2El = document.getElementById('atsStep2Row');
    const head1 = document.getElementById('step-ats-1');
    const head2 = document.getElementById('step-ats-2');

    if (stepNum === 2) {
      if (step1El) step1El.classList.remove('studio-step-active-glow');
      if (head1) head1.classList.remove('active-step-head');
      if (step2El) step2El.classList.add('studio-step-active-glow');
      if (head2) head2.classList.add('active-step-head');
    } else {
      if (step2El) step2El.classList.remove('studio-step-active-glow');
      if (head2) head2.classList.remove('active-step-head');
      if (step1El) step1El.classList.add('studio-step-active-glow');
      if (head1) head1.classList.add('active-step-head');
    }
  }

  function populateAtsJobSelector() {
    if (typeof document === 'undefined' || typeof document.getElementById !== 'function') return;
    const sel = document.getElementById('atsJobSelector');
    if (!sel) return;
    const currentVal = sel.value;

    const allJobs = (typeof getAllAvailableJobs === 'function')
      ? getAllAvailableJobs()
      : (Array.isArray(rawJobsData) ? rawJobsData : (window.jobsData || []));

    // Filter only jobs that are currently starred or saved from jobs page, excluding rejected/purged
    atsEligibleJobs = (allJobs || []).filter(job => {
      if (!job) return false;
      const link = job.link || job.id;
      const state = (typeof getJobState === 'function')
        ? getJobState(link)
        : ((typeof jobStates !== 'undefined' && jobStates && jobStates[link]) || 'pending');
      if (state === 'rejected' || state === 'purged') return false;

      const isStarred = (typeof isJobStarred === 'function')
        ? isJobStarred(link)
        : Boolean(typeof starredJobs !== 'undefined' && starredJobs && starredJobs[link]);
      const isSaved = (state === 'saved');

      return isStarred || isSaved;
    });

    if (atsEligibleJobs.length === 0) {
      sel.innerHTML = '<option value="">-- אין משרות מסומנות בכוכב או שמורות כרגע (יש לסמן בלוח המשרות) --</option>';
      return;
    }

    sel.innerHTML = '<option value="">-- בחר משרה מתוך המשרות השמורות והמסומנות בכוכב (' + atsEligibleJobs.length + ') --</option>';
    atsEligibleJobs.forEach((job, idx) => {
      const opt = document.createElement('option');
      opt.value = String(idx);

      const link = job.link || job.id;
      const state = (typeof getJobState === 'function')
        ? getJobState(link)
        : ((typeof jobStates !== 'undefined' && jobStates && jobStates[link]) || 'pending');
      const isStarred = (typeof isJobStarred === 'function')
        ? isJobStarred(link)
        : Boolean(typeof starredJobs !== 'undefined' && starredJobs && starredJobs[link]);

      let tag = '';
      if (isStarred && state === 'saved') {
        tag = '[כוכב + שמורה]';
      } else if (isStarred) {
        tag = '[כוכב]';
      } else {
        tag = '[שמורה]';
      }

      const scoreTag = job.match_score ? `[${job.match_score}%]` : '';
      const prefix = [tag, scoreTag].filter(Boolean).join(' ');
      opt.textContent = `${prefix} ${job.title || 'ללא כותרת'} • ${job.company || 'חברה לא צוינה'}`;
      sel.appendChild(opt);
    });

    if (currentVal && atsEligibleJobs[parseInt(currentVal, 10)]) {
      sel.value = currentVal;
    }
  }

  function onAtsJobSelected(jobIndex) {
    if (jobIndex === '' || jobIndex === null || jobIndex === undefined) return;
    const pool = (Array.isArray(atsEligibleJobs) && atsEligibleJobs.length > 0)
      ? atsEligibleJobs
      : (Array.isArray(rawJobsData) ? rawJobsData : (window.jobsData || []));
    const idx = parseInt(jobIndex, 10);
    if (isNaN(idx) || !pool[idx]) return;
    const job = pool[idx];

    const parts = [
      job.title ? `כותרת משרה: ${job.title}` : '',
      job.company ? `חברה: ${job.company}` : '',
      job.company_requirements ? `דרישות התפקיד:\n${job.company_requirements}` : '',
      job.job_summary ? `תיאור התפקיד:\n${job.job_summary}` : '',
      job.snippet ? `פירוט נוסף:\n${job.snippet}` : '',
      job.experience_strengths ? `התאמה נדרשת:\n${job.experience_strengths}` : ''
    ].filter(Boolean).join('\n\n');

    const inputEl = document.getElementById('atsJobInput');
    if (inputEl) {
      inputEl.value = parts;
      triggerAtsMatching();
    }
  }

  function onAtsInputChanged() {
    if (atsInputDebounceTimer) clearTimeout(atsInputDebounceTimer);
    atsInputDebounceTimer = setTimeout(() => {
      triggerAtsMatching();
    }, 350);
  }

  function loadSampleAtsJob(type) {
    const inputEl = document.getElementById('atsJobInput');
    if (!inputEl) return;

    if (type === 'gas') {
      inputEl.value = `דרוש בקר גז טבעי ותפעול מתקני אנרגיה 24/7 בחברת אנרגיה מובילה.
דרישות התפקיד:
- הנדסאי מכונות מוסמך (חובה)
- שליטה מלאה במערכות בקרה SCADA ומתקני הפחתת לחץ ומדידה PRMS
- ניסיון בניהול בקשות Nomination ו-Re-nomination מול אסדת הפקה ימית (FPSO) ונתג״ז
- עבודה במשמרות לילה עצמאיות 24/7 וקבלת החלטות תחת לחץ
- שליטה ב-SAP וב-Excel, יתרון להיכרות עם תקני ASME ורציפות תפקודית`;
    } else if (type === 'solar') {
      inputEl.value = `דרוש מנהל פרויקטים סולאריים ומערכות אגירת אנרגיה BESS לחברת אנרגיה מתחדשת.
דרישות התפקיד:
- הנדסאי מכונות עם התמחות באנרגיות מתחדשות או בוגר לימודי חשמל
- רישיון חשמלאי מוסמך (או בלימודים לקראת סיום הרישיון)
- ניסיון בהקמת שדות סולאריים ופאנלים Bifacial PV מסחריים
- הדרכת עבודה בגובה בתוקף
- היכרות עם מתח גבוה (High Voltage) וחיבור לרשת החשמל`;
    } else if (type === 'bsc_gap') {
      inputEl.value = `דרוש מהנדס מכונות ראשי (Senior Mechanical R&D Engineer) למפעל תעשייתי.
דרישות סף חובה:
- תואר ראשון בהנדסת מכונות (B.Sc בלבד ממוסד אקדמי מוכר - לא הנדסאי)
- ניסיון מוכח במתודולוגיות Lean ו-Six Sigma
- ניהול תקציבי CAPEX ו-OPEX בהיקף נרחב
- הסמכת ממונה בטיחות בעבודה מוסמך מטעם משרד העבודה`;
    }

    triggerAtsMatching();
  }

  function clearAtsInput() {
    const inputEl = document.getElementById('atsJobInput');
    if (inputEl) inputEl.value = '';
    const sel = document.getElementById('atsJobSelector');
    if (sel) sel.value = '';
    triggerAtsMatching();
    setAtsActiveStep(1);
  }

  function triggerAtsMatching() {
    const inputEl = document.getElementById('atsJobInput');
    const jobText = inputEl ? inputEl.value : '';

    const report = runAtsJobMatching(jobText, getActiveCvProfile());

    // Update Percentage Match Gauge
    const scoreValEl = document.getElementById('atsScoreValue');
    const progressEl = document.getElementById('atsGaugeProgress');
    const badgeEl = document.getElementById('atsMatchBadge');
    const badgeTextEl = document.getElementById('atsMatchBadgeText');
    const descEl = document.getElementById('atsScoreDescription');

    const score = report.matchScore;
    if (scoreValEl) scoreValEl.textContent = score + '%';

    if (progressEl) {
      const circ = 314.159;
      const offset = circ - (score / 100) * circ;
      progressEl.style.strokeDashoffset = offset;
      if (score >= 80) {
        progressEl.style.stroke = 'var(--dashboard-lime)';
      } else if (score >= 65) {
        progressEl.style.stroke = 'var(--dashboard-cyan)';
      } else if (score >= 50) {
        progressEl.style.stroke = 'var(--dashboard-gold)';
      } else {
        progressEl.style.stroke = '#f87171';
      }
    }

    if (badgeEl && badgeTextEl) {
      badgeEl.className = 'ats-match-level-badge';
      if (!jobText.trim()) {
        badgeEl.classList.add('level-neutral');
        badgeTextEl.textContent = 'טרם נותחה משרה';
      } else if (score >= 80) {
        badgeEl.classList.add('level-high');
        badgeTextEl.textContent = 'התאמה גבוהה (High Match)';
      } else if (score >= 60) {
        badgeEl.classList.add('level-med');
        badgeTextEl.textContent = 'התאמה טובה (Good Match)';
      } else if (score >= 45) {
        badgeEl.classList.add('level-fair');
        badgeTextEl.textContent = 'התאמה בינונית / חלקית';
      } else {
        badgeEl.classList.add('level-gap');
        badgeTextEl.textContent = 'פער סף / התאמה נמוכה';
      }
    }

    if (descEl) {
      descEl.textContent = jobText.trim() ? report.summary : 'הזן תיאור משרה להפקת ציון התאמה משוקלל המבוסס על שערי סף סטטוטוריים, מילות מפתח ומבנה קו״ח.';
    }

    // Update KPIs
    const kpiGates = document.getElementById('atsKpiGates');
    if (kpiGates) {
      kpiGates.textContent = `${report.hardGates.length} / 7`;
    }

    const totalMissing = (report.missingKeywords.methodologies.length +
                          report.missingKeywords.financials.length +
                          report.missingKeywords.systems.length +
                          report.missingKeywords.energy.length);
    const kpiKeywords = document.getElementById('atsKpiKeywords');
    if (kpiKeywords) {
      kpiKeywords.textContent = String(totalMissing);
    }

    const kpiStructural = document.getElementById('atsKpiStructural');
    if (kpiStructural) {
      kpiStructural.textContent = report.structuralCompliance.score + '%';
    }

    const gatesSummaryBadge = document.getElementById('atsGatesSummaryBadge');
    if (gatesSummaryBadge) {
      gatesSummaryBadge.textContent = `${report.hardGates.length} שערים זוהו במשרה`;
    }

    const keywordsBadge = document.getElementById('atsKeywordsCountBadge');
    if (keywordsBadge) {
      keywordsBadge.textContent = `${totalMissing} פערי מפתח`;
    }

    // Render Subcards
    renderHardGates(report.hardGates, jobText);
    renderKeywordTaxonomy(report.missingKeywords, report.matchedKeywords, jobText);
    renderAtsStructuralChecklist(report.structuralCompliance);

    // Progressive step subtle glow transition
    if (jobText && jobText.trim()) {
      setAtsActiveStep(2);
    } else {
      setAtsActiveStep(1);
    }
  }

  function renderHardGates(triggeredGates, jobText) {
    const listEl = document.getElementById('atsHardGatesList');
    if (!listEl) return;

    let html = '';
    STATUTORY_HARD_GATES.forEach(gate => {
      const activeMatch = (triggeredGates || []).find(g => g.id === gate.id);
      const isTriggered = Boolean(activeMatch);
      const status = activeMatch ? activeMatch.status : gate.candidate_status;
      const evidence = activeMatch ? activeMatch.evidence : gate.candidate_evidence;
      const note = activeMatch ? activeMatch.note : (gate.note_he || '');
      let badgeClass = 'badge-notice';
      let statusLabel = 'לתשומת לב / NOTICE';
      let statusIcon = 'ph-info';

      if (status === 'PASS') {
        badgeClass = 'badge-pass';
        statusLabel = 'תואם מלא / PASS';
        statusIcon = 'ph-check-circle';
      } else if (status === 'IN_PROGRESS') {
        badgeClass = 'badge-in-progress';
        statusLabel = 'במהלך לימודים / IN_PROGRESS';
        statusIcon = 'ph-clock';
      } else if (status === 'GAP') {
        badgeClass = 'badge-gap';
        statusLabel = 'פער סף / GAP';
        statusIcon = 'ph-x-circle';
      } else if (status === 'PASS_REFRESH_RECOMMENDED') {
        badgeClass = 'badge-notice';
        statusLabel = 'רענון שנתי נדרש';
        statusIcon = 'ph-warning';
      } else if (status === 'EVALUATE_PER_JOB') {
        badgeClass = 'badge-notice';
        statusLabel = 'בדיקה פרטנית לפי אתר';
        statusIcon = 'ph-scales';
      } else if (status === 'FAMILIARITY') {
        badgeClass = 'badge-notice';
        statusLabel = 'היכרות מעשית';
        statusIcon = 'ph-info';
      } else if (status === 'NOTICE') {
        badgeClass = 'badge-notice';
        statusLabel = 'יתרון / לתשומת לב';
        statusIcon = 'ph-info';
      }

      const rowClass = `ats-gate-row ${isTriggered ? 'is-triggered' : ''} ${isTriggered && status === 'GAP' ? 'is-gap' : ''}`;

      html += `
        <div class="${rowClass}">
          <div class="ats-gate-main">
            <div class="ats-gate-name-wrap">
              <i class="ph-duotone ${status === 'PASS' ? 'ph-shield-check' : (status === 'GAP' ? 'ph-warning-octagon' : 'ph-shield')}"></i>
              <div>
                <span class="ats-gate-name">${gate.name_he}</span>
                <span class="ats-gate-subname">(${gate.name_en})</span>
              </div>
            </div>
            <div class="ats-gate-badges">
              ${isTriggered 
                ? '<span class="ats-badge-trigger active"><i class="ph-bold ph-crosshair"></i> נדרש במשרה זו</span>' 
                : '<span class="ats-badge-trigger"><i class="ph-bold ph-minus"></i> לא צוין במשרה</span>'}
              <span class="ats-badge-status ${badgeClass}">
                <i class="ph-bold ${statusIcon}"></i>
                <span>${statusLabel}</span>
              </span>
            </div>
          </div>
          <div class="ats-gate-evidence">
            <strong>ראיות מועמד:</strong> ${evidence}
          </div>
          ${note ? `<div class="ats-gate-note"><i class="ph-duotone ph-warning"></i> ${note}</div>` : ''}
        </div>
      `;
    });

    listEl.innerHTML = html;
  }

  function renderKeywordTaxonomy(missing, matched, jobText) {
    const cats = ['methodologies', 'financials', 'systems', 'energy'];
    cats.forEach(cat => {
      const cap = cat.charAt(0).toUpperCase() + cat.slice(1);
      const wrapEl = document.getElementById('atsKeywords' + cap);
      if (!wrapEl) return;

      const missingList = (missing && missing[cat]) || [];
      const matchedList = (matched && matched[cat]) || [];

      if (!jobText.trim() || (missingList.length === 0 && matchedList.length === 0)) {
        wrapEl.innerHTML = '<span class="ats-empty-tag">לא נדרשו מונחים מקטגוריה זו במשרה</span>';
        return;
      }

      let html = '';
      missingList.forEach(term => {
        html += `
          <span class="ats-keyword-tag missing" title="מונח חסר בקו״ח - מומלץ להוסיף">
            <i class="ph-bold ph-warning-circle"></i>
            <span>${term}</span>
          </span>
        `;
      });

      matchedList.forEach(term => {
        html += `
          <span class="ats-keyword-tag matched" title="מונח קיים ומתועד בקו״ח של עידו גל">
            <i class="ph-bold ph-check"></i>
            <span>${term}</span>
          </span>
        `;
      });

      wrapEl.innerHTML = html;
    });
  }

  function renderAtsStructuralChecklist(structuralReport) {
    const listEl = document.getElementById('atsRulesChecklist');
    if (!listEl) return;

    const rep = structuralReport || checkAtsStructuralCompliance();
    const resultsMap = {};
    (rep.rule_results || []).forEach(r => { resultsMap[r.rule_id] = r; });

    let html = '';
    ATS_STRUCTURAL_RULES.forEach(rule => {
      const res = resultsMap[rule.rule_id] || { passed: true };
      const isPass = Boolean(res.passed);

      html += `
        <div class="ats-rule-item ${isPass ? 'rule-pass' : 'rule-fail'}">
          <div class="ats-rule-icon ${isPass ? 'pass' : 'fail'}">
            <i class="ph-bold ${isPass ? 'ph-check' : 'ph-x'}"></i>
          </div>
          <div class="ats-rule-info">
            <div class="ats-rule-title-row">
              <span class="ats-rule-title">${rule.title_he}</span>
              <span class="ats-card-badge ${isPass ? 'status-pass' : ''}">
                ${isPass ? 'תואם תקן' : 'דורש תיקון (' + rule.severity + ')'}
              </span>
            </div>
            <p class="ats-rule-desc">${rule.description_he}</p>
          </div>
        </div>
      `;
    });

    listEl.innerHTML = html;

    const statusBadge = document.getElementById('atsStructuralStatusBadge');
    if (statusBadge) {
      if (rep.passed) {
        statusBadge.className = 'ats-card-badge status-pass';
        statusBadge.innerHTML = '<i class="ph-duotone ph-shield-check"></i> <span>תואם מלא (0 בעיות)</span>';
      } else {
        statusBadge.className = 'ats-card-badge';
        statusBadge.style.background = 'rgba(248,113,113,0.15)';
        statusBadge.style.color = '#fca5a5';
        statusBadge.style.borderColor = 'rgba(248,113,113,0.35)';
        statusBadge.innerHTML = `<i class="ph-duotone ph-warning"></i> <span>${rep.issues.length} התראות מבנה</span>`;
      }
    }
  }

  let atsInitialized = false;
  function initAtsModule() {
    if (typeof document === 'undefined' || typeof document.getElementById !== 'function') return;
    if (!document.getElementById('atsModuleContent') && !document.getElementById('atsJobSelector')) return;
    populateAtsJobSelector();
    const hasJobInput = Boolean(document.getElementById('atsJobInput')?.value?.trim());
    setAtsActiveStep(hasJobInput ? 2 : 1);
    if (!atsInitialized) {
      renderHardGates([], '');
      renderKeywordTaxonomy({ methodologies: [], financials: [], systems: [], energy: [] }, { methodologies: [], financials: [], systems: [], energy: [] }, '');
      renderAtsStructuralChecklist(checkAtsStructuralCompliance());
      atsInitialized = true;
    }
  }

  /* ==========================================================================
     CAREER STUDIO: MILESTONE 3 - AI WRITER, 3-MODE TONE SWITCHER & INDUSTRIAL TERMINOLOGY ENGINE
     ========================================================================== */

  const TONE_SWITCHER_PROFILES = {
    technical: {
      id: "technical",
      label_he: "הנדסי / טכני",
      icon: "ph-gear-six",
      description_he: "מיקוד בפרמטרים הנדסיים, לחצים, ספיקות, חוק החשמל, יעילות תרמודינמית, כיול ומכשור.",
      active_verbs: ["ניטרתי", "כיַילתי", "חישבתי", "ניתחתי", "אפיינתי", "התקנתי"],
      active_verbs_en: ["Monitored", "Calibrated", "Calculated", "Analyzed", "Engineered", "Installed"],
      bullet_transformation_formula: "[פועל הנדסי פעיל] + [מערכת/פרמטר טכני מדויק] + [תוצאה הנדסית כמותית/תקן]",
      example_before: "עבדתי במשמרות בניטור גז ודאגתי שלא יהיו תקלות.",
      example_after: "ניטרתי באופן רציף לחצי צנרת וספיקות גז במערך של 10+ תחנות PRMS, תוך זיהוי מיידי של סטיות לחץ מתחת ל-45 bar ומניעת תקלות הולכה."
    },
    operational: {
      id: "operational",
      label_he: "תפעולי / סמכות שטח",
      icon: "ph-shield-check",
      description_he: "מיקוד במשמרות 24/7, תגובה לחירום, ניהול משמרת לילה עצמאית, אפס השבתה ואכיפת בטיחות.",
      active_verbs: ["הובלתי", "תפעלתי", "ניהלתי", "בלמתי", "אכפתי", "הכרעתי"],
      active_verbs_en: ["Spearheaded", "Operated", "Managed", "Mitigated", "Enforced", "Resolved"],
      bullet_transformation_formula: "[פועל פיקודי/תפעולי] + [תרחיש/מערך 24/7 בשטח] + [מדד בטיחות/רציפות תפקודית 100%]",
      example_before: "הייתי אחראי על המשמרת בלילה ב-Energean.",
      example_after: "שימשתי כגורם תפעולי עצמאי יחיד במשמרות לילה 24/7 במתקן אנרגיה רגיש, תוך ניהול תרחישי חירום וקבלת החלטות מהירות עם 100% רציפות אספקה ואפס תאונות LTI."
    },
    strategic: {
      id: "strategic",
      label_he: "אסטרטגי / ניהולי",
      icon: "ph-trend-up",
      description_he: "מיקוד בממשקים רב-מערכתיים (אסדה ימית, נתג״ז, לקוחות קצה), אופטימיזציית אספקה והכשרת צוותים בינלאומיים.",
      active_verbs: ["סנכרנתי", "תיאמתי", "ייעלתי", "הכשרתי", "הטמעתי", "ניהלתי"],
      active_verbs_en: ["Synchronized", "Coordinated", "Streamlined", "Trained", "Implemented", "Directed"],
      bullet_transformation_formula: "[פועל מערכתי] + [ממשק בין-ארגוני/צוותי] + [השפעה עסקית, חיסכון או שיפור תהליך]",
      example_before: "עשיתי נומינציות ודיברתי עם חברת החשמל ונתג״ז.",
      example_after: "סנכרנתי באופן שוטף בקשות נומינציה מורכבות מול אסדת ההפקה הימית ונתג״ז, תוך הבטחת התאמה מלאה של 100% בין יכולת ההפקה לדרישות הלקוחות המסחריים ותחנות הכוח."
    }
  };

  const ENERGY_DICTIONARY = [
    {
      term_en: "PRMS (Pressure Reduction and Metering Station)",
      term_he: "תחנת הפחתת לחץ ומדידה (PRMS)",
      acronym: "PRMS",
      category: "gas",
      category_he: "גז טבעי",
      description_he: "מתקן להפחתת לחץ הגז הטבעי מצנרת הולכה (כ-65-80 bar) ללחץ חלוקה/צריכה ומדידה פיסקאלית מדויקת.",
      snippet: "תחנות PRMS (הפחתת לחץ ומדידה)"
    },
    {
      term_en: "Nomination / Re-nomination",
      term_he: "בקשת הקצאת גז יומית ועדכון כמויות (נומינציה)",
      acronym: "Nomination",
      category: "gas",
      category_he: "גז טבעי",
      description_he: "תהליך מסחרי-תפעולי יומי לתזמון כמויות גז בין צרכנים, ספקים ורשת ההולכה הארצית.",
      snippet: "בקשות Nomination ו-Re-nomination מסחריות"
    },
    {
      term_en: "FPSO (Floating Production Storage and Offloading)",
      term_he: "אסדת הפקה, אחסון ופריקה צפה (FPSO)",
      acronym: "FPSO",
      category: "gas",
      category_he: "גז טבעי",
      description_he: "אסדה צפה לטיפול בגז וקונדנסט בלב ים והזרמתו לצנרת החוף.",
      snippet: "ממשק תפעולי מול אסדת הפקה ימית (FPSO)"
    },
    {
      term_en: "INGL (Israel Natural Gas Lines)",
      term_he: "נתג״ז (נתיבי הגז הטבעי לישראל)",
      acronym: "INGL",
      category: "gas",
      category_he: "גז טבעי",
      description_he: "החברה הממשלתית האחראית על רשת ההולכה הארצית של גז טבעי בלחץ גבוה.",
      snippet: "תיאום הזרמה וממשקי לחץ מול נתג״ז"
    },
    {
      term_en: "SCADA (Supervisory Control and Data Acquisition)",
      term_he: "מערכת פיקוח, שליטה ורכישת נתונים (סקאדה)",
      acronym: "SCADA",
      category: "automation",
      category_he: "אוטומציה ובקרה",
      description_he: "ארכיטקטורת בקרה תעשייתית לניטור ופיקוח בזמן אמת על תהליכים, חיישנים ושסתומים.",
      snippet: "מערכת SCADA תעשייתית לניטור 24/7"
    },
    {
      term_en: "PLC (Programmable Logic Controller)",
      term_he: "בקר לוגי מתוכנת (PLC)",
      acronym: "PLC",
      category: "automation",
      category_he: "אוטומציה ובקרה",
      description_he: "מחשב תעשייתי מוקשח לתפעול ובקרה אוטומטית של מכונות, משאבות ומערכות חירום.",
      snippet: "בקרי PLC ומערכי I/O תעשייתיים"
    },
    {
      term_en: "HMI (Human-Machine Interface)",
      term_he: "ממשק אדם-מכונה (HMI)",
      acronym: "HMI",
      category: "automation",
      category_he: "אוטומציה ובקרה",
      description_he: "מסכי תצוגה גרפיים בחדרי בקרה המאפשרים למפעיל לקבל תמונת מצב ולשלוח פקודות למתקן.",
      snippet: "מסכי HMI ולוחות פיקוד ובקרה"
    },
    {
      term_en: "Bifacial PV Solar Panels",
      term_he: "פאנלים סולאריים פוטו-וולטאיים דו-צדדיים (Bifacial)",
      acronym: "Bifacial PV",
      category: "renewables",
      category_he: "אנרגיה מתחדשת",
      description_he: "טכנולוגיה סולארית הקולטת קרינת שמש ישירה מקדימה וקרינה מוחזרת (אלבדו) מאחור לתוספת תפוקה של 10%-25%.",
      snippet: "מערכות סולאריות Bifacial PV בעלות ניצולת גבוהה"
    },
    {
      term_en: "Monofacial PV Solar Panels",
      term_he: "פאנלים סולאריים חד-צדדיים (Monofacial)",
      acronym: "Monofacial PV",
      category: "renewables",
      category_he: "אנרגיה מתחדשת",
      description_he: "קולטים סולאריים סטנדרטיים הקולטים קרינה מהצד העליון בלבד.",
      snippet: "מערכי Monofacial PV מסורתיים"
    },
    {
      term_en: "BESS (Battery Energy Storage Systems)",
      term_he: "מערכות אגירת אנרגיה בסוללות (BESS)",
      acronym: "BESS",
      category: "renewables",
      category_he: "אנרגיה מתחדשת",
      description_he: "מתקני אגירה מבוססי סוללות ליתיום לייצוב רשת החשמל, ויסות שיאי ביקוש (Peak Shaving) ואגירת אנרגיה סולארית.",
      snippet: "מתקני אגירת אנרגיה בסוללות (BESS)"
    },
    {
      term_en: "Inverter",
      term_he: "ממיר מתח סולארי (Inverter)",
      acronym: "Inverter",
      category: "electrical",
      category_he: "חשמל",
      description_he: "רכיב אלקטרוניקת הספק הממיר זרם ישר (DC) מהפאנלים הסולאריים לזרם חילופין (AC) המסונכרן לרשת החשמל.",
      snippet: "ממירי מתח סולאריים מרכזיים ומבוזרים (String Inverters)"
    },
    {
      term_en: "Transformer",
      term_he: "שנאי מתח (Transformer)",
      acronym: "Transformer",
      category: "electrical",
      category_he: "חשמל",
      description_he: "מכשיר אלקטרומגנטי להעלאת או הורדת מתח חשמלי לצורך חיבור לרשת ההולכה והחלוקה.",
      snippet: "שנאי מתח גבוה להזנת רשת"
    },
    {
      term_en: "High Voltage (HV)",
      term_he: "מתח גבוה (מתקני חשמל מעל 1,000V)",
      acronym: "HV",
      category: "electrical",
      category_he: "חשמל",
      description_he: "מערכות ומתקני חשמל הפועלים במתח העולה על 1,000 וולט AC לפי חוק החשמל ותקנות הבטיחות.",
      snippet: "מערכות מתח גבוה (High Voltage)"
    },
    {
      term_en: "Low Voltage (LV)",
      term_he: "מתח נמוך (חוק החשמל)",
      acronym: "LV",
      category: "electrical",
      category_he: "חשמל",
      description_he: "מתקני חשמל הפועלים עד 1,000 וולט AC, תחום הליבה של רישיון חשמלאי מוסמך.",
      snippet: "לוחות ורשתות מתח נמוך לפי חוק החשמל"
    },
    {
      term_en: "LTI (Lost Time Incident)",
      term_he: "תאונת עבודה עם אובדן ימי עבודה (מדד בטיחות LTI)",
      acronym: "LTI",
      category: "safety",
      category_he: "בטיחות ו-HSE",
      description_he: "מדד בטיחות בינלאומי מוביל (Zero LTI) המודד אירועי פציעה שגרמו להיעדרות מעבודה.",
      snippet: "עמידה ביעד בטיחות של 0 תאונות LTI"
    },
    {
      term_en: "Zero Harm / Zero Incidents",
      term_he: "אפס תקריות בטיחות ורציפות תפקודית",
      acronym: "Zero Harm",
      category: "safety",
      category_he: "בטיחות ו-HSE",
      description_he: "תפיסת תרבות בטיחות תעשייתית השואפת לאפס פגיעות בחיי אדם, בסביבה ובמתקן.",
      snippet: "הובלת תרבות בטיחות ואפס אירועים (Zero Harm)"
    },
    {
      term_en: "ESD (Emergency Shutdown System)",
      term_he: "מערכת השבתת חירום אוטומטית (ESD)",
      acronym: "ESD",
      category: "safety",
      category_he: "בטיחות ו-HSE",
      description_he: "מערך בטיחות בלתי תלוי לסגירת מגופי חירום ובידוד מקטעי צנרת במקרה של דליפה או זינוק לחץ.",
      snippet: "מערכות השבתת חירום (ESD) ובלימת תקלות"
    },
    {
      term_en: "Telemetry",
      term_he: "טלמטריה (שידור נתוני חיישנים בזמן אמת)",
      acronym: "Telemetry",
      category: "automation",
      category_he: "אוטומציה ובקרה",
      description_he: "מערך איסוף ושידור נתוני מדידה מחיישני שטח (לחץ, טמפרטורה, ספיקה) לעמדת הפיקוח המרכזית.",
      snippet: "ערוצי טלמטריה ושידור נתוני שטח בזמן אמת"
    },
    {
      term_en: "LOTO (Lockout / Tagout)",
      term_he: "נעילה ותיוג בטיחותי (LOTO)",
      acronym: "LOTO",
      category: "safety",
      category_he: "בטיחות ו-HSE",
      description_he: "נוהל בטיחות מחייב לבידוד אנרגיה מכנית וחשמלית בעת טיפול ותחזוקת ציוד מסוכן.",
      snippet: "אכיפת נוהל נעילה ותיוג (LOTO) קפדני"
    },
    {
      term_en: "DCS (Distributed Control System)",
      term_he: "מערכת בקרה מבוזרת (DCS)",
      acronym: "DCS",
      category: "automation",
      category_he: "אוטומציה ובקרה",
      description_he: "מערכת בקרה מרובת לולאות עם בקרים מבוזרים ייעודיים לתהליכים תעשייתיים רציפים.",
      snippet: "אינטגרציה וניטור במערכות בקרה מבוזרות (DCS)"
    }
  ];

  function searchEnergyDictionary(query, category) {
    const q = (query || '').trim().toLowerCase();
    const cat = (category || 'all').trim().toLowerCase();

    return ENERGY_DICTIONARY.filter(item => {
      const matchCat = (cat === 'all' || item.category.toLowerCase() === cat);
      if (!matchCat) return false;
      if (!q) return true;

      return (
        item.term_en.toLowerCase().includes(q) ||
        item.term_he.toLowerCase().includes(q) ||
        item.acronym.toLowerCase().includes(q) ||
        item.description_he.toLowerCase().includes(q)
      );
    });
  }

  function transformBulletTone(rawBullet, toneMode) {
    const raw = (rawBullet || '').trim();
    if (!raw) return '';

    const mode = (toneMode || 'technical').toLowerCase();

    // Check for standard presets from domain specifications
    const isGasMonitorPreset = /(?:עבדתי\s+במשמרות\s+בניטור\s+גז|ניטור\s+גז\s+ודאגתי)/i.test(raw);
    const isNightShiftPreset = /(?:הייתי\s+אחראי\s+על\s+המשמרת\s+בלילה|משמרת\s+בלילה\s+ב-Energean|משמרת\s+בלילה)/i.test(raw);
    const isNominationPreset = /(?:עשיתי\s+נומינציות|דיברתי\s+עם\s+חברת\s+החשמל\s+ונתג״ז|נומינציות\s+ונתג״ז)/i.test(raw);
    const isSolarPvPreset = /(?:טיפלתי\s+במערכות\s+סולאריות|התקנתי\s+פאנלים|פאנלים\s+סולאריים)/i.test(raw);

    // English presets
    const isEnNightShiftPreset = /(?:responsible\s+for\s+night\s+shifts|monitored\s+gas\s+pressures)/i.test(raw);

    if (isGasMonitorPreset) {
      if (mode === 'technical') {
        return "ניטרתי באופן רציף לחצי צנרת וספיקות גז במערך של 10+ תחנות PRMS, תוך זיהוי מיידי של סטיות לחץ מתחת ל-45 bar ומניעת תקלות הולכה.";
      } else if (mode === 'operational') {
        return "תפעלתי באופן רציף משמרות בקרה 24/7 במערך תחנות PRMS, תוך בלימת אירועי לחץ חריגים והבטחת 100% רציפות אספקה ללא תקלות.";
      } else {
        return "תיאמתי באופן שוטף ממשקי הולכת גז וניטור ספיקות מול נתג״ז ואסדת ההפקה, תוך הבטחת אספקה רציפה ומדויקת ללקוחות הקצה.";
      }
    }

    if (isNightShiftPreset) {
      if (mode === 'operational') {
        return "שימשתי כגורם תפעולי עצמאי יחיד במשמרות לילה 24/7 במתקן אנרגיה רגיש, תוך ניהול תרחישי חירום וקבלת החלטות מהירות עם 100% רציפות אספקה ואפס תאונות LTI.";
      } else if (mode === 'technical') {
        return "ניטרתי באופן רציף לחצים וספיקות במשמרות לילה עצמאיות 24/7 במתקן אנרגיה רגיש, תוך כיול פרמטרים הנדסיים ושמירה על יציבות הידראולית מלאה.";
      } else {
        return "ניהלתי תיאומים רב-ממשקיים מורכבים במשמרות לילה עצמאיות 24/7 מול אסדת ההפקה הימית ונתג״ז, תוך מניעת צווארי בקבוק באספקת הגז.";
      }
    }

    if (isNominationPreset) {
      if (mode === 'strategic') {
        return "סנכרנתי באופן שוטף בקשות נומינציה מורכבות מול אסדת ההפקה הימית ונתג״ז, תוך הבטחת התאמה מלאה של 100% בין יכולת ההפקה לדרישות הלקוחות המסחריים ותחנות הכוח.";
      } else if (mode === 'technical') {
        return "חישבתי וניתחתי כמויות נומינציה שעתית ויומית במערכות SCADA, תוך אופטימיזציית לחצי הזרמה בצנרת והפחתת סטיות מדידה מתחת ל-0.5%.";
      } else {
        return "תפעלתי את תהליכי ה-Nomination וה-Re-nomination תחת לוחות זמנים מבצעיים הדוקים, תוך מניעת קנסות חריגה ושמירה על 100% רציפות אספקה.";
      }
    }

    if (isSolarPvPreset) {
      if (mode === 'technical') {
        return "אפיינתי וכיַילתי מערכי פאנלים סולאריים מתקדמים מסוג Bifacial PV וממירי מתח, תוך השגת תוספת נצילות שנתית של מעל 22% ועמידה מלאה בחוק החשמל.";
      } else if (mode === 'operational') {
        return "הובלתי התקנות שטח מורכבות של מערכי פאנלים סולאריים וממירי מתח, תוך הקפדה מחמירה על נהלי עבודה בגובה ואפס תאונות בטיחות.";
      } else {
        return "ייעלתי תהליכי הקמה ותפעול של שדות סולאריים מסחריים (Bifacial PV), תוך סנכרון ממשקי קבלנים וחיבור מוצלח לרשת החשמל הארצית.";
      }
    }

    if (isEnNightShiftPreset) {
      if (mode === 'operational') {
        return "Spearheaded 24/7 solo night shift operations at a mission-critical energy facility, mitigating emergency scenarios and securing 100% supply continuity with 0 LTI incidents.";
      } else if (mode === 'technical') {
        return "Monitored pipeline pressures and flow rates across 10+ PRMS stations via SCADA, detecting pressure deviations below 45 bar and preventing transit faults.";
      } else {
        return "Synchronized cross-functional operations between offshore FPSO and the national gas grid (INGL), maintaining 100% nomination compliance.";
      }
    }

    // Dynamic transformation for arbitrary input:
    const isEnglish = /^[A-Za-z0-9\s.,;:'"()\-–—/%]+$/.test(raw);

    // Strip passive phrases
    let cleaned = raw;
    if (isEnglish) {
      cleaned = cleaned.replace(/^(?:I\s+was\s+responsible\s+for|responsible\s+for|worked\s+(?:on|with|at)|handled|took\s+part\s+in|helped\s+with|assisted\s+in)\s*/i, '');
    } else {
      cleaned = cleaned.replace(/^(?:הייתי\s+אחראי(?:\s+על|\s+ל)?|עבדתי\s+(?:ב|עם)|עשיתי|טיפלתי\s+ב|אחראי\s+(?:על|ל)|אחריות\s+על|ביצעתי|דאגתי\s+ש|לקחתי\s+חלק\s+ב|עזרתי\s+ב)\s*/i, '');
    }
    cleaned = cleaned.trim();
    if (cleaned.endsWith('.')) cleaned = cleaned.slice(0, -1);

    // Identify domain context
    const hasGas = /(?:גז|לחץ|ספיק|צנרת|prms|נתג|הפק|אסד|gas|pressure|flow|pipeline)/i.test(raw);
    const hasSolar = /(?:סולאר|פאנל|שמש|pv|bifacial|חשמל|ממיר|שנאי|inverter|solar|bess|battery)/i.test(raw);
    const hasAutomation = /(?:סקאד|בקר|scada|plc|hmi|אוטומצי|מוקד|שליט)/i.test(raw);
    const hasNomination = /(?:נומינצי|הקצא|מסחר|לקוח|nomination|commercial)/i.test(raw);

    if (isEnglish) {
      if (mode === 'technical') {
        const sys = hasGas ? "PRMS and SCADA telemetry" : (hasSolar ? "Bifacial PV arrays and central inverters" : "control systems and electrical instrumentation");
        const metric = hasGas ? "maintaining operating pressure at 45-65 bar and eliminating telemetry drift" : "achieving >22% energy conversion efficiency and full statutory code compliance";
        return `Monitored and calibrated ${cleaned || sys}, ${metric}.`;
      } else if (mode === 'operational') {
        const metric = "securing 100% supply continuity and 0 LTI safety incidents";
        return `Spearheaded 24/7 mission-critical operations for ${cleaned || "field energy infrastructure"}, ${metric}.`;
      } else {
        const interf = hasNomination ? "commercial nomination workflows and grid balance" : "stakeholder and technical contractor interfaces";
        return `Synchronized and optimized ${cleaned || interf}, achieving 100% contractual delivery compliance.`;
      }
    } else {
      if (mode === 'technical') {
        if (hasSolar) {
          return `אפיינתי וכיַילתי ${cleaned || "מערכי פאנלים סולאריים מסוג Bifacial PV וממירי מתח"}, תוך אופטימיזציית נצילות של מעל 22% ועמידה מלאה בחוק החשמל.`;
        } else if (hasNomination) {
          return `חישבתי וניתחתי ${cleaned || "כמויות נומינציה שעתית ויומית במערכות SCADA"}, תוך אופטימיזציית ספיקות בצנרת והפחתת סטיות מתחת ל-0.5%.`;
        } else {
          return `ניטרתי וכיַילתי באופן רציף ${cleaned || "לחצי צנרת וספיקות גז במערך תחנות PRMS ו-SCADA"}, תוך שמירה קפדנית על לחץ יעד של 45-65 bar ומניעת תקלות הולכה.`;
        }
      } else if (mode === 'operational') {
        return `שימשתי כגורם תפעולי מוביל במשמרות 24/7 לניהול ${cleaned || "מערכות אנרגיה ותשתיות שטח קריטיות"}, תוך קבלת החלטות מהירות בחירום והשגת 100% רציפות אספקה עם אפס תאונות LTI.`;
      } else {
        if (hasGas || hasNomination) {
          return `סנכרנתי ותיאמתי ${cleaned || "ממשקי הולכת גז ובקשות נומינציה מורכבות"} מול נתג״ז ואסדת ההפקה הימית, תוך הבטחת התאמה מלאה של 100% לדרישות הלקוחות המסחריים.`;
        } else {
          return `ייעלתי והובלתי ${cleaned || "תהליכים וממשקים תפעוליים חוצי-ארגונים"}, תוך קיצור זמני תגובה והבטחת 100% עמידה ביעדי השירות והתקציב.`;
        }
      }
    }
  }

  function validateBulletGrammar(bulletText) {
    const raw = (bulletText || '').trim();
    if (!raw) {
      return {
        score: 0,
        hasActiveVerb: false,
        hasMetric: false,
        hasScope: false,
        detectedTone: 'neutral',
        suggestions: ['הזן ניסוח נקודת קו״ח לניתוח תחבירי ומדדי איכות.']
      };
    }

    const suggestions = [];

    // 1. Check for Active Action Verb at start
    const firstWord = raw.split(/[\s,.:;]+/)[0] || '';
    const activeVerbsHe = [
      'ניטרתי', 'כיַילתי', 'כיילתי', 'חישבתי', 'ניתחתי', 'אפיינתי', 'התקנתי', 'מיפיתי', 'תכננתי', 'תיכננתי', 'שדרגתי', 'בדקתי',
      'הובלתי', 'תפעלתי', 'ניהלתי', 'בלמתי', 'אכפתי', 'הכרעתי', 'שימשתי', 'פיקדתי', 'ייצבתי', 'חילצתי', 'הגנתי', 'הפעלתי',
      'סנכרנתי', 'תיאמתי', 'ייעלתי', 'הכשרתי', 'הטמעתי', 'יזמתי', 'הסדרתי', 'גיבשתי', 'הנהגתי', 'בניתי', 'פיתחתי', 'הקמתי'
    ];
    const activeVerbsEn = [
      'monitored', 'calibrated', 'calculated', 'analyzed', 'engineered', 'installed', 'designed', 'tested', 'upgraded',
      'spearheaded', 'operated', 'managed', 'mitigated', 'enforced', 'resolved', 'stabilized', 'directed', 'commanded',
      'synchronized', 'coordinated', 'streamlined', 'trained', 'implemented', 'pioneered', 'negotiated', 'formulated'
    ];

    const passivePhrasesHe = ['הייתי', 'עבדתי', 'עשיתי', 'טיפלתי', 'לקחתי', 'עזרתי', 'אחראי', 'אחריות'];
    const passivePhrasesEn = ['i was', 'responsible', 'worked', 'helped', 'assisted'];

    const isPassiveStartHe = passivePhrasesHe.some(p => raw.startsWith(p));
    const isPassiveStartEn = passivePhrasesEn.some(p => raw.toLowerCase().startsWith(p));
    const isPassive = isPassiveStartHe || isPassiveStartEn;

    const hasActiveVerb = !isPassive && (
      activeVerbsHe.includes(firstWord) ||
      activeVerbsEn.includes(firstWord.toLowerCase()) ||
      raw.startsWith('שימשתי כ')
    );

    // 2. Check for Quantified Metric / HSE
    const metricRegex = /(?:\d+[\d.,]*\s*(?:%|bar|MW|kW|V|Volt|kV|LTI|hr|hours|שעות|משמרות|שנים|שנה|חודשים|חודש|תחנות|פאנלים|מגה-ואט|בר|אחוז|ש״ח|₪|\$|EUR|ק״מ|מטר|דקות|שניות))|\b24\/7\b|\b100%\b|\b0\s*(?:LTI|תאונות|תקלות|נפגעים|אירועי בטיחות)|(?:אפס\s*(?:תאונות|תקלות|נפגעים|השבתה))|\bzero\s*(?:harm|lti|incidents|downtime)\b/i;
    const hasMetric = metricRegex.test(raw);

    // 3. Check for System / Scope Specificity
    const scopeRegex = /(?:PRMS|SCADA|PLC|HMI|DCS|BESS|PV|Bifacial|Monofacial|Inverter|Transformer|HV|LV|ESD|INGL|נתג״ז|FPSO|SAP|Excel|Modbus|TIA|ASME|ISO|חוק החשמל|משאבות|שסתומים|טורבינות|צנרת|ממסרים|נומינצי|נומינציה|רשת החשמל|אסדת הפקה|מתקן אנרגיה|רחפנים)/i;
    const hasScope = scopeRegex.test(raw);

    // 4. Tone Detection
    let detectedTone = 'neutral';
    const techWords = /(?:PRMS|SCADA|PLC|bar|לחץ|ספיקה|Bifacial|Inverter|כיול|הנדס|תרמודינמ|חוק החשמל|חישבתי|ניטרתי|מתח)/i;
    const operWords = /(?:24\/7|משמרת|לילה|חירום|LTI|בטיחות|תפעלתי|הובלתי|הכרעתי|רציפות|בלמתי|אפס תאונות)/i;
    const stratWords = /(?:נומינצי|נתג״ז|FPSO|אסדה|סנכרנתי|תיאמתי|ייעלתי|הכשרתי|הסכם|בינלאומי|לקוחות|מסחרי)/i;

    let techMatches = (raw.match(new RegExp(techWords, 'gi')) || []).length;
    let operMatches = (raw.match(new RegExp(operWords, 'gi')) || []).length;
    let stratMatches = (raw.match(new RegExp(stratWords, 'gi')) || []).length;

    if (techMatches > operMatches && techMatches > stratMatches) {
      detectedTone = 'technical';
    } else if (operMatches >= techMatches && operMatches > stratMatches) {
      detectedTone = 'operational';
    } else if (stratMatches > 0 && stratMatches >= techMatches && stratMatches >= operMatches) {
      detectedTone = 'strategic';
    }

    // 5. Score computation
    let score = 20; // Base score for non-empty input
    if (hasActiveVerb) score += 30;
    if (hasMetric) score += 30;
    if (hasScope) score += 20;

    if (isPassive) {
      score = Math.max(10, score - 20);
      suggestions.push("החלף ניסוח סביל ('הייתי אחראי' / 'עבדתי') בפועל פעיל בזמן עבר בראש המשפט (כגון ניטרתי, הובלתי, סנכרנתי).");
    } else if (!hasActiveVerb) {
      suggestions.push("פתח את המשפט בפועל פעיל בזמן עבר המדגיש את תרומתך האישית (לדוגמה: ניטרתי, הובלתי, ייעלתי).");
    }

    if (!hasMetric) {
      suggestions.push("הוסף מדד כמותי או יעד בטיחות/תפעול מוגדר (כגון 24/7, 0 תאונות LTI, 100% רציפות אספקה, או ערכי לחץ ב-bar).");
    }

    if (!hasScope) {
      suggestions.push("ציין תשתית, מערכת או מתקן תעשייתי ספציפי (לדוגמה: תחנות PRMS, מערכת SCADA, פאנלי Bifacial PV, או נתג״ז).");
    }

    if (suggestions.length === 0) {
      suggestions.push("מבנה הישג מצוין: פועל פעיל, תשתית הנדסית מדויקת ומדד כמותי/HSE מוגדר היטב.");
    }

    score = Math.min(100, Math.max(0, score));

    return {
      score,
      hasActiveVerb,
      hasMetric,
      hasScope,
      detectedTone,
      suggestions
    };
  }

  let currentWriterTone = 'technical';
  let currentDictCategory = 'all';
  let writerInitialized = false;

  function setWriterToneMode(mode) {
    if (!TONE_SWITCHER_PROFILES[mode]) return;
    currentWriterTone = mode;

    if (typeof document === 'undefined') return;

    ['btnToneTechnical', 'btnToneOperational', 'btnToneStrategic'].forEach(id => {
      const btn = document.getElementById(id);
      if (btn) {
        const isTarget = (id === `btnTone${mode.charAt(0).toUpperCase() + mode.slice(1)}`);
        btn.classList.toggle('active', isTarget);
        btn.setAttribute('aria-selected', isTarget ? 'true' : 'false');
      }
    });

    updateWriterToneCard(mode);

    // If input already has text, re-transform
    const inputEl = document.getElementById('writerRawInput');
    if (inputEl && inputEl.value.trim()) {
      triggerBulletTransform();
    }
  }

  function updateWriterToneCard(mode) {
    const profile = TONE_SWITCHER_PROFILES[mode];
    if (!profile) return;

    const iconEl = document.getElementById('writerToneActiveIcon');
    const titleEl = document.getElementById('writerToneActiveTitle');
    const descEl = document.getElementById('writerToneActiveDesc');
    const verbsChipsEl = document.getElementById('writerActiveVerbsChips');

    if (iconEl) iconEl.className = `ph-duotone ${profile.icon}`;
    if (titleEl) titleEl.textContent = `סגנון ${profile.label_he}`;
    if (descEl) descEl.textContent = profile.description_he;
    if (verbsChipsEl) {
      verbsChipsEl.innerHTML = profile.active_verbs
        .map(v => `<span class="writer-verb-chip">${v}</span>`)
        .join('');
    }
  }

  function onWriterInputChanged() {
    const inputEl = document.getElementById('writerRawInput');
    const countEl = document.getElementById('writerCharCount');
    if (!inputEl) return;
    const len = inputEl.value.length;
    if (countEl) countEl.textContent = `${len} תווים`;
  }

  function loadWriterSample(sampleKey) {
    const inputEl = document.getElementById('writerRawInput');
    if (!inputEl) return;

    const samples = {
      gas_monitor: "עבדתי במשמרות בניטור גז ודאגתי שלא יהיו תקלות.",
      night_shift: "הייתי אחראי על המשמרת בלילה ב-Energean ודאגתי שלא יהיו תקלות.",
      nomination: "עשיתי נומינציות ודיברתי עם חברת החשמל ונתג״ז.",
      solar_pv: "טיפלתי במערכות סולאריות והתקנתי פאנלים."
    };

    if (samples[sampleKey]) {
      inputEl.value = samples[sampleKey];
      onWriterInputChanged();
      triggerBulletTransform();
    }
  }

  function clearWriterInput() {
    const inputEl = document.getElementById('writerRawInput');
    const outputEl = document.getElementById('writerTransformedOutput');
    if (inputEl) inputEl.value = '';
    onWriterInputChanged();
    if (outputEl) {
      outputEl.innerHTML = '<span class="writer-output-placeholder">ההישג המשודרג יוצג כאן לאחר לחיצה על "שדרג לסגנון נבחר"...</span>';
    }
    renderGrammarAnalysis(validateBulletGrammar(''));
  }

  function triggerBulletTransform() {
    const inputEl = document.getElementById('writerRawInput');
    const outputEl = document.getElementById('writerTransformedOutput');
    if (!inputEl || !outputEl) return;

    const raw = inputEl.value.trim();
    if (!raw) {
      outputEl.innerHTML = '<span class="writer-output-placeholder">נא להזין ניסוח נקודת קו״ח...</span>';
      renderGrammarAnalysis(validateBulletGrammar(''));
      return;
    }

    const transformed = transformBulletTone(raw, currentWriterTone);
    outputEl.textContent = transformed;

    const analysis = validateBulletGrammar(transformed);
    renderGrammarAnalysis(analysis);
  }

  function triggerGrammarValidation() {
    const inputEl = document.getElementById('writerRawInput');
    const outputEl = document.getElementById('writerTransformedOutput');
    if (!inputEl) return;

    const textToValidate = (outputEl && outputEl.textContent && !outputEl.querySelector('.writer-output-placeholder'))
      ? outputEl.textContent.trim()
      : inputEl.value.trim();

    const analysis = validateBulletGrammar(textToValidate);
    renderGrammarAnalysis(analysis);
  }

  function renderGrammarAnalysis(analysis) {
    if (typeof document === 'undefined') return;

    const scoreBadge = document.getElementById('grammarScoreBadge');
    if (scoreBadge) {
      scoreBadge.textContent = `${analysis.score} / 100`;
      scoreBadge.className = 'writer-score-badge';
      if (analysis.score >= 80) scoreBadge.classList.add('score-high');
      else if (analysis.score >= 50) scoreBadge.classList.add('score-mid');
      else if (analysis.score > 0) scoreBadge.classList.add('score-low');
      else scoreBadge.classList.add('score-neutral');
    }

    const indVerb = document.getElementById('indActiveVerb');
    if (indVerb) {
      indVerb.className = `writer-indicator-item ${analysis.hasActiveVerb ? 'pass' : (analysis.score > 0 ? 'fail' : '')}`;
      indVerb.innerHTML = `<i class="ph-duotone ${analysis.hasActiveVerb ? 'ph-check-circle' : 'ph-circle'}"></i> <span>פועל פעיל בזמן עבר</span>`;
    }

    const indMetric = document.getElementById('indMetric');
    if (indMetric) {
      indMetric.className = `writer-indicator-item ${analysis.hasMetric ? 'pass' : (analysis.score > 0 ? 'fail' : '')}`;
      indMetric.innerHTML = `<i class="ph-duotone ${analysis.hasMetric ? 'ph-check-circle' : 'ph-circle'}"></i> <span>מדד כמותי / בטיחות HSE</span>`;
    }

    const indScope = document.getElementById('indScope');
    if (indScope) {
      indScope.className = `writer-indicator-item ${analysis.hasScope ? 'pass' : (analysis.score > 0 ? 'fail' : '')}`;
      indScope.innerHTML = `<i class="ph-duotone ${analysis.hasScope ? 'ph-check-circle' : 'ph-circle'}"></i> <span>תשתית / מערכת ספציפית</span>`;
    }

    const indTone = document.getElementById('indTone');
    const indToneText = document.getElementById('indToneText');
    if (indToneText) {
      const toneLabels = {
        technical: 'סגנון: הנדסי / טכני',
        operational: 'סגנון: תפעולי / שטח',
        strategic: 'סגנון: אסטרטגי / ניהולי',
        neutral: 'סגנון: טרם נותח'
      };
      indToneText.textContent = toneLabels[analysis.detectedTone] || 'סגנון: ניטרלי';
    }

    const suggestionsList = document.getElementById('grammarSuggestionsList');
    if (suggestionsList) {
      if (!analysis.suggestions || analysis.suggestions.length === 0) {
        suggestionsList.innerHTML = '<li class="writer-suggestion-placeholder">אין הערכות לניסוח הנוכחי.</li>';
      } else {
        suggestionsList.innerHTML = analysis.suggestions
          .map(s => `<li>${s}</li>`)
          .join('');
      }
    }
  }

  function copyTransformedBullet() {
    const outputEl = document.getElementById('writerTransformedOutput');
    if (!outputEl) return;
    const txt = outputEl.textContent.trim();
    if (!txt || outputEl.querySelector('.writer-output-placeholder')) return;

    if (navigator && navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      navigator.clipboard.writeText(txt).catch(() => {});
    }

    const btn = document.getElementById('btnCopyBullet');
    if (btn) {
      const orig = btn.innerHTML;
      btn.innerHTML = '<i class="ph-duotone ph-check"></i> <span>הועתק!</span>';
      setTimeout(() => { btn.innerHTML = orig; }, 1800);
    }
  }

  function applyBulletToCv() {
    const outputEl = document.getElementById('writerTransformedOutput');
    if (!outputEl) return;
    const txt = outputEl.textContent.trim();
    if (!txt || outputEl.querySelector('.writer-output-placeholder')) return;

    const btn = document.getElementById('btnApplyToCv');
    if (btn) {
      const orig = btn.innerHTML;
      btn.innerHTML = '<i class="ph-duotone ph-check-circle"></i> <span>הוחל בהצלחה!</span>';
      setTimeout(() => { btn.innerHTML = orig; }, 2000);
    }
  }

  function renderEnergyDictionary(terms) {
    const gridEl = document.getElementById('dictCardsGrid');
    const counterEl = document.getElementById('dictTermsCount');
    if (!gridEl) return;

    if (counterEl) counterEl.textContent = `${terms.length} מונחים`;

    if (terms.length === 0) {
      gridEl.innerHTML = '<div class="ats-empty-tag">לא נמצאו מונחים תואמים לחיפוש.</div>';
      return;
    }

    const catClassMap = {
      gas: 'cat-gas',
      renewables: 'cat-renewables',
      electrical: 'cat-electrical',
      automation: 'cat-automation',
      safety: 'cat-safety'
    };

    gridEl.innerHTML = terms.map(t => {
      const catClass = catClassMap[t.category] || 'cat-automation';
      const safeSnippet = t.snippet.replace(/'/g, "\\'");
      return `
        <div class="writer-dict-card" onclick="insertDictionaryTerm('${safeSnippet}')">
          <div class="writer-dict-card-top">
            <span class="writer-dict-card-term-en">${t.acronym}</span>
            <span class="writer-dict-card-cat ${catClass}">${t.category_he}</span>
          </div>
          <div class="writer-dict-card-term-he">${t.term_he}</div>
          <div class="writer-dict-card-desc">${t.description_he}</div>
          <div class="writer-dict-card-bottom">
            <span class="writer-dict-card-cat ${catClass}">${t.category_he}</span>
            <button type="button" class="writer-dict-insert-btn" onclick="event.stopPropagation(); insertDictionaryTerm('${safeSnippet}')">
              <i class="ph-duotone ph-arrow-up-right"></i>
              <span>שלב בטקסט</span>
            </button>
          </div>
        </div>
      `;
    }).join('');
  }

  function filterDictionaryCategory(category) {
    currentDictCategory = category || 'all';

    if (typeof document === 'undefined') return;

    const buttons = document.querySelectorAll('.writer-dict-cat-btn');
    buttons.forEach(btn => {
      const cat = btn.getAttribute('data-category');
      btn.classList.toggle('active', cat === currentDictCategory);
    });

    const searchInput = document.getElementById('dictSearchInput');
    const q = searchInput ? searchInput.value : '';
    const filtered = searchEnergyDictionary(q, currentDictCategory);
    renderEnergyDictionary(filtered);
  }

  function onDictSearchInputChanged() {
    const searchInput = document.getElementById('dictSearchInput');
    const clearBtn = document.getElementById('btnDictClearSearch');
    if (!searchInput) return;

    const q = searchInput.value;
    if (clearBtn) clearBtn.style.display = q ? 'block' : 'none';

    const filtered = searchEnergyDictionary(q, currentDictCategory);
    renderEnergyDictionary(filtered);
  }

  function clearDictSearch() {
    const searchInput = document.getElementById('dictSearchInput');
    const clearBtn = document.getElementById('btnDictClearSearch');
    if (searchInput) searchInput.value = '';
    if (clearBtn) clearBtn.style.display = 'none';
    const filtered = searchEnergyDictionary('', currentDictCategory);
    renderEnergyDictionary(filtered);
  }

  function insertDictionaryTerm(snippet) {
    const inputEl = document.getElementById('writerRawInput');
    if (!inputEl) return;
    const currentVal = inputEl.value.trim();
    if (currentVal) {
      inputEl.value = `${currentVal} (${snippet})`;
    } else {
      inputEl.value = snippet;
    }
    onWriterInputChanged();
    triggerBulletTransform();
  }

  function initWriterModule() {
    if (typeof document === 'undefined' || typeof document.getElementById !== 'function') return;
    if (!document.getElementById('studioModuleWriter') && !document.getElementById('writerRawInput')) return;

    if (!writerInitialized) {
      updateWriterToneCard(currentWriterTone);
      renderEnergyDictionary(ENERGY_DICTIONARY);
      renderGrammarAnalysis(validateBulletGrammar(''));
      writerInitialized = true;
    }
  }

  // Expose global functions to window
  window.switchDashboardAppMode = switchDashboardAppMode;
  window.switchStudioModule = switchStudioModule;
  window.getActiveCvProfile = getActiveCvProfile;
  window.processCvFile = processCvFile;
  window.extractTextFromFile = extractTextFromFile;
  window.handleManualCvUpload = handleManualCvUpload;
  window.resetToBaselineCv = resetToBaselineCv;
  window.initCvUploadState = initCvUploadState;
  window.STATUTORY_HARD_GATES = STATUTORY_HARD_GATES;
  window.KEYWORD_TAXONOMY = KEYWORD_TAXONOMY;
  window.ATS_STRUCTURAL_RULES = ATS_STRUCTURAL_RULES;
  window.CANONICAL_CV_PROFILE = CANONICAL_CV_PROFILE;
  window.evaluateHardGates = evaluateHardGates;
  window.extractMissingKeywords = extractMissingKeywords;
  window.checkAtsStructuralCompliance = checkAtsStructuralCompliance;
  window.runAtsJobMatching = runAtsJobMatching;
  window.initAtsModule = initAtsModule;
  window.populateAtsJobSelector = populateAtsJobSelector;
  window.setAtsActiveStep = setAtsActiveStep;
  window.triggerAtsMatching = triggerAtsMatching;
  window.onAtsJobSelected = onAtsJobSelected;
  window.onAtsInputChanged = onAtsInputChanged;
  window.loadSampleAtsJob = loadSampleAtsJob;
  window.clearAtsInput = clearAtsInput;
  window.generateCvBulletActionItem = generateCvBulletActionItem;

  // Milestone 3 AI Writer & Tone Switcher Exposures
  window.TONE_SWITCHER_PROFILES = TONE_SWITCHER_PROFILES;
  window.ENERGY_DICTIONARY = ENERGY_DICTIONARY;
  window.transformBulletTone = transformBulletTone;
  window.validateBulletGrammar = validateBulletGrammar;
  window.searchEnergyDictionary = searchEnergyDictionary;
  window.initWriterModule = initWriterModule;
  window.setWriterToneMode = setWriterToneMode;
  window.triggerBulletTransform = triggerBulletTransform;
  window.triggerGrammarValidation = triggerGrammarValidation;
  window.onWriterInputChanged = onWriterInputChanged;
  window.loadWriterSample = loadWriterSample;
  window.copyTransformedBullet = copyTransformedBullet;
  window.applyBulletToCv = applyBulletToCv;
  window.insertDictionaryTerm = insertDictionaryTerm;
  window.filterDictionaryCategory = filterDictionaryCategory;
  window.onDictSearchInputChanged = onDictSearchInputChanged;
  window.clearDictSearch = clearDictSearch;
  window.clearWriterInput = clearWriterInput;


  // ==========================================================================
  // Milestone 6: Interview Q&A, Web Audio STAR, LinkedIn & Anonymizer
  // ==========================================================================

  const INTERVIEW_QUESTIONS_BANK = {
    crisis: [
      {
        title: "תרחיש: זיהוי נפילת לחץ פתאומית במתקן הפחתת לחץ (PRMS) ראשי",
        desc: "במהלך משמרת לילה מתקבלת התרעת SCADA על צניחת לחץ במעלה הקו וריח גז עז סמוך למגוף הראשי. צוות קבלני עבודות עפר פועל במרחק 50 מטרים. כיצד תפעל בדקות הראשונות?",
        category: "משבר תפעולי בשטח"
      },
      {
        title: "תרחיש: התלקחות מקומית סמוך לפילטר גז טבעי דחוס (CNG)",
        desc: "צוות תחזוקה ביצע עבודה חמה ומתקבלת התרעת גילוי אש אוטומטית. כיצד אתה מנהל את הפסקת החירום (ESD), בידוד הקו ופינוי עובדים?",
        category: "משבר תפעולי בשטח"
      }
    ],
    contractors: [
      {
        title: "תרחיש: קבלן משנה מסרב להשתמש ברתמת בטיחות תקנית בעבודה בגובה",
        desc: "קבלן צנרת מבצע התקנת מגוף בגובה 4 מטרים בלוח זמנים קריטי לפני השבתת מתקן. הוא טוען שהרתמה מאיטה אותו ויעכב את הפרויקט במיליון ש״ח. מהי תגובתך המיידית?",
        category: "ניהול קבלנים וספקים"
      },
      {
        title: "תרחיש: גילוי כשל בצינור לחץ שסופק ע״י קבלן ללא תעודת ASME",
        desc: "קבלן מבקש להתקין קטע צנרת ללא מסמכי בדיקה מטלורגית (MTR) מתאימים לתקן ASME B31.8. כיצד תפעל מבלי לעצור את שאר עבודות האתר?",
        category: "ניהול קבלנים וספקים"
      }
    ],
    hse: [
      {
        title: "תרחיש: הטמעת תרבות דיווח על כמעט-ונפגע (Near Miss) בצוות ותיק",
        desc: "צוות טכנאים ותיק נוטה לפתור תקלות 'מתחת לרדאר' מבלי לדווח במערכת הבטיחות. כיצד תרתום אותם לתרבות של Zero LTI ושקיפות מלאה?",
        category: "תרבות בטיחות ו-HSE"
      }
    ],
    mechanical: [
      {
        title: "תרחיש: רעידות חריגות ורעש קביטציה במשאבת סחרור ראשית",
        desc: "משאבת הזנה ראשית מציגה עלייה הדרגתית בטמפרטורת המיסב ורעידות מעל התקן. כיצד תאבחן את מקור הכשל לפני גרימת השבתה קטסטרופלית?",
        category: "אבחון תקלות מכניות"
      }
    ]
  };

  let currentInterviewCategory = 'crisis';
  let isVoiceRecording = false;
  let voiceTimerInterval = null;
  let voiceSecondsCount = 0;

  function initInterviewModule() {
    generateNextInterviewQuestion();
  }

  function setInterviewCategory(cat, btn) {
    currentInterviewCategory = cat;
    const chips = document.querySelectorAll('.q-chip');
    chips.forEach(c => c.classList.remove('active'));
    if (btn) btn.classList.add('active');
    generateNextInterviewQuestion();
  }

  function generateNextInterviewQuestion() {
    const list = INTERVIEW_QUESTIONS_BANK[currentInterviewCategory] || INTERVIEW_QUESTIONS_BANK.crisis;
    const q = list[Math.floor(Math.random() * list.length)];
    if (!q) return;

    const titleEl = document.getElementById('interviewQuestionTitle');
    const descEl = document.getElementById('interviewQuestionDesc');
    const badgeEl = document.getElementById('interviewQuestionCategoryBadge');

    if (titleEl) titleEl.textContent = q.title;
    if (descEl) descEl.textContent = q.desc;
    if (badgeEl) badgeEl.textContent = q.category;
  }

  function toggleVoiceRecording() {
    const btn = document.getElementById('btnRecordVoice');
    const label = document.getElementById('voiceRecLabel');
    const timer = document.getElementById('voiceRecTimer');
    const canvas = document.getElementById('voiceWaveCanvas');

    isVoiceRecording = !isVoiceRecording;
    if (isVoiceRecording) {
      if (btn) btn.classList.add('recording');
      if (label) label.textContent = 'עצור הקלטה';
      voiceSecondsCount = 0;

      if (voiceTimerInterval) clearInterval(voiceTimerInterval);
      voiceTimerInterval = setInterval(() => {
        voiceSecondsCount++;
        const mins = String(Math.floor(voiceSecondsCount / 60)).padStart(2, '0');
        const secs = String(voiceSecondsCount % 60).padStart(2, '0');
        if (timer) timer.textContent = `${mins}:${secs}`;
      }, 1000);

      drawSimulatedAudioWave(canvas, true);
      showToast('הקלטת מענה קולי החלה... דבר ברור', 'info');
    } else {
      if (btn) btn.classList.remove('recording');
      if (label) label.textContent = 'התחל הקלטת תשובה';
      if (voiceTimerInterval) {
        clearInterval(voiceTimerInterval);
        voiceTimerInterval = null;
      }
      drawSimulatedAudioWave(canvas, false);
      showToast('ההקלטה נשמרה ותומללה בהצלחה!', 'success');
      evaluateStarAnswer();
    }
  }

  function drawSimulatedAudioWave(canvas, isLive) {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const bars = 28;
    const barWidth = canvas.width / bars;

    for (let i = 0; i < bars; i++) {
      const height = isLive ? Math.random() * 28 + 6 : 4;
      const x = i * barWidth;
      const y = (canvas.height - height) / 2;
      ctx.fillStyle = isLive ? '#f43f5e' : '#334155';
      ctx.fillRect(x + 2, y, barWidth - 4, height);
    }
  }

  function evaluateStarAnswer() {
    const input = document.getElementById('interviewAnswerInput');
    const txt = input ? input.value : '';

    let sScore = 25, tScore = 25, aScore = 25, rScore = 25;
    let sDesc = 'הגדרת זירה ורקע תפעולי ברורים.',
        tDesc = 'הצבת יעד ברור לבלימת הכשל והגנה על הצוות.',
        aDesc = 'שימוש נכון בסמכות מקצועית, מגופים ונוהל חירום.',
        rDesc = 'תוצאה חיובית עם שמירה על 0 נפגעים (Zero LTI).';

    if (!txt.includes('PRMS') && !txt.includes('שטח') && !txt.includes('משמרת')) {
      sScore = 18;
      sDesc = 'מומלץ לציין במפורש את זירת הפעולה (למשל: משמרת לילה במתקן PRMS).';
    }
    if (!txt.includes('פינוי') && !txt.includes('משימה') && !txt.includes('יעד')) {
      tScore = 19;
      tDesc = 'כדאי להדגיש את המשימה הדחופה ביותר: הצלת חיי אדם ובלימת הדליפה.';
    }
    if (!txt.includes('ESD') && !txt.includes('SCADA') && !txt.includes('סגרתי') && !txt.includes('נוהל')) {
      aScore = 18;
      aDesc = 'מומלץ לתאר פעולות הנדסיות קונקרטיות: הפעלת ESD ובידוד קווים.';
    }
    if (!txt.includes('Zero LTI') && !txt.includes('דקות') && !txt.includes('0 תאונות')) {
      rScore = 18;
      rDesc = 'מומלץ לחזק את התוצאה במדד כמותי: זמן תגובה בדקות ומדד Zero LTI.';
    }

    const total = sScore + tScore + aScore + rScore;
    const scoreEl = document.getElementById('starTotalScore');
    if (scoreEl) scoreEl.textContent = `${total} / 100`;

    const sEl = document.getElementById('starSituationText');
    const tEl = document.getElementById('starTaskText');
    const aEl = document.getElementById('starActionText');
    const rEl = document.getElementById('starResultText');

    if (sEl) sEl.textContent = sDesc;
    if (tEl) tEl.textContent = tDesc;
    if (aEl) aEl.textContent = aDesc;
    if (rEl) rEl.textContent = rDesc;

    showToast(`ניתוח STAR הושלם: ציון ${total}/100`, 'success');
  }

  function copyLinkedInOptimizedBio() {
    const bioText = `Gas Controller | Natural Gas Operations | Practical Mechanical Engineer
Practical Mechanical Engineer with experience in 24/7 natural gas operations, real-time supply monitoring, Nomination and Re-nomination management, and offshore production coordination at Energean Israel. Collaborated with commercial teams and strategic customers, making independent operational decisions. Improved operational reporting and shift handovers using Excel, SAP, Microsoft 365 Copilot, and AI tools; brings international team leadership and commercial experience.`;

    if (navigator.clipboard) {
      navigator.clipboard.writeText(bioText).then(() => {
        const btnText = document.getElementById('copyLinkedInBioText');
        if (btnText) btnText.textContent = 'הועתק בהצלחה ללוח!';
        showToast('נוסח About ללינקדאין הועתק ללוח!', 'success');
        setTimeout(() => {
          if (btnText) btnText.textContent = 'העתק נוסח מומלץ ל-About בלינקדאין';
        }, 3000);
      });
    }
  }


  // ==========================================================================
  // Milestone 6: Skill Gap Engine & Privacy Anonymizer
  // ==========================================================================

  let isAnonymizerActive = false;

  const ANONYMIZED_CV_TEXT = `הנדסאי מכונות בהתמחות בגז טבעי ובאנרגיה ירוקה עם ניסיון בבקרה תפעולית בזמן אמת ובתיאום אספקת גז במערך 24/7.
ניסיון בניטור לחצים וספיקות עם AVEVA System Platform, ניהול Nomination ו-Re-nomination ותיאום מול אסדת הפקה ימית ונתג״ז.
פיתוח סוכני Microsoft 365 Copilot לחישוב כמויות גז ושיפור העברת משמרת, עבודה עם SAP ו-Excel וכעת בלימודי חשמלאי מוסמך.
ליצירת קשר דיסקרטי: candidate@confidential.il`;

  const ORIGINAL_CV_SUMMARY_TEXT = `עידו גל — הנדסאי מכונות | בקרת גז טבעי | תפעול מערכות אנרגיה
תל אביב | 0526328886 | idogal0210@gmail.com | linkedin.com/in/ido-g/
ניסיון: בקר גז — תפעול ומוצר ב-Energean Israel Ltd. (2022–2026), עבודה עם AVEVA System Platform, SAP ו-Excel.
פיתוח סוכני Microsoft 365 Copilot לחישוב כמויות גז עבור 10+ לקוחות גדולים ולשיפור תהליך העברת משמרת.
השכלה: הנדסאי מכונות (רופין 2022) ולימודי חשמלאי מוסמך (צפי סיום: דצמבר 2026).`;

  function initSkillsModule() {
    const toggle = document.getElementById('anonToggleCheckbox');
    if (toggle) toggle.checked = false;
  }

  function toggleAnonymizerMode(isChecked) {
    isAnonymizerActive = isChecked;
    const preview = document.getElementById('anonymizedPreviewArea');
    if (!preview) return;

    if (isChecked) {
      preview.value = ANONYMIZED_CV_TEXT;
      showToast('מצב אנונימי פעיל: כל הפרטים המזהים הוסתרו', 'success');
    } else {
      preview.value = ORIGINAL_CV_SUMMARY_TEXT;
      showToast('מצב אנונימי כבוי: מוצגים פרטים מלאים', 'info');
    }
  }

  function copyAnonymizedCv() {
    const preview = document.getElementById('anonymizedPreviewArea');
    const textToCopy = preview ? preview.value : ANONYMIZED_CV_TEXT;

    if (navigator.clipboard) {
      navigator.clipboard.writeText(textToCopy).then(() => {
        const btnText = document.getElementById('copyAnonBtnText');
        if (btnText) btnText.textContent = 'הועתק ללוח בהצלחה!';
        showToast('הנוסח האנונימי הועתק בהצלחה לשיתוף בטוח!', 'success');
        setTimeout(() => {
          if (btnText) btnText.textContent = 'העתק נוסח אנונימי ללוח (Clipboard)';
        }, 3000);
      });
    }
  }

  // Window Exposures for Milestones 4, 5, 6


  function scrollToStudioStep(stepId) {
    const el = document.getElementById(stepId);
    if (!el) return;
    const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    el.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
    el.setAttribute('tabindex', '-1');
    el.focus({ preventScroll: true });
  }
  window.scrollToStudioStep = scrollToStudioStep;

  window.initInterviewModule = initInterviewModule;
  window.setInterviewCategory = setInterviewCategory;
  window.generateNextInterviewQuestion = generateNextInterviewQuestion;
  window.toggleVoiceRecording = toggleVoiceRecording;
  window.evaluateStarAnswer = evaluateStarAnswer;
  window.copyLinkedInOptimizedBio = copyLinkedInOptimizedBio;

  window.initSkillsModule = initSkillsModule;
  window.toggleAnonymizerMode = toggleAnonymizerMode;
  window.copyAnonymizedCv = copyAnonymizedCv;
  window.purgeJobPermanently = purgeJobPermanently;
  window.restoreJob = restoreJob;
  window.clearAllRejected = clearAllRejected;
  window.openDuplicatesModal = openDuplicatesModal;
  window.closeDuplicatesModal = closeDuplicatesModal;
  window.openInactiveJobsModal = openInactiveJobsModal;
  window.runLiveJobCheck = runLiveJobCheck;
  window.saveJobCheckWorkerUrl = saveJobCheckWorkerUrl;
  window.closeInactiveJobsModal = closeInactiveJobsModal;
  window.handleRemoveInactiveJob = handleRemoveInactiveJob;
  window.handleRemoveAllInactiveJobs = handleRemoveAllInactiveJobs;
  window.handleMergeDuplicates = handleMergeDuplicates;
  window.handleRemoveDuplicates = handleRemoveDuplicates;
  window.handleIgnoreGroup = handleIgnoreGroup;


  window.onload = async () => {
    updateCubeCountsImmediately();
    checkUrlSync();
    updateSortIconAndToast(currentSort, false);
    await fetchJobsData();
    await fetchCloudSync();
    fetchLatestCloudRunStatus();
    setViewMode(currentViewMode);
    initAtsModule();
    initCvUploadState();
    initWriterModule();
    initInterviewModule();
    initSkillsModule();

    const rawHash = (window.location.hash || '').replace('#', '').trim();
    let initialMode = 'radar';
    try {
      initialMode = localStorage.getItem(APP_ACTIVE_MODE_KEY) || 'radar';
    } catch (e) {}

    if (rawHash === 'studio' || (!rawHash && initialMode === 'studio')) {
      switchDashboardAppMode('studio', false);
    } else {
      switchDashboardAppMode('radar', false);
      if (rawHash === 'saved' || rawHash === 'rejected' || rawHash === 'starred') {
        const cubeEl = document.getElementById('cube_' + rawHash);
        setFilter(rawHash, cubeEl);
      }
    }
  };

  // Hash navigation listener for direct deep-linking
  window.addEventListener('hashchange', () => {
    const h = (window.location.hash || '').replace('#', '').trim();
    if (h === 'studio') {
      switchDashboardAppMode('studio', false);
    } else if (h === 'radar') {
      switchDashboardAppMode('radar', false);
    } else if (h === 'saved' || h === 'rejected' || h === 'starred') {
      switchDashboardAppMode('radar', false);
      const cubeEl = document.getElementById('cube_' + h);
      setFilter(h, cubeEl);
    }
  });

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      fetchCloudSync();
    }
  });

  window.addEventListener('focus', () => {
    fetchCloudSync();
  });

  window.addEventListener('scroll', () => {
    const btn = document.getElementById('btnBackToTop');
    if (!btn) return;
    if (window.scrollY > 380) {
      btn.classList.add('visible');
    } else {
      btn.classList.remove('visible');
    }
  }, { passive: true });

  let windowResizeTimer = null;
  window.addEventListener('resize', () => {
    if (windowResizeTimer) clearTimeout(windowResizeTimer);
    windowResizeTimer = setTimeout(() => {
      filterCards();
    }, 100);
  });
