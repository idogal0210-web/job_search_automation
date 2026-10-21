"""Bounded retries and independent circuit breakers for Groq (Llama 3.3 70B)."""
import json
import os
import random
import time
from dataclasses import dataclass
import requests
from pydantic import ValidationError

from src.gemini_runtime import Evaluation, EvaluationUnavailable, classify_error, retry_after


class GroqPool:
    """Evaluates jobs using Groq's high-speed API with Llama 3.3 70B."""
    def __init__(self, api_key=None, models=None, *, clock=time.monotonic, sleep=time.sleep,
                 jitter=lambda: random.uniform(0, 0.5), max_attempts=3, timeout=20, min_interval=2.0):
        self.api_key = api_key if api_key is not None else os.getenv("GROQ_API_KEY")
        configured = os.getenv("GROQ_MODELS") or "openai/gpt-oss-120b,openai/gpt-oss-20b,qwen/qwen3.8-27b"
        self.models = tuple(dict.fromkeys(models if models is not None else
                                         [m.strip() for m in configured.split(",") if m.strip()]))
        if not self.models:
            raise ValueError("GROQ_MODELS must contain at least one model")
        self.clock, self.sleep, self.jitter = clock, sleep, jitter
        self.max_attempts = max(1, min(3, max_attempts))
        self.timeout = timeout
        self.min_interval = min_interval
        self.last_request = None
        self.states = {name: {"failures": 0, "open_until": 0, "reason": ""} for name in self.models}

    def evaluate(self, prompt, health):
        if not self.api_key:
            raise EvaluationUnavailable({"groq": "missing_groq_api_key"})

        reasons = {}
        for name in self.models:
            state = self.states[name]
            if self.clock() < state["open_until"]:
                reasons[name] = state["reason"]
                print(f"[GROQ_SKIP] model={name} reason={state['reason']}", flush=True)
                continue

            for attempt in range(self.max_attempts):
                if self.last_request is not None:
                    self.sleep(max(0, self.min_interval - (self.clock() - self.last_request)))
                self.last_request = self.clock()
                health.gemini_attempts += 1
                try:
                    url = "https://api.groq.com/openai/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    system_msg = (
                        "You are an expert technical recruiter and job evaluation system. "
                        "You must return ONLY a valid JSON object strictly matching the required schema. "
                        "All explanatory and textual strings (such as reasoning, location, etc.) must be in Hebrew. "
                        "Do not include any conversational preamble or markdown code blocks."
                    )
                    payload = {
                        "model": name,
                        "messages": [
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": prompt}
                        ],
                        "response_format": {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "Evaluation",
                                "schema": Evaluation.model_json_schema()
                            }
                        },
                        "temperature": 0.1
                    }
                    resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
                    if resp.status_code != 200:
                        resp.raise_for_status()

                    raw_json = resp.json()
                    content = raw_json["choices"][0]["message"]["content"]
                    data = Evaluation.model_validate_json(content).model_dump()
                except Exception as error:
                    kind = classify_error(error)
                    reasons[name] = kind
                    health.gemini_failures += 1
                    print(f"[GROQ_ERROR] model={name} kind={kind} attempt={attempt+1} error={error}", flush=True)
                    delay = max(2 ** (attempt + 1) + self.jitter(), retry_after(error))
                    if (kind in {"invalid_response", "timeout", "unavailable", "rate_limit"}
                            and attempt + 1 < self.max_attempts and delay <= 25):
                        self.sleep(delay)
                        continue
                    state["failures"] += 1
                    state["reason"] = kind
                    if kind in {"daily_quota", "authentication", "configuration"}:
                        state["open_until"] = float("inf")
                    else:
                        base = 15
                        state["open_until"] = self.clock() + max(delay, min(120, base * 2 ** min(state["failures"] - 1, 3)))
                    break
                else:
                    state["failures"], state["open_until"], state["reason"] = 0, 0, ""
                    health.gemini_successes += 1
                    data["evaluation_source"] = "groq"
                    data["evaluation_model"] = name
                    data["evaluation_complete"] = True
                    return data
        raise EvaluationUnavailable(reasons)
