/**
 * render.js - High-Performance DOM Rendering Engine
 * Implements DocumentFragment atomic batching and zero layout thrashing.
 * Renders semantic, zero-emoji job cards matching So-Me Design System tokens.
 */

import { store } from './store.js';
import { updateMapMarkers } from './geoMap.js';

export function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function sanitizeUrl(rawUrl) {
  if (!rawUrl || typeof rawUrl !== 'string') return '#';
  const trimmed = rawUrl.trim();
  const lower = trimmed.toLowerCase();
  if (lower.startsWith('javascript:') || lower.startsWith('data:') || lower.startsWith('vbscript:')) {
    return '#';
  }
  return trimmed;
}

export function stripEmojis(str) {
  if (!str || typeof str !== 'string') return '';
  return str.replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{1F600}-\u{1F64F}\u{1F680}-\u{1F6FF}\u{FE0F}\u{20E3}]/gu, '').trim();
}

export function classifyJobSector(job) {
  if (!job) return 'אנרגיה';
  const secKey = (job.sector_key || '').toLowerCase().trim();
  const sec = (job.sector || '').toLowerCase().trim();
  const title = (job.title || '').toLowerCase().trim();

  if (secKey === 'solar' || ['סולאר', 'solar', 'pv'].some(k => sec.includes(k))) return 'סולאר';
  if (['drones', 'cuas', 'avionics'].includes(secKey) || ['רחפן', 'כטב', 'drone', 'uav', 'אוויוניקה', 'תעופה', 'ביטחון'].some(k => sec.includes(k))) return 'רחפנים';
  if (['natural_gas', 'naturalgas', 'gas'].includes(secKey) || ['גז טבעי', ' גז', 'gas'].some(k => sec.includes(k))) return 'גז טבעי';
  if (['scada', 'control', 'automation'].includes(secKey) || ['scada', 'בקרה', 'control', 'אוטומציה', 'noc'].some(k => sec.includes(k)) || ['scada', 'בקרה', 'control room', 'בקר'].some(k => title.includes(k))) return 'בקרה ו-SCADA';
  if (['energy_tech', 'energytech', 'storage', 'bess'].includes(secKey) || ['אגירה', 'storage', 'bess'].some(k => sec.includes(k))) return 'אגירה';
  if (['operations', 'maintenance'].includes(secKey) || ['תפעול', 'אחזקה', 'מכונות', 'ייצור'].some(k => sec.includes(k))) return 'תפעול ואחזקה';
  return 'אנרגיה';
}

export function classifyJobRegion(locStr) {
  if (!locStr) return 'center';
  const loc = locStr.toLowerCase();
  if (['חיפה', 'haifa', 'צפון', 'north', 'כרמיאל', 'עכו', 'נהריה', 'נצרת', 'עפולה', 'טבריה', 'גליל', 'משגב'].some(k => loc.includes(k))) return 'north';
  if (['שרון', 'sharon', 'נתניה', 'הרצליה', 'רעננה', 'כפר סבא', 'הוד השרון', 'חדרה', 'עמק חפר'].some(k => loc.includes(k))) return 'sharon';
  if (['שפלה', 'רחובות', 'נס ציונה', 'יבנה', 'מודיעין', 'רמלה', 'לוד', 'איירפורט סיטי'].some(k => loc.includes(k))) return 'shfela';
  if (['דרום', 'south', 'באר שבע', 'beer sheva', 'אשדוד', 'אשקלון', 'קריית גת', 'נגב', 'דימונה'].some(k => loc.includes(k))) return 'south';
  if (['ירושלים', 'jerusalem', 'בית שמש'].some(k => loc.includes(k))) return 'jerusalem';
  return 'center';
}

