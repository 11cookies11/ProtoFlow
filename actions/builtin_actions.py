from __future__ import annotations

import time
from typing import Any, Dict

from actions.registry import ActionRegistry
from dsl.expression import eval_expr


def _eval(ctx, val):
    if isinstance(val, str) and "$" in val:
        return eval_expr(val, ctx.vars_snapshot())
    return val


def action_set(ctx, args: Dict[str, Any]):
    for key, val in args.items():
        ctx.set_var(key, _eval(ctx, val))
    return ctx.vars_snapshot()


def action_log(ctx, args: Dict[str, Any]):
    msg = args.get("message") or args.get("msg") or ""
    if isinstance(msg, str) and "$" in msg:
        msg = eval_expr(msg, ctx.vars_snapshot())
    ctx.logger.info(str(msg))


def action_wait(ctx, args: Dict[str, Any]):
    ms = int(args.get("ms", 0))
    time.sleep(ms / 1000.0)


def action_wait_for_event(ctx, args: Dict[str, Any]):
    expected = args.get("event")
    timeout = float(args.get("timeout", 1.0))
    end = time.time() + timeout
    while time.time() < end:
        evt = ctx.next_event(timeout=0.1)
        if evt is None:
            continue
        if expected is None or evt == expected:
            ctx.set_var("event", evt)
            return evt
    return None


def register_builtin_actions():
    ActionRegistry.register("set", action_set)
    ActionRegistry.register("log", action_log)
    ActionRegistry.register("wait", action_wait)
    ActionRegistry.register("wait_for_event", action_wait_for_event)
