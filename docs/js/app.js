/**
 * app.js - Main Bootstrap Controller (ES Architecture)
 * Orchestrates Store, ATS Engine, GeoMap, Exporter, and Render Modules.
 * Binds debounced filters, sorting, search, and mode-switching events.
 */

import { store } from './modules/store.js';
import * as atsEngine from './modules/atsEngine.js';
import * as geoMap from './modules/geoMap.js';
import { exportSavedToExcel } from './modules/export.js';
import {
  renderCards,
  filterCards,
  updateUI,
  updateCubeCountsImmediately,
  openJobModal,
  closeJobModal,
  escapeHtml,
  sanitizeUrl,
  stripEmojis
} from './modules/render.js';

// Expose modules and core APIs to window for legacy templates & headless test runners
if (typeof window !== 'undefined') {
  window.store = store;
  window.atsEngine = atsEngine;
  window.geoMap = geoMap;
  window.exportSavedToExcel = exportSavedToExcel;

  window.renderCards = renderCards;
  window.filterCards = filterCards;
  window.updateUI = updateUI;
  window.updateCubeCountsImmediately = updateCubeCountsImmediately;
  window.openJobModal = openJobModal;
  window.closeJobModal = closeJobModal;
  window.escapeHtml = escapeHtml;
  window.sanitizeUrl = sanitizeUrl;
  window.stripEmojis = stripEmojis;

  // ATS symbols
  window.CANONICAL_CV_PROFILE = atsEngine.CANONICAL_CV_PROFILE;
  window.STATUTORY_HARD_GATES = atsEngine.STATUTORY_HARD_GATES;
  window.KEYWORD_TAXONOMY = atsEngine.KEYWORD_TAXONOMY;
  window.ATS_STRUCTURAL_RULES = atsEngine.ATS_STRUCTURAL_RULES;
  window.evaluateHardGates = atsEngine.evaluateHardGates;
  window.extractMissingKeywords = atsEngine.extractMissingKeywords;
  window.checkAtsStructuralCompliance = atsEngine.checkAtsStructuralCompliance;
  window.runAtsJobMatching = atsEngine.runAtsJobMatching;
  window.generateCvBulletActionItem = atsEngine.generateCvBulletActionItem;

  // Map symbols
  window.initLiveJobsMap = geoMap.initLiveJobsMap;
  window.updateMapMarkers = geoMap.updateMapMarkers;
  window.getJobLatLng = geoMap.getJobLatLng;
}

// Mode Switcher Logic
export function switchDashboardAppMode(mode, updateHash = true) {
  if (typeof document === 'undefined') return;
  const targetMode = (mode === 'studio') ? 'studio' : 'radar';

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
    if (updateHash && typeof window !== 'undefined' && window.location.hash !== '#studio') {
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
    if (updateHash && typeof window !== 'undefined' && window.location.hash !== '#radar') {
      window.location.hash = '#radar';
    }
  }

  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('ido_app_active_mode', targetMode);
    }
  } catch (e) {}
}

export function switchStudioModule(moduleId) {
  if (typeof document === 'undefined') return;
  const modules = ['ats', 'writer', 'visual', 'kanban', 'interview', 'skills'];
  const activeModule = modules.includes(moduleId) ? moduleId : 'ats';

  const tabMap = {
    ats: 'studioTabAts',
    writer: 'studioTabWriter',
    visual: 'studioTabVisual',
    kanban: 'studioTabKanban',
    interview: 'studioTabInterview',
    skills: 'studioTabSkills'
  };

  const panelMap = {
    ats: 'studioModuleAts',
    writer: 'studioModuleWriter',
    visual: 'studioModuleVisual',
    kanban: 'studioModuleKanban',
    interview: 'studioModuleInterview',
    skills: 'studioModuleSkills'
  };

  modules.forEach(m => {
    const tab = document.getElementById(tabMap[m]);
    const panel = document.getElementById(panelMap[m]);
    if (m === activeModule) {
      if (tab) {
        tab.classList.add('active');
        tab.setAttribute('aria-selected', 'true');
      }
      if (panel) {
        panel.style.display = 'block';
        panel.classList.remove('hidden');
        panel.classList.add('active');
      }
    } else {
      if (tab) {
        tab.classList.remove('active');
        tab.setAttribute('aria-selected', 'false');
      }
      if (panel) {
        panel.style.display = 'none';
        panel.classList.add('hidden');
        panel.classList.remove('active');
      }
    }
  });
}

