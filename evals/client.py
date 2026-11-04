"""Model clients with an on-disk cache.

Providers:
  anthropic  needs `pip install anthropic` and ANTHROPIC_API_KEY
  openai     needs `pip install openai` and OPENAI_API_KEY
  mock       offline, deterministic noise for smoke tests. Its numbers mean nothing.

Every call is cached by (provider, model, temperature, sample index, prompt), so
re-running a report never re-bills and results stay reproducible.
"""

import hashlib
import json
import os
import random
import re

from .config import CACHE


class Client:
    def __init__(self, provider, model, temperature=0.0):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self._sdk = None

    @property
    def family(self):
        return self.provider

    def _key(self, prompt, sample):
        raw = json.dumps([self.provider, self.model, self.temperature, sample, prompt])
        return hashlib.sha256(raw.encode()).hexdigest()

    def complete(self, prompt, sample=0, max_tokens=1024):
        CACHE.mkdir(parents=True, exist_ok=True)
        path = CACHE / f"{self._key(prompt, sample)}.json"
        if path.exists():
            return json.loads(path.read_text())["text"]
        text = self._call(prompt, sample, max_tokens)
        path.write_text(json.dumps({"provider": self.provider, "model": self.model, "text": text}))
        return text

    def _call(self, prompt, sample, max_tokens):
        if self.provider == "mock":
            return _mock(prompt, sample)
        if self.provider == "anthropic":
            if self._sdk is None:
                import anthropic
                self._sdk = anthropic.Anthropic()
            r = self._sdk.messages.create(
                model=self.model, max_tokens=max_tokens, temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        if self.provider == "openai":
            if self._sdk is None:
                import openai
                self._sdk = openai.OpenAI()
            r = self._sdk.chat.completions.create(
                model=self.model, temperature=self.temperature, max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return r.choices[0].message.content
        raise ValueError(f"unknown provider {self.provider}")


def from_env(prefix="JUDGE"):
    provider = os.environ.get(f"{prefix}_PROVIDER", "mock")
    model = os.environ.get(f"{prefix}_MODEL", "mock")
    temp = float(os.environ.get(f"{prefix}_TEMPERATURE", "0"))
    return Client(provider, model, temp)


def parse_json(text):
    """Pull the last JSON object out of a model reply."""
    text = re.sub(r"```(?:json)?", "", text)
    depth, start, last = 0, None, None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth:
            depth -= 1
            if depth == 0:
                last = text[start:i + 1]
    if last is None:
        raise ValueError(f"no JSON object in reply: {text[:200]!r}")
    return json.loads(last)


def _mock(prompt, sample):
    """Seeded random replies in the right shape. Exists only to exercise the pipeline."""
    rng = random.Random(hashlib.md5(f"{prompt}{sample}".encode()).hexdigest())
    kind = re.search(r"prompt: (\w+)", prompt).group(1)
    if kind == "faithfulness":
        verdicts = ["supported"] * 4 + ["unsupported", "contradicted"]
        return json.dumps({"claims": [
            {"claim": f"claim {i}", "verdict": rng.choice(verdicts), "evidence": "mock"} for i in range(3)]})
    if kind in ("salience", "voice"):
        s = int(rng.random() < 0.7)
        return json.dumps({"covered_standouts": [], "errors": [] if s else [["mock", "mock"]], "score": s})
    if kind == "pairwise":
        return json.dumps({"reasoning": "mock", "winner": rng.choice(["A", "B", "tie"])})
    if kind == "v1_monolithic":
        return json.dumps({"justification": "mock", "scores": {
            "factual_fidelity": int(rng.random() < 0.7), "attribute_density": rng.randint(1, 3),
            "constraints": rng.randint(1, 3), "ux_clarity": rng.randint(1, 3)}})
    if kind == "generator":
        return "A mock highlight for pipeline testing."
    raise ValueError(kind)
