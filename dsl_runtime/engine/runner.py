from __future__ import annotations

import logging

from dsl_runtime.actions.dsl_builtin_actions import register_builtin_actions
from dsl_runtime.actions.dsl_protocol_actions import register_protocol_actions
from dsl_runtime.actions.dsl_protocol_schema_actions import register_schema_protocol_actions
from dsl_runtime.actions.dsl_chart_actions import register_chart_actions
from dsl_runtime.actions.dsl_record_actions import register_record_actions
from dsl_runtime.actions.dsl_data_actions import register_data_actions
from dsl_runtime.lang.executor import StateMachineExecutor
from dsl_runtime.lang.parser import parse_script
from dsl_runtime.engine.channels import build_channels
from dsl_runtime.engine.context import RuntimeContext


def _register_actions() -> None:
    register_builtin_actions()
    register_protocol_actions()
    register_schema_protocol_actions()
    register_chart_actions()
    register_record_actions()
    register_data_actions()


def run_dsl(path: str, *, bus=None, external_events: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    _register_actions()

    ast = parse_script(path)
    channels = build_channels(ast.channels)
    if not channels:
        raise ValueError("未定义任何 channel")
    default_channel = next(iter(channels.keys()))
    ctx = RuntimeContext(
        channels,
        default_channel,
        vars_init=ast.vars,
        bus=bus,
        external_events=external_events,
        script_path=path,
    )

    executor = StateMachineExecutor(ast, ctx)
    executor.run()
    if hasattr(ctx, "close"):
        ctx.close()
    return 0
