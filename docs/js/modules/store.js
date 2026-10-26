/**
 * store.js - Central Reactive State Manager (Pub/Sub pattern)
 * Manages job bookmarks, triage status (saved/rejected), historical catalog,
 * review progress calculations, LocalStorage persistence, and cloud sync.
 */

// Storage Keys
export const STORAGE_KEYS = {
  TRIAGE: 'ido_job_triage_states_v2',
  STARRED: 'ido_starred_jobs_v2',
  SORT: 'ido_dashboard_sort',
  ACTIVE_MODE: 'ido_app_active_mode',
  LEGACY_TRIAGE: 'jobTriageStates',
  LEGACY_STARRED: 'jobStars'
};

// Default Curated Starred Jobs (Fallback Seed)
export const DEFAULT_STARRED_LINKS = [
  "https://il.linkedin.com/jobs/view/%D7%AA%D7%94%D7%9C%D7%99%D7%9B%D7%99-%D7%91%D7%A7%D7%A8%D7%94-%D7%95-ai-at-iai-israel-aerospace-industries-4478429532",
  "https://il.linkedin.com/jobs/view/high-pressure-natural-gas-project-israel-at-rina-4469463836",
  "https://www.comeet.com/jobs/enlightenergy/99.006/project-manager---construction---enlight-local/92.F66",
  "https://il.linkedin.com/jobs/view/junior-business-development-manager-at-ormash-group-%D7%A7%D7%91%D7%95%D7%A6%D7%AA-%D7%90%D7%95%D7%A8%D7%9E%D7%A9-4468984224",
  "https://il.linkedin.com/jobs/view/junior-solar-account-coordinator-at-amarel-ltd-4481350574",
  "https://il.linkedin.com/jobs/view/practical-engineer-at-solaredge-technologies-4481748648",
  "https://il.linkedin.com/jobs/view/system-engineer-renewable-energy-energy-storage-projects-at-nextcom-group-4478214360"
];

// Pub/Sub Event System
class EventEmitter {
  constructor() {
    this._listeners = new Map();
  }

  subscribe(event, callback) {
    if (!this._listeners.has(event)) {
      this._listeners.set(event, new Set());
    }
    this._listeners.get(event).add(callback);
    return () => this._listeners.get(event).delete(callback);
  }

  publish(event, data) {
    if (!this._listeners.has(event)) return;
    this._listeners.get(event).forEach(cb => {
      try {
        cb(data);
      } catch (err) {
        console.error(`Error in event listener for ${event}:`, err);
      }
    });
  }
}

class Store extends EventEmitter {
  constructor() {
    super();
    this.rawJobsData = (typeof window !== 'undefined' && window.__INLINE_JOBS_FALLBACK__) ? window.__INLINE_JOBS_FALLBACK__ : [];
    this.historicalCatalog = (typeof window !== 'undefined' && window.__INLINE_CATALOG_FALLBACK__) ? window.__INLINE_CATALOG_FALLBACK__ : {};
    this.allJobsMap = {};
    this.isCatalogLoaded = false;
    this.isJobsLoading = false;
    this.jobsLoadError = null;

    this.starredJobs = this.loadStarredJobs();
    this.jobStates = this.loadTriageState();

    this.currentFilter = 'all';
    this.currentSort = this._loadInitialSort();
    this.currentSectorFilter = 'all';
    this.currentRegionFilter = 'all';
    this.searchQuery = '';
    this.activeTagFilter = null;
    this.cloudSyncStatus = 'idle';
    this.lastSyncTimestamp = null;
    this._cloudPushDebounceTimer = null;
  }

  _loadInitialSort() {
    try {
      if (typeof localStorage !== 'undefined') {
        return localStorage.getItem(STORAGE_KEYS.SORT) || 'score_desc';
      }
    } catch (e) {}
    return 'score_desc';
  }

  loadStarredJobs() {
    try {
      if (typeof localStorage !== 'undefined') {
        const stored = localStorage.getItem(STORAGE_KEYS.STARRED);
        if (stored) {
          const parsed = JSON.parse(stored);
          if (parsed && typeof parsed === 'object') return parsed;
        }
        // Legacy fallback
        const legacy = localStorage.getItem(STORAGE_KEYS.LEGACY_STARRED);
        if (legacy) {
          const parsed = JSON.parse(legacy);
          if (Array.isArray(parsed)) {
            const mapped = {};
            parsed.forEach(id => { mapped[id] = true; });
            return mapped;
          }
        }
      }
    } catch (e) {
      console.warn('Failed to load starred jobs from storage:', e);
    }
    // Default fallback to 7 starred jobs
    const initial = {};
    DEFAULT_STARRED_LINKS.forEach(l => { initial[l] = true; });
    return initial;
  }

