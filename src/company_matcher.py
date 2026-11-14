"""
Normalized word-boundary company name matching and employer blacklist verification.
Prevents substring false positives (e.g. 'mer' in 'Mercedes', 'intel' in 'Intelligent',
'ors' in 'Sensors', 'ingl' in 'Single', or generic Hebrew words 'עתיד'/'מעוף' in prose).
"""

import re
from typing import Iterable, List, Optional, Tuple

_DOUBLE_QUOTE_CHARS = '״“”„″'
_SINGLE_QUOTE_CHARS = "׳’‘`′"
_CORP_SUFFIX_RE = re.compile(
    r"(?:^|(?<=[\s,.\-]))(?:בע\"מ|בעמ|ltd\.?|inc\.?|corp\.?|corporation|llc|gmbh|limited|group|ישראל|israel)(?=$|[\s,.\-])",
    re.IGNORECASE,
)

# Ambiguous Hebrew words that are common nouns ("future", "vision/flight") and must only
# match when the company itself is the staffing agency or explicitly qualified as HR/placement.
_AMBIGUOUS_STAFFING_QUALIFIERS = {
    "עתיד": (
        "עתיד השמה",
        "עתיד משאבי אנוש",
        "עתיד כוח אדם",
        "עתיד כ\"א",
        "קבוצת עתיד",
        "עתיד בייקום",
    ),
    "מעוף": (
        "מעוף משאבי אנוש",
        "מעוף השמה",
        "מעוף כוח אדם",
        "מעוף כ\"א",
        "קבוצת מעוף",
        "מעוף אאוטסורסינג",
    ),
}


def normalize_company_name(value: str, strip_quotes: bool = False) -> str:
    """
    Normalize a company or employer name:
    - Strip zero-width/control characters
    - Apply Unicode casefold()
    - Unify Hebrew gershayim (״) and typographic quotes to ASCII '"'
    - Unify Hebrew geresh (׳) and typographic apostrophes to ASCII "'"
    - Optionally strip internal quotes/apostrophes for equivalence matching
    - Collapse whitespace
    """
    if not value:
        return ""
    s = re.sub(r"[\u200b-\u200f\u00a0\ufeff]", " ", str(value))
    s = s.casefold()
    for ch in _DOUBLE_QUOTE_CHARS:
        s = s.replace(ch, '"')
    for ch in _SINGLE_QUOTE_CHARS:
        s = s.replace(ch, "'")
    if strip_quotes:
        s = re.sub(r"(?<=[\w\u0590-\u05ff])[\"\'](?=[\w\u0590-\u05ff])", "", s)
    return " ".join(s.split())


def strip_corporate_suffixes(value: str) -> str:
    """Remove generic corporate suffixes (בע\"מ, Ltd, Inc, etc.) from a normalized company name."""
    norm = normalize_company_name(value)
    if not norm:
        return ""
    cleaned = _CORP_SUFFIX_RE.sub(" ", norm)
    cleaned = re.sub(r"^[\s,.\-|()]+|[\s,.\-|()]+$", "", cleaned)
    return " ".join(cleaned.split())


def deduplicate_employer_list(items: Iterable[str]) -> List[str]:
    """Deduplicate an employer list under quote-insensitive and case-folded normalization."""
    result: List[str] = []
    seen = set()
    for raw in items or []:
        norm = normalize_company_name(str(raw))
        if not norm:
            continue
        canon_key = normalize_company_name(norm, strip_quotes=True)
        if canon_key not in seen:
            seen.add(canon_key)
            result.append(norm)
    return result


def _word_boundary_pattern(token: str) -> re.Pattern:
    """
    Build a regex that matches `token` only on strict word boundaries
    across ASCII and Hebrew letters/digits (including internal quotes like נתג"ז).
    """
    word_char = r"0-9a-z\u0590-\u05ff"
    return re.compile(
        rf"(?<![{word_char}]){re.escape(token)}(?![{word_char}])",
        re.IGNORECASE,
    )


def company_tokens_match(company_name: str, key: str) -> bool:
    """
    Return True if `key` matches `company_name` on strict word boundaries after normalization.
    Checks both quote-preserved and quote-stripped forms so 'נתג״ז' matches 'נתג"ז' and 'נתגז',
    while 'mer' never matches 'Mercedes' and 'intel' never matches 'Intelligent'.
    """
    if not company_name or not key:
        return False

    for strip_q in (False, True):
        norm_company = normalize_company_name(company_name, strip_quotes=strip_q)
        norm_key = normalize_company_name(key, strip_quotes=strip_q)
        if not norm_company or not norm_key:
            continue
        if _word_boundary_pattern(norm_key).search(norm_company):
            return True
    return False


def match_excluded_employer(
    company_name: str,
    job_text: str = "",
    excluded_employers: Optional[Iterable[str]] = None,
) -> Tuple[bool, str]:
    """
    Check whether a company name (or explicit employer header in job_text) matches
    any entry in `excluded_employers` using normalized word-boundary rules.
    """
    norm_company = normalize_company_name(company_name or "")
    stripped_company = strip_corporate_suffixes(company_name or "")
    norm_text = normalize_company_name((job_text or "")[:300])

    if not norm_company and not norm_text:
        return False, ""

    candidates = deduplicate_employer_list(excluded_employers or [])
    for employer in candidates:
        token = normalize_company_name(employer)
        if not token:
            continue

        if token in _AMBIGUOUS_STAFFING_QUALIFIERS:
            if stripped_company == token:
                return True, f"החברה מופיעה ברשימת ההחרגות של מדיניות המועמד ({token})."
            for qualified in _AMBIGUOUS_STAFFING_QUALIFIERS[token]:
                if company_tokens_match(norm_company, qualified) or company_tokens_match(norm_text, qualified):
                    return True, f"החברה מופיעה ברשימת ההחרגות של מדיניות המועמד ({token})."
            continue

        if company_tokens_match(norm_company, token):
            return True, f"החברה מופיעה ברשימת ההחרגות של מדיניות המועמד ({token})."

        # For job_text fallback (when company_name is missing or generic), do not match
        # short <= 3 char ASCII tokens unless company_name itself matched above.
        is_short_ascii = len(token) <= 3 and token.isascii()
        if not is_short_ascii and norm_text and company_tokens_match(norm_text, token):
            return True, f"החברה מופיעה ברשימת ההחרגות של מדיניות המועמד ({token})."

    return False, ""
