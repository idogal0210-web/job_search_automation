"""Bounded retries and independent, time-based circuit breakers per model."""
import json
import os
import random
import re
import time
from dataclasses import dataclass
from typing import Literal, Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class EvidenceQuote(BaseModel):
    model_config = ConfigDict(strict=True)
    quote: str = ""
    source_field: str = ""


class RequirementAssessment(BaseModel):
    model_config = ConfigDict(strict=True)
    requirement: str
    importance: Literal["required", "preferred", "unknown"] = "unknown"
    ad_evidence: EvidenceQuote = Field(default_factory=EvidenceQuote)
    profile_evidence: EvidenceQuote = Field(default_factory=EvidenceQuote)
    assessment: Literal["match", "gap", "unknown"] = "unknown"
    explanation: str = ""


class Evaluation(BaseModel):
    model_config = ConfigDict(strict=True)
    status: Literal["QUALIFIED", "DISQUALIFIED"]
    technical_role: bool
    match_score: int = Field(ge=0, le=100)
    concrete_matches_count: int = Field(ge=0, le=10)
    reasoning: str = Field(min_length=1)
    sector_key: Literal["solar", "natural_gas", "energy_tech", "drones", "cuas", "scada", "operations", "energy", "other"]
    sector: str = ""
    location: str = "לא צוין"
    company_domain_product: str = "לא צוין"
    job_summary: str = "לא צוין"
    experience_strengths: str = "לא צוין"
    key_highlights: str = "לא צוין"
    company_size: str = "לא צוין"
    junior_openness: str = "לא צוין"
    work_model: str = "לא צוין"
    company_requirements: str = "לא צוין"
    fit_gaps: str = "אין מספיק מידע לאימות פערי ההתאמה."
    requirement_assessments: list[RequirementAssessment] = Field(default_factory=list)

    @field_validator("junior_openness", mode="before")
    @classmethod
    def normalize_junior_openness(cls, v):
        if isinstance(v, bool):
            return "כן" if v else "לא"
        return str(v) if v is not None else "לא צוין"


class EvaluationUnavailable(RuntimeError):
    def __init__(self, reasons):
        self.reasons = reasons
        super().__init__(json.dumps(reasons, sort_keys=True))


class AtsScorecardCategory(BaseModel):
    model_config = ConfigDict(strict=True)
    category: str = Field(min_length=1)
    score: int = Field(ge=0, le=100)


class AtsCategorizedGap(BaseModel):
    model_config = ConfigDict(strict=True)
    requirement: str = Field(min_length=1)
    severity: Literal["blocking", "important", "nice_to_have"]
    explanation: str = Field(min_length=1)
    bridgeable: bool = True
    bridge_strategy: str = ""


class AtsStudioAnalysisSchema(BaseModel):
    model_config = ConfigDict(strict=True)
    overall_score: int = Field(ge=0, le=100)
    match_summary: str = Field(min_length=1)
    scorecard: list[AtsScorecardCategory] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    key_strengths: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    recommended_changes: list[str] = Field(default_factory=list)
    unmatched_requirements: list[str] = Field(default_factory=list)
    categorized_gaps: list[AtsCategorizedGap] = Field(default_factory=list)


class TailoredCvPackageSchema(BaseModel):
    model_config = ConfigDict(strict=True)
    cv_markdown: str = Field(min_length=1)
    cover_letter_markdown: str = Field(min_length=1)
    interview_talking_points: list[str] = Field(default_factory=list)
    unmatched_requirements: list[str] = Field(default_factory=list)


class CvTailoredBulletSchema(BaseModel):
    model_config = ConfigDict(strict=True)
    rewritten_bullet: str = Field(min_length=1)
    tone_mode: Literal["technical", "operational", "strategic"]
    active_verb: str = ""
    system_scope: str = ""
    metric_or_hse: str = ""
    grounded_in_profile: bool = True
    note_he: str = ""


