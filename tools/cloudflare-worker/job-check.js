/**
 * Job liveness checker - Cloudflare Worker.
 *
 * GET /?u=<encoded job url>
 * Response: { "state": "inactive" | "active" | "unknown", "reason": string, "status": number }
 *
 * "unknown" means the target blocked the request, rate limited it, failed or timed out.
 * It is never reported as active, and is always returned with Cache-Control: no-store.
 *
 * Canonical signature source: src/closure_signatures.json
 */

const DEFAULT_ORIGINS = [
  "https://idogal0210-web.github.io",
  "http://localhost:8099",
  "http://localhost:8000",
  "http://127.0.0.1:8099",
];

const USER_AGENT =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

const MAX_RESPONSE_BYTES = 1024 * 1024; // 1 MiB ceiling
const RATE_LIMIT_WINDOW_MS = 60 * 1000;
const RATE_LIMIT_MAX_REQ = 60;
const ipBuckets = new Map();

export const CLOSURE_CONFIG = {
  version: "2.0.0",
  known_ats_hosts: [
    "linkedin.com",
    "comeet.com",
    "comeet.co",
    "greenhouse.io",
    "lever.co",
    "ashbyhq.com",
    "myworkdayjobs.com",
    "workday.com",
    "smartrecruiters.com",
    "bamboohr.com",
    "drushim.co.il",
    "alljobs.co.il",
    "jobmaster.co.il",
    "gotfriends.co.il",
    "sqlink.com",
    "ethosia.co.il",
    "nisha.co.il"
  ],
  structural_markers: [
    {
      id: "linkedin_closed_flavor",
      group: "dom_linkedin_closed",
      pattern: "closed-job__flavor",
      flags: "i",
      reason: "משרה סגורה בלינקדאין"
    },
    {
      id: "linkedin_topcard_closed",
      group: "dom_linkedin_closed",
      pattern: "topcard__flavor--closed",
      flags: "i",
      reason: "משרה סגורה בלינקדאין"
    },
    {
      id: "data_job_closed_attr",
      group: "dom_data_closed",
      pattern: "data-job-(?:closed|expired)=[\"']true[\"']",
      flags: "i",
      reason: "המשרה סומנה כסגורה באתר"
    }
  ],
  strong_signatures: [
    {
      id: "en_not_currently_accepting",
      group: "en_not_accepting",
      pattern: "not currently accepting applications",
      flags: "i",
      reason: "הגשת המועמדות נסגרה (Not currently accepting applications)"
    },
    {
      id: "en_no_longer_accepting",
      group: "en_not_accepting",
      pattern: "no longer accepting applications",
      flags: "i",
      reason: "הגשת המועמדות נסגרה (No longer accepting applications)"
    },
    {
      id: "en_not_accepting_variants",
      group: "en_not_accepting",
      pattern: "(?:not|no longer|not currently)\\s+accepting\\s+applications",
      flags: "i",
      reason: "הגשת המועמדות נסגרה"
    },
    {
      id: "en_applications_no_longer_accepted",
      group: "en_not_accepting",
      pattern: "applications are no longer being accepted",
      flags: "i",
      reason: "הגשת המועמדות נסגרה"
    },
    {
      id: "en_this_job_no_longer_available",
      group: "en_no_longer_available",
      pattern: "this job is no longer available",
      flags: "i",
      reason: "המשרה אינה זמינה עוד"
    },
    {
      id: "en_this_position_closed_filled_expired",
      group: "en_position_closed",
      pattern: "this (?:job|position|role) (?:is|has been) (?:closed|filled|expired)",
      flags: "i",
      reason: "המשרה נסגרה"
    },
    {
      id: "en_this_position_is_closed",
      group: "en_position_closed",
      pattern: "this position is closed",
      flags: "i",
      reason: "המשרה נסגרה"
    },
    {
      id: "en_position_no_longer_open",
      group: "en_no_longer_available",
      pattern: "position is no longer open",
      flags: "i",
      reason: "המשרה אינה פתוחה עוד"
    },
    {
      id: "en_job_posting_expired",
      group: "en_posting_expired",
      pattern: "job posting has expired",
      flags: "i",
      reason: "תוקף פרסום המשרה פג"
    },
    {
      id: "en_job_filled_closed_removed",
      group: "en_job_closed_removed",
      pattern: "job (?:has been|was) (?:filled|closed|removed)",
      flags: "i",
      reason: "המשרה נסגרה"
    },
    {
      id: "en_position_has_been_filled",
      group: "en_position_filled",
      pattern: "position (?:has been )?filled",
      flags: "i",
      reason: "המשרה אויישה"
    },
    {
      id: "he_job_inactive",
      group: "he_job_inactive",
      pattern: "המשרה (?:אינה|איננה) פעילה",
      flags: "",
      reason: "המשרה אינה פעילה באתר"
    },
    {
      id: "he_job_closed",
      group: "he_job_closed",
      pattern: "המשרה נסגרה",
      flags: "",
      reason: "המשרה נסגרה לקבלת מועמדויות"
    },
    {
      id: "he_job_filled",
      group: "he_job_filled",
      pattern: "המשרה אוישה",
      flags: "",
      reason: "המשרה אוישה"
    },
    {
      id: "he_job_removed",
      group: "he_job_removed",
      pattern: "המשרה הוסרה",
      flags: "",
      reason: "המשרה הוסרה מהאתר"
    },
    {
      id: "he_job_page_not_found",
      group: "he_page_not_found",
      pattern: "דף המשרה לא נמצא",
      flags: "",
      reason: "דף המשרה לא נמצא באתר"
    },
    {
      id: "he_job_not_located",
      group: "he_job_not_located",
      pattern: "לא אותרה משרה",
      flags: "",
      reason: "לא אותרה משרה פעילה"
    },
    {
      id: "he_ad_not_relevant",
      group: "he_ad_not_relevant",
      pattern: "מודעה זו אינה רלוונטית",
      flags: "",
      reason: "המודעה אינה רלוונטית עוד"
    },
    {
      id: "he_applications_ended",
      group: "he_not_accepting",
      pattern: "הגשת מועמדות למשרה זו הסתיימה",
      flags: "",
      reason: "הגשת מועמדות הסתיימה"
    },
    {
      id: "he_not_accepting_applications",
      group: "he_not_accepting",
      pattern: "(?:אינה|איננה|לא) מקבלת מועמדויות",
      flags: "",
      reason: "הגשת המועמדות נסגרה"
    }
  ],
  weak_signatures: [
    {
      id: "en_page_not_found",
      group: "en_page_not_found",
      pattern: "\\bpage not found\\b",
      flags: "i",
      reason: "דף המשרה לא נמצא"
    },
    {
      id: "en_no_longer_available_open_active",
      group: "en_no_longer_available",
      pattern: "\\bno longer (?:available|open|active)\\b",
      flags: "i",
      reason: "המשרה אינה זמינה עוד"
    },
    {
      id: "en_posting_closed_expired",
      group: "en_posting_expired",
      pattern: "\\bposting (?:is )?(?:closed|expired)\\b",
      flags: "i",
      reason: "תוקף פרסום המשרה פג"
    },
    {
      id: "he_expired_generic",
      group: "he_expired_generic",
      pattern: "פג תוקף(?:ה של המשרה| המשרה| המודעה)?",
      flags: "",
      reason: "תוקף פרסום המשרה פג"
    }
  ]
};

