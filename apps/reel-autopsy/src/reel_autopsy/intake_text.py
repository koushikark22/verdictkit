"""Transient deterministic claim extraction; never persist source text (reel 8)."""
from __future__ import annotations

import re
from dataclasses import dataclass

MAX_CHARS = 2000


@dataclass(frozen=True, slots=True)
class ExtractedField:
    name: str
    value: str
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class Extraction:
    fields: tuple[ExtractedField, ...]


_URL = re.compile(r"(?i)(?:https?://|www\.|\b[a-z0-9-]+\.(?:com|net|org|io|co|gg|app|dev|ai|xyz|tv|me|edu|gov)\b(?:/|\b))")
_HANDLE = re.compile(r"(?<![\w.])@[A-Za-z][A-Za-z0-9_.]{1,30}\b")
_EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
# US-style telephone formats, requiring ten digits (with optional country prefix).
_PHONE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")
_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


def privacy_violations(text: str) -> tuple[str, ...]:
    if not isinstance(text, str):
        raise ValueError("claim text must be a string")
    problems = []
    if len(text) > MAX_CHARS:
        problems.append("too_long")
    if _URL.search(text):
        problems.append("url")
    if _HANDLE.search(text):
        problems.append("handle")
    if _EMAIL.search(text):
        problems.append("email")
    safe_text = _ISO_DATE.sub("DATE", text)
    if _PHONE.search(safe_text):
        problems.append("phone")
    return tuple(problems)


def extract(text: str) -> Extraction:
    issues = privacy_violations(text)
    if issues:
        raise ValueError("private or oversized text: " + ", ".join(issues))
    fields: list[ExtractedField] = []

    def add(name: str, match: re.Match, group: int = 1, value: str | None = None):
        start, end = match.span(group)
        fields.append(ExtractedField(name, value if value is not None else match.group(group), start, end))

    template_names = r"BUY_AND_HOLD|SMA_CROSS|DONCHIAN_BREAKOUT|RSI_REVERSION"
    m = re.search(rf"(?i)\b({template_names})\b", text)
    if m:
        add("template", m, value=m.group(1).upper())
    else:
        natural = re.search(r"(?i)\b(SMA\s+cross)\b", text)
        if natural:
            add("template", natural, value="SMA_CROSS")
    m = re.search(r"(?i)\b(?:symbol|instrument|ticker)\s*[:=]?\s*([A-Z][A-Z0-9._/-]{0,20})\b", text)
    if m:
        add("instrument", m)
    m = re.search(r"(?i)\b(?:timeframe|interval)\s*[:=]?\s*(1h|4h|1d)\b", text)
    if m:
        add("timeframe", m, value=m.group(1).lower())
    for name in ("fast", "slow", "lookback", "period", "lower", "upper"):
        m = re.search(rf"(?i)\b{name}\s*[:=]?\s*(\d+)\b", text)
        if m:
            add(f"template_params.{name}", m)
    for name, pattern in (
        ("total_return_pct", r"(?i)\b(?:total\s+return|return|gain|made)\s*[:=]?\s*([+-]?\d+(?:\.\d+)?)\s*%"),
        ("max_drawdown_pct", r"(?i)\b(?:max(?:imum)?\s+drawdown|drawdown)\s*[:=]?\s*([+-]?\d+(?:\.\d+)?)\s*%"),
        ("win_rate_pct", r"(?i)\bwin\s*rate\s*[:=]?\s*([+-]?\d+(?:\.\d+)?)\s*%"),
        ("trade_count", r"(?i)\b(?:trades|trade\s+count)\s*[:=]?\s*(\d+)\b"),
    ):
        m = re.search(pattern, text)
        if m:
            value = m.group(1).lstrip("+") if name == "total_return_pct" else None
            add(name, m, value=value)
    for name in ("start", "end"):
        m = re.search(rf"(?i)\b{name}\s*[:=]?\s*(\d{{4}}-\d{{2}}-\d{{2}})\b", text)
        if m:
            add(name, m)
    return Extraction(tuple(sorted(fields, key=lambda f: (f.start, f.name))))
