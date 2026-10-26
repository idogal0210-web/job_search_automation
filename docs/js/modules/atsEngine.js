/**
 * atsEngine.js - Decoupled ATS Scoring & Statutory Hard Gates Engine
 * Evaluates candidate qualifications, statutory licenses, and technical keywords
 * across Energy, Gas PRMS, BESS, SCADA/PLC, and Lean/5S domains.
 * Includes an instant Action Item generator to generate tailored STAR CV bullets.
 */

export const CANONICAL_CV_PROFILE = {
  name: "עידו גל",
  name_en: "Ido Gal",
  title_he: "בקר גז טבעי ותפעול מערכות אנרגיה | הנדסאי מכונות",
  title_en: "Gas Controller | Natural Gas & Energy Systems Operations | Practical Mechanical Engineer",
  contact: {
    phone: "050-000-0000",
    phone_intl: "+972-50-000-0000",
    email: "contact@ido-gal.dev",
    linkedin: "https://www.linkedin.com/in/ido-g",
    location: "תל אביב"
  },
  education: [
    "הנדסאי מכונות – התמחות בגז טבעי ובאנרגיה ירוקה, המרכז האקדמי רופין, 2022. פרויקט גמר: השוואת נצילות וכדאיות כלכלית וטכנית של מערכת סולארית PV בעלת פאנלים דו-צדדיים (Bifacial) לבין מערכת בעלת פאנלים חד-צדדיים (Monofacial).",
    "לימודי חשמלאי מוסמך, המרכז האקדמי רופין, 2026 (במהלך לימודים, כחודשיים לסיום)."
  ],
  experience: [
    "Energean Israel Ltd. (2022–היום): בקר גז - תפעול ומוצר. בקרה 24/7, ניטור לחצים וספיקות, Nomination ו-Re-nomination, ממשק מול אסדת הפקה ימית (FPSO), נתג״ז, לקוחות מסחריים, משמרות לילה עצמאיות, דוחות SAP ו-Excel, אוטומציה עם Copilot 365 ו-Gemini.",
    "וולקן עוצמה בע״מ / Energean (2020–2022): אחמ״ש אבטחה, מתקן אנרגיה אסטרטגי.",
    "ראש צוות ומדריך מכירות (2015–2020): פעילות בינלאומית (ארה״ב וגרמניה) באנגלית שוטפת.",
    "Group MER (2010–2012): מתקין מערכות סולאריות PV בשטח."
  ],
  military: "סיירת נח״ל | חבלה והנדסה קרבית | 2012–2015 (כולל קבע). רובאי 08, פלס/חבלה 07, ניסיון מבצעי בהפעלת רחפנים (UAV), סריקה ומיפוי שטח.",
  skills: [
    "SCADA", "PRMS", "Nomination", "Re-nomination", "FPSO", "SAP", "Excel",
    "Copilot 365", "Gemini", "Bifacial PV", "Monofacial PV", "ניטור לחצים וספיקות",
    "אסדת הפקה", "נתג״ז", "חבלה 07", "רובאי 08", "הפעלת רחפנים", "UAV",
    "מתח נמוך", "חוק החשמל"
  ],
  text: `עידו גל בקר גז טבעי ותפעול מערכות אנרגיה הנדסאי מכונות רופין 2022 אנרגיה ירוקה וגז טבעי
פרויקט גמר פאנלים סולאריים דו צדדיים Bifacial PV מול Monofacial
לימודי חשמלאי מוסמך רופין 2026 לקראת סיום חוק החשמל חישובים תיאורטיים
Energean בקר גז תפעול ומוצר אסדת הפקה FPSO נתג״ז PRMS SCADA Nomination Re-nomination SAP Excel מתקן אנרגיה 24/7
וולקן עוצמה אחמ״ש אבטחה מתקן אנרגיה אסטרטגי
Group MER מתקין מערכות סולאריות PV שטח עבודה בגובה
סיירת נח״ל חבלה והנדסה קרבית פלס 07 רובאי 08 מפעיל רחפנים מבצעי טלמטריה
טלפון 050-000-0000 דואל contact@ido-gal.dev לינקדאין https://www.linkedin.com/in/ido-g`
};

