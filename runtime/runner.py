from __future__ import annotations

import logging

from actions.builtin_actions import register_builtin_actions
from actions.protocol_actions import register_protocol_actions
from dsl.executor import StateMachineExecutor
from dsl.parser import parse_script
from runtime.channels import build_channels
from runtime.context import RuntimeContext


def _register_actions() -> None:
    register_builtin_actions()
    register_protocol_actions()


def run_dsl(path: str) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    _register_actions()

    ast = parse_script(path)
    channels = build_channels(ast.channels)
    if not channels:
        raise ValueError("未定义任何 channel")
    default_channel = next(iter(channels.keys()))
    ctx = RuntimeContext(channels, default_channel, vars_init=ast.vars)

    executor = StateMachineExecutor(ast, ctx)
    executor.run()
    return 0
