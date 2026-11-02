/**
 * Job liveness checker - Cloudflare Worker.
 *
 * GET /?u=<encoded job url>
 * Response: { "state": "inactive" | "active" | "unknown", "reason": string, "status": number }
 *
 * "unknown" means the target blocked the request, rate limited it, failed or timed out.
 * It is never reported as active.
 *
 * Optional environment variable ALLOWED_ORIGINS: comma separated list of origins that may call
 * the worker. Defaults to the project GitHub Pages origin and localhost.
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

const SIGNATURES = [
  [/not currently accepting applications/i, "הגשת המועמדות נסגרה"],
  [/no longer accepting applications/i, "הגשת המועמדות נסגרה"],
  [/applications are no longer being accepted/i, "הגשת המועמדות נסגרה"],
  [/this job is no longer available/i, "המשרה אינה זמינה עוד"],
  [/this (?:job|position|role) (?:is|has been) (?:closed|filled|expired)/i, "המשרה נסגרה"],
  [/position is no longer open/i, "המשרה אינה פתוחה עוד"],
  [/job posting has expired/i, "תוקף פרסום המשרה פג"],
  [/job (?:has been|was) (?:filled|closed|removed)/i, "המשרה נסגרה"],
  [/no longer (?:available|open|active)/i, "המשרה אינה זמינה עוד"],
  [/posting (?:is )?(?:closed|expired)/i, "תוקף פרסום המשרה פג"],
  [/position (?:has been )?filled/i, "המשרה אויישה"],
  [/closed-job__flavor/i, "משרה סגורה בלינקדאין"],
  [/topcard__flavor--closed/i, "משרה סגורה בלינקדאין"],
  [/page not found/i, "דף המשרה לא נמצא"],
  [/המשרה (?:אינה|איננה) פעילה/, "המשרה אינה פעילה באתר"],
  [/המשרה נסגרה/, "המשרה נסגרה לקבלת מועמדויות"],
  [/המשרה אוישה/, "המשרה אוישה"],
  [/המשרה הוסרה/, "המשרה הוסרה מהאתר"],
  [/דף המשרה לא נמצא/, "דף המשרה לא נמצא באתר"],
  [/לא אותרה משרה/, "לא אותרה משרה פעילה"],
  [/מודעה זו אינה רלוונטית/, "המודעה אינה רלוונטית עוד"],
  [/הגשת מועמדות למשרה זו הסתיימה/, "הגשת מועמדות הסתיימה"],
  [/(?:אינה|איננה|לא) מקבלת מועמדויות/, "הגשת המועמדות נסגרה"],
  [/פג תוקף/, "תוקף פרסום המשרה פג"],
];

function allowedOrigins(env) {
  const extra = (env && env.ALLOWED_ORIGINS ? env.ALLOWED_ORIGINS : "")
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
  return DEFAULT_ORIGINS.concat(extra);
}

function corsHeaders(origin, env) {
  const allowed = allowedOrigins(env);
  const headers = {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "public, max-age=3600",
    Vary: "Origin",
  };
  if (origin && allowed.includes(origin)) {
    headers["Access-Control-Allow-Origin"] = origin;
    headers["Access-Control-Allow-Methods"] = "GET, OPTIONS";
  }
  return headers;
}

function reply(body, status, origin, env) {
  return new Response(JSON.stringify(body), { status, headers: corsHeaders(origin, env) });
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

function validThroughExpired(html) {
  const re = /"validThrough"\s*:\s*"(\d{4}-\d{2}-\d{2})/g;
  let m;
  const today = new Date().toISOString().slice(0, 10);
  while ((m = re.exec(html)) !== null) {
    if (m[1] < today) return true;
  }
  return false;
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
  const { resp, error } = await fetchWithRetry(target);
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
  const finalUrl = resp.url.toLowerCase();
  if (
    target.toString().toLowerCase().includes("jobs/view") &&
    !finalUrl.includes("jobs/view") &&
    finalUrl.includes("linkedin.com")
  ) {
    return { state: "inactive", reason: "הפניה לדף ראשי - המשרה הוסרה", status };
  }
  const html = await resp.text();
  for (const [re, reason] of SIGNATURES) {
    if (re.test(html)) return { state: "inactive", reason, status };
  }
  if (validThroughExpired(html)) {
    return { state: "inactive", reason: "תוקף פרסום המשרה פג (validThrough)", status };
  }
  return { state: "active", reason: "משרה פעילה ומאומתת", status };
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin, env) });
    }
    if (request.method !== "GET") {
      return reply({ error: "method_not_allowed" }, 405, origin, env);
    }
    if (!origin || !allowedOrigins(env).includes(origin)) {
      return reply({ error: "origin_not_allowed" }, 403, origin, env);
    }
    const target = isSafeTarget(new URL(request.url).searchParams.get("u") || "");
    if (!target) {
      return reply({ error: "invalid_url" }, 400, origin, env);
    }
    const result = await classify(target);
    return reply(result, 200, origin, env);
  },
};
