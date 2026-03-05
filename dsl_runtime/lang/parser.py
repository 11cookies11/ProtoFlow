from __future__ import annotations

from typing import Any, Dict, List

import yaml

from dsl_runtime.lang.ast_nodes import ArtifactsConfig, DefaultsConfig, RetryPolicy, ScriptAST, SessionConfig


_ALLOWED_PARITY = {"none", "odd", "even", "mark", "space"}
_ALLOWED_ENCODING = {"ascii", "utf8", "hex"}
_ALLOWED_EOL = {"none", "cr", "lf", "crlf"}
_ALLOWED_RETRY_STRATEGY = {"fixed", "exponential"}


def _as_mapping(value: Any, *, field: str, required: bool = False) -> Dict[str, Any]:
    if value is None:
        if required:
            raise ValueError(f"{field} is required")
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a mapping")
    return value


def _as_int(value: Any, *, field: str, minimum: int | None = None) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    try:
        parsed = int(value)
    except Exception as exc:
        raise ValueError(f"{field} must be an integer") from exc
    if minimum is not None and parsed < minimum:
        raise ValueError(f"{field} must be >= {minimum}")
    return parsed


def _as_bool(value: Any, *, field: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ValueError(f"{field} must be a boolean")


def _as_str(value: Any, *, field: str, required: bool = False) -> str:
    if value is None:
        if required:
            raise ValueError(f"{field} is required")
        return ""
    parsed = str(value).strip()
    if required and not parsed:
        raise ValueError(f"{field} is required")
    return parsed


def _parse_session(session_data: Dict[str, Any]) -> SessionConfig:
    transport = _as_str(session_data.get("transport"), field="session.transport", required=True).lower()
    if transport != "serial":
        raise ValueError("session.transport must be serial in v0.1")

    port = _as_str(session_data.get("port"), field="session.port", required=True)
    baud = _as_int(session_data.get("baud", 115200), field="session.baud", minimum=1)
    data_bits = _as_int(session_data.get("data_bits", 8), field="session.data_bits", minimum=5)
    if data_bits not in {5, 6, 7, 8}:
        raise ValueError("session.data_bits must be one of 5/6/7/8")

    parity = _as_str(session_data.get("parity", "none"), field="session.parity", required=True).lower()
    if parity not in _ALLOWED_PARITY:
        raise ValueError("session.parity must be one of none/odd/even/mark/space")

    stop_bits = _as_int(session_data.get("stop_bits", 1), field="session.stop_bits", minimum=1)
    if stop_bits not in {1, 2}:
        raise ValueError("session.stop_bits must be 1 or 2 in v0.1")

    encoding = _as_str(session_data.get("encoding", "ascii"), field="session.encoding", required=True).lower()
    if encoding not in _ALLOWED_ENCODING:
        raise ValueError("session.encoding must be one of ascii/utf8/hex")

    eol = _as_str(session_data.get("eol", "none"), field="session.eol", required=True).lower()
    if eol not in _ALLOWED_EOL:
        raise ValueError("session.eol must be one of none/cr/lf/crlf")

    open_timeout_ms = _as_int(session_data.get("open_timeout_ms", 3000), field="session.open_timeout_ms", minimum=1)
    read_timeout_ms = _as_int(session_data.get("read_timeout_ms", 200), field="session.read_timeout_ms", minimum=1)

    return SessionConfig(
        transport=transport,
        port=port,
        baud=baud,
        data_bits=data_bits,
        parity=parity,
        stop_bits=stop_bits,
        encoding=encoding,
        eol=eol,
        open_timeout_ms=open_timeout_ms,
        read_timeout_ms=read_timeout_ms,
    )


def _parse_defaults(defaults_data: Dict[str, Any]) -> DefaultsConfig:
    retry_data = _as_mapping(defaults_data.get("retry"), field="defaults.retry")
    strategy = _as_str(retry_data.get("strategy", "fixed"), field="defaults.retry.strategy", required=True).lower()
    if strategy not in _ALLOWED_RETRY_STRATEGY:
        raise ValueError("defaults.retry.strategy must be fixed or exponential")

    retry = RetryPolicy(
        count=_as_int(retry_data.get("count", 0), field="defaults.retry.count", minimum=0),
        backoff_ms=_as_int(retry_data.get("backoff_ms", 0), field="defaults.retry.backoff_ms", minimum=0),
        strategy=strategy,
    )

    return DefaultsConfig(
        timeout_ms=_as_int(defaults_data.get("timeout_ms", 2000), field="defaults.timeout_ms", minimum=1),
        retry=retry,
        drain_before_expect=_as_bool(
            defaults_data.get("drain_before_expect", False), field="defaults.drain_before_expect"
        ),
        consume_on_match=_as_bool(defaults_data.get("consume_on_match", True), field="defaults.consume_on_match"),
    )


def _parse_artifacts(artifacts_data: Dict[str, Any]) -> ArtifactsConfig:
    return ArtifactsConfig(
        dir=_as_str(artifacts_data.get("dir", "./runs"), field="artifacts.dir") or "./runs",
        raw_log=_as_bool(artifacts_data.get("raw_log", True), field="artifacts.raw_log"),
        summary_json=_as_bool(artifacts_data.get("summary_json", True), field="artifacts.summary_json"),
        report_csv=_as_bool(artifacts_data.get("report_csv", False), field="artifacts.report_csv"),
    )


def _parse_steps(steps_data: Any) -> List[Dict[str, Any]]:
    if not isinstance(steps_data, list):
        raise ValueError("steps must be a list")
    parsed: List[Dict[str, Any]] = []
    for idx, step in enumerate(steps_data):
        if not isinstance(step, dict):
            raise ValueError(f"steps[{idx}] must be a mapping")
        name = step.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"steps[{idx}].name is required")
        parsed.append(step)
    return parsed


def parse_script(path: str) -> ScriptAST:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError("script root must be a mapping")

    version = str(data.get("version", "")).strip()
    if version != "0.1":
        raise ValueError("only YAML DSL version 0.1 is supported")

    params = _as_mapping(data.get("params"), field="params")
    vars_def = _as_mapping(data.get("vars"), field="vars")
    session = _parse_session(_as_mapping(data.get("session"), field="session", required=True))
    defaults = _parse_defaults(_as_mapping(data.get("defaults"), field="defaults"))
    steps = _parse_steps(data.get("steps"))
    artifacts = _parse_artifacts(_as_mapping(data.get("artifacts"), field="artifacts"))

    return ScriptAST(
        version=version,
        params=params,
        vars=vars_def,
        session=session,
        defaults=defaults,
        steps=steps,
        artifacts=artifacts,
    )