export const STATUTORY_HARD_GATES = [
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

export const KEYWORD_TAXONOMY = {
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

export const ATS_STRUCTURAL_RULES = [
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

export function evaluateHardGates(jobText) {
  if (!jobText || typeof jobText !== 'string' || !jobText.trim()) {
    return [];
  }
  const results = [];
  STATUTORY_HARD_GATES.forEach(gate => {
    if (gate.regex.test(jobText)) {
      let status = gate.candidate_status;
      let evidence = gate.candidate_evidence;
      let note = gate.note_he || '';

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

export function extractMissingKeywords(jobText, cvProfile) {
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

export function checkAtsStructuralCompliance(cvElement) {
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
  const contentText = (el && (el.innerText || el.textContent)) ? (el.innerText || el.textContent) : CANONICAL_CV_PROFILE.text;
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

export function runAtsJobMatching(jobText, cvProfile) {
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

  const hardGates = evaluateHardGates(jobText);

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
    score += Math.round(keywordRatio * 20) - 10;
  }

  if (structural.passed) {
    score += 5;
  } else {
    score -= structural.issues.length * 5;
  }

  score = Math.max(0, Math.min(100, score));

  let summary = "";
  if (hasCriticalGap) {
    summary = "נמצאו פערי סף מהותיים (תואר מהנדס B.Sc או ממונה בטיחות סטטוטורי). נדרש אימות דרישות סף מול המעסיק.";
  } else if (score >= 85) {
    summary = "התאמה גבוהה מאד לנתוני המועמד ולדרישות הסטטוטוריות המרכזיות.";
  } else if (score >= 70) {
    summary = "התאמה טובה; מומלץ לשלב את מילות המפתח החסרות בקורות החיים להעלאת הציון ב-ATS.";
  } else {
    summary = "התאמה בינונית; קיימים פערי מילות מפתח מרובים המצריכים התאמה ממוקדת של קו״ח.";
  }

  return {
    matchScore: score,
    hardGates: hardGates,
    missingKeywords: {
      methodologies: keywordResult.methodologies,
      financials: keywordResult.financials,
      systems: keywordResult.systems,
      energy: keywordResult.energy
    },
    matchedKeywords: keywordResult.matched,
    structuralCompliance: structural,
    summary: summary
  };
}

/**
 * Action Item Generator: Generates targeted, operational STAR CV bullet points
 * for any missing technical keyword or statutory qualification.
 * @param {string} keywordOrGate - Keyword term or gate ID
 * @param {Object} [jobContext] - Optional job context for tailor-made phrasing
 * @returns {Object} Action item with Hebrew & English STAR bullet suggestions and category
 */
export function generateCvBulletActionItem(keywordOrGate, jobContext = {}) {
  const term = String(keywordOrGate || '').trim().toLowerCase();
  const company = (jobContext && jobContext.company) ? jobContext.company : 'חברה תעשייתית';

  // Specific high-impact templates mapped to candidate's verified background
  const bulletTemplates = {
    // Systems & Automation
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
    hmi: {
      category: 'systems',
      label: 'HMI / ממשק מפעיל',
      bulletHe: 'תפעול ממשקי HMI מורכבים בחדר בקרה רציף, זיהוי חריגות לחץ וספיקה והפעלת פרוטוקולי חירום ואוטומציה ללא השבתת תהליך.',
      bulletEn: 'Operating complex control-room HMI consoles, detecting pressure/flow deviations, and activating emergency response protocols without process interruption.'
    },
    modbus: {
      category: 'systems',
      label: 'Modbus / פרוטוקולי תקשורת תעשייתית',
      bulletHe: 'בדיקת תקינות שידורי טלמטריה ומשדרי לחץ וטמפרטורה בפרוטוקול Modbus RTU/TCP מול מרכז הבקרה הארצי (נתג״ז).',
      bulletEn: 'Verifying telemetry data integrity and Modbus RTU/TCP field transmitters interfacing with national dispatch control systems.'
    },

    // Energy & Electrical
    bess: {
      category: 'energy',
      label: 'BESS / אגירת אנרגיה',
      bulletHe: 'ניתוח הנדסי ותפעול מערכות אגירת אנרגיה (BESS) וסוללות ליתיום, תוך בקרה על פרופילי טעינה/פריקה, מערכות קירור וייצוב תדר רשת החשמל.',
      bulletEn: 'Operational analysis and integration of Battery Energy Storage Systems (BESS), overseeing charge/discharge profiles, thermal management, and grid stability.'
    },
    'high voltage': {
      category: 'energy',
      label: 'מתח גבוה / High Voltage',
      bulletHe: 'עבודה בסביבת מתקני מתח גבוה וטרנספורמטורים, הקפדה על נהלי כניסה, ניתוק, נעילה ותיוג (LOTO) תחת פיקוח מהנדס חשמל.',
      bulletEn: 'Working within high-voltage sub-stations and transformer yards, strictly maintaining LOTO safety protocols under registered PE supervision.'
    },
    'bifacial pv': {
      category: 'energy',
      label: 'Bifacial PV / סולארי דו-צדדי',
      bulletHe: 'הובלת פרויקט הנדסי לבחינת כדאיות ונצילות של פאנלים סולאריים דו-צדדיים (Bifacial) לעומת חד-צדדיים, כולל סימולציות תפוקה וחיבור לרשת.',
      bulletEn: 'Authored engineering thesis benchmarking efficiency and economic ROI of Bifacial vs. Monofacial solar PV arrays, including grid-connection models.'
    },
    fpso: {
      category: 'energy',
      label: 'FPSO / אסדת הפקה ימית',
      bulletHe: 'ממשק תפעולי 24/7 מול אסדת הפקה ימית (FPSO Energean Power), ניטור זרימות גז טבעי והתאמת כמויות Nomination בזמן אמת.',
      bulletEn: '24/7 operational coordination with offshore FPSO (Energean Power), executing gas flow nominations and real-time delivery reconciliation.'
    },

    // Methodologies & Operational Excellence
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
    kaizen: {
      category: 'methodologies',
      label: 'Kaizen / שיפור מתמיד',
      bulletHe: 'הובלת יוזמות שיפור מתמיד (Kaizen) לתהליכי דיווח נתונים יומיים, באמצעות אוטומציה מבוססת Python ו-Excel.',
      bulletEn: 'Initiated Kaizen continuous improvement cycles for daily operational reporting, implementing Python and Excel automation scripts.'
    },

    // Financials & Engineering Economics
    capex: {
      category: 'financials',
      label: 'CAPEX / השקעות הוניות',
      bulletHe: 'בחינת תקציבי השקעה הונית (CAPEX) בפרויקטי תשתיות אנרגיה וחישובי פחת ציוד כחלק ממחקרי היתכנות הנדסיים.',
      bulletEn: 'Evaluated CAPEX budgets and asset depreciation models for energy infrastructure expansion projects.'
    },
    opex: {
      category: 'financials',
      label: 'OPEX / עלויות תפעול',
      bulletHe: 'ניתוח עלויות תפעול שוטפות (OPEX) של מערכי שאיבה ודחיסה, כולל אופטימיזציית צריכת אנרגיה עצמית במשמרות פעילות.',
      bulletEn: 'Analyzed ongoing operational expenditures (OPEX) for compression equipment, optimizing parasitic electrical loads during peak hours.'
    },
    roi: {
      category: 'financials',
      label: 'ROI / כדאיות כלכלית',
      bulletHe: 'חישוב מדדי החזר השקעה (ROI) ותקופת Payback עבור שדרוג מתקני אנרגיה סולארית ומערכי ניטור מתקדמים.',
      bulletEn: 'Calculated project payback periods and Return on Investment (ROI) metrics for solar system upgrades and smart telemetry retrofits.'
    },

    // Statutory Hard Gates
    gate_certified_electrician: {
      category: 'statutory',
      label: 'חשמלאי מוסמך (בלימודים לקראת סיום)',
      bulletHe: 'לימודי חשמלאי מוסמך במרכז האקדמי רופין (סיום צפוי: 2026, כחודשיים לסיום) — שליטה מעמיקה בחוק החשמל, מעגלי פיקוד ותכנון לוחות מתח נמוך.',
      bulletEn: 'Certified Electrician coursework near completion at Ruppin Academic Center (expected 2026) — in-depth mastery of the Israeli Electricity Law and LV switchboard design.'
    },
    gate_working_at_heights: {
      category: 'statutory',
      label: 'עבודה בגובה',
      bulletHe: 'הסמכת עבודה בגובה פעילה וניסיון מעשי מוכח בהתקנת מערכות סולאריות PV וקונסטרוקציות גג תעשייתיות ב-Group MER.',
      bulletEn: 'Certified in Working at Heights with hands-on track record executing rooftop solar PV and industrial mounting installations at Group MER.'
    },
    gate_safety_officer: {
      category: 'statutory',
      label: 'בטיחות ונהלי תפעול מחמירים',
      bulletHe: 'ניהול משמרות ואכיפת נהלי בטיחות מחמירים באתרי אנרגיה רגישים (סיווג בטחוני גבוה), תדריכי בטיחות לעובדים וקבלני שטח ומניעת מפגעים.',
      bulletEn: 'Enforced high-security industrial safety protocols at critical energy infrastructure, directing daily safety briefings for field contractors.'
    }
  };

  // Check direct match in templates
  let matched = bulletTemplates[term];
  if (!matched) {
    // Partial substring search
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

  // Smart Generic Generator
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

// Window export for tests and headless runners
if (typeof window !== 'undefined') {
  window.CANONICAL_CV_PROFILE = CANONICAL_CV_PROFILE;
  window.STATUTORY_HARD_GATES = STATUTORY_HARD_GATES;
  window.KEYWORD_TAXONOMY = KEYWORD_TAXONOMY;
  window.ATS_STRUCTURAL_RULES = ATS_STRUCTURAL_RULES;
  window.evaluateHardGates = evaluateHardGates;
  window.extractMissingKeywords = extractMissingKeywords;
  window.checkAtsStructuralCompliance = checkAtsStructuralCompliance;
  window.runAtsJobMatching = runAtsJobMatching;
  window.generateCvBulletActionItem = generateCvBulletActionItem;
}
