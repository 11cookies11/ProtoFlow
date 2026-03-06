from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

from .models import MatchRule, ResponseSpec, Scenario, ScenarioRule


def _parse_response(raw: Any) -> ResponseSpec | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("respond must be a mapping")
    text = raw.get("text")
    hex_text = raw.get("hex")
    eol = raw.get("eol")
    if text is None and hex_text is None:
        raise ValueError("respond.text or respond.hex is required")
    return ResponseSpec(
        text=str(text) if text is not None else None,
        hex=str(hex_text) if hex_text is not None else None,
        eol=str(eol) if eol is not None else None,
    )


def _parse_rule(raw: Any, idx: int) -> ScenarioRule:
    if not isinstance(raw, dict):
        raise ValueError(f"rules[{idx}] must be a mapping")
    rule_id = str(raw.get("id") or f"rule_{idx + 1}")
    when = raw.get("when")
    if not isinstance(when, dict):
        raise ValueError(f"rules[{idx}].when must be a mapping")
    match_type = str(when.get("type") or "contains").strip().lower()
    pattern = str(when.get("pattern") or "")
    if not pattern:
        raise ValueError(f"rules[{idx}].when.pattern is required")
    respond = _parse_response(raw.get("respond"))
    return ScenarioRule(
        id=rule_id,
        when=MatchRule(type=match_type, pattern=pattern),
        respond=respond,
        delay_ms=int(raw.get("delay_ms", 0)),
        drop=bool(raw.get("drop", False)),
        close_after=bool(raw.get("close_after", False)),
        once=bool(raw.get("once", False)),
        enabled=bool(raw.get("enabled", True)),
        meta=dict(raw.get("meta") or {}),
    )


def load_scenario(path: str | Path) -> Scenario:
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("scenario root must be a mapping")
    version = str(data.get("version") or "1")
    meta = data.get("meta") or {}
    if not isinstance(meta, dict):
        raise ValueError("meta must be a mapping")
    transport = data.get("transport_defaults") or {}
    if not isinstance(transport, dict):
        raise ValueError("transport_defaults must be a mapping")
    raw_rules = data.get("rules") or []
    if not isinstance(raw_rules, list):
        raise ValueError("rules must be a list")
    rules = [_parse_rule(item, idx) for idx, item in enumerate(raw_rules)]
    fallback_raw = data.get("fallback") or {}
    if fallback_raw and not isinstance(fallback_raw, dict):
        raise ValueError("fallback must be a mapping")
    fallback = _parse_response(fallback_raw.get("respond")) if fallback_raw else None
    return Scenario(
        version=version,
        name=str(meta.get("name") or p.stem),
        description=str(meta.get("description") or ""),
        encoding=str(transport.get("encoding") or "utf-8"),
        eol=str(transport.get("eol") or "crlf"),
        rules=rules,
        fallback=fallback,
        metadata=meta,
    )
