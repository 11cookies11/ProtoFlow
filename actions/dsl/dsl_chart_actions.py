from __future__ import annotations

import time
from typing import Any, Dict

from actions.dsl.base import DslActionBase
from actions.chart_bridge import chart_bridge
from actions.registry import ActionRegistry


def _eval(ctx, val: Any) -> Any:
    if hasattr(ctx, "eval_value"):
        return ctx.eval_value(val)
    return val


class ChartAddAction(DslActionBase):
    def __init__(self) -> None:
        super().__init__(
            name="chart_add",
            schema={
                "required": ["bind", "value"],
                "aliases": {"val": "value", "timestamp": "ts"},
                "optional": {"ts": None},
                "types": {"ts": "number"},
                "allow_extra": False,
            },
        )

    def execute(self, ctx, args: Dict[str, Any]):
        bind = args.get("bind")
        raw_val = args.get("value")
        ts_arg = args.get("ts")
        ts = float(_eval(ctx, ts_arg)) if ts_arg is not None else time.time()
        try:
            val = float(_eval(ctx, raw_val))
        except Exception as exc:
            raise ValueError(f"chart_add value invalid: {exc}") from exc
        payload = {"ts": ts, str(bind): val}
        if hasattr(ctx, "record_chart"):
            try:
                ctx.record_chart(payload)
            except Exception:
                pass
        if chart_bridge is None:
            ctx.logger.warning("chart bridge unavailable (Qt not loaded)")
            return payload
        chart_bridge.sig_data.emit(payload)
        return {"ts": ts, "bind": str(bind), "value": val}


class ChartAdd3dAction(DslActionBase):
    def __init__(self) -> None:
        super().__init__(
            name="chart_add3d",
            schema={
                "required": ["x", "y", "z"],
                "aliases": {"timestamp": "ts"},
                "optional": {"ts": None, "bind_x": "x", "bind_y": "y", "bind_z": "z"},
                "types": {"ts": "number"},
                "allow_extra": False,
            },
        )

    def execute(self, ctx, args: Dict[str, Any]):
        bx = str(args.get("bind_x", "x"))
        by = str(args.get("bind_y", "y"))
        bz = str(args.get("bind_z", "z"))
        x_val = _eval(ctx, args.get("x"))
        y_val = _eval(ctx, args.get("y"))
        z_val = _eval(ctx, args.get("z"))
        ts_arg = args.get("ts")
        ts = float(_eval(ctx, ts_arg)) if ts_arg is not None else time.time()
        payload = {"ts": ts, bx: x_val, by: y_val, bz: z_val}
        if hasattr(ctx, "record_chart"):
            try:
                ctx.record_chart(payload)
            except Exception:
                pass
        if chart_bridge is None:
            ctx.logger.warning("chart bridge unavailable (Qt not loaded)")
            return payload
        chart_bridge.sig_data.emit(payload)
        return payload


def register_chart_actions() -> None:
    ActionRegistry.register("chart_add", ChartAddAction())
    ActionRegistry.register("chart_add3d", ChartAdd3dAction())