// Global Filter Setter
export function setFilter(filter, el) {
  store.setFilter(filter);
  if (typeof document === 'undefined') return;

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

  filterCards();
  updateCubeCountsImmediately();
}

// Debounce helper
export function debounce(func, wait = 200) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Toast notification helper
export function showToast(iconClass, message, duration = 3000) {
  if (typeof document === 'undefined') return;
  const toast = document.getElementById('toast');
  const toastIcon = document.getElementById('toastIcon');
  const toastMsg = document.getElementById('toastMsg');
  if (!toast) return;

  if (toastIcon) toastIcon.innerHTML = `<i class="ph-duotone ${iconClass}"></i>`;
  if (toastMsg) toastMsg.textContent = message;

  toast.classList.add('show');
  clearTimeout(toast.__timer);
  toast.__timer = setTimeout(() => {
    toast.classList.remove('show');
  }, duration);
}

// Attach to window
if (typeof window !== 'undefined') {
  window.switchDashboardAppMode = switchDashboardAppMode;
  window.switchStudioModule = switchStudioModule;
  window.setFilter = setFilter;
  window.showToast = showToast;
  window.debounce = debounce;
}

// Bootstrap Initialization
export async function initApp() {
  if (typeof document === 'undefined') return;

  // Bind debounced search
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    const debouncedSearch = debounce((e) => {
      store.setSearchQuery(e.target.value);
      filterCards();
    }, 200);
    searchInput.addEventListener('input', debouncedSearch);
  }

  // Bind sector and region filters
  const sectorFilter = document.getElementById('sectorFilter');
  if (sectorFilter) {
    sectorFilter.addEventListener('change', (e) => {
      store.setSectorFilter(e.target.value);
      filterCards();
    });
  }

  const regionFilter = document.getElementById('regionFilter');
  if (regionFilter) {
    regionFilter.addEventListener('change', (e) => {
      store.setRegionFilter(e.target.value);
      filterCards();
    });
  }

  // Bind view mode toggles (cards vs map)
  const btnViewCards = document.getElementById('viewModeCards');
  const btnViewMap = document.getElementById('viewModeMap');
  const cardsContainer = document.getElementById('cardsContainer');
  const mapContainer = document.getElementById('liveJobsMapContainer');

  if (btnViewCards && btnViewMap) {
    btnViewCards.addEventListener('click', () => {
      btnViewCards.classList.add('active');
      btnViewMap.classList.remove('active');
      if (cardsContainer) cardsContainer.style.display = '';
      if (mapContainer) mapContainer.style.display = 'none';
    });

    btnViewMap.addEventListener('click', () => {
      btnViewMap.classList.add('active');
      btnViewCards.classList.remove('active');
      if (cardsContainer) cardsContainer.style.display = 'none';
      if (mapContainer) {
        mapContainer.style.display = 'block';
        geoMap.initLiveJobsMap();
      }
    });
  }

  // Subscribe render to store changes
  store.subscribe('stateChanged', () => {
    updateCubeCountsImmediately();
  });

  // Fetch initial data
  try {
    await store.fetchJobsData();
    renderCards();
    updateUI();
  } catch (err) {
    console.warn('Initial jobs fetch notice:', err);
    renderCards();
    updateUI();
  }

  // Check URL hash for initial mode
  if (typeof window !== 'undefined') {
    if (window.location.hash === '#studio') {
      switchDashboardAppMode('studio', false);
    } else {
      switchDashboardAppMode('radar', false);
    }
  }
}

// Export initApp for explicit invocation by module consumers
export { initApp };
