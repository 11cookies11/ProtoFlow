from __future__ import annotations

from pathlib import Path
from typing import List

from dsl.ast_nodes import ControlSpec, ScriptAST, UIConfig
from dsl.parser import parse_script


def controls_from_ast(ast: ScriptAST) -> List[ControlSpec]:
    ui_cfg: UIConfig = ast.ui if ast.ui else UIConfig()
    return list(ui_cfg.controls)


def controls_from_yaml(path: str | Path) -> List[ControlSpec]:
    ast = parse_script(str(path))
    return controls_from_ast(ast)

