from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dsl_runtime.actions.dsl_builtin_actions import register_builtin_actions
from dsl_runtime.engine.channels import DummyChannel
from dsl_runtime.engine.context import RuntimeContext
from dsl_runtime.lang.ast_nodes import ActionCall, ScriptAST, State, StateMachine, UIConfig
from dsl_runtime.lang.executor import StateMachineExecutor


class ObservableStopExecutor(StateMachineExecutor):
    def __init__(
        self,
        ast: ScriptAST,
        ctx: RuntimeContext,
        stop_event: threading.Event,
        state_trace: List[str],
        progress_trace: List[int],
    ) -> None:
        super().__init__(ast, ctx)
        self._stop_event = stop_event
        self._state_trace = state_trace
        self._progress_trace = progress_trace
        self._visited = 0
        self._total = max(1, len(ast.state_machine.states))

    def run(self) -> None:
        if self.current:
            self._notify(self.current.name)
        while not self.done and not self._stop_event.is_set() and self.current:
            state = self.current
            self._run_actions(state)
            if self._stop_event.is_set():
                break
            if state.goto:
                if state.when:
                    cond = bool(self.ctx.eval_value(state.when))
                    target = state.goto if cond else state.else_goto
                    if target:
                        self._goto(target)
                        continue
                else:
                    self._goto(state.goto)
                    continue
            next_state = self._wait_event_or_timeout(state)
            if next_state:
                self._goto(next_state)
            else:
                self.done = True

    def _wait_event_or_timeout(self, state: State):
        if not state.on_event and not state.timeout:
            return None
        deadline = time.time() + (state.timeout / 1000.0 if state.timeout else 1e9)
        while time.time() <= deadline and not self.done and not self._stop_event.is_set():
            evt = self.ctx.next_event(timeout=0.1)
            if evt is None:
                continue
            if evt in state.on_event:
                return state.on_event[evt]
        if self._stop_event.is_set():
            return None
        return state.on_timeout

    def _goto(self, name: str) -> None:
        super()._goto(name)
        if self.current:
            self._notify(self.current.name)

    def _notify(self, name: str) -> None:
        self._visited += 1
        progress = int(min(1.0, self._visited / self._total) * 100)
        self._state_trace.append(name)
        self._progress_trace.append(progress)


@dataclass
class ScenarioResult:
    name: str
    passed: bool
    state_trace: List[str]
    progress_trace: List[int]
    detail: Dict[str, Any]


def register_actions() -> None:
    register_builtin_actions()


def make_context(vars_init: Dict[str, Any] | None = None) -> RuntimeContext:
    channels = {"boot": DummyChannel()}
    return RuntimeContext(channels, "boot", vars_init=vars_init or {})


def ast_run_complete() -> ScriptAST:
    states = {
        "start": State(name="start", actions=[ActionCall(name="set", args={"counter": 1})], goto="middle"),
        "middle": State(name="middle", actions=[ActionCall(name="wait", args={"ms": 20})], goto="done"),
        "done": State(name="done", actions=[]),
    }
    return ScriptAST(version=1, vars={}, channels={}, state_machine=StateMachine(initial="start", states=states), ui=UIConfig(charts=[]))


def ast_stop_early() -> ScriptAST:
    states = {
        "start": State(name="start", actions=[], timeout=5000, on_timeout="done"),
        "done": State(name="done", actions=[]),
    }
    return ScriptAST(version=1, vars={}, channels={}, state_machine=StateMachine(initial="start", states=states), ui=UIConfig(charts=[]))


def run_complete_scenario() -> ScenarioResult:
    state_trace: List[str] = []
    progress_trace: List[int] = []
    stop_event = threading.Event()
    ctx = make_context()
    executor = ObservableStopExecutor(ast_run_complete(), ctx, stop_event, state_trace, progress_trace)
    executor.run()
    ctx.close()
    passed = bool(state_trace and state_trace[-1] == "done" and progress_trace and progress_trace[-1] >= 100)
    return ScenarioResult(
        name="run_complete",
        passed=passed,
        state_trace=state_trace,
        progress_trace=progress_trace,
        detail={"done_flag": executor.done},
    )


def run_stop_scenario() -> ScenarioResult:
    state_trace: List[str] = []
    progress_trace: List[int] = []
    stop_event = threading.Event()
    ctx = make_context()
    executor = ObservableStopExecutor(ast_stop_early(), ctx, stop_event, state_trace, progress_trace)

    worker = threading.Thread(target=executor.run, daemon=True)
    worker.start()
    time.sleep(0.2)
    stop_event.set()
    worker.join(timeout=2.0)
    alive = worker.is_alive()
    ctx.close()

    passed = bool((not alive) and state_trace and state_trace[-1] != "done")
    return ScenarioResult(
        name="stop_early",
        passed=passed,
        state_trace=state_trace,
        progress_trace=progress_trace,
        detail={"thread_alive_after_join": alive, "done_flag": executor.done},
    )


def main() -> int:
    register_actions()
    results = [run_complete_scenario(), run_stop_scenario()]
    payload = {
        "passed": all(item.passed for item in results),
        "scenarios": [
            {
                "name": item.name,
                "passed": item.passed,
                "state_trace": item.state_trace,
                "progress_trace": item.progress_trace,
                "detail": item.detail,
            }
            for item in results
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
