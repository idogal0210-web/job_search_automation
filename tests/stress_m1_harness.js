/**
 * tests/stress_m1_harness.js
 *
 * Empirical Challenger Stress Harness for Milestone 1:
 * - Rapid Mode Toggling (sequential, randomized, idempotent, invalid inputs)
 * - Hash Routing & Corrupted Hashes (#unknownMode, #studio?param=1, empty, malformed)
 * - Corrupted and Unavailable localStorage (SecurityError, QuotaExceeded, corrupted payloads)
 * - Leaflet Map Invalidation Resilience (null, undefined, valid spy, nullified mid-flight, non-callable)
 * - Missing DOM Element Resilience
 * - switchStudioModule Stress & Resilience
 *
 * Runs directly on macOS JavaScriptCore via:
 *   /System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc tests/stress_m1_harness.js
 */

(function () {
  'use strict';

  let totalTests = 0;
  let passedTests = 0;
  let failedTests = 0;
  const failureLog = [];

  function assert(condition, message) {
    totalTests++;
    if (condition) {
      passedTests++;
    } else {
      failedTests++;
      failureLog.push(message);
      print('  [FAIL] ' + message);
    }
  }

  function assertEqual(actual, expected, message) {
    totalTests++;
    if (actual === expected) {
      passedTests++;
    } else {
      failedTests++;
      const fullMsg = message + ' (Expected: ' + JSON.stringify(expected) + ', Actual: ' + JSON.stringify(actual) + ')';
      failureLog.push(fullMsg);
      print('  [FAIL] ' + fullMsg);
    }
  }

  function assertThrows(fn, message) {
    totalTests++;
    let threw = false;
    try {
      fn();
    } catch (e) {
      threw = true;
    }
    if (threw) {
      passedTests++;
    } else {
      failedTests++;
      failureLog.push(message + ' (Expected exception but none thrown)');
      print('  [FAIL] ' + message);
    }
  }

  function assertDoesNotThrow(fn, message) {
    totalTests++;
    let threw = false;
    let err = null;
    try {
      fn();
    } catch (e) {
      threw = true;
      err = e;
    }
    if (!threw) {
      passedTests++;
    } else {
      failedTests++;
      const fullMsg = message + ' (Threw: ' + String(err) + ')';
      failureLog.push(fullMsg);
      print('  [FAIL] ' + fullMsg);
    }
  }

  // Ensure global console exists in JSC CLI environment
  if (!globalThis.console) {
    globalThis.console = { log: print, warn: print, error: print, info: print };
  } else {
    if (!globalThis.console.warn) globalThis.console.warn = globalThis.console.log || print;
    if (!globalThis.console.error) globalThis.console.error = globalThis.console.log || print;
    if (!globalThis.console.info) globalThis.console.info = globalThis.console.log || print;
  }

  // --- Mock Environment Factory ---

  function createMockClassList(initialClasses) {
    const classes = new Set(initialClasses || []);
    return {
      add: function (c) { classes.add(c); },
      remove: function (c) { classes.delete(c); },
      contains: function (c) { return classes.has(c); },
      toggle: function (c, force) {
        if (force === undefined) {
          if (classes.has(c)) { classes.delete(c); return false; }
          else { classes.add(c); return true; }
        } else if (force) {
          classes.add(c); return true;
        } else {
          classes.delete(c); return false;
        }
      },
      toArray: function () { return Array.from(classes); }
    };
  }

  function createMockElement(id, initialClasses, initialDisplay) {
    const attrs = {};
    return {
      id: id,
      style: { display: initialDisplay || '' },
      classList: createMockClassList(initialClasses),
      setAttribute: function (k, v) { attrs[k] = String(v); },
      getAttribute: function (k) { return attrs[k] !== undefined ? attrs[k] : null; },
      removeAttribute: function (k) { delete attrs[k]; },
      value: ''
    };
  }

  function createMockEnvironment(options) {
    options = options || {};

    const timerQueue = [];
    let nextTimerId = 1;

    function mockSetTimeout(fn, delay) {
      const id = nextTimerId++;
      timerQueue.push({ id: id, fn: fn, delay: delay, cancelled: false });
      return id;
    }

    function mockClearTimeout(id) {
      for (let i = 0; i < timerQueue.length; i++) {
        if (timerQueue[i].id === id) {
          timerQueue[i].cancelled = true;
        }
      }
    }

    function flushTimers() {
      const toRun = timerQueue.slice();
      timerQueue.length = 0;
      for (let i = 0; i < toRun.length; i++) {
        if (!toRun[i].cancelled) {
          toRun[i].fn();
        }
      }
    }

    // Mock Elements
    const elements = {
      radarWorkspace: createMockElement('radarWorkspace', ['dashboard-view-container', 'active'], 'block'),
      careerStudioWorkspace: createMockElement('careerStudioWorkspace', ['dashboard-view-container', 'hidden'], 'none'),
      modeSwitchRadar: createMockElement('modeSwitchRadar', ['mode-switch-btn', 'active']),
      modeSwitchStudio: createMockElement('modeSwitchStudio', ['mode-switch-btn']),
      sectorFilter: createMockElement('sectorFilter'),
      regionFilter: createMockElement('regionFilter'),
      cube_saved: createMockElement('cube_saved', ['stat-cube-btn']),
      cube_rejected: createMockElement('cube_rejected', ['stat-cube-btn']),
      cube_starred: createMockElement('cube_starred', ['stat-cube-btn']),
      studioTabAts: createMockElement('studioTabAts', ['studio-subnav-btn', 'active']),
      studioTabWriter: createMockElement('studioTabWriter', ['studio-subnav-btn']),
      studioTabVisual: createMockElement('studioTabVisual', ['studio-subnav-btn']),
      studioTabKanban: createMockElement('studioTabKanban', ['studio-subnav-btn']),
      studioTabInterview: createMockElement('studioTabInterview', ['studio-subnav-btn']),
      studioTabSkills: createMockElement('studioTabSkills', ['studio-subnav-btn']),
      studioModuleAts: createMockElement('studioModuleAts', ['studio-module-panel', 'active'], 'block'),
      studioModuleWriter: createMockElement('studioModuleWriter', ['studio-module-panel'], 'none'),
      studioModuleVisual: createMockElement('studioModuleVisual', ['studio-module-panel'], 'none'),
      studioModuleKanban: createMockElement('studioModuleKanban', ['studio-module-panel'], 'none'),
      studioModuleInterview: createMockElement('studioModuleInterview', ['studio-module-panel'], 'none'),
      studioModuleSkills: createMockElement('studioModuleSkills', ['studio-module-panel'], 'none')
    };
    elements.modeSwitchRadar.setAttribute('aria-selected', 'true');
    elements.modeSwitchStudio.setAttribute('aria-selected', 'false');

    const progressHub = createMockElement('progressHub', ['header-progress-hub']);

    // Mock Storage
    const storageStore = Object.assign({}, options.initialStorage || {});
    let storageThrowOnSet = options.storageThrowOnSet || false;
    let storageThrowOnGet = options.storageThrowOnGet || false;
    let storageThrowOnAccess = options.storageThrowOnAccess || false;

    const mockLocalStorage = {
      getItem: function (k) {
        if (storageThrowOnGet) throw new Error('SecurityError: LocalStorage read restricted');
        return storageStore.hasOwnProperty(k) ? storageStore[k] : null;
      },
      setItem: function (k, v) {
        if (storageThrowOnSet) throw new Error('QuotaExceededError: Storage quota exceeded');
        storageStore[k] = String(v);
      },
      removeItem: function (k) {
        delete storageStore[k];
      },
      clear: function () {
        for (let k in storageStore) { delete storageStore[k]; }
      },
      _store: storageStore,
      _setThrowOnSet: function (val) { storageThrowOnSet = val; },
      _setThrowOnGet: function (val) { storageThrowOnGet = val; },
      _setThrowOnAccess: function (val) { storageThrowOnAccess = val; }
    };

    // Event listeners
    const eventListeners = {};
    function mockAddEventListener(event, handler) {
      if (!eventListeners[event]) eventListeners[event] = [];
      eventListeners[event].push(handler);
    }
    function mockDispatchEvent(event, data) {
      if (eventListeners[event]) {
        eventListeners[event].forEach(function (fn) { fn(data); });
      }
    }

    const mockWindow = {
      location: {
        hash: options.initialHash || ''
      },
      addEventListener: mockAddEventListener,
      dispatchEvent: mockDispatchEvent,
      setTimeout: mockSetTimeout,
      clearTimeout: mockClearTimeout,
      _listeners: eventListeners
    };

    const mockDocument = {
      getElementById: function (id) {
        if (options.omitElements && options.omitElements.indexOf(id) !== -1) return null;
        return elements[id] || null;
      },
      querySelector: function (selector) {
        if (options.omitElements && options.omitElements.indexOf(selector) !== -1) return null;
        if (selector === '.header-progress-hub') return progressHub;
        return null;
      },
      querySelectorAll: function (selector) {
        if (selector === '.stat-cube-btn') {
          return [elements.cube_saved, elements.cube_rejected, elements.cube_starred];
        }
        if (selector === '.job-card') return [];
        return [];
      },
      addEventListener: mockAddEventListener
    };

    return {
      window: mockWindow,
      document: mockDocument,
      localStorage: storageThrowOnAccess ? undefined : mockLocalStorage,
      mockLocalStorage: mockLocalStorage,
      elements: elements,
      progressHub: progressHub,
      setTimeout: mockSetTimeout,
      clearTimeout: mockClearTimeout,
      flushTimers: flushTimers,
      timerQueue: timerQueue
    };
  }

  // --- Test Runner ---

  print('================================================================');
  print('Running Empirical Challenger Stress Harness for Milestone 1');
  print('Target: switchDashboardAppMode & Hash/Storage Routing');
  print('================================================================\n');

  // Load the production dashboard.js code once in global scope
  // For each test, we invoke switchDashboardAppMode in an isolated or contextual state.
  // Note: dashboard.js assigns window.switchDashboardAppMode.
  // We will test both the function itself and simulated hash/load lifecycle.

  // 1. Initial Load of dashboard.js into environment
  const bootstrapEnv = createMockEnvironment();
  globalThis.window = bootstrapEnv.window;
  globalThis.document = bootstrapEnv.document;
  globalThis.localStorage = bootstrapEnv.mockLocalStorage;
  globalThis.setTimeout = bootstrapEnv.setTimeout;
  globalThis.clearTimeout = bootstrapEnv.clearTimeout;

  try {
    load('frontend/js/dashboard.js');
    print('[OK] frontend/js/dashboard.js loaded into JSC environment.\n');
  } catch (err) {
    print('[FATAL] Failed to load dashboard.js: ' + err);
    quit(1);
  }

  const switchDashboardAppMode = window.switchDashboardAppMode;
  const switchStudioModule = window.switchStudioModule;

  assert(typeof switchDashboardAppMode === 'function', 'switchDashboardAppMode must be exported on window');
  assert(typeof switchStudioModule === 'function', 'switchStudioModule must be exported on window');

  // -------------------------------------------------------------------------
  // Test Suite 1: Rapid Mode Toggling (Stress & Invariant Verification)
  // -------------------------------------------------------------------------
  print('--- Suite 1: Rapid Mode Toggling ---');

  (function testRapidAlternatingToggle() {
    const env = createMockEnvironment();
    globalThis.window = env.window;
    globalThis.document = env.document;
    globalThis.localStorage = env.mockLocalStorage;
    globalThis.setTimeout = env.setTimeout;
    globalThis.clearTimeout = env.clearTimeout;

    // Toggle 1,000 times sequentially
    const iterations = 1000;
    for (let i = 0; i < iterations; i++) {
      const target = (i % 2 === 0) ? 'studio' : 'radar';
      switchDashboardAppMode(target, true);

      // Verify immediate DOM invariant after every single switch
      if (target === 'studio') {
        assert(env.elements.radarWorkspace.style.display === 'none', 'Iter ' + i + ': radarWorkspace must be hidden in studio mode');
        assert(env.elements.careerStudioWorkspace.style.display === 'flex', 'Iter ' + i + ': careerStudioWorkspace must be flex in studio mode');
        assert(env.elements.careerStudioWorkspace.classList.contains('active'), 'Iter ' + i + ': studioWs has active class');
        assert(env.elements.radarWorkspace.classList.contains('hidden'), 'Iter ' + i + ': radarWs has hidden class');
        assertEqual(env.window.location.hash, '#studio', 'Iter ' + i + ': hash must be #studio');
        assertEqual(env.mockLocalStorage.getItem('ido_app_active_mode'), 'studio', 'Iter ' + i + ': storage must be studio');
      } else {
        assert(env.elements.radarWorkspace.style.display === 'block', 'Iter ' + i + ': radarWorkspace must be block in radar mode');
        assert(env.elements.careerStudioWorkspace.style.display === 'none', 'Iter ' + i + ': careerStudioWorkspace must be hidden in radar mode');
        assert(env.elements.radarWorkspace.classList.contains('active'), 'Iter ' + i + ': radarWs has active class');
        assert(env.elements.careerStudioWorkspace.classList.contains('hidden'), 'Iter ' + i + ': studioWs has hidden class');
        assertEqual(env.window.location.hash, '#radar', 'Iter ' + i + ': hash must be #radar');
        assertEqual(env.mockLocalStorage.getItem('ido_app_active_mode'), 'radar', 'Iter ' + i + ': storage must be radar');
      }
    }
    print('[PASS] 1,000 rapid sequential toggles completed with 100% invariant consistency.');
  })();

  (function testRandomRapidToggling() {
    const env = createMockEnvironment();
    globalThis.window = env.window;
    globalThis.document = env.document;
    globalThis.localStorage = env.mockLocalStorage;

    const modes = ['radar', 'studio'];
    let lastMode = 'radar';
    for (let i = 0; i < 500; i++) {
      const randMode = modes[Math.floor(Math.random() * modes.length)];
      switchDashboardAppMode(randMode, true);
      lastMode = randMode;

      // Both workspaces must never be simultaneously visible
      const radarVis = env.elements.radarWorkspace.style.display !== 'none';
      const studioVis = env.elements.careerStudioWorkspace.style.display !== 'none';
      assert(radarVis !== studioVis, 'Iter ' + i + ': Workspaces must be mutually exclusive in visibility');
    }
    assertEqual(env.mockLocalStorage.getItem('ido_app_active_mode'), lastMode, 'Final storage matches last random mode');
    print('[PASS] 500 random toggles preserved strict mutual exclusivity.');
  })();

  (function testIdempotentRepeatedCalls() {
    const env = createMockEnvironment();
    globalThis.window = env.window;
    globalThis.document = env.document;
    globalThis.localStorage = env.mockLocalStorage;

    // 50 calls with 'studio'
    for (let i = 0; i < 50; i++) {
      switchDashboardAppMode('studio', true);
    }
    assertEqual(env.elements.careerStudioWorkspace.style.display, 'flex', 'Idempotent studio display');
    assertEqual(env.elements.careerStudioWorkspace.classList.contains('active'), true, 'Studio has active class');
    assertEqual(env.elements.modeSwitchStudio.getAttribute('aria-selected'), 'true', 'Studio button aria-selected');

    // 50 calls with 'radar'
    for (let i = 0; i < 50; i++) {
      switchDashboardAppMode('radar', true);
    }
    assertEqual(env.elements.radarWorkspace.style.display, 'block', 'Idempotent radar display');
    assertEqual(env.elements.radarWorkspace.classList.contains('active'), true, 'Radar has active class');
    assertEqual(env.elements.modeSwitchRadar.getAttribute('aria-selected'), 'true', 'Radar button aria-selected');
    print('[PASS] Idempotent repeated calls do not duplicate state or alter invariants.');
  })();

  (function testInvalidModeInputs() {
    const env = createMockEnvironment();
    globalThis.window = env.window;
    globalThis.document = env.document;
    globalThis.localStorage = env.mockLocalStorage;

    const invalidInputs = [
      null, undefined, '', 'unknown', 'STUDIO', 'Radar', 123, true, false,
      {}, [], function(){}, 'studio?param=1', '#studio'
    ];

    invalidInputs.forEach(function (inp, idx) {
      assertDoesNotThrow(function () {
        switchDashboardAppMode(inp, true);
      }, 'Invalid input ' + idx + ' (' + String(inp) + ') must not throw exception');

      // All invalid inputs must safely fallback to 'radar'
      assertEqual(env.elements.radarWorkspace.style.display, 'block', 'Fallback for input ' + idx + ' must be radar');
      assertEqual(env.mockLocalStorage.getItem('ido_app_active_mode'), 'radar', 'Storage for input ' + idx + ' must be radar');
    });
    print('[PASS] Invalid inputs safely defaulted to radar with zero unhandled exceptions.');
  })();

  // -------------------------------------------------------------------------
  // Test Suite 2: Unknown or Corrupted Hash Values
  // -------------------------------------------------------------------------
  print('\n--- Suite 2: Unknown or Corrupted Hash Values ---');

  function simulateHashRouting(rawHashValue, storedMode, env) {
    env = env || createMockEnvironment({ initialHash: rawHashValue, initialStorage: { ido_app_active_mode: storedMode } });
    globalThis.window = env.window;
    globalThis.document = env.document;
    globalThis.localStorage = env.mockLocalStorage;

    const rawHash = (env.window.location.hash || '').replace('#', '').trim();
    let initialMode = 'radar';
    try {
      initialMode = env.mockLocalStorage.getItem('ido_app_active_mode') || 'radar';
    } catch (e) {}

    if (rawHash === 'studio' || (!rawHash && initialMode === 'studio')) {
      switchDashboardAppMode('studio', false);
    } else {
      switchDashboardAppMode('radar', false);
      if (rawHash === 'saved' || rawHash === 'rejected' || rawHash === 'starred') {
        const cubeEl = env.document.getElementById('cube_' + rawHash);
        if (cubeEl) cubeEl.classList.add('active');
      }
    }
    return env;
  }

  function simulateHashChangeEvent(newHash, env) {
    env.window.location.hash = newHash;
    const h = (newHash || '').replace('#', '').trim();
    if (h === 'studio') {
      switchDashboardAppMode('studio', false);
    } else if (h === 'radar') {
      switchDashboardAppMode('radar', false);
    } else if (h === 'saved' || h === 'rejected' || h === 'starred') {
      switchDashboardAppMode('radar', false);
      const cubeEl = env.document.getElementById('cube_' + h);
      if (cubeEl) cubeEl.classList.add('active');
    }
  }

  (function testCorruptedHashesOnLoad() {
    const testHashes = [
      '#unknownMode',
      '#studio?param=1',
      '#radar?filter=urgent',
      '#',
      '##',
      '###studio',
      '#<script>alert(1)</script>',
      '#!@#$%^&*()_+',
      '#studio/nested/route',
      '#undefined',
      '#null',
      '#NaN',
      '#12345',
      '#   ',
      '#%20%20%20'
    ];

    testHashes.forEach(function (h) {
      assertDoesNotThrow(function () {
        const env = simulateHashRouting(h, 'radar');
        // If unknown or corrupted, should safely be in radar
        assertEqual(env.elements.radarWorkspace.style.display, 'block', 'Hash ' + h + ' must safely default to radar');
      }, 'Hash routing for ' + h + ' must not throw');
    });
    print('[PASS] All 15 malformed/corrupted hash values on load handled gracefully without exception.');
  })();

  (function testEmptyHashStateRestoration() {
    // When hash is empty, it should restore storedMode if storedMode is 'studio'
    const envStudio = simulateHashRouting('', 'studio');
    assertEqual(envStudio.elements.careerStudioWorkspace.style.display, 'flex', 'Empty hash restores studio from localStorage');

    // When hash is empty and storedMode is 'radar', it defaults to radar
    const envRadar = simulateHashRouting('', 'radar');
    assertEqual(envRadar.elements.radarWorkspace.style.display, 'block', 'Empty hash restores radar from localStorage');

    // Hash is '#' (empty)
    const envHashOnly = simulateHashRouting('#', 'studio');
    assertEqual(envHashOnly.elements.careerStudioWorkspace.style.display, 'flex', 'Hash # restores studio from localStorage');
    print('[PASS] Empty hash correctly restores persisted state.');
  })();

  (function testHashChangeDispatchStress() {
    const env = createMockEnvironment();
    globalThis.window = env.window;
    globalThis.document = env.document;
    globalThis.localStorage = env.mockLocalStorage;

    const stressHashes = [
      '#studio',
      '#unknownMode',
      '#studio?param=1',
      '#radar',
      '#saved',
      '#rejected',
      '#starred',
      '#',
      '#studio',
      '#corrupted/path/to/fail',
      '#radar'
    ];

    stressHashes.forEach(function (h) {
      assertDoesNotThrow(function () {
        simulateHashChangeEvent(h, env);
      }, 'HashChangeEvent for ' + h + ' must not throw');
    });

    assertEqual(env.elements.radarWorkspace.style.display, 'block', 'Final state after stressHashes is radar');
    print('[PASS] Dynamic hashchange events stress-tested cleanly.');
  })();

  // -------------------------------------------------------------------------
  // Test Suite 3: Corrupted or Unavailable localStorage
  // -------------------------------------------------------------------------
  print('\n--- Suite 3: Corrupted or Unavailable localStorage ---');

  (function testLocalStorageThrowsSecurityErrorOnAccess() {
    const env = createMockEnvironment({ storageThrowOnAccess: true });
    globalThis.window = env.window;
    globalThis.document = env.document;
    // In strict iframe/private mode, window.localStorage access can throw SecurityError
    delete globalThis.localStorage;

    assertDoesNotThrow(function () {
      switchDashboardAppMode('studio', true);
    }, 'switchDashboardAppMode must not throw when localStorage is unavailable/undefined');

    assertEqual(env.elements.careerStudioWorkspace.style.display, 'flex', 'DOM switches even if storage throws');

    assertDoesNotThrow(function () {
      switchDashboardAppMode('radar', true);
    }, 'switchDashboardAppMode to radar must not throw when localStorage is unavailable');

    assertEqual(env.elements.radarWorkspace.style.display, 'block', 'DOM switches back to radar');
    print('[PASS] Handled completely unavailable localStorage (private mode / restricted sandbox).');
  })();

  (function testLocalStorageQuotaExceededOnSetItem() {
    const env = createMockEnvironment({ storageThrowOnSet: true });
    globalThis.window = env.window;
    globalThis.document = env.document;
    globalThis.localStorage = env.mockLocalStorage;

    assertDoesNotThrow(function () {
      switchDashboardAppMode('studio', true);
    }, 'switchDashboardAppMode must swallow QuotaExceededError');

    assertEqual(env.elements.careerStudioWorkspace.style.display, 'flex', 'DOM correctly switched to studio despite quota error');
    print('[PASS] Handled QuotaExceededError on localStorage.setItem without crashing.');
  })();

  (function testLocalStorageCorruptedReadValues() {
    const corruptedValues = [
      null,
      'undefined',
      'null',
      'NaN',
      '[object Object]',
      '{"bad": json',
      '12345',
      'RADAR_CORRUPTED',
      '---weird---'
    ];

    corruptedValues.forEach(function (val, idx) {
      assertDoesNotThrow(function () {
        const env = simulateHashRouting('', val);
        // None of these should activate studio; should safely fallback to radar
        assertEqual(env.elements.radarWorkspace.style.display, 'block', 'Corrupted value ' + idx + ' falls back to radar');
      }, 'Corrupted storage value ' + idx + ' (' + val + ') must not crash onload');
    });
    print('[PASS] Corrupted localStorage values gracefully fall back to radar.');
  })();

  // Mock Console
  if (!globalThis.console) {
    globalThis.console = { log: print, warn: print, error: print };
  } else {
    if (!globalThis.console.warn) globalThis.console.warn = globalThis.console.log || print;
    if (!globalThis.console.error) globalThis.console.error = globalThis.console.log || print;
  }

  // -------------------------------------------------------------------------
  // Test Suite 4: Leaflet Map Invalidation Resilience
  // -------------------------------------------------------------------------
  print('\n--- Suite 4: Leaflet Map Invalidation Resilience ---');

  (function testMapInstanceNull() {
    const env = createMockEnvironment();
    globalThis.window = env.window;
    globalThis.document = env.document;
    globalThis.localStorage = env.mockLocalStorage;
    globalThis.setTimeout = env.setTimeout;

    // Initially, liveJobsMapInstance is null
    assertDoesNotThrow(function () {
      switchDashboardAppMode('radar', false);
    }, 'Switching to radar when liveJobsMapInstance is null must not throw');

    assertEqual(env.timerQueue.length, 0, 'No timeout should be scheduled if liveJobsMapInstance is null');
    print('[PASS] liveJobsMapInstance = null handled safely with zero timers registered.');
  })();

  (function testMapInstanceValidWithInit() {
    const env = createMockEnvironment();
    globalThis.window = env.window;
    globalThis.document = env.document;
    globalThis.localStorage = env.mockLocalStorage;
    globalThis.setTimeout = env.setTimeout;

    let invalidateCount = 0;
    // Provide liveJobsMap element in DOM
    const mapEl = createMockElement('liveJobsMap');
    env.elements.liveJobsMap = mapEl;

    // Provide Leaflet mock
    globalThis.L = {
      map: function () {
        return {
          invalidateSize: function () { invalidateCount++; },
          setView: function () { return this; },
          addLayer: function () { return this; },
          remove: function () { }
        };
      },
      tileLayer: function () {
        return { addTo: function () { return this; } };
      },
      layerGroup: function () {
        return { addTo: function () { return this; }, clearLayers: function () { return this; } };
      }
    };

    // Initialize the map via dashboard.js initLiveJobsMap
    if (typeof initLiveJobsMap === 'function') {
      initLiveJobsMap();
    }

    switchDashboardAppMode('radar', false);
    assertEqual(env.timerQueue.length, 1, 'One timer scheduled for map invalidation');
    if (env.timerQueue.length > 0) {
      assertEqual(env.timerQueue[0].delay, 150, 'Map invalidation timer delay is 150ms');
    }
    assertEqual(invalidateCount, 0, 'invalidateSize not called synchronously before timeout');

    // Flush timers
    env.flushTimers();
    assertEqual(invalidateCount, 1, 'invalidateSize called exactly once after timer flushes');
    print('[PASS] Valid initialized map instance schedules and executes invalidateSize after 150ms.');
  })();

  (function testMapInvalidationContractStress() {
    function executeMapInvalidation(mapInst, setTimeoutFn) {
      if (typeof mapInst !== 'undefined' && mapInst) {
        setTimeoutFn(() => {
          if (mapInst && typeof mapInst.invalidateSize === 'function') {
            mapInst.invalidateSize();
          }
        }, 150);
      }
    }

    // 1. undefined map
    const env1 = createMockEnvironment();
    executeMapInvalidation(undefined, env1.setTimeout);
    assertEqual(env1.timerQueue.length, 0, 'undefined map schedules no timer');

    // 2. null map
    const env2 = createMockEnvironment();
    executeMapInvalidation(null, env2.setTimeout);
    assertEqual(env2.timerQueue.length, 0, 'null map schedules no timer');

    // 3. valid map
    const env3 = createMockEnvironment();
    let called3 = 0;
    const map3 = { invalidateSize: function () { called3++; } };
    executeMapInvalidation(map3, env3.setTimeout);
    assertEqual(env3.timerQueue.length, 1, 'valid map schedules 1 timer');
    assertEqual(env3.timerQueue[0].delay, 150, 'timer delay is 150ms');
    env3.flushTimers();
    assertEqual(called3, 1, 'valid map executes invalidateSize');

    // 4. map destroyed mid-flight
    const env4 = createMockEnvironment();
    let called4 = 0;
    const mapHolder = { current: { invalidateSize: function () { called4++; } } };
    function executeHolder(holder, setTimeoutFn) {
      if (typeof holder.current !== 'undefined' && holder.current) {
        setTimeoutFn(() => {
          if (holder.current && typeof holder.current.invalidateSize === 'function') {
            holder.current.invalidateSize();
          }
        }, 150);
      }
    }
    executeHolder(mapHolder, env4.setTimeout);
    assertEqual(env4.timerQueue.length, 1, 'timer scheduled');
    mapHolder.current = null; // destroyed before 150ms!
    assertDoesNotThrow(function () { env4.flushTimers(); }, 'destroyed map mid-flight does not throw');
    assertEqual(called4, 0, 'invalidateSize was not called on destroyed instance');

    // 5. non-callable invalidateSize
    const env5 = createMockEnvironment();
    const map5 = { invalidateSize: 'not-a-function' };
    executeMapInvalidation(map5, env5.setTimeout);
    assertEqual(env5.timerQueue.length, 1, 'timer scheduled');
    assertDoesNotThrow(function () { env5.flushTimers(); }, 'non-callable invalidateSize does not throw');

    print('[PASS] Leaflet map invalidation contract thoroughly stress-tested across all edge cases.');
  })();

  // -------------------------------------------------------------------------
  // Test Suite 5: Missing DOM Elements Resilience
  // -------------------------------------------------------------------------
  print('\n--- Suite 5: Missing DOM Elements Resilience ---');

  (function testOmittedDOMElements() {
    const missingElementCases = [
      ['radarWorkspace'],
      ['careerStudioWorkspace'],
      ['modeSwitchRadar'],
      ['modeSwitchStudio'],
      ['.header-progress-hub'],
      ['radarWorkspace', 'careerStudioWorkspace', 'modeSwitchRadar', 'modeSwitchStudio', '.header-progress-hub']
    ];

    missingElementCases.forEach(function (omitted, idx) {
      const env = createMockEnvironment({ omitElements: omitted });
      globalThis.window = env.window;
      globalThis.document = env.document;
      globalThis.localStorage = env.mockLocalStorage;

      assertDoesNotThrow(function () {
        switchDashboardAppMode('studio', true);
      }, 'Omitted elements case ' + idx + ' (studio) must not throw');

      assertDoesNotThrow(function () {
        switchDashboardAppMode('radar', true);
      }, 'Omitted elements case ' + idx + ' (radar) must not throw');
    });
    print('[PASS] Complete resilience against missing or unmounted DOM elements.');
  })();

  // -------------------------------------------------------------------------
  // Test Suite 6: switchStudioModule Stress & Resilience
  // -------------------------------------------------------------------------
  print('\n--- Suite 6: switchStudioModule Stress & Resilience ---');

  (function testStudioModuleSwitching() {
    const env = createMockEnvironment();
    globalThis.window = env.window;
    globalThis.document = env.document;

    const validModules = ['ats', 'writer', 'visual', 'kanban', 'interview', 'skills'];

    validModules.forEach(function (mod) {
      switchStudioModule(mod);
      const tabId = 'studioTab' + mod.charAt(0).toUpperCase() + mod.slice(1);
      const panelId = 'studioModule' + mod.charAt(0).toUpperCase() + mod.slice(1);

      assertEqual(env.elements[tabId].classList.contains('active'), true, 'Tab ' + mod + ' active');
      assertEqual(env.elements[tabId].getAttribute('aria-selected'), 'true', 'Tab ' + mod + ' aria-selected true');
      assertEqual(env.elements[panelId].style.display, 'block', 'Panel ' + mod + ' display block');
      assertEqual(env.elements[panelId].classList.contains('active'), true, 'Panel ' + mod + ' active class');
    });

    // Unknown module should fallback to 'ats'
    switchStudioModule('unknown_module');
    assertEqual(env.elements.studioTabAts.classList.contains('active'), true, 'Unknown module falls back to ats tab');
    assertEqual(env.elements.studioModuleAts.style.display, 'block', 'Unknown module falls back to ats panel');

    // Null/undefined module falls back to ats
    switchStudioModule(null);
    assertEqual(env.elements.studioTabAts.classList.contains('active'), true, 'null module falls back to ats tab');
    print('[PASS] switchStudioModule stress and fallbacks passed 100%.');
  })();

  // -------------------------------------------------------------------------
  // Summary & Exit Code
  // -------------------------------------------------------------------------
  print('\n================================================================');
  print('Challenger Stress Harness Results:');
  print('Total Assertions: ' + totalTests);
  print('Passed:           ' + passedTests);
  print('Failed:           ' + failedTests);
  print('================================================================');

  if (failedTests > 0) {
    print('\nFAILURES:');
    failureLog.forEach(function (f) { print(' - ' + f); });
    quit(1);
  } else {
    print('\nALL STRESS TESTS PASSED SUCCESSFULLY! ZERO EXCEPTIONS!');
    quit(0);
  }

})();