export function getJobCuratedTags(job) {
  if (!job) return [];
  if (Array.isArray(job.curated_tags) && job.curated_tags.length > 0) {
    return job.curated_tags;
  }
  const tags = [];
  const salaryVal = (job.salary_range || '').trim();
  const salarySource = (job.salary_source_type || '').toLowerCase();
  if ((salarySource === 'job_ad' || salarySource === 'ad' || salarySource === 'employer') && salaryVal && salaryVal !== 'לא צוין במודעה' && salaryVal !== 'לא צוין') {
    tags.push({ type: 'tag-salary', icon: 'ph-bold ph-currency-circle-dollar', label: salaryVal });
  }

  const fullText = [job.title, job.company_requirements, job.job_summary, job.experience_strengths, job.reasoning].join(' ').toLowerCase();
  if (/(?:עבודת שטח|טכנאי שטח|מהנדס שטח|הנדסאי שטח|התקנות שטח|field technician|field engineer)/i.test(fullText) && !/ללא עבודת שטח/i.test(fullText)) {
    tags.push({ type: 'tag-field', icon: 'ph-bold ph-wrench', label: 'עבודת שטח' });
  }
  if (/(?:משמרות|24\/7|משמרת לילה|shift work)/i.test(fullText)) {
    tags.push({ type: 'tag-shifts', icon: 'ph-bold ph-clock-countdown', label: 'משמרות / 24/7' });
  }
  if (/(?:היברידי|hybrid|עבודה מרחוק חלקית)/i.test(fullText)) {
    tags.push({ type: 'tag-hybrid', icon: 'ph-bold ph-laptop', label: 'היברידי' });
  }
  return tags.slice(0, 5);
}

export function getCompanyInitials(name) {
  const clean = (name || 'חברה').trim().split(/\s+/).filter(Boolean);
  if (clean.length >= 2) return (clean[0][0] || '') + (clean[1][0] || '');
  if (clean.length === 1 && clean[0].length >= 2) return clean[0].slice(0, 2);
  return clean[0] || 'חב';
}