  saveStarredJobs(stars) {
    this.starredJobs = stars || this.starredJobs;
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEYS.STARRED, JSON.stringify(this.starredJobs));
      }
    } catch (e) {
      console.warn('Failed to save starred jobs to storage:', e);
    }
    this.publish('starredChanged', this.starredJobs);
    this.publish('stateChanged', this.getState());
  }

  toggleStar(id) {
    if (!id) return;
    if (this.starredJobs[id]) {
      delete this.starredJobs[id];
    } else {
      this.starredJobs[id] = true;
    }
    this.saveStarredJobs(this.starredJobs);
    this.scheduleCloudPush();
    return Boolean(this.starredJobs[id]);
  }

  isStarred(id) {
    return Boolean(this.starredJobs[id]);
  }

  loadTriageState() {
    try {
      if (typeof localStorage !== 'undefined') {
        const stored = localStorage.getItem(STORAGE_KEYS.TRIAGE);
        if (stored) {
          const parsed = JSON.parse(stored);
          if (parsed && typeof parsed === 'object') return parsed;
        }
        // Legacy fallback
        const legacy = localStorage.getItem(STORAGE_KEYS.LEGACY_TRIAGE);
        if (legacy) {
          const parsed = JSON.parse(legacy);
          if (parsed && typeof parsed === 'object') return parsed;
        }
      }
    } catch (e) {
      console.warn('Failed to load triage state:', e);
    }
    return {};
  }

  saveTriageState(states) {
    this.jobStates = states || this.jobStates;
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEYS.TRIAGE, JSON.stringify(this.jobStates));
      }
    } catch (e) {
      console.warn('Failed to save triage state:', e);
    }
    this.publish('triageChanged', this.jobStates);
    this.publish('stateChanged', this.getState());
  }

  setJobAction(id, action) {
    if (!id) return;
    const current = this.jobStates[id];
    if (current === action) {
      delete this.jobStates[id];
    } else {
      this.jobStates[id] = action;
    }
    this.saveTriageState(this.jobStates);
    this.scheduleCloudPush();
    return this.jobStates[id];
  }

  getJobState(id) {
    return this.jobStates[id];
  }

  setSort(sortVal) {
    this.currentSort = sortVal;
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEYS.SORT, sortVal);
      }
    } catch (e) {}
    this.publish('sortChanged', sortVal);
  }

  setFilter(filter) {
    this.currentFilter = filter;
    this.publish('filterChanged', filter);
    this.publish('stateChanged', this.getState());
  }

  setSearchQuery(q) {
    this.searchQuery = q || '';
    this.publish('searchChanged', this.searchQuery);
  }

  setSectorFilter(s) {
    this.currentSectorFilter = s || 'all';
    this.publish('filterChanged', this.currentFilter);
  }

  setRegionFilter(r) {
    this.currentRegionFilter = r || 'all';
    this.publish('filterChanged', this.currentFilter);
  }

  setTagFilter(tag) {
    this.activeTagFilter = (this.activeTagFilter === tag) ? null : tag;
    this.publish('filterChanged', this.currentFilter);
  }

  getAllAvailableJobs() {
    const list = [...this.rawJobsData];
    const seenLinks = new Set(this.rawJobsData.map(j => j.link));

    if (this.historicalCatalog && typeof this.historicalCatalog === 'object') {
      Object.entries(this.historicalCatalog).forEach(([link, job]) => {
        if (!seenLinks.has(link) && (this.jobStates[link] === 'saved' || this.jobStates[link] === 'rejected' || this.starredJobs[link])) {
          list.push(job);
          seenLinks.add(link);
        }
      });
    }

    // Refresh allJobsMap
    this.allJobsMap = {};
    list.forEach(j => {
      if (j && j.link) this.allJobsMap[j.link] = j;
    });

    return list;
  }

  getCounts() {
    const all = this.getAllAvailableJobs();
    let newCount = 0;
    let savedCount = 0;
    let rejectedCount = 0;
    let starredCount = 0;

    all.forEach(j => {
      const link = j.link;
      const state = this.jobStates[link];
      if (state === 'saved') savedCount++;
      else if (state === 'rejected') rejectedCount++;
      else newCount++;

      if (this.starredJobs[link]) starredCount++;
    });

    const total = all.length;
    const reviewed = savedCount + rejectedCount;
    const progressPct = total > 0 ? Math.round((reviewed / total) * 100) : 0;

    return {
      total,
      newCount,
      savedCount,
      rejectedCount,
      starredCount,
      reviewed,
      progressPct
    };
  }

  getState() {
    return {
      rawJobsData: this.rawJobsData,
      historicalCatalog: this.historicalCatalog,
      starredJobs: this.starredJobs,
      jobStates: this.jobStates,
      currentFilter: this.currentFilter,
      currentSort: this.currentSort,
      currentSectorFilter: this.currentSectorFilter,
      currentRegionFilter: this.currentRegionFilter,
      searchQuery: this.searchQuery,
      activeTagFilter: this.activeTagFilter,
      counts: this.getCounts(),
      cloudSyncStatus: this.cloudSyncStatus,
      lastSyncTimestamp: this.lastSyncTimestamp
    };
  }

  scheduleCloudPush() {
    if (this._cloudPushDebounceTimer) {
      clearTimeout(this._cloudPushDebounceTimer);
    }
    this._cloudPushDebounceTimer = setTimeout(() => {
      this.pushCloudSync();
    }, 1500);
  }

  async pushCloudSync() {
    if (typeof window === 'undefined') return;
    const syncAdapter = window.__PRIVATE_SYNC__;
    if (!syncAdapter || typeof syncAdapter.compareAndSwap !== 'function') return;

    this.cloudSyncStatus = 'syncing';
    this.publish('cloudSyncChanged', { status: 'syncing' });

    try {
      const payload = {
        jobStates: this.jobStates,
        starredJobs: this.starredJobs,
        updated_at: new Date().toISOString()
      };
      const res = await syncAdapter.compareAndSwap(payload, this.lastSyncTimestamp);
      if (res && res.ok) {
        this.cloudSyncStatus = 'synced';
        this.lastSyncTimestamp = payload.updated_at;
        this.publish('cloudSyncChanged', { status: 'synced', timestamp: this.lastSyncTimestamp });
      } else {
        this.cloudSyncStatus = 'conflict';
        this.publish('cloudSyncChanged', { status: 'conflict' });
      }
    } catch (e) {
      console.warn('Cloud push sync error:', e);
      this.cloudSyncStatus = 'error';
      this.publish('cloudSyncChanged', { status: 'error' });
    }
  }

  async fetchJobsData(jobsUrl) {
    this.isJobsLoading = true;
    this.jobsLoadError = null;
    this.publish('jobsLoading', true);

    const config = (typeof window !== 'undefined' && window.__APP_CONFIG__) || {};
    const url = jobsUrl || config.jobs_data_url || 'data/jobs.json';

    try {
      const resp = await fetch(url, { cache: 'no-cache' });
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status} (${resp.statusText})`);
      }
      const data = await resp.json();
      const nextJobs = Array.isArray(data) ? data : data.jobs;
      if (!Array.isArray(nextJobs)) throw new Error('מבנה נתוני המשרות אינו תקין');

      this.rawJobsData = nextJobs;
      this.isJobsLoading = false;
      this.publish('jobsLoaded', this.rawJobsData);
      this.publish('stateChanged', this.getState());
      return this.rawJobsData;
    } catch (err) {
      this.isJobsLoading = false;
      this.jobsLoadError = err.message;
      this.publish('jobsError', err.message);
      throw err;
    }
  }

  async fetchHistoricalCatalog(catalogUrl) {
    if (this.isCatalogLoaded) return this.historicalCatalog;
    const config = (typeof window !== 'undefined' && window.__APP_CONFIG__) || {};
    const url = catalogUrl || config.catalog_data_url || 'data/historical_catalog.json';

    try {
      const resp = await fetch(url, { cache: 'no-cache' });
      if (!resp.ok) return {};
      const data = await resp.json();
      this.historicalCatalog = (data && typeof data === 'object') ? data : {};
      this.isCatalogLoaded = true;
      this.publish('catalogLoaded', this.historicalCatalog);
      this.publish('stateChanged', this.getState());
      return this.historicalCatalog;
    } catch (e) {
      console.warn('Could not load historical catalog:', e);
      return {};
    }
  }
}

export const store = new Store();

// Backwards compatibility for window
if (typeof window !== 'undefined') {
  window.store = store;
  window.jobStates = store.jobStates;
  window.starredJobs = store.starredJobs;
  window.rawJobsData = store.rawJobsData;
  window.historicalCatalog = store.historicalCatalog;
  window.allJobsMap = store.allJobsMap;
  window.getAllAvailableJobs = () => store.getAllAvailableJobs();
  window.toggleStar = (id) => store.toggleStar(id);
  window.saveTriageState = (s) => store.saveTriageState(s);
  window.saveStarredJobs = (s) => store.saveStarredJobs(s);
}
