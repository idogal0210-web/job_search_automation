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

  function normalizeSalaryRange(text) {
    if (!text) return '';
    return String(text).replace(
      /(?:₪\s*)?([\d,]+)\s*[-–]\s*([\d,]+)(?:\s*₪)?/g,
      (_, a, b) => {
        const n1 = Number(a.replace(/,/g, ''));
        const n2 = Number(b.replace(/,/g, ''));
        if (!Number.isFinite(n1) || !Number.isFinite(n2)) return `${a} - ${b}`;
        const [minVal, maxVal] = n1 <= n2 ? [a, b] : [b, a];
        return `${minVal} - ${maxVal} ₪`;
      }
    );
  }

  function normalizeJobLocation(rawLocation) {
    return stripEmojis(rawLocation || '')
      .replace(/\b([A-Za-z\s]+),\s*\1\b/gi, '$1')
      .replace(/([\u0590-\u05FF\s"״'-]+),\s*\1(?=$|,)/g, '$1')
      .trim();
  }

  function formatJobSalaryTag(job) {
    if (!job) return '';
    let sal = (job.salary_range || '').trim();
    if (!sal || sal === 'לא צוין במודעה' || sal === 'לא צוין שכר' || sal === 'לא צוין') {
      return '';
    }
    // Clean any accidental word 'הערכה' and normalize reversed ranges
    sal = sal.replace(/הערכה\s*(?:חודשית|פנימית|בלבד)?/g, '').replace(/—\s*$/, '').replace(/;\s*:/g, ':').trim();
    sal = sal.replace(/\(\s*\)/g, '').trim();
    sal = normalizeSalaryRange(sal);

    const isAd = job.salary_source_type === 'job_ad' || job.salary_source_type === 'ad' || job.salary_source_type === 'employer';
    if (isAd) {
      return `<span class="job-salary-chip salary-chip-ad salary-badge" title="שכר שפורסם במודעת המשרה"><i class="ph-duotone ph-coins"></i> ${escapeHtml(sal)} (במודעה)</span>`;
    }
    return `<span class="job-salary-chip salary-chip-benchmark salary-badge" title="טווח שכר ענפי מותאם לתפקיד"><i class="ph-duotone ph-coins"></i> ${escapeHtml(sal)}</span>`;
  }

  function isolateBiDiTerms(escapedText) {
    if (!escapedText) return '';
    return escapedText.replace(/([A-Za-z0-9][A-Za-z0-9\s\.\+\#\-\/]*[A-Za-z0-9]|[A-Za-z0-9])/g, '<bdi>$1</bdi>');
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

  function condenseMatchInsight(text) {
    if (!text || text === 'אין ניתוח התאמה מאומת למשרה זו.') {
      return 'התאמה טכנית ומקצועית גבוהה';
    }
    const t = text.trim();
    const hasCommand = /פיקוד|ניהול\s+צוות|מפקד/.test(t);
    const hasSolar = /סולאר|BESS|אגיר/.test(t);
    const hasGas = /גז|לחץ|טורבינ/.test(t);
    const hasUav = /רחפן|כטב|C-UAS/.test(t);
    const hasScada = /SCADA|בקרה/.test(t);
    const hasField = /שטח|אינטגרצי/.test(t);

    if (hasCommand) return 'התאמה טכנית ופיקודית גבוהה';
    if (hasSolar) return 'התאמה גבוהה (רקע סולארי ומכונות)';
    if (hasGas) return 'התאמה גבוהה (רקע גז ומערכות לחץ)';
    if (hasUav) return 'התאמה גבוהה (כטב"ם ומערכות שטח)';
    if (hasScada) return 'התאמה גבוהה (בקרה ו-SCADA)';
    if (hasField) return 'התאמה טכנית גבוהה (מכונות ושטח)';

    let clean = t.replace(/^(?:המועמד\s+(?:הוא|הינו)|עידו\s+(?:הוא)?|לעידו|המוועמד\s+(?:הוא|הינו))\s*/i, '');
    clean = clean.split(/,?\s*(?:המתאים|העונה|ועונה|התואם|המשתלבים|אשר|ומהווה)\s+/)[0];
    clean = clean.replace(/^הנדסאי מכונות מוסמך\s+(?:עם|בעל)\s*/, '');
    clean = clean.replace(/^(?:רקע\s+(?:מוצק|חזק|טוב)\s+ב?)/, '');
    const words = clean.trim().split(/\s+/);
    if (words.length > 5) {
      clean = words.slice(0, 5).join(' ');
    }
    return clean ? ('התאמה טכנית גבוהה (' + clean.replace(/[,;]+$/, '') + ')') : 'התאמה טכנית ומקצועית גבוהה';
  }

  function condenseFitGap(text) {
    if (!text) return 'עונה על דרישות הסף';
    const t = text.trim();
    if (/אין פערי סף|אין פער|עונה על דריש|ללא פער/.test(t)) {
      return 'עונה על דרישות הסף';
    }
    let clean = t.split(/,?\s*(?:אך|אולם|עם זאת|כאשר|ויש לו)\s+/)[0];
    clean = clean.replace(/^(?:למועמד\s+אין|אין\s+למועמד|היעדר|קיים\s+פער\s+(?:מסוים\s+)?ב?)\s*/, 'חסר ');
    clean = clean.replace(/^חסר\s+ניסיון\s+(?:קודם\s+ספציפי|ספציפי\s+מוקדם|מעשי\s+עמוק|קודם)\s+ב?/, 'חסר ניסיון ב');
    if (/ייצור בתעשייה כבדה|ניהול מחלקת ייצור/.test(clean)) {
      return 'חסר ניסיון בניהול ייצור תעשייתי';
    }
    const words = clean.trim().split(/\s+/);
    if (words.length > 7) {
      clean = words.slice(0, 7).join(' ');
    }
    return clean.replace(/[,;.]+$/, '');
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

    const shortInsight = condenseMatchInsight(insightRaw);
    const shortGap = condenseFitGap(gapsRaw);
    const isNoGap = (shortGap === 'עונה על דרישות הסף');

    let badgeHtml = '';
    let statusHtml = '';

    if (isNoGap) {
      badgeHtml = '<span class="gap-status-pill gap-status-ok">[OK] ללא פערי סף</span>';
      statusHtml = '<span class="gap-text-ok">[OK] עונה על דרישות הסף</span>';
    } else {
      badgeHtml = '<span class="gap-status-pill gap-status-alert">[פער] קיים פער סף</span>';
      statusHtml = `<span class="gap-text-alert">[פער] ${escapeHtml(shortGap)}</span>`;
    }

    return {
      isNoGap,
      badgeHtml,
      statusHtml,
      fullHtml: `${escapeHtml(shortInsight)} | ${statusHtml}`
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
  const SORT_STORAGE_KEY = 'ido_job_sort_mode';
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
  const PURGED_STORAGE_KEY = 'ido_job_purged_keys';

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

  function loadPurgedJobs() {
    try {
      const stored = localStorage.getItem(PURGED_STORAGE_KEY);
      if (stored) return JSON.parse(stored) || {};
    } catch (e) {}
    return {};
  }

  function savePurgedJobs(map) {
    try {
      localStorage.setItem(PURGED_STORAGE_KEY, JSON.stringify(map || {}));
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

    const canon = getCanonicalJobKey(id);
    document.querySelectorAll('.job-card').forEach(card => {
      const cardId = card.getAttribute('data-id');
      if (cardId === id || (canon && getCanonicalJobKey(cardId) === canon)) {
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

    const purgedMap = loadPurgedJobs();
    Object.keys(purgedMap).forEach(key => {
      if (purgedMap[key]) {
        state[key] = 'purged';
      }
    });

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

  // Authenticated per-user adapter: Supabase Cloud Sync
  const appConfig = window.__APP_CONFIG__ || {};
  const SUPABASE_SYNC_CONFIG = {
    url: appConfig.supabase_url || 'https://wvwdxpttwsrdbvvtiyoh.supabase.co',
    publishableKey: appConfig.supabase_anon_key || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind2d2R4cHR0d3NyZGJ2dnRpeW9oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQyNjA0MTcsImV4cCI6MjEwOTgzNjQxN30.YUun0ttLje3gwWvOU-ACimAtX-xgbUbXhJoELCsx0V4',
    table: 'sync_state',
    rowId: 'default'
  };

  const SUPABASE_AUTH_STORAGE_KEY = 'supabase_auth_session_v1';

  function loadSupabaseSession() {
    try { return JSON.parse(localStorage.getItem(SUPABASE_AUTH_STORAGE_KEY) || 'null'); } catch (e) { return null; }
  }

  function saveSupabaseSession(tokenResponse, emailFallback = '') {
    if (!tokenResponse || !tokenResponse.access_token) return null;
    const userEmail = (tokenResponse.user && tokenResponse.user.email) || emailFallback || '';
    const userId = (tokenResponse.user && tokenResponse.user.id) || '';
    const session = {
      access_token: tokenResponse.access_token,
      refresh_token: tokenResponse.refresh_token,
      user_id: userId,
      user_email: userEmail,
      expires_at: Math.floor(Date.now() / 1000) + (tokenResponse.expires_in || 3600)
    };
    try { localStorage.setItem(SUPABASE_AUTH_STORAGE_KEY, JSON.stringify(session)); } catch (e) {}
    return session;
  }

  async function supabaseAuthRequest(path, body) {
    const resp = await fetch(`${SUPABASE_SYNC_CONFIG.url}/auth/v1/${path}`, {
      method: 'POST',
      headers: { 'apikey': SUPABASE_SYNC_CONFIG.publishableKey, 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    let json = {};
    try { json = await resp.json(); } catch (e) {}
    return { ok: resp.ok, json };
  }

  async function getSupabaseAccessToken() {
    let session = loadSupabaseSession();
    if (!session) return null;
    if (session.expires_at - 60 > Date.now() / 1000) return session.access_token;
    if (!session.refresh_token) return null;
    try {
      const r = await supabaseAuthRequest('token?grant_type=refresh_token', { refresh_token: session.refresh_token });
      if (r.ok) {
        session = saveSupabaseSession(r.json, session.user_email);
        return session ? session.access_token : null;
      }
      if (r.json && (r.json.error_code === 'refresh_token_not_found' || r.json.error_code === 'refresh_token_already_used')) {
        localStorage.removeItem(SUPABASE_AUTH_STORAGE_KEY);
      }
    } catch (e) {}
    return null;
  }

  async function supabaseSignIn(email, password) {
    const r = await supabaseAuthRequest('token?grant_type=password', { email, password });
    if (r.ok && saveSupabaseSession(r.json, email)) return { ok: true };
    const rawErr = (r.json && (r.json.error_description || r.json.msg || r.json.error)) || '';
    let msg = 'ההתחברות נכשלה';
    if (rawErr.includes('Invalid login credentials')) {
      msg = 'פרטי התחברות שגויים (בדוק אימייל וסיסמה)';
    } else if (rawErr.includes('Email not confirmed')) {
      msg = 'כתובת האימייל טרם אושרה. בדוק את תיבת הדואר שלך';
    } else if (rawErr) {
      msg = rawErr;
    }
    return { ok: false, message: msg };
  }

  async function supabaseSignUp(email, password) {
    const r = await supabaseAuthRequest('signup', { email, password });
    if (!r.ok) {
      const rawErr = (r.json && (r.json.msg || r.json.error_description || r.json.error)) || '';
      let msg = 'ההרשמה נכשלה';
      if (rawErr.includes('already registered')) {
        msg = 'משתמש עם כתובת זו כבר קיים. נסה להתחבר';
      } else if (rawErr) {
        msg = rawErr;
      }
      return { ok: false, message: msg };
    }
    if (r.json && r.json.access_token) {
      saveSupabaseSession(r.json, email);
      return { ok: true, confirmed: true };
    }
    return { ok: true, confirmEmail: true };
  }

  function supabaseSignOut() {
    try { localStorage.removeItem(SUPABASE_AUTH_STORAGE_KEY); } catch (e) {}
  }

  function openCloudModal() {
    updateCloudAuthModalUI();
    openDialogEl(document.getElementById('cloudModal'));
  }

  function closeCloudModal() {
    closeDialogEl(document.getElementById('cloudModal'));
  }

  function setCloudAuthMessage(text, tone) {
    const el = document.getElementById('cloudAuthMsg');
    if (!el) return;
    el.textContent = text || '';
    el.style.color = tone === 'error' ? '#f87171' : (tone === 'ok' ? 'var(--dashboard-lime)' : 'var(--dashboard-muted)');
  }

  function updateCloudAuthModalUI() {
    const session = loadSupabaseSession();
    const isAuthed = Boolean(session && session.access_token);
    const outBox = document.getElementById('cloudAuthSignedOut');
    const inBox = document.getElementById('cloudAuthSignedIn');
    if (outBox) outBox.style.display = isAuthed ? 'none' : 'flex';
    if (inBox) inBox.style.display = isAuthed ? 'flex' : 'none';
    const userEl = document.getElementById('cloudAuthUser');
    if (userEl) userEl.textContent = (session && session.user_email) || '';
    const emailInput = document.getElementById('cloudAuthEmail');
    if (emailInput && !emailInput.value) {
      try { emailInput.value = localStorage.getItem('supabase_last_email') || ''; } catch (e) {}
    }
    setCloudAuthMessage('', '');
  }

  function readCloudAuthCredentials() {
    const email = (document.getElementById('cloudAuthEmail') || {}).value || '';
    const password = (document.getElementById('cloudAuthPassword') || {}).value || '';
    return { email: email.trim(), password };
  }

  async function runCloudAuthAction(kind) {
    if (kind === 'signup') {
      setCloudAuthMessage('הרשמה עצמית חסומה בלוח בקרה אישי זה.', 'error');
      return;
    }
    const { email, password } = readCloudAuthCredentials();
    if (!email || password.length < 8) {
      setCloudAuthMessage('נא להזין אימייל וסיסמה (לפחות 8 תווים)', 'error');
      return;
    }
    const buttons = document.querySelectorAll('#cloudAuthSignedOut button');
    buttons.forEach(b => { b.disabled = true; });
    setCloudAuthMessage('מתחבר...', '');
    try {
      const res = await supabaseSignIn(email, password);
      if (!res.ok) {
        setCloudAuthMessage(res.message || 'הפעולה נכשלה', 'error');
        return;
      }
      try { localStorage.setItem('supabase_last_email', email); } catch (e) {}
      const pw = document.getElementById('cloudAuthPassword');
      if (pw) pw.value = '';
      updateCloudAuthModalUI();
      await fetchCloudSync(true);
      closeCloudModal();
    } catch (e) {
      setCloudAuthMessage('שגיאת רשת. נסה שוב.', 'error');
    } finally {
      buttons.forEach(b => { b.disabled = false; });
    }
  }

  function handleCloudSignOut() {
    supabaseSignOut();
    cloudSyncMeta = null;
    setCloudSyncStatus('local');
    updateCloudAuthModalUI();
  }

  let cloudSyncMeta = null;

  function extractUserIdFromJwt(jwt) {
    if (!jwt || typeof jwt !== 'string') return '';
    try {
      const parts = jwt.split('.');
      if (parts.length < 2) return '';
      const b64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
      const jsonStr = typeof atob === 'function' ? atob(b64) : '';
      const payload = jsonStr ? JSON.parse(jsonStr) : {};
      return payload.sub || '';
    } catch (_) {
      return '';
    }
  }

  const supabaseSyncAdapter = {
    async read() {
      try {
        const token = await getSupabaseAccessToken();
        if (!token) return { ok: false, authRequired: true };
        const resp = await fetch(`${SUPABASE_SYNC_CONFIG.url}/rest/v1/${SUPABASE_SYNC_CONFIG.table}?select=*&limit=1`, {
          headers: {
            'apikey': SUPABASE_SYNC_CONFIG.publishableKey,
            'Authorization': `Bearer ${token}`
          },
          cache: 'no-store'
        });
        if (resp.status === 401 || resp.status === 403) return { ok: false, authRequired: true };
        if (!resp.ok) return { ok: false };
        const rows = await resp.json();
        if (!rows || rows.length === 0) {
          cloudSyncMeta = { exists: false, id: null, user_id: extractUserIdFromJwt(token), version: null, updated_at: null };
          return { ok: false, notFound: true };
        }
        const row = rows[0];
        cloudSyncMeta = {
          exists: true,
          id: row.id || null,
          user_id: row.user_id || extractUserIdFromJwt(token) || null,
          version: typeof row.version === 'number' ? row.version : null,
          updated_at: row.updated_at || null
        };
        const data = Object.assign({}, row.payload || {});
        data.updated_at = row.updated_at;
        data.version = row.version;
        return {
          ok: true,
          json: async () => data
        };
      } catch (e) {
        return { ok: false };
      }
    },

    async compareAndSwap(payload, expectedTimestamp) {
      try {
        const token = await getSupabaseAccessToken();
        if (!token) return { ok: false, authRequired: true };
        const session = loadSupabaseSession();
        const userId = (session && session.user_id) || extractUserIdFromJwt(token) || '';
        const nowIso = new Date().toISOString();

        // Ensure we have current row metadata before attempting conditional write
        if (!cloudSyncMeta) {
          await this.read();
        }

        // Case 1: Existing row -> conditional PATCH (true Compare-And-Swap)
        if (cloudSyncMeta && cloudSyncMeta.exists) {
          let queryFilter = '';
          const patchBody = {
            payload: payload,
            updated_at: nowIso
          };
          if (typeof cloudSyncMeta.version === 'number' && (cloudSyncMeta.user_id || userId)) {
            const targetUid = cloudSyncMeta.user_id || userId;
            queryFilter = `user_id=eq.${encodeURIComponent(targetUid)}&version=eq.${encodeURIComponent(String(cloudSyncMeta.version))}`;
            patchBody.version = cloudSyncMeta.version + 1;
          } else if (cloudSyncMeta.updated_at) {
            const targetId = cloudSyncMeta.id || userId || SUPABASE_SYNC_CONFIG.rowId;
            queryFilter = `id=eq.${encodeURIComponent(targetId)}&updated_at=eq.${encodeURIComponent(cloudSyncMeta.updated_at)}`;
          } else {
            const targetId = cloudSyncMeta.id || userId || SUPABASE_SYNC_CONFIG.rowId;
            queryFilter = `id=eq.${encodeURIComponent(targetId)}`;
          }

          const resp = await fetch(`${SUPABASE_SYNC_CONFIG.url}/rest/v1/${SUPABASE_SYNC_CONFIG.table}?${queryFilter}`, {
            method: 'PATCH',
            headers: {
              'apikey': SUPABASE_SYNC_CONFIG.publishableKey,
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
              'Prefer': 'return=representation'
            },
            body: JSON.stringify(patchBody)
          });
          if (resp.status === 401 || resp.status === 403) {
            return { ok: false, authRequired: true };
          }
          if (!resp.ok) {
            return { ok: false };
          }
          const updatedRows = await resp.json().catch(() => []);
          if (!Array.isArray(updatedRows) || updatedRows.length === 0) {
            // Concurrent modification detected: expected version/timestamp did not match
            return { ok: false, conflict: true };
          }
          const updated = updatedRows[0];
          cloudSyncMeta = {
            exists: true,
            id: updated.id || cloudSyncMeta.id,
            user_id: updated.user_id || cloudSyncMeta.user_id || userId,
            version: typeof updated.version === 'number' ? updated.version : cloudSyncMeta.version,
            updated_at: updated.updated_at || nowIso
          };
          return { ok: true, version: cloudSyncMeta.version, updated_at: cloudSyncMeta.updated_at };
        }

        // Case 2: No row exists yet -> atomic INSERT without merge-duplicates overwrite
        const insertBody = {
          id: userId || SUPABASE_SYNC_CONFIG.rowId,
          payload: payload,
          updated_at: nowIso
        };
        if (userId) insertBody.user_id = userId;
        const resp = await fetch(`${SUPABASE_SYNC_CONFIG.url}/rest/v1/${SUPABASE_SYNC_CONFIG.table}`, {
          method: 'POST',
          headers: {
            'apikey': SUPABASE_SYNC_CONFIG.publishableKey,
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
          },
          body: JSON.stringify(insertBody)
        });
        if (resp.status === 409) {
          return { ok: false, conflict: true };
        }
        if (resp.status === 401 || resp.status === 403) {
          return { ok: false, authRequired: true };
        }
        if (!resp.ok) {
          return { ok: false };
        }
        const insertedRows = await resp.json().catch(() => []);
        const inserted = Array.isArray(insertedRows) && insertedRows[0] ? insertedRows[0] : insertBody;
        cloudSyncMeta = {
          exists: true,
          id: inserted.id || insertBody.id,
          user_id: inserted.user_id || userId || null,
          version: typeof inserted.version === 'number' ? inserted.version : null,
          updated_at: inserted.updated_at || nowIso
        };
        return { ok: true, version: cloudSyncMeta.version, updated_at: cloudSyncMeta.updated_at };
      } catch (e) {
        return { ok: false };
      }
    }
  };

  const privateSync = supabaseSyncAdapter;
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
      let needsAuth = false;
      if (privateSync) {
        try {
          const resp = await privateSync.read();
          if (resp && resp.ok) {
            data = await resp.json();
          } else if (resp && resp.authRequired) {
            needsAuth = true;
          }
        } catch(e) {}
      }
      if (data) {
        const remoteTimestamp = data.updated_at ? new Date(data.updated_at).getTime() : 0;
        if (remoteTimestamp) {
          cloudLastUpdated = remoteTimestamp;
        }

        const lastLocalVersion = Number(localStorage.getItem('ido_job_last_cloud_version') || 0);
        const remoteVersion = typeof data.version === 'number' ? data.version : 0;
        const isNewRemoteVersion = (remoteVersion > 0 && remoteVersion > lastLocalVersion);

        const lastLocalEdit = Number(localStorage.getItem(LAST_LOCAL_EDIT_KEY) || 0);
        const storedTriage = localStorage.getItem(STORAGE_KEY);
        const storedStarred = localStorage.getItem(STARRED_STORAGE_KEY);
        const isClientVirgin = (lastLocalEdit === 0) && (!storedTriage || storedTriage === '{}') && (!storedStarred || storedStarred === '{}');
        const shouldMirrorFromRemote = forceMirror || isClientVirgin || isNewRemoteVersion || (remoteTimestamp > (lastLocalEdit + 500));

        if (shouldMirrorFromRemote) {
          if (remoteVersion > 0) {
            localStorage.setItem('ido_job_last_cloud_version', String(remoteVersion));
          }
          const restoredMap = loadRestoredJobs();
          const purgedMap = loadPurgedJobs();
          const newJobStates = {};
          if (Array.isArray(data.purged)) {
            data.purged.forEach(link => {
              newJobStates[link] = 'purged';
              const c = getCanonicalJobKey(link);
              if (c) newJobStates[c] = 'purged';
            });
          }
          // Preserve locally purged tombstones so remote mirror does not un-purge freshly purged jobs
          Object.keys(purgedMap).forEach(link => {
            newJobStates[link] = 'purged';
            const c = getCanonicalJobKey(link);
            if (c) newJobStates[c] = 'purged';
          });
          if (Array.isArray(data.saved)) {
            data.saved.forEach(link => {
              const c = getCanonicalJobKey(link);
              const isPurged = Boolean(newJobStates[link] === 'purged' || (c && newJobStates[c] === 'purged') || purgedMap[link] || (c && purgedMap[c]));
              if (!isPurged) {
                newJobStates[link] = 'saved';
                if (c) newJobStates[c] = 'saved';
              }
            });
          }
          if (Array.isArray(data.rejected)) {
            data.rejected.forEach(link => {
              const c = getCanonicalJobKey(link);
              const isPurged = Boolean(newJobStates[link] === 'purged' || (c && newJobStates[c] === 'purged') || purgedMap[link] || (c && purgedMap[c]));
              const isRestored = Boolean(restoredMap[link] || (c && restoredMap[c]));
              if (!isPurged && !isRestored) {
                newJobStates[link] = 'rejected';
                if (c) newJobStates[c] = 'rejected';
              }
            });
          }
          const newStarredJobs = {};
          if (Array.isArray(data.starred)) {
            data.starred.forEach(link => {
              const c = getCanonicalJobKey(link);
              const isPurged = Boolean(newJobStates[link] === 'purged' || (c && newJobStates[c] === 'purged') || purgedMap[link] || (c && purgedMap[c]));
              if (!isPurged) {
                newStarredJobs[link] = true;
                if (c) newStarredJobs[c] = true;
              }
            });
          }
          // Clean up conflicting starred states (rejection/purged trumps starred)
          Object.keys(newStarredJobs).forEach(link => {
            const c = getCanonicalJobKey(link);
            if (newJobStates[link] === 'purged' || newJobStates[link] === 'rejected' || (c && (newJobStates[c] === 'purged' || newJobStates[c] === 'rejected'))) {
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
          if (remoteVersion > 0) {
            localStorage.setItem('ido_job_last_cloud_version', String(remoteVersion));
          }
          // Device has existing local edits: reconcile safely without overwriting user choices
          let changed = false;
          const unstarredMap = loadUnstarredJobs();
          const restoredMap = loadRestoredJobs();
          const purgedMap = loadPurgedJobs();

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

          // Apply local purged tombstones to ensure local purges are never lost
          Object.keys(purgedMap).forEach(link => {
            const c = getCanonicalJobKey(link);
            if (jobStates[link] !== 'purged') {
              jobStates[link] = 'purged';
              changed = true;
            }
            if (c && jobStates[c] !== 'purged') {
              jobStates[c] = 'purged';
              changed = true;
            }
          });

          if (Array.isArray(data.rejected)) {
            data.rejected.forEach(link => {
              const c = getCanonicalJobKey(link);
              const isPurged = Boolean(purgedMap[link] || (c && purgedMap[c]) || jobStates[link] === 'purged' || (c && jobStates[c] === 'purged'));
              if (!isPurged && !restoredMap[link] && !restoredMap[c] && (!jobStates[link] || jobStates[link] === 'pending')) {
                jobStates[link] = 'rejected';
                if (c) jobStates[c] = 'rejected';
                changed = true;
              }
            });
          }
          if (Array.isArray(data.saved)) {
            data.saved.forEach(link => {
              const c = getCanonicalJobKey(link);
              const isPurged = Boolean(purgedMap[link] || (c && purgedMap[c]) || jobStates[link] === 'purged' || (c && jobStates[c] === 'purged'));
              if (!isPurged && !jobStates[link] && !jobStates[c]) {
                jobStates[link] = 'saved';
                if (c) jobStates[c] = 'saved';
                changed = true;
              }
            });
          }
          if (Array.isArray(data.starred)) {
            data.starred.forEach(link => {
              const c = getCanonicalJobKey(link);
              const isPurged = Boolean(purgedMap[link] || (c && purgedMap[c]) || jobStates[link] === 'purged' || (c && jobStates[c] === 'purged'));
              if (!isPurged && !unstarredMap[link] && !unstarredMap[c] && !starredJobs[link] && !starredJobs[c]) {
                if (jobStates[link] !== 'purged' && jobStates[link] !== 'rejected' && (!c || (jobStates[c] !== 'purged' && jobStates[c] !== 'rejected'))) {
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
        setCloudSyncStatus(needsAuth ? 'local' : 'synced', Date.now());
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

  async function pushCloudSync(isConflictRetry = false) {
    if (isSyncInProgress) return;
    if (typeof navigator !== 'undefined' && navigator.onLine === false) {
      setCloudSyncStatus('offline');
      return;
    }
    isSyncInProgress = true;
    setCloudSyncStatus('syncing');

    try {
      const purgedMap = loadPurgedJobs();
      const purgedSet = new Set(Object.keys(jobStates).filter(id => jobStates[id] === 'purged' && !Boolean(starredJobs[id])));
      Object.keys(purgedMap).forEach(k => {
        if (!Boolean(starredJobs[k])) purgedSet.add(k);
      });
      const purgedList = Array.from(purgedSet);
      const rejectedList = Object.keys(jobStates).filter(id => jobStates[id] === 'rejected' && !Boolean(starredJobs[id]) && !purgedSet.has(id));
      const savedList = Object.keys(jobStates).filter(id => jobStates[id] === 'saved' && !Boolean(starredJobs[id]) && !purgedSet.has(id));
      const starredList = Object.keys(starredJobs).filter(id => Boolean(starredJobs[id]) && !purgedSet.has(id));
      
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
        cloudLastUpdated = resp.updated_at ? new Date(resp.updated_at).getTime() : Date.now();
        setCloudSyncStatus('synced', cloudLastUpdated);
      } else if (resp.conflict && !isConflictRetry) {
        // Concurrent update from another device: merge remote changes first, then retry CAS once
        isSyncInProgress = false;
        await fetchCloudSync(false);
        return await pushCloudSync(true);
      } else if (resp.authRequired) {
        setCloudSyncStatus('local');
      } else {
        setCloudSyncStatus('offline');
      }
    } catch (e) {
      setCloudSyncStatus('offline');
    } finally {
      isSyncInProgress = false;
    }
  }

  if (typeof window !== 'undefined' && typeof window.addEventListener === 'function' && typeof process === 'undefined') {
    window.addEventListener('online', () => { fetchCloudSync(); });
    window.addEventListener('offline', () => { setCloudSyncStatus('offline'); });
    if (typeof document !== 'undefined' && typeof document.addEventListener === 'function') {
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
          fetchCloudSync();
        }
      });
    }
    window.addEventListener('focus', () => {
      fetchCloudSync();
    });
    // Background polling every 25 seconds when tab is active to keep desktop and phone in sync
    if (typeof setInterval === 'function') {
      setInterval(() => {
        if (typeof document !== 'undefined' && document.visibilityState === 'visible' && !isSyncInProgress) {
          fetchCloudSync();
        }
      }, 25000);
    }
  }

  function extractJobId(link) {
    if (!link) return '';
    const match = link.match(/(\d{7,12})/);
    return match ? match[1] : link;
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
    if (img.naturalWidth === 0) {
      handleCompanyLogoError(img, domain);
      return;
    }
    if (img.naturalWidth <= 16 && img.naturalHeight <= 16 && step === 1 && domain) {
      handleCompanyLogoError(img, domain);
    }
  }

  function hideCompanyLogoElement(img) {
    const circle = img.closest('.card-logo-circle');
    if (circle) {
      circle.style.display = 'none';
    }
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
        <div class="job-company-logo company-logo-box" title="${safeComp}">
          <img src="${info.primaryUrl}" 
               alt="${safeComp}" 
               class="job-logo-img company-logo" 
               loading="lazy" 
               decoding="async" 
               data-step="${info.initialStep}"
               onload="handleCompanyLogoLoad(this, '${safeDom}')" 
               onerror="if(typeof handleCompanyLogoError==='function'){handleCompanyLogoError(this, '${safeDom}');}else{const c=this.closest('.card-logo-circle')||this.closest('.job-company-logo');if(c)c.style.display='none';}" />
        </div>
      `;
    }
    return '';
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
    const cleaned = String(rawUrl).replace(/[\u0000-\u001F\u007F]/g, '').trim();
    if (!cleaned) return '#';
    try {
      const url = new URL(cleaned);
      if (!['http:', 'https:', 'mailto:'].includes(url.protocol) || url.username || url.password) return '#';
      return escapeHtml(url.href);
    } catch (_) {
      return '#';
    }
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

  // Modern Web Guidance: light-dismiss on backdrop click for native modal dialogs
  document.addEventListener('click', (e) => {
    if (!e.target || e.target.nodeName !== 'DIALOG') return;
    const dlg = e.target;
    if (!dlg.open) return;
    if (typeof dlg.getBoundingClientRect !== 'function') return;
    const rect = dlg.getBoundingClientRect();
    const isInside = (
      rect.top <= e.clientY && e.clientY <= rect.top + rect.height &&
      rect.left <= e.clientX && e.clientX <= rect.left + rect.width
    );
    if (!isInside) {
      closeDialogEl(dlg);
    }
  });

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
      btn.setAttribute('title', 'הרחב ניתוח מלא');
      btn.setAttribute('aria-label', 'הרחב ניתוח מלא');
      btn.setAttribute('data-tooltip', 'הרחב ניתוח מלא');
      btn.innerHTML = '<i class="ph-bold ph-caret-down"></i>';
    } else {
      details.classList.add('expanded');
      btn.classList.add('expanded');
      btn.setAttribute('aria-expanded', 'true');
      btn.setAttribute('title', 'הסתר ניתוח מלא');
      btn.setAttribute('aria-label', 'הסתר ניתוח מלא');
      btn.setAttribute('data-tooltip', 'הסתר ניתוח מלא');
      btn.innerHTML = '<i class="ph-bold ph-caret-up"></i>';
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
      const loc = escapeHtml(normalizeJobLocation(job.location) || 'מיקום לא צוין');
      const jobSum = escapeHtml(stripEmojis(job.job_summary || job.company_summary || 'לא צוין תיאור מלא למשרה.'));
      const strengths = escapeHtml(stripEmojis(job.experience_strengths || job.reasoning || 'אין ניתוח התאמה מאומת למשרה זו.'));
      const quickInsight = escapeHtml(stripEmojis(job.reasoning || job.experience_strengths || job.job_summary || 'אין ניתוח התאמה מאומת למשרה זו.'));
      const fitGaps = escapeHtml(stripEmojis(job.fit_gaps || 'אין מספיק מידע לאימות פערי ההתאמה.'));
      const companyReqs = isolateBiDiTerms(escapeHtml(stripEmojis(job.company_requirements || job.key_highlights || (job.snippet ? job.snippet.slice(0, 160) + '...' : '') || 'דרישות סף טכניות בהתאם לתיאור המשרה (פירוט מלא בקישור להגשה).')));
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
        else if (link.includes('greenhouse.io') || link.includes('greenhouse')) sourceName = 'Greenhouse';
        else if (link.includes('lever.co') || link.includes('lever')) sourceName = 'Lever';
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
      } else if (sourceName.toLowerCase().includes('greenhouse')) {
        sourceChipStyle = 'color: #10b981; border-color: rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.12);';
        sourceIcon = 'ph-tree';
      } else if (sourceName.toLowerCase().includes('lever')) {
        sourceChipStyle = 'color: #f59e0b; border-color: rgba(245, 158, 11, 0.4); background: rgba(245, 158, 11, 0.12);';
        sourceIcon = 'ph-gear-six';
      }

      const isStarred = Boolean(starredJobs[id]);
      const state = jobStates[id] || 'pending';
      const classifiedRegion = classifyJobRegion(loc);
      const salaryTagHtml = formatJobSalaryTag(job);
      const isInactive = isJobInactive(link);
      const inactiveBadgeHtml = isInactive ? `<span class="dashboard-chip rose" style="font-size: 11px; padding: 2px 7px; gap: 4px; display: inline-flex; align-items: center;" title="${escapeHtml(getJobInactiveReason(link))}"><i class="ph-duotone ph-link-break"></i> משרה נסגרה</span>` : '';

      const curatedTags = getJobCuratedTags(job);
      const pastelThemes = [
        'card-pastel-peach',
        'card-pastel-mint',
        'card-pastel-lavender',
        'card-pastel-sky',
        'card-pastel-rose',
        'card-pastel-slate'
      ];
      const pastelClass = pastelThemes[idx % pastelThemes.length];

      let salaryValHtml = 'שכר ענפי גמיש';
      if (job.salary_range && job.salary_range.trim() && job.salary_range !== 'לא צוין במודעה' && job.salary_range !== 'לא צוין') {
        salaryValHtml = escapeHtml(normalizeSalaryRange(job.salary_range.trim()));
      }

      let tagsHtml = '';
      if (curatedTags && curatedTags.length > 0) {
        const pills = curatedTags.map(t => `<span class="card-tag-pill"><i class="${escapeHtml(t.icon)}"></i><span dir="auto">${escapeHtml(t.label)}</span></span>`).join('');
        tagsHtml = `<div class="card-tags-row">${pills}</div>`;
      }

      const card = document.createElement('article');
      card.setAttribute('data-id', id);
      card.setAttribute('data-sector', secKey);
      card.setAttribute('data-classified-sector', classifiedSector);
      card.setAttribute('data-location', loc.toLowerCase());
      card.setAttribute('data-region', classifiedRegion);
      card.setAttribute('data-starred', isStarred ? 'true' : 'false');
      card.setAttribute('data-score', score);
      card.className = `dashboard-card job-card ${pastelClass} ${isStarred ? 'is-starred-card' : ''}`;

      card.innerHTML = `
        <!-- Top Row: Date Pill & Actions -->
        <div class="card-top-row">
          <span class="card-date-pill">
            <i class="ph-duotone ph-calendar-blank" style="font-size: 11px;"></i>
            <span>${escapeHtml(jobDate)}</span>
          </span>
          <div class="card-top-actions">
            <button type="button" class="btn-star ${isStarred ? 'is-starred' : ''}" onclick="toggleStar(${escapeHtml(JSON.stringify(String(id)))}, event)" title="${isStarred ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב'}" aria-label="${isStarred ? 'הסר כוכב מהמשרה' : 'סמן משרה בכוכב'}">
              <i class="${isStarred ? 'ph-fill ph-star' : 'ph-bold ph-star'}"></i>
            </button>
            <button type="button" class="card-action-icon-btn action-save-btn ${state === 'saved' ? 'saved-active' : ''}" onclick="toggleAction(${escapeHtml(JSON.stringify(String(id)))}, 'saved', event)" title="${state === 'saved' ? 'נשמר להגשה (לחץ להסרה)' : 'שמור להגשה'}" aria-label="שמור להגשה">
              <i class="${state === 'saved' ? 'ph-fill ph-bookmark-simple' : 'ph-duotone ph-bookmark-simple'}"></i>
            </button>
            <button type="button" class="btn-copy-link" onclick="copyJobLink(${escapeHtml(JSON.stringify(String(link)))}, event)" title="העתק קישור למשרה" aria-label="העתק קישור למשרה">
              <i class="ph-bold ph-share-network"></i>
            </button>
          </div>
        </div>

        <!-- Body Header: Company + Job Title + Logo -->
        <div class="card-body-header">
          <div class="card-title-stack">
            <div class="card-company-name" dir="auto" title="${safeCompany}"><bdi>${safeCompany}</bdi></div>
            <h2 class="card-job-title" dir="auto" title="${safeTitle}"><bdi>${safeTitle}</bdi></h2>
          </div>
          ${logoHtml ? `<div class="card-logo-circle">${logoHtml}</div>` : ''}
        </div>

        <!-- Tags Row: Match Score + Inactive + Curated -->
        <div class="card-tags-row">
          <span class="card-tag-pill card-tag-match" style="font-weight: 700; color: #059669; background: rgba(16, 185, 129, 0.12); border-color: rgba(16, 185, 129, 0.25);">
            <i class="ph-duotone ph-lightning"></i> ${score}% התאמה
          </span>
          ${inactiveBadgeHtml}
          ${curatedTags && curatedTags.length > 0 ? curatedTags.map(t => `<span class="card-tag-pill"><i class="${escapeHtml(t.icon)}"></i><span dir="auto">${escapeHtml(t.label)}</span></span>`).join('') : ''}
        </div>

        <!-- Key Requirements Snippet -->
        <div class="card-reqs-preview" dir="auto">
          <strong>דרישות סף:</strong> ${companyReqs}
        </div>

        <!-- Bottom Row: Dedicated Salary/Location Tier & Action Controls -->
        <div class="card-bottom-row">
          <div class="card-salary-location">
            <div class="card-salary-val" dir="auto"><bdi>${salaryValHtml}</bdi></div>
            <div class="card-location-text"><i class="ph-duotone ph-map-pin"></i> <span>${loc}</span></div>
          </div>

          <div class="card-actions-cluster">
            <button type="button" class="btn-details-pill" onclick="openJobModal(${escapeHtml(JSON.stringify(String(id)))})" title="צפייה בפרטי משרה מלאים וניתוח">
              <span>פרטים</span>
              <i class="ph-bold ph-arrow-left"></i>
            </button>
            <div class="card-actions-subgroup">
              ${state === 'rejected' ? `
              <button type="button" onclick="restoreJob(${escapeHtml(JSON.stringify(String(id)))}, event)" class="card-action-icon-btn action-restore-btn" title="שחזר לחדשות" aria-label="שחזר לחדשות" data-tooltip="שחזר לחדשות">
                <i class="ph-duotone ph-arrow-counter-clockwise"></i>
              </button>
              <button type="button" onclick="purgeJobPermanently(${escapeHtml(JSON.stringify(String(id)))}, event)" class="card-action-icon-btn action-reject-btn rejected-active" title="מחיקה לצמיתות" aria-label="מחיקה לצמיתות" data-tooltip="מחיקה לצמיתות">
                <i class="ph-duotone ph-trash-simple"></i>
              </button>
              ` : `
              <button type="button" onclick="toggleAction(${escapeHtml(JSON.stringify(String(id)))}, 'rejected', event)" class="card-action-icon-btn action-reject-btn" title="הסר משרה" aria-label="הסר משרה" data-tooltip="הסר משרה">
                <i class="ph-duotone ph-trash"></i>
              </button>
              `}
              ${Array.isArray(altLinksStore[id]) && altLinksStore[id].length > 0 ? `
              <a href="${sanitizeUrl(altLinksStore[id][0])}" target="_blank" rel="noopener noreferrer" class="card-action-icon-btn btn-alt-link" onclick="event.stopPropagation()" title="מקור נוסף להגשת מועמדות (מוזג מכפילות)" aria-label="מקור נוסף" data-tooltip="מקור נוסף (${altLinksStore[id].length})">
                <i class="ph-duotone ph-link"></i>
              </a>
              ` : ''}
              <a href="${safeLink}" target="_blank" rel="noopener noreferrer" class="apply-icon-btn" title="הגש מועמדות" aria-label="הגש מועמדות" data-tooltip="הגש מועמדות" onclick="event.stopPropagation()">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
              </a>
            </div>
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
    const loc = escapeHtml(normalizeJobLocation(job.location) || 'מיקום לא צוין');
    const jobDate = escapeHtml(job.date || 'היום');
    const classifiedSector = classifyJobSector(job);
    const domain = escapeHtml(stripEmojis(job.company_domain_product || job.company_summary || 'מידע על החברה לא צוין'));
    const jobSum = escapeHtml(stripEmojis(job.job_summary || job.company_summary || 'לא צוין תיאור מלא למשרה.'));
    const strengths = escapeHtml(stripEmojis(job.experience_strengths || job.reasoning || 'אין ניתוח התאמה מאומת למשרה זו.'));
    const companyReqs = isolateBiDiTerms(escapeHtml(stripEmojis(job.company_requirements || job.key_highlights || (job.snippet ? job.snippet.slice(0, 160) + '...' : '') || 'דרישות סף טכניות בהתאם לתיאור המשרה.')));
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
      else if (link.includes('greenhouse.io') || link.includes('greenhouse')) sourceName = 'Greenhouse';
      else if (link.includes('lever.co') || link.includes('lever')) sourceName = 'Lever';
      else sourceName = 'LinkedIn';
    }
    let sourceIcon = 'ph-linkedin-logo';
    if (sourceName.toLowerCase().includes('drushim') || sourceName.includes('דרושים')) {
      sourceIcon = 'ph-briefcase';
    } else if (sourceName.toLowerCase().includes('comeet')) {
      sourceIcon = 'ph-buildings';
    } else if (sourceName.toLowerCase().includes('greenhouse')) {
      sourceIcon = 'ph-tree';
    } else if (sourceName.toLowerCase().includes('lever')) {
      sourceIcon = 'ph-gear-six';
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

    const isInactive = isJobInactive(link);
    const inactiveBannerHtml = isInactive ? `
      <div style="margin-bottom: 14px; padding: 10px 14px; border-radius: 12px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.35); color: #fca5a5; font-size: 13px; display: flex; align-items: center; gap: 10px;">
        <i class="ph-duotone ph-link-break" style="font-size: 18px; flex-shrink: 0;"></i>
        <span><strong>שים לב:</strong> משרה זו אותרה כסגורה באתר המקור (${escapeHtml(getJobInactiveReason(link))}).</span>
      </div>
    ` : '';

    body.innerHTML = `
      ${inactiveBannerHtml}
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
        const purgedMap = loadPurgedJobs();
        keys.forEach(k => {
          jobStates[k] = 'purged';
          purgedMap[k] = true;
        });
        savePurgedJobs(purgedMap);
        showToast('ph-trash', 'המשרה נמחקה לצמיתות ולא תוצג שוב');
      } else {
        const purgedMap = loadPurgedJobs();
        const restoredMap = loadRestoredJobs();
        keys.forEach(k => {
          jobStates[k] = 'rejected';
          delete purgedMap[k];
          delete restoredMap[k];
        });
        for (const k of Object.keys(purgedMap)) {
          if (keys.some(ref => getCanonicalJobKey(k) === getCanonicalJobKey(ref))) delete purgedMap[k];
        }
        for (const k of Object.keys(restoredMap)) {
          if (keys.some(ref => getCanonicalJobKey(k) === getCanonicalJobKey(ref))) delete restoredMap[k];
        }
        savePurgedJobs(purgedMap);
        saveRestoredJobs(restoredMap);
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
    const purgedMap = loadPurgedJobs();
    keys.forEach(k => {
      delete starredJobs[k];
      jobStates[k] = 'purged';
      purgedMap[k] = true;
    });
    for (const k of Object.keys(starredJobs)) {
      if (keys.some(ref => getCanonicalJobKey(k) === getCanonicalJobKey(ref))) delete starredJobs[k];
    }
    savePurgedJobs(purgedMap);
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
    const purgedMap = loadPurgedJobs();
    keys.forEach(k => {
      restoredMap[k] = true;
      delete purgedMap[k];
    });
    for (const k of Object.keys(purgedMap)) {
      if (keys.some(ref => getCanonicalJobKey(k) === getCanonicalJobKey(ref))) delete purgedMap[k];
    }
    saveRestoredJobs(restoredMap);
    savePurgedJobs(purgedMap);

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
    const hasVal = Boolean(val && val.trim().length > 0);
    if (wrapper) {
      wrapper.classList.toggle('has-value', hasVal);
    }
    const clearBtn = document.querySelector('.search-clear-btn');
    if (clearBtn) {
      clearBtn.classList.toggle('is-hidden', !hasVal);
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
    const clearBtn = document.querySelector('.search-clear-btn');
    if (clearBtn) {
      clearBtn.classList.add('is-hidden');
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
    const clearBtn = document.querySelector('.search-clear-btn');
    if (clearBtn) clearBtn.classList.add('is-hidden');

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

      if (saveBtn) {
        if (state === 'saved') {
          saveBtn.classList.add('saved-active');
          if (saveText) saveText.textContent = "נשמר להגשה";
          saveBtn.setAttribute('title', 'נשמר להגשה (לחץ להסרה)');
          saveBtn.setAttribute('data-tooltip', 'נשמר להגשה');
          const saveIcon = saveBtn.querySelector('i');
          if (saveIcon) saveIcon.className = 'ph-fill ph-bookmark-simple';
          if (rejectBtn) rejectBtn.classList.remove('rejected-active');
        } else if (state === 'rejected') {
          if (rejectBtn) rejectBtn.classList.add('rejected-active');
          saveBtn.classList.remove('saved-active');
          if (saveText) saveText.textContent = "שמור להגשה";
          saveBtn.setAttribute('title', 'שמור להגשה');
          saveBtn.setAttribute('data-tooltip', 'שמור להגשה');
          const saveIcon = saveBtn.querySelector('i');
          if (saveIcon) saveIcon.className = 'ph-duotone ph-bookmark-simple';
        } else {
          saveBtn.classList.remove('saved-active');
          if (rejectBtn) rejectBtn.classList.remove('rejected-active');
          if (saveText) saveText.textContent = "שמור להגשה";
          saveBtn.setAttribute('title', 'שמור להגשה');
          saveBtn.setAttribute('data-tooltip', 'שמור להגשה');
          const saveIcon = saveBtn.querySelector('i');
          if (saveIcon) saveIcon.className = 'ph-duotone ph-bookmark-simple';
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
        const reqsEl = card.querySelector('.job-key-requirements-content');

        if (titleEl) highlightSearchTerms(titleEl, searchTerms);
        if (compEl) highlightSearchTerms(compEl, searchTerms);
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
          const totalRejectedInStore = new Set(
            Object.keys(jobStates || {})
              .filter(k => jobStates[k] === 'rejected' || jobStates[k] === 'purged')
              .map(k => getCanonicalJobKey(k))
          ).size;
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

      const isLightMode = typeof document !== 'undefined' && document.documentElement && document.documentElement.getAttribute('data-theme') === 'light';
      const chartTextColor = isLightMode ? '#475569' : '#c0c5be';
      const chartGridColor = isLightMode ? 'rgba(15, 23, 42, 0.08)' : 'rgba(255, 255, 255, 0.08)';
      const tooltipBg = isLightMode ? '#FFFFFF' : '#191d1b';
      const tooltipTitle = isLightMode ? '#0F172A' : '#f5f6f0';
      const tooltipBody = isLightMode ? '#475569' : '#c0c5be';
      const tooltipBorder = isLightMode ? 'rgba(15, 23, 42, 0.12)' : 'rgba(255, 255, 255, 0.16)';

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
              backgroundColor: tooltipBg,
              titleColor: tooltipTitle,
              bodyColor: tooltipBody,
              borderColor: tooltipBorder,
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
              ticks: { stepSize: 1, color: chartTextColor, font: { family: 'Google Sans', size: 11 } },
              grid: { color: chartGridColor }
            },
            x: {
              ticks: { color: chartTextColor, font: { family: 'Google Sans', size: 10 } },
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
        closeCloudModal();
        closeDuplicatesModal();
        closeInactiveJobsModal();
        if (typeof closeJobModal === 'function') closeJobModal();
      }
    });
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

  function isJobInactive(link) {
    if (!cachedInactiveJobsReport || !Array.isArray(cachedInactiveJobsReport.inactive_jobs) || !link) return false;
    const canon = getCanonicalJobKey(link);
    return cachedInactiveJobsReport.inactive_jobs.some(i => getCanonicalJobKey(i.link) === canon);
  }

  function getJobInactiveReason(link) {
    if (!cachedInactiveJobsReport || !Array.isArray(cachedInactiveJobsReport.inactive_jobs) || !link) return '';
    const canon = getCanonicalJobKey(link);
    const item = cachedInactiveJobsReport.inactive_jobs.find(i => getCanonicalJobKey(i.link) === canon);
    return item ? (item.reason || 'המשרה נסגרה לקבלת מועמדויות') : '';
  }

  async function fetchInactiveJobsReport() {
    try {
      const resp = await fetch('data/inactive_jobs.json?t=' + Date.now(), { cache: 'no-store' });
      if (resp && resp.ok) {
        cachedInactiveJobsReport = await resp.json();
        updateInactiveBadgeCount();
      }
    } catch(e) {}
  }

  function updateInactiveBadgeCount() {
    const badge = document.getElementById('inactiveJobsCountBadge');
    if (!badge) return;
    const st = computeInactiveState();
    const count = st.inactiveList.length;
    if (count > 0) {
      badge.textContent = String(count);
      badge.style.display = 'inline-block';
    } else {
      badge.style.display = 'none';
    }
  }

  async function openInactiveJobsModal() {
    const modal = document.getElementById('inactiveJobsModal');
    const content = document.getElementById('inactiveJobsContent');
    if (!modal || !content) return;

    openDialogEl(modal);

    content.innerHTML = `
      <div style="padding: 24px; text-align: center; color: var(--dashboard-muted); font-size: 14px;">
        <i class="ph-duotone ph-spinner-gap ph-spin" style="font-size: 24px; display: block; margin-bottom: 8px;"></i>
        טוען נתוני סריקת משרות שנסגרו...
      </div>
    `;

    await fetchInactiveJobsReport();
    renderInactiveJobsModalContent();
  }

  function closeInactiveJobsModal() {
    const modal = document.getElementById('inactiveJobsModal');
    closeDialogEl(modal);
  }

  async function runLiveJobCheck() {
    await fetchInactiveJobsReport();
    renderInactiveJobsModalContent();
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
    const report = cachedInactiveJobsReport;
    if (report && Array.isArray(report.inactive_jobs)) {
      report.inactive_jobs.forEach(item => {
        const canon = getCanonicalJobKey(item.link);
        if (seen.has(canon)) return;
        if (activeJobsMap.has(canon)) {
          seen.add(canon);
          const job = activeJobsMap.get(canon);
          inactiveList.push({
            link: job.link,
            title: job.title || item.title || 'משרה ללא כותרת',
            company: job.company || item.company || 'חברה לא צוינה',
            reason: item.reason || 'המשרה נסגרה לקבלת מועמדויות',
            status_code: item.status_code || 0
          });
        }
      });
    }

    return { inactiveList, activeJobsMap, totalActive: activeJobsMap.size };
  }

  function inactiveStatusPanelHtml(st) {
    const report = cachedInactiveJobsReport;
    let reportLine = 'סריקה אוטומטית אחרונה';
    if (report && report.scanned_at) {
      let when = report.scanned_at;
      try { when = new Date(report.scanned_at).toLocaleString('he-IL'); } catch (e) {}
      reportLine = `מועד סריקה אחרון: ${escapeHtml(when)}`;
    }
    const count = st.inactiveList.length;
    return `
      <div style="padding: 14px 16px; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; background: rgba(255, 255, 255, 0.03); display: flex; flex-direction: column; gap: 8px; font-size: 13px; color: #cbd5e1;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
          <div style="display: flex; align-items: center; gap: 6px;">
            <i class="ph-duotone ph-clock" style="color: var(--dashboard-cyan);"></i>
            <span>${reportLine}</span>
          </div>
          <span class="dashboard-chip ${count > 0 ? 'rose' : 'lime'}" style="font-size: 12px; padding: 3px 10px;">
            ${count > 0 ? `${count} משרות לא-פעילות אותרו` : 'כל המשרות בלוח פעילות ומאומתות'}
          </span>
        </div>
        <div style="color: var(--dashboard-muted); font-size: 12px; line-height: 1.5;">
          הסריקה האוטומטית בענן מאמתת מדי יום את זמינות דפי המשרות בלינקדאין, דרושים ואתרי קריירה ומזהה מודעות שנסגרו או הוסרו.
        </div>
      </div>`;
  }

  function renderInactiveJobsModalContent() {
    const content = document.getElementById('inactiveJobsContent');
    if (!content) return;

    const st = computeInactiveState();
    const inactiveList = st.inactiveList;
    const panel = inactiveStatusPanelHtml(st);

    if (inactiveList.length === 0) {
      content.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 14px; direction: rtl; text-align: right;">
          ${panel}
          <div style="padding: 28px 16px; text-align: center; color: var(--dashboard-muted); font-size: 14.5px;">
            <div style="font-size: 32px; margin-bottom: 8px; color: var(--dashboard-lime);"><i class="ph-duotone ph-check-circle"></i></div>
            <div style="color: #fff; font-weight: 700; margin-bottom: 4px;">כל המשרות בלוח פעילות ומעודכנות!</div>
            <div>לא אותרו משרות שנסגרו או הוסרו במאגר הפעיל.</div>
          </div>
        </div>
      `;
      return;
    }

    let html = `
      <div style="display: flex; flex-direction: column; gap: 14px; direction: rtl; text-align: right;">
        ${panel}
        <div style="padding: 12px 16px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 12px; font-size: 13px; color: #fca5a5; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
          <div>
            אותרו <strong>${inactiveList.length}</strong> משרות שאינן פעילות עוד או שהגשת המועמדות אליהן נסגרה.
          </div>
          <button type="button" onclick="handleRemoveAllInactiveJobs()" class="dashboard-primary" style="background: rgba(239, 68, 68, 0.85); color: #fff; font-size: 13px; padding: 7px 16px; min-height: 38px; cursor: pointer; border-radius: 10px; border: none; font-weight: 600;">
            <i class="ph-duotone ph-trash"></i> <span>הסר את כולן מלוח המשרות (${inactiveList.length})</span>
          </button>
        </div>
    `;

    inactiveList.forEach((job, idx) => {
      const safeLink = sanitizeUrl(job.link);
      const safeTitle = escapeHtml(job.title);
      const safeCompany = escapeHtml(job.company);
      const safeReason = escapeHtml(job.reason);

      html += `
        <div id="inactive-card-${idx}" style="border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 12px 16px; background: rgba(255, 255, 255, 0.03); display: flex; justify-content: space-between; align-items: center; gap: 12px;">
          <div style="flex: 1; min-width: 0;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
              <span style="font-size: 11px; background: rgba(239, 68, 68, 0.2); color: #fca5a5; padding: 2px 8px; border-radius: 6px; font-weight: 600; border: 1px solid rgba(239, 68, 68, 0.3);">
                ${safeReason}
              </span>
            </div>
            <div style="font-weight: 600; font-size: 14.5px; color: #f1f5f9; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
              ${safeTitle}
            </div>
            <div style="font-size: 12px; color: var(--dashboard-muted); margin-top: 2px;">
              ${safeCompany} | <a href="${safeLink}" target="_blank" rel="noopener noreferrer" style="color: var(--dashboard-cyan); text-decoration: none;">בדיקת קישור המקור</a>
            </div>
          </div>
          <div style="display: flex; gap: 8px; flex-shrink: 0;">
            <button type="button" onclick="handleRemoveInactiveJob(${escapeHtml(JSON.stringify(job.link))}, ${idx})" class="tool-btn" style="background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.4); color: #fca5a5; font-size: 12px; padding: 6px 12px; min-height: 36px; cursor: pointer; border-radius: 8px;">
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
    updateInactiveBadgeCount();
    renderCards();
  }

  function handleRemoveAllInactiveJobs() {
    const st = computeInactiveState();
    const count = st.inactiveList.length;
    st.inactiveList.forEach(item => toggleAction(item.link, 'rejected'));
    renderInactiveJobsModalContent();
    updateInactiveBadgeCount();
    renderCards();
    showToast('ph-trash', `הוסרו בהצלחה ${count} משרות לא פעילות מלוח המשרות`);
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

    recordLocalEdit();
    const purgedMap = loadPurgedJobs();
    rejectedKeys.forEach(id => {
      const keys = getJobKeys(id);
      keys.forEach(k => {
        delete starredJobs[k];
        jobStates[k] = 'purged';
        purgedMap[k] = true;
      });
      jobStates[id] = 'purged';
      purgedMap[id] = true;
    });

    savePurgedJobs(purgedMap);
    saveStarredJobs(starredJobs);
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
     Dashboard Window Exports & Lifecycle (Studio UI reset for clean redesign)
     ========================================================================== */
  window.purgeJobPermanently = purgeJobPermanently;
  window.restoreJob = restoreJob;
  window.clearAllRejected = clearAllRejected;
  window.openDuplicatesModal = openDuplicatesModal;
  window.closeDuplicatesModal = closeDuplicatesModal;
  window.openInactiveJobsModal = openInactiveJobsModal;
  window.closeInactiveJobsModal = closeInactiveJobsModal;
  window.runLiveJobCheck = runLiveJobCheck;
  window.handleRemoveInactiveJob = handleRemoveInactiveJob;
  window.handleRemoveAllInactiveJobs = handleRemoveAllInactiveJobs;

  const THEME_STORAGE_KEY = 'ido_theme_preference';

  function applyDashboardTheme(theme) {
    const normalized = theme === 'light' ? 'light' : 'dark';
    if (typeof document !== 'undefined' && document.documentElement && typeof document.documentElement.setAttribute === 'function') {
      document.documentElement.setAttribute('data-theme', normalized);
    }
    if (typeof document !== 'undefined' && typeof document.getElementById === 'function') {
      const btn = document.getElementById('themeToggleBtn');
      const label = document.getElementById('themeToggleLabel');
      const icon = document.getElementById('themeToggleIcon');
      const isLight = normalized === 'light';
      if (btn && typeof btn.setAttribute === 'function') {
        btn.setAttribute('aria-pressed', isLight ? 'true' : 'false');
        btn.setAttribute('title', isLight ? 'החלף לערכת נושא כהה' : 'החלף לערכת נושא בהירה');
        btn.setAttribute('aria-label', isLight ? 'החלף לערכת נושא כהה' : 'החלף לערכת נושא בהירה');
      }
      if (label) {
        label.textContent = isLight ? 'בהיר' : 'כהה';
      }
      if (icon) {
        icon.className = isLight ? 'ph-duotone ph-moon' : 'ph-duotone ph-sun';
      }
      try {
        if (typeof renderSectorChart === 'function') {
          renderSectorChart();
        }
      } catch (chartErr) {}
    }
    return normalized;
  }

  function initDashboardTheme() {
    let saved = null;
    try {
      if (typeof localStorage !== 'undefined' && localStorage) {
        saved = localStorage.getItem(THEME_STORAGE_KEY);
      }
    } catch (e) {}
    if (saved === 'light' || saved === 'dark') {
      return applyDashboardTheme(saved);
    }
    return applyDashboardTheme('dark');
  }

  function toggleDashboardTheme() {
    let current = 'dark';
    if (typeof document !== 'undefined' && document.documentElement && typeof document.documentElement.getAttribute === 'function') {
      current = document.documentElement.getAttribute('data-theme') || 'dark';
    }
    const next = current === 'light' ? 'dark' : 'light';
    applyDashboardTheme(next);
    try {
      if (typeof localStorage !== 'undefined' && localStorage) {
        localStorage.setItem(THEME_STORAGE_KEY, next);
      }
    } catch (e) {}
    return next;
  }

  window.toggleDashboardTheme = toggleDashboardTheme;
  window.initDashboardTheme = initDashboardTheme;
  window.handleMergeDuplicates = handleMergeDuplicates;
  window.handleRemoveDuplicates = handleRemoveDuplicates;
  window.handleIgnoreGroup = handleIgnoreGroup;


  window.onload = async () => {
    initDashboardTheme();
    updateCubeCountsImmediately();
    updateSortIconAndToast(currentSort, false);
    await fetchJobsData();
    await fetchInactiveJobsReport();
    await fetchCloudSync();

    const rawHash = (window.location.hash || '').replace('#', '').trim();
    if (rawHash === 'saved' || rawHash === 'rejected' || rawHash === 'starred') {
      const cubeEl = document.getElementById('cube_' + rawHash);
      setFilter(rawHash, cubeEl);
    }
  };

  // Hash navigation listener for direct deep-linking
  window.addEventListener('hashchange', () => {
    const h = (window.location.hash || '').replace('#', '').trim();
    if (h === 'saved' || h === 'rejected' || h === 'starred') {
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