export function renderCards() {
  if (typeof document === 'undefined') return;
  const container = document.getElementById('cardsContainer');
  if (!container) return;

  const displayJobs = store.getAllAvailableJobs();
  if (!displayJobs || displayJobs.length === 0) {
    const emptyState = document.getElementById('emptyState');
    if (emptyState) emptyState.style.display = 'block';
    container.innerHTML = '';
    updateCubeCountsImmediately();
    return;
  }

  const emptyState = document.getElementById('emptyState');
  if (emptyState) emptyState.style.display = 'none';

  // Sort
  const sortedJobs = [...displayJobs];
  const sort = store.currentSort;
  sortedJobs.sort((a, b) => {
    if (sort === 'score_desc') {
      const sA = Number(a.match_score) || 0;
      const sB = Number(b.match_score) || 0;
      if (sB !== sA) return sB - sA;
      return (b.date || '').localeCompare(a.date || '');
    } else if (sort === 'company_asc') {
      const cA = (a.company || '').trim();
      const cB = (b.company || '').trim();
      return cA.localeCompare(cB, 'he', { sensitivity: 'base' });
    } else {
      const dA = a.date || '0000-00-00';
      const dB = b.date || '0000-00-00';
      if (dA !== dB) return dB.localeCompare(dA);
      return (Number(b.match_score) || 0) - (Number(a.match_score) || 0);
    }
  });

  // Use DocumentFragment for atomic DOM rendering
  const fragment = document.createDocumentFragment();

  sortedJobs.forEach((job, idx) => {
    const id = job.link || `job_${idx}`;
    const score = Math.max(0, Math.min(100, Number(job.base_match_score ?? job.match_score) || 0));
    const company = stripEmojis(job.company || 'חברה');
    const title = stripEmojis(job.title || 'משרה ללא כותרת');
    const link = job.link || '#';
    const secKey = job.sector_key || 'energy';
    const classifiedSector = classifyJobSector(job);
    const loc = escapeHtml(stripEmojis(job.location || 'ישראל'));
    const classifiedRegion = classifyJobRegion(loc);
    const isStarred = store.isStarred(id);

    let scoreClass = 'badge-score-high';
    if (score < 80) scoreClass = 'badge-score-fair';
    else if (score < 90) scoreClass = 'badge-score-med';

    const safeCompany = escapeHtml(company);
    const safeTitle = escapeHtml(title);
    const safeLink = sanitizeUrl(link);
    const safeId = encodeURIComponent(id).replace(/'/g, '%27');

    const curatedTags = getJobCuratedTags(job);
    let tagsHtml = '';
    if (curatedTags && curatedTags.length > 0) {
      const pills = curatedTags.map(t =>
        `<span class="job-tag-pill ${escapeHtml(t.type)}"><i class="${escapeHtml(t.icon)}"></i><span dir="auto">${escapeHtml(t.label)}</span></span>`
      ).join('');
      tagsHtml = `<div class="job-card-tags">${pills}</div>`;
    }

    const card = document.createElement('article');
    card.className = 'job-card';
    card.setAttribute('data-id', id);
    card.setAttribute('data-sector', secKey);
    card.setAttribute('data-classified-sector', classifiedSector);
    card.setAttribute('data-location', loc.toLowerCase());
    card.setAttribute('data-region', classifiedRegion);
    card.setAttribute('data-starred', isStarred ? 'true' : 'false');
    card.setAttribute('data-score', score);

    const initials = getCompanyInitials(company);

    card.innerHTML = `
      <div class="job-card-header">
        <div class="job-card-main-header">
          <div class="job-company-avatar">
            <span>${initials}</span>
          </div>
          <div class="job-card-titles">
            <div class="job-card-company-row">
              <span class="job-company-name" dir="auto">${safeCompany}</span>
              <span class="job-location-text"><i class="ph-duotone ph-map-pin"></i> ${loc}</span>
            </div>
            <h3 class="job-card-title" dir="auto">${safeTitle}</h3>
          </div>
        </div>
        <div class="job-card-header-actions">
          <button type="button" class="btn-star ${isStarred ? 'starred' : ''}" onclick="window.store.toggleStar('${id}')" title="סימון בכוכב" aria-label="סמן בכוכב">
            <i class="${isStarred ? 'ph-fill ph-star' : 'ph-bold ph-star'}"></i>
          </button>
          <div class="job-score-badge ${scoreClass}">
            <span class="score-num">${score}</span>
            <span class="score-pct">%</span>
          </div>
        </div>
      </div>

      ${tagsHtml}

      <div class="job-card-body">
        <p class="job-card-snippet" dir="auto">
          ${escapeHtml(stripEmojis(job.job_summary || job.company_summary || 'תיאור משרה תעשייתית באנרגיה ותפעול.'))}
        </p>
      </div>

      <div class="job-card-footer">
        <div class="job-card-actions">
          <button type="button" class="btn-action btn-save ${store.getJobState(id) === 'saved' ? 'active' : ''}" onclick="window.store.setJobAction('${id}', 'saved')" title="שמור להגשה">
            <i class="ph-bold ph-bookmark-simple"></i>
            <span>שמור</span>
          </button>
          <button type="button" class="btn-action btn-reject ${store.getJobState(id) === 'rejected' ? 'active' : ''}" onclick="window.store.setJobAction('${id}', 'rejected')" title="הסר משרה">
            <i class="ph-bold ph-trash"></i>
            <span>הסר</span>
          </button>
          <button type="button" class="btn-action btn-details" onclick="window.openJobModal('${safeId}')" title="פרטים מלאים">
            <i class="ph-bold ph-arrows-out-simple"></i>
            <span>פרטים</span>
          </button>
        </div>
        <a href="${safeLink}" target="_blank" rel="noopener noreferrer" class="btn-apply-direct" title="הגש מועמדות ישירות">
          <span>הגש עכשיו</span>
          <i class="ph-bold ph-arrow-left"></i>
        </a>
      </div>
    `;

    fragment.appendChild(card);
  });

  // Single DOM insertion
  container.innerHTML = '';
  container.appendChild(fragment);

  updateUI();
  updateCubeCountsImmediately();
}

export function filterCards() {
  if (typeof document === 'undefined') return;
  const cards = document.querySelectorAll('.job-card');
  const filter = store.currentFilter;
  const sector = store.currentSectorFilter;
  const region = store.currentRegionFilter;
  const q = (store.searchQuery || '').toLowerCase().trim();

  let visibleCount = 0;

  cards.forEach(card => {
    const id = card.getAttribute('data-id');
    const isStarred = card.getAttribute('data-starred') === 'true';
    const cardSector = card.getAttribute('data-classified-sector');
    const cardRegion = card.getAttribute('data-region');
    const state = store.getJobState(id);

    let matchFilter = true;
    if (filter === 'starred') matchFilter = isStarred;
    else if (filter === 'saved') matchFilter = (state === 'saved');
    else if (filter === 'rejected') matchFilter = (state === 'rejected');
    else matchFilter = (!state || state === 'new');

    let matchSector = (sector === 'all' || cardSector === sector);
    let matchRegion = (region === 'all' || cardRegion === region);

    let matchSearch = true;
    if (q) {
      const text = card.textContent.toLowerCase();
      matchSearch = text.includes(q);
    }

    if (matchFilter && matchSector && matchRegion && matchSearch) {
      card.classList.remove('is-hidden');
      card.style.display = '';
      visibleCount++;
    } else {
      card.classList.add('is-hidden');
      card.style.display = 'none';
    }
  });

  const emptyState = document.getElementById('emptyState');
  if (emptyState) {
    emptyState.style.display = (visibleCount === 0) ? 'block' : 'none';
  }

  // Update map if available
  if (typeof updateMapMarkers === 'function') {
    updateMapMarkers();
  }
}

export function updateUI() {
  filterCards();
  updateCubeCountsImmediately();
}

export function updateCubeCountsImmediately() {
  if (typeof document === 'undefined') return;
  const counts = store.getCounts();

  const elNew = document.getElementById('statNewCount');
  const elStarred = document.getElementById('statStarredCount');
  const elSaved = document.getElementById('statSavedCount');
  const elRejected = document.getElementById('statRejectedCount');

  if (elNew) elNew.textContent = counts.newCount;
  if (elStarred) elStarred.textContent = counts.starredCount;
  if (elSaved) elSaved.textContent = counts.savedCount;
  if (elRejected) elRejected.textContent = counts.rejectedCount;

  // Segmented progress bar
  const segNew = document.getElementById('progressSegNew');
  const segStarred = document.getElementById('progressSegStarred');
  const segSaved = document.getElementById('progressSegSaved');
  const segRejected = document.getElementById('progressSegRejected');

  if (counts.total > 0) {
    if (segNew) segNew.style.width = `${Math.round((counts.newCount / counts.total) * 100)}%`;
    if (segStarred) segStarred.style.width = `${Math.round((counts.starredCount / counts.total) * 100)}%`;
    if (segSaved) segSaved.style.width = `${Math.round((counts.savedCount / counts.total) * 100)}%`;
    if (segRejected) segRejected.style.width = `${Math.round((counts.rejectedCount / counts.total) * 100)}%`;
  }

  const pctText = document.getElementById('progressPctText');
  if (pctText) pctText.textContent = `${counts.progressPct}%`;
  const chip = document.getElementById('progressSummaryChip');
  if (chip) chip.textContent = `${counts.progressPct}% נסקרו`;
}

export function openJobModal(encodedId) {
  if (typeof document === 'undefined') return;
  const id = decodeURIComponent(encodedId);
  const job = store.allJobsMap[id];
  if (!job) return;

  const modal = document.getElementById('jobDetailsModal');
  const body = document.getElementById('jobModalBody');
  const topActions = document.getElementById('jobModalTopActions');
  const bottomBar = document.getElementById('jobModalBottomBar');
  if (!modal || !body) return;

  const score = Math.max(0, Math.min(100, Number(job.base_match_score ?? job.match_score) || 0));
  const safeComp = escapeHtml(stripEmojis(job.company || 'חברה'));
  const safeTitle = escapeHtml(stripEmojis(job.title || 'משרה'));
  const safeLoc = escapeHtml(stripEmojis(job.location || 'ישראל'));
  const safeLink = sanitizeUrl(job.link);
  const isStarred = store.isStarred(id);

  if (topActions) {
    topActions.innerHTML = `
      <button type="button" class="btn-star ${isStarred ? 'starred' : ''}" onclick="window.store.toggleStar('${id}'); this.classList.toggle('starred');">
        <i class="${isStarred ? 'ph-fill ph-star' : 'ph-bold ph-star'}"></i>
      </button>
      <div class="job-score-badge badge-score-high">
        <span>${score}%</span>
      </div>
    `;
  }

  body.innerHTML = `
    <div style="margin-bottom: 16px;">
      <span style="font-size: 13px; color: var(--dashboard-muted);"><i class="ph-duotone ph-buildings"></i> ${safeComp}</span>
      <h2 style="font-size: 20px; font-weight: 700; margin: 4px 0 8px; color: #fff;">${safeTitle}</h2>
      <div style="display: flex; gap: 12px; font-size: 13px; color: var(--dashboard-muted);">
        <span><i class="ph-duotone ph-map-pin"></i> ${safeLoc}</span>
        <span><i class="ph-duotone ph-calendar-blank"></i> ${escapeHtml(job.date || 'היום')}</span>
      </div>
    </div>

    <div style="background: rgba(0,0,0,0.25); border: 1px solid var(--dashboard-edge); border-radius: 16px; padding: 14px; margin-bottom: 16px;">
      <h4 style="font-size: 14px; font-weight: 600; color: var(--dashboard-lime); margin-bottom: 6px;">
        <i class="ph-duotone ph-sparkle"></i> נקודות חוזק והתאמה
      </h4>
      <p style="font-size: 13px; line-height: 1.6; color: var(--dashboard-text); margin: 0;">
        ${escapeHtml(stripEmojis(job.experience_strengths || job.reasoning || 'נמצאה התאמה לפרופיל המועמד.'))}
      </p>
    </div>

    <div style="margin-bottom: 16px;">
      <h4 style="font-size: 14px; font-weight: 600; margin-bottom: 8px;">תקציר דרישות המשרה</h4>
      <p style="font-size: 13.5px; line-height: 1.6; color: var(--dashboard-muted); margin: 0;">
        ${escapeHtml(stripEmojis(job.company_requirements || job.job_summary || 'פירוט מלא בקישור להגשה.'))}
      </p>
    </div>
  `;

  if (bottomBar) {
    bottomBar.innerHTML = `
      <div style="display: flex; gap: 8px; flex: 1;">
        <button type="button" class="btn-action btn-save" onclick="window.store.setJobAction('${id}', 'saved'); closeJobModal();">
          <i class="ph-bold ph-bookmark-simple"></i> שמור
        </button>
        <button type="button" class="btn-action btn-reject" onclick="window.store.setJobAction('${id}', 'rejected'); closeJobModal();">
          <i class="ph-bold ph-trash"></i> הסר
        </button>
      </div>
      <a href="${safeLink}" target="_blank" rel="noopener noreferrer" class="btn-apply-direct" style="padding: 9px 18px;">
        <span>הגש עכשיו</span>
        <i class="ph-bold ph-arrow-left"></i>
      </a>
    `;
  }

  modal.classList.remove('hidden');
}

export function closeJobModal() {
  if (typeof document === 'undefined') return;
  const modal = document.getElementById('jobDetailsModal');
  if (modal) modal.classList.add('hidden');
}

// Window export
if (typeof window !== 'undefined') {
  window.renderCards = renderCards;
  window.filterCards = filterCards;
  window.updateUI = updateUI;
  window.updateCubeCountsImmediately = updateCubeCountsImmediately;
  window.openJobModal = openJobModal;
  window.closeJobModal = closeJobModal;
  window.escapeHtml = escapeHtml;
  window.sanitizeUrl = sanitizeUrl;
  window.stripEmojis = stripEmojis;
}