class StarInterviewEvaluationSchema(BaseModel):
    model_config = ConfigDict(strict=True)
    total_score: int = Field(ge=0, le=100)
    situation_score: int = Field(ge=0, le=20)
    situation_feedback: str = ""
    task_score: int = Field(ge=0, le=20)
    task_feedback: str = ""
    action_score: int = Field(ge=0, le=40)
    action_feedback: str = ""
    result_score: int = Field(ge=0, le=20)
    result_feedback: str = ""
    golden_answer: str = ""
    improvement_tips: list[str] = Field(default_factory=list)


def classify_error(error):
    if isinstance(error, (ValidationError, json.JSONDecodeError)):
        return "invalid_response"
    code = getattr(error, "code", None) or getattr(error, "status_code", None)
    message = str(error).lower()
    if str(code) == "429" or "429" in message or "resource_exhausted" in message or "resource has been exhausted" in message:
        # 'quota' alone is NOT proof of a daily quota: per-minute limits use it too.
        if "per minute" in message or "per_minute" in message or "perminute" in message:
            return "rate_limit"
        if any(s in message for s in ("perday", "per_day", "per day", "daily", "free_tier", "quota exceeded")):
            return "daily_quota"
        return "rate_limit"
    if str(code) in {"401", "403"}:
        return "authentication"
    if str(code) in {"400", "404"}:
        return "configuration"
    if str(code) in {"408", "504"} or any(s in message for s in ("timeout", "timed out", "deadline_exceeded")):
        return "timeout"
    if str(code) in {"500", "502", "503"} or "503" in message or "unavailable" in message:
        return "unavailable"
    return "unknown_error"


def retry_after(error):
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", {}) or {}
    value = headers.get("Retry-After") or headers.get("retry-after")
    try:
        return max(0, float(value))
    except (ValueError, TypeError):
        match = re.search(r"retryDelay[^\d]*(\d+(?:\.\d+)?)s", str(error))
        return float(match.group(1)) if match else 0


@dataclass
class ModelState:
    failures: int = 0
    open_until: float = 0
    reason: str = ""


def mask_api_key(key: str) -> str:
    """Safely mask an API key for logs (e.g. AIza...4a12)."""
    if not key:
        return "<empty>"
    clean = key.strip()
    if len(clean) <= 8:
        return "***"
    return f"{clean[:4]}...{clean[-4:]}"


def load_gemini_api_keys() -> list[str]:
    """Collect unique Gemini API keys from GEMINI_API_KEYS and numbered GEMINI_API_KEY* env vars."""
    keys = []
    raw_keys = os.getenv("GEMINI_API_KEYS", "")
    if raw_keys:
        for k in re.split(r"[\s,]+", raw_keys):
            clean = k.strip()
            if clean and clean not in keys:
                keys.append(clean)

    primary = os.getenv("GEMINI_API_KEY", "").strip()
    if primary and primary not in keys:
        keys.append(primary)

    for i in range(2, 21):
        numbered = os.getenv(f"GEMINI_API_KEY_{i}", "").strip()
        if numbered and numbered not in keys:
            keys.append(numbered)

    return keys


class GeminiKeyEntry:
    def __init__(self, key: str, index: int, client: any = None):
        self.key = key
        self.index = index
        self.client = client
        self.is_daily_quota_exhausted = False
        self.open_until = 0.0
        self.masked = mask_api_key(key)


