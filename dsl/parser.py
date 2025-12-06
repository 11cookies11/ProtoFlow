from __future__ import annotations

from typing import Any, Dict, List

import yaml

from dsl.ast_nodes import ActionCall, ScriptAST, State, StateMachine


def _parse_actions(items: List[Any]) -> List[ActionCall]:
    actions: List[ActionCall] = []
    for item in items or []:
        if not isinstance(item, dict):
            raise ValueError(f"非法动作定义: {item}")
        if "action" in item:
            actions.append(ActionCall(name=item["action"], args=item.get("args", {}) or {}))
        elif "set" in item:
            actions.append(ActionCall(name="set", args=item["set"]))
        elif "log" in item:
            actions.append(ActionCall(name="log", args={"message": item["log"]}))
        elif "wait" in item:
            args = item["wait"] if isinstance(item["wait"], dict) else {"ms": item["wait"]}
            actions.append(ActionCall(name="wait", args=args))
        elif "wait_for_event" in item:
            args = item["wait_for_event"] if isinstance(item["wait_for_event"], dict) else {"event": item["wait_for_event"]}
            actions.append(ActionCall(name="wait_for_event", args=args))
        else:
            raise ValueError(f"未知动作类型: {item}")
    return actions


def _parse_state(name: str, node: Dict[str, Any]) -> State:
    return State(
        name=name,
        actions=_parse_actions(node.get("do", [])),
        on_event=node.get("on_event", {}) or {},
        timeout=node.get("timeout"),
        on_timeout=node.get("on_timeout"),
        when=node.get("when"),
        goto=node.get("goto"),
        else_goto=node.get("else_goto"),
    )


def parse_script(path: str) -> ScriptAST:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    version = int(data.get("version", 1))
    vars_def = data.get("vars", {}) or {}
    channels = data.get("channels", {}) or {}

    sm_cfg = data.get("state_machine") or {}
    initial = sm_cfg.get("initial")
    states_cfg = sm_cfg.get("states") or {}
    states: Dict[str, State] = {}
    for state_name, state_node in states_cfg.items():
        states[state_name] = _parse_state(state_name, state_node)
    if not initial or initial not in states:
        raise ValueError("state_machine.initial 未定义或未在 states 中声明")

    sm = StateMachine(initial=initial, states=states)
    return ScriptAST(version=version, vars=vars_def, channels=channels, state_machine=sm)
