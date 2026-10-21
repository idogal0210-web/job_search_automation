"""Bounded retries and independent, time-based circuit breakers per model."""
import json
import os
import random
import re
import time
from dataclasses import dataclass
from typing import Literal

from google.genai import types
from pydantic import BaseModel, ConfigDict, Field, ValidationError


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


class EvaluationUnavailable(RuntimeError):
    def __init__(self, reasons):
        self.reasons = reasons
        super().__init__(json.dumps(reasons, sort_keys=True))


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
        configured = os.getenv("GEMINI_MODELS") or "gemini-3.8-flash,gemini-3.7-flash,gemini-3.5-flash-lite,gemini-3.5-flash"
        self.models = tuple(dict.fromkeys(models if models is not None else
                                         [m.strip() for m in configured.split(",") if m.strip()]))
        if not self.models:
            raise ValueError("GEMINI_MODELS must contain at least one model")
        self.states = {name: ModelState() for name in self.models}
        self.clock, self.sleep, self.jitter = clock, sleep, jitter
        self.max_attempts = max(1, min(3, max_attempts))
        self.min_interval = min_interval
        self.last_request = None

    def evaluate(self, client, prompt, health):
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
                health.gemini_attempts += 1
                try:
                    response = client.models.generate_content(
                        model=name, contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json", response_schema=Evaluation,
                            http_options=types.HttpOptions(timeout=20000,
                                retry_options=types.HttpRetryOptions(attempts=1))))
                    data = Evaluation.model_validate_json(response.text or "").model_dump()
                except Exception as error:
                    kind = classify_error(error)
                    reasons[name] = kind
                    health.gemini_failures += 1
                    print(f"[MODEL_ERROR] model={name} kind={kind} attempt={attempt+1} error={error}", flush=True)
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
                    health.gemini_successes += 1
                    data["evaluation_source"] = "gemini"
                    data["evaluation_model"] = name
                    data["evaluation_complete"] = True
                    return data
        raise EvaluationUnavailable(reasons)