class GeminiClientPool:
    """Manages a pool of Gemini API keys with automatic failover upon daily quota exhaustion."""

    class _ModelsProxy:
        def __init__(self, pool):
            self._pool = pool

        def generate_content(self, *args, **kwargs):
            client = self._pool.get_current_client()
            if client is None:
                raise EvaluationUnavailable({"client": "all_api_keys_exhausted"})
            return client.models.generate_content(*args, **kwargs)

    def __init__(self, keys: list[str] = None, *, client_factory=None, clock=time.monotonic):
        if keys is None:
            keys = load_gemini_api_keys()
        self.clock = clock
        self._client_factory = client_factory or (lambda k: genai.Client(
            api_key=k,
            http_options=types.HttpOptions(
                timeout=20000,
                retry_options=types.HttpRetryOptions(attempts=1)
            )
        ))
        self.entries = []
        for i, k in enumerate(keys, 1):
            client = None
            try:
                client = self._client_factory(k)
            except Exception as e:
                print(f"[KEY_POOL] Warning: failed to initialize client for key {i}: {type(e).__name__}", flush=True)
            self.entries.append(GeminiKeyEntry(key=k, index=i, client=client))
        self.current_index = 0
        self.models = self._ModelsProxy(self)

    @property
    def has_keys(self) -> bool:
        return len(self.entries) > 0

    def active_key_count(self) -> int:
        return sum(1 for e in self.entries if not e.is_daily_quota_exhausted and e.client is not None)

    def total_key_count(self) -> int:
        return len(self.entries)

    def get_current_entry(self) -> Optional[GeminiKeyEntry]:
        if not self.entries:
            return None
        now = self.clock()
        for offset in range(len(self.entries)):
            idx = (self.current_index + offset) % len(self.entries)
            entry = self.entries[idx]
            if not entry.is_daily_quota_exhausted and entry.client is not None and now >= entry.open_until:
                self.current_index = idx
                return entry
        for offset in range(len(self.entries)):
            idx = (self.current_index + offset) % len(self.entries)
            entry = self.entries[idx]
            if not entry.is_daily_quota_exhausted and entry.client is not None:
                self.current_index = idx
                return entry
        return None

    def get_current_client(self):
        entry = self.get_current_entry()
        return entry.client if entry else None

    def rotate_on_error(self, error_kind: str) -> bool:
        """Mark current key as exhausted/cooling down and rotate to next available key.
        Returns True if a fresh active key is available, False if all keys are exhausted."""
        current = self.get_current_entry()
        if not current:
            return False

        if error_kind in {"daily_quota", "authentication"}:
            current.is_daily_quota_exhausted = True
            print(f"[KEY_ROTATION] Key {current.index}/{len(self.entries)} ({current.masked}) hit {error_kind}. Tripping key.", flush=True)
        else:
            current.open_until = self.clock() + 60.0
            print(f"[KEY_ROTATION] Key {current.index}/{len(self.entries)} ({current.masked}) hit {error_kind}. Backing off key for 60s.", flush=True)

        self.current_index = (self.current_index + 1) % len(self.entries)
        next_entry = self.get_current_entry()
        if next_entry and next_entry != current and not next_entry.is_daily_quota_exhausted:
            print(f"[KEY_ROTATION] Switched to Key {next_entry.index}/{len(self.entries)} ({next_entry.masked}).", flush=True)
            return True
        return False

    def is_all_exhausted(self) -> bool:
        return all(e.is_daily_quota_exhausted or e.client is None for e in self.entries)

    def close(self):
        for entry in self.entries:
            if entry.client is not None and hasattr(entry.client, "close"):
                try:
                    entry.client.close()
                except Exception:
                    pass


def init_gemini_client_pool(keys: list[str] = None) -> Optional[GeminiClientPool]:
    """Initialize a GeminiClientPool from environment variables or explicit keys."""
    pool = GeminiClientPool(keys)
    if not pool.has_keys or pool.active_key_count() == 0:
        return None
    print(f"[AI_CONFIG] Initialized Gemini key pool with {pool.active_key_count()} active keys (total {pool.total_key_count()}).", flush=True)
    return pool


