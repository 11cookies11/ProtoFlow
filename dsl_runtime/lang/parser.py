from __future__ import annotations

from copy import deepcopy
from pathlib import Path
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
        template_ref = step.get("template")
        if (not isinstance(name, str) or not name.strip()) and (not isinstance(template_ref, str) or not template_ref.strip()):
            raise ValueError(f"steps[{idx}].name or steps[{idx}].template is required")
        parsed.append(step)
    return parsed


def _replace_tokens(obj: Any, values: Dict[str, Any]) -> Any:
    if isinstance(obj, str):
        out = obj
        for k, v in values.items():
            out = out.replace("${" + str(k) + "}", str(v))
        return out
    if isinstance(obj, list):
        return [_replace_tokens(item, values) for item in obj]
    if isinstance(obj, dict):
        return {key: _replace_tokens(value, values) for key, value in obj.items()}
    return obj


def _expand_step_templates(steps: List[Dict[str, Any]], templates_data: Any) -> List[Dict[str, Any]]:
    if templates_data is None:
        return steps
    if not isinstance(templates_data, dict):
        raise ValueError("step_templates must be a mapping")
    expanded: List[Dict[str, Any]] = []
    for idx, step in enumerate(steps):
        template_name = step.get("template")
        if not template_name:
            expanded.append(step)
            continue
        if not isinstance(template_name, str):
            raise ValueError(f"steps[{idx}].template must be string")
        tpl = templates_data.get(template_name)
        if not isinstance(tpl, dict):
            raise ValueError(f"step template not found: {template_name}")
        params = tpl.get("params") or []
        if not isinstance(params, list):
            raise ValueError(f"step_templates.{template_name}.params must be list")
        args = step.get("args") or {}
        if not isinstance(args, dict):
            raise ValueError(f"steps[{idx}].args must be a mapping")
        values: Dict[str, Any] = {}
        for p in params:
            key = str(p)
            if key not in args:
                raise ValueError(f"steps[{idx}].args missing template param: {key}")
            values[key] = args[key]
        tpl_steps: List[Any]
        if "step" in tpl:
            tpl_steps = [tpl.get("step")]
        else:
            tpl_steps = tpl.get("steps") or []
        if not isinstance(tpl_steps, list):
            raise ValueError(f"step_templates.{template_name}.steps must be list")
        for item in tpl_steps:
            if not isinstance(item, dict):
                raise ValueError(f"step_templates.{template_name} contains non-mapping step")
            rendered = _replace_tokens(deepcopy(item), values)
            expanded.append(rendered)
    return expanded


def _load_import_steps(script_path: str, imports_data: Any, visited: set[str] | None = None) -> List[Dict[str, Any]]:
    if imports_data is None:
        return []
    if not isinstance(imports_data, list):
        raise ValueError("imports/include must be a list")
    visited = visited or set()
    base = Path(script_path).resolve().parent
    merged: List[Dict[str, Any]] = []
    for idx, item in enumerate(imports_data):
        rel = str(item).strip()
        if not rel:
            raise ValueError(f"imports[{idx}] path is empty")
        fp = (base / rel).resolve()
        key = str(fp)
        if key in visited:
            continue
        visited.add(key)
        if not fp.exists():
            raise ValueError(f"import file not found: {rel}")
        with fp.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise ValueError(f"import file must be a mapping: {rel}")
        nested = data.get("imports")
        if nested is None:
            nested = data.get("include")
        merged.extend(_load_import_steps(str(fp), nested, visited))
        merged.extend(_parse_steps(data.get("steps", [])))
    return merged


def parse_script(path: str) -> ScriptAST:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError("script root must be a mapping")

    version = str(data.get("version", "")).strip()
    if version not in {"0.1", "0.2"}:
        raise ValueError("only YAML DSL version 0.1/0.2 is supported")

    params = _as_mapping(data.get("params"), field="params")
    vars_def = _as_mapping(data.get("vars"), field="vars")
    profiles = _as_mapping(data.get("profiles"), field="profiles")
    session_raw = _as_mapping(data.get("session"), field="session", required=True)
    profile_name = session_raw.get("profile")
    if profile_name is not None:
        profile_key = str(profile_name).strip()
        profile_cfg = profiles.get(profile_key)
        if not isinstance(profile_cfg, dict):
            raise ValueError(f"session.profile not found: {profile_key}")
        merged_session = dict(profile_cfg)
        for key, value in session_raw.items():
            if key == "profile":
                continue
            merged_session[key] = value
        session_raw = merged_session
    session = _parse_session(session_raw)
    defaults = _parse_defaults(_as_mapping(data.get("defaults"), field="defaults"))
    imports_data = data.get("imports")
    if imports_data is None:
        imports_data = data.get("include")
    raw_steps = _load_import_steps(path, imports_data) + _parse_steps(data.get("steps"))
    steps = _expand_step_templates(raw_steps, data.get("step_templates"))
    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError(f"expanded steps[{idx}] must be a mapping")
        name = step.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"expanded steps[{idx}].name is required")
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
