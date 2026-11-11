"""Bounded retries and independent, time-based circuit breakers per model."""
import json
import os
import random
import re
import time
from dataclasses import dataclass
from typing import Literal

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
    if str(code) == "429" or "429" in message or "resource_exhausted" in message:
        # 'quota' alone is NOT proof of a daily quota: per-minute limits use it too.
        if any(s in message for s in ("perday", "per_day", "per day", "daily")):
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


class GeminiPool:
    """One pool per run; no global cross-job shutdown on a single model error."""
    def __init__(self, models=None, *, clock=time.monotonic, sleep=time.sleep,
                 jitter=lambda: random.uniform(0, 0.5), max_attempts=2, min_interval=2):
        configured = os.getenv("GEMINI_MODELS") or "gemini-3.8-flash,gemini-3.5-flash-lite,gemini-3.5-flash"
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
        for name in self.models:
            state = self.states[name]
            if self.clock() < state.open_until:
                reasons[name] = state.reason
                print(f"[MODEL_SKIP] model={name} reason={state.reason}", flush=True)
                continue
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
                    response = client.models.generate_content(
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
                except Exception as error:
                    kind = classify_error(error)
                    reasons[name] = kind
                    if health is not None:
                        health.gemini_failures += 1
                    print(f"[MODEL_ERROR] model={name} kind={kind} attempt={attempt+1}", flush=True)
                    delay = max(2 ** (attempt + 1) + self.jitter(), retry_after(error))
                    if (kind in {"invalid_response", "timeout", "unavailable", "rate_limit"}
                            and attempt + 1 < self.max_attempts and delay <= 8):
                        self.sleep(delay)
                        continue
                    state.failures += 1
                    state.reason = kind
                    if kind in {"daily_quota", "authentication", "configuration"}:
                        state.open_until = float("inf")
                    else:
                        base = 60 if kind == "rate_limit" else 15
                        state.open_until = self.clock() + max(delay, min(300, base * 2 ** min(state.failures - 1, 4)))
                    break
                else:
                    state.failures, state.open_until, state.reason = 0, 0, ""
                    if health is not None:
                        health.gemini_successes += 1
                    data["evaluation_model"] = name
                    return data
        raise EvaluationUnavailable(reasons)

    def evaluate(self, client, prompt, health):
        data = self.generate_json(client, prompt, schema=Evaluation, health=health)
        data["evaluation_source"] = "gemini"
        data["evaluation_complete"] = True
        return data