class GeminiPool:
    """One pool per run; no global cross-job shutdown on a single model error."""
    def __init__(self, models=None, *, clock=time.monotonic, sleep=time.sleep,
                 jitter=lambda: random.uniform(0, 0.5), max_attempts=2, min_interval=2):
        configured = os.getenv("GEMINI_MODELS") or "gemini-3.5-flash-lite,gemini-flash-lite-latest,gemini-3.5-flash,gemini-3.8-flash"
        self.models = tuple(dict.fromkeys(models if models is not None else
                                         [m.strip() for m in configured.split(",") if m.strip()]))
        if not self.models:
            raise ValueError("GEMINI_MODELS must contain at least one model")
        self.states = {name: ModelState() for name in self.models}
        self.clock, self.sleep, self.jitter = clock, sleep, jitter
        self.max_attempts = max(1, min(3, max_attempts))
        self.min_interval = min_interval
        self.last_request = None

    def generate_json(self, client, prompt, *, schema=None, temperature=None, health=None):
        reasons = {}
        key_pool = client if isinstance(client, GeminiClientPool) else None
        for name in self.models:
            state = self.states[name]
            if self.clock() < state.open_until:
                reasons[name] = state.reason
                print(f"[MODEL_SKIP] model={name} reason={state.reason}", flush=True)
                continue
            while True:
                active_client = key_pool.get_current_client() if key_pool else client
                if active_client is None:
                    reasons[name] = "no_active_client"
                    break
                rotated_to_new_key = False
                for attempt in range(self.max_attempts):
                    if self.last_request is not None:
                        self.sleep(max(0, self.min_interval - (self.clock() - self.last_request)))
                    self.last_request = self.clock()
                    if health is not None:
                        health.gemini_attempts += 1
                    try:
                        cfg_kwargs = {"response_mime_type": "application/json"}
                        if schema is not None:
                            cfg_kwargs["response_schema"] = schema
                        if temperature is not None:
                            cfg_kwargs["temperature"] = temperature
                        cfg_kwargs["http_options"] = types.HttpOptions(
                            timeout=20000, retry_options=types.HttpRetryOptions(attempts=1)
                        )
                        response = active_client.models.generate_content(
                            model=name, contents=prompt,
                            config=types.GenerateContentConfig(**cfg_kwargs)
                        )
                        text = response.text or ""
                        if schema is not None:
                            data = schema.model_validate_json(text).model_dump()
                        else:
                            clean_text = text.strip()
                            if clean_text.startswith("```json"):
                                clean_text = clean_text[7:]
                            if clean_text.startswith("```"):
                                clean_text = clean_text[3:]
                            if clean_text.endswith("```"):
                                clean_text = clean_text[:-3]
                            data = json.loads(clean_text.strip())

                        state.failures, state.open_until, state.reason = 0, 0, ""
                        if health is not None:
                            health.gemini_successes += 1
                        data["evaluation_model"] = name
                        return data
                    except Exception as error:
                        kind = classify_error(error)
                        reasons[name] = kind
                        if health is not None:
                            health.gemini_failures += 1
                        print(f"[MODEL_ERROR] model={name} kind={kind} attempt={attempt+1}", flush=True)

                        if key_pool and kind in {"daily_quota", "authentication", "rate_limit"}:
                            if key_pool.rotate_on_error(kind):
                                rotated_to_new_key = True
                                break

                        delay = max(2 ** (attempt + 1) + self.jitter(), retry_after(error))
                        if (kind in {"invalid_response", "timeout", "unavailable", "rate_limit"}
                                and attempt + 1 < self.max_attempts and delay <= 8):
                            self.sleep(delay)
                            continue
                        state.failures += 1
                        state.reason = kind
                        if kind in {"daily_quota", "authentication", "configuration"} or state.failures >= 3:
                            state.open_until = float("inf")
                        else:
                            base = 60 if kind == "rate_limit" else 15
                            state.open_until = self.clock() + max(delay, min(300, base * 2 ** min(state.failures - 1, 4)))
                        break

                if not rotated_to_new_key or (key_pool and key_pool.is_all_exhausted()):
                    break
        raise EvaluationUnavailable(reasons)

    def is_exhausted(self) -> bool:
        """Check if all models in the pool have tripped circuit breakers for the run."""
        return all(self.states[name].open_until == float("inf") for name in self.models)

    def evaluate(self, client, prompt, health):
        data = self.generate_json(client, prompt, schema=Evaluation, health=health)
        data["evaluation_source"] = "gemini"
        data["evaluation_complete"] = True
        return data
