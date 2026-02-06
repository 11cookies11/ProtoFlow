from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple, Type


class ActionValidationError(ValueError):
    pass


_TYPE_ALIASES: Dict[str, Tuple[Type[Any], ...]] = {
    "number": (int, float),
    "string": (str,),
    "bool": (bool,),
    "mapping": (dict,),
    "list": (list, tuple),
}


@dataclass
class ActionBase:
    name: str
    schema: Dict[str, Any] | None = None

    def run(self, ctx, args: Dict[str, Any] | None) -> Any:
        payload = self.validate_args(args)
        return self.execute(ctx, payload)

    def execute(self, ctx, args: Dict[str, Any]) -> Any:
        raise NotImplementedError()

    def validate_args(self, args: Dict[str, Any] | None) -> Dict[str, Any]:
        if args is None:
            args = {}
        if not isinstance(args, dict):
            raise ActionValidationError("action args must be a mapping")
        schema = self.schema or {}
        aliases = schema.get("aliases", {}) or {}
        required = list(schema.get("required", []) or [])
        optional = dict(schema.get("optional", {}) or {})
        types = dict(schema.get("types", {}) or {})
        allow_extra = bool(schema.get("allow_extra", True))

        normalized = dict(args)
        for alias, target in aliases.items():
            if alias in normalized and target not in normalized:
                normalized[target] = normalized.pop(alias)

        for key, spec in optional.items():
            if key not in normalized:
                if isinstance(spec, dict) and "default" in spec:
                    normalized[key] = self._copy_default(spec.get("default"))
                else:
                    normalized[key] = self._copy_default(spec)

        for key in required:
            if key not in normalized:
                raise ActionValidationError(f"missing required arg: {key}")

        if not allow_extra:
            allowed = set(required) | set(optional) | set(types)
            extra = [k for k in normalized.keys() if k not in allowed]
            if extra:
                raise ActionValidationError(f"unknown args: {', '.join(extra)}")

        for key, type_spec in types.items():
            if key not in normalized:
                continue
            value = normalized.get(key)
            if value is None:
                continue
            expected = self._resolve_type_spec(type_spec)
            if expected is not None and not isinstance(value, expected):
                raise ActionValidationError(
                    f"arg '{key}' has invalid type: {type(value).__name__}"
                )
        return normalized

    @staticmethod
    def _resolve_type_spec(type_spec: Any) -> Tuple[Type[Any], ...] | None:
        if type_spec is None:
            return None
        if isinstance(type_spec, tuple):
            return type_spec
        if isinstance(type_spec, list):
            return tuple(type_spec)
        if isinstance(type_spec, str):
            return _TYPE_ALIASES.get(type_spec)
        if isinstance(type_spec, type):
            return (type_spec,)
        return None

    @staticmethod
    def _copy_default(value: Any) -> Any:
        if isinstance(value, dict):
            return dict(value)
        if isinstance(value, list):
            return list(value)
        return value