function allowedOrigins(env) {
  const extra = (env && env.ALLOWED_ORIGINS ? env.ALLOWED_ORIGINS : "")
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
  return DEFAULT_ORIGINS.concat(extra);
}

function corsHeaders(origin, env, cacheable = false) {
  const allowed = allowedOrigins(env);
  const headers = {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": cacheable ? "public, max-age=3600" : "no-store",
    Vary: "Origin",
  };
  if (origin && allowed.includes(origin)) {
    headers["Access-Control-Allow-Origin"] = origin;
    headers["Access-Control-Allow-Methods"] = "GET, OPTIONS";
    headers["Access-Control-Allow-Headers"] = "Content-Type, X-Job-Check-Token";
  }
  return headers;
}

function reply(body, status, origin, env) {
  const isCacheable =
    status === 200 &&
    body &&
    (body.state === "active" || body.state === "inactive");
  return new Response(JSON.stringify(body), {
    status,
    headers: corsHeaders(origin, env, isCacheable),
  });
}

function checkRateLimit(ip) {
  const now = Date.now();
  const key = ip || "anon";
  let bucket = ipBuckets.get(key);
  if (!bucket || now - bucket.windowStart > RATE_LIMIT_WINDOW_MS) {
    bucket = { windowStart: now, count: 0 };
  }
  bucket.count += 1;
  ipBuckets.set(key, bucket);
  if (ipBuckets.size > 1000) {
    for (const [k, v] of ipBuckets.entries()) {
      if (now - v.windowStart > RATE_LIMIT_WINDOW_MS) ipBuckets.delete(k);
    }
  }
  return bucket.count <= RATE_LIMIT_MAX_REQ;
}

function isSafeTarget(raw) {
  let url;
  try {
    url = new URL(raw);
  } catch (e) {
    return null;
  }
  if (url.protocol !== "https:" && url.protocol !== "http:") return null;
  const host = url.hostname.toLowerCase();
  if (host === "localhost" || host.endsWith(".local") || host.endsWith(".internal")) return null;
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(host) || host.includes(":")) return null;
  return url;
}

function isKnownAtsUrl(rawUrl) {
  try {
    const host = new URL(rawUrl).hostname.toLowerCase();
    return CLOSURE_CONFIG.known_ats_hosts.some(
      (d) => host === d || host.endsWith("." + d)
    );
  } catch (e) {
    return false;
  }
}

function collectJsonLdPostings(node, out, inItemList = false) {
  if (!node) return;
  if (Array.isArray(node)) {
    for (const item of node) collectJsonLdPostings(item, out, inItemList);
    return;
  }
  if (typeof node !== "object") return;
  const rawType = node["@type"];
  const types = (Array.isArray(rawType) ? rawType : [rawType])
    .filter(Boolean)
    .map((t) => String(t).split("/").pop());
  if (types.includes("ItemList")) return;
  if (types.includes("JobPosting") && !inItemList) {
    out.push(node);
    return;
  }
  if (node["@graph"]) collectJsonLdPostings(node["@graph"], out, inItemList);
  if (node.mainEntity) collectJsonLdPostings(node.mainEntity, out, inItemList);
  if (node.about) collectJsonLdPostings(node.about, out, inItemList);
}

export function evaluateJsonLdJobPosting(html, pageUrl = "") {
  if (!html) return { isExpired: false, hasActive: false };
  const scriptRe = /<script[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
  const postings = [];
  let m;
  while ((m = scriptRe.exec(html)) !== null) {
    try {
      const parsed = JSON.parse(m[1].trim());
      collectJsonLdPostings(parsed, postings);
    } catch (e) {
      // Ignore malformed JSON-LD block
    }
  }
  if (postings.length === 0) return { isExpired: false, hasActive: false };

  let targetPostings = postings;
  if (postings.length > 1 && pageUrl) {
    const normUrl = pageUrl.split("?")[0].replace(/\/$/, "").toLowerCase();
    const matched = postings.filter((p) => {
      for (const k of ["url", "sameAs", "@id"]) {
        const val = String(p[k] || "").split("?")[0].replace(/\/$/, "").toLowerCase();
        if (val && val === normUrl) return true;
      }
      return false;
    });
    if (matched.length > 0) targetPostings = matched;
  }

  const today = new Date().toISOString().slice(0, 10);
  let expiredCount = 0;
  let activeCount = 0;
  for (const p of targetPostings) {
    const vt = String(p.validThrough || "").trim();
    const dm = vt.match(/^(\d{4}-\d{2}-\d{2})/);
    if (!dm) {
      activeCount += 1;
    } else if (dm[1] < today) {
      expiredCount += 1;
    } else {
      activeCount += 1;
    }
  }
  return {
    isExpired: expiredCount > 0 && activeCount === 0,
    hasActive: activeCount > 0,
  };
}

function extractDomViews(html) {
  const withoutScripts = String(html || "").replace(
    /<(script|style|noscript|template|svg)\b[^>]*>[\s\S]*?<\/\1>/gi,
    " "
  );
  const withoutBoilerplate = withoutScripts.replace(
    /<(nav|footer|header|aside)\b[^>]*>[\s\S]*?<\/\1>/gi,
    " "
  );

  const prominentParts = [];
  const titleMatch = withoutScripts.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i);
  if (titleMatch) prominentParts.push(titleMatch[1]);
  const headingRe = /<h[1-3]\b[^>]*>([\s\S]*?)<\/h[1-3]>/gi;
  let hm;
  while ((hm = headingRe.exec(withoutBoilerplate)) !== null) {
    prominentParts.push(hm[1]);
  }
  const alertRe = /<([a-z0-9]+)\b[^>]*(?:role=["']alert["']|(?:class|id)=["'][^"']*(?:alert|closed|expired|inactive|error|not-found|empty-state|status-banner|job-closed)[^"']*["'])[^>]*>([\s\S]*?)<\/\1>/gi;
  let am;
  while ((am = alertRe.exec(withoutBoilerplate)) !== null) {
    prominentParts.push(am[2]);
  }

  const stripTags = (s) =>
    String(s || "")
      .replace(/<[^>]+>/g, " ")
      .replace(/\s+/g, " ")
      .trim();

  const visibleText = stripTags(withoutBoilerplate);
  const prominentText = stripTags(prominentParts.join(" "));
  const hasActiveApply =
    /(?:\bapply\s+now\b|\bsubmit\s+application\b|\bapply\s+for\s+this\s+job\b|הגש(?:ו|י)?\s+מועמדות|הגשת\s+מועמדות|שלח(?:ו|י)?\s+קורות\s+חיים)/i.test(
      visibleText
    );

  return {
    domWithoutScripts: withoutScripts,
    visibleText,
    prominentText,
    hasActiveApply,
  };
}

function matchSignatureGroup(entries, text) {
  if (!text) return [];
  const matched = [];
  const seen = new Set();
  for (const entry of entries) {
    const re = new RegExp(entry.pattern, entry.flags || "");
    if (re.test(text)) {
      const grp = entry.group || entry.id || entry.pattern;
      if (!seen.has(grp)) {
        seen.add(grp);
        matched.push(entry);
      }
    }
  }
  return matched;
}

export function classifyHtml(html, pageUrl = "", status = 200) {
  const views = extractDomViews(html);
  const structural = matchSignatureGroup(
    CLOSURE_CONFIG.structural_markers,
    views.domWithoutScripts
  );
  if (structural.length > 0) {
    return { state: "inactive", reason: structural[0].reason, status };
  }

  const strongMatches = matchSignatureGroup(
    CLOSURE_CONFIG.strong_signatures,
    views.visibleText
  );
  const strongGroups = new Set(strongMatches.map((m) => m.group));
  const weakMatches = matchSignatureGroup(
    CLOSURE_CONFIG.weak_signatures,
    views.visibleText
  ).filter((m) => !strongGroups.has(m.group));

  const prominentStrong = matchSignatureGroup(
    CLOSURE_CONFIG.strong_signatures,
    views.prominentText
  );
  const prominentWeak = matchSignatureGroup(
    CLOSURE_CONFIG.weak_signatures,
    views.prominentText
  );
  const prominentMatches =
    prominentStrong.length > 0 ? prominentStrong : prominentWeak;

  const { isExpired: jsonldExpired, hasActive: jsonldActive } =
    evaluateJsonLdJobPosting(html, pageUrl);

  if (isKnownAtsUrl(pageUrl)) {
    if (strongMatches.length > 0) {
      return { state: "inactive", reason: strongMatches[0].reason, status };
    }
    if (jsonldExpired) {
      return {
        state: "inactive",
        reason: "תוקף פרסום המשרה פג (validThrough)",
        status,
      };
    }
    if (
      weakMatches.length > 0 &&
      (prominentMatches.length > 0 ||
        weakMatches.length >= 2 ||
        !views.hasActiveApply)
    ) {
      return { state: "inactive", reason: weakMatches[0].reason, status };
    }
    return { state: "active", reason: "משרה פעילה ומאומתת", status };
  }

  const signals = [];
  for (const m of strongMatches) {
    signals.push(["strong:" + m.group, m.reason]);
  }
  if (jsonldExpired) {
    signals.push(["jsonld_expired", "תוקף פרסום המשרה פג (validThrough)"]);
  }
  if (prominentMatches.length > 0) {
    signals.push(["prominent_dom", prominentMatches[0].reason]);
  }
  if (
    !views.hasActiveApply ||
    prominentMatches.length > 0 ||
    strongMatches.length > 0 ||
    jsonldExpired
  ) {
    for (const m of weakMatches) {
      signals.push(["weak:" + m.group, m.reason]);
    }
  }
  if (
    (strongMatches.length > 0 || jsonldExpired) &&
    !views.hasActiveApply &&
    !jsonldActive
  ) {
    if (views.visibleText.length < 260 || jsonldExpired) {
      const primaryReason =
        strongMatches.length > 0
          ? strongMatches[0].reason
          : "תוקף פרסום המשרה פג (validThrough)";
      signals.push(["no_active_apply_cta", primaryReason]);
    }
  }

  if (signals.length >= 2) {
    return { state: "inactive", reason: signals[0][1], status };
  }

  return { state: "active", reason: "משרה פעילה ומאומתת", status };
}

async function readResponseTextBounded(resp, maxBytes = MAX_RESPONSE_BYTES) {
  if (!resp.body || typeof resp.body.getReader !== "function") {
    const txt = await resp.text();
    return txt.slice(0, maxBytes);
  }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: false });
  let total = 0;
  let out = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > maxBytes) {
      out += decoder.decode(value.subarray(0, maxBytes - (total - value.byteLength)), {
        stream: false,
      });
      try {
        await reader.cancel();
      } catch (e) {
        // Ignore cancel errors
      }
      break;
    }
    out += decoder.decode(value, { stream: true });
  }
  out += decoder.decode();
  return out;
}

async function fetchWithRetry(target) {
  let last = null;
  for (let attempt = 0; attempt < 2; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 9000);
    try {
      const resp = await fetch(target.toString(), {
        headers: {
          "User-Agent": USER_AGENT,
          Accept: "text/html,application/xhtml+xml",
          "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
        },
        redirect: "follow",
        signal: controller.signal,
      });
      clearTimeout(timer);
      if ((resp.status === 429 || resp.status === 503) && attempt === 0) {
        await new Promise((r) => setTimeout(r, 1500));
        continue;
      }
      return { resp };
    } catch (e) {
      clearTimeout(timer);
      last = e;
    }
  }
  return { error: last };
}

async function classify(target) {
  const { resp } = await fetchWithRetry(target);
  if (!resp) {
    return { state: "unknown", reason: "פסק זמן או שגיאת תקשורת, לא ניתן לאמת", status: 0 };
  }
  const status = resp.status;
  if (status === 404 || status === 410) {
    return { state: "inactive", reason: `דף המשרה הוסר (HTTP ${status})`, status };
  }
  if (status === 401 || status === 403 || status === 429 || status >= 500) {
    return { state: "unknown", reason: `האתר חסם או לא ענה (HTTP ${status}), לא ניתן לאמת`, status };
  }
  const finalUrl = (resp.url || target.toString()).toLowerCase();
  if (
    target.toString().toLowerCase().includes("jobs/view") &&
    !finalUrl.includes("jobs/view") &&
    finalUrl.includes("linkedin.com")
  ) {
    return { state: "inactive", reason: "הפניה לדף ראשי - המשרה הוסרה", status };
  }
  const html = await readResponseTextBounded(resp, MAX_RESPONSE_BYTES);
  return classifyHtml(html, resp.url || target.toString(), status);
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin, env, false) });
    }
    if (request.method !== "GET") {
      return reply({ error: "method_not_allowed" }, 405, origin, env);
    }
    if (!origin || !allowedOrigins(env).includes(origin)) {
      return reply({ error: "origin_not_allowed" }, 403, origin, env);
    }
    const clientIp = request.headers.get("CF-Connecting-IP") || "";
    if (!checkRateLimit(clientIp)) {
      return reply({ error: "rate_limited", state: "unknown" }, 429, origin, env);
    }
    if (env && env.JOB_CHECK_TOKEN) {
      const provided =
        request.headers.get("X-Job-Check-Token") ||
        new URL(request.url).searchParams.get("token") ||
        "";
      if (provided !== env.JOB_CHECK_TOKEN) {
        return reply({ error: "unauthorized" }, 401, origin, env);
      }
    }
    const target = isSafeTarget(new URL(request.url).searchParams.get("u") || "");
    if (!target) {
      return reply({ error: "invalid_url" }, 400, origin, env);
    }
    const result = await classify(target);
    return reply(result, 200, origin, env);
  },
};
